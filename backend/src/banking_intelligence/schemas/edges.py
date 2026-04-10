"""
Banking Intelligence — Graph Edge Registry
============================================
7 typed edge contracts for the GCC banking + fintech knowledge graph.

Every edge carries:
- confidence:           0.0–1.0 trust score
- source_references:    Provenance list (who asserted this relationship)
- merge_key:            Deterministic key for idempotent MERGE in Neo4j
- created_at / updated_at
- evidence_payload:     Optional structured evidence

Design rules:
  - Edges are directional and typed
  - merge_key is computed from (from_id, to_id, edge_type) — no duplicates
  - Evidence payloads are typed, not raw JSON
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, model_validator


# ─── Edge Type Enum ─────────────────────────────────────────────────────────

class EdgeType(str, Enum):
    REGULATES = "REGULATES"
    OPERATES_IN = "OPERATES_IN"
    DEPENDS_ON = "DEPENDS_ON"
    EXPOSED_TO = "EXPOSED_TO"
    PROPAGATES_TO = "PROPAGATES_TO"
    HAS_PLAYBOOK = "HAS_PLAYBOOK"
    TRIGGERS = "TRIGGERS"


# ─── Evidence Payload ───────────────────────────────────────────────────────

class EdgeEvidence(BaseModel):
    """Structured evidence supporting an edge assertion."""
    evidence_type: str = Field(
        ..., description="'regulation', 'license', 'contract', 'observation', 'inference'"
    )
    reference_id: Optional[str] = Field(
        None, description="Document or record ID"
    )
    reference_url: Optional[str] = None
    summary: str = Field(..., min_length=1)
    observed_at: Optional[datetime] = None
    confidence_contribution: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="How much this evidence contributes to edge confidence"
    )


class SourceReference(BaseModel):
    """Who asserted this relationship and when."""
    source_system: str = Field(..., min_length=1)
    source_document_id: Optional[str] = None
    asserted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    asserted_by: str = Field(..., min_length=1)


# ─── Base Edge ──────────────────────────────────────────────────────────────

class BaseEdge(BaseModel):
    """Common contract for all graph edges."""
    from_entity_id: str = Field(
        ..., min_length=3,
        description="canonical_id of source entity"
    )
    to_entity_id: str = Field(
        ..., min_length=3,
        description="canonical_id of target entity"
    )
    edge_type: EdgeType
    confidence: float = Field(
        ..., ge=0.0, le=1.0,
        description="Aggregate confidence in this relationship"
    )
    source_references: list[SourceReference] = Field(
        ..., min_length=1,
        description="At least one source must assert the relationship"
    )
    merge_key: str = Field(
        default="",
        description="Deterministic key — auto-computed from (from, to, type)"
    )
    evidence_payload: list[EdgeEvidence] = Field(default_factory=list)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @model_validator(mode="after")
    def compute_merge_key(self) -> "BaseEdge":
        if not self.merge_key:
            raw = f"{self.from_entity_id}|{self.to_entity_id}|{self.edge_type.value}"
            self.merge_key = hashlib.sha256(raw.encode()).hexdigest()[:24]
        return self


# ─── 1. REGULATES ───────────────────────────────────────────────────────────

class RegulatesEdge(BaseEdge):
    """
    Authority → Bank | Fintech | PaymentRail

    Captures supervisory relationship: who regulates whom, under what power.
    """
    edge_type: EdgeType = Field(default=EdgeType.REGULATES, frozen=True)
    regulatory_powers: list[str] = Field(
        default_factory=list,
        description="Applicable powers: ['license_grant', 'fine', 'audit', 'sanction']"
    )
    regulation_ids: list[str] = Field(
        default_factory=list,
        description="Specific regulation references"
    )
    enforcement_history_count: int = Field(
        default=0, ge=0,
        description="Number of enforcement actions in last 3 years"
    )


# ─── 2. OPERATES_IN ────────────────────────────────────────────────────────

class OperatesInEdge(BaseEdge):
    """
    Bank | Fintech | PaymentRail → Country

    Captures geographic operational presence.
    """
    edge_type: EdgeType = Field(default=EdgeType.OPERATES_IN, frozen=True)
    presence_type: str = Field(
        ..., description="'headquartered', 'branch', 'subsidiary', 'representative', 'digital_only'"
    )
    license_type: Optional[str] = None
    market_share_pct: Optional[float] = Field(None, ge=0, le=100)
    operational_since: Optional[datetime] = None


# ─── 3. DEPENDS_ON ─────────────────────────────────────────────────────────

class DependencyType(str, Enum):
    INFRASTRUCTURE = "infrastructure"
    LIQUIDITY = "liquidity"
    TECHNOLOGY = "technology"
    REGULATORY_APPROVAL = "regulatory_approval"
    DATA_FEED = "data_feed"
    SETTLEMENT = "settlement"
    CORRESPONDENT_BANKING = "correspondent_banking"


class DependsOnEdge(BaseEdge):
    """
    Entity → Entity

    Captures operational dependency: if the target degrades,
    the source is impacted.
    """
    edge_type: EdgeType = Field(default=EdgeType.DEPENDS_ON, frozen=True)
    dependency_type: DependencyType
    criticality: float = Field(
        ..., ge=0.0, le=1.0,
        description="1.0 = total dependency (single point of failure)"
    )
    fallback_available: bool = False
    fallback_entity_id: Optional[str] = None
    degradation_impact_description: str = Field(
        ..., description="What happens when dependency degrades"
    )
    recovery_time_hours: Optional[float] = Field(None, ge=0)


# ─── 4. EXPOSED_TO ─────────────────────────────────────────────────────────

class ExposureType(str, Enum):
    DIRECT = "direct"
    INDIRECT = "indirect"
    CONTINGENT = "contingent"
    CONCENTRATION = "concentration"
    COUNTERPARTY = "counterparty"


class ExposedToEdge(BaseEdge):
    """
    Entity → ScenarioTrigger | Entity

    Captures risk exposure: how much loss potential exists.
    """
    edge_type: EdgeType = Field(default=EdgeType.EXPOSED_TO, frozen=True)
    exposure_type: ExposureType
    exposure_usd_millions: Optional[float] = Field(None, ge=0)
    exposure_pct_of_assets: Optional[float] = Field(None, ge=0, le=100)
    hedge_ratio: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="0 = unhedged, 1 = fully hedged"
    )
    stress_loss_usd_millions: Optional[float] = Field(
        None, ge=0,
        description="Estimated loss under stress scenario"
    )


# ─── 5. PROPAGATES_TO ──────────────────────────────────────────────────────

class TransferMechanism(str, Enum):
    LIQUIDITY_CHANNEL = "liquidity_channel"
    CREDIT_CHANNEL = "credit_channel"
    PAYMENT_CHANNEL = "payment_channel"
    CONFIDENCE_CHANNEL = "confidence_channel"
    OPERATIONAL_CHANNEL = "operational_channel"
    REGULATORY_CHANNEL = "regulatory_channel"
    MARKET_CHANNEL = "market_channel"
    CONTAGION = "contagion"


class PropagatesToEdge(BaseEdge):
    """
    Entity → Entity

    Captures how risk or disruption travels between entities.
    This is the intervention-usable edge — not descriptive only.
    """
    edge_type: EdgeType = Field(default=EdgeType.PROPAGATES_TO, frozen=True)
    transfer_mechanism: TransferMechanism
    delay_hours: float = Field(
        ..., ge=0,
        description="Estimated propagation delay"
    )
    severity_transfer: float = Field(
        ..., ge=0.0, le=1.0,
        description="Fraction of severity that transfers (0 = no transfer)"
    )
    is_breakable: bool = Field(
        ..., description="Can intervention halt this propagation?"
    )
    intervention_lever: Optional[str] = Field(
        None,
        description="What action breaks this link: 'circuit_breaker', 'liquidity_injection', 'regulatory_halt'"
    )
    historical_activation_count: int = Field(default=0, ge=0)


# ─── 6. HAS_PLAYBOOK ───────────────────────────────────────────────────────

class HasPlaybookEdge(BaseEdge):
    """
    Entity | ScenarioTrigger → DecisionPlaybook

    Links an entity or trigger to its response playbook.
    """
    edge_type: EdgeType = Field(default=EdgeType.HAS_PLAYBOOK, frozen=True)
    applicability_scope: str = Field(
        ..., description="'primary', 'backup', 'escalation'"
    )
    last_tested_at: Optional[datetime] = None
    test_result: Optional[str] = Field(
        None, description="'passed', 'failed', 'partial', 'untested'"
    )
    activation_count: int = Field(default=0, ge=0)


# ─── 7. TRIGGERS ───────────────────────────────────────────────────────────

class TriggersEdge(BaseEdge):
    """
    ScenarioTrigger → DecisionPlaybook | DecisionContract

    Links an observable trigger to the decision it activates.
    """
    edge_type: EdgeType = Field(default=EdgeType.TRIGGERS, frozen=True)
    activation_delay_hours: float = Field(
        default=0.0, ge=0,
        description="Delay between trigger detection and decision activation"
    )
    auto_activate: bool = Field(
        default=False,
        description="Does this trigger auto-activate the decision, or require manual approval?"
    )
    required_confirmations: int = Field(
        default=1, ge=1,
        description="Number of independent confirmations before activation"
    )
    false_positive_rate: Optional[float] = Field(
        None, ge=0.0, le=1.0,
        description="Historical false positive rate"
    )


# ─── Edge Type Registry ────────────────────────────────────────────────────

EDGE_TYPE_MAP: dict[EdgeType, type[BaseEdge]] = {
    EdgeType.REGULATES: RegulatesEdge,
    EdgeType.OPERATES_IN: OperatesInEdge,
    EdgeType.DEPENDS_ON: DependsOnEdge,
    EdgeType.EXPOSED_TO: ExposedToEdge,
    EdgeType.PROPAGATES_TO: PropagatesToEdge,
    EdgeType.HAS_PLAYBOOK: HasPlaybookEdge,
    EdgeType.TRIGGERS: TriggersEdge,
}
