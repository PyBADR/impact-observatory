"""
Governance Layer — Pydantic Domain Models
==========================================

8 domain models for decision governance, rule lifecycle,
truth validation, calibration triggers, and unified audit.

Every model carries a provenance_hash for tamper detection.
Audit-chain models carry previous_*_hash for SHA-256 chaining.

Python 3.10 compatible — no StrEnum.
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

__all__ = [
    "GovernancePolicy",
    "RuleLifecycleEvent",
    "TruthValidationPolicy",
    "TruthValidationResult",
    "CalibrationTrigger",
    "CalibrationEvent",
    "GovernanceAuditEntry",
    "PolicyType",
    "TransitionType",
    "SpecStatus",
    "CalibrationTriggerType",
    "CalibrationEventStatus",
    "GovernanceEventType",
    "GovernanceSubjectType",
]


# ═══════════════════════════════════════════════════════════════════════════════
# String-enum constants (Python 3.10 compatible)
# ═══════════════════════════════════════════════════════════════════════════════


class PolicyType:
    APPROVAL_GATE = "APPROVAL_GATE"
    ESCALATION_PATH = "ESCALATION_PATH"
    RETENTION = "RETENTION"
    REVIEW_CYCLE = "REVIEW_CYCLE"
    OVERRIDE_LIMIT = "OVERRIDE_LIMIT"
    ALL = [APPROVAL_GATE, ESCALATION_PATH, RETENTION, REVIEW_CYCLE, OVERRIDE_LIMIT]


class SpecStatus:
    """RuleSpec lifecycle statuses — mirrors rule_specs/schema.py."""
    DRAFT = "DRAFT"
    REVIEW = "REVIEW"
    APPROVED = "APPROVED"
    ACTIVE = "ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    RETIRED = "RETIRED"
    TERMINAL = {SUPERSEDED, RETIRED}
    ALL = [DRAFT, REVIEW, APPROVED, ACTIVE, SUPERSEDED, RETIRED]


class TransitionType:
    CREATE = "CREATE"
    ADVANCE = "ADVANCE"
    REJECT = "REJECT"
    RETIRE = "RETIRE"
    SUPERSEDE = "SUPERSEDE"
    ALL = [CREATE, ADVANCE, REJECT, RETIRE, SUPERSEDE]


class CalibrationTriggerType:
    CONFIDENCE_DRIFT = "CONFIDENCE_DRIFT"
    FALSE_POSITIVE_SPIKE = "FALSE_POSITIVE_SPIKE"
    FALSE_NEGATIVE_SPIKE = "FALSE_NEGATIVE_SPIKE"
    REVIEW_DATE_EXPIRY = "REVIEW_DATE_EXPIRY"
    CORRECTNESS_DEGRADATION = "CORRECTNESS_DEGRADATION"
    MANUAL = "MANUAL"
    ALL = [CONFIDENCE_DRIFT, FALSE_POSITIVE_SPIKE, FALSE_NEGATIVE_SPIKE,
           REVIEW_DATE_EXPIRY, CORRECTNESS_DEGRADATION, MANUAL]


class CalibrationEventStatus:
    TRIGGERED = "TRIGGERED"
    ACKNOWLEDGED = "ACKNOWLEDGED"
    RESOLVED = "RESOLVED"
    DISMISSED = "DISMISSED"
    ALL = [TRIGGERED, ACKNOWLEDGED, RESOLVED, DISMISSED]


class GovernanceEventType:
    POLICY_CREATED = "POLICY_CREATED"
    POLICY_UPDATED = "POLICY_UPDATED"
    POLICY_DEACTIVATED = "POLICY_DEACTIVATED"
    LIFECYCLE_TRANSITION = "LIFECYCLE_TRANSITION"
    TRUTH_VALIDATION = "TRUTH_VALIDATION"
    CALIBRATION_TRIGGERED = "CALIBRATION_TRIGGERED"
    CALIBRATION_RESOLVED = "CALIBRATION_RESOLVED"
    OVERRIDE_APPLIED = "OVERRIDE_APPLIED"
    APPROVAL_GRANTED = "APPROVAL_GRANTED"
    APPROVAL_DENIED = "APPROVAL_DENIED"
    ALL = [POLICY_CREATED, POLICY_UPDATED, POLICY_DEACTIVATED,
           LIFECYCLE_TRANSITION, TRUTH_VALIDATION,
           CALIBRATION_TRIGGERED, CALIBRATION_RESOLVED,
           OVERRIDE_APPLIED, APPROVAL_GRANTED, APPROVAL_DENIED]


class GovernanceSubjectType:
    GOVERNANCE_POLICY = "GOVERNANCE_POLICY"
    RULE_SPEC = "RULE_SPEC"
    TRUTH_POLICY = "TRUTH_POLICY"
    CALIBRATION_TRIGGER = "CALIBRATION_TRIGGER"
    DECISION_LOG = "DECISION_LOG"
    ALL = [GOVERNANCE_POLICY, RULE_SPEC, TRUTH_POLICY,
           CALIBRATION_TRIGGER, DECISION_LOG]


# ═══════════════════════════════════════════════════════════════════════════════
# Utility
# ═══════════════════════════════════════════════════════════════════════════════


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:16]}"


def _sha256(data: Dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. GovernancePolicy
# ═══════════════════════════════════════════════════════════════════════════════


class GovernancePolicy(BaseModel):
    """Configurable governance constraint applied to decisions/rules.

    These are meta-rules — rules about rules. They define approval gates,
    escalation paths, review cycles, and override limits.
    """

    policy_id: str = Field(
        default_factory=lambda: _gen_id("GPOL"),
    )
    policy_name: str = Field(...)
    policy_name_ar: Optional[str] = Field(default=None)
    policy_type: str = Field(
        ...,
        description="APPROVAL_GATE, ESCALATION_PATH, RETENTION, REVIEW_CYCLE, OVERRIDE_LIMIT.",
    )

    # ── Scope ──────────────────────────────────────────────────────────────
    scope_risk_levels: List[str] = Field(
        default_factory=list,
        description="Risk levels this policy applies to. Empty = all.",
    )
    scope_actions: List[str] = Field(
        default_factory=list,
        description="DecisionActions. Empty = all.",
    )
    scope_countries: List[str] = Field(default_factory=list)
    scope_sectors: List[str] = Field(default_factory=list)

    # ── Configuration ──────────────────────────────────────────────────────
    policy_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Type-specific configuration. Schema varies by policy_type.",
    )

    # ── Activation ─────────────────────────────────────────────────────────
    is_active: bool = Field(default=True)
    effective_date: Optional[date] = Field(default=None)
    expiry_date: Optional[date] = Field(default=None)

    # ── Audit ──────────────────────────────────────────────────────────────
    authored_by: str = Field(...)
    approved_by: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _sha256({
            "policy_id": self.policy_id,
            "policy_type": self.policy_type,
            "created_at": self.created_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 2. RuleLifecycleEvent
# ═══════════════════════════════════════════════════════════════════════════════


class RuleLifecycleEvent(BaseModel):
    """Immutable log of a rule spec status transition.

    Append-only — never updated or deleted. Every status change
    on a RuleSpec produces exactly one of these.
    """

    event_id: str = Field(default_factory=lambda: _gen_id("RLCE"))
    spec_id: str = Field(...)
    from_status: Optional[str] = Field(
        default=None,
        description="Previous status. Null for initial creation.",
    )
    to_status: str = Field(...)
    transition_type: str = Field(
        ...,
        description="CREATE, ADVANCE, REJECT, RETIRE, SUPERSEDE.",
    )

    # ── Actor ──────────────────────────────────────────────────────────────
    actor: str = Field(...)
    actor_role: Optional[str] = Field(default=None)
    reason: str = Field(..., description="Why the transition occurred.")

    # ── Context ────────────────────────────────────────────────────────────
    validation_result_snapshot: Dict[str, Any] = Field(
        default_factory=dict,
        description="Frozen validator output at transition time.",
    )
    policy_id: Optional[str] = Field(
        default=None,
        description="GovernancePolicy that authorized this transition.",
    )
    supersedes_spec_id: Optional[str] = Field(
        default=None,
        description="If SUPERSEDE, which spec was superseded.",
    )

    # ── Audit chain ────────────────────────────────────────────────────────
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_hash: str = Field(default="")
    previous_event_hash: Optional[str] = Field(
        default=None,
        description="SHA-256 of previous lifecycle event for this spec.",
    )

    def compute_hash(self) -> None:
        self.provenance_hash = _sha256({
            "event_id": self.event_id,
            "spec_id": self.spec_id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "actor": self.actor,
            "occurred_at": self.occurred_at.isoformat(),
            "previous_event_hash": self.previous_event_hash,
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 3. TruthValidationPolicy
# ═══════════════════════════════════════════════════════════════════════════════


class TruthValidationPolicy(BaseModel):
    """Defines what constitutes authoritative truth for a dataset.

    Each policy governs one dataset. When data from multiple sources
    conflicts, the source_priority_order determines the winner.
    """

    policy_id: str = Field(default_factory=lambda: _gen_id("TVP"))
    target_dataset: str = Field(
        ...,
        description="Which P1 dataset this policy governs.",
        examples=["p1_oil_energy_signals", "p1_cbk_indicators", "p1_macro_indicators"],
    )
    policy_name: str = Field(...)

    # ── Source ranking ─────────────────────────────────────────────────────
    source_priority_order: List[str] = Field(
        ...,
        min_length=1,
        description="Ranked source IDs. First = highest priority. Winner on conflict.",
    )

    # ── Freshness ──────────────────────────────────────────────────────────
    freshness_max_hours: float = Field(
        default=24.0, ge=0,
        description="Max age (hours) before data is considered stale.",
    )

    # ── Completeness ───────────────────────────────────────────────────────
    completeness_min_fields: int = Field(
        default=1, ge=1,
        description="Minimum non-null fields required for acceptance.",
    )

    # ── Corroboration ──────────────────────────────────────────────────────
    corroboration_required: bool = Field(
        default=False,
        description="Must multiple sources agree?",
    )
    corroboration_min_sources: int = Field(
        default=2, ge=1,
        description="How many sources must agree (if corroboration_required).",
    )
    deviation_max_pct: Optional[float] = Field(
        default=None, ge=0,
        description="Max allowed deviation (%) between corroborating sources.",
    )

    # ── Field-level validation ─────────────────────────────────────────────
    validation_rules: List[Dict[str, Any]] = Field(
        default_factory=list,
        description=(
            "Field-level checks. Each dict: {field, check, ...params}. "
            "Check types: range (min/max), freshness (max_age_hours), "
            "not_null, regex, enum_member."
        ),
    )

    # ── Meta ───────────────────────────────────────────────────────────────
    is_active: bool = Field(default=True)
    authored_by: str = Field(...)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _sha256({
            "policy_id": self.policy_id,
            "target_dataset": self.target_dataset,
            "created_at": self.created_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TruthValidationResult
# ═══════════════════════════════════════════════════════════════════════════════


class TruthValidationResult(BaseModel):
    """Output of validating a data record against a TruthValidationPolicy."""

    result_id: str = Field(default_factory=lambda: _gen_id("TVR"))
    policy_id: str = Field(...)
    target_dataset: str = Field(...)
    record_id: str = Field(..., description="ID of the record validated.")

    # ── Check results ──────────────────────────────────────────────────────
    is_valid: bool = Field(...)
    freshness_passed: bool = Field(default=True)
    completeness_passed: bool = Field(default=True)
    corroboration_passed: Optional[bool] = Field(
        default=None,
        description="Null if corroboration not required by policy.",
    )
    field_checks_passed: int = Field(default=0, ge=0)
    field_checks_failed: int = Field(default=0, ge=0)
    failure_details: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Per-check failure reasons.",
    )

    # ── Meta ───────────────────────────────────────────────────────────────
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _sha256({
            "result_id": self.result_id,
            "policy_id": self.policy_id,
            "record_id": self.record_id,
            "is_valid": self.is_valid,
            "validated_at": self.validated_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CalibrationTrigger
# ═══════════════════════════════════════════════════════════════════════════════


class CalibrationTrigger(BaseModel):
    """Defines when a rule should be flagged for recalibration.

    Evaluates evaluation metrics against thresholds.
    NOT ML — purely deterministic threshold checks.
    """

    trigger_id: str = Field(default_factory=lambda: _gen_id("CTRIG"))
    trigger_name: str = Field(...)
    trigger_type: str = Field(
        ...,
        description=(
            "CONFIDENCE_DRIFT, FALSE_POSITIVE_SPIKE, FALSE_NEGATIVE_SPIKE, "
            "REVIEW_DATE_EXPIRY, CORRECTNESS_DEGRADATION, MANUAL."
        ),
    )
    target_metric: str = Field(
        ...,
        description="Which metric to monitor from RulePerformanceSnapshot.",
        examples=[
            "avg_confidence_gap",
            "false_positive_count",
            "false_negative_count",
            "avg_correctness_score",
        ],
    )
    threshold_operator: str = Field(
        ...,
        description="gt, lt, gte, lte, exceeds_threshold.",
    )
    threshold_value: float = Field(...)
    lookback_window_days: int = Field(
        default=30, ge=1,
        description="How far back to compute the metric.",
    )
    min_evaluations: int = Field(
        default=5, ge=1,
        description="Min sample size before trigger can fire.",
    )

    # ── Meta ───────────────────────────────────────────────────────────────
    is_active: bool = Field(default=True)
    authored_by: str = Field(...)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _sha256({
            "trigger_id": self.trigger_id,
            "trigger_type": self.trigger_type,
            "target_metric": self.target_metric,
            "created_at": self.created_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 6. CalibrationEvent
# ═══════════════════════════════════════════════════════════════════════════════


class CalibrationEvent(BaseModel):
    """Immutable record of a calibration being triggered."""

    event_id: str = Field(default_factory=lambda: _gen_id("CALEV"))
    trigger_id: str = Field(...)
    rule_id: str = Field(...)
    spec_id: Optional[str] = Field(default=None)

    # ── Trigger context ────────────────────────────────────────────────────
    metric_value: float = Field(..., description="Actual metric value that triggered.")
    threshold_value: float = Field(..., description="Threshold that was breached.")
    lookback_start: datetime = Field(...)
    lookback_end: datetime = Field(...)
    sample_size: int = Field(..., ge=0)

    # ── Resolution ─────────────────────────────────────────────────────────
    status: str = Field(default=CalibrationEventStatus.TRIGGERED)
    resolved_by: Optional[str] = Field(default=None)
    resolution_notes: Optional[str] = Field(default=None)
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = Field(default=None)

    # ── Meta ───────────────────────────────────────────────────────────────
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _sha256({
            "event_id": self.event_id,
            "trigger_id": self.trigger_id,
            "rule_id": self.rule_id,
            "metric_value": self.metric_value,
            "triggered_at": self.triggered_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 7. GovernanceAuditEntry
# ═══════════════════════════════════════════════════════════════════════════════


class GovernanceAuditEntry(BaseModel):
    """Unified governance audit chain.

    Every governance action — policy change, lifecycle transition,
    truth validation, calibration event — is logged here.
    SHA-256 hash chaining provides tamper detection.
    """

    entry_id: str = Field(default_factory=lambda: _gen_id("GAUD"))
    event_type: str = Field(
        ...,
        description="What happened. See GovernanceEventType.",
    )
    subject_type: str = Field(
        ...,
        description="What entity was affected. See GovernanceSubjectType.",
    )
    subject_id: str = Field(..., description="ID of the affected entity.")

    # ── Actor ──────────────────────────────────────────────────────────────
    actor: str = Field(...)
    actor_role: Optional[str] = Field(default=None)

    # ── Payload ────────────────────────────────────────────────────────────
    detail: Dict[str, Any] = Field(
        default_factory=dict,
        description="Event-specific structured payload.",
    )

    # ── Audit chain ────────────────────────────────────────────────────────
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    audit_hash: str = Field(default="")
    previous_audit_hash: Optional[str] = Field(
        default=None,
        description="Hash of the previous entry in the chain.",
    )

    def compute_hash(self) -> None:
        self.audit_hash = _sha256({
            "entry_id": self.entry_id,
            "event_type": self.event_type,
            "subject_id": self.subject_id,
            "actor": self.actor,
            "occurred_at": self.occurred_at.isoformat(),
            "previous_audit_hash": self.previous_audit_hash,
            "detail": self.detail,
        })
