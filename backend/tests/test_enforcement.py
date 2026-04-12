"""
Enforcement Layer — Comprehensive Test Suite
=============================================

Tests:
  - Schema instantiation and hash computation
  - Enforcement engine: policy matching, blocking, approval,
    fallback, shadow mode, confidence degradation
  - Execution gate service: gate resolution, approval lifecycle
  - Enforcement audit: audit entry creation and chain integrity
  - Constant classes and their ALL lists
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from src.data_foundation.enforcement.schemas import (
    ApprovalRequest,
    ApprovalStatus,
    EnforcementAction,
    EnforcementDecision,
    EnforcementPolicy,
    EnforcementTriggerType,
    ExecutionGateResult,
    GateOutcome,
)
from src.data_foundation.enforcement.enforcement_engine import (
    EnforcementContext,
    evaluate_enforcement,
    _scope_matches,
    _check_conditions,
)
from src.data_foundation.enforcement.execution_gate_service import (
    resolve_gate,
    resolve_approval,
)
from src.data_foundation.enforcement.enforcement_audit import (
    audit_enforcement_policy_created,
    audit_enforcement_evaluated,
    audit_gate_resolved,
    audit_approval_requested,
    audit_approval_resolved,
    ENFORCEMENT_EVENT_POLICY_CREATED,
    ENFORCEMENT_EVENT_EVALUATED,
    ENFORCEMENT_EVENT_GATE_RESOLVED,
    ENFORCEMENT_EVENT_APPROVAL_REQUESTED,
    ENFORCEMENT_EVENT_APPROVAL_RESOLVED,
)
from src.data_foundation.governance.governance_audit import verify_chain


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════


def _make_context(**overrides) -> EnforcementContext:
    defaults = dict(
        decision_log_id="DLOG-test-001",
        rule_id="RULE-test-001",
        spec_id="SPEC-test-001",
        decision_action="ALERT",
        decision_risk_level="ELEVATED",
        decision_country="SA",
        decision_sector="energy",
        decision_confidence=0.85,
        rule_status="ACTIVE",
        truth_valid=True,
        unresolved_calibrations=0,
        latest_correctness_score=0.90,
    )
    defaults.update(overrides)
    return EnforcementContext(**defaults)


def _make_policy(**overrides) -> EnforcementPolicy:
    defaults = dict(
        policy_name="Test Policy",
        enforcement_action=EnforcementAction.BLOCK,
        authored_by="test-author",
        is_active=True,
        priority=100,
    )
    defaults.update(overrides)
    return EnforcementPolicy(**defaults)


# ═══════════════════════════════════════════════════════════════════════════════
# Schema tests
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnforcementPolicySchema:
    def test_instantiation(self):
        p = _make_policy()
        assert p.policy_id.startswith("EPOL-")
        assert p.enforcement_action == EnforcementAction.BLOCK
        assert p.is_active is True

    def test_hash_computation(self):
        p = _make_policy()
        assert p.provenance_hash == ""
        p.compute_hash()
        assert len(p.provenance_hash) == 64  # SHA-256 hex

    def test_unique_ids(self):
        ids = {_make_policy().policy_id for _ in range(50)}
        assert len(ids) == 50


class TestEnforcementDecisionSchema:
    def test_instantiation(self):
        d = EnforcementDecision(
            decision_log_id="DLOG-1",
            rule_id="RULE-1",
            enforcement_action=EnforcementAction.ALLOW,
            is_executable=True,
            original_confidence=0.9,
            effective_confidence=0.9,
        )
        assert d.decision_id.startswith("ENFD-")
        assert d.is_executable is True

    def test_hash_computation(self):
        d = EnforcementDecision(
            decision_log_id="DLOG-1",
            rule_id="RULE-1",
            enforcement_action=EnforcementAction.BLOCK,
            is_executable=False,
            original_confidence=0.9,
            effective_confidence=0.9,
        )
        d.compute_hash()
        assert len(d.provenance_hash) == 64

    def test_executable_flag(self):
        assert EnforcementAction.ALLOW in EnforcementAction.EXECUTABLE
        assert EnforcementAction.DEGRADE_CONFIDENCE in EnforcementAction.EXECUTABLE
        assert EnforcementAction.BLOCK in EnforcementAction.NON_EXECUTABLE
        assert EnforcementAction.SHADOW_ONLY in EnforcementAction.NON_EXECUTABLE


class TestExecutionGateResultSchema:
    def test_instantiation(self):
        g = ExecutionGateResult(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            gate_outcome=GateOutcome.PROCEED,
            may_execute=True,
            applied_confidence=0.9,
        )
        assert g.gate_id.startswith("GATE-")
        assert g.may_execute is True

    def test_hash_computation(self):
        g = ExecutionGateResult(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            gate_outcome=GateOutcome.BLOCKED,
            may_execute=False,
            applied_confidence=0.5,
        )
        g.compute_hash()
        assert len(g.provenance_hash) == 64


class TestApprovalRequestSchema:
    def test_instantiation(self):
        a = ApprovalRequest(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            required_approver_role="chief_risk_officer",
        )
        assert a.request_id.startswith("AREQ-")
        assert a.status == ApprovalStatus.PENDING

    def test_hash_computation(self):
        a = ApprovalRequest(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            required_approver_role="cro",
        )
        a.compute_hash()
        assert len(a.provenance_hash) == 64


class TestConstantClasses:
    def test_enforcement_action_all(self):
        assert len(EnforcementAction.ALL) == 7
        for a in EnforcementAction.ALL:
            assert isinstance(a, str)

    def test_trigger_type_all(self):
        assert len(EnforcementTriggerType.ALL) == 13

    def test_approval_status_all(self):
        assert len(ApprovalStatus.ALL) == 4

    def test_gate_outcome_all(self):
        assert len(GateOutcome.ALL) == 5

    def test_executable_vs_non_executable_partition(self):
        all_actions = set(EnforcementAction.ALL)
        exe = EnforcementAction.EXECUTABLE
        non_exe = EnforcementAction.NON_EXECUTABLE
        assert exe | non_exe == all_actions
        assert exe & non_exe == set()


# ═══════════════════════════════════════════════════════════════════════════════
# Enforcement Engine — scope matching
# ═══════════════════════════════════════════════════════════════════════════════


class TestScopeMatching:
    def test_empty_scope_matches_all(self):
        policy = _make_policy()
        context = _make_context()
        assert _scope_matches(policy, context) is True

    def test_matching_risk_level(self):
        policy = _make_policy(scope_risk_levels=["ELEVATED", "HIGH"])
        context = _make_context(decision_risk_level="ELEVATED")
        assert _scope_matches(policy, context) is True

    def test_non_matching_risk_level(self):
        policy = _make_policy(scope_risk_levels=["SEVERE"])
        context = _make_context(decision_risk_level="ELEVATED")
        assert _scope_matches(policy, context) is False

    def test_matching_country(self):
        policy = _make_policy(scope_countries=["SA", "AE"])
        context = _make_context(decision_country="SA")
        assert _scope_matches(policy, context) is True

    def test_non_matching_country(self):
        policy = _make_policy(scope_countries=["AE"])
        context = _make_context(decision_country="SA")
        assert _scope_matches(policy, context) is False

    def test_matching_sector(self):
        policy = _make_policy(scope_sectors=["energy", "banking"])
        context = _make_context(decision_sector="energy")
        assert _scope_matches(policy, context) is True

    def test_non_matching_action(self):
        policy = _make_policy(scope_actions=["DIVEST"])
        context = _make_context(decision_action="ALERT")
        assert _scope_matches(policy, context) is False

    def test_null_context_field_passes(self):
        """If context field is None, scope check passes (no constraint)."""
        policy = _make_policy(scope_risk_levels=["HIGH"])
        context = _make_context(decision_risk_level=None)
        assert _scope_matches(policy, context) is True


# ═══════════════════════════════════════════════════════════════════════════════
# Enforcement Engine — condition checking
# ═══════════════════════════════════════════════════════════════════════════════


class TestConditionChecking:
    def test_rule_status_active_passes(self):
        policy = _make_policy(min_rule_status="ACTIVE")
        context = _make_context(rule_status="ACTIVE")
        fires, _ = _check_conditions(policy, context)
        assert fires is False

    def test_rule_status_draft_fails(self):
        policy = _make_policy(min_rule_status="ACTIVE")
        context = _make_context(rule_status="DRAFT")
        fires, reason = _check_conditions(policy, context)
        assert fires is True
        assert "below minimum" in reason

    def test_rule_status_review_fails(self):
        policy = _make_policy(min_rule_status="ACTIVE")
        context = _make_context(rule_status="REVIEW")
        fires, _ = _check_conditions(policy, context)
        assert fires is True

    def test_truth_validation_passed(self):
        policy = _make_policy(require_truth_validation=True)
        context = _make_context(truth_valid=True)
        fires, _ = _check_conditions(policy, context)
        assert fires is False

    def test_truth_validation_failed(self):
        policy = _make_policy(require_truth_validation=True)
        context = _make_context(truth_valid=False)
        fires, reason = _check_conditions(policy, context)
        assert fires is True
        assert "Truth validation" in reason

    def test_calibration_within_tolerance(self):
        policy = _make_policy(max_unresolved_calibrations=2)
        context = _make_context(unresolved_calibrations=1)
        fires, _ = _check_conditions(policy, context)
        assert fires is False

    def test_calibration_over_tolerance(self):
        policy = _make_policy(max_unresolved_calibrations=0)
        context = _make_context(unresolved_calibrations=3)
        fires, reason = _check_conditions(policy, context)
        assert fires is True
        assert "calibrations" in reason.lower()

    def test_correctness_above_threshold(self):
        policy = _make_policy(min_correctness_score=0.7)
        context = _make_context(latest_correctness_score=0.85)
        fires, _ = _check_conditions(policy, context)
        assert fires is False

    def test_correctness_below_threshold(self):
        policy = _make_policy(min_correctness_score=0.8)
        context = _make_context(latest_correctness_score=0.5)
        fires, reason = _check_conditions(policy, context)
        assert fires is True
        assert "Correctness" in reason

    def test_confidence_above_threshold(self):
        policy = _make_policy(min_confidence_score=0.6)
        context = _make_context(decision_confidence=0.85)
        fires, _ = _check_conditions(policy, context)
        assert fires is False

    def test_confidence_below_threshold(self):
        policy = _make_policy(min_confidence_score=0.9)
        context = _make_context(decision_confidence=0.5)
        fires, reason = _check_conditions(policy, context)
        assert fires is True
        assert "confidence" in reason.lower()

    def test_no_conditions_set_does_not_fire(self):
        """Policy with no conditions never fires (ALLOW by default)."""
        policy = _make_policy(
            min_rule_status=None,
            require_truth_validation=False,
            max_unresolved_calibrations=999,
            min_correctness_score=None,
            min_confidence_score=None,
        )
        context = _make_context()
        fires, _ = _check_conditions(policy, context)
        assert fires is False


# ═══════════════════════════════════════════════════════════════════════════════
# Enforcement Engine — full evaluation
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnforcementEvaluation:
    def test_no_policies_allows(self):
        """No policies = ALLOW."""
        context = _make_context()
        decision = evaluate_enforcement([], context)
        assert decision.enforcement_action == EnforcementAction.ALLOW
        assert decision.is_executable is True
        assert len(decision.triggered_policy_ids) == 0

    def test_single_block_policy(self):
        policy = _make_policy(
            enforcement_action=EnforcementAction.BLOCK,
            min_rule_status="ACTIVE",
        )
        context = _make_context(rule_status="DRAFT")
        decision = evaluate_enforcement([policy], context)
        assert decision.enforcement_action == EnforcementAction.BLOCK
        assert decision.is_executable is False
        assert policy.policy_id in decision.triggered_policy_ids

    def test_allow_when_conditions_met(self):
        policy = _make_policy(
            enforcement_action=EnforcementAction.BLOCK,
            min_rule_status="ACTIVE",
        )
        context = _make_context(rule_status="ACTIVE")
        decision = evaluate_enforcement([policy], context)
        assert decision.enforcement_action == EnforcementAction.ALLOW
        assert decision.is_executable is True

    def test_require_approval(self):
        policy = _make_policy(
            enforcement_action=EnforcementAction.REQUIRE_APPROVAL,
            min_confidence_score=0.9,
            required_approver_role="chief_risk_officer",
        )
        context = _make_context(decision_confidence=0.6)
        decision = evaluate_enforcement([policy], context)
        assert decision.enforcement_action == EnforcementAction.REQUIRE_APPROVAL
        assert decision.is_executable is False
        assert decision.required_approver == "chief_risk_officer"

    def test_shadow_only(self):
        policy = _make_policy(
            enforcement_action=EnforcementAction.SHADOW_ONLY,
            require_truth_validation=True,
        )
        context = _make_context(truth_valid=False)
        decision = evaluate_enforcement([policy], context)
        assert decision.enforcement_action == EnforcementAction.SHADOW_ONLY
        assert decision.is_executable is False

    def test_fallback(self):
        policy = _make_policy(
            enforcement_action=EnforcementAction.FALLBACK,
            min_correctness_score=0.8,
            fallback_action="MONITOR",
        )
        context = _make_context(latest_correctness_score=0.3)
        decision = evaluate_enforcement([policy], context)
        assert decision.enforcement_action == EnforcementAction.FALLBACK
        assert decision.fallback_action == "MONITOR"

    def test_confidence_degradation(self):
        policy = _make_policy(
            enforcement_action=EnforcementAction.DEGRADE_CONFIDENCE,
            max_unresolved_calibrations=0,
            confidence_degradation_factor=0.5,
        )
        context = _make_context(unresolved_calibrations=2, decision_confidence=0.8)
        decision = evaluate_enforcement([policy], context)
        assert decision.enforcement_action == EnforcementAction.DEGRADE_CONFIDENCE
        assert decision.is_executable is True
        assert decision.effective_confidence == pytest.approx(0.4, rel=1e-6)
        assert decision.original_confidence == 0.8

    def test_strictest_wins(self):
        """BLOCK (severity 100) wins over DEGRADE_CONFIDENCE (severity 50)."""
        block_policy = _make_policy(
            policy_id="EPOL-block",
            enforcement_action=EnforcementAction.BLOCK,
            min_rule_status="ACTIVE",
            priority=200,
        )
        degrade_policy = _make_policy(
            policy_id="EPOL-degrade",
            enforcement_action=EnforcementAction.DEGRADE_CONFIDENCE,
            max_unresolved_calibrations=0,
            confidence_degradation_factor=0.5,
            priority=100,
        )
        context = _make_context(rule_status="DRAFT", unresolved_calibrations=3)
        decision = evaluate_enforcement([degrade_policy, block_policy], context)
        assert decision.enforcement_action == EnforcementAction.BLOCK
        assert decision.is_executable is False
        assert len(decision.triggered_policy_ids) == 2

    def test_inactive_policy_skipped(self):
        policy = _make_policy(
            enforcement_action=EnforcementAction.BLOCK,
            min_rule_status="ACTIVE",
            is_active=False,
        )
        context = _make_context(rule_status="DRAFT")
        decision = evaluate_enforcement([policy], context)
        assert decision.enforcement_action == EnforcementAction.ALLOW

    def test_scope_mismatch_skipped(self):
        policy = _make_policy(
            enforcement_action=EnforcementAction.BLOCK,
            min_rule_status="ACTIVE",
            scope_countries=["AE"],
        )
        context = _make_context(rule_status="DRAFT", decision_country="SA")
        decision = evaluate_enforcement([policy], context)
        assert decision.enforcement_action == EnforcementAction.ALLOW

    def test_hash_computed(self):
        decision = evaluate_enforcement([], _make_context())
        assert len(decision.provenance_hash) == 64

    def test_deterministic(self):
        """Same inputs always produce same enforcement action."""
        policies = [
            _make_policy(
                policy_id="EPOL-fixed",
                enforcement_action=EnforcementAction.BLOCK,
                min_rule_status="ACTIVE",
            ),
        ]
        context = _make_context(rule_status="DRAFT")
        results = [evaluate_enforcement(policies, context).enforcement_action for _ in range(20)]
        assert all(r == EnforcementAction.BLOCK for r in results)

    def test_multiple_degradations_multiply(self):
        """Multiple DEGRADE_CONFIDENCE policies multiply their factors."""
        p1 = _make_policy(
            policy_id="EPOL-d1",
            enforcement_action=EnforcementAction.DEGRADE_CONFIDENCE,
            max_unresolved_calibrations=0,
            confidence_degradation_factor=0.5,
            priority=10,
        )
        p2 = _make_policy(
            policy_id="EPOL-d2",
            enforcement_action=EnforcementAction.DEGRADE_CONFIDENCE,
            min_confidence_score=0.95,
            confidence_degradation_factor=0.5,
            priority=20,
        )
        context = _make_context(
            unresolved_calibrations=1,
            decision_confidence=0.8,
        )
        decision = evaluate_enforcement([p1, p2], context)
        assert decision.enforcement_action == EnforcementAction.DEGRADE_CONFIDENCE
        # 0.8 * 0.5 * 0.5 = 0.2
        assert decision.effective_confidence == pytest.approx(0.2, rel=1e-6)


# ═══════════════════════════════════════════════════════════════════════════════
# Execution Gate Service
# ═══════════════════════════════════════════════════════════════════════════════


class TestGateResolution:
    def _make_decision(self, action: str, **kwargs) -> EnforcementDecision:
        defaults = dict(
            decision_log_id="DLOG-1",
            rule_id="RULE-1",
            enforcement_action=action,
            is_executable=action in EnforcementAction.EXECUTABLE,
            original_confidence=0.9,
            effective_confidence=kwargs.pop("effective_confidence", 0.9),
        )
        defaults.update(kwargs)
        return EnforcementDecision(**defaults)

    def test_allow_proceeds(self):
        d = self._make_decision(EnforcementAction.ALLOW)
        gate, approval = resolve_gate(d)
        assert gate.gate_outcome == GateOutcome.PROCEED
        assert gate.may_execute is True
        assert approval is None

    def test_degrade_confidence_proceeds(self):
        d = self._make_decision(EnforcementAction.DEGRADE_CONFIDENCE, effective_confidence=0.4)
        gate, approval = resolve_gate(d)
        assert gate.gate_outcome == GateOutcome.PROCEED
        assert gate.may_execute is True
        assert gate.applied_confidence == 0.4

    def test_block_blocks(self):
        d = self._make_decision(EnforcementAction.BLOCK)
        gate, approval = resolve_gate(d)
        assert gate.gate_outcome == GateOutcome.BLOCKED
        assert gate.may_execute is False
        assert approval is None

    def test_escalate_blocks(self):
        d = self._make_decision(EnforcementAction.ESCALATE)
        gate, approval = resolve_gate(d)
        assert gate.gate_outcome == GateOutcome.BLOCKED
        assert gate.may_execute is False

    def test_require_approval_creates_request(self):
        d = self._make_decision(
            EnforcementAction.REQUIRE_APPROVAL,
            required_approver="chief_risk_officer",
        )
        gate, approval = resolve_gate(d, approval_timeout_hours=48.0)
        assert gate.gate_outcome == GateOutcome.AWAITING_APPROVAL
        assert gate.may_execute is False
        assert approval is not None
        assert approval.status == ApprovalStatus.PENDING
        assert approval.required_approver_role == "chief_risk_officer"
        assert approval.timeout_hours == 48.0
        assert gate.approval_request_id == approval.request_id

    def test_shadow_only_shadow_mode(self):
        d = self._make_decision(EnforcementAction.SHADOW_ONLY)
        gate, approval = resolve_gate(d)
        assert gate.gate_outcome == GateOutcome.SHADOW_MODE
        assert gate.may_execute is False
        assert gate.is_shadow_mode is True
        assert approval is None

    def test_fallback_applies_action(self):
        d = self._make_decision(
            EnforcementAction.FALLBACK,
            fallback_action="MONITOR",
        )
        gate, approval = resolve_gate(d)
        assert gate.gate_outcome == GateOutcome.FALLBACK_APPLIED
        assert gate.may_execute is True
        assert gate.applied_fallback_action == "MONITOR"

    def test_gate_hash_computed(self):
        d = self._make_decision(EnforcementAction.ALLOW)
        gate, _ = resolve_gate(d)
        assert len(gate.provenance_hash) == 64


class TestApprovalResolution:
    def test_approve(self):
        a = ApprovalRequest(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            required_approver_role="cro",
        )
        resolved = resolve_approval(a, approved=True, approver="john.doe", reason="Reviewed")
        assert resolved.status == ApprovalStatus.APPROVED
        assert resolved.approved_by == "john.doe"
        assert resolved.resolved_at is not None

    def test_deny(self):
        a = ApprovalRequest(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            required_approver_role="cro",
        )
        resolved = resolve_approval(a, approved=False, approver="jane.doe", reason="Rejected")
        assert resolved.status == ApprovalStatus.DENIED
        assert resolved.approved_by == "jane.doe"

    def test_hash_computed(self):
        a = ApprovalRequest(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            required_approver_role="cro",
        )
        resolved = resolve_approval(a, approved=True, approver="x")
        assert len(resolved.provenance_hash) == 64


# ═══════════════════════════════════════════════════════════════════════════════
# Enforcement Audit
# ═══════════════════════════════════════════════════════════════════════════════


class TestEnforcementAudit:
    def test_policy_created_audit(self):
        policy = _make_policy()
        entry = audit_enforcement_policy_created(policy, "admin")
        assert entry.event_type == ENFORCEMENT_EVENT_POLICY_CREATED
        assert entry.subject_id == policy.policy_id
        assert entry.actor == "admin"
        assert len(entry.audit_hash) == 64

    def test_evaluated_audit(self):
        decision = EnforcementDecision(
            decision_log_id="DLOG-1",
            rule_id="RULE-1",
            enforcement_action=EnforcementAction.BLOCK,
            is_executable=False,
            original_confidence=0.9,
            effective_confidence=0.9,
        )
        entry = audit_enforcement_evaluated(decision)
        assert entry.event_type == ENFORCEMENT_EVENT_EVALUATED
        assert entry.subject_id == decision.decision_id

    def test_gate_resolved_audit(self):
        gate = ExecutionGateResult(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            gate_outcome=GateOutcome.BLOCKED,
            may_execute=False,
            applied_confidence=0.5,
        )
        entry = audit_gate_resolved(gate)
        assert entry.event_type == ENFORCEMENT_EVENT_GATE_RESOLVED

    def test_approval_requested_audit(self):
        a = ApprovalRequest(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            required_approver_role="cro",
        )
        entry = audit_approval_requested(a)
        assert entry.event_type == ENFORCEMENT_EVENT_APPROVAL_REQUESTED

    def test_approval_resolved_audit(self):
        a = ApprovalRequest(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            required_approver_role="cro",
            status=ApprovalStatus.APPROVED,
            approved_by="admin",
        )
        entry = audit_approval_resolved(a, "admin")
        assert entry.event_type == ENFORCEMENT_EVENT_APPROVAL_RESOLVED
        assert entry.actor == "admin"

    def test_audit_chain_integrity(self):
        """Build a chain of enforcement audit entries and verify."""
        policy = _make_policy()
        decision = EnforcementDecision(
            decision_log_id="DLOG-1",
            rule_id="RULE-1",
            enforcement_action=EnforcementAction.BLOCK,
            is_executable=False,
            original_confidence=0.9,
            effective_confidence=0.9,
        )
        gate = ExecutionGateResult(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            gate_outcome=GateOutcome.BLOCKED,
            may_execute=False,
            applied_confidence=0.5,
        )

        e1 = audit_enforcement_policy_created(policy, "admin", None)
        e2 = audit_enforcement_evaluated(decision, "system", e1.audit_hash)
        e3 = audit_gate_resolved(gate, "system", e2.audit_hash)

        violations = verify_chain([e1, e2, e3])
        assert violations == []


# ═══════════════════════════════════════════════════════════════════════════════
# Replay Integration — enforcement must answer executability
# ═══════════════════════════════════════════════════════════════════════════════


class TestReplayIntegration:
    """Test that the enforcement engine can be used in replay context."""

    def test_replay_enforcement_with_different_governance_states(self):
        """Simulate replay: same decision, different governance states → different enforcement."""
        policies = [
            _make_policy(
                policy_id="EPOL-replay-block",
                enforcement_action=EnforcementAction.BLOCK,
                min_rule_status="ACTIVE",
                priority=10,
            ),
        ]

        # Original: ACTIVE rule → ALLOW
        original_ctx = _make_context(rule_status="ACTIVE")
        original_decision = evaluate_enforcement(policies, original_ctx)
        assert original_decision.enforcement_action == EnforcementAction.ALLOW
        assert original_decision.is_executable is True

        # Replay with DRAFT rule → BLOCK
        replay_ctx = _make_context(rule_status="DRAFT")
        replay_decision = evaluate_enforcement(policies, replay_ctx)
        assert replay_decision.enforcement_action == EnforcementAction.BLOCK
        assert replay_decision.is_executable is False

    def test_replay_enforcement_with_calibration_drift(self):
        """Replay: calibration events changed → enforcement changes."""
        policies = [
            _make_policy(
                policy_id="EPOL-replay-cal",
                enforcement_action=EnforcementAction.SHADOW_ONLY,
                max_unresolved_calibrations=0,
                priority=10,
            ),
        ]

        # Original: no calibrations → ALLOW
        original = evaluate_enforcement(
            policies, _make_context(unresolved_calibrations=0)
        )
        assert original.enforcement_action == EnforcementAction.ALLOW

        # Replay: with calibrations → SHADOW_ONLY
        replay = evaluate_enforcement(
            policies, _make_context(unresolved_calibrations=2)
        )
        assert replay.enforcement_action == EnforcementAction.SHADOW_ONLY

    def test_replay_full_pipeline(self):
        """End-to-end: enforcement → gate → check executability."""
        policies = [
            _make_policy(
                enforcement_action=EnforcementAction.REQUIRE_APPROVAL,
                min_confidence_score=0.9,
                required_approver_role="cro",
            ),
        ]
        context = _make_context(decision_confidence=0.6)

        decision = evaluate_enforcement(policies, context)
        gate, approval = resolve_gate(decision)

        assert decision.enforcement_action == EnforcementAction.REQUIRE_APPROVAL
        assert gate.gate_outcome == GateOutcome.AWAITING_APPROVAL
        assert gate.may_execute is False
        assert approval is not None
        assert approval.status == ApprovalStatus.PENDING

        # Approve → would allow
        resolved = resolve_approval(approval, approved=True, approver="cro-user")
        assert resolved.status == ApprovalStatus.APPROVED


# ═══════════════════════════════════════════════════════════════════════════════
# Converter round-trip tests (no DB — schema ↔ ORM field mapping)
# ═══════════════════════════════════════════════════════════════════════════════


class TestConverterRoundTrip:
    def test_enforcement_policy_round_trip(self):
        from src.data_foundation.enforcement.converters import (
            enforcement_policy_to_orm,
            enforcement_policy_from_orm,
        )
        original = _make_policy(
            scope_risk_levels=["HIGH", "SEVERE"],
            fallback_action="MONITOR",
        )
        original.compute_hash()
        orm = enforcement_policy_to_orm(original)
        restored = enforcement_policy_from_orm(orm)
        assert restored.policy_id == original.policy_id
        assert restored.enforcement_action == original.enforcement_action
        assert restored.scope_risk_levels == ["HIGH", "SEVERE"]
        assert restored.fallback_action == "MONITOR"
        assert restored.provenance_hash == original.provenance_hash

    def test_enforcement_decision_round_trip(self):
        from src.data_foundation.enforcement.converters import (
            enforcement_decision_to_orm,
            enforcement_decision_from_orm,
        )
        original = EnforcementDecision(
            decision_log_id="DLOG-1",
            rule_id="RULE-1",
            enforcement_action=EnforcementAction.BLOCK,
            is_executable=False,
            triggered_policy_ids=["EPOL-1", "EPOL-2"],
            trigger_reasons=["RULE_NOT_ACTIVE"],
            blocking_reasons=["Rule not active"],
            original_confidence=0.9,
            effective_confidence=0.9,
        )
        original.compute_hash()
        orm = enforcement_decision_to_orm(original)
        restored = enforcement_decision_from_orm(orm)
        assert restored.triggered_policy_ids == ["EPOL-1", "EPOL-2"]
        assert restored.trigger_reasons == ["RULE_NOT_ACTIVE"]
        assert restored.provenance_hash == original.provenance_hash

    def test_execution_gate_round_trip(self):
        from src.data_foundation.enforcement.converters import (
            execution_gate_to_orm,
            execution_gate_from_orm,
        )
        original = ExecutionGateResult(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            gate_outcome=GateOutcome.FALLBACK_APPLIED,
            may_execute=True,
            applied_fallback_action="MONITOR",
            applied_confidence=0.5,
            is_shadow_mode=False,
        )
        original.compute_hash()
        orm = execution_gate_to_orm(original)
        restored = execution_gate_from_orm(orm)
        assert restored.gate_outcome == GateOutcome.FALLBACK_APPLIED
        assert restored.applied_fallback_action == "MONITOR"
        assert restored.provenance_hash == original.provenance_hash

    def test_approval_request_round_trip(self):
        from src.data_foundation.enforcement.converters import (
            approval_request_to_orm,
            approval_request_from_orm,
        )
        now = datetime.now(timezone.utc)
        original = ApprovalRequest(
            enforcement_decision_id="ENFD-1",
            decision_log_id="DLOG-1",
            required_approver_role="cro",
            timeout_hours=24.0,
            expires_at=now + timedelta(hours=24),
        )
        original.compute_hash()
        orm = approval_request_to_orm(original)
        restored = approval_request_from_orm(orm)
        assert restored.required_approver_role == "cro"
        assert restored.timeout_hours == 24.0
        assert restored.provenance_hash == original.provenance_hash
