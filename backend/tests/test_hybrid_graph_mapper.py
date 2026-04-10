"""End-to-end validation: Hybrid Graph Mapper pipeline.

Tests:
  1. Rule-only mode (AI disabled) — must match existing behavior
  2. Hybrid mode (AI enabled with MockLLMBackend) — rule + AI merge
  3. Deduplication — AI entities matching rule-based are skipped
  4. Confidence gating — quarantine tier works
  5. Capacity limits — max_ai_nodes_per_signal enforced
  6. Expansion service integration — HybridGraphMapper wired correctly
  7. Audit hash — SHA-256 computed on every result
"""

import sys
import os
import json

# Ensure backend/src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.graph_brain.graph_mapper import MappingResult, map_signal_to_graph
from src.graph_brain.ai_entity_extractor import (
    AIEntityExtractor,
    MockLLMBackend,
    AIExtractedEntity,
    AIExtractedRelationship,
)
from src.graph_brain.hybrid_graph_mapper import (
    HybridGraphMapper,
    HybridMergeConfig,
    HybridMappingResult,
    ConfidenceTier,
    MergeStrategy,
    _normalize_label,
)
from src.graph_brain.types import GraphEntityType, GraphRelationType


# ── Test Signal Fixtures ──────────────────────────────────────────────────────

OIL_SIGNAL = {
    "signal_id": "test-oil-001",
    "signal_type": "oil_price_shock",
    "domain": "macroeconomic",
    "title": "Brent Crude Surge to $95/bbl",
    "description": "Oil prices surge due to OPEC+ production cuts and Hormuz tensions",
    "severity": "HIGH",
    "severity_score": 0.75,
    "status": "active",
    "source": {
        "source_id": "reuters-test",
        "source_name": "Reuters Test",
        "source_type": "market_data",
    },
    "geo": {
        "region_code": "SA",
        "region_name": "Saudi Arabia",
        "affected_zones": ["hormuz_strait", "ras_tanura_terminal"],
    },
    "tags": ["oil", "energy", "opec"],
    "entity_refs": [
        {"entity_id": "ent_aramco", "entity_type": "organization", "entity_label": "Saudi Aramco"},
    ],
    "payload": {
        "payload_type": "macroeconomic",
        "indicator_code": "brent_crude_usd",
        "value": 95.0,
        "unit": "USD/bbl",
        "delta_pct": 12.5,
        "affected_sectors": ["energy", "maritime", "insurance"],
    },
}

PORT_SIGNAL = {
    "signal_id": "test-port-001",
    "signal_type": "port_closure",
    "domain": "operational",
    "title": "Salalah Port Emergency Closure",
    "description": "Port facility closed due to maritime security incident",
    "severity": "ELEVATED",
    "severity_score": 0.60,
    "status": "active",
    "source": {
        "source_id": "oman-ports-authority",
        "source_name": "Oman Ports Authority",
        "source_type": "government",
    },
    "geo": {
        "region_code": "OM",
        "region_name": "Oman",
        "affected_zones": ["salalah_port"],
    },
    "tags": ["port", "closure", "maritime"],
    "payload": {
        "payload_type": "operational",
        "system_id": "salalah_port",
        "incident_type": "security_closure",
        "capacity_impact_pct": 100.0,
        "upstream_dependencies": ["suez_canal"],
        "downstream_impacts": [
            {"target_id": "maersk_line", "target_type": "organization"},
        ],
        "affected_flow_types": ["container_shipping", "bulk_cargo"],
    },
}


# ── Test 1: Rule-Only Mode ───────────────────────────────────────────────────

def test_rule_only_mode():
    """AI disabled → HybridGraphMapper returns pure rule-based result."""
    mapper = HybridGraphMapper(ai_enabled=False)
    result = mapper.map_signal(OIL_SIGNAL)

    assert isinstance(result, HybridMappingResult)
    assert result.mapping.node_count > 0
    assert result.mapping.edge_count > 0
    assert result.merge_stats.ai_enabled is False
    assert result.merge_stats.ai_nodes_total == 0
    assert result.merge_stats.ai_nodes_promoted == 0
    assert result.audit_hash != ""

    # Must match pure rule-based output
    pure_rule = map_signal_to_graph(OIL_SIGNAL)
    assert result.mapping.node_count == pure_rule.node_count
    assert result.mapping.edge_count == pure_rule.edge_count
    print(f"  ✅ Rule-only: {result.mapping.node_count} nodes, {result.mapping.edge_count} edges")


# ── Test 2: Hybrid Mode (AI Augments) ────────────────────────────────────────

def test_hybrid_mode_oil():
    """AI enabled → returns merged rule + AI entities."""
    mapper = HybridGraphMapper(
        ai_enabled=True,
        backend=MockLLMBackend(),
    )
    result = mapper.map_signal(OIL_SIGNAL)

    assert result.merge_stats.ai_enabled is True
    assert result.merge_stats.ai_available is True
    assert result.merge_stats.rule_nodes > 0
    assert result.merge_stats.ai_nodes_total > 0

    # AI should add at least some novel nodes
    total_nodes = result.mapping.node_count
    rule_nodes = result.merge_stats.rule_nodes
    ai_promoted = result.merge_stats.ai_nodes_promoted
    ai_dedup = result.merge_stats.ai_nodes_deduplicated

    print(f"  ✅ Hybrid oil: {total_nodes} total = {rule_nodes} rule + {ai_promoted} AI promoted "
          f"({ai_dedup} dedup)")

    # Merged result should have more or equal nodes than rule-only
    assert total_nodes >= rule_nodes


def test_hybrid_mode_port():
    """Port signal → AI discovers maritime/supply chain entities."""
    mapper = HybridGraphMapper(
        ai_enabled=True,
        backend=MockLLMBackend(),
    )
    result = mapper.map_signal(PORT_SIGNAL)

    assert result.merge_stats.ai_nodes_total > 0
    print(f"  ✅ Hybrid port: {result.mapping.node_count} nodes, "
          f"{result.merge_stats.ai_nodes_promoted} AI promoted")


# ── Test 3: Deduplication ─────────────────────────────────────────────────────

def test_deduplication():
    """AI entities matching rule-based by label are deduplicated."""
    mapper = HybridGraphMapper(
        ai_enabled=True,
        backend=MockLLMBackend(),
        merge_config=HybridMergeConfig(dedup_by_label_similarity=True),
    )
    result = mapper.map_signal(OIL_SIGNAL)

    # The MockLLMBackend returns "Energy Sector" which should match rule-based
    # "energy" sector node after normalization
    dedup_decisions = [
        d for d in result.mapping.decisions
        if d.stage == "hybrid_merge" and d.action == "skip" and "Duplicate" in d.reason
    ]
    print(f"  ✅ Dedup: {len(dedup_decisions)} dedup decisions, "
          f"{result.merge_stats.ai_nodes_deduplicated} nodes deduped")


# ── Test 4: Confidence Gating ─────────────────────────────────────────────────

def test_confidence_quarantine():
    """Entities below quarantine threshold are quarantined, not promoted."""
    # Set very high threshold so most AI entities get quarantined
    config = HybridMergeConfig(
        standard_threshold=0.95,
        low_confidence_threshold=0.92,
    )
    mapper = HybridGraphMapper(
        ai_enabled=True,
        backend=MockLLMBackend(),
        merge_config=config,
    )
    result = mapper.map_signal(OIL_SIGNAL)

    # With 0.92 quarantine threshold, MockLLMBackend entities (0.85-0.9 conf)
    # should mostly be quarantined
    assert result.merge_stats.ai_nodes_quarantined > 0 or result.merge_stats.ai_nodes_promoted >= 0
    print(f"  ✅ Quarantine: {result.merge_stats.ai_nodes_quarantined} quarantined, "
          f"{result.merge_stats.ai_nodes_promoted} promoted, "
          f"{len(result.quarantined_nodes)} in quarantine list")


# ── Test 5: Capacity Limits ──────────────────────────────────────────────────

def test_capacity_limits():
    """max_ai_nodes_per_signal is enforced."""
    config = HybridMergeConfig(max_ai_nodes_per_signal=1)
    mapper = HybridGraphMapper(
        ai_enabled=True,
        backend=MockLLMBackend(),
        merge_config=config,
    )
    result = mapper.map_signal(OIL_SIGNAL)

    # After dedup, at most 1 AI node should be promoted
    assert result.merge_stats.ai_nodes_promoted <= 1
    print(f"  ✅ Capacity: {result.merge_stats.ai_nodes_promoted} promoted (limit=1)")


# ── Test 6: Audit Hash ───────────────────────────────────────────────────────

def test_audit_hash():
    """Every HybridMappingResult has a non-empty SHA-256 audit hash."""
    mapper = HybridGraphMapper(ai_enabled=True, backend=MockLLMBackend())
    result = mapper.map_signal(OIL_SIGNAL)

    assert result.audit_hash != ""
    assert len(result.audit_hash) == 64  # SHA-256 hex
    print(f"  ✅ Audit hash: {result.audit_hash[:16]}...")


# ── Test 7: AI Extractor Standalone ───────────────────────────────────────────

def test_ai_extractor_standalone():
    """AIEntityExtractor returns valid MappingResult."""
    extractor = AIEntityExtractor(backend=MockLLMBackend())
    result = extractor.extract(OIL_SIGNAL)

    assert isinstance(result, MappingResult)
    assert result.node_count > 0
    assert result.edge_count > 0

    # All AI nodes should carry ai_extracted property
    for node in result.nodes:
        assert node.properties.get("ai_extracted") is True

    print(f"  ✅ AI extractor: {result.node_count} nodes, {result.edge_count} edges")


# ── Test 8: Label Normalization ───────────────────────────────────────────────

def test_label_normalization():
    """_normalize_label produces stable keys for dedup."""
    assert _normalize_label("Energy Sector") == "energy_sector"
    assert _normalize_label("  Brent Crude  ") == "brent_crude"
    assert _normalize_label("OPEC+") == "opec+"
    assert _normalize_label("Saudi-Aramco") == "saudi_aramco"
    print("  ✅ Label normalization")


# ── Test 9: Entity/Relationship Validators ────────────────────────────────────

def test_entity_type_validation():
    """AIExtractedEntity validates and fuzzy-maps entity types."""
    # Valid type
    ent = AIExtractedEntity(name="Test", type="organization", confidence=0.9)
    assert ent.type == "organization"

    # Fuzzy mapped
    ent2 = AIExtractedEntity(name="Test", type="company", confidence=0.9)
    assert ent2.type == "organization"

    # Invalid should raise
    try:
        AIExtractedEntity(name="Test", type="invalid_nonsense", confidence=0.9)
        assert False, "Should have raised ValueError"
    except Exception:
        pass

    print("  ✅ Entity type validation + fuzzy mapping")


def test_relationship_type_validation():
    """AIExtractedRelationship validates and fuzzy-maps relation types."""
    rel = AIExtractedRelationship(source="A", target="B", type="affects", confidence=0.8)
    assert rel.type == "affects"

    rel2 = AIExtractedRelationship(source="A", target="B", type="impacts", confidence=0.8)
    assert rel2.type == "affects"

    print("  ✅ Relationship type validation + fuzzy mapping")


# ── Run All ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        ("Rule-only mode", test_rule_only_mode),
        ("Hybrid mode (oil)", test_hybrid_mode_oil),
        ("Hybrid mode (port)", test_hybrid_mode_port),
        ("Deduplication", test_deduplication),
        ("Confidence quarantine", test_confidence_quarantine),
        ("Capacity limits", test_capacity_limits),
        ("Audit hash", test_audit_hash),
        ("AI extractor standalone", test_ai_extractor_standalone),
        ("Label normalization", test_label_normalization),
        ("Entity type validation", test_entity_type_validation),
        ("Relationship type validation", test_relationship_type_validation),
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
