"""Macro Intelligence Layer — Causal Domain Models.

Source-of-truth Pydantic contracts for the causal entry sublayer.

Domain types:
  CausalEntryPoint  — a signal's entry into the causal graph
  CausalChannel     — a directed edge in the causal graph (domain → domain)
  CausalMapping     — full mapping result: entry point + activated channels
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalDirection,
    SignalSeverity,
    SignalSource,
    SignalType,
)


class CausalEntryPoint(BaseModel):
    """A signal's structured entry into the causal graph.

    Maps a NormalizedSignal to one or more initial impact domains,
    with severity inheritance and region scope.

    Invariants:
      - entry_domains is non-empty (at least one domain must be affected)
      - inherited_severity comes from the source signal
      - entry_strength is derived: severity × confidence_weight
      - reasoning explains WHY these domains are the entry points
    """
    entry_id: UUID = Field(default_factory=uuid4)
    signal_id: UUID = Field(..., description="Source signal UUID")
    signal_title: str = Field(..., description="Human-readable signal title for tracing")
    source: SignalSource
    signal_type: Optional[SignalType] = Field(
        None,
        description="Canonical signal type from upstream NormalizedSignal"
    )
    entry_domains: list[ImpactDomain] = Field(
        ..., min_length=1,
        description="Initial domains this signal enters the causal graph through"
    )
    direction: SignalDirection = Field(
        ..., description="Directional impact inherited from source signal"
    )
    inherited_severity: float = Field(
        ..., ge=0.0, le=1.0,
        description="Severity score inherited from source signal"
    )
    severity_level: SignalSeverity
    confidence: SignalConfidence = Field(
        ..., description="Confidence level inherited from source signal"
    )
    entry_strength: float = Field(
        ..., ge=0.0, le=1.0,
        description="Derived entry strength: severity × confidence_weight. "
                    "Determines initial propagation force."
    )
    regions: list[GCCRegion] = Field(
        ..., min_length=1,
        description="GCC regions in scope for this causal entry"
    )
    reasoning: str = Field(
        ..., min_length=10,
        description="Explainability: why these domains are causal entry points"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


class RelationshipType(str, Enum):
    """Classification of the causal relationship between two domains."""
    DIRECT_EXPOSURE = "direct_exposure"       # direct financial/operational linkage
    SUPPLY_CHAIN = "supply_chain"             # supply chain dependency
    MARKET_CONTAGION = "market_contagion"     # market sentiment / price contagion
    FISCAL_LINKAGE = "fiscal_linkage"         # government revenue / spending dependency
    INFRASTRUCTURE_DEP = "infrastructure_dep" # infrastructure dependency (power, telecom)
    REGULATORY = "regulatory"                 # regulatory / compliance dependency
    RISK_TRANSFER = "risk_transfer"           # insurance / hedging linkage


class CausalChannel(BaseModel):
    """A directed causal edge between two impact domains.

    Represents a known transmission mechanism through which stress
    propagates from one domain to another in GCC markets.

    Example: OIL_GAS → BANKING (oil revenue drop → bank NPL increase)
    """
    channel_id: str = Field(
        ..., min_length=3,
        description="Stable identifier for this channel (e.g. 'oil_gas__banking')"
    )
    from_domain: ImpactDomain
    to_domain: ImpactDomain
    relationship_type: RelationshipType = Field(
        ..., description="Classification of the causal relationship"
    )
    transmission_label: str = Field(
        ..., min_length=5,
        description="Human-readable description of the transmission mechanism"
    )
    base_weight: float = Field(
        ..., ge=0.0, le=1.0,
        description="Base transmission strength [0.0, 1.0]. "
                    "1.0 = full pass-through, 0.0 = no transmission."
    )
    decay_per_hop: float = Field(
        default=0.15, ge=0.0, le=1.0,
        description="Severity decay applied at this hop. Default 15%."
    )
    lag_hours: int = Field(
        default=0, ge=0,
        description="Estimated propagation delay in hours. "
                    "0 = near-instantaneous. Used for ordering and scheduling."
    )
    regions: list[GCCRegion] = Field(
        default_factory=lambda: [GCCRegion.GCC_WIDE],
        description="Regions where this channel is active. Default: GCC-wide."
    )
    bidirectional: bool = Field(
        default=False,
        description="If True, stress can flow in both directions."
    )

    @model_validator(mode="after")
    def no_self_loop(self) -> "CausalChannel":
        if self.from_domain == self.to_domain:
            raise ValueError(
                f"CausalChannel cannot be a self-loop: "
                f"{self.from_domain.value} → {self.to_domain.value}"
            )
        return self


class CausalMapping(BaseModel):
    """Full causal mapping result for a signal.

    Combines the entry point with all activated downstream channels.
    This is the input contract for the propagation engine.
    """
    mapping_id: UUID = Field(default_factory=uuid4)
    entry_point: CausalEntryPoint
    activated_channels: list[CausalChannel] = Field(
        default_factory=list,
        description="Channels activated from the entry domains"
    )
    total_reachable_domains: int = Field(
        default=0,
        description="Count of unique domains reachable from entry (including entry domains)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
