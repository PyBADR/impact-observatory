"""
Rule Lifecycle State Machine — Tests
======================================

Validates:
  1. All valid transitions produce correct events
  2. Invalid transitions are rejected
  3. Terminal states block all transitions
  4. Guard functions enforce preconditions
  5. Hash chaining works across transitions
  6. create_spec_event convenience function
"""

from __future__ import annotations

import pytest
from types import SimpleNamespace

from src.data_foundation.governance.schemas import (
    SpecStatus,
    TransitionType,
    RuleLifecycleEvent,
)
from src.data_foundation.governance.rule_lifecycle import (
    is_valid_transition,
    get_allowed_transitions,
    validate_transition,
    execute_transition,
    create_spec_event,
    LifecycleError,
)


def _make_spec(**kwargs):
    """Create a minimal spec-like object for testing."""
    defaults = {
        "spec_id": "SPEC-TEST-v1",
        "status": "DRAFT",
        "trigger_signals": [{"signal": "oil_energy_signals.change_pct"}],
        "authored_by": "analyst-1",
        "approved_by": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# Structural transition validity
# ═══════════════════════════════════════════════════════════════════════════════


class TestIsValidTransition:

    def test_create(self):
        assert is_valid_transition(None, SpecStatus.DRAFT) is True

    def test_draft_to_review(self):
        assert is_valid_transition(SpecStatus.DRAFT, SpecStatus.REVIEW) is True

    def test_review_to_approved(self):
        assert is_valid_transition(SpecStatus.REVIEW, SpecStatus.APPROVED) is True

    def test_review_to_draft_reject(self):
        assert is_valid_transition(SpecStatus.REVIEW, SpecStatus.DRAFT) is True

    def test_approved_to_active(self):
        assert is_valid_transition(SpecStatus.APPROVED, SpecStatus.ACTIVE) is True

    def test_active_to_retired(self):
        assert is_valid_transition(SpecStatus.ACTIVE, SpecStatus.RETIRED) is True

    def test_active_to_superseded(self):
        assert is_valid_transition(SpecStatus.ACTIVE, SpecStatus.SUPERSEDED) is True

    def test_invalid_draft_to_active(self):
        assert is_valid_transition(SpecStatus.DRAFT, SpecStatus.ACTIVE) is False

    def test_invalid_retired_to_active(self):
        assert is_valid_transition(SpecStatus.RETIRED, SpecStatus.ACTIVE) is False

    def test_invalid_superseded_to_anything(self):
        assert is_valid_transition(SpecStatus.SUPERSEDED, SpecStatus.DRAFT) is False


class TestGetAllowedTransitions:

    def test_from_none(self):
        assert SpecStatus.DRAFT in get_allowed_transitions(None)

    def test_from_draft(self):
        assert get_allowed_transitions(SpecStatus.DRAFT) == [SpecStatus.REVIEW]

    def test_from_review(self):
        allowed = get_allowed_transitions(SpecStatus.REVIEW)
        assert SpecStatus.APPROVED in allowed
        assert SpecStatus.DRAFT in allowed

    def test_from_active(self):
        allowed = get_allowed_transitions(SpecStatus.ACTIVE)
        assert SpecStatus.RETIRED in allowed
        assert SpecStatus.SUPERSEDED in allowed

    def test_terminal_has_no_transitions(self):
        assert get_allowed_transitions(SpecStatus.RETIRED) == []
        assert get_allowed_transitions(SpecStatus.SUPERSEDED) == []


# ═══════════════════════════════════════════════════════════════════════════════
# Guard enforcement
# ═══════════════════════════════════════════════════════════════════════════════


class TestGuards:

    def test_draft_to_review_requires_triggers(self):
        spec = _make_spec(trigger_signals=[])
        ok, msg = validate_transition(spec, SpecStatus.DRAFT, SpecStatus.REVIEW, "admin")
        assert ok is False
        assert "trigger signals" in msg.lower()

    def test_draft_to_review_passes_with_triggers(self):
        spec = _make_spec()
        ok, msg = validate_transition(spec, SpecStatus.DRAFT, SpecStatus.REVIEW, "admin")
        assert ok is True

    def test_review_to_approved_rejects_self_review(self):
        spec = _make_spec(authored_by="analyst-1")
        ok, msg = validate_transition(
            spec, SpecStatus.REVIEW, SpecStatus.APPROVED, "analyst-1",
        )
        assert ok is False
        assert "reviewer" in msg.lower() or "differ" in msg.lower()

    def test_review_to_approved_passes_different_reviewer(self):
        spec = _make_spec(authored_by="analyst-1")
        ok, msg = validate_transition(
            spec, SpecStatus.REVIEW, SpecStatus.APPROVED, "reviewer-2",
        )
        assert ok is True

    def test_review_to_draft_requires_reason(self):
        spec = _make_spec()
        ok, msg = validate_transition(
            spec, SpecStatus.REVIEW, SpecStatus.DRAFT, "admin",
            context={"reason": ""},
        )
        assert ok is False
        assert "reason" in msg.lower()

    def test_review_to_draft_passes_with_reason(self):
        spec = _make_spec()
        ok, msg = validate_transition(
            spec, SpecStatus.REVIEW, SpecStatus.DRAFT, "admin",
            context={"reason": "Needs rework."},
        )
        assert ok is True

    def test_approved_to_active_requires_approved_by(self):
        spec = _make_spec()
        ok, msg = validate_transition(
            spec, SpecStatus.APPROVED, SpecStatus.ACTIVE, "admin",
            context={},
        )
        assert ok is False
        assert "approved_by" in msg.lower()

    def test_approved_to_active_passes_with_approval(self):
        spec = _make_spec()
        ok, msg = validate_transition(
            spec, SpecStatus.APPROVED, SpecStatus.ACTIVE, "admin",
            context={"approved_by": "cro"},
        )
        assert ok is True

    def test_approved_to_active_rejects_validation_errors(self):
        spec = _make_spec()
        ok, msg = validate_transition(
            spec, SpecStatus.APPROVED, SpecStatus.ACTIVE, "admin",
            context={
                "approved_by": "cro",
                "validation_result_snapshot": {"errors": ["Missing threshold"]},
            },
        )
        assert ok is False
        assert "error" in msg.lower()

    def test_active_to_retired_requires_reason(self):
        spec = _make_spec()
        ok, msg = validate_transition(
            spec, SpecStatus.ACTIVE, SpecStatus.RETIRED, "admin",
            context={"reason": ""},
        )
        assert ok is False

    def test_active_to_superseded_requires_spec_id(self):
        spec = _make_spec()
        ok, msg = validate_transition(
            spec, SpecStatus.ACTIVE, SpecStatus.SUPERSEDED, "admin",
            context={"reason": "Replaced."},
        )
        assert ok is False
        assert "supersedes_spec_id" in msg.lower()

    def test_active_to_superseded_passes(self):
        spec = _make_spec()
        ok, msg = validate_transition(
            spec, SpecStatus.ACTIVE, SpecStatus.SUPERSEDED, "admin",
            context={"reason": "Replaced.", "supersedes_spec_id": "SPEC-NEW-v2"},
        )
        assert ok is True

    def test_terminal_state_blocked(self):
        spec = _make_spec()
        ok, msg = validate_transition(
            spec, SpecStatus.RETIRED, SpecStatus.DRAFT, "admin",
        )
        assert ok is False
        assert "terminal" in msg.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# execute_transition
# ═══════════════════════════════════════════════════════════════════════════════


class TestExecuteTransition:

    def test_produces_event(self):
        spec = _make_spec()
        event = execute_transition(
            spec, SpecStatus.DRAFT, SpecStatus.REVIEW,
            actor="admin", reason="Ready.",
        )
        assert isinstance(event, RuleLifecycleEvent)
        assert event.from_status == SpecStatus.DRAFT
        assert event.to_status == SpecStatus.REVIEW
        assert event.transition_type == TransitionType.ADVANCE
        assert event.provenance_hash != ""

    def test_raises_on_invalid(self):
        spec = _make_spec(trigger_signals=[])
        with pytest.raises(LifecycleError):
            execute_transition(
                spec, SpecStatus.DRAFT, SpecStatus.REVIEW,
                actor="admin", reason="Nope.",
            )

    def test_hash_chaining(self):
        spec = _make_spec()
        e1 = create_spec_event(spec, actor="admin")
        e2 = execute_transition(
            spec, SpecStatus.DRAFT, SpecStatus.REVIEW,
            actor="admin", reason="Ready.",
            previous_event_hash=e1.provenance_hash,
        )
        assert e2.previous_event_hash == e1.provenance_hash
        assert e2.provenance_hash != e1.provenance_hash


class TestCreateSpecEvent:

    def test_creates_draft_event(self):
        spec = _make_spec()
        event = create_spec_event(spec, actor="admin")
        assert event.from_status is None
        assert event.to_status == SpecStatus.DRAFT
        assert event.transition_type == TransitionType.CREATE
        assert event.provenance_hash != ""

    def test_uses_spec_id(self):
        spec = _make_spec(spec_id="SPEC-CUSTOM-v1")
        event = create_spec_event(spec, actor="admin")
        assert event.spec_id == "SPEC-CUSTOM-v1"
