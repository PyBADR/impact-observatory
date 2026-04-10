/**
 * graph-contracts — Frontend read-path contract enforcement.
 *
 * Mirrors backend src/services/graph_contracts.py logic.
 * Applied at Zustand store sync points so all persona views
 * receive only contract-valid records.
 *
 * Fail closed: orphan records are silently dropped with a
 * single console.warn per orphan (minimal noise, auditable).
 */

import type {
  OperatorDecision,
  OperatorDecisionStatus,
  Outcome,
  OutcomeLifecycleStatus,
  DecisionValue,
} from "@/types/observatory";

// ── Valid status sets (mirrors backend VALID_* constants) ─────────────────────

const VALID_DECISION_STATUSES = new Set<OperatorDecisionStatus>([
  "CREATED",
  "IN_REVIEW",
  "EXECUTED",
  "FAILED",
  "CLOSED",
]);

const VALID_OUTCOME_STATUSES = new Set<OutcomeLifecycleStatus>([
  "PENDING_OBSERVATION",
  "OBSERVED",
  "CONFIRMED",
  "DISPUTED",
  "CLOSED",
  "FAILED",
]);

// ── Record validators ─────────────────────────────────────────────────────────

/**
 * A decision is valid if it has a non-empty id and a recognised status.
 * source_run_id absence is allowed (warn only — creation path may omit it).
 */
export function validateDecisionRecord(d: OperatorDecision): boolean {
  if (!d.decision_id) return false;
  if (!VALID_DECISION_STATUSES.has(d.decision_status)) return false;
  return true;
}

/**
 * An outcome is valid if it has a non-empty id, a recognised status,
 * and its source_decision_id resolves to an entry in the provided decision set.
 */
export function validateOutcomeRecord(
  o: Outcome,
  decisionIds: Set<string>,
): boolean {
  if (!o.outcome_id) return false;
  if (!VALID_OUTCOME_STATUSES.has(o.outcome_status)) return false;
  // Outcomes must be linked to a known decision.
  if (!o.source_decision_id || !decisionIds.has(o.source_decision_id))
    return false;
  return true;
}

/**
 * A value is valid if it has a non-empty id, its source_outcome_id resolves
 * to a known outcome, and the chain continues to a known decision.
 */
export function validateValueRecord(
  v: DecisionValue,
  outcomeIds: Set<string>,
  decisionIds: Set<string>,
): boolean {
  if (!v.value_id) return false;
  if (!v.source_outcome_id || !outcomeIds.has(v.source_outcome_id))
    return false;
  // Full chain: value → outcome → decision
  if (!v.source_decision_id || !decisionIds.has(v.source_decision_id))
    return false;
  return true;
}

// ── Filter helpers ────────────────────────────────────────────────────────────

/**
 * Return only contract-valid decisions. Orphans are warned and dropped.
 */
export function filterValidDecisions(
  decisions: OperatorDecision[],
): OperatorDecision[] {
  const valid: OperatorDecision[] = [];
  for (const d of decisions) {
    if (validateDecisionRecord(d)) {
      valid.push(d);
    } else {
      console.warn(
        "[graph-contracts] orphan decision dropped",
        d.decision_id,
        d.decision_status,
      );
    }
  }
  return valid;
}

/**
 * Return only contract-valid outcomes. Requires the filtered decision list
 * (already validated) to check parent linkage.
 */
export function filterValidOutcomes(
  outcomes: Outcome[],
  decisions: OperatorDecision[],
): Outcome[] {
  const decisionIds = new Set(decisions.map((d) => d.decision_id));
  const valid: Outcome[] = [];
  for (const o of outcomes) {
    if (validateOutcomeRecord(o, decisionIds)) {
      valid.push(o);
    } else {
      console.warn(
        "[graph-contracts] orphan outcome dropped",
        o.outcome_id,
        o.source_decision_id,
      );
    }
  }
  return valid;
}

/**
 * Return only contract-valid decision values. Requires filtered decisions
 * and outcomes to verify the full chain.
 */
export function filterValidValues(
  values: DecisionValue[],
  outcomes: Outcome[],
  decisions: OperatorDecision[],
): DecisionValue[] {
  const outcomeIds  = new Set(outcomes.map((o) => o.outcome_id));
  const decisionIds = new Set(decisions.map((d) => d.decision_id));
  const valid: DecisionValue[] = [];
  for (const v of values) {
    if (validateValueRecord(v, outcomeIds, decisionIds)) {
      valid.push(v);
    } else {
      console.warn(
        "[graph-contracts] orphan value dropped",
        v.value_id,
        v.source_outcome_id,
        v.source_decision_id,
      );
    }
  }
  return valid;
}
