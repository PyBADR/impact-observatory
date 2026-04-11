"""Tests for governance audit chain."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.data_foundation.governance.governance_audit import (
    audit_calibration_resolved,
    audit_calibration_triggered,
    audit_lifecycle_transition,
    audit_override_applied,
    audit_policy_created,
    audit_policy_updated,
    audit_truth_validation,
    compute_hash,
    create_audit_entry,
    verify_chain,
)
from src.data_foundation.governance.schemas import GovernanceAuditEntry


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class TestCreateAuditEntry:
    def test_basic_entry(self):
        entry = create_audit_entry(
            "POLICY_CREATED", "GOVERNANCE_POLICY", "GPOL-001", "admin",
        )
        assert entry.entry_id.startswith("GAUD-")
        assert entry.event_type == "POLICY_CREATED"
        assert entry.audit_hash is not None

    def test_entry_with_detail(self):
        entry = create_audit_entry(
            "POLICY_UPDATED", "GOVERNANCE_POLICY", "GPOL-001", "admin",
            detail={"changed_field": "scope_countries"},
        )
        assert entry.detail["changed_field"] == "scope_countries"

    def test_entry_with_previous_hash(self):
        entry = create_audit_entry(
            "POLICY_CREATED", "GOVERNANCE_POLICY", "GPOL-001", "admin",
            previous_audit_hash="abc123",
        )
        assert entry.previous_audit_hash == "abc123"

    def test_hash_is_sha256(self):
        entry = create_audit_entry(
            "POLICY_CREATED", "GOVERNANCE_POLICY", "GPOL-001", "admin",
        )
        assert len(entry.audit_hash) == 64  # SHA-256 hex

    def test_different_entries_different_hashes(self):
        e1 = create_audit_entry("POLICY_CREATED", "GOVERNANCE_POLICY", "GPOL-A", "admin")
        e2 = create_audit_entry("POLICY_CREATED", "GOVERNANCE_POLICY", "GPOL-B", "admin")
        assert e1.audit_hash != e2.audit_hash


class TestComputeHash:
    def test_deterministic(self):
        now = _utcnow()
        entry = GovernanceAuditEntry(
            entry_id="GAUD-FIXED",
            event_type="POLICY_CREATED",
            subject_type="GOVERNANCE_POLICY",
            subject_id="GPOL-001",
            actor="admin",
            occurred_at=now,
        )
        h1 = compute_hash(entry)
        h2 = compute_hash(entry)
        assert h1 == h2

    def test_changes_with_different_data(self):
        now = _utcnow()
        base = dict(
            event_type="POLICY_CREATED",
            subject_type="GOVERNANCE_POLICY",
            actor="admin",
            occurred_at=now,
        )
        e1 = GovernanceAuditEntry(entry_id="GAUD-1", subject_id="A", **base)
        e2 = GovernanceAuditEntry(entry_id="GAUD-2", subject_id="B", **base)
        assert compute_hash(e1) != compute_hash(e2)


class TestConvenienceFactories:
    def test_audit_policy_created(self):
        entry = audit_policy_created("GPOL-001", "admin", {"type": "APPROVAL_GATE"})
        assert entry.event_type == "POLICY_CREATED"
        assert entry.subject_type == "GOVERNANCE_POLICY"

    def test_audit_policy_updated(self):
        entry = audit_policy_updated("GPOL-001", "admin")
        assert entry.event_type == "POLICY_UPDATED"

    def test_audit_lifecycle_transition(self):
        entry = audit_lifecycle_transition("RULE-001", "analyst", {"from": "DRAFT", "to": "REVIEW"})
        assert entry.event_type == "LIFECYCLE_TRANSITION"
        assert entry.subject_type == "RULE_SPEC"

    def test_audit_truth_validation(self):
        entry = audit_truth_validation("TVP-001", "system")
        assert entry.event_type == "TRUTH_VALIDATION"
        assert entry.subject_type == "TRUTH_POLICY"

    def test_audit_calibration_triggered(self):
        entry = audit_calibration_triggered("CTRIG-001", "system")
        assert entry.event_type == "CALIBRATION_TRIGGERED"
        assert entry.subject_type == "CALIBRATION_TRIGGER"

    def test_audit_calibration_resolved(self):
        entry = audit_calibration_resolved("CTRIG-001", "analyst")
        assert entry.event_type == "CALIBRATION_RESOLVED"

    def test_audit_override_applied(self):
        entry = audit_override_applied("DLOG-001", "cro", {"reason": "override"})
        assert entry.event_type == "OVERRIDE_APPLIED"
        assert entry.subject_type == "DECISION_LOG"


class TestVerifyChain:
    def test_valid_chain(self):
        e1 = create_audit_entry("POLICY_CREATED", "GOVERNANCE_POLICY", "GPOL-001", "admin")
        e2 = create_audit_entry("POLICY_UPDATED", "GOVERNANCE_POLICY", "GPOL-001", "admin",
                                previous_audit_hash=e1.audit_hash)
        e3 = create_audit_entry("LIFECYCLE_TRANSITION", "RULE_SPEC", "RULE-001", "analyst",
                                previous_audit_hash=e2.audit_hash)
        result = verify_chain([e1, e2, e3])
        assert result["valid"] is True
        assert result["total_entries"] == 3
        assert result["verified"] == 3
        assert result["tampered"] == []
        assert result["chain_breaks"] == []

    def test_tampered_entry(self):
        e1 = create_audit_entry("POLICY_CREATED", "GOVERNANCE_POLICY", "GPOL-001", "admin")
        e2 = create_audit_entry("POLICY_UPDATED", "GOVERNANCE_POLICY", "GPOL-001", "admin",
                                previous_audit_hash=e1.audit_hash)
        # Tamper with e2's hash
        e2.audit_hash = "0000000000000000000000000000000000000000000000000000000000000000"
        result = verify_chain([e1, e2])
        assert result["valid"] is False
        assert e2.entry_id in result["tampered"]

    def test_broken_chain(self):
        e1 = create_audit_entry("POLICY_CREATED", "GOVERNANCE_POLICY", "GPOL-001", "admin")
        e2 = create_audit_entry("POLICY_UPDATED", "GOVERNANCE_POLICY", "GPOL-001", "admin",
                                previous_audit_hash="wrong_hash")
        result = verify_chain([e1, e2])
        assert result["valid"] is False
        assert e2.entry_id in result["chain_breaks"]

    def test_single_entry_chain(self):
        e1 = create_audit_entry("POLICY_CREATED", "GOVERNANCE_POLICY", "GPOL-001", "admin")
        result = verify_chain([e1])
        assert result["valid"] is True
        assert result["total_entries"] == 1

    def test_empty_chain(self):
        result = verify_chain([])
        assert result["valid"] is True
        assert result["total_entries"] == 0


class TestPackageImports:
    def test_import_schemas(self):
        from src.data_foundation.governance.schemas import (
            GovernancePolicy, RuleLifecycleEvent, TruthValidationPolicy,
            TruthValidationResult, CalibrationTrigger, CalibrationEvent,
            GovernanceAuditEntry,
        )

    def test_import_orm(self):
        from src.data_foundation.governance.orm_models import (
            GovernancePolicyORM, RuleLifecycleEventORM,
            TruthValidationPolicyORM, TruthValidationResultORM,
            CalibrationTriggerORM, CalibrationEventORM,
            GovernanceAuditEntryORM,
        )

    def test_import_converters(self):
        from src.data_foundation.governance.converters import (
            governance_policy_to_orm, governance_policy_from_orm,
            calibration_trigger_to_orm, calibration_trigger_from_orm,
        )

    def test_import_repositories(self):
        from src.data_foundation.governance.repositories import (
            GovernancePolicyRepository, RuleLifecycleEventRepository,
            TruthValidationPolicyRepository, TruthValidationResultRepository,
            CalibrationTriggerRepository, CalibrationEventRepository,
            GovernanceAuditEntryRepository,
        )

    def test_import_package_root(self):
        from src.data_foundation.governance import (
            GovernancePolicy, validate_transition, check_freshness,
            evaluate_threshold, compute_hash, verify_chain,
        )
