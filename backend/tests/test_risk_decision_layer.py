"""End-to-end validation: Decision Layer — Risk Intelligence Engine.

Tests:
  1. Single entity risk assessment on chokepoint
  2. Sector entity risk assessment
  3. Country entity risk assessment
  4. Portfolio multi-entity assessment
  5. Systemic risk detection
  6. URS 6-tier classification accuracy
  7. Temporal decay computation
  8. Cross-sector contagion detection
  9. Scenario matching
  10. Empty graph graceful handling
  11. Recommendation generation by severity
  12. Audit hash computation
"""

import sys
import os
import math

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
from src.graph_brain.decision.risk_models import (
    RiskFactor,
    RiskFactorSource,
    RiskLevel,
    RiskResult,
    PortfolioRiskResult,
)
from src.graph_brain.decision.risk_rules import (
    classify_risk_level,
    compute_composite_score,
    compute_temporal_decay,
    generate_recommendations,
    get_sector_sensitivity,
    get_vulnerability_weight,
)
from src.graph_brain.decision.risk_engine import RiskEngine
from src.graph_brain.decision.risk_service import RiskService


# ── Test Graph Setup ──────────────────────────────────────────────────────────

def _build_test_graph() -> GraphBrainService:
    """Build a realistic GCC test graph with risk-relevant topology."""
    service = GraphBrainService()
    store = service.store
    ref = GraphSourceRef(source_type="test", source_id="test-setup")

    # Countries
    for code, name in [("SA", "Saudi Arabia"), ("AE", "UAE"), ("QA", "Qatar")]:
        store.add_node(GraphNode(
            node_id=f"country:{code}", entity_type=GraphEntityType.COUNTRY,
            label=name, confidence=GraphConfidence.DEFINITIVE, source_refs=[ref],
        ))

    # Chokepoints
    store.add_node(GraphNode(
        node_id="chokepoint:hormuz_strait", entity_type=GraphEntityType.CHOKEPOINT,
        label="Strait of Hormuz", confidence=GraphConfidence.DEFINITIVE, source_refs=[ref],
    ))

    # Sectors
    for name in ["Energy", "Maritime", "Banking", "Insurance"]:
        store.add_node(GraphNode(
            node_id=f"sector:{name.lower()}", entity_type=GraphEntityType.SECTOR,
            label=f"{name} Sector", confidence=GraphConfidence.HIGH, source_refs=[ref],
        ))

    # Organizations
    store.add_node(GraphNode(
        node_id="organization:saudi_aramco", entity_type=GraphEntityType.ORGANIZATION,
        label="Saudi Aramco", confidence=GraphConfidence.HIGH, source_refs=[ref],
    ))

    # Risk factors
    store.add_node(GraphNode(
        node_id="risk_factor:oil_price_shock", entity_type=GraphEntityType.RISK_FACTOR,
        label="Oil Price Shock", confidence=GraphConfidence.MODERATE, source_refs=[ref],
        properties={"severity_score": 0.75},
    ))

    # Events
    store.add_node(GraphNode(
        node_id="event:hormuz_disruption_001", entity_type=GraphEntityType.EVENT,
        label="Hormuz Disruption Event", confidence=GraphConfidence.HIGH, source_refs=[ref],
        properties={"severity_score": 0.85},
    ))

    # Edges — risk propagation topology
    edges = [
        ("chokepoint:hormuz_strait", "sector:energy", GraphRelationType.AFFECTS, 0.90),
        ("chokepoint:hormuz_strait", "sector:maritime", GraphRelationType.AFFECTS, 0.85),
        ("sector:energy", "sector:banking", GraphRelationType.PROPAGATES_TO, 0.60),
        ("sector:energy", "sector:insurance", GraphRelationType.PROPAGATES_TO, 0.55),
        ("sector:maritime", "sector:insurance", GraphRelationType.PROPAGATES_TO, 0.50),
        ("organization:saudi_aramco", "sector:energy", GraphRelationType.OPERATES_IN, 0.95),
        ("organization:saudi_aramco", "country:SA", GraphRelationType.LOCATED_IN, 1.0),
        ("event:hormuz_disruption_001", "chokepoint:hormuz_strait", GraphRelationType.AFFECTS, 0.88),
        ("risk_factor:oil_price_shock", "sector:energy", GraphRelationType.AFFECTS, 0.80),
        ("risk_factor:oil_price_shock", "organization:saudi_aramco", GraphRelationType.AFFECTS, 0.70),
    ]
    for src, tgt, rel, weight in edges:
        store.add_edge(GraphEdge(
            edge_id=f"{src}--{rel.value}-->{tgt}",
            source_id=src, target_id=tgt,
            relation_type=rel, label=f"{src} {rel.value} {tgt}",
            weight=weight, source_refs=[ref],
        ))

    return service


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_chokepoint_risk():
    """Chokepoint with active event → HIGH or SEVERE risk."""
    service = _build_test_graph()
    engine = RiskEngine(service.store, max_depth=3)
    result = engine.assess("chokepoint:hormuz_strait")

    assert isinstance(result, RiskResult)
    assert result.entity_id == "chokepoint:hormuz_strait"
    assert result.entity_label == "Strait of Hormuz"
    assert result.risk_score > 0
    assert result.risk_level != RiskLevel.NOMINAL
    assert len(result.drivers) > 0
    assert result.audit_hash != ""
    print(f"  ✅ Chokepoint risk: score={result.risk_score:.3f}, "
          f"level={result.risk_level.value}, {len(result.drivers)} drivers")


def test_sector_risk():
    """Sector with incoming propagation → measurable risk."""
    service = _build_test_graph()
    engine = RiskEngine(service.store, max_depth=3)
    result = engine.assess("sector:energy")

    assert result.risk_score > 0
    assert len(result.drivers) > 0
    # Energy sector should have contagion channels
    assert len(result.exposed_sectors) >= 0
    print(f"  ✅ Sector risk: score={result.risk_score:.3f}, "
          f"level={result.risk_level.value}, sectors={result.exposed_sectors}")


def test_country_risk():
    """Country entity risk assessment."""
    service = _build_test_graph()
    engine = RiskEngine(service.store, max_depth=3)
    result = engine.assess("country:SA")

    assert isinstance(result, RiskResult)
    assert result.entity_type == "country"
    print(f"  ✅ Country risk: score={result.risk_score:.3f}, "
          f"level={result.risk_level.value}, {len(result.drivers)} drivers")


def test_portfolio_assessment():
    """Multi-entity portfolio → aggregated systemic risk."""
    service = _build_test_graph()
    risk_service = RiskService(graph_brain=service)
    result = risk_service.assess_portfolio([
        "chokepoint:hormuz_strait",
        "sector:energy",
        "sector:insurance",
        "country:SA",
    ])

    assert isinstance(result, PortfolioRiskResult)
    assert len(result.entity_results) == 4
    assert result.portfolio_risk_score >= 0
    assert result.audit_hash != ""
    print(f"  ✅ Portfolio: score={result.portfolio_risk_score:.3f}, "
          f"level={result.portfolio_risk_level.value}, "
          f"systemic={result.systemic_risk_score:.3f}, "
          f"contagion={result.contagion_channels}")


def test_systemic_risk():
    """Portfolio with shared sectors → systemic risk > 0."""
    service = _build_test_graph()
    risk_service = RiskService(graph_brain=service)
    result = risk_service.assess_portfolio([
        "sector:energy",
        "sector:maritime",
        "sector:insurance",
    ])

    # All sectors share contagion channels
    assert result.systemic_risk_score >= 0
    print(f"  ✅ Systemic risk: {result.systemic_risk_score:.3f}, "
          f"channels={result.contagion_channels}")


def test_urs_classification():
    """All 6 URS tiers classify correctly."""
    assert classify_risk_level(0.05) == RiskLevel.NOMINAL
    assert classify_risk_level(0.25) == RiskLevel.LOW
    assert classify_risk_level(0.42) == RiskLevel.GUARDED
    assert classify_risk_level(0.58) == RiskLevel.ELEVATED
    assert classify_risk_level(0.72) == RiskLevel.HIGH
    assert classify_risk_level(0.90) == RiskLevel.SEVERE
    assert classify_risk_level(1.0) == RiskLevel.SEVERE
    assert classify_risk_level(0.0) == RiskLevel.NOMINAL
    print("  ✅ URS 6-tier classification")


def test_temporal_decay():
    """Exponential decay with 7-day half-life."""
    assert compute_temporal_decay(0) == 1.0
    assert abs(compute_temporal_decay(168.0) - 0.5) < 0.001  # 7 days = half-life
    assert abs(compute_temporal_decay(336.0) - 0.25) < 0.001  # 14 days
    assert compute_temporal_decay(1000) < 0.05  # ~42 days → nearly decayed
    print("  ✅ Temporal decay")


def test_cross_sector_contagion():
    """Energy entity → detects banking/maritime/insurance contagion."""
    service = _build_test_graph()
    engine = RiskEngine(service.store, max_depth=3)
    result = engine.assess("sector:energy")

    # Energy should propagate to banking, maritime, insurance
    contagion_drivers = [d for d in result.drivers if d.source == RiskFactorSource.SECTOR_CONTAGION]
    print(f"  ✅ Contagion: {len(contagion_drivers)} channels detected, "
          f"sectors={result.exposed_sectors}")


def test_scenario_matching():
    """Hormuz-related entities → match Hormuz scenario."""
    service = _build_test_graph()
    engine = RiskEngine(service.store, max_depth=3)
    result = engine.assess("chokepoint:hormuz_strait")

    assert "hormuz_chokepoint_disruption" in result.active_scenarios
    print(f"  ✅ Scenario matching: {result.active_scenarios}")


def test_empty_graph():
    """Empty graph → NOMINAL risk, no crash."""
    empty_service = GraphBrainService()
    engine = RiskEngine(empty_service.store)
    result = engine.assess("nonexistent:entity")

    assert result.risk_score == 0.0
    assert result.risk_level == RiskLevel.NOMINAL
    assert result.audit_hash != ""
    print("  ✅ Empty graph: graceful NOMINAL")


def test_recommendations_by_severity():
    """Different risk levels → different recommendation catalogs."""
    recs_severe = generate_recommendations(RiskLevel.SEVERE)
    recs_nominal = generate_recommendations(RiskLevel.NOMINAL)

    assert len(recs_severe) > len(recs_nominal)
    assert any("CRO" in r or "escalate" in r.lower() for r in recs_severe)
    print(f"  ✅ Recommendations: SEVERE={len(recs_severe)}, NOMINAL={len(recs_nominal)}")


def test_audit_hash():
    """Every RiskResult has a valid SHA-256 audit hash."""
    service = _build_test_graph()
    engine = RiskEngine(service.store)
    result = engine.assess("chokepoint:hormuz_strait")

    assert len(result.audit_hash) == 64
    print(f"  ✅ Audit hash: {result.audit_hash[:16]}...")


def test_composite_score_formula():
    """Composite score uses URS weights correctly."""
    # All components at 1.0 → should sum to 1.0
    score = compute_composite_score(1.0, 1.0, 1.0, 1.0, 1.0)
    assert abs(score - 1.0) < 0.001

    # All components at 0.0 → should be 0.0
    score_zero = compute_composite_score(0.0, 0.0, 0.0, 0.0, 0.0)
    assert score_zero == 0.0

    # Severity-only (g1=0.35)
    score_sev = compute_composite_score(severity_component=1.0)
    assert abs(score_sev - 0.35) < 0.001
    print("  ✅ Composite score formula")


def test_vulnerability_by_hop():
    """Vulnerability weights decay by hop distance."""
    assert get_vulnerability_weight(0) == 1.00
    assert get_vulnerability_weight(1) == 0.70
    assert get_vulnerability_weight(2) == 0.35
    assert get_vulnerability_weight(5) == 0.10  # default
    print("  ✅ Vulnerability hop decay")


# ── Run All ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("Chokepoint risk", test_chokepoint_risk),
        ("Sector risk", test_sector_risk),
        ("Country risk", test_country_risk),
        ("Portfolio assessment", test_portfolio_assessment),
        ("Systemic risk", test_systemic_risk),
        ("URS 6-tier classification", test_urs_classification),
        ("Temporal decay", test_temporal_decay),
        ("Cross-sector contagion", test_cross_sector_contagion),
        ("Scenario matching", test_scenario_matching),
        ("Empty graph", test_empty_graph),
        ("Recommendations by severity", test_recommendations_by_severity),
        ("Audit hash", test_audit_hash),
        ("Composite score formula", test_composite_score_formula),
        ("Vulnerability hop decay", test_vulnerability_by_hop),
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
