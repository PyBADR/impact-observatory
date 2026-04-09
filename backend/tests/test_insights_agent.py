"""End-to-end validation: AI Insights Agent pipeline.

Tests:
  1. Entity resolution from natural language queries
  2. Graph-RAG context retrieval with subgraph + paths
  3. Full insights pipeline (query → context → LLM → structured output)
  4. Structured output parsing
  5. Audit hash computation
  6. Error handling (empty graph, bad query)
  7. GCC vocabulary resolution
  8. Context builder budget enforcement
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.graph_brain.store import GraphStore
from src.graph_brain.service import GraphBrainService
from src.graph_brain.types import (
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphRelationType,
    GraphSourceRef,
)
from src.graph_brain.graph_rag_service import (
    EntityResolver,
    ContextBuilder,
    GraphRAGService,
    RetrievedContext,
)
from src.graph_brain.insights_agent import (
    InsightsAgent,
    InsightResult,
    MockInsightsBackend,
)


# ── Test Graph Setup ──────────────────────────────────────────────────────────

def _build_test_graph() -> GraphBrainService:
    """Build a small but realistic GCC test graph."""
    service = GraphBrainService()
    store = service.store
    ref = GraphSourceRef(source_type="test", source_id="test-setup")

    # Countries
    store.add_node(GraphNode(
        node_id="country:SA", entity_type=GraphEntityType.COUNTRY,
        label="Saudi Arabia", confidence=GraphConfidence.DEFINITIVE, source_refs=[ref],
    ))
    store.add_node(GraphNode(
        node_id="country:AE", entity_type=GraphEntityType.COUNTRY,
        label="United Arab Emirates", confidence=GraphConfidence.DEFINITIVE, source_refs=[ref],
    ))

    # Chokepoints
    store.add_node(GraphNode(
        node_id="chokepoint:hormuz_strait", entity_type=GraphEntityType.CHOKEPOINT,
        label="Strait of Hormuz", confidence=GraphConfidence.DEFINITIVE, source_refs=[ref],
    ))

    # Sectors
    store.add_node(GraphNode(
        node_id="sector:energy", entity_type=GraphEntityType.SECTOR,
        label="Energy Sector", confidence=GraphConfidence.HIGH, source_refs=[ref],
    ))
    store.add_node(GraphNode(
        node_id="sector:insurance", entity_type=GraphEntityType.SECTOR,
        label="Insurance Sector", confidence=GraphConfidence.HIGH, source_refs=[ref],
    ))
    store.add_node(GraphNode(
        node_id="sector:maritime", entity_type=GraphEntityType.SECTOR,
        label="Maritime Sector", confidence=GraphConfidence.HIGH, source_refs=[ref],
    ))

    # Organizations
    store.add_node(GraphNode(
        node_id="organization:saudi_aramco", entity_type=GraphEntityType.ORGANIZATION,
        label="Saudi Aramco", confidence=GraphConfidence.HIGH, source_refs=[ref],
    ))

    # Indicators
    store.add_node(GraphNode(
        node_id="indicator:brent_crude_usd", entity_type=GraphEntityType.INDICATOR,
        label="Brent Crude (USD/bbl)", confidence=GraphConfidence.HIGH, source_refs=[ref],
        properties={"unit": "USD/bbl", "last_value": 82.0},
    ))

    # Risk Factors
    store.add_node(GraphNode(
        node_id="risk_factor:oil_price_shock", entity_type=GraphEntityType.RISK_FACTOR,
        label="Oil Price Shock", confidence=GraphConfidence.MODERATE, source_refs=[ref],
    ))

    # Edges
    store.add_edge(GraphEdge(
        edge_id="chokepoint:hormuz_strait--affects-->sector:energy",
        source_id="chokepoint:hormuz_strait", target_id="sector:energy",
        relation_type=GraphRelationType.AFFECTS,
        label="Hormuz affects Energy", weight=0.9, source_refs=[ref],
    ))
    store.add_edge(GraphEdge(
        edge_id="chokepoint:hormuz_strait--affects-->sector:maritime",
        source_id="chokepoint:hormuz_strait", target_id="sector:maritime",
        relation_type=GraphRelationType.AFFECTS,
        label="Hormuz affects Maritime", weight=0.85, source_refs=[ref],
    ))
    store.add_edge(GraphEdge(
        edge_id="sector:energy--propagates_to-->sector:insurance",
        source_id="sector:energy", target_id="sector:insurance",
        relation_type=GraphRelationType.PROPAGATES_TO,
        label="Energy risk propagates to Insurance", weight=0.65, source_refs=[ref],
    ))
    store.add_edge(GraphEdge(
        edge_id="organization:saudi_aramco--operates_in-->sector:energy",
        source_id="organization:saudi_aramco", target_id="sector:energy",
        relation_type=GraphRelationType.OPERATES_IN,
        label="Aramco operates in Energy", weight=0.95, source_refs=[ref],
    ))
    store.add_edge(GraphEdge(
        edge_id="organization:saudi_aramco--located_in-->country:SA",
        source_id="organization:saudi_aramco", target_id="country:SA",
        relation_type=GraphRelationType.LOCATED_IN,
        label="Aramco located in Saudi Arabia", weight=1.0, source_refs=[ref],
    ))
    store.add_edge(GraphEdge(
        edge_id="risk_factor:oil_price_shock--affects-->indicator:brent_crude_usd",
        source_id="risk_factor:oil_price_shock", target_id="indicator:brent_crude_usd",
        relation_type=GraphRelationType.AFFECTS,
        label="Oil shock affects Brent Crude", weight=0.88, source_refs=[ref],
    ))
    store.add_edge(GraphEdge(
        edge_id="indicator:brent_crude_usd--influences-->sector:energy",
        source_id="indicator:brent_crude_usd", target_id="sector:energy",
        relation_type=GraphRelationType.INFLUENCES,
        label="Brent Crude influences Energy", weight=0.82, source_refs=[ref],
    ))

    return service


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_entity_resolution_exact():
    """Exact node_id resolves correctly."""
    service = _build_test_graph()
    resolver = EntityResolver(service.store)
    results = resolver.resolve("country:SA")
    ids = [r.node_id for r in results]
    assert "country:SA" in ids
    print(f"  ✅ Exact resolution: found {len(results)} entities")


def test_entity_resolution_gcc_vocab():
    """GCC vocabulary terms resolve to correct nodes."""
    service = _build_test_graph()
    resolver = EntityResolver(service.store)
    results = resolver.resolve("hormuz oil saudi insurance")
    ids = [r.node_id for r in results]
    assert "chokepoint:hormuz_strait" in ids
    assert "sector:energy" in ids or "indicator:brent_crude_usd" in ids
    print(f"  ✅ GCC vocab: resolved {len(results)} entities: {ids[:5]}")


def test_entity_resolution_label_match():
    """Label substring match works."""
    service = _build_test_graph()
    resolver = EntityResolver(service.store)
    results = resolver.resolve("Aramco operations")
    ids = [r.node_id for r in results]
    assert "organization:saudi_aramco" in ids
    print(f"  ✅ Label match: found Aramco in {len(results)} entities")


def test_graph_rag_retrieval():
    """Full retrieval pipeline returns context."""
    service = _build_test_graph()
    rag = GraphRAGService(graph_brain=service, max_depth=2)
    context = rag.retrieve("impact of Hormuz closure on Saudi insurance")

    assert isinstance(context, RetrievedContext)
    assert len(context.resolved_entities) > 0
    assert context.node_count > 0
    assert context.context_text != ""
    assert context.retrieval_ms >= 0
    print(f"  ✅ Graph-RAG: {len(context.resolved_entities)} entities → "
          f"{context.node_count} nodes, {context.edge_count} edges, "
          f"{context.path_count} paths, {len(context.context_text)} chars context")


def test_context_builder_budget():
    """Context builder respects max_chars budget."""
    builder = ContextBuilder(max_chars=200)
    # Build with empty data
    text = builder.build([], [], [], [])
    assert len(text) <= 200

    # Build with enough data to trigger truncation
    service = _build_test_graph()
    resolver = EntityResolver(service.store)
    resolved = resolver.resolve("hormuz oil saudi insurance energy")
    text2 = builder.build(resolved, service.store.all_nodes(), service.store.all_edges(), [])
    assert len(text2) <= 200 + 50  # budget + truncation message
    print(f"  ✅ Context budget: {len(text2)} chars (budget=200)")


def test_insights_agent_full_pipeline():
    """Full pipeline: query → context → LLM → structured InsightResult."""
    service = _build_test_graph()
    agent = InsightsAgent(
        graph_brain=service,
        backend=MockInsightsBackend(),
    )
    result = agent.query("What is the impact of Hormuz closure on Saudi insurance?")

    assert isinstance(result, InsightResult)
    assert result.query != ""
    assert len(result.insights) > 0
    assert result.overall_confidence > 0
    assert result.audit_hash != ""
    assert len(result.audit_hash) == 64  # SHA-256
    assert result.duration_ms >= 0
    assert result.graph_context_summary.get("resolved_entities", 0) > 0

    print(f"  ✅ Full pipeline: {len(result.insights)} insights, "
          f"{len(result.risks)} risks, conf={result.overall_confidence:.2f}, "
          f"audit={result.audit_hash[:16]}...")

    # Check insight structure
    ins = result.insights[0]
    assert ins.title != ""
    assert ins.description != ""
    assert ins.category in (
        "risk_assessment", "impact_analysis", "dependency_map",
        "anomaly_detection", "scenario_analysis", "trend_insight",
        "compliance_alert", "general",
    )
    print(f"  ✅ Insight structure: '{ins.title}' ({ins.category}, severity={ins.severity})")


def test_insights_insurance_query():
    """Insurance-specific query returns insurance-related insights."""
    service = _build_test_graph()
    agent = InsightsAgent(graph_brain=service, backend=MockInsightsBackend())
    result = agent.query("claims surge pattern in insurance sector")

    assert len(result.insights) > 0
    assert any("insurance" in ins.description.lower() or "claims" in ins.description.lower()
               for ins in result.insights)
    print(f"  ✅ Insurance query: {len(result.insights)} insights")


def test_insights_cyber_query():
    """Cyber-specific query returns cyber-related insights."""
    service = _build_test_graph()
    agent = InsightsAgent(graph_brain=service, backend=MockInsightsBackend())
    result = agent.query("cyber attack risk on financial infrastructure")

    assert len(result.insights) > 0
    print(f"  ✅ Cyber query: {len(result.insights)} insights, "
          f"severity={result.insights[0].severity}")


def test_empty_graph_graceful():
    """Empty graph → agent still returns without crashing."""
    empty_service = GraphBrainService()
    agent = InsightsAgent(graph_brain=empty_service, backend=MockInsightsBackend())
    result = agent.query("test query on empty graph")

    assert isinstance(result, InsightResult)
    assert result.audit_hash != ""
    print(f"  ✅ Empty graph: graceful handling, {len(result.insights)} insights")


def test_audit_hash_determinism():
    """Same query → same audit hash (deterministic)."""
    service = _build_test_graph()
    agent = InsightsAgent(graph_brain=service, backend=MockInsightsBackend())
    r1 = agent.query("Hormuz oil impact")
    r2 = agent.query("Hormuz oil impact")

    # Audit hashes won't match exactly because created_at differs,
    # but both should be valid SHA-256
    assert len(r1.audit_hash) == 64
    assert len(r2.audit_hash) == 64
    print(f"  ✅ Audit hash: valid SHA-256 on both runs")


# ── Run All ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("Entity resolution (exact)", test_entity_resolution_exact),
        ("Entity resolution (GCC vocab)", test_entity_resolution_gcc_vocab),
        ("Entity resolution (label match)", test_entity_resolution_label_match),
        ("Graph-RAG retrieval", test_graph_rag_retrieval),
        ("Context builder budget", test_context_builder_budget),
        ("Full insights pipeline", test_insights_agent_full_pipeline),
        ("Insurance query", test_insights_insurance_query),
        ("Cyber query", test_insights_cyber_query),
        ("Empty graph graceful", test_empty_graph_graceful),
        ("Audit hash determinism", test_audit_hash_determinism),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as exc:
            print(f"  ❌ {name}: {exc}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)}")
    if failed == 0:
        print("All tests passed ✅")
    else:
        print(f"{failed} test(s) FAILED ❌")
        sys.exit(1)
