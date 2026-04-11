"""Tests for rule lifecycle state machine."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.data_foundation.governance.rule_lifecycle import (
    TERMINAL_STATES,
    TRANSITION_MAP,
    build_event_chain,
    execute_transition,
    validate_transition,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestTransitionMap:
    def test_all_transitions_defined(self):
        assert len(TRANSITION_MAP) == 7

    def test_create_goes_to_draft(self):
        assert TRANSITION_MAP[(None, "CREATE")] == "DRAFT"

    def test_draft_advance_goes_to_review(self):
        assert TRANSITION_MAP[("DRAFT", "ADVANCE")] == "REVIEW"

    def test_review_advance_goes_to_approved(self):
        assert TRANSITION_MAP[("REVIEW", "ADVANCE")] == "APPROVED"

    def test_review_reject_goes_to_draft(self):
        assert TRANSITION_MAP[("REVIEW", "REJECT")] == "DRAFT"

    def test_approved_advance_goes_to_active(self):
        assert TRANSITION_MAP[("APPROVED", "ADVANCE")] == "ACTIVE"

    def test_active_retire_goes_to_retired(self):
        assert TRANSITION_MAP[("ACTIVE", "RETIRE")] == "RETIRED"

    def test_active_supersede_goes_to_superseded(self):
        assert TRANSITION_MAP[("ACTIVE", "SUPERSEDE")] == "SUPERSEDED"

    def test_terminal_states(self):
        assert TERMINAL_STATES == {"RETIRED", "SUPERSEDED"}


class TestValidateTransition:
    def test_valid_create(self):
        errors = validate_transition(None, "CREATE", {"reason": "New rule"})
        assert errors == []

    def test_valid_advance_to_review(self):
        errors = validate_transition("DRAFT", "ADVANCE", {"reason": "Ready"})
        assert errors == []

    def test_valid_advance_to_approved(self):
        errors = validate_transition("REVIEW", "ADVANCE", {
            "reviewed_by": "reviewer", "authored_by": "author",
        })
        assert errors == []

    def test_advance_to_approved_requires_reviewer(self):
        errors = validate_transition("REVIEW", "ADVANCE", {})
        assert any("reviewed_by" in e for e in errors)

    def test_advance_to_approved_reviewer_must_differ(self):
        errors = validate_transition("REVIEW", "ADVANCE", {
            "reviewed_by": "same_person", "authored_by": "same_person",
        })
        assert any("differ" in e for e in errors)

    def test_valid_advance_to_active(self):
        errors = validate_transition("APPROVED", "ADVANCE", {
            "approved_by": "cro", "validation_passed": True,
        })
        assert errors == []

    def test_advance_to_active_requires_approval(self):
        errors = validate_transition("APPROVED", "ADVANCE", {
            "validation_passed": True,
        })
        assert any("approved_by" in e for e in errors)

    def test_advance_to_active_requires_validation(self):
        errors = validate_transition("APPROVED", "ADVANCE", {
            "approved_by": "cro",
        })
        assert any("validation_passed" in e for e in errors)

    def test_reject_requires_reason(self):
        errors = validate_transition("REVIEW", "REJECT", {})
        assert any("reason" in e.lower() for e in errors)

    def test_retire_requires_reason(self):
        errors = validate_transition("ACTIVE", "RETIRE", {})
        assert any("reason" in e.lower() for e in errors)

    def test_supersede_requires_spec_id(self):
        errors = validate_transition("ACTIVE", "SUPERSEDE", {"reason": "replaced"})
        assert any("supersedes_spec_id" in e for e in errors)

    def test_terminal_state_blocked(self):
        for state in TERMINAL_STATES:
            errors = validate_transition(state, "ADVANCE", {"reason": "nope"})
            assert any("terminal" in e.lower() for e in errors)

    def test_invalid_transition(self):
        errors = validate_transition("DRAFT", "RETIRE", {"reason": "skip"})
        assert any("Invalid transition" in e for e in errors)


class TestExecuteTransition:
    def test_create_success(self):
        event = execute_transition(
            spec_id="RULE-TEST",
            from_status=None,
            transition_type="CREATE",
            actor="admin",
            reason="New rule created.",
        )
        assert event.to_status == "DRAFT"
        assert event.from_status is None
        assert event.transition_type == "CREATE"
        assert event.event_id.startswith("RLE-")

    def test_full_lifecycle(self):
        """Walk through the full happy path: CREATE → ... → ACTIVE."""
        e1 = execute_transition("RULE-X", None, "CREATE", "author", "New")
        assert e1.to_status == "DRAFT"

        e2 = execute_transition("RULE-X", "DRAFT", "ADVANCE", "author", "Ready")
        assert e2.to_status == "REVIEW"

        e3 = execute_transition("RULE-X", "REVIEW", "ADVANCE", "reviewer", "Reviewed",
                                context={"reviewed_by": "reviewer", "authored_by": "author"})
        assert e3.to_status == "APPROVED"

        e4 = execute_transition("RULE-X", "APPROVED", "ADVANCE", "cro", "Approved",
                                context={"approved_by": "cro", "validation_passed": True})
        assert e4.to_status == "ACTIVE"

    def test_reject_returns_to_draft(self):
        event = execute_transition("RULE-X", "REVIEW", "REJECT", "reviewer", "Needs work")
        assert event.to_status == "DRAFT"

    def test_retire(self):
        event = execute_transition("RULE-X", "ACTIVE", "RETIRE", "admin", "No longer needed")
        assert event.to_status == "RETIRED"

    def test_supersede(self):
        event = execute_transition("RULE-X", "ACTIVE", "SUPERSEDE", "admin", "Replaced by v2",
                                   context={"supersedes_spec_id": "RULE-X-V2", "reason": "Replaced by v2"})
        assert event.to_status == "SUPERSEDED"

    def test_invalid_transition_raises(self):
        with pytest.raises(ValueError, match="Transition failed"):
            execute_transition("RULE-X", "DRAFT", "RETIRE", "admin", "skip ahead")

    def test_terminal_state_raises(self):
        with pytest.raises(ValueError, match="terminal"):
            execute_transition("RULE-X", "RETIRED", "ADVANCE", "admin", "comeback")

    def test_event_has_correct_fields(self):
        event = execute_transition(
            "RULE-Y", None, "CREATE", "admin", "First version",
            actor_role="Risk Analyst", policy_id="GPOL-001",
        )
        assert event.actor == "admin"
        assert event.actor_role == "Risk Analyst"
        assert event.policy_id == "GPOL-001"
        assert event.occurred_at is not None


class TestBuildEventChain:
    def test_chain_links_hashes(self):
        events = [
            execute_transition("RULE-Z", None, "CREATE", "admin", "New"),
            execute_transition("RULE-Z", "DRAFT", "ADVANCE", "admin", "Ready"),
        ]
        chained = build_event_chain(events)
        assert chained[0].previous_event_hash is None
        assert chained[1].previous_event_hash is not None

    def test_chain_single_event(self):
        events = [execute_transition("RULE-Z", None, "CREATE", "admin", "New")]
        chained = build_event_chain(events)
        assert len(chained) == 1
        assert chained[0].previous_event_hash is None

    def test_chain_three_events(self):
        events = [
            execute_transition("RULE-Z", None, "CREATE", "admin", "New"),
            execute_transition("RULE-Z", "DRAFT", "ADVANCE", "admin", "Ready"),
            execute_transition("RULE-Z", "REVIEW", "ADVANCE", "reviewer", "OK",
                               context={"reviewed_by": "reviewer", "authored_by": "admin"}),
        ]
        chained = build_event_chain(events)
        assert chained[0].previous_event_hash is None
        assert chained[1].previous_event_hash is not None
        assert chained[2].previous_event_hash is not None
        # Each hash should be unique
        hashes = {c.previous_event_hash for c in chained if c.previous_event_hash}
        assert len(hashes) == 2
