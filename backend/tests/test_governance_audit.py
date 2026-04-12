"""
Governance Audit Chain — Tests
================================

Validates:
  1. Audit entry creation with SHA-256 hash
  2. Hash chaining (previous_audit_hash linkage)
  3. Convenience factories for each event type
  4. Chain verification — valid and tampered chains
  5. Chain summary reporting
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, timedelta

from src.data_foundation.governance.schemas import (
    GovernancePolicy,
    RuleLifecycleEvent,
    TruthValidationResult,
    CalibrationEvent,
    GovernanceAuditEntry,
    GovernanceEventType,
    GovernanceSubjectType,
    PolicyType,
    SpecStatus,
    TransitionType,
    CalibrationEventStatus,
)
from src.data_foundation.governance.governance_audit import (
    create_audit_entry,
    audit_policy_created,
    audit_policy_updated,
    audit_policy_deactivated,
    audit_lifecycle_transition,
    audit_truth_validation,
    audit_calibration_triggered,
    audit_calibration_resolved,
    verify_chain,
    get_chain_summary,
)


NOW = datetime(2026, 4, 12, 12, 0, 0, tzinfo=timezone.utc)


def _make_policy():
    return GovernancePolicy(
        policy_name="Test Policy",
        policy_type=PolicyType.APPROVAL_GATE,
        authored_by="admin",
    )


def _make_lifecycle_event():
    return RuleLifecycleEvent(
        spec_id="SPEC-OIL-1",
        from_status=SpecStatus.DRAFT,
        to_status=SpecStatus.REVIEW,
        transition_type=TransitionType.ADVANCE,
        actor="analyst-1",
        reason="Ready.",
    )


def _make_truth_result():
    return TruthValidationResult(
        policy_id="TVP-1",
        target_dataset="p1_oil_energy_signals",
        record_id="REC-1",
        is_valid=False,
        field_checks_failed=2,
    )


def _make_calibration_event():
    return CalibrationEvent(
        trigger_id="CTRIG-1",
        rule_id="RULE-OIL-1",
        metric_value=0.35,
        threshold_value=0.25,
        lookback_start=NOW - timedelta(days=30),
        lookback_end=NOW,
        sample_size=10,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Core entry creation
# ═══════════════════════════════════════════════════════════════════════════════


class TestCreateAuditEntry:

    def test_creates_entry_with_hash(self):
        entry = create_audit_entry(
            event_type=GovernanceEventType.POLICY_CREATED,
            subject_type=GovernanceSubjectType.GOVERNANCE_POLICY,
            subject_id="GPOL-1",
            actor="admin",
        )
        assert entry.entry_id.startswith("GAUD-")
        assert len(entry.audit_hash) == 64
        assert entry.previous_audit_hash is None

    def test_chaining(self):
        e1 = create_audit_entry(
            event_type="POLICY_CREATED",
            subject_type="GOVERNANCE_POLICY",
            subject_id="GPOL-1",
            actor="admin",
        )
        e2 = create_audit_entry(
            event_type="POLICY_UPDATED",
            subject_type="GOVERNANCE_POLICY",
            subject_id="GPOL-1",
            actor="admin",
            previous_audit_hash=e1.audit_hash,
        )
        assert e2.previous_audit_hash == e1.audit_hash
        assert e2.audit_hash != e1.audit_hash

    def test_with_detail(self):
        entry = create_audit_entry(
            event_type="OVERRIDE_APPLIED",
            subject_type="DECISION_LOG",
            subject_id="DLOG-1",
            actor="cro",
            detail={"override_score": 0.9, "reason": "Manual override."},
        )
        assert entry.detail["override_score"] == 0.9


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience factories
# ═══════════════════════════════════════════════════════════════════════════════


class TestConvenienceFactories:

    def test_audit_policy_created(self):
        policy = _make_policy()
        entry = audit_policy_created(policy, actor="admin")
        assert entry.event_type == GovernanceEventType.POLICY_CREATED
        assert entry.subject_type == GovernanceSubjectType.GOVERNANCE_POLICY
        assert entry.subject_id == policy.policy_id
        assert entry.detail["policy_type"] == PolicyType.APPROVAL_GATE

    def test_audit_policy_updated(self):
        policy = _make_policy()
        entry = audit_policy_updated(
            policy, actor="admin", changes={"is_active": False},
        )
        assert entry.event_type == GovernanceEventType.POLICY_UPDATED
        assert entry.detail["changes"]["is_active"] is False

    def test_audit_policy_deactivated(self):
        policy = _make_policy()
        entry = audit_policy_deactivated(policy, actor="admin", reason="Expired.")
        assert entry.event_type == GovernanceEventType.POLICY_DEACTIVATED
        assert entry.detail["reason"] == "Expired."

    def test_audit_lifecycle_transition(self):
        event = _make_lifecycle_event()
        entry = audit_lifecycle_transition(event, actor="analyst-1")
        assert entry.event_type == GovernanceEventType.LIFECYCLE_TRANSITION
        assert entry.subject_type == GovernanceSubjectType.RULE_SPEC
        assert entry.subject_id == "SPEC-OIL-1"
        assert entry.detail["from_status"] == SpecStatus.DRAFT
        assert entry.detail["to_status"] == SpecStatus.REVIEW

    def test_audit_truth_validation(self):
        result = _make_truth_result()
        entry = audit_truth_validation(result, actor="system")
        assert entry.event_type == GovernanceEventType.TRUTH_VALIDATION
        assert entry.subject_type == GovernanceSubjectType.TRUTH_POLICY
        assert entry.detail["is_valid"] is False

    def test_audit_calibration_triggered(self):
        event = _make_calibration_event()
        entry = audit_calibration_triggered(event, actor="system")
        assert entry.event_type == GovernanceEventType.CALIBRATION_TRIGGERED
        assert entry.detail["metric_value"] == 0.35

    def test_audit_calibration_resolved(self):
        event = _make_calibration_event()
        event.status = CalibrationEventStatus.RESOLVED
        event.resolved_by = "cro"
        event.resolution_notes = "Threshold adjusted."
        entry = audit_calibration_resolved(event, actor="cro")
        assert entry.event_type == GovernanceEventType.CALIBRATION_RESOLVED
        assert entry.detail["resolved_by"] == "cro"


# ═══════════════════════════════════════════════════════════════════════════════
# Chain verification
# ═══════════════════════════════════════════════════════════════════════════════


class TestChainVerification:

    def _build_chain(self, length: int = 5) -> list:
        chain = []
        prev_hash = None
        for i in range(length):
            entry = create_audit_entry(
                event_type="POLICY_CREATED",
                subject_type="GOVERNANCE_POLICY",
                subject_id=f"GPOL-{i}",
                actor="admin",
                previous_audit_hash=prev_hash,
            )
            chain.append(entry)
            prev_hash = entry.audit_hash
        return chain

    def test_valid_chain(self):
        chain = self._build_chain(5)
        violations = verify_chain(chain)
        assert violations == []

    def test_single_entry_valid(self):
        chain = self._build_chain(1)
        violations = verify_chain(chain)
        assert violations == []

    def test_empty_chain_valid(self):
        violations = verify_chain([])
        assert violations == []

    def test_tampered_hash_detected(self):
        chain = self._build_chain(3)
        # Tamper with middle entry's hash
        chain[1].audit_hash = "tampered_hash_value_0000000000000000000000000000000000"
        violations = verify_chain(chain)
        assert len(violations) > 0
        # Should detect self-hash mismatch on entry 1 AND chain break on entry 2
        violation_types = [v["reason"] for v in violations]
        assert "self_hash_mismatch" in violation_types or "chain_link_broken" in violation_types

    def test_broken_chain_link_detected(self):
        chain = self._build_chain(3)
        # Break the chain by setting wrong previous hash
        chain[2].previous_audit_hash = "wrong_hash"
        # Recompute to make self-hash valid but chain broken
        chain[2].compute_hash()
        violations = verify_chain(chain)
        assert len(violations) > 0
        assert any(v["reason"] == "chain_link_broken" for v in violations)


# ═══════════════════════════════════════════════════════════════════════════════
# Chain summary
# ═══════════════════════════════════════════════════════════════════════════════


class TestChainSummary:

    def test_empty_chain_summary(self):
        summary = get_chain_summary([])
        assert summary["total_entries"] == 0
        assert summary["chain_valid"] is True

    def test_valid_chain_summary(self):
        chain = []
        prev = None
        for i in range(3):
            e = create_audit_entry(
                event_type="POLICY_CREATED" if i < 2 else "LIFECYCLE_TRANSITION",
                subject_type="GOVERNANCE_POLICY",
                subject_id=f"GPOL-{i}",
                actor="admin" if i < 2 else "analyst",
                previous_audit_hash=prev,
            )
            chain.append(e)
            prev = e.audit_hash

        summary = get_chain_summary(chain)
        assert summary["total_entries"] == 3
        assert summary["chain_valid"] is True
        assert summary["event_type_counts"]["POLICY_CREATED"] == 2
        assert summary["event_type_counts"]["LIFECYCLE_TRANSITION"] == 1
        assert summary["actor_counts"]["admin"] == 2
        assert summary["actor_counts"]["analyst"] == 1
