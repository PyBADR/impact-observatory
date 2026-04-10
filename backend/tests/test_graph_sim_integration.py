"""
Tests for Graph Brain Integration Pack A — Simulation Engine Bridge.

Tests:
  1. Graph population from GCC_NODES + GCC_ADJACENCY
  2. Graph-enriched cross-sector dependencies
  3. Graph-enriched adjacency matrix
  4. Graph-backed causal chain explanation
  5. Fallback behavior when graph is unavailable
  6. End-to-end: simulation engine with graph enrichment
  7. Explanation correctness
"""

import pytest
from src.graph_brain.store import GraphStore
from src.graph_brain.sim_integration import (
    ensure_sim_graph_populated,
    graph_cross_sector_deps,
    graph_enriched_adjacency,
    graph_explain_causal_step,
    build_graph_explanation,
    set_sim_graph_enabled,
    is_sim_graph_active,
    SIM_GRAPH_ENABLED,
)
from src.graph_brain.types import (
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphRelationType,
    GraphSourceRef,
)
from src.risk_models import (
    compute_sector_exposure,
    compute_propagation,
    _CROSS_SECTOR_DEPS,
)
from src.explainability import build_causal_chain


# ── Fixtures ──────────────────────────────────────────────────────────────────

MINI_NODES = [
    {"id": "hormuz", "label": "Strait of Hormuz", "sector": "maritime",
     "capacity": 21_000_000, "current_load": 0.82, "criticality": 1.0, "redundancy": 0.05},
    {"id": "dubai_port", "label": "Jebel Ali Port", "sector": "maritime",
     "capacity": 22_000_000, "current_load": 0.73, "criticality": 0.90, "redundancy": 0.20},
    {"id": "saudi_aramco", "label": "Saudi Aramco", "sector": "energy",
     "capacity": 12_000_000, "current_load": 0.85, "criticality": 0.98, "redundancy": 0.18},
    {"id": "uae_banking", "label": "UAE Banking Sector", "sector": "banking",
     "capacity": 5_000_000, "current_load": 0.60, "criticality": 0.88, "redundancy": 0.30},
    {"id": "gcc_insurance", "label": "GCC Insurance", "sector": "insurance",
     "capacity": 2_000_000, "current_load": 0.50, "criticality": 0.70, "redundancy": 0.40},
    {"id": "gcc_fintech", "label": "GCC FinTech", "sector": "fintech",
     "capacity": 1_000_000, "current_load": 0.45, "criticality": 0.55, "redundancy": 0.50},
]

MINI_ADJACENCY = {
    "hormuz": ["dubai_port", "saudi_aramco"],
    "dubai_port": ["hormuz", "uae_banking", "gcc_insurance"],
    "saudi_aramco": ["hormuz", "uae_banking"],
    "uae_banking": ["dubai_port", "gcc_fintech", "gcc_insurance"],
    "gcc_insurance": ["uae_banking", "gcc_fintech"],
    "gcc_fintech": ["uae_banking"],
}

NODE_SECTORS = {n["id"]: n["sector"] for n in MINI_NODES}


@pytest.fixture
def graph_store():
    """Create and populate a fresh GraphStore with mini test data."""
    store = GraphStore()
    ensure_sim_graph_populated(store, MINI_NODES, MINI_ADJACENCY)
    return store


@pytest.fixture
def empty_store():
    """Return an empty GraphStore."""
    return GraphStore()


# ══════════════════════════════════════════════════════════════════════════════
# 1. Graph Population Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestGraphPopulation:
    """Test ensure_sim_graph_populated."""

    def test_all_nodes_added(self, graph_store: GraphStore):
        """All MINI_NODES should be in the store."""
        assert graph_store.node_count == len(MINI_NODES)
        for node_data in MINI_NODES:
            assert graph_store.has_node(node_data["id"])

    def test_node_properties_preserved(self, graph_store: GraphStore):
        """Node properties should match input data."""
        node = graph_store.get_node("hormuz")
        assert node is not None
        assert node.label == "Strait of Hormuz"
        assert node.properties["sector"] == "maritime"
        assert node.properties["criticality"] == 1.0
        assert node.confidence == GraphConfidence.DEFINITIVE

    def test_edges_added(self, graph_store: GraphStore):
        """All adjacency edges should be in the store."""
        total_edges = sum(len(v) for v in MINI_ADJACENCY.values())
        assert graph_store.edge_count == total_edges

    def test_idempotent(self, graph_store: GraphStore):
        """Re-populating should not duplicate nodes/edges."""
        stats = ensure_sim_graph_populated(graph_store, MINI_NODES, MINI_ADJACENCY)
        assert stats["nodes_added"] == 0
        assert stats["edges_added"] == 0
        assert stats["nodes_skipped"] == len(MINI_NODES)

    def test_edge_weights_from_criticality(self, graph_store: GraphStore):
        """Edge weights should be derived from target node criticality."""
        edge = graph_store.get_edge("hormuz--adjacent-->dubai_port")
        assert edge is not None
        # dubai_port criticality = 0.90 → weight = min(1.0, 0.5 + 0.90 * 0.4) = 0.86
        assert 0.8 <= edge.weight <= 0.95

    def test_population_stats(self):
        """Stats dict should report correct counts."""
        store = GraphStore()
        stats = ensure_sim_graph_populated(store, MINI_NODES, MINI_ADJACENCY)
        assert stats["nodes_added"] == len(MINI_NODES)
        total_edges = sum(len(v) for v in MINI_ADJACENCY.values())
        assert stats["edges_added"] == total_edges


# ══════════════════════════════════════════════════════════════════════════════
# 2. Graph-Enriched Causal Entry Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestGraphCausalEnrichment:
    """Test graph_cross_sector_deps."""

    def test_static_deps_returned_when_graph_none(self):
        """When store is None, should return static deps unchanged."""
        result = graph_cross_sector_deps(
            None, {"maritime"}, _CROSS_SECTOR_DEPS,
        )
        assert result is _CROSS_SECTOR_DEPS

    def test_static_deps_returned_when_disabled(self, graph_store):
        """When feature is disabled, should return static deps."""
        set_sim_graph_enabled(False)
        try:
            result = graph_cross_sector_deps(
                graph_store, {"maritime"}, _CROSS_SECTOR_DEPS,
            )
            assert result is _CROSS_SECTOR_DEPS
        finally:
            set_sim_graph_enabled(True)

    def test_graph_discovers_additional_deps(self, graph_store: GraphStore):
        """Graph should discover deps beyond static map."""
        static = {"maritime": ["energy"]}
        result = graph_cross_sector_deps(
            graph_store, {"maritime"}, static,
        )
        # Graph should find maritime → banking (via dubai_port → uae_banking)
        assert "banking" in result.get("maritime", [])

    def test_static_deps_preserved(self, graph_store: GraphStore):
        """Existing static deps should not be removed."""
        static = {"maritime": ["energy", "logistics"]}
        result = graph_cross_sector_deps(
            graph_store, {"maritime"}, static,
        )
        assert "energy" in result["maritime"]
        assert "logistics" in result["maritime"]

    def test_empty_shocked_sectors(self, graph_store: GraphStore):
        """Empty shocked sectors should return static deps."""
        result = graph_cross_sector_deps(
            graph_store, set(), _CROSS_SECTOR_DEPS,
        )
        assert result == {k: list(v) for k, v in _CROSS_SECTOR_DEPS.items()}


# ══════════════════════════════════════════════════════════════════════════════
# 3. Graph-Enriched Propagation Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestGraphPropagationEnrichment:
    """Test graph_enriched_adjacency."""

    def test_static_returned_when_graph_none(self):
        """When store is None, should return static adjacency."""
        result = graph_enriched_adjacency(None, MINI_ADJACENCY)
        assert result is MINI_ADJACENCY

    def test_static_returned_when_disabled(self, graph_store):
        """When feature disabled, should return static adjacency."""
        set_sim_graph_enabled(False)
        try:
            result = graph_enriched_adjacency(graph_store, MINI_ADJACENCY)
            assert result is MINI_ADJACENCY
        finally:
            set_sim_graph_enabled(True)

    def test_static_edges_preserved(self, graph_store: GraphStore):
        """All static adjacency edges should remain."""
        result = graph_enriched_adjacency(graph_store, MINI_ADJACENCY)
        for source, targets in MINI_ADJACENCY.items():
            assert source in result
            for target in targets:
                assert target in result[source]

    def test_does_not_mutate_input(self, graph_store: GraphStore):
        """Input adjacency dict should not be modified."""
        original = {k: list(v) for k, v in MINI_ADJACENCY.items()}
        graph_enriched_adjacency(graph_store, MINI_ADJACENCY)
        assert MINI_ADJACENCY == original

    def test_propagation_works_with_enriched_adjacency(self, graph_store: GraphStore):
        """compute_propagation should work with graph-enriched adjacency."""
        enriched = graph_enriched_adjacency(graph_store, MINI_ADJACENCY)
        result = compute_propagation(
            shock_nodes=["hormuz"],
            severity=0.7,
            adjacency=MINI_ADJACENCY,
            horizon_days=5,
            graph_adjacency=enriched,
        )
        assert len(result) > 0
        assert all(r["impact"] > 0 for r in result)


# ══════════════════════════════════════════════════════════════════════════════
# 4. Graph-Backed Explanation Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestGraphExplanation:
    """Test graph_explain_causal_step and build_graph_explanation."""

    def test_explain_step_returns_dict(self, graph_store: GraphStore):
        """Should return a dict with graph path info."""
        result = graph_explain_causal_step(
            graph_store, "hormuz", "dubai_port",
        )
        assert result is not None
        assert "graph_path" in result
        assert "relationships" in result
        assert "reasoning_chain" in result
        assert "confidence" in result
        assert len(result["relationships"]) > 0

    def test_explain_step_no_path(self, graph_store: GraphStore):
        """Should return None if no path exists."""
        # gcc_fintech has no path to hormuz (only outgoing to uae_banking)
        # Actually it does — uae_banking → dubai_port → hormuz
        # Let's use an edge case: add a disconnected node
        node = GraphNode(
            node_id="isolated_node",
            entity_type=GraphEntityType.INFRASTRUCTURE,
            label="Isolated",
            confidence=GraphConfidence.HIGH,
        )
        graph_store.add_node(node)
        result = graph_explain_causal_step(
            graph_store, "isolated_node", "hormuz",
        )
        assert result is None

    def test_explain_step_none_store(self):
        """Should return None if store is None."""
        result = graph_explain_causal_step(None, "hormuz", "dubai_port")
        assert result is None

    def test_build_full_explanation(self, graph_store: GraphStore):
        """Should build a full explanation with multiple steps."""
        causal_chain = [
            {"entity_id": "hormuz", "step": 0},
            {"entity_id": "dubai_port", "step": 1},
            {"entity_id": "uae_banking", "step": 2},
        ]
        propagation = [
            {"entity_id": "hormuz", "impact": 0.7, "step": 0},
            {"entity_id": "dubai_port", "impact": 0.5, "step": 1},
        ]
        result = build_graph_explanation(
            graph_store, ["hormuz"], propagation, causal_chain,
        )
        assert result is not None
        assert result["graph_paths_used"] > 0
        assert result["total_relationships"] > 0
        assert "reasoning_summary" in result

    def test_explanation_none_when_graph_unavailable(self):
        """Should return None if store is None."""
        result = build_graph_explanation(
            None, ["hormuz"], [], [],
        )
        assert result is None

    def test_explanation_confidence_field(self, graph_store: GraphStore):
        """Confidence should be a valid confidence level string."""
        result = graph_explain_causal_step(
            graph_store, "hormuz", "uae_banking",
        )
        assert result is not None
        valid_levels = {"definitive", "high", "moderate", "low", "speculative"}
        assert result["confidence"] in valid_levels


# ══════════════════════════════════════════════════════════════════════════════
# 5. Fallback Behavior Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestFallbackBehavior:
    """Test that graph failures don't break existing logic."""

    def test_sector_exposure_without_graph(self):
        """compute_sector_exposure should work identically without graph_deps."""
        result_no_graph = compute_sector_exposure(
            shock_nodes=["hormuz", "dubai_port"],
            severity=0.6,
            node_sectors=NODE_SECTORS,
            graph_deps=None,
        )
        result_static = compute_sector_exposure(
            shock_nodes=["hormuz", "dubai_port"],
            severity=0.6,
            node_sectors=NODE_SECTORS,
        )
        assert result_no_graph == result_static

    def test_propagation_without_graph(self):
        """compute_propagation should work identically without graph_adjacency."""
        result_no_graph = compute_propagation(
            shock_nodes=["hormuz"],
            severity=0.6,
            adjacency=MINI_ADJACENCY,
            horizon_days=5,
            graph_adjacency=None,
        )
        result_static = compute_propagation(
            shock_nodes=["hormuz"],
            severity=0.6,
            adjacency=MINI_ADJACENCY,
            horizon_days=5,
        )
        assert result_no_graph == result_static

    def test_causal_chain_without_graph(self):
        """build_causal_chain should work identically without graph_store."""
        propagation = [
            {"entity_id": "hormuz", "impact": 0.7, "step": 1, "propagation_score": 0.5,
             "mechanism": "Direct shock", "mechanism_en": "Direct shock"},
            {"entity_id": "dubai_port", "impact": 0.5, "step": 2, "propagation_score": 0.4,
             "mechanism": "Supply chain", "mechanism_en": "Supply chain"},
        ]
        financial = [
            {"entity_id": "hormuz", "loss_usd": 1_000_000},
            {"entity_id": "dubai_port", "loss_usd": 500_000},
        ]

        result_no_graph = build_causal_chain(
            shock_nodes=["hormuz"],
            propagation=propagation,
            financial_impacts=financial,
            severity=0.6,
            graph_store=None,
        )
        result_default = build_causal_chain(
            shock_nodes=["hormuz"],
            propagation=propagation,
            financial_impacts=financial,
            severity=0.6,
        )
        # Should produce same chain (no graph enrichment)
        assert len(result_no_graph) == len(result_default)
        for a, b in zip(result_no_graph, result_default):
            assert a["entity_id"] == b["entity_id"]
            assert a["step"] == b["step"]

    def test_feature_flag_disables_all(self, graph_store: GraphStore):
        """With SIM_GRAPH_ENABLED=False, all enrichment returns fallback."""
        set_sim_graph_enabled(False)
        try:
            assert not is_sim_graph_active()
            assert graph_cross_sector_deps(
                graph_store, {"maritime"}, _CROSS_SECTOR_DEPS,
            ) is _CROSS_SECTOR_DEPS
            assert graph_enriched_adjacency(
                graph_store, MINI_ADJACENCY,
            ) is MINI_ADJACENCY
            assert graph_explain_causal_step(
                graph_store, "hormuz", "dubai_port",
            ) is None
        finally:
            set_sim_graph_enabled(True)


# ══════════════════════════════════════════════════════════════════════════════
# 6. End-to-End: Sector Exposure with Graph Enrichment
# ══════════════════════════════════════════════════════════════════════════════

class TestEndToEndEnrichment:
    """Test that graph-enriched functions produce valid output."""

    def test_enriched_sector_exposure_valid(self, graph_store: GraphStore):
        """Graph-enriched sector exposure should be valid."""
        graph_deps = graph_cross_sector_deps(
            graph_store, {"maritime"}, _CROSS_SECTOR_DEPS,
        )
        result = compute_sector_exposure(
            shock_nodes=["hormuz", "dubai_port"],
            severity=0.6,
            node_sectors=NODE_SECTORS,
            graph_deps=graph_deps,
        )
        # All sectors should have exposure values
        assert len(result) > 0
        for sector, exposure in result.items():
            assert 0.0 <= exposure <= 1.0, f"{sector}: {exposure}"

    def test_enriched_propagation_valid(self, graph_store: GraphStore):
        """Graph-enriched propagation should produce valid results."""
        enriched = graph_enriched_adjacency(graph_store, MINI_ADJACENCY)
        result = compute_propagation(
            shock_nodes=["hormuz"],
            severity=0.7,
            adjacency=MINI_ADJACENCY,
            horizon_days=5,
            graph_adjacency=enriched,
        )
        assert len(result) > 0
        for r in result:
            assert 0.0 <= r["impact"] <= 1.0
            assert r["entity_id"] in enriched

    def test_enriched_causal_chain_with_graph(self, graph_store: GraphStore):
        """Causal chain with graph should include graph_explanation on steps."""
        propagation = [
            {"entity_id": "hormuz", "impact": 0.7, "step": 1, "propagation_score": 0.5,
             "mechanism": "Direct shock", "mechanism_en": "Direct shock"},
            {"entity_id": "dubai_port", "impact": 0.5, "step": 2, "propagation_score": 0.4,
             "mechanism": "Supply chain", "mechanism_en": "Supply chain"},
            {"entity_id": "uae_banking", "impact": 0.3, "step": 3, "propagation_score": 0.3,
             "mechanism": "Contagion", "mechanism_en": "Contagion"},
        ]
        financial = [
            {"entity_id": "hormuz", "loss_usd": 1_000_000},
            {"entity_id": "dubai_port", "loss_usd": 500_000},
            {"entity_id": "uae_banking", "loss_usd": 300_000},
        ]
        result = build_causal_chain(
            shock_nodes=["hormuz"],
            propagation=propagation,
            financial_impacts=financial,
            severity=0.7,
            graph_store=graph_store,
        )
        # At least one step should have graph_explanation
        graph_enriched = [
            s for s in result
            if "graph_explanation" in s and s["graph_explanation"] is not None
        ]
        assert len(graph_enriched) > 0

    def test_graph_explanation_fields(self, graph_store: GraphStore):
        """Graph explanation should have all required fields."""
        explanation = graph_explain_causal_step(
            graph_store, "hormuz", "dubai_port",
        )
        assert explanation is not None
        required_fields = {
            "graph_path", "path_weight", "path_hops",
            "relationships", "reasoning_chain",
            "confidence", "paths_found",
        }
        assert required_fields.issubset(explanation.keys())

        # Relationships should have structured data
        for rel in explanation["relationships"]:
            assert "source" in rel
            assert "target" in rel
            assert "relation" in rel
            assert "weight" in rel
            assert "confidence" in rel


# ══════════════════════════════════════════════════════════════════════════════
# 7. Explanation Correctness Tests
# ══════════════════════════════════════════════════════════════════════════════

class TestExplanationCorrectness:
    """Test that graph explanations are semantically correct."""

    def test_path_matches_source_target(self, graph_store: GraphStore):
        """Graph path should start from source and end at target."""
        explanation = graph_explain_causal_step(
            graph_store, "hormuz", "uae_banking",
        )
        assert explanation is not None
        # First relationship source should be hormuz
        if explanation["relationships"]:
            assert explanation["relationships"][0]["source"] == "hormuz"
            # Last relationship target should be uae_banking
            assert explanation["relationships"][-1]["target"] == "uae_banking"

    def test_path_weight_positive(self, graph_store: GraphStore):
        """Path weight should be positive."""
        explanation = graph_explain_causal_step(
            graph_store, "hormuz", "dubai_port",
        )
        assert explanation is not None
        assert explanation["path_weight"] > 0

    def test_reasoning_chain_human_readable(self, graph_store: GraphStore):
        """Reasoning chain should contain readable step descriptions."""
        explanation = graph_explain_causal_step(
            graph_store, "hormuz", "dubai_port",
        )
        assert explanation is not None
        for step in explanation["reasoning_chain"]:
            assert "→" in step  # should contain arrow notation
            assert len(step) > 5  # should be non-trivial
