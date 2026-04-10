"""
Banking Intelligence — Counterfactual Contract Layer
=====================================================
4-branch scenario comparison for every decision:
  1. do_nothing        — baseline: what happens if we take no action
  2. recommended_action — the action we're proposing
  3. delayed_action     — same action but delayed by N hours
  4. alternative_action — a different response entirely

Each branch carries:
  - expected_loss_usd / expected_cost_usd
  - time_to_stabilize
  - downside_risk
  - 4 confidence dimensions
  - delta_vs_baseline

This is what makes ROI defensible to a CFO.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ─── Confidence Dimensions ──────────────────────────────────────────────────

class ConfidenceLevel(str, Enum):
    VERY_HIGH = "very_high"     # >= 0.85
    HIGH = "high"               # >= 0.70
    MODERATE = "moderate"       # >= 0.50
    LOW = "low"                 # >= 0.30
    VERY_LOW = "very_low"      # < 0.30


def confidence_to_level(score: float) -> ConfidenceLevel:
    if score >= 0.85:
        return ConfidenceLevel.VERY_HIGH
    elif score >= 0.70:
        return ConfidenceLevel.HIGH
    elif score >= 0.50:
        return ConfidenceLevel.MODERATE
    elif score >= 0.30:
        return ConfidenceLevel.LOW
    return ConfidenceLevel.VERY_LOW


class ConfidenceDimensions(BaseModel):
    """
    4-axis confidence assessment.
    Each dimension is independent — a model can be highly confident
    in the direction of impact but uncertain about magnitude.
    """
    directional_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Are we right about the direction of impact?"
    )
    impact_estimate_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="How precise is the USD estimate?"
    )
    execution_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Can this action actually be executed as planned?"
    )
    data_sufficiency_confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Do we have enough data to support this estimate?"
    )

    @property
    def composite_confidence(self) -> float:
        """Geometric mean — penalizes any single weak dimension."""
        product = (
            self.directional_confidence
            * self.impact_estimate_confidence
            * self.execution_confidence
            * self.data_sufficiency_confidence
        )
        return product ** 0.25

    @property
    def weakest_dimension(self) -> str:
        dims = {
            "directional": self.directional_confidence,
            "impact_estimate": self.impact_estimate_confidence,
            "execution": self.execution_confidence,
            "data_sufficiency": self.data_sufficiency_confidence,
        }
        return min(dims, key=dims.get)  # type: ignore[arg-type]


# ─── Counterfactual Branch ──────────────────────────────────────────────────

class DownsideRisk(BaseModel):
    """What's the worst case if this branch plays out?"""
    worst_case_loss_usd: float = Field(..., ge=0)
    probability_of_worst_case: float = Field(..., ge=0.0, le=1.0)
    description: str = Field(..., min_length=1)
    tail_risk_multiplier: float = Field(
        default=1.0, ge=1.0,
        description="How much worse than expected the tail can be"
    )


class AssumptionRecord(BaseModel):
    """Every number must be traceable to an assumption."""
    assumption_id: str = Field(..., min_length=1)
    description: str = Field(..., min_length=1)
    source: str = Field(..., description="Where this assumption comes from")
    sensitivity: float = Field(
        ..., ge=0.0, le=1.0,
        description="How sensitive is the outcome to this assumption? 1.0 = very"
    )
    last_validated_at: Optional[datetime] = None


class CounterfactualBranch(BaseModel):
    """Single branch of a counterfactual analysis."""
    branch_label: str = Field(
        ..., description="'do_nothing', 'recommended_action', 'delayed_action', 'alternative_action'"
    )
    description: str = Field(
        ..., min_length=5,
        description="What this branch represents"
    )
    expected_loss_usd: float = Field(
        ..., ge=0,
        description="Total expected loss if this branch plays out"
    )
    expected_cost_usd: float = Field(
        ..., ge=0,
        description="Cost of executing this branch (0 for do_nothing)"
    )
    expected_time_to_stabilize_hours: float = Field(
        ..., ge=0,
        description="Hours until the system returns to acceptable risk levels"
    )
    downside_risk: DownsideRisk
    confidence: ConfidenceDimensions
    delta_vs_baseline_usd: float = Field(
        ..., description="Difference from do_nothing branch (negative = saves money)"
    )
    assumptions: list[AssumptionRecord] = Field(
        default_factory=list,
        description="Assumptions underpinning this branch's estimates"
    )
    net_expected_value_usd: float = Field(
        default=0.0,
        description="expected_loss_usd - expected_cost_usd (auto-computed)"
    )

    @model_validator(mode="after")
    def compute_net_value(self) -> "CounterfactualBranch":
        self.net_expected_value_usd = self.expected_loss_usd - self.expected_cost_usd
        return self


# ─── Counterfactual Contract ────────────────────────────────────────────────

class CounterfactualContract(BaseModel):
    """
    Complete 4-branch counterfactual analysis for a decision.
    The do_nothing branch IS the baseline — all deltas are relative to it.

    This contract makes the ROI conversation defensible:
      - "If we do nothing, we lose $X"
      - "If we act now, we spend $Y but avoid $Z"
      - "If we delay 24h, the window shifts by $W"
      - "The alternative approach costs $A but only avoids $B"
    """
    counterfactual_id: str = Field(
        ..., min_length=3, pattern=r"^cf:[a-z0-9_\-]+$",
        description="Unique ID: 'cf:hormuz_liquidity_20260410'"
    )
    decision_id: str = Field(
        ..., description="Linked DecisionContract ID"
    )
    scenario_id: str = Field(
        ..., description="SCENARIO_CATALOG key"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # ── The 4 branches ──────────────────────────────────────────────────
    do_nothing: CounterfactualBranch
    recommended_action: CounterfactualBranch
    delayed_action: CounterfactualBranch
    alternative_action: CounterfactualBranch

    # ── Summary metrics (auto-computed) ─────────────────────────────────
    recommended_net_benefit_usd: float = Field(
        default=0.0,
        description="do_nothing.loss - recommended.loss - recommended.cost"
    )
    confidence_adjusted_benefit_usd: float = Field(
        default=0.0,
        description="net_benefit × composite_confidence"
    )
    delay_penalty_usd: float = Field(
        default=0.0,
        description="Additional loss from delaying vs acting now"
    )

    # ── Metadata ────────────────────────────────────────────────────────
    analysis_horizon_hours: float = Field(
        ..., gt=0,
        description="Time horizon for this counterfactual analysis"
    )
    model_version: str = Field(default="1.0.0")
    analyst_entity_id: Optional[str] = Field(
        None, description="canonical_id of the entity that produced this analysis"
    )

    @model_validator(mode="after")
    def validate_branches_and_compute_summary(self) -> "CounterfactualContract":
        # do_nothing is the baseline — delta must be 0
        if self.do_nothing.delta_vs_baseline_usd != 0.0:
            raise ValueError("do_nothing.delta_vs_baseline_usd must be 0.0 (it IS the baseline)")
        if self.do_nothing.branch_label != "do_nothing":
            raise ValueError("do_nothing branch must have label 'do_nothing'")

        # Compute summary metrics
        self.recommended_net_benefit_usd = (
            self.do_nothing.expected_loss_usd
            - self.recommended_action.expected_loss_usd
            - self.recommended_action.expected_cost_usd
        )
        self.confidence_adjusted_benefit_usd = (
            self.recommended_net_benefit_usd
            * self.recommended_action.confidence.composite_confidence
        )
        self.delay_penalty_usd = (
            self.delayed_action.expected_loss_usd
            - self.recommended_action.expected_loss_usd
        )
        return self

    @property
    def best_branch(self) -> CounterfactualBranch:
        """Branch with lowest net expected value (loss - cost)."""
        branches = [
            self.do_nothing,
            self.recommended_action,
            self.delayed_action,
            self.alternative_action,
        ]
        return min(branches, key=lambda b: b.expected_loss_usd + b.expected_cost_usd)

    @property
    def is_action_justified(self) -> bool:
        """Is the recommended action better than doing nothing, confidence-adjusted?"""
        return self.confidence_adjusted_benefit_usd > 0
