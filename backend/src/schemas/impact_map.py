"""
Impact Map Schema — unified contract for the causal decision surface.

Replaces the fragmented trio of map_payload / graph_payload / propagation_steps
with a single typed response: ImpactMapResponse.

Typed nodes, typed edges, propagation events with delay + failure timing,
decision overlays that modify graph behavior, regime influence, and validation.

Every field has a safe default — no None numerics, no Optional lists.
Frontend can call .map() / .toFixed() without null checks.

Layer: Schemas (source of truth for frontend types + backend engines)
"""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from src.schemas.base import VersionedModel


# ═══════════════════════════════════════════════════════════════════════════════
# Enumerations (Literal types for strict validation)
# ═══════════════════════════════════════════════════════════════════════════════

NodeType = Literal[
    "BANK",
    "FINTECH",
    "PAYMENT_RAIL",
    "PORT",
    "SHIPPING_LANE",
    "ENERGY_ASSET",
    "REGULATOR",
    "INSURER",
    "MARKET_INFRA",
]

NodeState = Literal[
    "NOMINAL",
    "STRESSED",
    "DEGRADED",
    "FAILING",
    "BREACHED",
]

EdgeType = Literal[
    "LIQUIDITY_DEPENDENCY",
    "PAYMENT_DEPENDENCY",
    "TRADE_FLOW",
    "ENERGY_SUPPLY",
    "INSURANCE_CLAIMS_LINK",
    "REGULATORY_CONTROL",
    "CORRESPONDENT_BANKING",
    "SETTLEMENT_ROUTE",
]

OverlayOperation = Literal[
    "CUT",        # sever an edge entirely
    "DELAY",      # increase propagation delay on an edge
    "REDIRECT",   # reroute flow to alternate target
    "BUFFER",     # add capacity buffer to a node
    "NOTIFY",     # flag a node/edge for human review
    "ISOLATE",    # disconnect a node from all inbound edges
]

GraphLayer = Literal[
    "INFRASTRUCTURE",
    "ENERGY",
    "FINANCE",
    "SOVEREIGN",
]

StressLevel = Literal[
    "NOMINAL",
    "LOW",
    "MODERATE",
    "ELEVATED",
    "HIGH",
    "SEVERE",
    "CRITICAL",
]


# ═══════════════════════════════════════════════════════════════════════════════
# Sub-models
# ═══════════════════════════════════════════════════════════════════════════════

class ImpactMapNode(BaseModel):
    """A typed node in the causal impact graph.

    Every node has geo-coordinates, sector classification, stress level,
    and estimated time to breach (None = no breach projected).
    """
    id: str = Field(..., description="Unique node identifier (matches GCC_NODES)")
    label: str = ""
    label_ar: str = ""
    type: NodeType = "MARKET_INFRA"
    sector: str = "unknown"
    layer: GraphLayer = "INFRASTRUCTURE"
    state: NodeState = "NOMINAL"
    stress_level: float = Field(default=0.0, ge=0.0, le=1.0, description="Current stress [0.0–1.0]")
    stress_classification: StressLevel = "NOMINAL"
    time_to_breach_hours: Optional[float] = Field(
        default=None,
        description="Estimated hours until failure threshold. null = no breach projected.",
    )
    lat: float = 0.0
    lng: float = 0.0
    criticality: float = Field(default=0.5, ge=0.0, le=1.0)
    is_bottleneck: bool = False
    regime_sensitivity: float = Field(default=1.0, ge=0.0, description="Regime-adjusted sensitivity multiplier")
    loss_usd: float = Field(default=0.0, ge=0.0, description="Attributed loss at this node")

    model_config = ConfigDict(extra="ignore")


class ImpactMapEdge(BaseModel):
    """A typed, directed edge in the causal impact graph.

    Carries propagation weight, delay, and regime-adjusted transfer ratio.
    """
    source: str = Field(..., description="Source node ID")
    target: str = Field(..., description="Target node ID")
    type: EdgeType = "LIQUIDITY_DEPENDENCY"
    weight: float = Field(default=1.0, ge=0.0, le=1.0, description="Propagation weight [0.0–1.0]")
    delay_hours: float = Field(default=6.0, ge=0.0, description="Propagation delay in hours")
    transfer_ratio: float = Field(
        default=0.72, ge=0.0, le=1.0,
        description="Severity attenuation through this edge",
    )
    is_breakable: bool = Field(default=False, description="Intervention can interrupt this link")
    is_active: bool = Field(default=True, description="Edge is currently carrying propagation")
    regime_modifier: float = Field(default=1.0, ge=0.0, description="Regime amplification on this edge")
    mechanism: str = Field(default="propagation", description="Causal mechanism label")

    model_config = ConfigDict(extra="ignore")

    @field_validator("source", "target")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Edge source/target must not be empty")
        return v.strip()


class PropagationEvent(BaseModel):
    """A discrete propagation event — shock arriving at a node at a specific time.

    Events are ordered by arrival_hour to form the timeline.
    """
    event_id: str = ""
    hop: int = Field(default=0, ge=0, description="Hop index from origin")
    source_id: str = ""
    target_id: str = ""
    arrival_hour: float = Field(default=0.0, ge=0.0, description="Hours since scenario onset")
    severity_at_arrival: float = Field(default=0.0, ge=0.0, le=1.0)
    mechanism: str = ""
    mechanism_ar: str = ""
    is_failure_event: bool = Field(default=False, description="True if this arrival triggers breach")
    failure_type: str = Field(default="", description="Breach type if is_failure_event=True")

    model_config = ConfigDict(extra="ignore")


class TimelinePoint(BaseModel):
    """A point on the aggregate timeline — used for sparklines and time-series."""
    hour: float = Field(default=0.0, ge=0.0)
    active_nodes: int = Field(default=0, ge=0)
    breached_nodes: int = Field(default=0, ge=0)
    aggregate_stress: float = Field(default=0.0, ge=0.0, le=1.0)
    cumulative_loss_usd: float = Field(default=0.0, ge=0.0)

    model_config = ConfigDict(extra="ignore")


class DecisionOverlay(BaseModel):
    """A decision overlay — a structural modification applied to the graph.

    When a decision action is taken, it modifies graph behavior:
      CUT severs an edge, DELAY increases propagation time,
      REDIRECT reroutes flow, BUFFER adds capacity, etc.
    """
    overlay_id: str = ""
    operation: OverlayOperation = "NOTIFY"
    target_edge: Optional[str] = Field(
        default=None,
        description="Edge key (source→target) affected by this overlay",
    )
    target_node: Optional[str] = Field(
        default=None,
        description="Node ID affected by this overlay",
    )
    action_id: str = Field(default="", description="Links to action_registry action_id")
    action_label: str = ""
    action_label_ar: str = ""
    effect_description: str = ""
    effect_description_ar: str = ""
    delay_delta_hours: float = Field(default=0.0, description="Hours added to edge delay (DELAY op)")
    weight_multiplier: float = Field(
        default=1.0, ge=0.0,
        description="Multiplier on edge weight (0.0 = CUT, <1.0 = dampen, >1.0 = amplify)",
    )
    buffer_capacity_usd: float = Field(default=0.0, ge=0.0, description="USD capacity added (BUFFER op)")
    redirect_target: Optional[str] = Field(default=None, description="Alternate target node (REDIRECT op)")
    priority_score: float = Field(default=0.0, ge=0.0, le=1.0)
    urgency: float = Field(default=0.0, ge=0.0, le=1.0)

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def validate_overlay_targets(self) -> "DecisionOverlay":
        """At least one of target_edge or target_node must be set."""
        if not self.target_edge and not self.target_node:
            raise ValueError("DecisionOverlay must target at least one edge or node")
        return self


class RegimeInfluence(BaseModel):
    """Regime influence snapshot — how the current regime modifies the graph."""
    regime_id: str = "STABLE"
    regime_label: str = "Stable Operations"
    regime_label_ar: str = "عمليات مستقرة"
    propagation_amplifier: float = Field(default=1.0, ge=0.0)
    delay_compression: float = Field(default=1.0, ge=0.0, le=1.0)
    failure_threshold_shift: float = Field(default=0.0, ge=-1.0, le=0.0)
    persistence: float = Field(default=0.9, ge=0.0, le=1.0)

    model_config = ConfigDict(extra="ignore")


class ImpactMapHeadline(BaseModel):
    """Executive headline for the impact map."""
    propagation_headline_en: str = "No propagation chain detected — impact is localized."
    propagation_headline_ar: str = "لم يتم اكتشاف سلسلة انتشار — التأثير محلي."
    total_loss_usd: float = Field(default=0.0, ge=0.0)
    total_loss_formatted: str = "$0"
    sectors_impacted: int = Field(default=0, ge=0)
    nodes_breached: int = Field(default=0, ge=0)
    time_to_first_breach_hours: Optional[float] = None
    risk_level: str = "NOMINAL"

    model_config = ConfigDict(extra="ignore")


class ValidationFlag(BaseModel):
    """A validation flag from the impact map validator."""
    field: str = ""
    rule: str = ""
    severity: Literal["warning", "error", "info"] = "warning"
    message: str = ""
    message_ar: str = ""

    model_config = ConfigDict(extra="ignore")


# ═══════════════════════════════════════════════════════════════════════════════
# Top-level contract
# ═══════════════════════════════════════════════════════════════════════════════

class ImpactMapResponse(VersionedModel):
    """Unified impact map response — the causal decision surface.

    Replaces map_payload + graph_payload + propagation_steps with a single
    typed, validated, regime-aware contract. Every field has a safe default.
    Frontend can consume without null checks.

    Data Flow:
      SimulationEngine → ImpactMapEngine → ImpactMapValidator → ImpactMapResponse
      RegimeGraphAdapter → edge/node modifiers → baked into edges/nodes
      DecisionOverlayEngine → overlays → baked into decisionOverlays
    """
    run_id: str = ""
    scenario_id: str = ""
    scenario_label: str = ""

    # ── Graph structure ─────────────────────────────────────────────────────
    nodes: List[ImpactMapNode] = Field(default_factory=list)
    edges: List[ImpactMapEdge] = Field(default_factory=list)
    categories: List[str] = Field(default_factory=list)

    # ── Propagation events (ordered timeline of shock arrivals) ─────────────
    propagation_events: List[PropagationEvent] = Field(default_factory=list)

    # ── Aggregate timeline (for sparklines / time-series) ───────────────────
    timeline: List[TimelinePoint] = Field(default_factory=list)

    # ── Decision overlays (structural modifications from actions) ───────────
    decision_overlays: List[DecisionOverlay] = Field(default_factory=list)

    # ── Regime influence ────────────────────────────────────────────────────
    regime: RegimeInfluence = Field(default_factory=RegimeInfluence)

    # ── Executive headline ──────────────────────────────────────────────────
    headline: ImpactMapHeadline = Field(default_factory=ImpactMapHeadline)

    # ── Validation ──────────────────────────────────────────────────────────
    validation_flags: List[ValidationFlag] = Field(default_factory=list)

    # ── Metadata ────────────────────────────────────────────────────────────
    node_count: int = Field(default=0, ge=0)
    edge_count: int = Field(default=0, ge=0)
    propagation_event_count: int = Field(default=0, ge=0)
    overlay_count: int = Field(default=0, ge=0)

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="after")
    def sync_counts(self) -> "ImpactMapResponse":
        """Keep counts in sync with actual list lengths."""
        self.node_count = len(self.nodes)
        self.edge_count = len(self.edges)
        self.propagation_event_count = len(self.propagation_events)
        self.overlay_count = len(self.decision_overlays)
        return self
