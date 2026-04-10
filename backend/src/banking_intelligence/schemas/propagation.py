"""
Banking Intelligence — Propagation Intervention Contract
=========================================================
Models how disruption propagates between entities AND — critically —
where and how that propagation can be interrupted.

This is NOT a descriptive graph edge. It is an intervention-ready
contract that identifies:
  - WHERE the risk travels
  - HOW it transfers (mechanism)
  - HOW FAST (delay)
  - HOW MUCH (severity transfer)
  - WHERE to break it (breakable point)
  - WHO can break it (actionable owner)
  - WHAT lever to pull (intervention)
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ─── Enums ──────────────────────────────────────────────────────────────────

class TransferMechanism(str, Enum):
    LIQUIDITY_CHANNEL = "liquidity_channel"
    CREDIT_CHANNEL = "credit_channel"
    PAYMENT_CHANNEL = "payment_channel"
    CONFIDENCE_CHANNEL = "confidence_channel"
    OPERATIONAL_CHANNEL = "operational_channel"
    REGULATORY_CHANNEL = "regulatory_channel"
    MARKET_CHANNEL = "market_channel"
    CONTAGION = "contagion"


class InterventionType(str, Enum):
    CIRCUIT_BREAKER = "circuit_breaker"
    LIQUIDITY_INJECTION = "liquidity_injection"
    REGULATORY_HALT = "regulatory_halt"
    COLLATERAL_CALL = "collateral_call"
    COUNTERPARTY_ISOLATION = "counterparty_isolation"
    PAYMENT_REROUTING = "payment_rerouting"
    COMMUNICATION_DIRECTIVE = "communication_directive"
    MANUAL_OVERRIDE = "manual_override"
    NO_INTERVENTION_POSSIBLE = "no_intervention_possible"


class InterventionReadiness(str, Enum):
    READY = "ready"
    REQUIRES_APPROVAL = "requires_approval"
    REQUIRES_COORDINATION = "requires_coordination"
    NOT_READY = "not_ready"
    UNTESTED = "untested"


# ─── Evidence Source ────────────────────────────────────────────────────────

class PropagationEvidence(BaseModel):
    """Evidence supporting a propagation path assertion."""
    evidence_type: str = Field(
        ..., description="'historical_event', 'stress_test', 'regulatory_report', 'model_output', 'expert_judgment'"
    )
    reference_id: Optional[str] = None
    description: str = Field(..., min_length=1)
    observed_at: Optional[datetime] = None
    relevance_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="How relevant this evidence is to current conditions"
    )


# ─── Intervention Specification ─────────────────────────────────────────────

class InterventionSpec(BaseModel):
    """Detailed specification of an intervention lever."""
    intervention_type: InterventionType
    description: str = Field(..., min_length=5)
    owner_entity_id: str = Field(
        ..., description="canonical_id of the entity that can execute this intervention"
    )
    readiness: InterventionReadiness
    estimated_activation_hours: float = Field(
        ..., ge=0, description="Time to activate this intervention"
    )
    estimated_cost_usd: Optional[float] = Field(None, ge=0)
    effectiveness_estimate: float = Field(
        ..., ge=0.0, le=1.0,
        description="Expected reduction in severity transfer (1.0 = fully blocks)"
    )
    side_effects: list[str] = Field(
        default_factory=list,
        description="Known side effects of this intervention"
    )
    requires_approval_from: Optional[str] = Field(
        None, description="canonical_id of approving authority"
    )
    last_tested_at: Optional[datetime] = None
    test_result: Optional[str] = None


# ─── Propagation Contract ──────────────────────────────────────────────────

class PropagationContract(BaseModel):
    """
    Intervention-ready propagation path contract.

    Models a single directed link in the risk propagation graph
    with full intervention specification.
    """
    propagation_id: str = Field(
        ..., min_length=3, pattern=r"^prop:[a-z0-9_\-]+$",
        description="Unique ID: 'prop:snb_to_rajhi_liquidity'"
    )
    scenario_id: str = Field(
        ..., description="SCENARIO_CATALOG key"
    )

    # ── Path ────────────────────────────────────────────────────────────
    from_entity_id: str = Field(
        ..., description="canonical_id of the source entity"
    )
    to_entity_id: str = Field(
        ..., description="canonical_id of the target entity"
    )
    transfer_mechanism: TransferMechanism
    delay_hours: float = Field(
        ..., ge=0,
        description="Propagation delay between source and target"
    )
    severity_transfer: float = Field(
        ..., ge=0.0, le=1.0,
        description="Fraction of severity that transfers"
    )

    # ── Intervention ────────────────────────────────────────────────────
    breakable_point: bool = Field(
        ..., description="Can this propagation link be interrupted?"
    )
    interventions: list[InterventionSpec] = Field(
        default_factory=list,
        description="Available intervention levers at this point"
    )
    actionable_owner_id: str = Field(
        ..., description="canonical_id of the primary entity responsible for intervention"
    )

    # ── Evidence ────────────────────────────────────────────────────────
    evidence_sources: list[PropagationEvidence] = Field(
        ..., min_length=1,
        description="At least one evidence source required"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Confidence in this propagation path"
    )

    # ── Metadata ────────────────────────────────────────────────────────
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_activated_at: Optional[datetime] = None
    activation_count: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def validate_intervention_consistency(self) -> "PropagationContract":
        if self.breakable_point and not self.interventions:
            raise ValueError(
                "breakable_point=True but no interventions specified. "
                "Either add interventions or set breakable_point=False."
            )
        if not self.breakable_point and self.interventions:
            raise ValueError(
                "breakable_point=False but interventions are specified. "
                "Either remove interventions or set breakable_point=True."
            )
        return self

    @property
    def best_intervention(self) -> Optional[InterventionSpec]:
        """Highest-effectiveness intervention that is ready."""
        ready = [
            i for i in self.interventions
            if i.readiness in (InterventionReadiness.READY, InterventionReadiness.REQUIRES_APPROVAL)
        ]
        if not ready:
            return None
        return max(ready, key=lambda i: i.effectiveness_estimate)

    @property
    def max_blockable_severity(self) -> float:
        """Maximum severity that can be blocked by the best intervention."""
        best = self.best_intervention
        if not best:
            return 0.0
        return self.severity_transfer * best.effectiveness_estimate


# ─── Propagation Chain (multi-hop) ──────────────────────────────────────────

class PropagationChain(BaseModel):
    """
    Ordered sequence of PropagationContracts forming a multi-hop path.
    Used for end-to-end propagation analysis and intervention planning.
    """
    chain_id: str = Field(
        ..., min_length=3, pattern=r"^chain:[a-z0-9_\-]+$"
    )
    scenario_id: str
    links: list[PropagationContract] = Field(
        ..., min_length=1,
        description="Ordered propagation links"
    )
    total_delay_hours: float = Field(default=0.0)
    cumulative_severity_transfer: float = Field(default=0.0)
    first_breakable_point_index: Optional[int] = Field(
        None, description="Index of first link that can be interrupted"
    )

    @model_validator(mode="after")
    def compute_chain_metrics(self) -> "PropagationChain":
        self.total_delay_hours = sum(link.delay_hours for link in self.links)

        severity = 1.0
        for link in self.links:
            severity *= link.severity_transfer
        self.cumulative_severity_transfer = severity

        for i, link in enumerate(self.links):
            if link.breakable_point:
                self.first_breakable_point_index = i
                break

        # Validate chain continuity
        for i in range(1, len(self.links)):
            if self.links[i].from_entity_id != self.links[i - 1].to_entity_id:
                raise ValueError(
                    f"Chain broken at link {i}: "
                    f"link[{i-1}].to={self.links[i-1].to_entity_id} != "
                    f"link[{i}].from={self.links[i].from_entity_id}"
                )
        return self
