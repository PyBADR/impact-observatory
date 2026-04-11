"""Governance & Calibration Layer — Pydantic v2 schemas.

Seven domain models:

  GovernancePolicy           — meta-rules governing decision actions
  RuleLifecycleEvent         — immutable log of rule spec status transitions
  TruthValidationPolicy      — what constitutes "truth" for a dataset
  TruthValidationResult      — output of validating data against a policy
  CalibrationTrigger         — when a rule should be recalibrated
  CalibrationEvent           — log of triggered calibrations
  GovernanceAuditEntry       — SHA-256 hash-chained audit trail

All inherit FoundationModel.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from pydantic import Field, field_validator

from src.data_foundation.schemas.base import FoundationModel

__all__ = [
    "GovernancePolicy",
    "RuleLifecycleEvent",
    "TruthValidationPolicy",
    "TruthValidationResult",
    "CalibrationTrigger",
    "CalibrationEvent",
    "GovernanceAuditEntry",
    # Constants
    "VALID_POLICY_TYPES",
    "VALID_LIFECYCLE_STATUSES",
    "VALID_TRANSITION_TYPES",
    "VALID_CALIBRATION_TRIGGER_TYPES",
    "VALID_CALIBRATION_STATUSES",
    "VALID_AUDIT_EVENT_TYPES",
    "VALID_AUDIT_SUBJECT_TYPES",
    "VALID_THRESHOLD_OPERATORS",
]

# ═══════════════════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════════════════

VALID_POLICY_TYPES = {
    "APPROVAL_GATE", "ESCALATION_PATH", "RETENTION",
    "REVIEW_CYCLE", "OVERRIDE_LIMIT",
}

VALID_LIFECYCLE_STATUSES = {
    "DRAFT", "REVIEW", "APPROVED", "ACTIVE",
    "RETIRED", "SUPERSEDED",
}

VALID_TRANSITION_TYPES = {
    "CREATE", "ADVANCE", "REJECT", "RETIRE", "SUPERSEDE",
}

VALID_CALIBRATION_TRIGGER_TYPES = {
    "CONFIDENCE_DRIFT", "FALSE_POSITIVE_SPIKE", "FALSE_NEGATIVE_SPIKE",
    "REVIEW_DATE_EXPIRY", "CORRECTNESS_DEGRADATION", "MANUAL",
}

VALID_CALIBRATION_STATUSES = {
    "TRIGGERED", "ACKNOWLEDGED", "RESOLVED", "DISMISSED",
}

VALID_AUDIT_EVENT_TYPES = {
    "POLICY_CREATED", "POLICY_UPDATED", "LIFECYCLE_TRANSITION",
    "TRUTH_VALIDATION", "CALIBRATION_TRIGGERED", "CALIBRATION_RESOLVED",
    "OVERRIDE_APPLIED", "APPROVAL_GRANTED", "APPROVAL_DENIED",
}

VALID_AUDIT_SUBJECT_TYPES = {
    "GOVERNANCE_POLICY", "RULE_SPEC", "TRUTH_POLICY",
    "CALIBRATION_TRIGGER", "DECISION_LOG",
}

VALID_THRESHOLD_OPERATORS = {"gt", "lt", "gte", "lte", "exceeds_threshold"}


# ═══════════════════════════════════════════════════════════════════════════════
# Domain Models
# ═══════════════════════════════════════════════════════════════════════════════

class GovernancePolicy(FoundationModel):
    """Meta-rules governing decision actions — configurable by risk/sector/country."""

    policy_id: str = Field(..., description="Format: GPOL-{SCOPE}-{VARIANT}")
    policy_name: str = Field(..., min_length=1)
    policy_type: str = Field(...)
    scope_risk_levels: List[str] = Field(default_factory=list, description="Empty = all risk levels.")
    scope_actions: List[str] = Field(default_factory=list, description="Empty = all actions.")
    scope_countries: List[str] = Field(default_factory=list, description="Empty = all GCC countries.")
    scope_sectors: List[str] = Field(default_factory=list, description="Empty = all sectors.")
    policy_params: Dict[str, Any] = Field(default_factory=dict, description="Type-specific config.")
    is_active: bool = Field(default=True)
    effective_date: date = Field(...)
    expiry_date: Optional[date] = Field(default=None)
    authored_by: str = Field(..., min_length=1)
    approved_by: Optional[str] = Field(default=None)

    @field_validator("policy_type")
    @classmethod
    def _check_policy_type(cls, v: str) -> str:
        if v not in VALID_POLICY_TYPES:
            raise ValueError(f"policy_type must be one of {VALID_POLICY_TYPES}, got '{v}'")
        return v


class RuleLifecycleEvent(FoundationModel):
    """Immutable log of a rule spec status transition."""

    event_id: str = Field(...)
    spec_id: str = Field(...)
    from_status: Optional[str] = Field(default=None, description="Null for CREATE.")
    to_status: str = Field(...)
    transition_type: str = Field(...)
    actor: str = Field(..., min_length=1)
    actor_role: Optional[str] = Field(default=None)
    reason: str = Field(..., min_length=1)
    validation_result_snapshot: Dict[str, Any] = Field(default_factory=dict)
    policy_id: Optional[str] = Field(default=None)
    occurred_at: datetime = Field(...)
    previous_event_hash: Optional[str] = Field(default=None)

    @field_validator("to_status")
    @classmethod
    def _check_to_status(cls, v: str) -> str:
        if v not in VALID_LIFECYCLE_STATUSES:
            raise ValueError(f"to_status must be one of {VALID_LIFECYCLE_STATUSES}, got '{v}'")
        return v

    @field_validator("from_status")
    @classmethod
    def _check_from_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_LIFECYCLE_STATUSES:
            raise ValueError(f"from_status must be one of {VALID_LIFECYCLE_STATUSES}, got '{v}'")
        return v

    @field_validator("transition_type")
    @classmethod
    def _check_transition_type(cls, v: str) -> str:
        if v not in VALID_TRANSITION_TYPES:
            raise ValueError(f"transition_type must be one of {VALID_TRANSITION_TYPES}, got '{v}'")
        return v


class TruthValidationPolicy(FoundationModel):
    """What constitutes 'truth' for a specific dataset."""

    policy_id: str = Field(..., description="Format: TVP-{DATASET}-{VARIANT}")
    target_dataset: str = Field(..., min_length=1)
    policy_name: str = Field(..., min_length=1)
    source_priority_order: List[str] = Field(default_factory=list, description="Ranked source IDs.")
    freshness_max_hours: float = Field(default=24.0, ge=0.0)
    completeness_min_fields: int = Field(default=1, ge=0)
    corroboration_required: bool = Field(default=False)
    corroboration_min_sources: int = Field(default=2, ge=1)
    deviation_max_pct: Optional[float] = Field(default=None, ge=0.0)
    validation_rules: List[Dict[str, Any]] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    authored_by: str = Field(..., min_length=1)


class TruthValidationResult(FoundationModel):
    """Output of validating a data record against a TruthValidationPolicy."""

    result_id: str = Field(...)
    policy_id: str = Field(...)
    target_dataset: str = Field(...)
    record_id: str = Field(...)
    is_valid: bool = Field(...)
    freshness_passed: bool = Field(...)
    completeness_passed: bool = Field(...)
    corroboration_passed: Optional[bool] = Field(default=None, description="Null if not required.")
    field_checks_passed: int = Field(default=0, ge=0)
    field_checks_failed: int = Field(default=0, ge=0)
    failure_details: List[Dict[str, Any]] = Field(default_factory=list)
    validated_at: datetime = Field(...)


class CalibrationTrigger(FoundationModel):
    """Deterministic conditions under which a rule should be recalibrated."""

    trigger_id: str = Field(..., description="Format: CTRIG-{CONDITION}")
    trigger_name: str = Field(..., min_length=1)
    trigger_type: str = Field(...)
    target_metric: str = Field(..., min_length=1, description="Which evaluation metric to monitor.")
    threshold_operator: str = Field(...)
    threshold_value: float = Field(...)
    lookback_window_days: int = Field(default=30, ge=1)
    min_evaluations: int = Field(default=5, ge=1)
    is_active: bool = Field(default=True)
    authored_by: str = Field(..., min_length=1)

    @field_validator("trigger_type")
    @classmethod
    def _check_trigger_type(cls, v: str) -> str:
        if v not in VALID_CALIBRATION_TRIGGER_TYPES:
            raise ValueError(f"trigger_type must be one of {VALID_CALIBRATION_TRIGGER_TYPES}, got '{v}'")
        return v

    @field_validator("threshold_operator")
    @classmethod
    def _check_operator(cls, v: str) -> str:
        if v not in VALID_THRESHOLD_OPERATORS:
            raise ValueError(f"threshold_operator must be one of {VALID_THRESHOLD_OPERATORS}, got '{v}'")
        return v


class CalibrationEvent(FoundationModel):
    """Immutable record that a calibration was triggered."""

    event_id: str = Field(...)
    trigger_id: str = Field(...)
    rule_id: str = Field(...)
    spec_id: Optional[str] = Field(default=None)
    metric_value: float = Field(...)
    threshold_value: float = Field(...)
    lookback_start: datetime = Field(...)
    lookback_end: datetime = Field(...)
    sample_size: int = Field(..., ge=0)
    status: str = Field(default="TRIGGERED")
    resolved_by: Optional[str] = Field(default=None)
    resolution_notes: Optional[str] = Field(default=None)
    triggered_at: datetime = Field(...)
    resolved_at: Optional[datetime] = Field(default=None)

    @field_validator("status")
    @classmethod
    def _check_status(cls, v: str) -> str:
        if v not in VALID_CALIBRATION_STATUSES:
            raise ValueError(f"status must be one of {VALID_CALIBRATION_STATUSES}, got '{v}'")
        return v


class GovernanceAuditEntry(FoundationModel):
    """SHA-256 hash-chained audit trail for all governance actions."""

    entry_id: str = Field(...)
    event_type: str = Field(...)
    subject_type: str = Field(...)
    subject_id: str = Field(...)
    actor: str = Field(..., min_length=1)
    actor_role: Optional[str] = Field(default=None)
    detail: Dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(...)
    audit_hash: Optional[str] = Field(default=None)
    previous_audit_hash: Optional[str] = Field(default=None)

    @field_validator("event_type")
    @classmethod
    def _check_event_type(cls, v: str) -> str:
        if v not in VALID_AUDIT_EVENT_TYPES:
            raise ValueError(f"event_type must be one of {VALID_AUDIT_EVENT_TYPES}, got '{v}'")
        return v

    @field_validator("subject_type")
    @classmethod
    def _check_subject_type(cls, v: str) -> str:
        if v not in VALID_AUDIT_SUBJECT_TYPES:
            raise ValueError(f"subject_type must be one of {VALID_AUDIT_SUBJECT_TYPES}, got '{v}'")
        return v
