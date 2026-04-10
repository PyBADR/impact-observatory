/**
 * Impact Observatory | مرصد الأثر — In-Memory Server Store
 *
 * Module-level Maps that persist across Next.js API route requests in the same
 * Node.js process (dev server or non-serverless production). Used as a fallback
 * data layer when the Python backend OperatorDecision / Outcome / DecisionValue /
 * Authority endpoints are not registered.
 *
 * Shape rules: every record mirrors the Python backend response shape exactly so
 * that the existing frontend mapper functions (rawToAuthority, etc.) work as-is.
 */

import { emitAudit } from "@/lib/audit";

// ── Utility ───────────────────────────────────────────────────────────────────

function uid(): string {
  const ts = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 9);
  return `${ts}_${rand}`;
}

function isoNow(): string {
  return new Date().toISOString();
}

function classifyValue(net: number): string {
  if (net >= 1_000_000)  return "HIGH_VALUE";
  if (net > 0)           return "POSITIVE_VALUE";
  if (net >= -1_000_000) return "NEGATIVE_VALUE";
  return "LOSS_INDUCING";
}

// ── StoredDecision — mirrors OperatorDecision backend shape ──────────────────

export interface StoredDecision {
  decision_id:      string;
  source_signal_id: string | null;
  source_seed_id:   string | null;
  source_run_id:    string | null;
  scenario_id:      string | null;
  decision_type:    string;
  decision_status:  string;
  decision_payload: Record<string, unknown>;
  rationale:        string | null;
  confidence_score: number | null;
  created_by:       string;
  outcome_status:   string;
  outcome_payload:  Record<string, unknown>;
  outcome_id:       string | null;
  created_at:       string;
  updated_at:       string;
  closed_at:        string | null;
}

const _decisions = new Map<string, StoredDecision>();

// ── StoredAuthority — mirrors backend DecisionAuthority response shape ────────
// Fields named to match rawToAuthority() expectations in authority-store.ts

export interface StoredAuthorityEvent {
  event_id:             string;
  authority_id:         string;
  decision_id:          string;
  action:               string;
  from_status:          string | null;
  to_status:            string;
  actor_id:             string;
  actor_role:           string;
  timestamp:            string;
  notes:                string | null;
  metadata:             Record<string, unknown>;
  event_hash:           string;
  previous_event_hash:  string | null;
}

export interface StoredAuthority {
  authority_id:          string;
  decision_id:           string;
  authority_status:      string;
  proposed_by:           string;
  proposed_by_role:      string;
  proposal_rationale:    string | null;
  reviewer_id:           string | null;
  reviewer_role:         string | null;
  review_started_at:     string | null;
  authority_actor_id:    string | null;
  authority_actor_role:  string | null;
  authority_decided_at:  string | null;
  authority_rationale:   string | null;
  executed_by:           string | null;
  executed_by_role:      string | null;
  executed_at:           string | null;
  execution_result:      string | null;
  linked_outcome_id:     string | null;
  linked_value_id:       string | null;
  priority:              number;
  revision_number:       number;
  escalation_level:      number;
  tags:                  string[];
  created_at:            string;
  updated_at:            string;
  _events:               StoredAuthorityEvent[];
}

const _authority = new Map<string, StoredAuthority>();
// decision_id → authority_id index
const _authDecisionIdx = new Map<string, string>();

// ── StoredOutcome — mirrors Outcome backend shape ──────────────────────────────

export interface StoredOutcome {
  outcome_id:                  string;
  source_decision_id:          string | null;
  source_run_id:               string | null;
  source_signal_id:            string | null;
  source_seed_id:              string | null;
  outcome_status:              string;
  outcome_classification:      string | null;
  observed_at:                 string | null;
  recorded_at:                 string;
  updated_at:                  string;
  closed_at:                   string | null;
  recorded_by:                 string;
  expected_value:              number | null;
  realized_value:              number | null;
  error_flag:                  boolean;
  time_to_resolution_seconds:  number | null;
  evidence_payload:            Record<string, unknown>;
  notes:                       string | null;
}

const _outcomes = new Map<string, StoredOutcome>();

// ── StoredValue — mirrors DecisionValue backend shape ─────────────────────────

export interface StoredValue {
  value_id:               string;
  source_outcome_id:      string;
  source_decision_id:     string | null;
  source_run_id:          string | null;
  computed_at:            string;
  computed_by:            string;
  expected_value:         number | null;
  realized_value:         number | null;
  avoided_loss:           number;
  operational_cost:       number;
  decision_cost:          number;
  latency_cost:           number;
  total_cost:             number;
  net_value:              number;
  value_confidence_score: number;
  value_classification:   string;
  calculation_trace:      Record<string, unknown>;
  notes:                  string | null;
}

const _values = new Map<string, StoredValue>();

// ── Internal factory helpers ──────────────────────────────────────────────────

function _makeAuthority(decisionId: string, runId: string | null, sector?: string): StoredAuthority {
  const id   = `auth_${uid()}`;
  const now  = isoNow();
  const evt: StoredAuthorityEvent = {
    event_id:            `evt_${uid()}`,
    authority_id:        id,
    decision_id:         decisionId,
    action:              "propose",
    from_status:         null,
    to_status:           "PROPOSED",
    actor_id:            "system",
    actor_role:          "ANALYST",
    timestamp:           now,
    notes:               sector ? `Auto-proposed for ${sector} sector action` : null,
    metadata:            {},
    event_hash:          Math.random().toString(36).slice(2),
    previous_event_hash: null,
  };
  const auth: StoredAuthority = {
    authority_id:         id,
    decision_id:          decisionId,
    authority_status:     "PROPOSED",
    proposed_by:          "system",
    proposed_by_role:     "ANALYST",
    proposal_rationale:   null,
    reviewer_id:          null,
    reviewer_role:        null,
    review_started_at:    null,
    authority_actor_id:   null,
    authority_actor_role: null,
    authority_decided_at: null,
    authority_rationale:  null,
    executed_by:          null,
    executed_by_role:     null,
    executed_at:          null,
    execution_result:     null,
    linked_outcome_id:    null,
    linked_value_id:      null,
    priority:             3,
    revision_number:      1,
    escalation_level:     0,
    tags:                 sector ? [sector] : [],
    created_at:           now,
    updated_at:           now,
    _events:              [evt],
  };
  _authority.set(id, auth);
  _authDecisionIdx.set(decisionId, id);

  emitAudit({
    event_type:  "authority_item_created",
    entity_id:   id,
    run_id:      runId,
    actor:       "system",
    details: {
      authority_status: "PROPOSED",
      priority:         auth.priority,
      sector:           sector ?? null,
      decision_id:      decisionId,
    },
    lineage_ref: decisionId,
  });

  return auth;
}

function _makeOutcome(decisionId: string, runId: string | null, expectedValue: number): StoredOutcome {
  const id  = `out_${uid()}`;
  const now = isoNow();
  const out: StoredOutcome = {
    outcome_id:                 id,
    source_decision_id:         decisionId,
    source_run_id:              runId,
    source_signal_id:           null,
    source_seed_id:             null,
    outcome_status:             "PENDING_OBSERVATION",
    outcome_classification:     null,
    observed_at:                null,
    recorded_at:                now,
    updated_at:                 now,
    closed_at:                  null,
    recorded_by:                "system",
    expected_value:             expectedValue > 0 ? expectedValue : null,
    realized_value:             null,
    error_flag:                 false,
    time_to_resolution_seconds: null,
    evidence_payload:           {},
    notes:                      null,
  };
  _outcomes.set(id, out);

  emitAudit({
    event_type:  "outcome_derived",
    entity_id:   id,
    run_id:      runId,
    actor:       "system",
    details: {
      outcome_status: "PENDING_OBSERVATION",
      expected_value: out.expected_value,
      source_decision_id: decisionId,
    },
    lineage_ref: decisionId,
  });

  return out;
}

function _makeValue(
  outcomeId: string,
  decisionId: string | null,
  runId: string | null,
  avoidedLoss: number,
  cost: number,
  confidence: number,
): StoredValue {
  const id        = `val_${uid()}`;
  const opCost    = cost * 0.6;
  const decCost   = cost * 0.3;
  const latCost   = cost * 0.1;
  const totalCost = opCost + decCost + latCost;
  const netValue  = avoidedLoss - totalCost;
  const val: StoredValue = {
    value_id:               id,
    source_outcome_id:      outcomeId,
    source_decision_id:     decisionId,
    source_run_id:          runId,
    computed_at:            isoNow(),
    computed_by:            "system",
    expected_value:         avoidedLoss > 0 ? avoidedLoss : null,
    realized_value:         null,
    avoided_loss:           avoidedLoss,
    operational_cost:       opCost,
    decision_cost:          decCost,
    latency_cost:           latCost,
    total_cost:             totalCost,
    net_value:              netValue,
    value_confidence_score: confidence,
    value_classification:   classifyValue(netValue),
    calculation_trace: {
      avoided_loss:      avoidedLoss,
      operational_cost:  opCost,
      decision_cost:     decCost,
      latency_cost:      latCost,
      total_cost:        totalCost,
    },
    notes: null,
  };
  _values.set(id, val);

  emitAudit({
    event_type:  "value_computed",
    entity_id:   id,
    run_id:      runId,
    actor:       "system",
    details: {
      net_value:              val.net_value,
      avoided_loss:           val.avoided_loss,
      total_cost:             val.total_cost,
      value_classification:   val.value_classification,
      value_confidence_score: val.value_confidence_score,
      source_outcome_id:      outcomeId,
      source_decision_id:     decisionId,
    },
    lineage_ref: outcomeId,
  });

  return val;
}

// ── Public serverStore API ────────────────────────────────────────────────────

export const serverStore = {

  // ── Decisions ──────────────────────────────────────────────────────────────

  decisions: {
    list(params?: { status?: string; decision_type?: string; run_id?: string; limit?: number }): StoredDecision[] {
      let items = Array.from(_decisions.values()).reverse(); // newest first
      if (params?.status)        items = items.filter((d) => d.decision_status === params.status);
      if (params?.decision_type) items = items.filter((d) => d.decision_type   === params.decision_type);
      if (params?.run_id)        items = items.filter((d) => d.source_run_id   === params.run_id);
      if (params?.limit != null) items = items.slice(0, params.limit);
      return items;
    },

    get(id: string): StoredDecision | undefined {
      return _decisions.get(id);
    },

    /**
     * Create an OperatorDecision and auto-create authority envelope + outcome + value.
     * This is the single-call entry point for run-result auto-seeding.
     */
    create(body: {
      decision_type?:    string;
      source_run_id?:    string | null;
      scenario_id?:      string | null;
      source_signal_id?: string | null;
      source_seed_id?:   string | null;
      decision_payload?: Record<string, unknown>;
      rationale?:        string | null;
      confidence_score?: number | null;
      created_by?:       string | null;
    }): StoredDecision {
      const id  = `dec_${uid()}`;
      const now = isoNow();
      const dec: StoredDecision = {
        decision_id:      id,
        source_signal_id: body.source_signal_id ?? null,
        source_seed_id:   body.source_seed_id   ?? null,
        source_run_id:    body.source_run_id     ?? null,
        scenario_id:      body.scenario_id       ?? null,
        decision_type:    body.decision_type     ?? "APPROVE_ACTION",
        decision_status:  "CREATED",
        decision_payload: body.decision_payload  ?? {},
        rationale:        body.rationale         ?? null,
        confidence_score: body.confidence_score  ?? null,
        created_by:       body.created_by        ?? "system",
        outcome_status:   "PENDING",
        outcome_payload:  {},
        outcome_id:       null,
        created_at:       now,
        updated_at:       now,
        closed_at:        null,
      };
      _decisions.set(id, dec);

      emitAudit({
        event_type:  "decision_created",
        entity_id:   id,
        run_id:      body.source_run_id ?? null,
        actor:       dec.created_by,
        details: {
          decision_type:    dec.decision_type,
          confidence_score: dec.confidence_score,
          source_signal_id: dec.source_signal_id,
          source_seed_id:   dec.source_seed_id,
        },
        lineage_ref: null,
      });

      // Derive financial data from payload
      const payload     = body.decision_payload ?? {};
      const sector      = (payload.sector     as string)  ?? undefined;
      const avoidedLoss = (payload.loss_avoided_usd as number) ?? 0;
      const cost        = (payload.cost_usd   as number)  ?? 0;
      const confidence  = body.confidence_score ?? 0.70;

      // Auto-create authority envelope
      _makeAuthority(id, body.source_run_id ?? null, sector);

      // Auto-create pending outcome
      const outcome = _makeOutcome(id, body.source_run_id ?? null, avoidedLoss);

      // Bidirectional linkage: write outcome_id back to decision
      dec.outcome_id = outcome.outcome_id;

      // Auto-compute value when we have financial data
      if (avoidedLoss > 0 || cost > 0) {
        _makeValue(outcome.outcome_id, id, body.source_run_id ?? null, avoidedLoss, cost, confidence);
      }

      return dec;
    },

    /**
     * Transition decision to EXECUTED status (mirrors backend execute endpoint).
     * Guards: status must be CREATED or IN_REVIEW.
     */
    execute(id: string): StoredDecision | null {
      const dec = _decisions.get(id);
      if (!dec) {
        console.warn("[server-store] execute: decision not found", id);
        return null;
      }
      if (!["CREATED", "IN_REVIEW"].includes(dec.decision_status)) {
        console.warn("[server-store] execute: invalid status", dec.decision_status);
        return null;
      }
      dec.decision_status = "EXECUTED";
      dec.outcome_status  = "SUCCESS";
      dec.updated_at      = new Date().toISOString();
      return dec;
    },

    /**
     * Transition decision to CLOSED status (mirrors backend close endpoint).
     * Guards: must not already be CLOSED.
     */
    close(id: string): StoredDecision | null {
      const dec = _decisions.get(id);
      if (!dec) {
        console.warn("[server-store] close: decision not found", id);
        return null;
      }
      if (dec.decision_status === "CLOSED") {
        console.warn("[server-store] close: already closed", id);
        return null;
      }
      const now = new Date().toISOString();
      dec.decision_status = "CLOSED";
      dec.closed_at       = now;
      dec.updated_at      = now;
      return dec;
    },

    count(): number {
      return _decisions.size;
    },

    clear(): void {
      _decisions.clear();
      _authority.clear();
      _authDecisionIdx.clear();
      _outcomes.clear();
      _values.clear();
    },
  },

  // ── Authority ──────────────────────────────────────────────────────────────

  authority: {
    list(params?: { status?: string; limit?: number; offset?: number }): StoredAuthority[] {
      let items  = Array.from(_authority.values()).reverse();
      if (params?.status) items = items.filter((a) => a.authority_status === params.status);
      const offset = params?.offset ?? 0;
      const limit  = params?.limit  ?? 200;
      return items.slice(offset, offset + limit);
    },

    get(decisionId: string): StoredAuthority | undefined {
      const authId = _authDecisionIdx.get(decisionId);
      return authId ? _authority.get(authId) : undefined;
    },

    getById(authorityId: string): StoredAuthority | undefined {
      return _authority.get(authorityId);
    },

    events(decisionId: string): StoredAuthorityEvent[] {
      const auth = serverStore.authority.get(decisionId);
      return auth?._events ?? [];
    },

    metrics(): Record<string, number> {
      const items = Array.from(_authority.values());
      const countStatus = (s: string) => items.filter((a) => a.authority_status === s).length;
      return {
        proposed:                    countStatus("PROPOSED"),
        under_review:                countStatus("UNDER_REVIEW"),
        approved_pending_execution:
          countStatus("APPROVED") + countStatus("EXECUTION_PENDING"),
        executed:                    countStatus("EXECUTED"),
        rejected:                    countStatus("REJECTED"),
        failed:                      countStatus("EXECUTION_FAILED"),
        escalated:                   countStatus("ESCALATED"),
        returned:                    countStatus("RETURNED"),
        revoked:                     countStatus("REVOKED"),
        withdrawn:                   countStatus("WITHDRAWN"),
        total_active: items.filter(
          (a) => !["EXECUTED", "REJECTED", "REVOKED", "WITHDRAWN", "EXECUTION_FAILED"].includes(a.authority_status),
        ).length,
        total: items.length,
        overdue: 0,
      };
    },
  },

  // ── Outcomes ───────────────────────────────────────────────────────────────

  outcomes: {
    list(params?: {
      decision_id?: string;
      run_id?:      string;
      status?:      string;
      limit?:       number;
    }): StoredOutcome[] {
      let items = Array.from(_outcomes.values()).reverse();
      if (params?.decision_id) items = items.filter((o) => o.source_decision_id === params.decision_id);
      if (params?.run_id)      items = items.filter((o) => o.source_run_id       === params.run_id);
      if (params?.status)      items = items.filter((o) => o.outcome_status       === params.status);
      if (params?.limit != null) items = items.slice(0, params.limit);
      return items;
    },

    get(id: string): StoredOutcome | undefined {
      return _outcomes.get(id);
    },

    create(body: {
      source_decision_id?:     string | null;
      source_run_id?:          string | null;
      source_signal_id?:       string | null;
      source_seed_id?:         string | null;
      outcome_classification?: string | null;
      expected_value?:         number | null;
      realized_value?:         number | null;
      evidence_payload?:       Record<string, unknown>;
      notes?:                  string | null;
      recorded_by?:            string | null;
    }): StoredOutcome {
      return _makeOutcome(
        body.source_decision_id ?? `anon_${uid()}`,
        body.source_run_id ?? null,
        body.expected_value ?? 0,
      );
    },
  },

  // ── Decision Values ────────────────────────────────────────────────────────

  values: {
    list(params?: {
      outcome_id?:  string;
      decision_id?: string;
      run_id?:      string;
      limit?:       number;
    }): StoredValue[] {
      let items = Array.from(_values.values()).reverse();
      if (params?.outcome_id)  items = items.filter((v) => v.source_outcome_id  === params.outcome_id);
      if (params?.decision_id) items = items.filter((v) => v.source_decision_id === params.decision_id);
      if (params?.run_id)      items = items.filter((v) => v.source_run_id       === params.run_id);
      if (params?.limit != null) items = items.slice(0, params.limit);
      return items;
    },

    get(id: string): StoredValue | undefined {
      return _values.get(id);
    },

    compute(body: {
      source_outcome_id: string;
      avoided_loss?:     number | null;
      operational_cost?: number;
      decision_cost?:    number;
      latency_cost?:     number;
      notes?:            string | null;
      computed_by?:      string | null;
    }): StoredValue {
      const outcome    = _outcomes.get(body.source_outcome_id);
      const avoidedLoss = body.avoided_loss ?? outcome?.expected_value ?? 0;
      const opCost     = body.operational_cost ?? 0;
      const decCost    = body.decision_cost    ?? 0;
      const latCost    = body.latency_cost     ?? 0;
      const totalCost  = opCost + decCost + latCost;
      const netValue   = avoidedLoss - totalCost;

      const id         = `val_${uid()}`;
      const val: StoredValue = {
        value_id:               id,
        source_outcome_id:      body.source_outcome_id,
        source_decision_id:     outcome?.source_decision_id ?? null,
        source_run_id:          outcome?.source_run_id      ?? null,
        computed_at:            isoNow(),
        computed_by:            body.computed_by ?? "operator",
        expected_value:         avoidedLoss > 0 ? avoidedLoss : null,
        realized_value:         null,
        avoided_loss:           avoidedLoss,
        operational_cost:       opCost,
        decision_cost:          decCost,
        latency_cost:           latCost,
        total_cost:             totalCost,
        net_value:              netValue,
        value_confidence_score: 0.75,
        value_classification:   classifyValue(netValue),
        calculation_trace: {
          avoided_loss:     avoidedLoss,
          operational_cost: opCost,
          decision_cost:    decCost,
          latency_cost:     latCost,
          total_cost:       totalCost,
        },
        notes: body.notes ?? null,
      };
      _values.set(id, val);
      return val;
    },
  },
};
