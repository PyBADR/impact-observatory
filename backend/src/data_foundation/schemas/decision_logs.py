"""
Dataset N: Decision Logs
==========================

Immutable audit log of every decision rule activation, human review,
and action execution. Provides the SHA-256 auditable trail required
for GCC enterprise compliance.

KG Mapping: (:DecisionLog)-[:TRIGGERED_BY]->(:DecisionRule)
Consumers: Compliance audit, decision quality analysis, governance dashboard
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import Field

from src.data_foundation.schemas.base import FoundationModel
from src.data_foundation.schemas.enums import (
    DecisionAction,
    DecisionStatus,
    GCCCountry,
    RiskLevel,
)

__all__ = ["DecisionLogEntry"]


class TriggerContext(FoundationModel):
    """Snapshot of the data state that triggered the decision."""
    signal_ids: List[str] = Field(
        default_factory=list,
        description="Signal IDs that contributed to this trigger.",
    )
    indicator_values: Dict[str, Any] = Field(
        default_factory=dict,
        description="Key indicator values at trigger time.",
    )
    scenario_id: Optional[str] = Field(
        default=None,
        description="Active scenario at trigger time.",
    )
    urs_score: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="URS score at trigger time.",
    )
    risk_level: Optional[RiskLevel] = Field(
        default=None,
        description="Risk level at trigger time.",
    )


class DecisionLogEntry(FoundationModel):
    """An immutable record of a decision rule activation and its outcome."""

    log_id: str = Field(
        ...,
        description="Unique log entry ID.",
        examples=["DLOG-20250115-001"],
    )
    rule_id: str = Field(
        ...,
        description="FK to decision_rules.",
    )
    rule_version: int = Field(
        ...,
        ge=1,
        description="Version of the rule at trigger time.",
    )
    triggered_at: datetime = Field(
        ...,
        description="When the rule conditions were met (UTC).",
    )
    action: DecisionAction = Field(
        ...,
        description="Action prescribed by the rule.",
    )
    status: DecisionStatus = Field(
        default=DecisionStatus.PROPOSED,
        description="Current status of this decision.",
    )

    # --- Context ---
    trigger_context: TriggerContext = Field(
        ...,
        description="Snapshot of the data state at trigger time.",
    )
    country: Optional[GCCCountry] = Field(
        default=None,
        description="Primary country affected.",
    )
    entity_ids: List[str] = Field(
        default_factory=list,
        description="Entity IDs affected by this decision.",
    )

    # --- Human-in-the-loop ---
    requires_approval: bool = Field(
        default=True,
    )
    reviewed_by: Optional[str] = Field(
        default=None,
        description="User who reviewed this decision.",
    )
    reviewed_at: Optional[datetime] = Field(
        default=None,
        description="When the review happened.",
    )
    review_notes: Optional[str] = Field(
        default=None,
        description="Reviewer's notes.",
    )

    # --- Execution ---
    executed_at: Optional[datetime] = Field(
        default=None,
        description="When the action was executed.",
    )
    execution_result: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Result of action execution.",
    )

    # --- Supersession ---
    superseded_by: Optional[str] = Field(
        default=None,
        description="Log ID that supersedes this entry.",
    )

    # --- Audit ---
    audit_hash: Optional[str] = Field(
        default=None,
        description="SHA-256 of this log entry for tamper detection.",
    )
    previous_log_hash: Optional[str] = Field(
        default=None,
        description="Hash of the previous log entry (blockchain-style chaining).",
    )
