/** Tenant identity attached to every request through the platform. */
export interface TenantContext {
  tenantId: string;
  userId: string;
  role: "admin" | "operator" | "analyst" | "viewer";
  orgName?: string;
}

/** Persisted evaluation record — one row per orchestrator call. */
export interface EvaluationRecord {
  id: string;
  tenantId: string;
  userId: string;
  scenario: string;
  scenarioVersion: string;
  macro: { inflation: number; interestRate: number; gdpGrowth: number };
  entityCount: number;
  results: Array<{
    entityId: string;
    entity: string;
    decision: string;
    riskScore: number;
    delta: number;
    policies: string[];
    v1Linked: boolean;
  }>;
  v1Available: boolean;
  latencyMs: number;
  createdAt: string;
}

/** Persisted audit event — immutable append-only log. */
export interface AuditEvent {
  id: string;
  tenantId: string;
  userId: string;
  eventType:
    | "EVALUATION_REQUESTED"
    | "EVALUATION_COMPLETED"
    | "SCENARIO_CHANGED"
    | "MACRO_ADJUSTED"
    | "V1_LINKED"
    | "POLICY_TRIGGERED";
  entityId?: string;
  data: Record<string, unknown>;
  timestamp: string;
}

/** Tenant-scoped scenario override. */
export interface TenantScenario {
  id: string;
  tenantId: string;
  name: string;
  version: number;
  config: { inflation: number; interestRate: number; gdpGrowth: number };
  createdAt: string;
  updatedAt: string;
}
