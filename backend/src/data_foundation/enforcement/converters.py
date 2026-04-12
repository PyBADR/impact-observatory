"""
Enforcement Layer — Pydantic ↔ ORM Converters
===============================================

8 functions: to_orm and from_orm for each of the 4 domain models.
Follows the same pattern as governance/converters.py.
"""

from __future__ import annotations

from .schemas import (
    EnforcementPolicy,
    EnforcementDecision,
    ExecutionGateResult,
    ApprovalRequest,
)
from .orm_models import (
    EnforcementPolicyORM,
    EnforcementDecisionORM,
    ExecutionGateResultORM,
    ApprovalRequestORM,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. EnforcementPolicy
# ═══════════════════════════════════════════════════════════════════════════════


def enforcement_policy_to_orm(p: EnforcementPolicy) -> EnforcementPolicyORM:
    return EnforcementPolicyORM(
        policy_id=p.policy_id,
        policy_name=p.policy_name,
        policy_name_ar=p.policy_name_ar,
        enforcement_action=p.enforcement_action,
        min_rule_status=p.min_rule_status,
        require_truth_validation=p.require_truth_validation,
        max_unresolved_calibrations=p.max_unresolved_calibrations,
        min_correctness_score=p.min_correctness_score,
        min_confidence_score=p.min_confidence_score,
        confidence_degradation_factor=p.confidence_degradation_factor,
        scope_risk_levels=p.scope_risk_levels,
        scope_actions=p.scope_actions,
        scope_countries=p.scope_countries,
        scope_sectors=p.scope_sectors,
        fallback_action=p.fallback_action,
        required_approver_role=p.required_approver_role,
        approval_timeout_hours=p.approval_timeout_hours,
        priority=p.priority,
        is_active=p.is_active,
        authored_by=p.authored_by,
        provenance_hash=p.provenance_hash,
    )


def enforcement_policy_from_orm(row: EnforcementPolicyORM) -> EnforcementPolicy:
    from datetime import datetime, timezone
    return EnforcementPolicy(
        policy_id=row.policy_id,
        policy_name=row.policy_name,
        policy_name_ar=row.policy_name_ar,
        enforcement_action=row.enforcement_action,
        min_rule_status=row.min_rule_status,
        require_truth_validation=row.require_truth_validation,
        max_unresolved_calibrations=row.max_unresolved_calibrations,
        min_correctness_score=row.min_correctness_score,
        min_confidence_score=row.min_confidence_score,
        confidence_degradation_factor=row.confidence_degradation_factor,
        scope_risk_levels=row.scope_risk_levels or [],
        scope_actions=row.scope_actions or [],
        scope_countries=row.scope_countries or [],
        scope_sectors=row.scope_sectors or [],
        fallback_action=row.fallback_action,
        required_approver_role=row.required_approver_role,
        approval_timeout_hours=row.approval_timeout_hours,
        priority=row.priority,
        is_active=row.is_active,
        authored_by=row.authored_by,
        created_at=row.created_at or datetime.now(timezone.utc),
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. EnforcementDecision
# ═══════════════════════════════════════════════════════════════════════════════


def enforcement_decision_to_orm(d: EnforcementDecision) -> EnforcementDecisionORM:
    return EnforcementDecisionORM(
        decision_id=d.decision_id,
        decision_log_id=d.decision_log_id,
        rule_id=d.rule_id,
        spec_id=d.spec_id,
        enforcement_action=d.enforcement_action,
        is_executable=d.is_executable,
        triggered_policy_ids=d.triggered_policy_ids,
        trigger_reasons=d.trigger_reasons,
        blocking_reasons=d.blocking_reasons,
        original_confidence=d.original_confidence,
        effective_confidence=d.effective_confidence,
        fallback_action=d.fallback_action,
        required_approver=d.required_approver,
        rule_status=d.rule_status,
        truth_valid=d.truth_valid,
        unresolved_calibrations=d.unresolved_calibrations,
        latest_correctness_score=d.latest_correctness_score,
        evaluated_at=d.evaluated_at,
        provenance_hash=d.provenance_hash,
    )


def enforcement_decision_from_orm(row: EnforcementDecisionORM) -> EnforcementDecision:
    return EnforcementDecision(
        decision_id=row.decision_id,
        decision_log_id=row.decision_log_id,
        rule_id=row.rule_id,
        spec_id=row.spec_id,
        enforcement_action=row.enforcement_action,
        is_executable=row.is_executable,
        triggered_policy_ids=row.triggered_policy_ids or [],
        trigger_reasons=row.trigger_reasons or [],
        blocking_reasons=row.blocking_reasons or [],
        original_confidence=row.original_confidence,
        effective_confidence=row.effective_confidence,
        fallback_action=row.fallback_action,
        required_approver=row.required_approver,
        rule_status=row.rule_status,
        truth_valid=row.truth_valid,
        unresolved_calibrations=row.unresolved_calibrations,
        latest_correctness_score=row.latest_correctness_score,
        evaluated_at=row.evaluated_at,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ExecutionGateResult
# ═══════════════════════════════════════════════════════════════════════════════


def execution_gate_to_orm(g: ExecutionGateResult) -> ExecutionGateResultORM:
    return ExecutionGateResultORM(
        gate_id=g.gate_id,
        enforcement_decision_id=g.enforcement_decision_id,
        decision_log_id=g.decision_log_id,
        gate_outcome=g.gate_outcome,
        may_execute=g.may_execute,
        approval_request_id=g.approval_request_id,
        applied_fallback_action=g.applied_fallback_action,
        applied_confidence=g.applied_confidence,
        is_shadow_mode=g.is_shadow_mode,
        resolved_at=g.resolved_at,
        provenance_hash=g.provenance_hash,
    )


def execution_gate_from_orm(row: ExecutionGateResultORM) -> ExecutionGateResult:
    return ExecutionGateResult(
        gate_id=row.gate_id,
        enforcement_decision_id=row.enforcement_decision_id,
        decision_log_id=row.decision_log_id,
        gate_outcome=row.gate_outcome,
        may_execute=row.may_execute,
        approval_request_id=row.approval_request_id,
        applied_fallback_action=row.applied_fallback_action,
        applied_confidence=row.applied_confidence,
        is_shadow_mode=row.is_shadow_mode,
        resolved_at=row.resolved_at,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ApprovalRequest
# ═══════════════════════════════════════════════════════════════════════════════


def approval_request_to_orm(a: ApprovalRequest) -> ApprovalRequestORM:
    return ApprovalRequestORM(
        request_id=a.request_id,
        enforcement_decision_id=a.enforcement_decision_id,
        decision_log_id=a.decision_log_id,
        gate_id=a.gate_id,
        required_approver_role=a.required_approver_role,
        status=a.status,
        approved_by=a.approved_by,
        approval_reason=a.approval_reason,
        timeout_hours=a.timeout_hours,
        expires_at=a.expires_at,
        requested_at=a.requested_at,
        resolved_at=a.resolved_at,
        provenance_hash=a.provenance_hash,
    )


def approval_request_from_orm(row: ApprovalRequestORM) -> ApprovalRequest:
    return ApprovalRequest(
        request_id=row.request_id,
        enforcement_decision_id=row.enforcement_decision_id,
        decision_log_id=row.decision_log_id,
        gate_id=row.gate_id,
        required_approver_role=row.required_approver_role,
        status=row.status,
        approved_by=row.approved_by,
        approval_reason=row.approval_reason,
        timeout_hours=row.timeout_hours,
        expires_at=row.expires_at,
        requested_at=row.requested_at,
        resolved_at=row.resolved_at,
        provenance_hash=row.provenance_hash or "",
    )
