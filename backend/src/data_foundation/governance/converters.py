"""
Governance Layer — Pydantic ↔ ORM Converters
==============================================

14 functions: to_orm and from_orm for each of the 7 domain models.
Follows the same pattern as evaluation/converters.py.
"""

from __future__ import annotations

from typing import Optional

from .schemas import (
    GovernancePolicy,
    RuleLifecycleEvent,
    TruthValidationPolicy,
    TruthValidationResult,
    CalibrationTrigger,
    CalibrationEvent,
    GovernanceAuditEntry,
)
from .orm_models import (
    GovernancePolicyORM,
    RuleLifecycleEventORM,
    TruthValidationPolicyORM,
    TruthValidationResultORM,
    CalibrationTriggerORM,
    CalibrationEventORM,
    GovernanceAuditEntryORM,
)


# ═══════════════════════════════════════════════════════════════════════════════
# 1. GovernancePolicy
# ═══════════════════════════════════════════════════════════════════════════════

def governance_policy_to_orm(p: GovernancePolicy) -> GovernancePolicyORM:
    return GovernancePolicyORM(
        policy_id=p.policy_id,
        policy_name=p.policy_name,
        policy_name_ar=p.policy_name_ar,
        policy_type=p.policy_type,
        scope_risk_levels=p.scope_risk_levels,
        scope_actions=p.scope_actions,
        scope_countries=p.scope_countries,
        scope_sectors=p.scope_sectors,
        policy_params=p.policy_params,
        is_active=p.is_active,
        effective_date=p.effective_date,
        expiry_date=p.expiry_date,
        authored_by=p.authored_by,
        approved_by=p.approved_by,
        created_at=p.created_at,
        provenance_hash=p.provenance_hash,
    )


def governance_policy_from_orm(row: GovernancePolicyORM) -> GovernancePolicy:
    return GovernancePolicy(
        policy_id=row.policy_id,
        policy_name=row.policy_name,
        policy_name_ar=row.policy_name_ar,
        policy_type=row.policy_type,
        scope_risk_levels=row.scope_risk_levels or [],
        scope_actions=row.scope_actions or [],
        scope_countries=row.scope_countries or [],
        scope_sectors=row.scope_sectors or [],
        policy_params=row.policy_params or {},
        is_active=row.is_active,
        effective_date=row.effective_date,
        expiry_date=row.expiry_date,
        authored_by=row.authored_by,
        approved_by=row.approved_by,
        created_at=row.created_at,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 2. RuleLifecycleEvent
# ═══════════════════════════════════════════════════════════════════════════════

def lifecycle_event_to_orm(e: RuleLifecycleEvent) -> RuleLifecycleEventORM:
    return RuleLifecycleEventORM(
        event_id=e.event_id,
        spec_id=e.spec_id,
        from_status=e.from_status,
        to_status=e.to_status,
        transition_type=e.transition_type,
        actor=e.actor,
        actor_role=e.actor_role,
        reason=e.reason,
        validation_result_snapshot=e.validation_result_snapshot,
        policy_id=e.policy_id,
        supersedes_spec_id=e.supersedes_spec_id,
        occurred_at=e.occurred_at,
        provenance_hash=e.provenance_hash,
        previous_event_hash=e.previous_event_hash,
    )


def lifecycle_event_from_orm(row: RuleLifecycleEventORM) -> RuleLifecycleEvent:
    return RuleLifecycleEvent(
        event_id=row.event_id,
        spec_id=row.spec_id,
        from_status=row.from_status,
        to_status=row.to_status,
        transition_type=row.transition_type,
        actor=row.actor,
        actor_role=row.actor_role,
        reason=row.reason,
        validation_result_snapshot=row.validation_result_snapshot or {},
        policy_id=row.policy_id,
        supersedes_spec_id=row.supersedes_spec_id,
        occurred_at=row.occurred_at,
        provenance_hash=row.provenance_hash or "",
        previous_event_hash=row.previous_event_hash,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TruthValidationPolicy
# ═══════════════════════════════════════════════════════════════════════════════

def truth_policy_to_orm(p: TruthValidationPolicy) -> TruthValidationPolicyORM:
    return TruthValidationPolicyORM(
        policy_id=p.policy_id,
        target_dataset=p.target_dataset,
        policy_name=p.policy_name,
        source_priority_order=p.source_priority_order,
        freshness_max_hours=p.freshness_max_hours,
        completeness_min_fields=p.completeness_min_fields,
        corroboration_required=p.corroboration_required,
        corroboration_min_sources=p.corroboration_min_sources,
        deviation_max_pct=p.deviation_max_pct,
        validation_rules=p.validation_rules,
        is_active=p.is_active,
        authored_by=p.authored_by,
        created_at=p.created_at,
        provenance_hash=p.provenance_hash,
    )


def truth_policy_from_orm(row: TruthValidationPolicyORM) -> TruthValidationPolicy:
    return TruthValidationPolicy(
        policy_id=row.policy_id,
        target_dataset=row.target_dataset,
        policy_name=row.policy_name,
        source_priority_order=row.source_priority_order or [],
        freshness_max_hours=row.freshness_max_hours,
        completeness_min_fields=row.completeness_min_fields,
        corroboration_required=row.corroboration_required,
        corroboration_min_sources=row.corroboration_min_sources,
        deviation_max_pct=row.deviation_max_pct,
        validation_rules=row.validation_rules or [],
        is_active=row.is_active,
        authored_by=row.authored_by,
        created_at=row.created_at,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TruthValidationResult
# ═══════════════════════════════════════════════════════════════════════════════

def truth_result_to_orm(r: TruthValidationResult) -> TruthValidationResultORM:
    return TruthValidationResultORM(
        result_id=r.result_id,
        policy_id=r.policy_id,
        target_dataset=r.target_dataset,
        record_id=r.record_id,
        is_valid=r.is_valid,
        freshness_passed=r.freshness_passed,
        completeness_passed=r.completeness_passed,
        corroboration_passed=r.corroboration_passed,
        field_checks_passed=r.field_checks_passed,
        field_checks_failed=r.field_checks_failed,
        failure_details=r.failure_details,
        validated_at=r.validated_at,
        provenance_hash=r.provenance_hash,
    )


def truth_result_from_orm(row: TruthValidationResultORM) -> TruthValidationResult:
    return TruthValidationResult(
        result_id=row.result_id,
        policy_id=row.policy_id,
        target_dataset=row.target_dataset,
        record_id=row.record_id,
        is_valid=row.is_valid,
        freshness_passed=row.freshness_passed,
        completeness_passed=row.completeness_passed,
        corroboration_passed=row.corroboration_passed,
        field_checks_passed=row.field_checks_passed,
        field_checks_failed=row.field_checks_failed,
        failure_details=row.failure_details or [],
        validated_at=row.validated_at,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CalibrationTrigger
# ═══════════════════════════════════════════════════════════════════════════════

def calibration_trigger_to_orm(t: CalibrationTrigger) -> CalibrationTriggerORM:
    return CalibrationTriggerORM(
        trigger_id=t.trigger_id,
        trigger_name=t.trigger_name,
        trigger_type=t.trigger_type,
        target_metric=t.target_metric,
        threshold_operator=t.threshold_operator,
        threshold_value=t.threshold_value,
        lookback_window_days=t.lookback_window_days,
        min_evaluations=t.min_evaluations,
        is_active=t.is_active,
        authored_by=t.authored_by,
        created_at=t.created_at,
        provenance_hash=t.provenance_hash,
    )


def calibration_trigger_from_orm(row: CalibrationTriggerORM) -> CalibrationTrigger:
    return CalibrationTrigger(
        trigger_id=row.trigger_id,
        trigger_name=row.trigger_name,
        trigger_type=row.trigger_type,
        target_metric=row.target_metric,
        threshold_operator=row.threshold_operator,
        threshold_value=row.threshold_value,
        lookback_window_days=row.lookback_window_days,
        min_evaluations=row.min_evaluations,
        is_active=row.is_active,
        authored_by=row.authored_by,
        created_at=row.created_at,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CalibrationEvent
# ═══════════════════════════════════════════════════════════════════════════════

def calibration_event_to_orm(e: CalibrationEvent) -> CalibrationEventORM:
    return CalibrationEventORM(
        event_id=e.event_id,
        trigger_id=e.trigger_id,
        rule_id=e.rule_id,
        spec_id=e.spec_id,
        metric_value=e.metric_value,
        threshold_value=e.threshold_value,
        lookback_start=e.lookback_start,
        lookback_end=e.lookback_end,
        sample_size=e.sample_size,
        status=e.status,
        resolved_by=e.resolved_by,
        resolution_notes=e.resolution_notes,
        triggered_at=e.triggered_at,
        resolved_at=e.resolved_at,
        provenance_hash=e.provenance_hash,
    )


def calibration_event_from_orm(row: CalibrationEventORM) -> CalibrationEvent:
    return CalibrationEvent(
        event_id=row.event_id,
        trigger_id=row.trigger_id,
        rule_id=row.rule_id,
        spec_id=row.spec_id,
        metric_value=row.metric_value,
        threshold_value=row.threshold_value,
        lookback_start=row.lookback_start,
        lookback_end=row.lookback_end,
        sample_size=row.sample_size,
        status=row.status,
        resolved_by=row.resolved_by,
        resolution_notes=row.resolution_notes,
        triggered_at=row.triggered_at,
        resolved_at=row.resolved_at,
        provenance_hash=row.provenance_hash or "",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# 7. GovernanceAuditEntry
# ═══════════════════════════════════════════════════════════════════════════════

def audit_entry_to_orm(a: GovernanceAuditEntry) -> GovernanceAuditEntryORM:
    return GovernanceAuditEntryORM(
        entry_id=a.entry_id,
        event_type=a.event_type,
        subject_type=a.subject_type,
        subject_id=a.subject_id,
        actor=a.actor,
        actor_role=a.actor_role,
        detail=a.detail,
        occurred_at=a.occurred_at,
        audit_hash=a.audit_hash,
        previous_audit_hash=a.previous_audit_hash,
        provenance_hash=a.audit_hash,  # audit_hash IS the provenance hash
    )


def audit_entry_from_orm(row: GovernanceAuditEntryORM) -> GovernanceAuditEntry:
    return GovernanceAuditEntry(
        entry_id=row.entry_id,
        event_type=row.event_type,
        subject_type=row.subject_type,
        subject_id=row.subject_id,
        actor=row.actor,
        actor_role=row.actor_role,
        detail=row.detail or {},
        occurred_at=row.occurred_at,
        audit_hash=row.audit_hash or "",
        previous_audit_hash=row.previous_audit_hash,
    )
