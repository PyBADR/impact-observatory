/**
 * Banking Intelligence API Client
 *
 * Endpoint paths match backend routers registered under /api/v1:
 * - /api/v1/banking/entities   → entities.py (prefix="/banking/entities")
 * - /api/v1/banking/decisions  → decisions.py (prefix="/banking/decisions")
 * - /api/v1/banking/chain      → scenario_chain.py (prefix="/banking/chain")
 */

import type {
  DecisionContract,
  CounterfactualContract,
  PropagationContract,
  OutcomeReviewContract,
  DecisionValueAudit,
} from "@/types/banking-intelligence";
import { DecisionStatus } from "@/types/banking-intelligence";

/** Full decision chain returned by /banking/chain endpoints */
export interface BankingDecisionChain {
  decision_contract: DecisionContract;
  counterfactual_contract: CounterfactualContract;
  propagation_contracts: PropagationContract[];
  outcome_review_contract: OutcomeReviewContract;
  metadata: Record<string, unknown>;
}

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";
const API_KEY = process.env.NEXT_PUBLIC_API_KEY || "";

// ─── Fetch Helper ─────────────────────────────────────────────────────────

export class BankingApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string
  ) {
    super(message);
    this.name = "BankingApiError";
  }
}

async function fetchJSON<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers: HeadersInit = {
    "Content-Type": "application/json",
    ...(API_KEY && { "X-API-Key": API_KEY }),
    ...options.headers,
  };

  const response = await fetch(url, { ...options, headers });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new BankingApiError(
      response.status,
      error.code || "UNKNOWN_ERROR",
      error.detail || error.message || `HTTP ${response.status}`
    );
  }

  return response.json() as Promise<T>;
}

// ─── Entity Operations ────────────────────────────────────────────────────

/** Fetch banking entities with optional filtering */
export async function fetchBankingEntities(params?: {
  entity_type?: string;
  country_code?: string;
  limit?: number;
  offset?: number;
}): Promise<unknown[]> {
  const qs = params
    ? "?" + new URLSearchParams(
        Object.entries(params)
          .filter(([, v]) => v !== undefined)
          .map(([k, v]) => [k, String(v)])
      ).toString()
    : "";
  return fetchJSON(`/api/v1/banking/entities/${qs}`, { method: "GET" });
}

/** Ingest a new banking entity */
export async function ingestBankingEntity(
  entity_type: string,
  data: Record<string, unknown>
): Promise<unknown> {
  return fetchJSON(`/api/v1/banking/entities/ingest`, {
    method: "POST",
    body: JSON.stringify({ entity_type, ...data }),
  });
}

/** Get a single banking entity by canonical ID */
export async function fetchBankingEntity(
  canonicalId: string
): Promise<unknown> {
  return fetchJSON(`/api/v1/banking/entities/${canonicalId}`, {
    method: "GET",
  });
}

/** Get entity type list */
export async function fetchEntityTypes(): Promise<string[]> {
  return fetchJSON(`/api/v1/banking/entities/types`, { method: "GET" });
}

/** Get dedup stats */
export async function fetchDedupStats(): Promise<unknown> {
  return fetchJSON(`/api/v1/banking/entities/dedup/stats`, { method: "GET" });
}

// ─── Decision Chain Operations (scenario_chain.py) ────────────────────────

/** Bridge a simulation result to banking intelligence contracts */
export async function bridgeFromSimulation(
  runId: string,
  scenarioId: string,
  simResult: Record<string, unknown>
): Promise<BankingDecisionChain> {
  return fetchJSON(`/api/v1/banking/chain/from-simulation`, {
    method: "POST",
    body: JSON.stringify({
      run_id: runId,
      scenario_id: scenarioId,
      sim_result: simResult,
    }),
  });
}

/** Execute simulation and bridge to contracts end-to-end */
export async function bridgeFromRun(
  runId: string,
  scenarioId: string,
  baselineUrs: number = 0.25
): Promise<BankingDecisionChain> {
  return fetchJSON(`/api/v1/banking/chain/from-run/${runId}`, {
    method: "POST",
    body: JSON.stringify({
      scenario_id: scenarioId,
      baseline_urs: baselineUrs,
    }),
  });
}

/** Retrieve a previously stored scenario chain */
export async function fetchDecisionChain(
  runId: string
): Promise<BankingDecisionChain> {
  return fetchJSON(`/api/v1/banking/chain/${runId}`, { method: "GET" });
}

// ─── Decision Contract Operations ─────────────────────────────────────────

/** List decision contracts */
export async function fetchDecisionContracts(params?: {
  scenario_id?: string;
  status?: string;
  limit?: number;
  offset?: number;
}): Promise<DecisionContract[]> {
  const qs = params
    ? "?" + new URLSearchParams(
        Object.entries(params)
          .filter(([, v]) => v !== undefined)
          .map(([k, v]) => [k, String(v)])
      ).toString()
    : "";
  return fetchJSON(`/api/v1/banking/decisions/contracts${qs}`, {
    method: "GET",
  });
}

/** Create a new decision contract */
export async function createDecisionContract(
  data: Record<string, unknown>
): Promise<DecisionContract> {
  return fetchJSON(`/api/v1/banking/decisions/contracts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Get a single decision contract */
export async function fetchDecisionContract(
  decisionId: string
): Promise<DecisionContract> {
  return fetchJSON(`/api/v1/banking/decisions/contracts/${decisionId}`, {
    method: "GET",
  });
}

/** Transition a decision to a new status */
export async function transitionDecision(
  decisionId: string,
  targetStatus: DecisionStatus,
  changedBy: string,
  reason?: string
): Promise<DecisionContract> {
  return fetchJSON(
    `/api/v1/banking/decisions/contracts/${decisionId}/transition`,
    {
      method: "POST",
      body: JSON.stringify({
        target_status: targetStatus,
        changed_by: changedBy,
        reason,
      }),
    }
  );
}

/** Get full decision chain (decision + counterfactual + review + audit) */
export async function fetchDecisionFullChain(
  decisionId: string
): Promise<BankingDecisionChain> {
  return fetchJSON(
    `/api/v1/banking/decisions/contracts/${decisionId}/chain`,
    { method: "GET" }
  );
}

// ─── Counterfactual Operations ────────────────────────────────────────────

/** Create a counterfactual contract */
export async function createCounterfactual(
  data: Record<string, unknown>
): Promise<CounterfactualContract> {
  return fetchJSON(`/api/v1/banking/decisions/counterfactuals`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Get a counterfactual contract */
export async function fetchCounterfactual(
  cfId: string
): Promise<CounterfactualContract> {
  return fetchJSON(`/api/v1/banking/decisions/counterfactuals/${cfId}`, {
    method: "GET",
  });
}

// ─── Propagation Operations ───────────────────────────────────────────────

/** List propagation contracts with optional filtering */
export async function fetchPropagations(params?: {
  scenario_id?: string;
  from_entity_id?: string;
  to_entity_id?: string;
  breakable_only?: boolean;
  limit?: number;
  offset?: number;
}): Promise<PropagationContract[]> {
  const qs = params
    ? "?" + new URLSearchParams(
        Object.entries(params)
          .filter(([, v]) => v !== undefined)
          .map(([k, v]) => [k, String(v)])
      ).toString()
    : "";
  return fetchJSON(`/api/v1/banking/decisions/propagations${qs}`, {
    method: "GET",
  });
}

/** Create a propagation contract */
export async function createPropagation(
  data: Record<string, unknown>
): Promise<PropagationContract> {
  return fetchJSON(`/api/v1/banking/decisions/propagations`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Get a single propagation contract */
export async function fetchPropagation(
  propId: string
): Promise<PropagationContract> {
  return fetchJSON(`/api/v1/banking/decisions/propagations/${propId}`, {
    method: "GET",
  });
}

// ─── Outcome Review Operations ────────────────────────────────────────────

/** Create an outcome review */
export async function createOutcomeReview(
  data: Record<string, unknown>
): Promise<OutcomeReviewContract> {
  return fetchJSON(`/api/v1/banking/decisions/outcome-reviews`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Get an outcome review */
export async function fetchOutcomeReview(
  reviewId: string
): Promise<OutcomeReviewContract> {
  return fetchJSON(`/api/v1/banking/decisions/outcome-reviews/${reviewId}`, {
    method: "GET",
  });
}

// ─── Value Audit Operations ───────────────────────────────────────────────

/** Create a value audit */
export async function createValueAudit(
  data: Record<string, unknown>
): Promise<DecisionValueAudit> {
  return fetchJSON(`/api/v1/banking/decisions/value-audits`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

/** Get a value audit */
export async function fetchValueAudit(
  auditId: string
): Promise<DecisionValueAudit> {
  return fetchJSON(`/api/v1/banking/decisions/value-audits/${auditId}`, {
    method: "GET",
  });
}
