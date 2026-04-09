import type { MacroInput, Entity, DecisionResult } from "@/types/decision";
import type { TenantContext } from "@/types/tenant";

// ── Base Event ───────────────────────────────────────────────────────────────

export interface BaseEvent {
  id: string;
  type: string;
  tenantId: string;
  userId: string;
  timestamp: number;
  correlationId: string;
}

// ── Domain Events ────────────────────────────────────────────────────────────

export interface DecisionRequestedEvent extends BaseEvent {
  type: "DECISION_REQUESTED";
  payload: {
    evaluationId: string;
    macro: MacroInput;
    entities: Entity[];
    scenario: string;
    tenant: TenantContext;
  };
}

export interface DecisionCompletedEvent extends BaseEvent {
  type: "DECISION_COMPLETED";
  payload: {
    evaluationId: string;
    scenario: string;
    results: DecisionResult[];
    entityCount: number;
    avgRisk: number;
    v1Available: boolean;
    latencyMs: number;
  };
}

export interface AuditLoggedEvent extends BaseEvent {
  type: "AUDIT_LOGGED";
  payload: {
    evaluationId: string;
    eventType: string;
    entityId?: string;
    data: Record<string, unknown>;
  };
}

export interface ScenarioEvaluatedEvent extends BaseEvent {
  type: "SCENARIO_EVALUATED";
  payload: {
    evaluationId: string;
    scenario: string;
    macro: MacroInput;
    approved: number;
    conditional: number;
    rejected: number;
    avgRisk: number;
  };
}

export interface PolicyTriggeredEvent extends BaseEvent {
  type: "POLICY_TRIGGERED";
  payload: {
    evaluationId: string;
    entityId: string;
    entityName: string;
    riskScore: number;
    decision: string;
    policies: string[];
  };
}

export type DomainEvent =
  | DecisionRequestedEvent
  | DecisionCompletedEvent
  | AuditLoggedEvent
  | ScenarioEvaluatedEvent
  | PolicyTriggeredEvent;

export type EventType = DomainEvent["type"];

export type EventOfType<T extends EventType> = Extract<DomainEvent, { type: T }>;

export type EventHandler<T extends EventType> = (
  event: EventOfType<T>,
) => void | Promise<void>;
