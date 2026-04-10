/**
 * Impact Observatory | مرصد الأثر — Deterministic Audit Event Emitter
 *
 * Isomorphic: runs in Next.js server route handlers AND browser components.
 * Each environment gets its own module instance (server process / browser tab)
 * and therefore its own ring buffer — no shared state across the boundary.
 *
 * Design constraints:
 *  - emitAudit() is ALWAYS synchronous and NEVER throws.
 *  - No network calls, no external dependencies, no React imports.
 *  - console.error for violations (api_contract, same_run_integrity).
 *  - console.info for lifecycle / compute / fallback events.
 *  - Ring buffer of RING_SIZE events; oldest entry evicted on overflow.
 *
 * Usage:
 *   import { emitAudit } from "@/lib/audit";
 *   emitAudit({ event_type: "decision_created", entity_id: dec.decision_id, ... });
 */

// ── Event type union ─────────────────────────────────────────────────────────

export type AuditEventType =
  | "decision_created"
  | "authority_item_created"
  | "lifecycle_transition"
  | "outcome_derived"
  | "value_computed"
  | "api_contract_violation"
  | "same_run_integrity_violation"
  | "render_fallback_invoked";

// ── Canonical event shape ────────────────────────────────────────────────────

export interface AuditEvent {
  /** Stable, collision-resistant identifier for this audit record. */
  event_id: string;
  event_type: AuditEventType;
  /** The active simulation run this event belongs to (null when unknown). */
  run_id: string | null;
  /** The scenario template that triggered the run (null when unknown). */
  scenario_id: string | null;
  /**
   * Primary entity being audited.
   * Convention:
   *   decision_created          → decision_id
   *   authority_item_created    → authority_id
   *   lifecycle_transition      → decision_id | authority_id
   *   outcome_derived           → outcome_id
   *   value_computed            → value_id
   *   api_contract_violation    → function name ("unifiedToRunResult")
   *   same_run_integrity_violation → function name
   *   render_fallback_invoked   → function name ("toControlTowerViewModel")
   */
  entity_id: string;
  /** ISO-8601 wall-clock timestamp at emission. */
  occurred_at: string;
  /**
   * Who or what triggered the event.
   * "system" for automated pipeline steps; persona role string for operator actions.
   */
  actor: string;
  /** Structured payload — varies by event_type; always a plain object. */
  details: Record<string, unknown>;
  /**
   * Parent entity that caused this event (lineage chain).
   *   authority_item_created → decision_id
   *   outcome_derived        → decision_id
   *   value_computed         → outcome_id
   *   lifecycle_transition   → previous entity_id (if known)
   */
  lineage_ref: string | null;
}

// ── Ring buffer ──────────────────────────────────────────────────────────────

const RING_SIZE = 200;
const _ring: AuditEvent[] = [];

function _push(evt: AuditEvent): void {
  _ring.push(evt);
  if (_ring.length > RING_SIZE) _ring.shift();
}

// ── ID generator ─────────────────────────────────────────────────────────────

function _uid(): string {
  const ts   = Date.now().toString(36);
  const rand = Math.random().toString(36).slice(2, 8);
  return `aud_${ts}_${rand}`;
}

// ── Emitter ───────────────────────────────────────────────────────────────────

/**
 * Emit a deterministic audit event. Always synchronous. Never throws.
 * Returns the constructed AuditEvent so callers can capture the event_id
 * if they need to chain further events via lineage_ref.
 */
export function emitAudit(params: {
  event_type:   AuditEventType;
  entity_id:    string;
  run_id?:      string | null;
  scenario_id?: string | null;
  actor?:       string;
  details?:     Record<string, unknown>;
  lineage_ref?: string | null;
}): AuditEvent {
  const evt: AuditEvent = {
    event_id:    _uid(),
    event_type:  params.event_type,
    run_id:      params.run_id      ?? null,
    scenario_id: params.scenario_id ?? null,
    entity_id:   params.entity_id,
    occurred_at: new Date().toISOString(),
    actor:       params.actor       ?? "system",
    details:     params.details     ?? {},
    lineage_ref: params.lineage_ref ?? null,
  };

  try {
    _push(evt);

    const isViolation =
      params.event_type === "api_contract_violation" ||
      params.event_type === "same_run_integrity_violation";

    // Violations logged at error level so they appear in browser console
    // error filters and server stderr even when info is suppressed.
    if (isViolation) {
      console.error("[AUDIT]", JSON.stringify(evt));
    } else {
      // Use console.info so audit events are visible in dev but filterable.
      // In production, stdout/stderr aggregators pick these up for tracing.
      console.info("[AUDIT]", JSON.stringify(evt));
    }
  } catch {
    // Never let the audit hook crash a render or API route handler.
  }

  return evt;
}

// ── Query helpers ─────────────────────────────────────────────────────────────

/** Snapshot of ring buffer, newest first. */
export function getAuditLog(): AuditEvent[] {
  return _ring.slice().reverse();
}

/** Snapshot filtered by one or more event types, newest first. */
export function getAuditLogByType(...types: AuditEventType[]): AuditEvent[] {
  return _ring
    .filter((e) => types.includes(e.event_type))
    .reverse();
}

/** All violation events (api_contract + same_run_integrity), newest first. */
export function getViolations(): AuditEvent[] {
  return getAuditLogByType("api_contract_violation", "same_run_integrity_violation");
}
