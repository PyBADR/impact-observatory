"""Schemas 9-10: DecisionAction and DecisionPlan."""

from __future__ import annotations

from typing import Literal

from pydantic import Field

from src.schemas.base import VersionedModel

ActionStatus = Literal["PENDING_REVIEW", "APPROVED", "REJECTED"]


class DecisionAction(VersionedModel):
    """A single recommended action with priority scoring.

    Priority = 0.25*Urgency + 0.30*Value + 0.20*RegRisk + 0.15*Feasibility + 0.10*TimeEffect
    where:
        Urgency = max(0, 1 - time_to_act / time_to_failure)
        Value = (loss_avoided - cost) / loss_baseline
    """
    id: str
    action: str = Field(..., description="What to do")
    action_ar: str | None = Field(None, description="Arabic translation")
    sector: str = Field(..., description="banking, insurance, fintech, energy, maritime, aviation")
    owner: str = Field(..., description="Who executes: CRO, Treasury, Actuary, Ops, Regulator")
    urgency: float = Field(0.0, description="max(0, 1 - time_to_act / time_to_failure)")
    value: float = Field(0.0, description="(loss_avoided - cost) / loss_baseline")
    regulatory_risk: float = Field(0.0, ge=0.0, le=1.0, description="Regulatory exposure if not acted on")
    priority: float = Field(0.0, description="Weighted priority score 0-1")
    time_to_act_hours: float = Field(0.0, description="Window to execute")
    time_to_failure_hours: float = Field(float("inf"), description="When sector fails without action")
    loss_avoided_usd: float = Field(0.0, description="Loss prevented by this action")
    cost_usd: float = Field(0.0, description="Cost to execute this action")
    feasibility: float = Field(0.0, ge=0.0, le=1.0, description="execution_probability × resource_availability")
    time_effect: float = Field(0.0, ge=0.0, le=1.0, description="exp(-lambda × time_to_effect)")
    confidence: float = Field(0.5, ge=0.0, le=1.0)
    status: ActionStatus = Field("PENDING_REVIEW", description="Human-in-the-loop approval state")


class DecisionPlan(VersionedModel):
    """Top-3 prioritized actions for a run."""
    run_id: str
    scenario_label: str | None = None
    total_loss_usd: float = Field(0.0, description="Headline loss across all sectors")
    peak_day: int = Field(0, description="Day of peak system-wide impact")
    time_to_failure_hours: float = Field(float("inf"), description="Earliest sector failure")
    actions: list[DecisionAction] = Field(default_factory=list, description="Top 3 prioritized actions")
    all_actions: list[DecisionAction] = Field(default_factory=list, description="Full action list")
