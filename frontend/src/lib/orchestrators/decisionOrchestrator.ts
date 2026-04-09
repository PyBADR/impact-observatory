import { generateSignals } from "@/lib/engines/signalEngine";
import { evaluateRisk, explainRisk } from "@/lib/engines/decisionEngine";
import { applyPolicies } from "@/lib/engines/policyEngine";
import {
  fetchV1Decisions,
  fetchV1AuthorityMetrics,
  matchEntityToV1Decision,
} from "@/lib/adapters/v1Adapter";
import {
  saveEvaluation,
  appendAuditEvent,
  getEvaluations as loadEvaluations,
  getEvaluationCount,
} from "@/lib/persistence/store";
import { EventBus, eventId } from "@/lib/events/eventBus";
import {
  initializeWorkers,
  getCompletedResult,
} from "@/lib/workers/decisionWorker";
import type {
  MacroInput,
  Entity,
  SignalOutput,
  DecisionResult,
} from "@/types/decision";
import type { TenantContext, EvaluationRecord } from "@/types/tenant";
import type { OperatorDecision } from "@/types/observatory";
import type { DecisionRequestedEvent } from "@/lib/events/types";

/**
 * Decision Orchestrator — dual-mode execution.
 *
 * Mode: "sync"  → full pipeline inline, returns results immediately (default)
 * Mode: "async" → emits DecisionRequested event, returns evaluationId for polling
 *
 * The mode is controlled by the `async` flag in the input.
 */

// Ensure workers are registered on first import
initializeWorkers();

// In-memory delta cache
const previousScores: Map<string, number> = new Map();

export interface OrchestratedResult extends DecisionResult {
  entityId: string;
  sector: string;
  coverage: number;
  v1Decision: OperatorDecision | null;
  v1Linked: boolean;
}

export interface OrchestratedResponse {
  evaluationId: string;
  scenario: string;
  status: "completed" | "processing";
  results: OrchestratedResult[];
  signalSnapshot: SignalOutput | null;
  v1Context: {
    available: boolean;
    decisionsLoaded: number;
    authorityMetrics: Record<string, number> | null;
  } | null;
  tenant: {
    tenantId: string;
    userId: string;
    evaluationNumber: number;
  };
  eventBus: {
    processed: number;
    failed: number;
    logSize: number;
  };
  latencyMs: number;
  timestamp: string;
}

function generateEvalId(): string {
  return `eval_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
}

export async function evaluateMacroDecision(input: {
  macro: MacroInput;
  entities: Entity[];
  scenario?: string;
  tenant: TenantContext;
  async?: boolean;
}): Promise<OrchestratedResponse> {
  const { macro, entities, scenario = "custom", tenant } = input;
  const evaluationId = generateEvalId();
  const bus = EventBus.getInstance();

  // ── Async mode: emit event and return immediately ─────────────────────
  if (input.async) {
    const requestEvent: DecisionRequestedEvent = {
      id: eventId(),
      type: "DECISION_REQUESTED",
      tenantId: tenant.tenantId,
      userId: tenant.userId,
      timestamp: Date.now(),
      correlationId: evaluationId,
      payload: { evaluationId, macro, entities, scenario, tenant },
    };
    bus.emit(requestEvent);

    const evalCount = getEvaluationCount(tenant.tenantId);

    return {
      evaluationId,
      scenario,
      status: "processing",
      results: [],
      signalSnapshot: null,
      v1Context: null,
      tenant: {
        tenantId: tenant.tenantId,
        userId: tenant.userId,
        evaluationNumber: evalCount,
      },
      eventBus: bus.getStats(),
      latencyMs: 0,
      timestamp: new Date().toISOString(),
    };
  }

  // ── Sync mode: execute full pipeline inline (default) ─────────────────
  const startTime = performance.now();

  const [v1Decisions, v1Metrics] = await Promise.all([
    fetchV1Decisions({ limit: 50 }),
    fetchV1AuthorityMetrics(),
  ]);

  const signals = generateSignals(macro);

  const results: OrchestratedResult[] = entities.map((entity) => {
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

  // Persist
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

  // Audit
  appendAuditEvent({
    tenantId: tenant.tenantId,
    userId: tenant.userId,
    id: `audit_${Date.now()}_completed`,
    eventType: "EVALUATION_COMPLETED",
    timestamp: record.createdAt,
    data: {
      evaluationId,
      scenario,
      entityCount: entities.length,
      avgRisk: Math.round(results.reduce((s, r) => s + r.riskScore, 0) / results.length),
      latencyMs,
    },
  });

  // Emit domain events (fire-and-forget, non-blocking)
  const avgRisk = Math.round(results.reduce((s, r) => s + r.riskScore, 0) / results.length);
  bus.emit({
    id: eventId(),
    type: "DECISION_COMPLETED",
    tenantId: tenant.tenantId,
    userId: tenant.userId,
    timestamp: Date.now(),
    correlationId: evaluationId,
    payload: {
      evaluationId,
      scenario,
      results,
      entityCount: entities.length,
      avgRisk,
      v1Available: v1Decisions.available,
      latencyMs,
    },
  });

  bus.emit({
    id: eventId(),
    type: "SCENARIO_EVALUATED",
    tenantId: tenant.tenantId,
    userId: tenant.userId,
    timestamp: Date.now(),
    correlationId: evaluationId,
    payload: {
      evaluationId,
      scenario,
      macro,
      approved: results.filter((r) => r.decision === "APPROVED").length,
      conditional: results.filter((r) => r.decision === "CONDITIONAL").length,
      rejected: results.filter((r) => r.decision === "REJECTED").length,
      avgRisk,
    },
  });

  for (const r of results) {
    if (r.policies.some((p) => p.includes("RISK_CEILING") || p.includes("HIGH_RISK"))) {
      bus.emit({
        id: eventId(),
        type: "POLICY_TRIGGERED",
        tenantId: tenant.tenantId,
        userId: tenant.userId,
        timestamp: Date.now(),
        correlationId: evaluationId,
        payload: {
          evaluationId,
          entityId: r.entityId,
          entityName: r.entity,
          riskScore: r.riskScore,
          decision: r.decision,
          policies: r.policies,
        },
      });
    }
  }

  const evalCount = getEvaluationCount(tenant.tenantId);

  return {
    evaluationId,
    scenario,
    status: "completed",
    results,
    signalSnapshot: signals,
    v1Context: {
      available: v1Decisions.available,
      decisionsLoaded: v1Decisions.count,
      authorityMetrics: v1Metrics.available
        ? {
            proposed: v1Metrics.proposed,
            under_review: v1Metrics.under_review,
            approved: v1Metrics.approved_pending_execution,
            executed: v1Metrics.executed,
            rejected: v1Metrics.rejected,
            total: v1Metrics.total,
          }
        : null,
    },
    tenant: {
      tenantId: tenant.tenantId,
      userId: tenant.userId,
      evaluationNumber: evalCount,
    },
    eventBus: bus.getStats(),
    latencyMs,
    timestamp: record.createdAt,
  };
}

/** Poll for async evaluation result. */
export function pollEvaluation(evaluationId: string): Record<string, unknown> | null {
  return getCompletedResult(evaluationId);
}

export function getEvaluationHistory(tenantId: string, limit = 20) {
  return loadEvaluations(tenantId, limit);
}
