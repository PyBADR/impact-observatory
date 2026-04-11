"""Tests for governance schemas — instantiation, validation, constants."""

from __future__ import annotations

from datetime import date, datetime, timezone

import pytest

from src.data_foundation.governance.schemas import (
    CalibrationEvent,
    CalibrationTrigger,
    GovernanceAuditEntry,
    GovernancePolicy,
    RuleLifecycleEvent,
    TruthValidationPolicy,
    TruthValidationResult,
    VALID_AUDIT_EVENT_TYPES,
    VALID_AUDIT_SUBJECT_TYPES,
    VALID_CALIBRATION_STATUSES,
    VALID_CALIBRATION_TRIGGER_TYPES,
    VALID_LIFECYCLE_STATUSES,
    VALID_POLICY_TYPES,
    VALID_THRESHOLD_OPERATORS,
    VALID_TRANSITION_TYPES,
)


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestGovernancePolicy:
    def test_valid_policy(self):
        p = GovernancePolicy(
            policy_id="GPOL-TEST-001",
            policy_name="Test Policy",
            policy_type="APPROVAL_GATE",
            effective_date=date(2026, 1, 1),
            authored_by="admin",
        )
        assert p.policy_id == "GPOL-TEST-001"
        assert p.is_active is True

    def test_all_policy_types_valid(self):
        for pt in VALID_POLICY_TYPES:
            p = GovernancePolicy(
                policy_id=f"GPOL-{pt}",
                policy_name=f"Test {pt}",
                policy_type=pt,
                effective_date=date(2026, 1, 1),
                authored_by="admin",
            )
            assert p.policy_type == pt

    def test_invalid_policy_type(self):
        with pytest.raises(Exception):
            GovernancePolicy(
                policy_id="GPOL-BAD",
                policy_name="Bad",
                policy_type="INVALID",
                effective_date=date(2026, 1, 1),
                authored_by="admin",
            )

    def test_provenance_hash_computed(self):
        p = GovernancePolicy(
            policy_id="GPOL-HASH",
            policy_name="Hash Test",
            policy_type="RETENTION",
            effective_date=date(2026, 1, 1),
            authored_by="admin",
        )
        assert p.provenance_hash is not None
        assert len(p.provenance_hash) == 64  # SHA-256

    def test_unique_hashes(self):
        p1 = GovernancePolicy(
            policy_id="GPOL-A", policy_name="A", policy_type="RETENTION",
            effective_date=date(2026, 1, 1), authored_by="admin",
        )
        p2 = GovernancePolicy(
            policy_id="GPOL-B", policy_name="B", policy_type="RETENTION",
            effective_date=date(2026, 1, 1), authored_by="admin",
        )
        assert p1.provenance_hash != p2.provenance_hash


class TestRuleLifecycleEvent:
    def test_valid_event(self):
        e = RuleLifecycleEvent(
            event_id="RLE-001",
            spec_id="RULE-OIL-001",
            from_status="DRAFT",
            to_status="REVIEW",
            transition_type="ADVANCE",
            actor="analyst-1",
            reason="Ready for review.",
            occurred_at=_utcnow(),
        )
        assert e.to_status == "REVIEW"

    def test_create_null_from_status(self):
        e = RuleLifecycleEvent(
            event_id="RLE-002",
            spec_id="RULE-NEW",
            from_status=None,
            to_status="DRAFT",
            transition_type="CREATE",
            actor="admin",
            reason="New rule.",
            occurred_at=_utcnow(),
        )
        assert e.from_status is None

    def test_invalid_to_status(self):
        with pytest.raises(Exception):
            RuleLifecycleEvent(
                event_id="RLE-BAD", spec_id="RULE-X",
                to_status="IMAGINARY", transition_type="ADVANCE",
                actor="x", reason="y", occurred_at=_utcnow(),
            )

    def test_invalid_transition_type(self):
        with pytest.raises(Exception):
            RuleLifecycleEvent(
                event_id="RLE-BAD", spec_id="RULE-X",
                to_status="REVIEW", transition_type="TELEPORT",
                actor="x", reason="y", occurred_at=_utcnow(),
            )


class TestTruthValidationPolicy:
    def test_valid_policy(self):
        p = TruthValidationPolicy(
            policy_id="TVP-OIL-001",
            target_dataset="oil_energy_signals",
            policy_name="Oil data truth",
            authored_by="admin",
        )
        assert p.freshness_max_hours == 24.0
        assert p.corroboration_required is False

    def test_with_validation_rules(self):
        p = TruthValidationPolicy(
            policy_id="TVP-FX-001",
            target_dataset="fx_signals",
            policy_name="FX truth",
            validation_rules=[
                {"field": "rate_value", "check": "range", "min": 0, "max": 5000},
            ],
            authored_by="admin",
        )
        assert len(p.validation_rules) == 1


class TestTruthValidationResult:
    def test_valid_result(self):
        r = TruthValidationResult(
            result_id="TVR-001",
            policy_id="TVP-OIL-001",
            target_dataset="oil_energy_signals",
            record_id="REC-001",
            is_valid=True,
            freshness_passed=True,
            completeness_passed=True,
            validated_at=_utcnow(),
        )
        assert r.is_valid is True


class TestCalibrationTrigger:
    def test_valid_trigger(self):
        t = CalibrationTrigger(
            trigger_id="CTRIG-FP-SPIKE",
            trigger_name="False positive spike",
            trigger_type="FALSE_POSITIVE_SPIKE",
            target_metric="false_positive_rate",
            threshold_operator="gt",
            threshold_value=0.30,
            authored_by="admin",
        )
        assert t.min_evaluations == 5

    def test_all_trigger_types(self):
        for tt in VALID_CALIBRATION_TRIGGER_TYPES:
            CalibrationTrigger(
                trigger_id=f"CTRIG-{tt}", trigger_name=tt,
                trigger_type=tt, target_metric="x",
                threshold_operator="gt", threshold_value=0.5,
                authored_by="admin",
            )

    def test_invalid_trigger_type(self):
        with pytest.raises(Exception):
            CalibrationTrigger(
                trigger_id="CTRIG-BAD", trigger_name="Bad",
                trigger_type="ML_MAGIC", target_metric="x",
                threshold_operator="gt", threshold_value=0.5,
                authored_by="admin",
            )

    def test_all_operators(self):
        for op in VALID_THRESHOLD_OPERATORS:
            CalibrationTrigger(
                trigger_id=f"CTRIG-{op}", trigger_name=op,
                trigger_type="MANUAL", target_metric="x",
                threshold_operator=op, threshold_value=0.5,
                authored_by="admin",
            )


class TestCalibrationEvent:
    def test_valid_event(self):
        e = CalibrationEvent(
            event_id="CEVT-001",
            trigger_id="CTRIG-FP",
            rule_id="RULE-001",
            metric_value=0.45,
            threshold_value=0.30,
            lookback_start=_utcnow(),
            lookback_end=_utcnow(),
            sample_size=50,
            triggered_at=_utcnow(),
        )
        assert e.status == "TRIGGERED"

    def test_invalid_status(self):
        with pytest.raises(Exception):
            CalibrationEvent(
                event_id="CEVT-BAD", trigger_id="CTRIG-X",
                rule_id="RULE-X", metric_value=0.5, threshold_value=0.3,
                lookback_start=_utcnow(), lookback_end=_utcnow(),
                sample_size=10, status="CANCELLED", triggered_at=_utcnow(),
            )


class TestGovernanceAuditEntry:
    def test_valid_entry(self):
        e = GovernanceAuditEntry(
            entry_id="GAUD-001",
            event_type="POLICY_CREATED",
            subject_type="GOVERNANCE_POLICY",
            subject_id="GPOL-001",
            actor="admin",
            occurred_at=_utcnow(),
        )
        assert e.event_type == "POLICY_CREATED"

    def test_invalid_event_type(self):
        with pytest.raises(Exception):
            GovernanceAuditEntry(
                entry_id="GAUD-BAD",
                event_type="MAGIC_EVENT",
                subject_type="GOVERNANCE_POLICY",
                subject_id="GPOL-001",
                actor="admin",
                occurred_at=_utcnow(),
            )

    def test_invalid_subject_type(self):
        with pytest.raises(Exception):
            GovernanceAuditEntry(
                entry_id="GAUD-BAD",
                event_type="POLICY_CREATED",
                subject_type="UNICORN",
                subject_id="GPOL-001",
                actor="admin",
                occurred_at=_utcnow(),
            )


class TestConstants:
    def test_policy_types_nonempty(self):
        assert len(VALID_POLICY_TYPES) == 5

    def test_lifecycle_statuses_nonempty(self):
        assert len(VALID_LIFECYCLE_STATUSES) == 6

    def test_transition_types_nonempty(self):
        assert len(VALID_TRANSITION_TYPES) == 5

    def test_calibration_trigger_types_nonempty(self):
        assert len(VALID_CALIBRATION_TRIGGER_TYPES) == 6

    def test_calibration_statuses_nonempty(self):
        assert len(VALID_CALIBRATION_STATUSES) == 4

    def test_audit_event_types_nonempty(self):
        assert len(VALID_AUDIT_EVENT_TYPES) == 9

    def test_audit_subject_types_nonempty(self):
        assert len(VALID_AUDIT_SUBJECT_TYPES) == 5

    def test_threshold_operators_nonempty(self):
        assert len(VALID_THRESHOLD_OPERATORS) == 5
