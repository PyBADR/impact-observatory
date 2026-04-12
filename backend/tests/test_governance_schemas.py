"""
Governance Schemas — Instantiation + Validation Tests
=======================================================

Validates:
  1. All 7 schemas instantiate without Pydantic errors
  2. Default values are correct
  3. Hash computation works (SHA-256, 64-char hex)
  4. ID generation produces unique IDs
  5. Constant class values are correct
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone, date

from src.data_foundation.governance.schemas import (
    GovernancePolicy,
    RuleLifecycleEvent,
    TruthValidationPolicy,
    TruthValidationResult,
    CalibrationTrigger,
    CalibrationEvent,
    CalibrationEventStatus,
    GovernanceAuditEntry,
    PolicyType,
    SpecStatus,
    TransitionType,
    CalibrationTriggerType,
    GovernanceEventType,
    GovernanceSubjectType,
)


# ═══════════════════════════════════════════════════════════════════════════════
# GovernancePolicy
# ═══════════════════════════════════════════════════════════════════════════════


class TestGovernancePolicy:

    def test_instantiation(self):
        p = GovernancePolicy(
            policy_name="SEVERE Approval Gate",
            policy_type=PolicyType.APPROVAL_GATE,
            authored_by="admin",
        )
        assert p.policy_id.startswith("GPOL-")
        assert p.policy_name == "SEVERE Approval Gate"
        assert p.is_active is True
        assert p.scope_risk_levels == []
        assert p.policy_params == {}

    def test_hash_computation(self):
        p = GovernancePolicy(
            policy_name="Test",
            policy_type=PolicyType.RETENTION,
            authored_by="admin",
        )
        p.compute_hash()
        assert p.provenance_hash != ""
        assert len(p.provenance_hash) == 64

    def test_unique_ids(self):
        ids = set()
        for _ in range(100):
            p = GovernancePolicy(
                policy_name="T", policy_type="RETENTION", authored_by="a",
            )
            ids.add(p.policy_id)
        assert len(ids) == 100

    def test_with_scope(self):
        p = GovernancePolicy(
            policy_name="KW Escalation",
            policy_type=PolicyType.ESCALATION_PATH,
            scope_countries=["KW", "SA"],
            scope_risk_levels=["SEVERE", "HIGH"],
            authored_by="admin",
        )
        assert len(p.scope_countries) == 2
        assert len(p.scope_risk_levels) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# RuleLifecycleEvent
# ═══════════════════════════════════════════════════════════════════════════════


class TestRuleLifecycleEvent:

    def test_instantiation(self):
        e = RuleLifecycleEvent(
            spec_id="SPEC-OIL-1",
            from_status=SpecStatus.DRAFT,
            to_status=SpecStatus.REVIEW,
            transition_type=TransitionType.ADVANCE,
            actor="analyst-1",
            reason="Ready for review.",
        )
        assert e.event_id.startswith("RLCE-")
        assert e.from_status == "DRAFT"
        assert e.to_status == "REVIEW"

    def test_hash_with_chaining(self):
        e = RuleLifecycleEvent(
            spec_id="SPEC-1",
            to_status=SpecStatus.DRAFT,
            transition_type=TransitionType.CREATE,
            actor="admin",
            reason="Initial.",
            previous_event_hash="abc123",
        )
        e.compute_hash()
        assert e.provenance_hash != ""
        assert len(e.provenance_hash) == 64

    def test_create_has_null_from(self):
        e = RuleLifecycleEvent(
            spec_id="SPEC-1",
            to_status=SpecStatus.DRAFT,
            transition_type=TransitionType.CREATE,
            actor="admin",
            reason="New.",
        )
        assert e.from_status is None


# ═══════════════════════════════════════════════════════════════════════════════
# TruthValidationPolicy
# ═══════════════════════════════════════════════════════════════════════════════


class TestTruthValidationPolicy:

    def test_instantiation(self):
        p = TruthValidationPolicy(
            target_dataset="p1_oil_energy_signals",
            policy_name="Oil Signal Truth",
            source_priority_order=["IEA", "OPEC", "Reuters"],
            authored_by="admin",
        )
        assert p.policy_id.startswith("TVP-")
        assert p.freshness_max_hours == 24.0
        assert p.completeness_min_fields == 1
        assert p.corroboration_required is False

    def test_with_validation_rules(self):
        p = TruthValidationPolicy(
            target_dataset="p1_macro_indicators",
            policy_name="Macro Truth",
            source_priority_order=["CBK", "IMF"],
            validation_rules=[
                {"field": "gdp_growth", "check": "range", "min": -50, "max": 50},
                {"field": "country_code", "check": "not_null"},
            ],
            authored_by="admin",
        )
        assert len(p.validation_rules) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# TruthValidationResult
# ═══════════════════════════════════════════════════════════════════════════════


class TestTruthValidationResult:

    def test_instantiation(self):
        r = TruthValidationResult(
            policy_id="TVP-1",
            target_dataset="p1_oil_energy_signals",
            record_id="REC-001",
            is_valid=True,
        )
        assert r.result_id.startswith("TVR-")
        assert r.freshness_passed is True
        assert r.completeness_passed is True
        assert r.corroboration_passed is None

    def test_hash_computation(self):
        r = TruthValidationResult(
            policy_id="TVP-1",
            target_dataset="test",
            record_id="REC-1",
            is_valid=False,
        )
        r.compute_hash()
        assert len(r.provenance_hash) == 64


# ═══════════════════════════════════════════════════════════════════════════════
# CalibrationTrigger
# ═══════════════════════════════════════════════════════════════════════════════


class TestCalibrationTrigger:

    def test_instantiation(self):
        t = CalibrationTrigger(
            trigger_name="Confidence Drift Alert",
            trigger_type=CalibrationTriggerType.CONFIDENCE_DRIFT,
            target_metric="avg_confidence_gap",
            threshold_operator="gt",
            threshold_value=0.25,
            authored_by="admin",
        )
        assert t.trigger_id.startswith("CTRIG-")
        assert t.lookback_window_days == 30
        assert t.min_evaluations == 5

    def test_hash_computation(self):
        t = CalibrationTrigger(
            trigger_name="FP Spike",
            trigger_type=CalibrationTriggerType.FALSE_POSITIVE_SPIKE,
            target_metric="false_positive_count",
            threshold_operator="gt",
            threshold_value=3.0,
            authored_by="admin",
        )
        t.compute_hash()
        assert len(t.provenance_hash) == 64


# ═══════════════════════════════════════════════════════════════════════════════
# CalibrationEvent
# ═══════════════════════════════════════════════════════════════════════════════


class TestCalibrationEvent:

    def test_instantiation(self):
        now = datetime.now(timezone.utc)
        e = CalibrationEvent(
            trigger_id="CTRIG-1",
            rule_id="RULE-OIL-1",
            metric_value=0.35,
            threshold_value=0.25,
            lookback_start=now,
            lookback_end=now,
            sample_size=10,
        )
        assert e.event_id.startswith("CALEV-")
        assert e.status == CalibrationEventStatus.TRIGGERED
        assert e.resolved_by is None

    def test_hash_computation(self):
        now = datetime.now(timezone.utc)
        e = CalibrationEvent(
            trigger_id="CTRIG-1",
            rule_id="RULE-1",
            metric_value=0.5,
            threshold_value=0.3,
            lookback_start=now,
            lookback_end=now,
            sample_size=8,
        )
        e.compute_hash()
        assert len(e.provenance_hash) == 64


# ═══════════════════════════════════════════════════════════════════════════════
# GovernanceAuditEntry
# ═══════════════════════════════════════════════════════════════════════════════


class TestGovernanceAuditEntry:

    def test_instantiation(self):
        e = GovernanceAuditEntry(
            event_type=GovernanceEventType.POLICY_CREATED,
            subject_type=GovernanceSubjectType.GOVERNANCE_POLICY,
            subject_id="GPOL-1",
            actor="admin",
        )
        assert e.entry_id.startswith("GAUD-")
        assert e.audit_hash == ""
        assert e.previous_audit_hash is None

    def test_hash_with_chaining(self):
        e = GovernanceAuditEntry(
            event_type=GovernanceEventType.LIFECYCLE_TRANSITION,
            subject_type=GovernanceSubjectType.RULE_SPEC,
            subject_id="SPEC-1",
            actor="admin",
            previous_audit_hash="prev_hash_abc",
        )
        e.compute_hash()
        assert len(e.audit_hash) == 64
        assert e.previous_audit_hash == "prev_hash_abc"

    def test_deterministic_hash(self):
        """Same data → same hash."""
        hashes = set()
        for _ in range(50):
            e = GovernanceAuditEntry(
                entry_id="GAUD-fixed",
                event_type="POLICY_CREATED",
                subject_type="GOVERNANCE_POLICY",
                subject_id="GPOL-fixed",
                actor="admin",
                detail={"key": "value"},
                previous_audit_hash=None,
            )
            # Fix occurred_at for determinism
            e.occurred_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
            e.compute_hash()
            hashes.add(e.audit_hash)
        assert len(hashes) == 1, "Audit hash is non-deterministic!"


# ═══════════════════════════════════════════════════════════════════════════════
# Enum/Constant classes
# ═══════════════════════════════════════════════════════════════════════════════


class TestConstantClasses:

    def test_policy_type_values(self):
        assert len(PolicyType.ALL) == 5
        assert "APPROVAL_GATE" in PolicyType.ALL

    def test_spec_status_values(self):
        assert len(SpecStatus.ALL) == 6
        assert "ACTIVE" in SpecStatus.ALL
        assert SpecStatus.SUPERSEDED in SpecStatus.TERMINAL
        assert SpecStatus.RETIRED in SpecStatus.TERMINAL
        assert SpecStatus.ACTIVE not in SpecStatus.TERMINAL

    def test_transition_type_values(self):
        assert len(TransitionType.ALL) == 5

    def test_calibration_trigger_type_values(self):
        assert len(CalibrationTriggerType.ALL) == 6

    def test_calibration_event_status_values(self):
        assert len(CalibrationEventStatus.ALL) == 4

    def test_governance_event_type_values(self):
        assert len(GovernanceEventType.ALL) == 10

    def test_governance_subject_type_values(self):
        assert len(GovernanceSubjectType.ALL) == 5
