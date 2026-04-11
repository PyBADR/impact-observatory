"""Governance & Calibration — ORM ↔ Pydantic converter functions.

14 converter functions (to_orm + from_orm for each of 7 models).
"""

from __future__ import annotations

from src.data_foundation.governance.orm_models import (
    CalibrationEventORM,
    CalibrationTriggerORM,
    GovernanceAuditEntryORM,
    GovernancePolicyORM,
    RuleLifecycleEventORM,
    TruthValidationPolicyORM,
    TruthValidationResultORM,
)
from src.data_foundation.governance.schemas import (
    CalibrationEvent,
    CalibrationTrigger,
    GovernanceAuditEntry,
    GovernancePolicy,
    RuleLifecycleEvent,
    TruthValidationPolicy,
    TruthValidationResult,
)

__all__ = [
    "governance_policy_to_orm", "governance_policy_from_orm",
    "rule_lifecycle_event_to_orm", "rule_lifecycle_event_from_orm",
    "truth_validation_policy_to_orm", "truth_validation_policy_from_orm",
    "truth_validation_result_to_orm", "truth_validation_result_from_orm",
    "calibration_trigger_to_orm", "calibration_trigger_from_orm",
    "calibration_event_to_orm", "calibration_event_from_orm",
    "governance_audit_entry_to_orm", "governance_audit_entry_from_orm",
]


# ── GovernancePolicy ────────────────────────────────────────────────────────

def governance_policy_to_orm(schema: GovernancePolicy) -> GovernancePolicyORM:
    return GovernancePolicyORM(
        policy_id=schema.policy_id,
        policy_name=schema.policy_name,
        policy_type=schema.policy_type,
        scope_risk_levels=schema.scope_risk_levels or None,
        scope_actions=schema.scope_actions or None,
        scope_countries=schema.scope_countries or None,
        scope_sectors=schema.scope_sectors or None,
        policy_params=schema.policy_params or None,
        is_active=schema.is_active,
        effective_date=schema.effective_date,
        expiry_date=schema.expiry_date,
        authored_by=schema.authored_by,
        approved_by=schema.approved_by,
        provenance_hash=schema.provenance_hash,
    )


def governance_policy_from_orm(orm: GovernancePolicyORM) -> GovernancePolicy:
    return GovernancePolicy.model_validate(orm)


# ── RuleLifecycleEvent ──────────────────────────────────────────────────────

def rule_lifecycle_event_to_orm(schema: RuleLifecycleEvent) -> RuleLifecycleEventORM:
    return RuleLifecycleEventORM(
        event_id=schema.event_id,
        spec_id=schema.spec_id,
        from_status=schema.from_status,
        to_status=schema.to_status,
        transition_type=schema.transition_type,
        actor=schema.actor,
        actor_role=schema.actor_role,
        reason=schema.reason,
        validation_result_snapshot=schema.validation_result_snapshot or None,
        policy_id=schema.policy_id,
        occurred_at=schema.occurred_at,
        previous_event_hash=schema.previous_event_hash,
        provenance_hash=schema.provenance_hash,
    )


def rule_lifecycle_event_from_orm(orm: RuleLifecycleEventORM) -> RuleLifecycleEvent:
    return RuleLifecycleEvent.model_validate(orm)


# ── TruthValidationPolicy ──────────────────────────────────────────────────

def truth_validation_policy_to_orm(schema: TruthValidationPolicy) -> TruthValidationPolicyORM:
    return TruthValidationPolicyORM(
        policy_id=schema.policy_id,
        target_dataset=schema.target_dataset,
        policy_name=schema.policy_name,
        source_priority_order=schema.source_priority_order or None,
        freshness_max_hours=schema.freshness_max_hours,
        completeness_min_fields=schema.completeness_min_fields,
        corroboration_required=schema.corroboration_required,
        corroboration_min_sources=schema.corroboration_min_sources,
        deviation_max_pct=schema.deviation_max_pct,
        validation_rules=schema.validation_rules or None,
        is_active=schema.is_active,
        authored_by=schema.authored_by,
        provenance_hash=schema.provenance_hash,
    )


def truth_validation_policy_from_orm(orm: TruthValidationPolicyORM) -> TruthValidationPolicy:
    return TruthValidationPolicy.model_validate(orm)


# ── TruthValidationResult ──────────────────────────────────────────────────

def truth_validation_result_to_orm(schema: TruthValidationResult) -> TruthValidationResultORM:
    return TruthValidationResultORM(
        result_id=schema.result_id,
        policy_id=schema.policy_id,
        target_dataset=schema.target_dataset,
        record_id=schema.record_id,
        is_valid=schema.is_valid,
        freshness_passed=schema.freshness_passed,
        completeness_passed=schema.completeness_passed,
        corroboration_passed=schema.corroboration_passed,
        field_checks_passed=schema.field_checks_passed,
        field_checks_failed=schema.field_checks_failed,
        failure_details=schema.failure_details or None,
        validated_at=schema.validated_at,
        provenance_hash=schema.provenance_hash,
    )


def truth_validation_result_from_orm(orm: TruthValidationResultORM) -> TruthValidationResult:
    return TruthValidationResult.model_validate(orm)


# ── CalibrationTrigger ──────────────────────────────────────────────────────

def calibration_trigger_to_orm(schema: CalibrationTrigger) -> CalibrationTriggerORM:
    return CalibrationTriggerORM(
        trigger_id=schema.trigger_id,
        trigger_name=schema.trigger_name,
        trigger_type=schema.trigger_type,
        target_metric=schema.target_metric,
        threshold_operator=schema.threshold_operator,
        threshold_value=schema.threshold_value,
        lookback_window_days=schema.lookback_window_days,
        min_evaluations=schema.min_evaluations,
        is_active=schema.is_active,
        authored_by=schema.authored_by,
        provenance_hash=schema.provenance_hash,
    )


def calibration_trigger_from_orm(orm: CalibrationTriggerORM) -> CalibrationTrigger:
    return CalibrationTrigger.model_validate(orm)


# ── CalibrationEvent ────────────────────────────────────────────────────────

def calibration_event_to_orm(schema: CalibrationEvent) -> CalibrationEventORM:
    return CalibrationEventORM(
        event_id=schema.event_id,
        trigger_id=schema.trigger_id,
        rule_id=schema.rule_id,
        spec_id=schema.spec_id,
        metric_value=schema.metric_value,
        threshold_value=schema.threshold_value,
        lookback_start=schema.lookback_start,
        lookback_end=schema.lookback_end,
        sample_size=schema.sample_size,
        status=schema.status,
        resolved_by=schema.resolved_by,
        resolution_notes=schema.resolution_notes,
        triggered_at=schema.triggered_at,
        resolved_at=schema.resolved_at,
        provenance_hash=schema.provenance_hash,
    )


def calibration_event_from_orm(orm: CalibrationEventORM) -> CalibrationEvent:
    return CalibrationEvent.model_validate(orm)


# ── GovernanceAuditEntry ────────────────────────────────────────────────────

def governance_audit_entry_to_orm(schema: GovernanceAuditEntry) -> GovernanceAuditEntryORM:
    return GovernanceAuditEntryORM(
        entry_id=schema.entry_id,
        event_type=schema.event_type,
        subject_type=schema.subject_type,
        subject_id=schema.subject_id,
        actor=schema.actor,
        actor_role=schema.actor_role,
        detail=schema.detail or None,
        occurred_at=schema.occurred_at,
        audit_hash=schema.audit_hash,
        previous_audit_hash=schema.previous_audit_hash,
        provenance_hash=schema.provenance_hash,
    )


def governance_audit_entry_from_orm(orm: GovernanceAuditEntryORM) -> GovernanceAuditEntry:
    return GovernanceAuditEntry.model_validate(orm)
