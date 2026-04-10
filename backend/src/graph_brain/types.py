"""Graph Brain Shadow Layer — Core Domain Types.

Every node, edge, path, and explanation in the graph layer
conforms to these typed contracts. No untyped dicts.

Type hierarchy:
  GraphEntityType   — what kind of entity a node represents
  GraphRelationType — what kind of relationship an edge represents
  GraphConfidence   — confidence level for graph-derived assertions
  GraphNode         — a single entity in the graph
  GraphEdge         — a typed, directed relationship between two nodes
  GraphSourceRef    — provenance back-reference to source data
  GraphPath         — an ordered sequence of nodes and edges
  GraphExplanation  — full explainability output for a graph query
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


# ── Entity Type Taxonomy ────────────────────────────────────────────────────

class GraphEntityType(str, Enum):
    """Classification of graph node entities.

    Aligned with GCC domain model but generic enough for extension.
    Covers the full entity taxonomy required by the Graph Brain spec.
    """
    SIGNAL = "signal"                  # A macro intelligence signal
    EVENT = "event"                    # A discrete event (conflict, disaster, policy change)
    COUNTRY = "country"                # A GCC member state or external actor
    REGION = "region"                  # A geographic region (GCC-wide, sub-regional)
    SECTOR = "sector"                  # An economic/industry sector
    IMPACT_DOMAIN = "impact_domain"    # A causal impact domain (from Pack 2)
    ORGANIZATION = "organization"      # A named organization (Aramco, ADNOC, etc.)
    INFRASTRUCTURE = "infrastructure"  # Physical infrastructure (ports, grids)
    CHOKEPOINT = "chokepoint"          # Geographic chokepoint (Hormuz, Bab el-Mandeb)
    REGULATOR = "regulator"            # Regulatory body (SAMA, CBUAE)
    MARKET = "market"                  # A financial market or exchange
    RISK_FACTOR = "risk_factor"        # An abstract risk factor
    INDICATOR = "indicator"            # A measurable indicator (CDS spread, oil price, PMI)


# ── Relationship Type Taxonomy ──────────────────────────────────────────────

class GraphRelationType(str, Enum):
    """Classification of graph edge relationships.

    Superset of Pack 2 CausalChannel.RelationshipType, extended
    for entity-level graph semantics. Covers all 10 required relation
    types from the Graph Brain spec plus Pack 2 alignment types.
    """
    # ── Spec-required relation types (10) ────────────────────────────────
    AFFECTS = "affects"                    # signal/event affects domain/sector/country
    DEPENDS_ON = "depends_on"             # entity depends on another entity
    EXPOSED_TO = "exposed_to"             # entity has exposure to a risk/domain
    PROPAGATES_TO = "propagates_to"       # stress/impact propagates from A to B
    INFLUENCES = "influences"             # entity influences another (soft dependency)
    LINKED_TO = "linked_to"               # generic association / correlation
    TRIGGERED_BY = "triggered_by"         # entity/event was triggered by another
    LOCATED_IN = "located_in"             # entity is located in country/region
    CONSTRAINED_BY = "constrained_by"     # entity is constrained by regulator/policy/threshold
    CORRELATED_WITH = "correlated_with"   # statistical / observed correlation

    # ── Pack 2 causal alignment types ────────────────────────────────────
    DIRECT_EXPOSURE = "direct_exposure"
    SUPPLY_CHAIN = "supply_chain"
    MARKET_CONTAGION = "market_contagion"
    FISCAL_LINKAGE = "fiscal_linkage"
    INFRASTRUCTURE_DEP = "infrastructure_dep"
    REGULATORY = "regulatory"
    RISK_TRANSFER = "risk_transfer"

    # ── Extended entity-level relationships ──────────────────────────────
    OPERATES_IN = "operates_in"           # org operates in sector/domain
    REGULATES = "regulates"               # regulator governs entity
    DERIVED_FROM = "derived_from"         # entity was derived from another (provenance)


# ── Confidence ──────────────────────────────────────────────────────────────

class GraphConfidence(str, Enum):
    """Confidence level for graph-derived assertions.

    Maps to numeric weights for traversal scoring.
    """
    DEFINITIVE = "definitive"    # 1.00 — structural fact (country in GCC)
    HIGH = "high"                # 0.90 — strong evidence
    MODERATE = "moderate"        # 0.70 — reasonable inference
    LOW = "low"                  # 0.45 — weak inference
    SPECULATIVE = "speculative"  # 0.20 — unverified hypothesis


CONFIDENCE_WEIGHTS: dict[GraphConfidence, float] = {
    GraphConfidence.DEFINITIVE: 1.00,
    GraphConfidence.HIGH: 0.90,
    GraphConfidence.MODERATE: 0.70,
    GraphConfidence.LOW: 0.45,
    GraphConfidence.SPECULATIVE: 0.20,
}


# ── Source Reference (provenance) ───────────────────────────────────────────

class GraphSourceRef(BaseModel):
    """Provenance back-reference to the originating data.

    Every node and edge should carry at least one source reference
    so that graph assertions are traceable.
    """
    source_type: str = Field(
        ..., min_length=1,
        description="Type of source: 'normalized_signal', 'causal_channel', "
                    "'entity_registry', 'manual'"
    )
    source_id: str = Field(
        ..., min_length=1,
        description="Identifier within the source system (e.g. signal UUID)"
    )
    source_field: Optional[str] = Field(
        None,
        description="Specific field in the source that produced this assertion"
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this reference was recorded"
    )


# ── Graph Node ──────────────────────────────────────────────────────────────

class GraphNode(BaseModel):
    """A single entity in the knowledge graph.

    Immutable after creation. Nodes are identified by node_id (stable key).
    """
    node_id: str = Field(
        ..., min_length=1,
        description="Stable, unique identifier for this node. "
                    "Convention: {entity_type}:{domain_key} e.g. 'country:SA'"
    )
    entity_type: GraphEntityType
    label: str = Field(
        ..., min_length=1,
        description="Human-readable label (English)"
    )
    label_ar: Optional[str] = Field(
        None,
        description="Human-readable label (Arabic)"
    )
    confidence: GraphConfidence = Field(
        default=GraphConfidence.HIGH,
        description="Confidence in this node's existence/accuracy"
    )
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Type-specific properties (severity, gdp_weight, etc.)"
    )
    source_refs: list[GraphSourceRef] = Field(
        default_factory=list,
        description="Provenance references"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    def __hash__(self) -> int:
        return hash(self.node_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, GraphNode):
            return self.node_id == other.node_id
        return NotImplemented


# ── Graph Edge ──────────────────────────────────────────────────────────────

class GraphEdge(BaseModel):
    """A typed, directed relationship between two graph nodes.

    Edges are directional: source_id → target_id.
    Weight represents relationship strength [0.0, 1.0].
    """
    edge_id: str = Field(
        ..., min_length=1,
        description="Stable edge identifier. "
                    "Convention: {source_id}--{relation}-->{target_id}"
    )
    source_id: str = Field(
        ..., min_length=1,
        description="Source node ID"
    )
    target_id: str = Field(
        ..., min_length=1,
        description="Target node ID"
    )
    relation_type: GraphRelationType
    label: str = Field(
        ..., min_length=1,
        description="Human-readable description of the relationship"
    )
    weight: float = Field(
        ..., ge=0.0, le=1.0,
        description="Relationship strength [0.0, 1.0]"
    )
    confidence: GraphConfidence = Field(
        default=GraphConfidence.MODERATE,
        description="Confidence in this relationship assertion"
    )
    properties: dict[str, Any] = Field(
        default_factory=dict,
        description="Edge-specific properties (lag_hours, decay, etc.)"
    )
    source_refs: list[GraphSourceRef] = Field(
        default_factory=list,
        description="Provenance references"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @model_validator(mode="after")
    def no_self_loop(self) -> "GraphEdge":
        if self.source_id == self.target_id:
            raise ValueError(
                f"GraphEdge cannot be a self-loop: {self.source_id} → {self.target_id}"
            )
        return self

    def __hash__(self) -> int:
        return hash(self.edge_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, GraphEdge):
            return self.edge_id == other.edge_id
        return NotImplemented


# ── Graph Path ──────────────────────────────────────────────────────────────

class GraphPath(BaseModel):
    """An ordered sequence of nodes and edges representing a traversal path.

    Used for query results and explainability.
    """
    path_id: UUID = Field(default_factory=uuid4)
    nodes: list[GraphNode] = Field(
        ..., min_length=1,
        description="Ordered nodes in the path (start → end)"
    )
    edges: list[GraphEdge] = Field(
        default_factory=list,
        description="Ordered edges traversed (len = len(nodes) - 1)"
    )
    total_weight: float = Field(
        default=0.0,
        description="Product of all edge weights along the path"
    )
    total_hops: int = Field(
        default=0, ge=0,
        description="Number of edges traversed"
    )
    path_description: str = Field(
        default="",
        description="Human-readable path: 'signal:xyz → country:SA → sector:banking'"
    )

    @model_validator(mode="after")
    def compute_derived(self) -> "GraphPath":
        if self.nodes and not self.path_description:
            self.path_description = " → ".join(n.node_id for n in self.nodes)
        if not self.total_hops:
            self.total_hops = len(self.edges)
        if self.edges and self.total_weight == 0.0:
            w = 1.0
            for e in self.edges:
                w *= e.weight
            self.total_weight = round(w, 6)
        return self


# ── Graph Explanation ───────────────────────────────────────────────────────

class GraphExplanation(BaseModel):
    """Full explainability output for a graph query.

    Returned by the explain module to make graph-derived reasoning
    human-inspectable and audit-ready.
    """
    explanation_id: UUID = Field(default_factory=uuid4)
    query_description: str = Field(
        ..., min_length=1,
        description="What was asked (natural-language query summary)"
    )
    start_node: GraphNode
    end_node: Optional[GraphNode] = Field(
        None,
        description="Target node (None for single-node queries)"
    )
    paths: list[GraphPath] = Field(
        default_factory=list,
        description="All paths found between start and end"
    )
    nodes_traversed: list[GraphNode] = Field(
        default_factory=list,
        description="Unique nodes visited during the query"
    )
    edges_traversed: list[GraphEdge] = Field(
        default_factory=list,
        description="Unique edges traversed during the query"
    )
    reasoning_summary: str = Field(
        default="",
        description="Human-readable explanation of the graph reasoning"
    )
    confidence: GraphConfidence = Field(
        default=GraphConfidence.MODERATE,
        description="Overall confidence in this explanation"
    )
    provenance: list[GraphSourceRef] = Field(
        default_factory=list,
        description="Aggregated source references from traversed elements"
    )
    audit_hash: str = Field(default="")
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @model_validator(mode="after")
    def compute_audit_hash(self) -> "GraphExplanation":
        if not self.audit_hash:
            canonical = json.dumps({
                "explanation_id": str(self.explanation_id),
                "query": self.query_description,
                "start": self.start_node.node_id,
                "end": self.end_node.node_id if self.end_node else None,
                "paths_count": len(self.paths),
                "created_at": self.created_at.isoformat(),
            }, sort_keys=True)
            self.audit_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self
