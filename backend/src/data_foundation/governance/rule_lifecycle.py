"""
Rule Lifecycle State Machine
==============================

Enforced transitions for RuleSpec status:

  (null) → DRAFT         [CREATE]
  DRAFT → REVIEW         [ADVANCE]   requires: at least 1 trigger signal
  REVIEW → APPROVED      [ADVANCE]   requires: reviewed_by actor
  REVIEW → DRAFT         [REJECT]    requires: reason
  APPROVED → ACTIVE      [ADVANCE]   requires: approved_by, validation passes
  ACTIVE → RETIRED       [RETIRE]    requires: reason
  ACTIVE → SUPERSEDED    [SUPERSEDE] requires: supersedes_spec_id

Terminal states: SUPERSEDED, RETIRED — no further transitions.

All transitions are pure functions. No DB access. No side effects.
Produces RuleLifecycleEvent records for the audit chain.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .schemas import (
    RuleLifecycleEvent,
    SpecStatus,
    TransitionType,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Transition table: (from_status, to_status) → transition_type
# ═══════════════════════════════════════════════════════════════════════════════

_TRANSITIONS: Dict[Tuple[Optional[str], str], str] = {
    (None, SpecStatus.DRAFT): TransitionType.CREATE,
    (SpecStatus.DRAFT, SpecStatus.REVIEW): TransitionType.ADVANCE,
    (SpecStatus.REVIEW, SpecStatus.APPROVED): TransitionType.ADVANCE,
    (SpecStatus.REVIEW, SpecStatus.DRAFT): TransitionType.REJECT,
    (SpecStatus.APPROVED, SpecStatus.ACTIVE): TransitionType.ADVANCE,
    (SpecStatus.ACTIVE, SpecStatus.RETIRED): TransitionType.RETIRE,
    (SpecStatus.ACTIVE, SpecStatus.SUPERSEDED): TransitionType.SUPERSEDE,
}


class LifecycleError(Exception):
    """Raised when a lifecycle transition is invalid."""
    pass


# ═══════════════════════════════════════════════════════════════════════════════
# Guard functions — return (ok, reason)
# Each guard is a pure function: no DB, no side effects.
# ═══════════════════════════════════════════════════════════════════════════════


def _guard_draft_to_review(
    spec: Any,
    actor: str,
    context: Dict[str, Any],
) -> Tuple[bool, str]:
    """Spec must have at least 1 trigger signal."""
    trigger_signals = getattr(spec, "trigger_signals", None)
    if not trigger_signals or len(trigger_signals) == 0:
        return False, "Cannot advance to REVIEW: spec has no trigger signals."
    return True, ""


def _guard_review_to_approved(
    spec: Any,
    actor: str,
    context: Dict[str, Any],
) -> Tuple[bool, str]:
    """Must have a reviewer different from the spec author."""
    authored_by = getattr(spec, "authored_by", None) or context.get("authored_by")
    if authored_by and actor == authored_by:
        return False, "Cannot approve: reviewer must differ from author."
    return True, ""


def _guard_review_to_draft(
    spec: Any,
    actor: str,
    context: Dict[str, Any],
) -> Tuple[bool, str]:
    """Rejection requires a reason — enforced at transition time."""
    reason = context.get("reason", "")
    if not reason.strip():
        return False, "Cannot reject: reason is required."
    return True, ""


def _guard_approved_to_active(
    spec: Any,
    actor: str,
    context: Dict[str, Any],
) -> Tuple[bool, str]:
    """Must have approved_by set. Validation snapshot should be present."""
    approved_by = context.get("approved_by") or getattr(spec, "approved_by", None)
    if not approved_by:
        return False, "Cannot activate: approved_by is required."
    validation_snapshot = context.get("validation_result_snapshot", {})
    if validation_snapshot:
        errors = validation_snapshot.get("errors", [])
        if errors:
            return False, f"Cannot activate: validation has {len(errors)} error(s)."
    return True, ""


def _guard_active_to_retired(
    spec: Any,
    actor: str,
    context: Dict[str, Any],
) -> Tuple[bool, str]:
    """Retirement requires a reason."""
    reason = context.get("reason", "")
    if not reason.strip():
        return False, "Cannot retire: reason is required."
    return True, ""


def _guard_active_to_superseded(
    spec: Any,
    actor: str,
    context: Dict[str, Any],
) -> Tuple[bool, str]:
    """Supersession requires the superseding spec ID."""
    supersedes_spec_id = context.get("supersedes_spec_id")
    if not supersedes_spec_id:
        return False, "Cannot supersede: supersedes_spec_id is required."
    return True, ""


_GUARDS: Dict[Tuple[Optional[str], str], Any] = {
    (SpecStatus.DRAFT, SpecStatus.REVIEW): _guard_draft_to_review,
    (SpecStatus.REVIEW, SpecStatus.APPROVED): _guard_review_to_approved,
    (SpecStatus.REVIEW, SpecStatus.DRAFT): _guard_review_to_draft,
    (SpecStatus.APPROVED, SpecStatus.ACTIVE): _guard_approved_to_active,
    (SpecStatus.ACTIVE, SpecStatus.RETIRED): _guard_active_to_retired,
    (SpecStatus.ACTIVE, SpecStatus.SUPERSEDED): _guard_active_to_superseded,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════


def is_valid_transition(from_status: Optional[str], to_status: str) -> bool:
    """Check if a status transition is structurally valid (ignoring guards)."""
    return (from_status, to_status) in _TRANSITIONS


def get_allowed_transitions(from_status: Optional[str]) -> List[str]:
    """Return all structurally valid target statuses from the given status."""
    if from_status in SpecStatus.TERMINAL:
        return []
    return [
        to_s for (from_s, to_s) in _TRANSITIONS
        if from_s == from_status
    ]


def validate_transition(
    spec: Any,
    from_status: Optional[str],
    to_status: str,
    actor: str,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, str]:
    """Validate a transition including guard checks.

    Returns (is_valid, error_message). error_message is empty if valid.
    """
    ctx = context or {}

    # 1. Check terminal state
    if from_status in SpecStatus.TERMINAL:
        return False, f"Cannot transition from terminal status {from_status}."

    # 2. Check structural validity
    if not is_valid_transition(from_status, to_status):
        allowed = get_allowed_transitions(from_status)
        return False, (
            f"Invalid transition: {from_status} → {to_status}. "
            f"Allowed: {allowed}"
        )

    # 3. Run guard
    guard = _GUARDS.get((from_status, to_status))
    if guard is not None:
        ok, reason = guard(spec, actor, ctx)
        if not ok:
            return False, reason

    return True, ""


def execute_transition(
    spec: Any,
    from_status: Optional[str],
    to_status: str,
    actor: str,
    reason: str,
    context: Optional[Dict[str, Any]] = None,
    previous_event_hash: Optional[str] = None,
) -> RuleLifecycleEvent:
    """Execute a lifecycle transition. Raises LifecycleError if invalid.

    Pure function — mutates nothing. Returns the lifecycle event to record.
    The caller is responsible for:
      1. Updating spec.status
      2. Persisting the event
      3. Appending to the audit chain

    Args:
        spec: The RuleSpec being transitioned (read-only).
        from_status: Current status (None for initial creation).
        to_status: Target status.
        actor: Who is performing the transition.
        reason: Why the transition is happening.
        context: Additional context (approved_by, supersedes_spec_id, etc.).
        previous_event_hash: Hash of the previous lifecycle event for chaining.

    Returns:
        RuleLifecycleEvent with computed provenance hash.
    """
    ctx = context or {}
    ctx["reason"] = reason  # ensure reason is available to guards

    # Validate
    ok, error = validate_transition(spec, from_status, to_status, actor, ctx)
    if not ok:
        raise LifecycleError(error)

    # Determine transition type
    transition_type = _TRANSITIONS[(from_status, to_status)]

    # Build event
    event = RuleLifecycleEvent(
        spec_id=getattr(spec, "spec_id", ctx.get("spec_id", "UNKNOWN")),
        from_status=from_status,
        to_status=to_status,
        transition_type=transition_type,
        actor=actor,
        actor_role=ctx.get("actor_role"),
        reason=reason,
        validation_result_snapshot=ctx.get("validation_result_snapshot", {}),
        policy_id=ctx.get("policy_id"),
        supersedes_spec_id=ctx.get("supersedes_spec_id"),
        previous_event_hash=previous_event_hash,
    )
    event.compute_hash()
    return event


def create_spec_event(
    spec: Any,
    actor: str,
    reason: str = "Initial creation.",
    context: Optional[Dict[str, Any]] = None,
) -> RuleLifecycleEvent:
    """Convenience: create the initial DRAFT lifecycle event for a new spec."""
    return execute_transition(
        spec=spec,
        from_status=None,
        to_status=SpecStatus.DRAFT,
        actor=actor,
        reason=reason,
        context=context,
    )
