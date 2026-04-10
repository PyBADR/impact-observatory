"""Impact Observatory | مرصد الأثر — Decision Object Schema.

Structured decision units with ownership, timing, impact, and risk/tradeoff tracking.
Provides accountability and confidence scoring for operator decisions.
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import Field

from src.schemas.base import VersionedModel


# ── Enums ────────────────────────────────────────────────────────────────────

DecisionUrgency = Literal[
    "IMMEDIATE",
    "URGENT",
    "HIGH",
    "MEDIUM",
    "LOW",
    "DEFERRED",
]

DecisionSector = Literal[
    "ENERGY",
    "FINANCE",
    "SHIPPING",
    "TRADE",
    "BANKING",
    "INSURANCE",
    "INFRASTRUCTURE",
    "SOVEREIGN",
    "CROSS_SECTOR",
]


# ── DecisionObject ────────────────────────────────────────────────────────────

class DecisionObject(VersionedModel):
    """Structured decision unit with accountability, timing, impact, and confidence.

    Represents an actionable decision from the C5 layer with full lineage:
    owner, sector, action description, timing urgency, financial impact estimates,
    risk/tradeoff analysis, and confidence scoring.
    """

    decision_id: str = Field(..., description="Unique decision identifier")
    owner: str = Field(..., description="Owner/operator responsible for decision")
    sector: DecisionSector = Field(..., description="Sector most affected by decision")
    action: str = Field(..., description="Decision action description (imperative)")

    # Timing (hours until action must be taken)
    time_to_act_hours: float = Field(..., ge=0, description="Hours until action window closes")
    urgency: DecisionUrgency = Field(..., description="Decision urgency classification")

    # Impact (financial estimates in USD)
    expected_impact_usd: float = Field(..., description="Expected financial impact (USD)")
    cost_usd: float = Field(default=0.0, ge=0, description="Cost to execute decision (USD)")
    net_value_usd: float = Field(
        default=0.0,
        description="net_value = expected_impact - cost (USD)",
    )

    # Risk and tradeoffs
    risk_description: str | None = Field(None, description="Key risks if decision not taken")
    tradeoff_description: str | None = Field(None, description="Tradeoffs of executing decision")

    # Confidence and metadata
    confidence_score: float = Field(
        default=0.75,
        ge=0.0,
        le=1.0,
        description="Decision confidence (0–1)",
    )
    rationale: str | None = Field(None, description="Decision rationale")

    # ── Decision Gate (Sprint 2) ──────────────────────────────────────────────
    decision_deadline: str | None = Field(
        None,
        description="ISO 8601 deadline — action window closes at this time. "
        "Derived from time_to_act_hours + run start time.",
    )
    approval_required: bool = Field(
        default=False,
        description="True if human-in-the-loop approval is needed before execution. "
        "Auto-set when urgency ≤ MEDIUM or cost_usd > threshold.",
    )
    escalation_trigger: str | None = Field(
        None,
        description="Condition that triggers automatic escalation. "
        "E.g., 'Activate if SEVERE risk persists >12h'.",
    )

    created_at: str = Field(default="", description="ISO 8601 creation timestamp")
    updated_at: str = Field(default="", description="ISO 8601 last update timestamp")
    created_by: str = Field(default="system", description="User/system that created decision")


# ── Request/Response Models ────────────────────────────────────────────────────

class CreateDecisionObjectRequest(VersionedModel):
    """Body for POST /api/v1/decision_objects."""

    owner: str = Field(..., description="Owner/operator responsible")
    sector: DecisionSector = Field(..., description="Sector classification")
    action: str = Field(..., description="Decision action description")
    time_to_act_hours: float = Field(..., ge=0, description="Hours until action window closes")
    urgency: DecisionUrgency = Field(..., description="Urgency classification")
    expected_impact_usd: float = Field(..., description="Expected financial impact (USD)")
    cost_usd: float = Field(default=0.0, ge=0, description="Execution cost (USD)")
    risk_description: str | None = Field(None, description="Risk if not taken")
    tradeoff_description: str | None = Field(None, description="Execution tradeoffs")
    confidence_score: float = Field(default=0.75, ge=0.0, le=1.0, description="Confidence (0–1)")
    rationale: str | None = Field(None, description="Decision rationale")
    created_by: str | None = Field(None, description="User creating decision")
    decision_deadline: str | None = Field(None, description="ISO 8601 deadline for action window")
    approval_required: bool = Field(default=False, description="Require human approval before execution")
    escalation_trigger: str | None = Field(None, description="Condition for automatic escalation")


class UpdateDecisionObjectRequest(VersionedModel):
    """Body for PUT /api/v1/decision_objects/{id}."""

    owner: str | None = None
    action: str | None = None
    time_to_act_hours: float | None = None
    urgency: DecisionUrgency | None = None
    expected_impact_usd: float | None = None
    cost_usd: float | None = None
    risk_description: str | None = None
    tradeoff_description: str | None = None
    confidence_score: float | None = None
    rationale: str | None = None
    decision_deadline: str | None = None
    approval_required: bool | None = None
    escalation_trigger: str | None = None


class DecisionObjectListResponse(VersionedModel):
    """Response for GET /api/v1/decision_objects."""

    count: int
    decision_objects: list[DecisionObject]
