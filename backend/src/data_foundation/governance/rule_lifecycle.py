"""Rule Lifecycle State Machine — deterministic status transitions.

Valid transitions:
  (null) ──CREATE──→ DRAFT
  DRAFT  ──ADVANCE──→ REVIEW
  REVIEW ──ADVANCE──→ APPROVED    (requires reviewed_by)
  REVIEW ──REJECT───→ DRAFT       (with rejection reason)
  APPROVED ──ADVANCE──→ ACTIVE    (requires approved_by + validation pass)
  ACTIVE ──RETIRE───→ RETIRED
  ACTIVE ──SUPERSEDE→ SUPERSEDED  (requires supersedes_spec_id)
  RETIRED → (terminal)
  SUPERSEDED → (terminal)

Guards enforce preconditions. Invalid transitions raise ValueError.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from src.data_foundation.governance.schemas import (
    RuleLifecycleEvent,
    VALID_LIFECYCLE_STATUSES,
)

__all__ = [
    "TRANSITION_MAP",
    "TERMINAL_STATES",
    "validate_transition",
    "execute_transition",
    "build_event_chain",
]


# ═══════════════════════════════════════════════════════════════════════════════
# Transition Map — {(from_status, transition_type) → to_status}
# ═══════════════════════════════════════════════════════════════════════════════

TRANSITION_MAP: Dict[tuple[Optional[str], str], str] = {
    (None, "CREATE"): "DRAFT",
    ("DRAFT", "ADVANCE"): "REVIEW",
    ("REVIEW", "ADVANCE"): "APPROVED",
    ("REVIEW", "REJECT"): "DRAFT",
    ("APPROVED", "ADVANCE"): "ACTIVE",
    ("ACTIVE", "RETIRE"): "RETIRED",
    ("ACTIVE", "SUPERSEDE"): "SUPERSEDED",
}

TERMINAL_STATES = {"RETIRED", "SUPERSEDED"}


def _gen_id() -> str:
    return f"RLE-{str(uuid4())[:12]}"


def _compute_hash(event: RuleLifecycleEvent) -> str:
    """SHA-256 of the event's canonical fields for chain integrity."""
    data = {
        "event_id": event.event_id,
        "spec_id": event.spec_id,
        "from_status": event.from_status,
        "to_status": event.to_status,
        "transition_type": event.transition_type,
        "actor": event.actor,
        "occurred_at": event.occurred_at.isoformat(),
        "previous_event_hash": event.previous_event_hash,
    }
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# Guard Functions — preconditions for transitions
# ═══════════════════════════════════════════════════════════════════════════════

def _guard_create(context: Dict[str, Any]) -> List[str]:
    """CREATE requires: trigger_signals or reason."""
    errors = []
    if not context.get("reason"):
        errors.append("CREATE requires a reason.")
    return errors


def _guard_advance_to_review(context: Dict[str, Any]) -> List[str]:
    """DRAFT→REVIEW requires: trigger signals present."""
    errors = []
    if not context.get("reason"):
        errors.append("ADVANCE to REVIEW requires a reason.")
    return errors


def _guard_advance_to_approved(context: Dict[str, Any]) -> List[str]:
    """REVIEW→APPROVED requires: reviewed_by (separate from author)."""
    errors = []
    if not context.get("reviewed_by"):
        errors.append("ADVANCE to APPROVED requires reviewed_by.")
    if context.get("reviewed_by") == context.get("authored_by"):
        errors.append("Reviewer must differ from author.")
    return errors


def _guard_advance_to_active(context: Dict[str, Any]) -> List[str]:
    """APPROVED→ACTIVE requires: approved_by + validation pass."""
    errors = []
    if not context.get("approved_by"):
        errors.append("ADVANCE to ACTIVE requires approved_by.")
    validation = context.get("validation_passed", False)
    if not validation:
        errors.append("ADVANCE to ACTIVE requires validation_passed=True.")
    return errors


def _guard_retire(context: Dict[str, Any]) -> List[str]:
    """ACTIVE→RETIRED requires: reason."""
    errors = []
    if not context.get("reason"):
        errors.append("RETIRE requires a reason.")
    return errors


def _guard_supersede(context: Dict[str, Any]) -> List[str]:
    """ACTIVE→SUPERSEDED requires: supersedes_spec_id."""
    errors = []
    if not context.get("supersedes_spec_id"):
        errors.append("SUPERSEDE requires supersedes_spec_id.")
    if not context.get("reason"):
        errors.append("SUPERSEDE requires a reason.")
    return errors


def _guard_reject(context: Dict[str, Any]) -> List[str]:
    """REVIEW→DRAFT requires: rejection reason."""
    errors = []
    if not context.get("reason"):
        errors.append("REJECT requires a reason.")
    return errors


# Map of (from_status, transition_type) → guard function
_GUARDS: Dict[tuple[Optional[str], str], Any] = {
    (None, "CREATE"): _guard_create,
    ("DRAFT", "ADVANCE"): _guard_advance_to_review,
    ("REVIEW", "ADVANCE"): _guard_advance_to_approved,
    ("REVIEW", "REJECT"): _guard_reject,
    ("APPROVED", "ADVANCE"): _guard_advance_to_active,
    ("ACTIVE", "RETIRE"): _guard_retire,
    ("ACTIVE", "SUPERSEDE"): _guard_supersede,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

def validate_transition(
    from_status: Optional[str],
    transition_type: str,
    context: Dict[str, Any],
) -> List[str]:
    """Validate a proposed transition. Returns list of errors (empty = valid).

    Checks:
      1. from_status is not terminal
      2. (from_status, transition_type) is a valid transition
      3. Guard preconditions pass
    """
    errors: List[str] = []

    # Terminal state check
    if from_status in TERMINAL_STATES:
        errors.append(f"Cannot transition from terminal state: {from_status}")
        return errors

    # Valid transition check
    key = (from_status, transition_type)
    if key not in TRANSITION_MAP:
        errors.append(
            f"Invalid transition: ({from_status}, {transition_type}). "
            f"Valid transitions from {from_status}: "
            f"{[k for k in TRANSITION_MAP if k[0] == from_status]}"
        )
        return errors

    # Guard check
    guard = _GUARDS.get(key)
    if guard:
        errors.extend(guard(context))

    return errors


def execute_transition(
    spec_id: str,
    from_status: Optional[str],
    transition_type: str,
    actor: str,
    reason: str,
    context: Dict[str, Any] | None = None,
    *,
    previous_event_hash: str | None = None,
    actor_role: str | None = None,
    policy_id: str | None = None,
    validation_result_snapshot: Dict[str, Any] | None = None,
) -> RuleLifecycleEvent:
    """Execute a lifecycle transition. Returns the new event or raises ValueError.

    Args:
        spec_id: Which rule spec is transitioning.
        from_status: Current status (None for CREATE).
        transition_type: One of CREATE, ADVANCE, REJECT, RETIRE, SUPERSEDE.
        actor: Who is performing this transition.
        reason: Why.
        context: Additional context for guard validation.
        previous_event_hash: Hash chain link.
        actor_role: Role of the actor.
        policy_id: Governance policy authorizing this transition.
        validation_result_snapshot: Frozen validation output.
    """
    ctx = context or {}
    ctx.setdefault("reason", reason)

    errors = validate_transition(from_status, transition_type, ctx)
    if errors:
        raise ValueError(f"Transition failed: {'; '.join(errors)}")

    to_status = TRANSITION_MAP[(from_status, transition_type)]
    now = datetime.now(timezone.utc)

    event = RuleLifecycleEvent(
        event_id=_gen_id(),
        spec_id=spec_id,
        from_status=from_status,
        to_status=to_status,
        transition_type=transition_type,
        actor=actor,
        actor_role=actor_role,
        reason=reason,
        validation_result_snapshot=validation_result_snapshot or {},
        policy_id=policy_id,
        occurred_at=now,
        previous_event_hash=previous_event_hash,
    )

    return event


def build_event_chain(events: List[RuleLifecycleEvent]) -> List[RuleLifecycleEvent]:
    """Compute hash chain across a list of events (in order).

    Each event's provenance_hash is computed, and subsequent events
    link to the previous via previous_event_hash.
    """
    chained: List[RuleLifecycleEvent] = []
    prev_hash: Optional[str] = None

    for event in events:
        # Update the previous_event_hash link
        updated = event.model_copy(update={"previous_event_hash": prev_hash})
        # Compute this event's hash
        event_hash = _compute_hash(updated)
        chained.append(updated)
        prev_hash = event_hash

    return chained
