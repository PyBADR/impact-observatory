"""
Contract tests for the Impact Intelligence Layer (Stage 42).

Tests:
  - Schema import and instantiation
  - Impact map engine builds valid response for all scenarios
  - Decision overlay engine maps actions to overlays
  - Validator catches known bad inputs
  - Regime integration modifies nodes/edges
  - Cross-scenario coverage (all 20 scenarios)
"""
from __future__ import annotations

import pytest

from src.simulation_engine import SimulationEngine, GCC_NODES, GCC_ADJACENCY, SCENARIO_CATALOG
from src.schemas.impact_map import (
    ImpactMapResponse,
    ImpactMapNode,
    ImpactMapEdge,
    PropagationEvent,
    TimelinePoint,
    DecisionOverlay,
    RegimeInfluence,
    ImpactMapHeadline,
    ValidationFlag,
)
from src.engines.impact_map_engine import build_impact_map
from src.engines.decision_overlay_engine import build_decision_overlays
from src.engines.impact_map_validator import validate_impact_map
from src.regime.regime_engine import classify_regime_from_result
from src.regime.regime_graph_adapter import apply_regime_to_graph


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def engine():
    return SimulationEngine()


@pytest.fixture(scope="module")
def hormuz_result(engine):
    return engine.run("hormuz_chokepoint_disruption", 0.75, horizon_hours=336)


@pytest.fixture(scope="module")
def hormuz_impact_map(hormuz_result):
    rs = classify_regime_from_result(hormuz_result)
    rm = apply_regime_to_graph(rs.regime_id, GCC_NODES, GCC_ADJACENCY)
    im = build_impact_map(
        result=hormuz_result,
        gcc_nodes=GCC_NODES,
        gcc_adjacency=GCC_ADJACENCY,
        regime_modifiers=rm,
        scenario_id="hormuz_chokepoint_disruption",
        run_id="test-hormuz",
    )
    return validate_impact_map(im)


# ── Schema Tests ──────────────────────────────────────────────────────────────

class TestSchemaContract:
    def test_empty_response_instantiates(self):
        r = ImpactMapResponse()
        assert r.node_count == 0
        assert r.edge_count == 0
        assert r.propagation_event_count == 0
        assert r.overlay_count == 0
        assert r.nodes == []
        assert r.edges == []
        assert r.validation_flags == []

    def test_node_type_literals(self):
        for t in ["BANK", "FINTECH", "PAYMENT_RAIL", "PORT", "SHIPPING_LANE",
                   "ENERGY_ASSET", "REGULATOR", "INSURER", "MARKET_INFRA"]:
            n = ImpactMapNode(id="test", type=t)
            assert n.type == t

    def test_edge_type_literals(self):
        for t in ["LIQUIDITY_DEPENDENCY", "PAYMENT_DEPENDENCY", "TRADE_FLOW",
                   "ENERGY_SUPPLY", "INSURANCE_CLAIMS_LINK", "REGULATORY_CONTROL",
                   "CORRESPONDENT_BANKING", "SETTLEMENT_ROUTE"]:
            e = ImpactMapEdge(source="a", target="b", type=t)
            assert e.type == t

    def test_overlay_operation_literals(self):
        for op in ["CUT", "DELAY", "REDIRECT", "BUFFER", "NOTIFY", "ISOLATE"]:
            o = DecisionOverlay(operation=op, target_node="test")
            assert o.operation == op

    def test_node_stress_bounds(self):
        with pytest.raises(Exception):
            ImpactMapNode(id="test", stress_level=1.5)
        with pytest.raises(Exception):
            ImpactMapNode(id="test", stress_level=-0.1)

    def test_edge_requires_source_target(self):
        with pytest.raises(Exception):
            ImpactMapEdge(source="", target="b")
        with pytest.raises(Exception):
            ImpactMapEdge(source="a", target="")

    def test_overlay_requires_target(self):
        with pytest.raises(Exception):
            DecisionOverlay(operation="CUT")

    def test_response_syncs_counts(self):
        r = ImpactMapResponse(
            nodes=[ImpactMapNode(id="a"), ImpactMapNode(id="b")],
            edges=[ImpactMapEdge(source="a", target="b")],
            propagation_events=[PropagationEvent(event_id="e1")],
        )
        assert r.node_count == 2
        assert r.edge_count == 1
        assert r.propagation_event_count == 1

    def test_model_dump_serializable(self):
        r = ImpactMapResponse(run_id="test", scenario_id="test_scenario")
        d = r.model_dump()
        assert isinstance(d, dict)
        assert d["run_id"] == "test"
        assert isinstance(d["nodes"], list)
        assert isinstance(d["edges"], list)


# ── Engine Tests ──────────────────────────────────────────────────────────────

class TestImpactMapEngine:
    def test_builds_43_nodes(self, hormuz_impact_map):
        assert hormuz_impact_map.node_count == 43

    def test_builds_188_edges(self, hormuz_impact_map):
        assert hormuz_impact_map.edge_count == 188

    def test_has_propagation_events(self, hormuz_impact_map):
        assert hormuz_impact_map.propagation_event_count > 0

    def test_has_timeline(self, hormuz_impact_map):
        assert len(hormuz_impact_map.timeline) > 0

    def test_has_categories(self, hormuz_impact_map):
        assert len(hormuz_impact_map.categories) >= 2

    def test_nodes_have_valid_types(self, hormuz_impact_map):
        valid_types = {"BANK", "FINTECH", "PAYMENT_RAIL", "PORT", "SHIPPING_LANE",
                       "ENERGY_ASSET", "REGULATOR", "INSURER", "MARKET_INFRA"}
        for n in hormuz_impact_map.nodes:
            assert n.type in valid_types, f"Node {n.id} has invalid type {n.type}"

    def test_edges_have_valid_types(self, hormuz_impact_map):
        valid_types = {"LIQUIDITY_DEPENDENCY", "PAYMENT_DEPENDENCY", "TRADE_FLOW",
                       "ENERGY_SUPPLY", "INSURANCE_CLAIMS_LINK", "REGULATORY_CONTROL",
                       "CORRESPONDENT_BANKING", "SETTLEMENT_ROUTE"}
        for e in hormuz_impact_map.edges:
            assert e.type in valid_types, f"Edge {e.source}→{e.target} has invalid type {e.type}"

    def test_stressed_nodes_exist(self, hormuz_impact_map):
        stressed = [n for n in hormuz_impact_map.nodes if n.stress_level > 0.1]
        assert len(stressed) >= 5, "Hormuz scenario should stress multiple nodes"

    def test_active_edges_exist(self, hormuz_impact_map):
        active = [e for e in hormuz_impact_map.edges if e.is_active]
        assert len(active) >= 10, "Should have multiple active edges"

    def test_breakable_edges_exist(self, hormuz_impact_map):
        breakable = [e for e in hormuz_impact_map.edges if e.is_breakable]
        assert len(breakable) >= 1, "Hormuz scenario should have breakable edges"

    def test_headline_has_content(self, hormuz_impact_map):
        h = hormuz_impact_map.headline
        assert "Hormuz" in h.propagation_headline_en or "propagation" in h.propagation_headline_en.lower()
        assert h.sectors_impacted > 0

    def test_regime_influence_present(self, hormuz_impact_map):
        r = hormuz_impact_map.regime
        assert r.regime_id != ""
        assert r.propagation_amplifier >= 1.0

    def test_propagation_events_chronological(self, hormuz_impact_map):
        events = hormuz_impact_map.propagation_events
        for i in range(1, len(events)):
            assert events[i].arrival_hour >= events[i - 1].arrival_hour

    def test_timeline_monotonic(self, hormuz_impact_map):
        tl = hormuz_impact_map.timeline
        for i in range(1, len(tl)):
            assert tl[i].hour >= tl[i - 1].hour

    def test_node_stress_within_bounds(self, hormuz_impact_map):
        for n in hormuz_impact_map.nodes:
            assert 0.0 <= n.stress_level <= 1.0, f"Node {n.id} stress={n.stress_level}"

    def test_edge_weight_within_bounds(self, hormuz_impact_map):
        for e in hormuz_impact_map.edges:
            assert 0.0 <= e.weight <= 1.0, f"Edge {e.source}→{e.target} weight={e.weight}"

    def test_no_self_loop_edges(self, hormuz_impact_map):
        for e in hormuz_impact_map.edges:
            assert e.source != e.target, f"Self-loop: {e.source}"


# ── Overlay Tests ─────────────────────────────────────────────────────────────

class TestDecisionOverlayEngine:
    def test_maritime_actions_produce_overlays(self):
        actions = [
            {"action_id": "MAR-001", "action_en": "Divert", "priority_score": 0.9, "urgency": 0.85, "sector": "maritime"},
            {"action_id": "MAR-004", "action_en": "Force majeure", "priority_score": 0.7, "urgency": 0.6, "sector": "maritime"},
        ]
        overlays = build_decision_overlays(actions)
        assert len(overlays) >= 3  # MAR-001 has 2 overlays + MAR-004 has 1

    def test_cut_operation_weight_zero(self):
        actions = [{"action_id": "MAR-004", "action_en": "Cut", "priority_score": 0.7, "urgency": 0.6, "sector": "maritime"}]
        overlays = build_decision_overlays(actions)
        cuts = [o for o in overlays if o.operation == "CUT"]
        assert len(cuts) >= 1
        for c in cuts:
            assert c.weight_multiplier == 0.0

    def test_isolate_expands_edges(self):
        actions = [{"action_id": "LIQ-003", "action_en": "Capital controls", "priority_score": 0.8, "urgency": 0.7, "sector": "banking"}]
        overlays = build_decision_overlays(actions, GCC_ADJACENCY)
        # ISOLATE should expand to multiple CUT overlays for inbound edges
        cuts = [o for o in overlays if o.operation == "CUT"]
        assert len(cuts) >= 1, "ISOLATE should expand to CUT overlays"

    def test_unknown_action_gets_notify_fallback(self):
        actions = [{"action_id": "UNKNOWN-999", "action_en": "Unknown", "priority_score": 0.5, "urgency": 0.3, "sector": "banking"}]
        overlays = build_decision_overlays(actions)
        assert len(overlays) == 1
        assert overlays[0].operation == "NOTIFY"

    def test_buffer_has_capacity(self):
        actions = [{"action_id": "ENR-001", "action_en": "SPR release", "priority_score": 0.9, "urgency": 0.8, "sector": "energy"}]
        overlays = build_decision_overlays(actions)
        buffers = [o for o in overlays if o.operation == "BUFFER"]
        assert len(buffers) >= 1
        assert buffers[0].buffer_capacity_usd > 0


# ── Validator Tests ───────────────────────────────────────────────────────────

class TestImpactMapValidator:
    def test_empty_map_flags_error(self):
        im = ImpactMapResponse()
        im = validate_impact_map(im)
        errors = [f for f in im.validation_flags if f.severity == "error"]
        assert len(errors) >= 1  # at least "no nodes"

    def test_valid_map_passes(self, hormuz_impact_map):
        errors = [f for f in hormuz_impact_map.validation_flags if f.severity == "error"]
        assert len(errors) == 0, f"Valid map should have 0 errors, got: {[e.message for e in errors]}"

    def test_duplicate_node_flagged(self):
        im = ImpactMapResponse(
            nodes=[ImpactMapNode(id="dup"), ImpactMapNode(id="dup")],
            edges=[ImpactMapEdge(source="dup", target="dup")],
        )
        im = validate_impact_map(im)
        errors = [f for f in im.validation_flags if f.rule == "unique_node_id"]
        assert len(errors) >= 1

    def test_self_loop_flagged(self):
        im = ImpactMapResponse(
            nodes=[ImpactMapNode(id="a")],
            edges=[ImpactMapEdge(source="a", target="a")],
        )
        im = validate_impact_map(im)
        errors = [f for f in im.validation_flags if f.rule == "no_self_loops"]
        assert len(errors) >= 1

    def test_dangling_edge_flagged(self):
        im = ImpactMapResponse(
            nodes=[ImpactMapNode(id="a")],
            edges=[ImpactMapEdge(source="a", target="nonexistent")],
        )
        im = validate_impact_map(im)
        errors = [f for f in im.validation_flags if f.rule == "edge_target_exists"]
        assert len(errors) >= 1

    def test_flags_have_arabic(self):
        im = ImpactMapResponse()
        im = validate_impact_map(im)
        for f in im.validation_flags:
            assert f.message_ar != "", f"Flag {f.rule} missing Arabic message"


# ── Cross-Scenario Coverage ───────────────────────────────────────────────────

class TestCrossScenarioCoverage:
    @pytest.fixture(scope="class")
    def all_scenarios(self, engine):
        results = {}
        for sid in SCENARIO_CATALOG:
            result = engine.run(sid, 0.75, horizon_hours=336)
            rs = classify_regime_from_result(result)
            rm = apply_regime_to_graph(rs.regime_id, GCC_NODES, GCC_ADJACENCY)
            im = build_impact_map(
                result=result, gcc_nodes=GCC_NODES, gcc_adjacency=GCC_ADJACENCY,
                regime_modifiers=rm, scenario_id=sid, run_id=f"test-{sid}",
            )
            results[sid] = validate_impact_map(im)
        return results

    def test_all_scenarios_produce_43_nodes(self, all_scenarios):
        for sid, im in all_scenarios.items():
            assert im.node_count == 43, f"{sid}: expected 43 nodes, got {im.node_count}"

    def test_all_scenarios_produce_188_edges(self, all_scenarios):
        for sid, im in all_scenarios.items():
            assert im.edge_count == 188, f"{sid}: expected 188 edges, got {im.edge_count}"

    def test_all_scenarios_have_propagation_events(self, all_scenarios):
        for sid, im in all_scenarios.items():
            assert im.propagation_event_count > 0, f"{sid}: no propagation events"

    def test_all_scenarios_zero_errors(self, all_scenarios):
        for sid, im in all_scenarios.items():
            errors = [f for f in im.validation_flags if f.severity == "error"]
            assert len(errors) == 0, f"{sid}: {len(errors)} errors: {[e.message for e in errors]}"

    def test_all_scenarios_have_regime(self, all_scenarios):
        for sid, im in all_scenarios.items():
            assert im.regime.regime_id != "", f"{sid}: missing regime"

    def test_all_scenarios_have_headline(self, all_scenarios):
        for sid, im in all_scenarios.items():
            assert im.headline.propagation_headline_en != "", f"{sid}: empty headline"
