"""
Dataset M: Decision Rules
===========================

Configurable decision rules for the intelligence engine. Each rule defines
a condition (expressed as a predicate over signals/indicators) and an action
to be taken when the condition is met.

Rules are versioned, auditable, and require human-in-the-loop approval
before activation.

KG Mapping: (:DecisionRule)-[:TRIGGERS]->(:DecisionAction)
Consumers: Decision brain, alert system, scenario engine
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from src.data_foundation.schemas.base import AuditMixin, FoundationModel
from src.data_foundation.schemas.enums import (
    DecisionAction,
    GCCCountry,
    RiskLevel,
    Sector,
    SignalSeverity,
)

__all__ = ["DecisionRule"]


class RuleCondition(FoundationModel):
    """A single condition in a decision rule's predicate.

    Conditions are evaluated as: {field} {operator} {threshold}
    Multiple conditions in a rule are combined with AND logic.
    """
    field: str = Field(
        ...,
        description="Data field to evaluate (dot notation for nested).",
        examples=["macro_indicators.oil_price", "banking.npl_ratio_pct",
                   "event_signals.severity_score", "fx.deviation_from_peg_bps"],
    )
    operator: str = Field(
        ...,
        description="Comparison operator.",
        examples=["gt", "gte", "lt", "lte", "eq", "neq", "in", "not_in",
                   "between", "exceeds_threshold"],
    )
    threshold: Any = Field(
        ...,
        description="Threshold value or list for comparison.",
    )
    unit: Optional[str] = Field(
        default=None,
        description="Unit of the threshold for documentation.",
    )


class DecisionRule(FoundationModel, AuditMixin):
    """A configurable decision rule in the intelligence engine."""

    rule_id: str = Field(
        ...,
        description="Unique rule identifier.",
        examples=["RULE-OIL-PRICE-DROP-30", "RULE-NPL-BREACH-5PCT"],
    )
    rule_name: str = Field(
        ...,
        description="Human-readable rule name.",
        examples=["Oil Price Drop >30% Trigger"],
    )
    rule_name_ar: Optional[str] = Field(
        default=None,
    )
    description: str = Field(
        ...,
        description="What this rule does and why it exists.",
    )
    version: int = Field(
        default=1,
        ge=1,
        description="Rule version number. Increment on any change.",
    )
    is_active: bool = Field(
        default=False,
        description="Whether this rule is active. Requires approval to activate.",
    )

    # --- Conditions ---
    conditions: List[RuleCondition] = Field(
        ...,
        min_length=1,
        description="Conditions combined with AND logic.",
    )
    condition_logic: str = Field(
        default="AND",
        description="How conditions are combined.",
        examples=["AND", "OR"],
    )

    # --- Action ---
    action: DecisionAction = Field(
        ...,
        description="Action to trigger when conditions are met.",
    )
    action_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters for the action (e.g., alert recipients, hedge ratio).",
    )
    escalation_level: RiskLevel = Field(
        default=RiskLevel.ELEVATED,
        description="Risk level at which this rule triggers.",
    )

    # --- Scope ---
    applicable_countries: List[GCCCountry] = Field(
        default_factory=list,
        description="Countries this rule applies to. Empty = all GCC.",
    )
    applicable_sectors: List[Sector] = Field(
        default_factory=list,
        description="Sectors this rule applies to. Empty = all sectors.",
    )
    applicable_scenarios: List[str] = Field(
        default_factory=list,
        description="Scenario IDs this rule is relevant for.",
    )

    # --- Governance ---
    requires_human_approval: bool = Field(
        default=True,
        description="Whether the action requires human approval before execution.",
    )
    cooldown_minutes: int = Field(
        default=60,
        ge=0,
        description="Minimum time between consecutive triggers of this rule.",
    )
    expiry_date: Optional[datetime] = Field(
        default=None,
        description="Auto-deactivation date.",
    )

    # --- Metadata ---
    source_dataset_ids: List[str] = Field(
        default_factory=list,
        description="Datasets this rule depends on.",
    )
    tags: List[str] = Field(default_factory=list)
