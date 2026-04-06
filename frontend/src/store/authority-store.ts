/**
 * Impact Observatory | مرصد الأثر — Decision Authority Layer Store
 *
 * Backend-backed Zustand store. The backend is the single source of truth.
 * All authority mutations call the API first; the store is a read cache.
 *
 * Responsibilities:
 *   1. Async API dispatch for all authority lifecycle actions
 *   2. Response upsert (backend dict → DecisionAuthority / AuthorityEvent)
 *   3. Field mapping (backend lowercase roles → frontend uppercase AuthorityActor)
 *   4. Queue management for persona-specific surfaces
 *   5. Loading / error state for UI feedback
 *
 * Design rules:
 *   - No optimistic updates — wait for backend response before mutating store
 *   - Every action that changes state calls the backend first, then upserts
 *   - auditLog is now events: Map<authority_id, AuthorityEvent[]>
 *   - loadAll() must be called on mount to hydrate the store
 */

import { create } from "zustand";
import { api } from "@/lib/api";
import type {
  AuthorityStatus,
  AuthorityActor,
  AuthorityAction,
  DecisionAuthority,
  AuthorityEvent,
  AuthorityQueueSummary,
  AuthorityQueueItem,
} from "@/types/authority";
import {
  AUTHORITY_TRANSITIONS,
  AUTHORITY_PERMISSIONS,
  TERMINAL_AUTHORITY_STATES,
} from "@/types/authority";

// ─── Re-exported for consumers that import from here ─────────────────────────

export class AuthorityTransitionError extends Error {
  constructor(
    public readonly decision_id: string,
    public readonly from: AuthorityStatus,
    public readonly to: AuthorityStatus,
    public readonly reason: string,
  ) {
    super(`Authority transition blocked: ${from} → ${to} for decision ${decision_id}. ${reason}`);
    this.name = "AuthorityTransitionError";
  }
}

export class AuthorityPermissionError extends Error {
  constructor(
    public readonly action: AuthorityAction,
    public readonly actor_role: AuthorityActor,
  ) {
    super(`Permission denied: role ${actor_role} cannot perform ${action}`);
    this.name = "AuthorityPermissionError";
  }
}

// ─── Backend response → frontend type mapping ─────────────────────────────────

function toRole(r: unknown): AuthorityActor | null {
  if (!r) return null;
  return String(r).toUpperCase() as AuthorityActor;
}

function rawToAuthority(raw: Record<string, unknown>): DecisionAuthority {
  return {
    authority_id:          String(raw.authority_id ?? ""),
    decision_id:           String(raw.decision_id ?? ""),
    authority_status:      raw.authority_status as AuthorityStatus,
    proposed_by:           String(raw.proposed_by ?? ""),
    proposed_by_role:      toRole(raw.proposed_by_role) ?? "ANALYST",
    // Backend has no dedicated proposed_at — use created_at
    proposed_at:           String(raw.created_at ?? raw.proposed_at ?? new Date().toISOString()),
    proposal_rationale:    (raw.proposal_rationale as string) ?? null,
    reviewer_id:           (raw.reviewer_id as string) ?? null,
    reviewer_role:         toRole(raw.reviewer_role),
    review_started_at:     (raw.review_started_at as string) ?? null,
    authority_actor_id:    (raw.authority_actor_id as string) ?? null,
    authority_actor_role:  toRole(raw.authority_actor_role),
    authority_decided_at:  (raw.authority_decided_at as string) ?? null,
    authority_rationale:   (raw.authority_rationale as string) ?? null,
    executed_by:           (raw.executed_by as string) ?? null,
    executed_by_role:      toRole(raw.executed_by_role),
    executed_at:           (raw.executed_at as string) ?? null,
    execution_result:      (raw.execution_result as string) ?? null,
    linked_outcome_id:     (raw.linked_outcome_id as string) ?? null,
    linked_value_id:       (raw.linked_value_id as string) ?? null,
    priority:              ((raw.priority as number) ?? 3) as 1 | 2 | 3 | 4 | 5,
    // Not tracked in backend — defaulted
    authority_deadline:    null,
    is_overdue:            false,
    revision_number:       (raw.revision_number as number) ?? 1,
    escalation_level:      (raw.escalation_level as number) ?? 0,
    tags:                  (raw.tags as string[]) ?? [],
    created_at:            String(raw.created_at ?? new Date().toISOString()),
    updated_at:            String(raw.updated_at ?? new Date().toISOString()),
  };
}

function rawToEvent(raw: Record<string, unknown>): AuthorityEvent {
  return {
    event_id:              String(raw.event_id ?? ""),
    authority_id:          String(raw.authority_id ?? ""),
    decision_id:           String(raw.decision_id ?? ""),
    action:                raw.action as AuthorityAction,
    from_status:           (raw.from_status as AuthorityStatus) ?? null,
    to_status:             raw.to_status as AuthorityStatus,
    actor_id:              String(raw.actor_id ?? ""),
    actor_role:            String(raw.actor_role ?? "").toUpperCase() as AuthorityActor,
    timestamp:             String(raw.timestamp ?? new Date().toISOString()),
    notes:                 (raw.notes as string) ?? null,
    metadata:              (raw.metadata as Record<string, unknown>) ?? {},
    event_hash:            String(raw.event_hash ?? ""),
    previous_event_hash:   (raw.previous_event_hash as string) ?? null,
  };
}

// ─── Store Interface ──────────────────────────────────────────────────────────

interface AuthorityState {
  /** All authority envelopes, keyed by authority_id */
  authorities: Map<string, DecisionAuthority>;
  /** Audit events keyed by authority_id, newest-first */
  events: Map<string, AuthorityEvent[]>;
  /** decision_id → authority_id index */
  decisionIndex: Map<string, string>;
  /** Loading flag (covers loadAll / action dispatch) */
  loading: boolean;
  /** Last error message (null = no error) */
  error: string | null;
  /** Backend-authoritative queue metrics (loaded via loadMetrics) */
  metrics: AuthorityQueueSummary | null;

  // ── Sync helpers ──
  upsertAuthority: (raw: Record<string, unknown>) => DecisionAuthority;
  upsertEvents: (authorityId: string, rawEvents: Record<string, unknown>[]) => void;

  // ── Load from backend ──
  loadAll: (params?: { status?: string; limit?: number }) => Promise<void>;
  loadByDecision: (decisionId: string) => Promise<void>;
  loadByAuthority: (authorityId: string) => Promise<void>;
  loadEvents: (decisionId: string) => Promise<void>;
  loadMetrics: () => Promise<void>;
  verifyChain: (decisionId: string) => Promise<{
    valid: boolean;
    broken_at: number | null;
    expected_hash: string | null;
    actual_hash: string | null;
    events_checked: number;
    chain_trace: unknown[];
    errors: unknown[];
  }>;

  // ── Authority Lifecycle Actions (all async, backend-first) ──

  propose: (params: {
    decision_id: string;
    proposed_by: string;
    proposed_by_role: AuthorityActor;
    rationale: string | null;
    priority?: 1 | 2 | 3 | 4 | 5;
    deadline?: string | null;
    tags?: string[];
    source_run_id?: string | null;
    source_scenario_label?: string | null;
    decision_type?: string;
  }) => Promise<DecisionAuthority>;

  submitForReview: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  approve: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    rationale: string;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  reject: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    rationale: string;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  returnForRevision: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    rationale: string;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  escalate: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    target_role: AuthorityActor;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  queueExecution: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  markExecuted: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    execution_result: string;
    linked_outcome_id?: string;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  reportExecutionFailure: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    failure_reason: string;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  revoke: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    rationale: string;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  withdraw: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  resubmit: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    rationale: string;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  override: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    override_to: AuthorityStatus;
    rationale: string;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  annotate: (params: {
    authority_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    notes: string;
  }) => Promise<void>;

  // ── Link Management (backend-authoritative) ──
  linkOutcome: (params: {
    authority_id: string;
    outcome_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    notes?: string;
  }) => Promise<DecisionAuthority>;
  linkValue: (params: {
    authority_id: string;
    value_id: string;
    actor_id: string;
    actor_role: AuthorityActor;
    notes?: string;
  }) => Promise<DecisionAuthority>;

  // ── Selectors ──
  getAuthority: (authority_id: string) => DecisionAuthority | null;
  getAuthorityByDecision: (decision_id: string) => DecisionAuthority | null;
  getAuditLog: (authority_id: string) => AuthorityEvent[];
  getByStatus: (status: AuthorityStatus) => DecisionAuthority[];
  getQueueSummary: () => AuthorityQueueSummary;
  getQueueForPersona: (persona: string) => AuthorityQueueItem[];
  canPerform: (authority_id: string, action: AuthorityAction, actor_role: AuthorityActor) => boolean;
}

// ─── Store Implementation ─────────────────────────────────────────────────────

export const useAuthorityStore = create<AuthorityState>((set, get) => {

  // ── Internal: resolve authority → decision_id for API calls ──
  function getDecisionId(authorityId: string): string {
    const auth = get().authorities.get(authorityId);
    if (!auth) throw new Error(`Authority ${authorityId} not found in store`);
    return auth.decision_id;
  }

  // ── Internal: upsert a raw backend response into the store ──
  function _upsert(raw: Record<string, unknown>): DecisionAuthority {
    const authority = rawToAuthority(raw);
    set((s) => {
      const newAuth = new Map(s.authorities);
      newAuth.set(authority.authority_id, authority);
      const newIndex = new Map(s.decisionIndex);
      newIndex.set(authority.decision_id, authority.authority_id);
      return { authorities: newAuth, decisionIndex: newIndex };
    });
    return authority;
  }

  return {
    authorities: new Map(),
    events: new Map(),
    decisionIndex: new Map(),
    loading: false,
    error: null,
    metrics: null,

    // ── Sync helpers ──

    upsertAuthority: (raw) => _upsert(raw),

    upsertEvents: (authorityId, rawEvents) => {
      const mapped = rawEvents.map(rawToEvent);
      // Sort newest-first
      mapped.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
      set((s) => {
        const newEvents = new Map(s.events);
        newEvents.set(authorityId, mapped);
        return { events: newEvents };
      });
    },

    // ── Load from backend ──

    loadAll: async (params) => {
      set({ loading: true, error: null });
      try {
        const response = await api.authority.list({
          status: params?.status,
          limit: params?.limit ?? 200,
        });
        for (const raw of (response?.items ?? [])) {
          _upsert(raw as Record<string, unknown>);
        }
        // Always load authoritative metrics on full hydration
        await get().loadMetrics();
      } catch (err) {
        set({ error: err instanceof Error ? err.message : String(err) });
      } finally {
        set({ loading: false });
      }
    },

    loadByDecision: async (decisionId) => {
      set({ loading: true, error: null });
      try {
        const raw = await api.authority.get(decisionId);
        _upsert(raw as Record<string, unknown>);
      } catch (err) {
        set({ error: err instanceof Error ? err.message : String(err) });
      } finally {
        set({ loading: false });
      }
    },

    loadByAuthority: async (authorityId) => {
      const auth = get().authorities.get(authorityId);
      if (!auth) return;
      await get().loadByDecision(auth.decision_id);
    },

    loadEvents: async (decisionId) => {
      try {
        const response = await api.authority.events(decisionId);
        const authorityId = get().decisionIndex.get(decisionId);
        if (authorityId) {
          get().upsertEvents(authorityId, response.events as Record<string, unknown>[]);
        } else {
          // Store by decision_id temporarily until we know authority_id
          const mapped = (response.events as Record<string, unknown>[]).map(rawToEvent);
          mapped.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
          // authority_id is on each event
          if (mapped.length > 0) {
            const aid = mapped[0].authority_id;
            set((s) => {
              const newEvents = new Map(s.events);
              newEvents.set(aid, mapped);
              return { events: newEvents };
            });
          }
        }
      } catch (err) {
        // Non-fatal: events load failure doesn't break the UI
        console.warn("[authority-store] loadEvents failed:", err);
      }
    },

    verifyChain: async (decisionId) => {
      return api.authority.verify(decisionId);
    },

    loadMetrics: async () => {
      try {
        const metrics = await api.authority.metrics();
        set({ metrics: metrics as unknown as AuthorityQueueSummary });
      } catch (err) {
        console.warn("[authority-store] loadMetrics failed:", err);
      }
    },

    // ── PROPOSE ──
    propose: async (params) => {
      set({ loading: true, error: null });
      try {
        const raw = await api.authority.propose({
          decision_id:           params.decision_id,
          rationale:             params.rationale ?? undefined,
          priority:              params.priority ?? 3,
          source_run_id:         params.source_run_id ?? undefined,
          source_scenario_label: params.source_scenario_label ?? undefined,
          tags:                  params.tags,
          actor_id:              params.proposed_by,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── SUBMIT_FOR_REVIEW ──
    submitForReview: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.submit(decisionId, {
          notes:    params.notes,
          actor_id: params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── APPROVE ──
    approve: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.approve(decisionId, {
          rationale: params.rationale,
          notes:     params.notes,
          actor_id:  params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── REJECT ──
    reject: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.reject(decisionId, {
          rationale: params.rationale,
          notes:     params.notes,
          actor_id:  params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── RETURN_FOR_REVISION ──
    returnForRevision: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.returnForRevision(decisionId, {
          rationale: params.rationale,
          notes:     params.notes,
          actor_id:  params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── ESCALATE ──
    escalate: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.escalate(decisionId, {
          notes:    params.notes,
          actor_id: params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── QUEUE_EXECUTION ──
    queueExecution: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.queueExecution(decisionId, {
          notes:    params.notes,
          actor_id: params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── EXECUTE ──
    markExecuted: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.execute(decisionId, {
          execution_result:  params.execution_result,
          linked_outcome_id: params.linked_outcome_id,
          notes:             params.notes,
          actor_id:          params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── REPORT_EXECUTION_FAILURE ──
    reportExecutionFailure: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.executionFailed(decisionId, {
          failure_reason: params.failure_reason,
          notes:          params.notes,
          actor_id:       params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── REVOKE ──
    revoke: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.revoke(decisionId, {
          rationale: params.rationale,
          notes:     params.notes,
          actor_id:  params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── WITHDRAW ──
    withdraw: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.withdraw(decisionId, {
          notes:    params.notes,
          actor_id: params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── RESUBMIT ──
    resubmit: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.resubmit(decisionId, {
          rationale: params.rationale,
          notes:     params.notes,
          actor_id:  params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── OVERRIDE ──
    override: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.override(decisionId, {
          target_status: params.override_to,
          rationale:     params.rationale,
          notes:         params.notes,
          actor_id:      params.actor_id,
        });
        return _upsert(raw as Record<string, unknown>);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── ANNOTATE ──
    annotate: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        // Backend is authoritative — use response to refresh authority AND events
        const raw = await api.authority.annotate(decisionId, {
          notes:    params.notes,
          actor_id: params.actor_id,
        });
        // Upsert the authority from backend response to prevent drift
        if (raw && typeof raw === "object") {
          _upsert(raw as Record<string, unknown>);
        }
        // Refresh events and metrics from backend
        await Promise.all([
          get().loadEvents(decisionId),
          get().loadMetrics(),
        ]);
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── Link Management (backend-authoritative — NO local-only mutations) ──
    linkOutcome: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.link(decisionId, {
          linked_outcome_id: params.outcome_id,
          notes: params.notes,
          actor_id: params.actor_id,
        });
        const result = _upsert(raw as Record<string, unknown>);
        // Refresh metrics after mutation
        await get().loadMetrics();
        return result;
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    linkValue: async (params) => {
      set({ loading: true, error: null });
      try {
        const decisionId = getDecisionId(params.authority_id);
        const raw = await api.authority.link(decisionId, {
          linked_value_id: params.value_id,
          notes: params.notes,
          actor_id: params.actor_id,
        });
        const result = _upsert(raw as Record<string, unknown>);
        // Refresh metrics after mutation
        await get().loadMetrics();
        return result;
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        set({ error: msg });
        throw err;
      } finally {
        set({ loading: false });
      }
    },

    // ── Selectors ──

    getAuthority: (authority_id) => {
      return get().authorities.get(authority_id) ?? null;
    },

    getAuthorityByDecision: (decision_id) => {
      const authorityId = get().decisionIndex.get(decision_id);
      if (!authorityId) return null;
      return get().authorities.get(authorityId) ?? null;
    },

    getAuditLog: (authority_id) => {
      return get().events.get(authority_id) ?? [];
    },

    getByStatus: (status) => {
      const result: DecisionAuthority[] = [];
      get().authorities.forEach((auth) => {
        if (auth.authority_status === status) result.push(auth);
      });
      return result;
    },

    getQueueSummary: () => {
      // BACKEND-AUTHORITATIVE: Return cached metrics from loadMetrics().
      // If metrics haven't been loaded yet, return zeroed summary.
      // Control Tower MUST call loadMetrics() on mount before reading this.
      const m = get().metrics;
      if (m) return m;
      return {
        proposed: 0,
        under_review: 0,
        approved_pending_execution: 0,
        executed: 0,
        rejected: 0,
        failed: 0,
        escalated: 0,
        overdue: 0,
        total_active: 0,
      };
    },

    getQueueForPersona: (persona) => {
      const items: AuthorityQueueItem[] = [];
      get().authorities.forEach((auth) => {
        items.push({
          authority_id:         auth.authority_id,
          decision_id:          auth.decision_id,
          authority_status:     auth.authority_status,
          decision_type:        auth.tags[0] ?? "UNKNOWN",
          proposed_by:          auth.proposed_by,
          proposed_by_role:     auth.proposed_by_role,
          proposed_at:          auth.proposed_at,
          priority:             auth.priority,
          is_overdue:           auth.is_overdue,
          rationale_preview:    auth.proposal_rationale?.slice(0, 120) ?? null,
          source_run_id:        null,
          source_scenario_label: null,
          revision_number:      auth.revision_number,
          escalation_level:     auth.escalation_level,
          last_authority_actor: auth.authority_actor_id,
          last_authority_action: null,
          last_authority_at:    auth.authority_decided_at,
        });
      });
      items.sort((a, b) => {
        if (a.is_overdue !== b.is_overdue) return a.is_overdue ? -1 : 1;
        if (a.priority !== b.priority) return a.priority - b.priority;
        return new Date(b.proposed_at).getTime() - new Date(a.proposed_at).getTime();
      });
      return items;
    },

    canPerform: (authority_id, action, actor_role) => {
      const auth = get().authorities.get(authority_id);
      if (!auth) return false;

      const allowedRoles = AUTHORITY_PERMISSIONS[action] ?? [];
      if (!allowedRoles.includes(actor_role)) return false;

      if (action === "OVERRIDE") return true;
      if (action === "ANNOTATE") return true;

      const actionTargetMap: Partial<Record<AuthorityAction, AuthorityStatus>> = {
        SUBMIT_FOR_REVIEW:        "UNDER_REVIEW",
        APPROVE:                  "APPROVED",
        REJECT:                   "REJECTED",
        RETURN_FOR_REVISION:      "RETURNED",
        ESCALATE:                 "ESCALATED",
        QUEUE_EXECUTION:          "EXECUTION_PENDING",
        EXECUTE:                  "EXECUTED",
        REPORT_EXECUTION_FAILURE: "EXECUTION_FAILED",
        REVOKE:                   "REVOKED",
        WITHDRAW:                 "WITHDRAWN",
      };
      const targetStatus = actionTargetMap[action];
      if (!targetStatus) return true;

      const allowed = AUTHORITY_TRANSITIONS[auth.authority_status] ?? [];
      return allowed.includes(targetStatus);
    },
  };
});
