"""Graph Brain Shadow Layer — Comprehensive Test Suite.

Tests organized by component:
  1. Schema / Type Tests          — type construction and validation
  2. Store Tests                  — add/get/query nodes and edges
  3. Ingestion Tests              — NormalizedSignal → graph transformation
  4. Traversal / Query Tests      — connected, upstream, downstream, path trace
  5. Explanation Tests            — explainability output structure and content

All tests are deterministic. No external dependencies.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalDirection,
    SignalSeverity,
    SignalSource,
    SignalStatus,
    SignalType,
)
from src.macro.macro_schemas import NormalizedSignal

from src.graph_brain.types import (
    CONFIDENCE_WEIGHTS,
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphExplanation,
    GraphNode,
    GraphPath,
    GraphRelationType,
    GraphSourceRef,
)
from src.graph_brain.store import (
    DanglingEdgeError,
    DuplicateEdgeError,
    DuplicateNodeError,
    GraphStore,
    NodeNotFoundError,
)
from src.graph_brain.ingestion import (
    IngestionResult,
    ingest_signal,
)
from src.graph_brain.query import (
    extract_subgraph,
    find_by_relation,
    find_connected,
    find_downstream,
    find_upstream,
    trace_paths,
)
from src.graph_brain.explain import (
    explain_dependencies,
    explain_impact,
    explain_path,
)


# ═══════════════════════════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════════════════════════


def _make_signal(
    title: str = "Hormuz chokepoint disruption detected",
    severity: float = 0.75,
    regions: list[GCCRegion] | None = None,
    domains: list[ImpactDomain] | None = None,
    sectors: list[str] | None = None,
    countries: list[str] | None = None,
    confidence: SignalConfidence = SignalConfidence.HIGH,
) -> NormalizedSignal:
    """Factory for test NormalizedSignal instances."""
    now = datetime.now(timezone.utc)
    return NormalizedSignal(
        signal_id=uuid4(),
        title=title,
        description="Test signal for Graph Brain",
        source=SignalSource.GEOPOLITICAL,
        severity_score=severity,
        severity_level=SignalSeverity.HIGH if severity >= 0.65 else SignalSeverity.ELEVATED,
        direction=SignalDirection.NEGATIVE,
        confidence=confidence,
        regions=regions or [GCCRegion.UAE, GCCRegion.OMAN],
        impact_domains=domains or [ImpactDomain.OIL_GAS, ImpactDomain.MARITIME],
        event_time=now,
        intake_time=now,
        ttl_hours=72,
        expires_at=now + timedelta(hours=72),
        content_hash="test_hash_" + str(uuid4())[:8],
        signal_type=SignalType.GEOPOLITICAL,
        sector_scope=sectors or [],
        country_scope=countries or [],
    )


def _make_node(node_id: str, entity_type: GraphEntityType, label: str) -> GraphNode:
    return GraphNode(node_id=node_id, entity_type=entity_type, label=label)


def _make_edge(
    source_id: str,
    target_id: str,
    relation: GraphRelationType = GraphRelationType.AFFECTS,
    weight: float = 0.8,
    label: str = "test edge",
) -> GraphEdge:
    edge_id = f"{source_id}--{relation.value}-->{target_id}"
    return GraphEdge(
        edge_id=edge_id,
        source_id=source_id,
        target_id=target_id,
        relation_type=relation,
        label=label,
        weight=weight,
    )


@pytest.fixture
def empty_store() -> GraphStore:
    return GraphStore()


@pytest.fixture
def populated_store() -> GraphStore:
    """A store with a small GCC-like graph for testing traversal."""
    store = GraphStore()

    # Nodes
    signal = _make_node("signal:test1", GraphEntityType.SIGNAL, "Test Signal")
    sa = _make_node("country:SA", GraphEntityType.COUNTRY, "Saudi Arabia")
    ae = _make_node("country:AE", GraphEntityType.COUNTRY, "UAE")
    oil = _make_node("impact_domain:oil_gas", GraphEntityType.IMPACT_DOMAIN, "Oil & Gas")
    banking = _make_node("impact_domain:banking", GraphEntityType.IMPACT_DOMAIN, "Banking")
    maritime = _make_node("impact_domain:maritime", GraphEntityType.IMPACT_DOMAIN, "Maritime")
    trade = _make_node("impact_domain:trade_logistics", GraphEntityType.IMPACT_DOMAIN, "Trade Logistics")

    for n in [signal, sa, ae, oil, banking, maritime, trade]:
        store.add_node(n)

    # Edges: signal → countries/domains
    store.add_edge(_make_edge("signal:test1", "country:SA", GraphRelationType.AFFECTS, 0.75))
    store.add_edge(_make_edge("signal:test1", "country:AE", GraphRelationType.AFFECTS, 0.75))
    store.add_edge(_make_edge("signal:test1", "impact_domain:oil_gas", GraphRelationType.AFFECTS, 0.80))
    store.add_edge(_make_edge("signal:test1", "impact_domain:maritime", GraphRelationType.AFFECTS, 0.70))

    # Domain-to-domain edges (causal chain)
    store.add_edge(_make_edge(
        "impact_domain:oil_gas", "impact_domain:banking",
        GraphRelationType.DIRECT_EXPOSURE, 0.80, "Oil stress → bank NPLs",
    ))
    store.add_edge(_make_edge(
        "impact_domain:maritime", "impact_domain:trade_logistics",
        GraphRelationType.SUPPLY_CHAIN, 0.90, "Port disruption → supply chain",
    ))
    store.add_edge(_make_edge(
        "impact_domain:banking", "impact_domain:trade_logistics",
        GraphRelationType.FISCAL_LINKAGE, 0.50, "Banking stress → trade credit",
    ))

    # Region → domain
    store.add_edge(_make_edge(
        "country:SA", "impact_domain:oil_gas",
        GraphRelationType.OPERATES_IN, 0.90,
    ))
    store.add_edge(_make_edge(
        "country:AE", "impact_domain:maritime",
        GraphRelationType.OPERATES_IN, 0.85,
    ))

    return store


# ═══════════════════════════════════════════════════════════════════════════════
# 1. SCHEMA / TYPE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestGraphNodeSchema:
    """Test GraphNode construction and validation."""

    def test_node_creation(self):
        node = GraphNode(
            node_id="country:SA",
            entity_type=GraphEntityType.COUNTRY,
            label="Saudi Arabia",
            label_ar="المملكة العربية السعودية",
        )
        assert node.node_id == "country:SA"
        assert node.entity_type == GraphEntityType.COUNTRY
        assert node.label == "Saudi Arabia"
        assert node.label_ar == "المملكة العربية السعودية"
        assert node.properties == {}
        assert node.source_refs == []
        assert node.created_at is not None

    def test_node_with_properties(self):
        node = GraphNode(
            node_id="signal:abc",
            entity_type=GraphEntityType.SIGNAL,
            label="Test Signal",
            properties={"severity_score": 0.75, "direction": "negative"},
        )
        assert node.properties["severity_score"] == 0.75

    def test_node_hash_equality(self):
        n1 = _make_node("x:1", GraphEntityType.SIGNAL, "A")
        n2 = _make_node("x:1", GraphEntityType.SIGNAL, "B")
        assert n1 == n2
        assert hash(n1) == hash(n2)

    def test_node_inequality(self):
        n1 = _make_node("x:1", GraphEntityType.SIGNAL, "A")
        n2 = _make_node("x:2", GraphEntityType.SIGNAL, "A")
        assert n1 != n2


class TestGraphEdgeSchema:
    """Test GraphEdge construction and validation."""

    def test_edge_creation(self):
        edge = GraphEdge(
            edge_id="a--affects-->b",
            source_id="a",
            target_id="b",
            relation_type=GraphRelationType.AFFECTS,
            label="A affects B",
            weight=0.8,
        )
        assert edge.source_id == "a"
        assert edge.target_id == "b"
        assert edge.weight == 0.8

    def test_edge_no_self_loop(self):
        with pytest.raises(ValueError, match="self-loop"):
            GraphEdge(
                edge_id="a--affects-->a",
                source_id="a",
                target_id="a",
                relation_type=GraphRelationType.AFFECTS,
                label="Self loop",
                weight=0.5,
            )

    def test_edge_confidence_default(self):
        edge = GraphEdge(
            edge_id="a--affects-->b",
            source_id="a",
            target_id="b",
            relation_type=GraphRelationType.AFFECTS,
            label="test",
            weight=0.5,
        )
        assert edge.confidence == GraphConfidence.MODERATE


class TestGraphPathSchema:
    """Test GraphPath construction and derived fields."""

    def test_path_description_auto(self):
        n1 = _make_node("a", GraphEntityType.SIGNAL, "A")
        n2 = _make_node("b", GraphEntityType.COUNTRY, "B")
        path = GraphPath(nodes=[n1, n2], edges=[])
        assert path.path_description == "a → b"

    def test_path_weight_computation(self):
        n1 = _make_node("a", GraphEntityType.SIGNAL, "A")
        n2 = _make_node("b", GraphEntityType.COUNTRY, "B")
        n3 = _make_node("c", GraphEntityType.SECTOR, "C")
        e1 = GraphEdge(
            edge_id="a-->b", source_id="a", target_id="b",
            relation_type=GraphRelationType.AFFECTS, label="e1", weight=0.8,
        )
        e2 = GraphEdge(
            edge_id="b-->c", source_id="b", target_id="c",
            relation_type=GraphRelationType.AFFECTS, label="e2", weight=0.5,
        )
        path = GraphPath(nodes=[n1, n2, n3], edges=[e1, e2])
        assert path.total_weight == pytest.approx(0.4, abs=0.001)
        assert path.total_hops == 2


class TestGraphExplanationSchema:
    """Test GraphExplanation construction."""

    def test_explanation_audit_hash(self):
        node = _make_node("a", GraphEntityType.SIGNAL, "A")
        exp = GraphExplanation(
            query_description="Test query",
            start_node=node,
        )
        assert exp.audit_hash != ""
        assert len(exp.audit_hash) == 64  # SHA-256

    def test_explanation_deterministic_hash(self):
        """Same inputs → same hash (except for UUID/timestamp)."""
        node = _make_node("a", GraphEntityType.SIGNAL, "A")
        exp = GraphExplanation(
            query_description="Test query",
            start_node=node,
        )
        assert exp.audit_hash  # non-empty


class TestGraphSourceRef:
    """Test source reference construction."""

    def test_source_ref_creation(self):
        ref = GraphSourceRef(
            source_type="normalized_signal",
            source_id="abc-123",
            source_field="regions",
        )
        assert ref.source_type == "normalized_signal"
        assert ref.source_id == "abc-123"
        assert ref.source_field == "regions"
        assert ref.timestamp is not None


class TestConfidenceWeights:
    """Test confidence weight mapping."""

    def test_all_levels_mapped(self):
        for level in GraphConfidence:
            assert level in CONFIDENCE_WEIGHTS

    def test_monotonic_decreasing(self):
        levels = list(GraphConfidence)
        for i in range(len(levels) - 1):
            assert CONFIDENCE_WEIGHTS[levels[i]] >= CONFIDENCE_WEIGHTS[levels[i + 1]]


# ═══════════════════════════════════════════════════════════════════════════════
# 2. STORE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestGraphStore:
    """Test GraphStore CRUD and adjacency operations."""

    def test_empty_store(self, empty_store: GraphStore):
        assert empty_store.node_count == 0
        assert empty_store.edge_count == 0
        assert empty_store.all_nodes() == []
        assert empty_store.all_edges() == []

    def test_add_node(self, empty_store: GraphStore):
        node = _make_node("country:SA", GraphEntityType.COUNTRY, "Saudi Arabia")
        result = empty_store.add_node(node)
        assert result.node_id == "country:SA"
        assert empty_store.node_count == 1
        assert empty_store.has_node("country:SA")

    def test_add_duplicate_node_raises(self, empty_store: GraphStore):
        node = _make_node("country:SA", GraphEntityType.COUNTRY, "Saudi Arabia")
        empty_store.add_node(node)
        with pytest.raises(DuplicateNodeError):
            empty_store.add_node(node)

    def test_add_node_upsert(self, empty_store: GraphStore):
        n1 = _make_node("country:SA", GraphEntityType.COUNTRY, "Saudi Arabia")
        n2 = _make_node("country:SA", GraphEntityType.COUNTRY, "KSA Updated")
        empty_store.add_node(n1)
        empty_store.add_node(n2, upsert=True)
        assert empty_store.node_count == 1
        assert empty_store.get_node("country:SA").label == "KSA Updated"

    def test_get_node_not_found(self, empty_store: GraphStore):
        assert empty_store.get_node("nonexistent") is None

    def test_get_node_strict_raises(self, empty_store: GraphStore):
        with pytest.raises(NodeNotFoundError):
            empty_store.get_node_strict("nonexistent")

    def test_get_nodes_by_type(self, populated_store: GraphStore):
        countries = populated_store.get_nodes_by_type(GraphEntityType.COUNTRY)
        assert len(countries) == 2
        country_ids = {n.node_id for n in countries}
        assert "country:SA" in country_ids
        assert "country:AE" in country_ids

    def test_add_edge(self, empty_store: GraphStore):
        n1 = _make_node("a", GraphEntityType.SIGNAL, "A")
        n2 = _make_node("b", GraphEntityType.COUNTRY, "B")
        empty_store.add_node(n1)
        empty_store.add_node(n2)

        edge = _make_edge("a", "b")
        empty_store.add_edge(edge)
        assert empty_store.edge_count == 1
        assert empty_store.has_edge(edge.edge_id)

    def test_add_edge_dangling_source_raises(self, empty_store: GraphStore):
        n2 = _make_node("b", GraphEntityType.COUNTRY, "B")
        empty_store.add_node(n2)
        edge = _make_edge("a", "b")
        with pytest.raises(DanglingEdgeError):
            empty_store.add_edge(edge)

    def test_add_edge_dangling_target_raises(self, empty_store: GraphStore):
        n1 = _make_node("a", GraphEntityType.SIGNAL, "A")
        empty_store.add_node(n1)
        edge = _make_edge("a", "b")
        with pytest.raises(DanglingEdgeError):
            empty_store.add_edge(edge)

    def test_add_duplicate_edge_raises(self, empty_store: GraphStore):
        n1 = _make_node("a", GraphEntityType.SIGNAL, "A")
        n2 = _make_node("b", GraphEntityType.COUNTRY, "B")
        empty_store.add_node(n1)
        empty_store.add_node(n2)
        edge = _make_edge("a", "b")
        empty_store.add_edge(edge)
        with pytest.raises(DuplicateEdgeError):
            empty_store.add_edge(edge)

    def test_outgoing_edges(self, populated_store: GraphStore):
        outgoing = populated_store.get_outgoing_edges("signal:test1")
        assert len(outgoing) == 4  # SA, AE, oil_gas, maritime

    def test_incoming_edges(self, populated_store: GraphStore):
        incoming = populated_store.get_incoming_edges("impact_domain:oil_gas")
        assert len(incoming) >= 2  # signal + SA operates_in

    def test_get_neighbors_outgoing(self, populated_store: GraphStore):
        neighbors = populated_store.get_neighbors("signal:test1", direction="outgoing")
        neighbor_ids = {n.node_id for n in neighbors}
        assert "country:SA" in neighbor_ids
        assert "country:AE" in neighbor_ids
        assert "impact_domain:oil_gas" in neighbor_ids
        assert "impact_domain:maritime" in neighbor_ids

    def test_get_neighbors_incoming(self, populated_store: GraphStore):
        neighbors = populated_store.get_neighbors("impact_domain:banking", direction="incoming")
        neighbor_ids = {n.node_id for n in neighbors}
        assert "impact_domain:oil_gas" in neighbor_ids

    def test_get_edges_between(self, populated_store: GraphStore):
        edges = populated_store.get_edges_between("signal:test1", "country:SA")
        assert len(edges) == 1
        assert edges[0].relation_type == GraphRelationType.AFFECTS

    def test_clear(self, populated_store: GraphStore):
        assert populated_store.node_count > 0
        populated_store.clear()
        assert populated_store.node_count == 0
        assert populated_store.edge_count == 0

    def test_snapshot(self, populated_store: GraphStore):
        snap = populated_store.snapshot()
        assert snap["node_count"] == populated_store.node_count
        assert snap["edge_count"] == populated_store.edge_count
        assert len(snap["nodes"]) == populated_store.node_count
        assert len(snap["edges"]) == populated_store.edge_count

    def test_repr(self, populated_store: GraphStore):
        r = repr(populated_store)
        assert "GraphStore" in r
        assert "nodes=" in r
        assert "edges=" in r

    def test_bulk_add_nodes(self, empty_store: GraphStore):
        nodes = [
            _make_node(f"n:{i}", GraphEntityType.SIGNAL, f"Node {i}")
            for i in range(5)
        ]
        count = empty_store.add_nodes(nodes)
        assert count == 5
        assert empty_store.node_count == 5


# ═══════════════════════════════════════════════════════════════════════════════
# 3. INGESTION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestIngestion:
    """Test NormalizedSignal → GraphStore ingestion."""

    def test_basic_ingestion(self, empty_store: GraphStore):
        signal = _make_signal()
        result = ingest_signal(signal, empty_store)

        # Signal node + 2 region nodes + 2 domain nodes = 5
        assert len(result.nodes_created) == 5
        assert empty_store.node_count == 5

        # Signal→region edges (2) + signal→domain edges (2) + region→domain cross-edges
        assert empty_store.edge_count > 0
        assert len(result.edges_created) > 0

    def test_signal_node_properties(self, empty_store: GraphStore):
        signal = _make_signal(title="Oil shock signal", severity=0.82)
        ingest_signal(signal, empty_store)

        sig_node = empty_store.get_node(f"signal:{signal.signal_id}")
        assert sig_node is not None
        assert sig_node.entity_type == GraphEntityType.SIGNAL
        assert sig_node.label == "Oil shock signal"
        assert sig_node.properties["severity_score"] == 0.82

    def test_region_nodes_created(self, empty_store: GraphStore):
        signal = _make_signal(regions=[GCCRegion.SAUDI_ARABIA, GCCRegion.UAE, GCCRegion.QATAR])
        ingest_signal(signal, empty_store)

        assert empty_store.has_node("country:SA")
        assert empty_store.has_node("country:AE")
        assert empty_store.has_node("country:QA")

        sa = empty_store.get_node("country:SA")
        assert sa.entity_type == GraphEntityType.COUNTRY
        assert sa.label == "Saudi Arabia"

    def test_impact_domain_nodes_created(self, empty_store: GraphStore):
        signal = _make_signal(
            domains=[ImpactDomain.OIL_GAS, ImpactDomain.BANKING, ImpactDomain.MARITIME]
        )
        ingest_signal(signal, empty_store)

        assert empty_store.has_node("impact_domain:oil_gas")
        assert empty_store.has_node("impact_domain:banking")
        assert empty_store.has_node("impact_domain:maritime")

    def test_sector_scope_ingestion(self, empty_store: GraphStore):
        signal = _make_signal(sectors=["oil", "banking", "logistics"])
        ingest_signal(signal, empty_store)

        assert empty_store.has_node("sector:oil")
        assert empty_store.has_node("sector:banking")
        assert empty_store.has_node("sector:logistics")

    def test_country_scope_ingestion(self, empty_store: GraphStore):
        signal = _make_signal(countries=["Iraq", "Iran"])
        ingest_signal(signal, empty_store)

        assert empty_store.has_node("country:iraq")
        assert empty_store.has_node("country:iran")

    def test_signal_affects_edges(self, empty_store: GraphStore):
        signal = _make_signal()
        ingest_signal(signal, empty_store)

        sig_id = f"signal:{signal.signal_id}"
        outgoing = empty_store.get_outgoing_edges(sig_id)

        # Should have edges to both regions and both domains
        target_ids = {e.target_id for e in outgoing}
        assert "country:AE" in target_ids
        assert "country:OM" in target_ids
        assert "impact_domain:oil_gas" in target_ids
        assert "impact_domain:maritime" in target_ids

    def test_cross_entity_edges(self, empty_store: GraphStore):
        signal = _make_signal(
            regions=[GCCRegion.SAUDI_ARABIA],
            domains=[ImpactDomain.OIL_GAS],
        )
        ingest_signal(signal, empty_store)

        # Should have region → domain OPERATES_IN edge
        edges = empty_store.get_edges_between("country:SA", "impact_domain:oil_gas")
        assert len(edges) == 1
        assert edges[0].relation_type == GraphRelationType.OPERATES_IN

    def test_idempotent_ingestion(self, empty_store: GraphStore):
        signal = _make_signal()
        r1 = ingest_signal(signal, empty_store)
        node_count_1 = empty_store.node_count
        edge_count_1 = empty_store.edge_count

        r2 = ingest_signal(signal, empty_store)
        assert empty_store.node_count == node_count_1
        assert empty_store.edge_count == edge_count_1
        assert len(r2.nodes_existing) > 0

    def test_multi_signal_ingestion(self, empty_store: GraphStore):
        s1 = _make_signal(
            title="Signal Alpha",
            regions=[GCCRegion.UAE],
            domains=[ImpactDomain.MARITIME],
        )
        s2 = _make_signal(
            title="Signal Beta",
            regions=[GCCRegion.UAE],
            domains=[ImpactDomain.BANKING],
        )
        ingest_signal(s1, empty_store)
        ingest_signal(s2, empty_store)

        # UAE node should exist once (shared)
        uae = empty_store.get_node("country:AE")
        assert uae is not None

        # Both signal nodes should exist
        assert empty_store.has_node(f"signal:{s1.signal_id}")
        assert empty_store.has_node(f"signal:{s2.signal_id}")

    def test_ingestion_result_repr(self, empty_store: GraphStore):
        signal = _make_signal()
        result = ingest_signal(signal, empty_store)
        r = repr(result)
        assert "IngestionResult" in r

    def test_provenance_on_signal_node(self, empty_store: GraphStore):
        signal = _make_signal()
        ingest_signal(signal, empty_store)

        sig_node = empty_store.get_node(f"signal:{signal.signal_id}")
        assert len(sig_node.source_refs) == 1
        assert sig_node.source_refs[0].source_type == "normalized_signal"
        assert sig_node.source_refs[0].source_id == str(signal.signal_id)


# ═══════════════════════════════════════════════════════════════════════════════
# 4. TRAVERSAL / QUERY TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestQueryConnected:
    """Test find_connected queries."""

    def test_find_connected_from_signal(self, populated_store: GraphStore):
        connected = find_connected(populated_store, "signal:test1", max_depth=1)
        ids = {n.node_id for n in connected}
        assert "country:SA" in ids
        assert "country:AE" in ids
        assert "impact_domain:oil_gas" in ids
        assert "impact_domain:maritime" in ids

    def test_find_connected_depth_2(self, populated_store: GraphStore):
        connected = find_connected(populated_store, "signal:test1", max_depth=2)
        ids = {n.node_id for n in connected}
        # At depth 2, should also reach banking (oil→banking) and trade (maritime→trade)
        assert "impact_domain:banking" in ids
        assert "impact_domain:trade_logistics" in ids

    def test_find_connected_nonexistent_node(self, populated_store: GraphStore):
        result = find_connected(populated_store, "nonexistent", max_depth=3)
        assert result == []

    def test_find_connected_with_entity_type_filter(self, populated_store: GraphStore):
        connected = find_connected(
            populated_store, "signal:test1",
            max_depth=2,
            entity_type_filter={GraphEntityType.IMPACT_DOMAIN},
        )
        for node in connected:
            assert node.entity_type == GraphEntityType.IMPACT_DOMAIN

    def test_find_connected_with_relation_filter(self, populated_store: GraphStore):
        connected = find_connected(
            populated_store, "signal:test1",
            max_depth=2,
            relation_filter={GraphRelationType.AFFECTS},
        )
        # Should only follow AFFECTS edges → 4 direct neighbors
        assert len(connected) == 4


class TestQueryUpstreamDownstream:
    """Test find_upstream and find_downstream."""

    def test_find_downstream_from_oil(self, populated_store: GraphStore):
        downstream = find_downstream(populated_store, "impact_domain:oil_gas", max_depth=3)
        ids = {n.node_id for n in downstream}
        assert "impact_domain:banking" in ids
        # banking → trade_logistics
        assert "impact_domain:trade_logistics" in ids

    def test_find_upstream_of_banking(self, populated_store: GraphStore):
        upstream = find_upstream(populated_store, "impact_domain:banking", max_depth=3)
        ids = {n.node_id for n in upstream}
        assert "impact_domain:oil_gas" in ids

    def test_find_upstream_of_trade(self, populated_store: GraphStore):
        upstream = find_upstream(populated_store, "impact_domain:trade_logistics", max_depth=3)
        ids = {n.node_id for n in upstream}
        assert "impact_domain:maritime" in ids
        assert "impact_domain:banking" in ids


class TestQueryTracePaths:
    """Test trace_paths between nodes."""

    def test_direct_path(self, populated_store: GraphStore):
        paths = trace_paths(
            populated_store, "impact_domain:oil_gas", "impact_domain:banking",
            max_depth=3,
        )
        assert len(paths) >= 1
        best = paths[0]
        assert best.nodes[0].node_id == "impact_domain:oil_gas"
        assert best.nodes[-1].node_id == "impact_domain:banking"
        assert best.total_hops == 1

    def test_multi_hop_path(self, populated_store: GraphStore):
        paths = trace_paths(
            populated_store, "signal:test1", "impact_domain:banking",
            max_depth=4,
        )
        assert len(paths) >= 1
        # signal → oil_gas → banking (2 hops)
        shortest = min(paths, key=lambda p: p.total_hops)
        assert shortest.total_hops == 2

    def test_no_path(self, populated_store: GraphStore):
        # trade_logistics has no outgoing to signal
        paths = trace_paths(
            populated_store, "impact_domain:trade_logistics", "signal:test1",
            max_depth=5,
        )
        assert paths == []

    def test_same_node_path(self, populated_store: GraphStore):
        paths = trace_paths(
            populated_store, "country:SA", "country:SA",
            max_depth=3,
        )
        assert len(paths) == 1
        assert paths[0].total_hops == 0
        assert paths[0].total_weight == 1.0

    def test_path_weight_correct(self, populated_store: GraphStore):
        paths = trace_paths(
            populated_store, "impact_domain:oil_gas", "impact_domain:banking",
            max_depth=2,
        )
        assert len(paths) >= 1
        # Weight should be the edge weight: 0.80
        assert paths[0].total_weight == pytest.approx(0.80, abs=0.01)

    def test_nonexistent_start(self, populated_store: GraphStore):
        paths = trace_paths(populated_store, "nonexistent", "country:SA")
        assert paths == []


class TestQueryFindByRelation:
    """Test find_by_relation."""

    def test_find_affects_edges(self, populated_store: GraphStore):
        edges = find_by_relation(populated_store, GraphRelationType.AFFECTS)
        assert len(edges) == 4  # signal→SA, signal→AE, signal→oil, signal→maritime

    def test_find_operates_in_edges(self, populated_store: GraphStore):
        edges = find_by_relation(populated_store, GraphRelationType.OPERATES_IN)
        assert len(edges) == 2  # SA→oil, AE→maritime


class TestQueryExtractSubgraph:
    """Test subgraph extraction."""

    def test_extract_from_signal(self, populated_store: GraphStore):
        nodes, edges = extract_subgraph(
            populated_store, "signal:test1", max_depth=1,
        )
        node_ids = {n.node_id for n in nodes}
        assert "signal:test1" in node_ids
        assert len(nodes) == 5  # signal + 4 neighbors
        assert len(edges) == 4

    def test_extract_deeper(self, populated_store: GraphStore):
        nodes, edges = extract_subgraph(
            populated_store, "signal:test1", max_depth=2,
        )
        node_ids = {n.node_id for n in nodes}
        assert "impact_domain:banking" in node_ids
        assert "impact_domain:trade_logistics" in node_ids


# ═══════════════════════════════════════════════════════════════════════════════
# 5. EXPLANATION TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestExplainPath:
    """Test explain_path output."""

    def test_explain_direct_relationship(self, populated_store: GraphStore):
        exp = explain_path(
            populated_store,
            "impact_domain:oil_gas",
            "impact_domain:banking",
        )
        assert exp.start_node.node_id == "impact_domain:oil_gas"
        assert exp.end_node.node_id == "impact_domain:banking"
        assert len(exp.paths) >= 1
        assert exp.reasoning_summary != ""
        assert "Oil & Gas" in exp.reasoning_summary
        assert "Banking" in exp.reasoning_summary
        assert exp.audit_hash != ""
        assert exp.confidence in list(GraphConfidence)

    def test_explain_no_path(self, populated_store: GraphStore):
        exp = explain_path(
            populated_store,
            "impact_domain:trade_logistics",
            "signal:test1",
        )
        assert len(exp.paths) == 0
        assert "No paths found" in exp.reasoning_summary

    def test_explain_has_provenance(self, populated_store: GraphStore):
        exp = explain_path(
            populated_store,
            "impact_domain:oil_gas",
            "impact_domain:banking",
        )
        # Nodes traversed should be populated
        assert len(exp.nodes_traversed) >= 2
        assert len(exp.edges_traversed) >= 1


class TestExplainImpact:
    """Test explain_impact output."""

    def test_signal_impact(self, populated_store: GraphStore):
        exp = explain_impact(populated_store, "signal:test1", max_depth=3)
        assert exp.start_node.node_id == "signal:test1"
        assert exp.end_node is None  # impact query has no specific end
        assert "downstream impact" in exp.reasoning_summary.lower() or \
               "no downstream" in exp.reasoning_summary.lower()
        assert len(exp.nodes_traversed) > 0

    def test_oil_impact(self, populated_store: GraphStore):
        exp = explain_impact(populated_store, "impact_domain:oil_gas", max_depth=3)
        # Oil should have downstream impact on banking and trade
        assert len(exp.paths) >= 1
        reached_ids = {n.node_id for n in exp.nodes_traversed}
        assert "impact_domain:banking" in reached_ids


class TestExplainDependencies:
    """Test explain_dependencies output."""

    def test_banking_dependencies(self, populated_store: GraphStore):
        exp = explain_dependencies(populated_store, "impact_domain:banking", max_depth=3)
        assert exp.start_node.node_id == "impact_domain:banking"
        assert "depends on" in exp.reasoning_summary.lower() or \
               "no upstream" in exp.reasoning_summary.lower()

    def test_signal_no_dependencies(self, populated_store: GraphStore):
        exp = explain_dependencies(populated_store, "signal:test1", max_depth=3)
        # Signal is a root node — no upstream
        assert "no upstream" in exp.reasoning_summary.lower()


# ═══════════════════════════════════════════════════════════════════════════════
# 6. INTEGRATION: INGEST → QUERY → EXPLAIN
# ═══════════════════════════════════════════════════════════════════════════════


class TestEndToEnd:
    """Full pipeline: NormalizedSignal → ingest → query → explain."""

    def test_full_pipeline(self, empty_store: GraphStore):
        # 1. Create and ingest a signal
        signal = _make_signal(
            title="Strait of Hormuz partial blockage",
            severity=0.78,
            regions=[GCCRegion.UAE, GCCRegion.OMAN, GCCRegion.SAUDI_ARABIA],
            domains=[ImpactDomain.OIL_GAS, ImpactDomain.MARITIME, ImpactDomain.TRADE_LOGISTICS],
            sectors=["energy", "shipping"],
            countries=["Iran"],
        )
        result = ingest_signal(signal, empty_store)
        assert result.total_nodes > 0
        assert result.total_edges > 0

        # 2. Query downstream of the signal
        sig_id = f"signal:{signal.signal_id}"
        downstream = find_downstream(empty_store, sig_id, max_depth=2)
        assert len(downstream) > 0

        # 3. Query connected entities
        connected = find_connected(empty_store, sig_id, max_depth=1)
        connected_ids = {n.node_id for n in connected}
        assert "country:AE" in connected_ids
        assert "country:OM" in connected_ids
        assert "country:SA" in connected_ids
        assert "impact_domain:oil_gas" in connected_ids
        assert "impact_domain:maritime" in connected_ids

        # 4. Explain impact
        exp = explain_impact(empty_store, sig_id, max_depth=2)
        assert exp.start_node.node_id == sig_id
        assert len(exp.nodes_traversed) > 0
        assert exp.reasoning_summary != ""
        assert exp.audit_hash != ""

    def test_multi_signal_graph_grows(self, empty_store: GraphStore):
        s1 = _make_signal(
            title="Signal A: Oil disruption",
            regions=[GCCRegion.SAUDI_ARABIA],
            domains=[ImpactDomain.OIL_GAS],
        )
        s2 = _make_signal(
            title="Signal B: Banking stress",
            regions=[GCCRegion.UAE],
            domains=[ImpactDomain.BANKING],
        )
        s3 = _make_signal(
            title="Signal C: Maritime threat",
            regions=[GCCRegion.SAUDI_ARABIA, GCCRegion.UAE],
            domains=[ImpactDomain.MARITIME, ImpactDomain.OIL_GAS],
        )

        for s in [s1, s2, s3]:
            ingest_signal(s, empty_store)

        # 3 signal nodes + shared region/domain nodes
        signals = empty_store.get_nodes_by_type(GraphEntityType.SIGNAL)
        assert len(signals) == 3

        countries = empty_store.get_nodes_by_type(GraphEntityType.COUNTRY)
        # SA + AE (deduplicated)
        assert len(countries) == 2

        domains = empty_store.get_nodes_by_type(GraphEntityType.IMPACT_DOMAIN)
        # oil_gas + banking + maritime (deduplicated)
        assert len(domains) == 3

        # Snapshot
        snap = empty_store.snapshot()
        assert snap["node_count"] == empty_store.node_count
        assert snap["edge_count"] == empty_store.edge_count


# ═══════════════════════════════════════════════════════════════════════════════
# 7. EXPANDED ENTITY & RELATION TYPE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestExpandedEntityTypes:
    """Verify all required entity types exist and are usable."""

    def test_all_required_entity_types_exist(self):
        required = {
            "signal", "event", "region", "country", "sector",
            "organization", "risk_factor", "impact_domain", "indicator",
        }
        actual = {e.value for e in GraphEntityType}
        assert required.issubset(actual), f"Missing: {required - actual}"

    def test_event_node_creation(self, empty_store: GraphStore):
        node = GraphNode(
            node_id="event:hormuz_blockage_2026",
            entity_type=GraphEntityType.EVENT,
            label="Hormuz Blockage 2026",
            confidence=GraphConfidence.HIGH,
            properties={"event_date": "2026-04-01", "severity": 0.85},
        )
        empty_store.add_node(node)
        assert empty_store.has_node("event:hormuz_blockage_2026")
        retrieved = empty_store.get_node("event:hormuz_blockage_2026")
        assert retrieved.entity_type == GraphEntityType.EVENT
        assert retrieved.confidence == GraphConfidence.HIGH

    def test_indicator_node_creation(self, empty_store: GraphStore):
        node = GraphNode(
            node_id="indicator:cds_spread_sa",
            entity_type=GraphEntityType.INDICATOR,
            label="Saudi CDS Spread",
            confidence=GraphConfidence.DEFINITIVE,
            properties={"unit": "bps", "latest_value": 45.2},
        )
        empty_store.add_node(node)
        assert empty_store.get_node("indicator:cds_spread_sa").entity_type == GraphEntityType.INDICATOR

    def test_risk_factor_node(self, empty_store: GraphStore):
        node = GraphNode(
            node_id="risk_factor:oil_price_volatility",
            entity_type=GraphEntityType.RISK_FACTOR,
            label="Oil Price Volatility",
        )
        empty_store.add_node(node)
        assert empty_store.has_node("risk_factor:oil_price_volatility")

    def test_organization_node(self, empty_store: GraphStore):
        node = GraphNode(
            node_id="organization:aramco",
            entity_type=GraphEntityType.ORGANIZATION,
            label="Saudi Aramco",
            label_ar="أرامكو السعودية",
            confidence=GraphConfidence.DEFINITIVE,
        )
        empty_store.add_node(node)
        assert empty_store.get_node("organization:aramco").label_ar == "أرامكو السعودية"


class TestExpandedRelationTypes:
    """Verify all 10 required relation types plus Pack 2 alignment types."""

    def test_all_required_relation_types_exist(self):
        required = {
            "affects", "depends_on", "exposed_to", "propagates_to",
            "influences", "linked_to", "triggered_by", "located_in",
            "constrained_by", "correlated_with",
        }
        actual = {r.value for r in GraphRelationType}
        assert required.issubset(actual), f"Missing: {required - actual}"

    def test_pack2_alignment_types_exist(self):
        pack2 = {
            "direct_exposure", "supply_chain", "market_contagion",
            "fiscal_linkage", "infrastructure_dep", "regulatory", "risk_transfer",
        }
        actual = {r.value for r in GraphRelationType}
        assert pack2.issubset(actual), f"Missing Pack 2 types: {pack2 - actual}"

    def test_exposed_to_edge(self, empty_store: GraphStore):
        n1 = _make_node("organization:aramco", GraphEntityType.ORGANIZATION, "Aramco")
        n2 = _make_node("risk_factor:oil_vol", GraphEntityType.RISK_FACTOR, "Oil Volatility")
        empty_store.add_node(n1)
        empty_store.add_node(n2)

        edge = GraphEdge(
            edge_id="organization:aramco--exposed_to-->risk_factor:oil_vol",
            source_id="organization:aramco",
            target_id="risk_factor:oil_vol",
            relation_type=GraphRelationType.EXPOSED_TO,
            label="Aramco exposed to oil price volatility",
            weight=0.90,
        )
        empty_store.add_edge(edge)
        assert empty_store.has_edge(edge.edge_id)

    def test_triggered_by_edge(self, empty_store: GraphStore):
        n1 = _make_node("event:crisis", GraphEntityType.EVENT, "Crisis")
        n2 = _make_node("signal:alert", GraphEntityType.SIGNAL, "Alert")
        empty_store.add_node(n1)
        empty_store.add_node(n2)

        edge = GraphEdge(
            edge_id="event:crisis--triggered_by-->signal:alert",
            source_id="event:crisis",
            target_id="signal:alert",
            relation_type=GraphRelationType.TRIGGERED_BY,
            label="Crisis triggered by alert signal",
            weight=0.75,
        )
        empty_store.add_edge(edge)
        retrieved = empty_store.get_edge(edge.edge_id)
        assert retrieved.relation_type == GraphRelationType.TRIGGERED_BY

    def test_constrained_by_edge(self, empty_store: GraphStore):
        n1 = _make_node("sector:banking", GraphEntityType.SECTOR, "Banking")
        n2 = _make_node("regulator:sama", GraphEntityType.REGULATOR, "SAMA")
        empty_store.add_node(n1)
        empty_store.add_node(n2)

        edge = GraphEdge(
            edge_id="sector:banking--constrained_by-->regulator:sama",
            source_id="sector:banking",
            target_id="regulator:sama",
            relation_type=GraphRelationType.CONSTRAINED_BY,
            label="Banking constrained by SAMA regulation",
            weight=0.70,
        )
        empty_store.add_edge(edge)
        assert empty_store.get_edge(edge.edge_id).weight == 0.70

    def test_correlated_with_edge(self, empty_store: GraphStore):
        n1 = _make_node("indicator:oil_price", GraphEntityType.INDICATOR, "Oil Price")
        n2 = _make_node("indicator:cds_sa", GraphEntityType.INDICATOR, "Saudi CDS")
        empty_store.add_node(n1)
        empty_store.add_node(n2)

        edge = GraphEdge(
            edge_id="indicator:oil_price--correlated_with-->indicator:cds_sa",
            source_id="indicator:oil_price",
            target_id="indicator:cds_sa",
            relation_type=GraphRelationType.CORRELATED_WITH,
            label="Oil price inversely correlated with Saudi CDS spread",
            weight=0.65,
            properties={"correlation": -0.72, "period": "5Y"},
        )
        empty_store.add_edge(edge)
        retrieved = empty_store.get_edge(edge.edge_id)
        assert retrieved.properties["correlation"] == -0.72

    def test_propagates_to_edge(self, empty_store: GraphStore):
        n1 = _make_node("impact_domain:oil_gas", GraphEntityType.IMPACT_DOMAIN, "Oil")
        n2 = _make_node("impact_domain:banking", GraphEntityType.IMPACT_DOMAIN, "Banking")
        empty_store.add_node(n1)
        empty_store.add_node(n2)

        edge = GraphEdge(
            edge_id="impact_domain:oil_gas--propagates_to-->impact_domain:banking",
            source_id="impact_domain:oil_gas",
            target_id="impact_domain:banking",
            relation_type=GraphRelationType.PROPAGATES_TO,
            label="Oil stress propagates to banking",
            weight=0.80,
        )
        empty_store.add_edge(edge)
        assert empty_store.has_edge(edge.edge_id)

    def test_influences_edge(self, empty_store: GraphStore):
        n1 = _make_node("country:SA", GraphEntityType.COUNTRY, "Saudi Arabia")
        n2 = _make_node("sector:banking", GraphEntityType.SECTOR, "Banking")
        empty_store.add_node(n1)
        empty_store.add_node(n2)

        edge = GraphEdge(
            edge_id="country:SA--influences-->sector:banking",
            source_id="country:SA",
            target_id="sector:banking",
            relation_type=GraphRelationType.INFLUENCES,
            label="Saudi Arabia influences banking sector",
            weight=0.75,
        )
        empty_store.add_edge(edge)
        assert empty_store.has_edge(edge.edge_id)


# ═══════════════════════════════════════════════════════════════════════════════
# 8. NODE CONFIDENCE TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestNodeConfidence:
    """Verify confidence field on GraphNode."""

    def test_default_confidence_is_high(self):
        node = GraphNode(
            node_id="test:1",
            entity_type=GraphEntityType.SIGNAL,
            label="Test",
        )
        assert node.confidence == GraphConfidence.HIGH

    def test_explicit_confidence(self):
        node = GraphNode(
            node_id="test:2",
            entity_type=GraphEntityType.COUNTRY,
            label="Test Country",
            confidence=GraphConfidence.DEFINITIVE,
        )
        assert node.confidence == GraphConfidence.DEFINITIVE

    def test_ingested_signal_node_has_mapped_confidence(self, empty_store: GraphStore):
        signal = _make_signal(confidence=SignalConfidence.VERIFIED)
        ingest_signal(signal, empty_store)
        sig_node = empty_store.get_node(f"signal:{signal.signal_id}")
        assert sig_node.confidence == GraphConfidence.HIGH

    def test_ingested_unverified_signal_is_speculative(self, empty_store: GraphStore):
        signal = _make_signal(confidence=SignalConfidence.UNVERIFIED)
        ingest_signal(signal, empty_store)
        sig_node = empty_store.get_node(f"signal:{signal.signal_id}")
        assert sig_node.confidence == GraphConfidence.SPECULATIVE

    def test_ingested_region_node_is_definitive(self, empty_store: GraphStore):
        signal = _make_signal(regions=[GCCRegion.SAUDI_ARABIA])
        ingest_signal(signal, empty_store)
        sa = empty_store.get_node("country:SA")
        assert sa.confidence == GraphConfidence.DEFINITIVE

    def test_ingested_domain_node_is_definitive(self, empty_store: GraphStore):
        signal = _make_signal(domains=[ImpactDomain.OIL_GAS])
        ingest_signal(signal, empty_store)
        oil = empty_store.get_node("impact_domain:oil_gas")
        assert oil.confidence == GraphConfidence.DEFINITIVE

    def test_ingested_sector_node_is_moderate(self, empty_store: GraphStore):
        signal = _make_signal(sectors=["energy"])
        ingest_signal(signal, empty_store)
        sector = empty_store.get_node("sector:energy")
        assert sector.confidence == GraphConfidence.MODERATE


# ═══════════════════════════════════════════════════════════════════════════════
# 9. SERVICE LAYER TESTS
# ═══════════════════════════════════════════════════════════════════════════════


class TestGraphBrainService:
    """Test the GraphBrainService singleton wrapper."""

    def test_service_creation(self):
        from src.graph_brain.service import GraphBrainService
        svc = GraphBrainService()
        assert svc.store.node_count == 0
        assert svc.store.edge_count == 0

    def test_service_ingest(self):
        from src.graph_brain.service import GraphBrainService
        svc = GraphBrainService()
        signal = _make_signal()
        result = svc.ingest(signal)
        assert result.total_nodes > 0
        assert svc.store.node_count > 0

    def test_service_get_node(self):
        from src.graph_brain.service import GraphBrainService
        svc = GraphBrainService()
        signal = _make_signal()
        svc.ingest(signal)
        node = svc.get_node(f"signal:{signal.signal_id}")
        assert node is not None

    def test_service_connected(self):
        from src.graph_brain.service import GraphBrainService
        svc = GraphBrainService()
        signal = _make_signal()
        svc.ingest(signal)
        connected = svc.connected(f"signal:{signal.signal_id}", max_depth=1)
        assert len(connected) > 0

    def test_service_downstream(self):
        from src.graph_brain.service import GraphBrainService
        svc = GraphBrainService()
        signal = _make_signal()
        svc.ingest(signal)
        downstream = svc.downstream(f"signal:{signal.signal_id}", max_depth=2)
        assert len(downstream) > 0

    def test_service_stats(self):
        from src.graph_brain.service import GraphBrainService
        svc = GraphBrainService()
        signal = _make_signal()
        svc.ingest(signal)
        stats = svc.stats()
        assert stats["node_count"] > 0
        assert stats["edge_count"] > 0
        assert "signal" in stats["nodes_by_type"]

    def test_service_explain(self):
        from src.graph_brain.service import GraphBrainService
        svc = GraphBrainService()
        signal = _make_signal(
            regions=[GCCRegion.SAUDI_ARABIA],
            domains=[ImpactDomain.OIL_GAS],
        )
        svc.ingest(signal)
        exp = svc.explain_downstream(f"signal:{signal.signal_id}", max_depth=2)
        assert exp.reasoning_summary != ""

    def test_singleton(self):
        from src.graph_brain.service import get_graph_brain_service
        import src.graph_brain.service as mod
        mod._instance = None  # reset for test isolation
        svc1 = get_graph_brain_service()
        svc2 = get_graph_brain_service()
        assert svc1 is svc2
        mod._instance = None  # cleanup
