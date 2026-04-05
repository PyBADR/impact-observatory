/**
 * Impact Observatory | مرصد الأثر — API Client (unified pipeline)
 *
 * 3 endpoints only:
 *   POST /api/v1/runs          → Launch unified pipeline (13 stages)
 *   GET  /api/v1/runs/{id}     → Full UnifiedRunResult
 *   GET  /api/v1/runs/{id}/status → Poll run status
 *   GET  /api/v1/scenarios     → Scenario catalog
 *
 * All section-fetch endpoints removed — unified payload replaces them.
 */

const BASE = "";
const API_KEY = process.env.NEXT_PUBLIC_IO_API_KEY || "io_master_key_2026";

function apiErrorMessage(status: number): string {
  if (status === 422) return "The request could not be processed. Please verify the inputs and try again.";
  if (status === 404) return "The requested resource was not found. Please refresh or try a different selection.";
  if (status === 401 || status === 403) return "Access to this resource is restricted. Please contact your administrator.";
  if (status >= 500) return "The analysis service is temporarily unavailable. Please try again in a moment.";
  return "An unexpected error occurred. Please try again.";
}

async function fetchJSON<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      "X-IO-API-Key": API_KEY,
      ...init?.headers,
    },
  });
  if (!res.ok) {
    throw new Error(apiErrorMessage(res.status));
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => fetchJSON<{ status: string }>("/health"),

  signals: {
    /** POST /api/v1/signals — Submit a raw signal → returns pending ScenarioSeed (202) */
    ingest: (raw: Record<string, unknown>) =>
      fetchJSON<import("@/types/observatory").IngestSignalResponse>("/api/v1/signals", {
        method: "POST",
        body: JSON.stringify(raw),
      }),

    /** GET /api/v1/signals/pending — List all seeds awaiting HITL review */
    listPending: () =>
      fetchJSON<import("@/types/observatory").SeedListResponse>("/api/v1/signals/pending"),

    /** GET /api/v1/signals/seeds/{seedId} — Get a seed by ID */
    getSeed: (seedId: string) =>
      fetchJSON<import("@/types/observatory").ScenarioSeed>(`/api/v1/signals/seeds/${seedId}`),

    /** POST /api/v1/signals/seeds/{seedId}/approve — Approve → triggers pipeline */
    approve: (seedId: string, reason?: string, reviewedBy?: string) =>
      fetchJSON<import("@/types/observatory").ApproveSeedResponse>(
        `/api/v1/signals/seeds/${seedId}/approve`,
        {
          method: "POST",
          body: JSON.stringify({ reason: reason ?? null, reviewed_by: reviewedBy ?? null }),
        }
      ),

    /** POST /api/v1/signals/seeds/{seedId}/reject — Reject → no pipeline */
    reject: (seedId: string, reason?: string, reviewedBy?: string) =>
      fetchJSON<import("@/types/observatory").RejectSeedResponse>(
        `/api/v1/signals/seeds/${seedId}/reject`,
        {
          method: "POST",
          body: JSON.stringify({ reason: reason ?? null, reviewed_by: reviewedBy ?? null }),
        }
      ),
  },

  outcomes: {
    /** GET /api/v1/outcomes — List outcomes, optionally filtered */
    list: (params?: { decision_id?: string; run_id?: string; status?: string; limit?: number }) => {
      const qs = new URLSearchParams();
      if (params?.decision_id) qs.set("decision_id", params.decision_id);
      if (params?.run_id) qs.set("run_id", params.run_id);
      if (params?.status) qs.set("status", params.status);
      if (params?.limit != null) qs.set("limit", String(params.limit));
      const q = qs.toString();
      return fetchJSON<import("@/types/observatory").OutcomeListResponse>(
        `/api/v1/outcomes${q ? `?${q}` : ""}`
      );
    },

    /** GET /api/v1/outcomes/{id} — Get outcome by ID */
    get: (outcomeId: string) =>
      fetchJSON<import("@/types/observatory").Outcome>(`/api/v1/outcomes/${outcomeId}`),

    /** POST /api/v1/outcomes — Record a new outcome */
    create: (body: import("@/types/observatory").CreateOutcomeRequest) =>
      fetchJSON<import("@/types/observatory").Outcome>("/api/v1/outcomes", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    /** POST /api/v1/outcomes/{id}/observe — Observe an outcome */
    observe: (outcomeId: string, body?: import("@/types/observatory").ObserveOutcomeRequest) =>
      fetchJSON<import("@/types/observatory").Outcome>(
        `/api/v1/outcomes/${outcomeId}/observe`,
        { method: "POST", body: JSON.stringify(body ?? {}) }
      ),

    /** POST /api/v1/outcomes/{id}/confirm — Confirm with classification */
    confirm: (outcomeId: string, body: import("@/types/observatory").ConfirmOutcomeRequest) =>
      fetchJSON<import("@/types/observatory").Outcome>(
        `/api/v1/outcomes/${outcomeId}/confirm`,
        { method: "POST", body: JSON.stringify(body) }
      ),

    /** POST /api/v1/outcomes/{id}/dispute — Dispute an outcome observation */
    dispute: (outcomeId: string, body: import("@/types/observatory").DisputeOutcomeRequest) =>
      fetchJSON<import("@/types/observatory").Outcome>(
        `/api/v1/outcomes/${outcomeId}/dispute`,
        { method: "POST", body: JSON.stringify(body) }
      ),

    /** POST /api/v1/outcomes/{id}/close — Close an outcome (terminal) */
    close: (outcomeId: string, body?: import("@/types/observatory").CloseOutcomeRequest) =>
      fetchJSON<import("@/types/observatory").Outcome>(
        `/api/v1/outcomes/${outcomeId}/close`,
        { method: "POST", body: JSON.stringify(body ?? {}) }
      ),
  },

  decisions: {
    /** GET /api/v1/decisions — List operator decisions */
    list: (params?: { status?: string; decision_type?: string; limit?: number }) => {
      const qs = new URLSearchParams();
      if (params?.status) qs.set("status", params.status);
      if (params?.decision_type) qs.set("decision_type", params.decision_type);
      if (params?.limit != null) qs.set("limit", String(params.limit));
      const q = qs.toString();
      return fetchJSON<import("@/types/observatory").DecisionListResponse>(
        `/api/v1/decisions${q ? `?${q}` : ""}`
      );
    },

    /** GET /api/v1/decisions/{id} — Get decision by ID */
    get: (decisionId: string) =>
      fetchJSON<import("@/types/observatory").OperatorDecision>(`/api/v1/decisions/${decisionId}`),

    /** POST /api/v1/decisions — Create a new decision */
    create: (body: import("@/types/observatory").CreateDecisionRequest) =>
      fetchJSON<import("@/types/observatory").OperatorDecision>("/api/v1/decisions", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    /** POST /api/v1/decisions/{id}/execute — Execute a decision */
    execute: (decisionId: string, body?: import("@/types/observatory").ExecuteDecisionRequest) =>
      fetchJSON<import("@/types/observatory").OperatorDecision>(
        `/api/v1/decisions/${decisionId}/execute`,
        { method: "POST", body: JSON.stringify(body ?? {}) }
      ),

    /** POST /api/v1/decisions/{id}/close — Close a decision */
    close: (decisionId: string, body?: import("@/types/observatory").CloseDecisionRequest) =>
      fetchJSON<import("@/types/observatory").OperatorDecision>(
        `/api/v1/decisions/${decisionId}/close`,
        { method: "POST", body: JSON.stringify(body ?? {}) }
      ),
  },

  values: {
    /** POST /api/v1/values/compute — Compute ROI from an existing Outcome (OPERATOR+) */
    compute: (body: import("@/types/observatory").ComputeValueRequest) =>
      fetchJSON<import("@/types/observatory").DecisionValue>("/api/v1/values/compute", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    /** POST /api/v1/values/{id}/recompute — Recompute with updated inputs, writes new row */
    recompute: (valueId: string, body: import("@/types/observatory").RecomputeValueRequest) =>
      fetchJSON<import("@/types/observatory").DecisionValue>(
        `/api/v1/values/${valueId}/recompute`,
        { method: "POST", body: JSON.stringify(body) }
      ),

    /** GET /api/v1/values — List values, optionally filtered (ANALYST+) */
    list: (params?: { outcome_id?: string; decision_id?: string; run_id?: string; limit?: number }) => {
      const qs = new URLSearchParams();
      if (params?.outcome_id)  qs.set("outcome_id",  params.outcome_id);
      if (params?.decision_id) qs.set("decision_id", params.decision_id);
      if (params?.run_id)      qs.set("run_id",       params.run_id);
      if (params?.limit != null) qs.set("limit", String(params.limit));
      const q = qs.toString();
      return fetchJSON<import("@/types/observatory").DecisionValueListResponse>(
        `/api/v1/values${q ? `?${q}` : ""}`
      );
    },

    /** GET /api/v1/values/{id} — Get value by ID (ANALYST+) */
    get: (valueId: string) =>
      fetchJSON<import("@/types/observatory").DecisionValue>(`/api/v1/values/${valueId}`),
  },

  observatory: {
    /** POST /api/v1/runs — Launch unified pipeline */
    run: (body: { template_id: string; severity?: number; horizon_hours?: number; label?: string }) =>
      fetchJSON<{ data: Record<string, unknown> }>("/api/v1/runs", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    /** GET /api/v1/runs/{id} — Full UnifiedRunResult */
    result: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}`),

    /** GET /api/v1/runs/{id}/status — Poll run status */
    status: (runId: string) =>
      fetchJSON<{ data: Record<string, unknown> }>(`/api/v1/runs/${runId}/status`),

    /** GET /api/v1/scenarios — Scenario catalog */
    scenarios: () =>
      fetchJSON<{ data: Record<string, unknown> }>("/api/v1/scenarios"),
  },

  /**
   * Decision Authority Layer — backend source of truth.
   * All actions produce stable authority envelope responses.
   * Errors: 400 (bad transition), 403 (unauthorized), 404 (not found), 409 (conflict).
   */
  authority: {
    /** POST /api/v1/authority/propose — Create authority envelope (PROPOSED) */
    propose: (body: {
      decision_id: string;
      rationale?: string;
      priority?: number;
      source_run_id?: string;
      source_scenario_label?: string;
      tags?: string[];
      notes?: string;
      actor_id?: string;
    }) =>
      fetchJSON<Record<string, unknown>>("/api/v1/authority/propose", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    /** POST /api/v1/authority/{id}/submit — Submit for review */
    submit: (decisionId: string, body?: { reviewer_id?: string; notes?: string; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/submit`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    /** POST /api/v1/authority/{id}/approve — Approve (ADMIN) */
    approve: (decisionId: string, body?: { rationale?: string; notes?: string; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/approve`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    /** POST /api/v1/authority/{id}/reject — Reject (ADMIN) */
    reject: (decisionId: string, body?: { rationale?: string; notes?: string; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/reject`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    /** POST /api/v1/authority/{id}/return — Return for revision (ADMIN) */
    returnForRevision: (decisionId: string, body?: { rationale?: string; notes?: string; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/return`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    /** POST /api/v1/authority/{id}/escalate — Escalate (OPERATOR+) */
    escalate: (decisionId: string, body?: { notes?: string; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/escalate`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    /** POST /api/v1/authority/{id}/queue-execution — Queue for execution (OPERATOR+) */
    queueExecution: (decisionId: string, body?: { notes?: string; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/queue-execution`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    /** POST /api/v1/authority/{id}/execute — Execute (OPERATOR+). Requires APPROVED/EXECUTION_PENDING. */
    execute: (decisionId: string, body?: {
      execution_result?: string;
      linked_outcome_id?: string;
      linked_value_id?: string;
      notes?: string;
      actor_id?: string;
    }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/execute`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    /** POST /api/v1/authority/{id}/execution-failed — Report execution failure */
    executionFailed: (decisionId: string, body?: { failure_reason?: string; notes?: string; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/execution-failed`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    /** POST /api/v1/authority/{id}/revoke — Revoke (ADMIN) */
    revoke: (decisionId: string, body?: { rationale?: string; notes?: string; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/revoke`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    /** POST /api/v1/authority/{id}/withdraw — Withdraw (ANALYST+) */
    withdraw: (decisionId: string, body?: { notes?: string; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/withdraw`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    /** POST /api/v1/authority/{id}/resubmit — Resubmit after rejection/return/failure */
    resubmit: (decisionId: string, body?: { rationale?: string; notes?: string; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/resubmit`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    /** POST /api/v1/authority/{id}/override — Admin force-transition */
    override: (decisionId: string, body: { target_status: string; rationale: string; notes?: string; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/override`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    /** POST /api/v1/authority/{id}/annotate — Append annotation (no status change) */
    annotate: (decisionId: string, body: { notes: string; metadata?: Record<string, unknown>; actor_id?: string }) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/annotate`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    /** GET /api/v1/authority — List authority envelopes */
    list: (params?: { status?: string; limit?: number; offset?: number }) => {
      const qs = new URLSearchParams();
      if (params?.status) qs.set("status", params.status);
      if (params?.limit != null) qs.set("limit", String(params.limit));
      if (params?.offset != null) qs.set("offset", String(params.offset));
      const q = qs.toString();
      return fetchJSON<{ items: Record<string, unknown>[]; count: number }>(
        `/api/v1/authority${q ? `?${q}` : ""}`
      );
    },

    /** GET /api/v1/authority/{decision_id} — Get authority envelope */
    get: (decisionId: string) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}`),

    /** GET /api/v1/authority/{decision_id}/events — Full audit event log */
    events: (decisionId: string, limit?: number) => {
      const q = limit != null ? `?limit=${limit}` : "";
      return fetchJSON<{ events: Record<string, unknown>[]; count: number }>(
        `/api/v1/authority/${decisionId}/events${q}`
      );
    },

    /** POST /api/v1/authority/{id}/link — Attach outcome/value links (backend-authoritative) */
    link: (decisionId: string, body: Record<string, unknown>) =>
      fetchJSON<Record<string, unknown>>(`/api/v1/authority/${decisionId}/link`, {
        method: "POST", body: JSON.stringify(body),
      }),

    /** GET /api/v1/authority/{decision_id}/verify — Verify hash chain integrity */
    verify: (decisionId: string) =>
      fetchJSON<{
        valid: boolean;
        broken_at: number | null;
        expected_hash: string | null;
        actual_hash: string | null;
        events_checked: number;
        authority_id: string;
        chain_trace: Array<{
          index: number;
          event_id: string;
          action: string;
          from_status: string | null;
          to_status: string;
          timestamp: string;
          event_hash: string;
          previous_event_hash: string | null;
          recomputed_hash: string;
          link_valid: boolean;
          hash_valid: boolean;
        }>;
        errors: unknown[];
      }>(
        `/api/v1/authority/${decisionId}/verify`
      ),

    /** GET /api/v1/authority/metrics — Authoritative queue metrics (backend source of truth) */
    metrics: () =>
      fetchJSON<{
        proposed: number;
        under_review: number;
        approved_pending_execution: number;
        executed: number;
        rejected: number;
        failed: number;
        escalated: number;
        returned: number;
        revoked: number;
        withdrawn: number;
        total_active: number;
        total: number;
      }>("/api/v1/authority/metrics"),
  },
};
