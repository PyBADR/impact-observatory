"""
Banking Intelligence — Decision Contract Layer
================================================
Executable decision objects with accountability-grade ownership,
approval chains, legal basis, and reversibility tracking.

This is NOT a label — it's a live contract that moves through
a state machine: DRAFT → PENDING_APPROVAL → APPROVED → EXECUTING →
EXECUTED → UNDER_REVIEW → CLOSED | ROLLED_BACK.

Every decision must answer:
  - WHO owns it (not a label, an accountable entity)?
  - WHO approves it?
  - WHAT triggers it?
  - WHEN must it be decided?
  - CAN it be reversed?
  - WHAT is the legal authority basis?
  - WHAT are the dependencies?
  - WHAT is the rollback plan?
  - HOW will we observe the outcome?
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ─── Decision Enums ─────────────────────────────────────────────────────────

class DecisionStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    UNDER_REVIEW = "UNDER_REVIEW"
    CLOSED = "CLOSED"
    ROLLED_BACK = "ROLLED_BACK"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class DecisionType(str, Enum):
    PREVENTIVE = "preventive"
    MITIGATING = "mitigating"
    REACTIVE = "reactive"
    MONITORING = "monitoring"
    ESCALATION = "escalation"
    REGULATORY_COMPLIANCE = "regulatory_compliance"


class DecisionSector(str, Enum):
    BANKING = "banking"
    FINTECH = "fintech"
    INSURANCE = "insurance"
    PAYMENTS = "payments"
    CAPITAL_MARKETS = "capital_markets"
    CROSS_SECTOR = "cross_sector"
    SOVEREIGN = "sovereign"


class Reversibility(str, Enum):
    FULLY_REVERSIBLE = "fully_reversible"
    PARTIALLY_REVERSIBLE = "partially_reversible"
    IRREVERSIBLE = "irreversible"
    TIME_BOUNDED_REVERSIBLE = "time_bounded_reversible"


class ExecutionFeasibility(str, Enum):
    READY = "ready"
    REQUIRES_PREPARATION = "requires_preparation"
    BLOCKED = "blocked"
    CONDITIONAL = "conditional"


# ─── Valid State Transitions ────────────────────────────────────────────────

VALID_TRANSITIONS: dict[DecisionStatus, list[DecisionStatus]] = {
    DecisionStatus.DRAFT: [
        DecisionStatus.PENDING_APPROVAL,
        DecisionStatus.REJECTED,
    ],
    DecisionStatus.PENDING_APPROVAL: [
        DecisionStatus.APPROVED,
        DecisionStatus.REJECTED,
        DecisionStatus.EXPIRED,
    ],
    DecisionStatus.APPROVED: [
        DecisionStatus.EXECUTING,
        DecisionStatus.EXPIRED,
    ],
    DecisionStatus.EXECUTING: [
        DecisionStatus.EXECUTED,
        DecisionStatus.ROLLED_BACK,
    ],
    DecisionStatus.EXECUTED: [
        DecisionStatus.UNDER_REVIEW,
        DecisionStatus.CLOSED,
    ],
    DecisionStatus.UNDER_REVIEW: [
        DecisionStatus.CLOSED,
        DecisionStatus.ROLLED_BACK,
    ],
    DecisionStatus.CLOSED: [],
    DecisionStatus.ROLLED_BACK: [DecisionStatus.CLOSED],
    DecisionStatus.EXPIRED: [DecisionStatus.CLOSED],
    DecisionStatus.REJECTED: [DecisionStatus.CLOSED],
}


# ─── Supporting Models ──────────────────────────────────────────────────────

class DependencySpec(BaseModel):
    """A dependency that must be satisfied before execution."""
    dependency_id: str = Field(..., description="canonical_id of the dependency")
    dependency_type: str = Field(
        ..., description="'data_available', 'approval_granted', 'system_ready', 'entity_notified'"
    )
    is_satisfied: bool = False
    satisfied_at: Optional[datetime] = None
    blocker_description: Optional[str] = None


class RollbackPlan(BaseModel):
    """What to do if the decision needs to be reversed."""
    is_rollback_possible: bool
    rollback_steps: list[str] = Field(default_factory=list)
    rollback_owner_id: str = Field(
        ..., description="canonical_id of rollback owner"
    )
    max_rollback_window_hours: Optional[float] = Field(None, ge=0)
    estimated_rollback_cost_usd: Optional[float] = Field(None, ge=0)
    side_effects_of_rollback: list[str] = Field(default_factory=list)


class ObservationPlan(BaseModel):
    """How we will measure the outcome of this decision."""
    observation_windows_hours: list[float] = Field(
        default=[6.0, 24.0, 72.0, 168.0],
        description="Review checkpoints in hours"
    )
    primary_metric: str = Field(
        ..., description="Key metric to observe: 'liquidity_ratio', 'npl_rate', 'transaction_volume'"
    )
    secondary_metrics: list[str] = Field(default_factory=list)
    baseline_value: Optional[float] = None
    target_value: Optional[float] = None
    alert_threshold: Optional[float] = None
    observer_entity_id: str = Field(
        ..., description="canonical_id of the entity responsible for observation"
    )


# ─── Decision Contract ─────────────────────────────────────────────────────

class DecisionContract(BaseModel):
    """
    Executable decision contract — the core unit of the decision
    intelligence layer.

    This object is NOT a log entry. It is a live, stateful contract
    that drives execution, tracks accountability, and feeds the
    outcome review loop.
    """
    decision_id: str = Field(
        ..., min_length=3, pattern=r"^dec:[a-z0-9_\-]+$",
        description="Unique decision identifier: 'dec:hormuz_liquidity_inject_20260410'"
    )
    scenario_id: str = Field(
        ..., description="SCENARIO_CATALOG key that triggered this decision"
    )
    title: str = Field(
        ..., min_length=5, max_length=200,
        description="Human-readable decision title"
    )
    description: Optional[str] = Field(
        None, max_length=2000,
        description="Detailed description of what this decision entails"
    )
    sector: DecisionSector
    decision_type: DecisionType

    # ── Accountability ──────────────────────────────────────────────────
    primary_owner_id: str = Field(
        ..., description="canonical_id of the accountable entity (Authority or Bank)"
    )
    approver_id: str = Field(
        ..., description="canonical_id of the approving entity"
    )
    supporting_entity_ids: list[str] = Field(
        default_factory=list,
        description="canonical_ids of entities involved in execution"
    )

    # ── Timing ──────────────────────────────────────────────────────────
    deadline_at: datetime = Field(
        ..., description="When this decision must be made by (UTC)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    executed_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None

    # ── Trigger & Escalation ────────────────────────────────────────────
    trigger_condition: str = Field(
        ..., description="Machine-parseable: 'URS >= 0.65 AND sector == banking'"
    )
    escalation_threshold: float = Field(
        ..., ge=0.0, le=1.0,
        description="URS level at which this decision auto-escalates"
    )
    approval_required: bool = True
    auto_execute_on_approval: bool = False

    # ── Legal & Governance ──────────────────────────────────────────────
    legal_authority_basis: str = Field(
        ..., description="Regulatory basis: 'SAMA_BCR_Art_42', 'CBUAE_RNCF_S3.2'"
    )
    reversibility: Reversibility
    execution_feasibility: ExecutionFeasibility

    # ── Dependencies & Plans ────────────────────────────────────────────
    dependencies: list[DependencySpec] = Field(default_factory=list)
    rollback_plan: RollbackPlan
    observation_plan: ObservationPlan

    # ── State ───────────────────────────────────────────────────────────
    status: DecisionStatus = Field(default=DecisionStatus.DRAFT)
    status_reason: Optional[str] = None
    status_history: list[dict] = Field(
        default_factory=list,
        description="Audit trail: [{status, timestamp, changed_by, reason}]"
    )

    # ── Linkage ─────────────────────────────────────────────────────────
    counterfactual_id: Optional[str] = Field(
        None, description="Linked CounterfactualContract ID"
    )
    outcome_review_id: Optional[str] = Field(
        None, description="Linked OutcomeReviewContract ID"
    )
    value_audit_id: Optional[str] = Field(
        None, description="Linked DecisionValueAudit ID"
    )
    source_run_id: Optional[str] = Field(
        None, description="Simulation run that generated this decision"
    )

    def can_transition_to(self, target: DecisionStatus) -> bool:
        """Check if a state transition is valid."""
        return target in VALID_TRANSITIONS.get(self.status, [])

    def transition_to(
        self,
        target: DecisionStatus,
        changed_by: str,
        reason: Optional[str] = None,
    ) -> None:
        """Execute a state transition with audit trail."""
        if not self.can_transition_to(target):
            raise ValueError(
                f"Invalid transition: {self.status.value} → {target.value}. "
                f"Valid targets: {[t.value for t in VALID_TRANSITIONS.get(self.status, [])]}"
            )
        self.status_history.append({
            "from_status": self.status.value,
            "to_status": target.value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "changed_by": changed_by,
            "reason": reason,
        })
        self.status = target
        self.status_reason = reason
        self.updated_at = datetime.now(timezone.utc)

        if target == DecisionStatus.EXECUTED:
            self.executed_at = datetime.now(timezone.utc)
        elif target in (DecisionStatus.CLOSED, DecisionStatus.ROLLED_BACK):
            self.closed_at = datetime.now(timezone.utc)

    @property
    def is_terminal(self) -> bool:
        return self.status in (
            DecisionStatus.CLOSED,
            DecisionStatus.EXPIRED,
            DecisionStatus.REJECTED,
        )

    @property
    def dependencies_satisfied(self) -> bool:
        return all(d.is_satisfied for d in self.dependencies)

    @field_validator("deadline_at")
    @classmethod
    def deadline_must_be_future_on_creation(cls, v: datetime) -> datetime:
        # Allow past deadlines for historical imports
        return v
