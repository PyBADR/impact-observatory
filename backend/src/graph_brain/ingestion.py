"""Graph Brain Shadow Layer — Ingestion Adapters.

Transforms NormalizedSignal (Pack 1 output) into graph-safe
GraphNode and GraphEdge instances for the GraphStore.

Mapping strategy:
  1. Signal → GraphNode (entity_type=SIGNAL)
  2. Each region → GraphNode (entity_type=COUNTRY or REGION)
  3. Each impact_domain → GraphNode (entity_type=IMPACT_DOMAIN)
  4. Each sector_scope entry → GraphNode (entity_type=SECTOR)
  5. Each country_scope entry → GraphNode (entity_type=COUNTRY)
  6. Signal → region edges (AFFECTS)
  7. Signal → impact_domain edges (AFFECTS)
  8. Signal → sector edges (AFFECTS)
  9. Signal → country edges (AFFECTS)
  10. Region → impact_domain edges (LOCATED_IN / contextual)

All generated nodes and edges carry GraphSourceRef provenance
back to the originating NormalizedSignal.

Design rules:
  - Pure functions: same NormalizedSignal → same nodes/edges (deterministic)
  - Idempotent: re-ingesting the same signal produces identical graph elements
  - Node IDs follow convention: {entity_type}:{domain_key}
  - Edge IDs follow convention: {source_id}--{relation}-->{target_id}
"""

from __future__ import annotations

from src.macro.macro_enums import GCCRegion, ImpactDomain
from src.macro.macro_schemas import NormalizedSignal
from src.graph_brain.store import GraphStore
from src.graph_brain.types import (
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphRelationType,
    GraphSourceRef,
)

# Re-export for external consumers
__all__ = ["ingest_signal", "IngestionResult"]


# ── Region mapping ──────────────────────────────────────────────────────────

GCC_REGION_LABELS: dict[GCCRegion, tuple[str, str]] = {
    GCCRegion.SAUDI_ARABIA: ("Saudi Arabia", "المملكة العربية السعودية"),
    GCCRegion.UAE: ("United Arab Emirates", "الإمارات العربية المتحدة"),
    GCCRegion.QATAR: ("Qatar", "قطر"),
    GCCRegion.KUWAIT: ("Kuwait", "الكويت"),
    GCCRegion.BAHRAIN: ("Bahrain", "البحرين"),
    GCCRegion.OMAN: ("Oman", "عُمان"),
    GCCRegion.GCC_WIDE: ("GCC Region", "منطقة الخليج"),
}

IMPACT_DOMAIN_LABELS: dict[ImpactDomain, str] = {
    ImpactDomain.OIL_GAS: "Oil & Gas",
    ImpactDomain.BANKING: "Banking",
    ImpactDomain.INSURANCE: "Insurance",
    ImpactDomain.TRADE_LOGISTICS: "Trade & Logistics",
    ImpactDomain.SOVEREIGN_FISCAL: "Sovereign Fiscal",
    ImpactDomain.REAL_ESTATE: "Real Estate",
    ImpactDomain.TELECOMMUNICATIONS: "Telecommunications",
    ImpactDomain.AVIATION: "Aviation",
    ImpactDomain.MARITIME: "Maritime",
    ImpactDomain.ENERGY_GRID: "Energy Grid",
    ImpactDomain.CYBER_INFRASTRUCTURE: "Cyber Infrastructure",
    ImpactDomain.CAPITAL_MARKETS: "Capital Markets",
}


# ── Confidence mapping from signal confidence ──────────────────────────────

def _map_signal_confidence(signal_conf: str) -> GraphConfidence:
    """Map Pack 1 SignalConfidence to GraphConfidence."""
    mapping = {
        "verified": GraphConfidence.HIGH,
        "high": GraphConfidence.HIGH,
        "moderate": GraphConfidence.MODERATE,
        "low": GraphConfidence.LOW,
        "unverified": GraphConfidence.SPECULATIVE,
    }
    return mapping.get(signal_conf, GraphConfidence.MODERATE)


# ── Node Factories ──────────────────────────────────────────────────────────

def _make_source_ref(signal: NormalizedSignal, field: str = "") -> GraphSourceRef:
    """Create a provenance reference back to a NormalizedSignal."""
    return GraphSourceRef(
        source_type="normalized_signal",
        source_id=str(signal.signal_id),
        source_field=field or None,
    )


def _signal_node(signal: NormalizedSignal) -> GraphNode:
    """Create a GraphNode for the signal itself."""
    return GraphNode(
        node_id=f"signal:{signal.signal_id}",
        entity_type=GraphEntityType.SIGNAL,
        label=signal.title,
        confidence=_map_signal_confidence(signal.confidence.value),
        properties={
            "severity_score": signal.severity_score,
            "severity_level": signal.severity_level.value,
            "direction": signal.direction.value,
            "confidence": signal.confidence.value,
            "source": signal.source.value,
            "signal_type": signal.signal_type.value if signal.signal_type else None,
            "content_hash": signal.content_hash,
        },
        source_refs=[_make_source_ref(signal)],
    )


def _region_node(region: GCCRegion) -> GraphNode:
    """Create a GraphNode for a GCC region."""
    labels = GCC_REGION_LABELS.get(region, (region.value, None))
    entity_type = GraphEntityType.REGION if region == GCCRegion.GCC_WIDE else GraphEntityType.COUNTRY
    return GraphNode(
        node_id=f"country:{region.value}",
        entity_type=entity_type,
        label=labels[0],
        label_ar=labels[1],
        confidence=GraphConfidence.DEFINITIVE,
        properties={"gcc_code": region.value},
        source_refs=[GraphSourceRef(
            source_type="entity_registry",
            source_id=f"gcc_region:{region.value}",
        )],
    )


def _impact_domain_node(domain: ImpactDomain) -> GraphNode:
    """Create a GraphNode for an impact domain."""
    return GraphNode(
        node_id=f"impact_domain:{domain.value}",
        entity_type=GraphEntityType.IMPACT_DOMAIN,
        label=IMPACT_DOMAIN_LABELS.get(domain, domain.value),
        confidence=GraphConfidence.DEFINITIVE,
        properties={"domain_key": domain.value},
        source_refs=[GraphSourceRef(
            source_type="entity_registry",
            source_id=f"impact_domain:{domain.value}",
        )],
    )


def _sector_node(sector: str) -> GraphNode:
    """Create a GraphNode for a sector scope entry."""
    normalized = sector.strip().lower().replace(" ", "_")
    return GraphNode(
        node_id=f"sector:{normalized}",
        entity_type=GraphEntityType.SECTOR,
        label=sector.strip(),
        confidence=GraphConfidence.MODERATE,
        properties={"sector_key": normalized},
        source_refs=[GraphSourceRef(
            source_type="normalized_signal",
            source_id=f"sector_scope:{normalized}",
            source_field="sector_scope",
        )],
    )


def _country_scope_node(country: str) -> GraphNode:
    """Create a GraphNode for a country_scope entry (non-GCC or freeform)."""
    normalized = country.strip().lower().replace(" ", "_")
    return GraphNode(
        node_id=f"country:{normalized}",
        entity_type=GraphEntityType.COUNTRY,
        label=country.strip(),
        confidence=GraphConfidence.MODERATE,
        properties={"country_key": normalized},
        source_refs=[GraphSourceRef(
            source_type="normalized_signal",
            source_id=f"country_scope:{normalized}",
            source_field="country_scope",
        )],
    )


# ── Edge Factories ──────────────────────────────────────────────────────────

def _make_edge_id(source_id: str, relation: str, target_id: str) -> str:
    return f"{source_id}--{relation}-->{target_id}"


def _signal_affects_edge(
    signal_node_id: str,
    target_node_id: str,
    target_label: str,
    weight: float,
    confidence: GraphConfidence,
    source_ref: GraphSourceRef,
) -> GraphEdge:
    """Create an AFFECTS edge from signal to a target entity."""
    edge_id = _make_edge_id(signal_node_id, "affects", target_node_id)
    return GraphEdge(
        edge_id=edge_id,
        source_id=signal_node_id,
        target_id=target_node_id,
        relation_type=GraphRelationType.AFFECTS,
        label=f"Signal affects {target_label}",
        weight=weight,
        confidence=confidence,
        source_refs=[source_ref],
    )


# ── Main Ingestion Function ────────────────────────────────────────────────

class IngestionResult:
    """Result of ingesting a NormalizedSignal into the graph store."""

    def __init__(self) -> None:
        self.nodes_created: list[str] = []
        self.nodes_existing: list[str] = []
        self.edges_created: list[str] = []
        self.edges_existing: list[str] = []

    @property
    def total_nodes(self) -> int:
        return len(self.nodes_created) + len(self.nodes_existing)

    @property
    def total_edges(self) -> int:
        return len(self.edges_created) + len(self.edges_existing)

    def __repr__(self) -> str:
        return (
            f"IngestionResult(nodes_new={len(self.nodes_created)}, "
            f"nodes_existing={len(self.nodes_existing)}, "
            f"edges_new={len(self.edges_created)}, "
            f"edges_existing={len(self.edges_existing)})"
        )


def ingest_signal(
    signal: NormalizedSignal,
    store: GraphStore,
) -> IngestionResult:
    """Ingest a NormalizedSignal into the GraphStore.

    Creates nodes and edges for the signal and all its related entities.
    Idempotent: re-ingesting the same signal skips existing nodes/edges.

    Args:
        signal: The NormalizedSignal to ingest.
        store: The target GraphStore.

    Returns:
        IngestionResult with counts of created/existing elements.
    """
    result = IngestionResult()
    graph_confidence = _map_signal_confidence(signal.confidence.value)
    source_ref = _make_source_ref(signal)

    # ── 1. Signal node ──────────────────────────────────────────────────
    sig_node = _signal_node(signal)
    _safe_add_node(store, sig_node, result)

    # ── 2. Region nodes + signal→region edges ───────────────────────────
    for region in signal.regions:
        r_node = _region_node(region)
        _safe_add_node(store, r_node, result)
        edge = _signal_affects_edge(
            sig_node.node_id, r_node.node_id, r_node.label,
            weight=signal.severity_score,
            confidence=graph_confidence,
            source_ref=source_ref,
        )
        _safe_add_edge(store, edge, result)

    # ── 3. Impact domain nodes + signal→domain edges ────────────────────
    for domain in signal.impact_domains:
        d_node = _impact_domain_node(domain)
        _safe_add_node(store, d_node, result)
        edge = _signal_affects_edge(
            sig_node.node_id, d_node.node_id, d_node.label,
            weight=signal.severity_score,
            confidence=graph_confidence,
            source_ref=source_ref,
        )
        _safe_add_edge(store, edge, result)

    # ── 4. Sector scope nodes + signal→sector edges ─────────────────────
    for sector in signal.sector_scope:
        s_node = _sector_node(sector)
        _safe_add_node(store, s_node, result)
        edge = _signal_affects_edge(
            sig_node.node_id, s_node.node_id, s_node.label,
            weight=signal.severity_score * 0.8,  # sector scope is secondary
            confidence=GraphConfidence.MODERATE,
            source_ref=source_ref,
        )
        _safe_add_edge(store, edge, result)

    # ── 5. Country scope nodes + signal→country edges ───────────────────
    for country in signal.country_scope:
        c_node = _country_scope_node(country)
        _safe_add_node(store, c_node, result)
        edge = _signal_affects_edge(
            sig_node.node_id, c_node.node_id, c_node.label,
            weight=signal.severity_score * 0.85,
            confidence=GraphConfidence.MODERATE,
            source_ref=source_ref,
        )
        _safe_add_edge(store, edge, result)

    # ── 6. Cross-entity edges: region → impact_domain (contextual) ──────
    for region in signal.regions:
        r_id = f"country:{region.value}"
        for domain in signal.impact_domains:
            d_id = f"impact_domain:{domain.value}"
            edge_id = _make_edge_id(r_id, "operates_in", d_id)
            if not store.has_edge(edge_id):
                edge = GraphEdge(
                    edge_id=edge_id,
                    source_id=r_id,
                    target_id=d_id,
                    relation_type=GraphRelationType.OPERATES_IN,
                    label=f"{GCC_REGION_LABELS.get(region, (region.value,))[0]} "
                          f"operates in {IMPACT_DOMAIN_LABELS.get(domain, domain.value)}",
                    weight=0.7,
                    confidence=GraphConfidence.HIGH,
                    source_refs=[source_ref],
                )
                _safe_add_edge(store, edge, result)

    return result


# ── Helpers ─────────────────────────────────────────────────────────────────

def _safe_add_node(
    store: GraphStore,
    node: GraphNode,
    result: IngestionResult,
) -> None:
    """Add node to store, tracking new vs existing."""
    if store.has_node(node.node_id):
        result.nodes_existing.append(node.node_id)
    else:
        store.add_node(node)
        result.nodes_created.append(node.node_id)


def _safe_add_edge(
    store: GraphStore,
    edge: GraphEdge,
    result: IngestionResult,
) -> None:
    """Add edge to store, tracking new vs existing."""
    if store.has_edge(edge.edge_id):
        result.edges_existing.append(edge.edge_id)
    else:
        store.add_edge(edge)
        result.edges_created.append(edge.edge_id)
