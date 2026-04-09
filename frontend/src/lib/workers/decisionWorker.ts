import { EventBus, eventId } from "@/lib/events/eventBus";
import type {
  DecisionRequestedEvent,
  DecisionCompletedEvent,
  ScenarioEvaluatedEvent,
  PolicyTriggeredEvent,
  AuditLoggedEvent,
} from "@/lib/events/types";
import { generateSignals } from "@/lib/engines/signalEngine";
import { evaluateRisk, explainRisk } from "@/lib/engines/decisionEngine";
import { applyPolicies } from "@/lib/engines/policyEngine";
import {
  fetchV1Decisions,
  matchEntityToV1Decision,
} from "@/lib/adapters/v1Adapter";
import {
  saveEvaluation,
  appendAuditEvent,
} from "@/lib/persistence/store";
import { appendEventRecord } from "@/lib/persistence/eventStore";
import type { EvaluationRecord, AuditEvent } from "@/types/tenant";

/**
 * Decision Worker — processes DecisionRequested events asynchronously.
 *
 * Subscribes to DECISION_REQUESTED and executes the full pipeline:
 *   V1 fetch → Signal → Decision → Policy → Persist → Emit completion events
 */

// In-memory delta cache (tenant-scoped)
const previousScores: Map<string, number> = new Map();

// Track completed evaluations for polling
const completedResults: Map<string, Record<string, unknown>> = new Map();
const MAX_COMPLETED_CACHE = 200;

export function getCompletedResult(evaluationId: string): Record<string, unknown> | null {
  return completedResults.get(evaluationId) ?? null;
}

function cacheResult(evaluationId: string, result: Record<string, unknown>): void {
  completedResults.set(evaluationId, result);
  // Evict oldest entries
  if (completedResults.size > MAX_COMPLETED_CACHE) {
    const firstKey = completedResults.keys().next().value;
    if (firstKey) completedResults.delete(firstKey);
  }
}

async function handleDecisionRequested(event: DecisionRequestedEvent): Promise<void> {
  const startTime = performance.now();
  const { evaluationId, macro, entities, scenario, tenant } = event.payload;
  const bus = EventBus.getInstance();

  // ── Execute pipeline ──────────────────────────────────────────────────
  const v1Decisions = await fetchV1Decisions({ limit: 50 });
  const signals = generateSignals(macro);

  const results = entities.map((entity) => {
    const scoreKey = `${tenant.tenantId}:${entity.id}`;
    const riskScore = evaluateRisk(entity, signals);

    const prevScore = previousScores.get(scoreKey);
    const delta = prevScore !== undefined ? riskScore - prevScore : 0;
    previousScores.set(scoreKey, riskScore);

    const { decision, policies } = applyPolicies(riskScore, entity);
    const explanation = explainRisk(entity, signals, riskScore, macro);
    const v1Match = matchEntityToV1Decision(entity, v1Decisions.decisions);

    const enrichedPolicies = [...policies];
    if (v1Match) {
      enrichedPolicies.push(`V1_LINKED:${v1Match.decision_status}`);
      if (v1Match.decision_status === "EXECUTED") {
        enrichedPolicies.push("V1_ALREADY_EXECUTED");
      }
    }

    return {
      entity: entity.name,
      entityId: entity.id,
      sector: entity.sector,
      coverage: entity.coverage,
      decision,
      riskScore,
      delta,
      policies: enrichedPolicies,
      explanation,
      v1Decision: v1Match,
      v1Linked: v1Match !== null,
    };
  });

  const latencyMs = Math.round(performance.now() - startTime);
  const avgRisk = Math.round(results.reduce((s, r) => s + r.riskScore, 0) / results.length);

  // ── Persist evaluation ────────────────────────────────────────────────
  const record: EvaluationRecord = {
    id: evaluationId,
    tenantId: tenant.tenantId,
    userId: tenant.userId,
    scenario,
    scenarioVersion: "v1",
    macro,
    entityCount: entities.length,
    results: results.map((r) => ({
      entityId: r.entityId,
      entity: r.entity,
      decision: r.decision,
      riskScore: r.riskScore,
      delta: r.delta,
      policies: r.policies,
      v1Linked: r.v1Linked,
    })),
    v1Available: v1Decisions.available,
    latencyMs,
    createdAt: new Date().toISOString(),
  };

  saveEvaluation(record);

  // ── Persist audit ─────────────────────────────────────────────────────
  appendAuditEvent({
    tenantId: tenant.tenantId,
    userId: tenant.userId,
    id: `audit_${Date.now()}_completed`,
    eventType: "EVALUATION_COMPLETED",
    timestamp: record.createdAt,
    data: { evaluationId, scenario, entityCount: entities.length, avgRisk, latencyMs },
  });

  // ── Cache result for polling ──────────────────────────────────────────
  const fullResult = {
    evaluationId,
    scenario,
    results,
    signalSnapshot: signals,
    v1Context: { available: v1Decisions.available, decisionsLoaded: v1Decisions.count },
    tenant: { tenantId: tenant.tenantId, userId: tenant.userId },
    latencyMs,
    status: "completed" as const,
    timestamp: record.createdAt,
  };
  cacheResult(evaluationId, fullResult);

  // ── Emit completion events ────────────────────────────────────────────
  const baseFields = {
    tenantId: tenant.tenantId,
    userId: tenant.userId,
    timestamp: Date.now(),
    correlationId: evaluationId,
  };

  const completedEvent: DecisionCompletedEvent = {
    ...baseFields,
    id: eventId(),
    type: "DECISION_COMPLETED",
    payload: {
      evaluationId,
      scenario,
      results,
      entityCount: entities.length,
      avgRisk,
      v1Available: v1Decisions.available,
      latencyMs,
    },
  };
  bus.emit(completedEvent);

  const scenarioEvent: ScenarioEvaluatedEvent = {
    ...baseFields,
    id: eventId(),
    type: "SCENARIO_EVALUATED",
    payload: {
      evaluationId,
      scenario,
      macro,
      approved: results.filter((r) => r.decision === "APPROVED").length,
      conditional: results.filter((r) => r.decision === "CONDITIONAL").length,
      rejected: results.filter((r) => r.decision === "REJECTED").length,
      avgRisk,
    },
  };
  bus.emit(scenarioEvent);

  // Emit per-entity policy triggers
  for (const r of results) {
    if (r.policies.some((p) => p.includes("RISK_CEILING") || p.includes("HIGH_RISK"))) {
      const policyEvent: PolicyTriggeredEvent = {
        ...baseFields,
        id: eventId(),
        type: "POLICY_TRIGGERED",
        payload: {
          evaluationId,
          entityId: r.entityId,
          entityName: r.entity,
          riskScore: r.riskScore,
          decision: r.decision,
          policies: r.policies,
        },
      };
      bus.emit(policyEvent);
    }
  }
}

// ── Audit Logger Worker ──────────────────────────────────────────────────────

function handleAuditLogged(event: AuditLoggedEvent): void {
  appendAuditEvent({
    id: event.id,
    tenantId: event.tenantId,
    userId: event.userId,
    eventType: event.payload.eventType as AuditEvent["eventType"],
    entityId: event.payload.entityId,
    data: event.payload.data,
    timestamp: new Date(event.timestamp).toISOString(),
  });
}

// ── Event Persistence Worker ─────────────────────────────────────────────────

function handleAllEvents(event: DecisionRequestedEvent | DecisionCompletedEvent | ScenarioEvaluatedEvent | PolicyTriggeredEvent): void {
  appendEventRecord(event.tenantId, {
    id: event.id,
    type: event.type,
    correlationId: event.correlationId,
    timestamp: new Date(event.timestamp).toISOString(),
    payload: event.payload,
  });
}

// ── Bootstrap ────────────────────────────────────────────────────────────────

let initialized = false;

export function initializeWorkers(): void {
  if (initialized) return;
  initialized = true;

  const bus = EventBus.getInstance();

  // Core decision processing
  bus.on("DECISION_REQUESTED", handleDecisionRequested);

  // Audit persistence
  bus.on("AUDIT_LOGGED", handleAuditLogged);

  // Event persistence (all major events)
  bus.on("DECISION_COMPLETED", handleAllEvents);
  bus.on("SCENARIO_EVALUATED", handleAllEvents);
  bus.on("POLICY_TRIGGERED", handleAllEvents);
}
