"""
Enforcement Layer — Pydantic Domain Models
============================================

4 domain models for decision enforcement, execution gating,
and approval workflow.

Every model carries a provenance_hash for tamper detection.
Python 3.10 compatible — no StrEnum.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field

__all__ = [
    "EnforcementPolicy",
    "EnforcementDecision",
    "ExecutionGateResult",
    "ApprovalRequest",
    "EnforcementAction",
    "EnforcementTriggerType",
    "ApprovalStatus",
    "GateOutcome",
]


# ═══════════════════════════════════════════════════════════════════════════════
# String-enum constants (Python 3.10 compatible)
# ═══════════════════════════════════════════════════════════════════════════════


class EnforcementAction:
    """Possible enforcement outcomes for a decision candidate."""

    ALLOW = "ALLOW"
    BLOCK = "BLOCK"
    ESCALATE = "ESCALATE"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    FALLBACK = "FALLBACK"
    SHADOW_ONLY = "SHADOW_ONLY"
    DEGRADE_CONFIDENCE = "DEGRADE_CONFIDENCE"
    ALL = [
        ALLOW, BLOCK, ESCALATE, REQUIRE_APPROVAL,
        FALLBACK, SHADOW_ONLY, DEGRADE_CONFIDENCE,
    ]
    EXECUTABLE = {ALLOW, DEGRADE_CONFIDENCE}
    NON_EXECUTABLE = {BLOCK, ESCALATE, REQUIRE_APPROVAL, FALLBACK, SHADOW_ONLY}


class EnforcementTriggerType:
    """Why enforcement was triggered."""

    RULE_NOT_ACTIVE = "RULE_NOT_ACTIVE"
    RULE_IN_REVIEW = "RULE_IN_REVIEW"
    TRUTH_VALIDATION_FAILED = "TRUTH_VALIDATION_FAILED"
    CALIBRATION_UNRESOLVED = "CALIBRATION_UNRESOLVED"
    PERFORMANCE_BELOW_THRESHOLD = "PERFORMANCE_BELOW_THRESHOLD"
    CONFIDENCE_TOO_LOW = "CONFIDENCE_TOO_LOW"
    POLICY_BLOCK = "POLICY_BLOCK"
    POLICY_ESCALATE = "POLICY_ESCALATE"
    POLICY_REQUIRE_APPROVAL = "POLICY_REQUIRE_APPROVAL"
    POLICY_SHADOW = "POLICY_SHADOW"
    POLICY_FALLBACK = "POLICY_FALLBACK"
    POLICY_DEGRADE = "POLICY_DEGRADE"
    NO_TRIGGER = "NO_TRIGGER"
    ALL = [
        RULE_NOT_ACTIVE, RULE_IN_REVIEW,
        TRUTH_VALIDATION_FAILED, CALIBRATION_UNRESOLVED,
        PERFORMANCE_BELOW_THRESHOLD, CONFIDENCE_TOO_LOW,
        POLICY_BLOCK, POLICY_ESCALATE, POLICY_REQUIRE_APPROVAL,
        POLICY_SHADOW, POLICY_FALLBACK, POLICY_DEGRADE, NO_TRIGGER,
    ]


class ApprovalStatus:
    """Status of an approval request."""

    PENDING = "PENDING"
    APPROVED = "APPROVED"
    DENIED = "DENIED"
    EXPIRED = "EXPIRED"
    ALL = [PENDING, APPROVED, DENIED, EXPIRED]


class GateOutcome:
    """Final gate resolution after enforcement + approval."""

    PROCEED = "PROCEED"
    BLOCKED = "BLOCKED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    SHADOW_MODE = "SHADOW_MODE"
    FALLBACK_APPLIED = "FALLBACK_APPLIED"
    ALL = [PROCEED, BLOCKED, AWAITING_APPROVAL, SHADOW_MODE, FALLBACK_APPLIED]


# ═══════════════════════════════════════════════════════════════════════════════
# Utility
# ═══════════════════════════════════════════════════════════════════════════════


def _gen_id(prefix: str) -> str:
    return f"{prefix}-{uuid4().hex[:16]}"


def _sha256(data: Dict[str, Any]) -> str:
    canonical = json.dumps(data, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ═══════════════════════════════════════════════════════════════════════════════
# 1. EnforcementPolicy
# ═══════════════════════════════════════════════════════════════════════════════


class EnforcementPolicy(BaseModel):
    """Configurable enforcement rule applied before decision execution.

    Defines conditions under which a decision should be blocked,
    escalated, forced into shadow mode, or require approval.
    """

    policy_id: str = Field(default_factory=lambda: _gen_id("EPOL"))
    policy_name: str = Field(...)
    policy_name_ar: Optional[str] = Field(default=None)

    # ── Enforcement action ────────────────────────────────────────────────
    enforcement_action: str = Field(
        ...,
        description="ALLOW, BLOCK, ESCALATE, REQUIRE_APPROVAL, FALLBACK, SHADOW_ONLY, DEGRADE_CONFIDENCE.",
    )

    # ── Conditions ────────────────────────────────────────────────────────
    min_rule_status: Optional[str] = Field(
        default=None,
        description="Minimum rule lifecycle status for execution (e.g., ACTIVE).",
    )
    require_truth_validation: bool = Field(
        default=False,
        description="Block if latest truth validation failed.",
    )
    max_unresolved_calibrations: int = Field(
        default=0, ge=0,
        description="Max unresolved calibration events before enforcement triggers. 0 = no tolerance.",
    )
    min_correctness_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Min avg_correctness_score from latest performance snapshot.",
    )
    min_confidence_score: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Min decision confidence for execution.",
    )
    confidence_degradation_factor: Optional[float] = Field(
        default=None, ge=0.0, le=1.0,
        description="Multiply confidence by this factor when DEGRADE_CONFIDENCE fires.",
    )

    # ── Scope ─────────────────────────────────────────────────────────────
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

    # ── Fallback ──────────────────────────────────────────────────────────
    fallback_action: Optional[str] = Field(
        default=None,
        description="DecisionAction to substitute when FALLBACK triggers.",
    )

    # ── Approver ──────────────────────────────────────────────────────────
    required_approver_role: Optional[str] = Field(
        default=None,
        description="Required role for REQUIRE_APPROVAL (e.g., 'chief_risk_officer').",
    )
    approval_timeout_hours: Optional[float] = Field(
        default=None, ge=0,
        description="Hours before unapproved request expires.",
    )

    # ── Priority ──────────────────────────────────────────────────────────
    priority: int = Field(
        default=100,
        description="Lower = higher priority. Evaluated in priority order.",
    )

    # ── Activation ────────────────────────────────────────────────────────
    is_active: bool = Field(default=True)

    # ── Audit ─────────────────────────────────────────────────────────────
    authored_by: str = Field(...)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _sha256({
            "policy_id": self.policy_id,
            "enforcement_action": self.enforcement_action,
            "created_at": self.created_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 2. EnforcementDecision
# ═══════════════════════════════════════════════════════════════════════════════


class EnforcementDecision(BaseModel):
    """Immutable record of an enforcement evaluation against a decision candidate.

    Produced by the enforcement engine. Never updated — append-only.
    """

    decision_id: str = Field(default_factory=lambda: _gen_id("ENFD"))
    decision_log_id: str = Field(
        ..., description="The decision log entry being evaluated.",
    )
    rule_id: str = Field(...)
    spec_id: Optional[str] = Field(default=None)

    # ── Enforcement outcome ───────────────────────────────────────────────
    enforcement_action: str = Field(
        ...,
        description="Resolved action: ALLOW, BLOCK, ESCALATE, REQUIRE_APPROVAL, FALLBACK, SHADOW_ONLY, DEGRADE_CONFIDENCE.",
    )
    is_executable: bool = Field(
        ...,
        description="True only for ALLOW and DEGRADE_CONFIDENCE.",
    )

    # ── Trigger details ───────────────────────────────────────────────────
    triggered_policy_ids: List[str] = Field(
        default_factory=list,
        description="EnforcementPolicy IDs that contributed to this outcome.",
    )
    trigger_reasons: List[str] = Field(
        default_factory=list,
        description="EnforcementTriggerType values explaining why.",
    )
    blocking_reasons: List[str] = Field(
        default_factory=list,
        description="Human-readable blocking reasons.",
    )

    # ── Confidence ────────────────────────────────────────────────────────
    original_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Original decision confidence score.",
    )
    effective_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confidence after degradation (if any).",
    )

    # ── Fallback ──────────────────────────────────────────────────────────
    fallback_action: Optional[str] = Field(
        default=None,
        description="Substituted action if FALLBACK enforcement.",
    )
    required_approver: Optional[str] = Field(
        default=None,
        description="Required approver role for REQUIRE_APPROVAL.",
    )

    # ── Context snapshot ──────────────────────────────────────────────────
    rule_status: Optional[str] = Field(default=None)
    truth_valid: Optional[bool] = Field(default=None)
    unresolved_calibrations: int = Field(default=0, ge=0)
    latest_correctness_score: Optional[float] = Field(default=None)

    # ── Audit ─────────────────────────────────────────────────────────────
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _sha256({
            "decision_id": self.decision_id,
            "decision_log_id": self.decision_log_id,
            "enforcement_action": self.enforcement_action,
            "is_executable": self.is_executable,
            "evaluated_at": self.evaluated_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 3. ExecutionGateResult
# ═══════════════════════════════════════════════════════════════════════════════


class ExecutionGateResult(BaseModel):
    """Final gate resolution for a decision — proceed, block, await approval, or fallback.

    Combines enforcement decision with approval status to produce a
    final binary: can this decision execute right now?
    """

    gate_id: str = Field(default_factory=lambda: _gen_id("GATE"))
    enforcement_decision_id: str = Field(...)
    decision_log_id: str = Field(...)

    # ── Gate outcome ──────────────────────────────────────────────────────
    gate_outcome: str = Field(
        ...,
        description="PROCEED, BLOCKED, AWAITING_APPROVAL, SHADOW_MODE, FALLBACK_APPLIED.",
    )
    may_execute: bool = Field(
        ...,
        description="True only if the decision may proceed to execution right now.",
    )

    # ── Approval reference ────────────────────────────────────────────────
    approval_request_id: Optional[str] = Field(
        default=None,
        description="If AWAITING_APPROVAL, the pending approval request.",
    )

    # ── Applied modifications ─────────────────────────────────────────────
    applied_fallback_action: Optional[str] = Field(default=None)
    applied_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Effective confidence for execution.",
    )
    is_shadow_mode: bool = Field(
        default=False,
        description="True if decision is recorded but not executed.",
    )

    # ── Audit ─────────────────────────────────────────────────────────────
    resolved_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _sha256({
            "gate_id": self.gate_id,
            "enforcement_decision_id": self.enforcement_decision_id,
            "gate_outcome": self.gate_outcome,
            "may_execute": self.may_execute,
            "resolved_at": self.resolved_at.isoformat(),
        })


# ═══════════════════════════════════════════════════════════════════════════════
# 4. ApprovalRequest
# ═══════════════════════════════════════════════════════════════════════════════


class ApprovalRequest(BaseModel):
    """Tracks a pending human approval required by enforcement policy.

    Created when enforcement resolves to REQUIRE_APPROVAL.
    Resolved by an authorised approver via APPROVED or DENIED.
    """

    request_id: str = Field(default_factory=lambda: _gen_id("AREQ"))
    enforcement_decision_id: str = Field(...)
    decision_log_id: str = Field(...)
    gate_id: Optional[str] = Field(default=None)

    # ── Approval details ──────────────────────────────────────────────────
    required_approver_role: str = Field(...)
    status: str = Field(default=ApprovalStatus.PENDING)
    approved_by: Optional[str] = Field(default=None)
    approval_reason: Optional[str] = Field(default=None)

    # ── Timeout ───────────────────────────────────────────────────────────
    timeout_hours: Optional[float] = Field(default=None, ge=0)
    expires_at: Optional[datetime] = Field(default=None)

    # ── Audit ─────────────────────────────────────────────────────────────
    requested_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    resolved_at: Optional[datetime] = Field(default=None)
    provenance_hash: str = Field(default="")

    def compute_hash(self) -> None:
        self.provenance_hash = _sha256({
            "request_id": self.request_id,
            "enforcement_decision_id": self.enforcement_decision_id,
            "status": self.status,
            "requested_at": self.requested_at.isoformat(),
        })
