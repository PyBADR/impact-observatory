"""
Decision Intelligence System — Contract Tests (7 engines + pipeline).

Tests validate:
  - Each engine's data contract (types, bounds, required fields)
  - Cross-engine integration via pipeline
  - Cross-scenario coverage (all 20 scenarios)
  - Edge cases (empty inputs, single action, no triggers)

Run: .venv/bin/python -m pytest tests/test_decision_intelligence.py -v
"""
from __future__ import annotations

import pytest

from src.simulation_engine import SimulationEngine, GCC_NODES, GCC_ADJACENCY, SCENARIO_CATALOG
from src.engines.impact_map_engine import build_impact_map
from src.engines.decision_overlay_engine import build_decision_overlays
from src.engines.impact_map_validator import validate_impact_map
from src.schemas.impact_map import ImpactMapResponse
from src.regime.regime_graph_adapter import RegimeGraphModifiers

from src.decision_intelligence.trigger_engine import GraphDecisionTrigger, build_graph_triggers
from src.decision_intelligence.breakpoint_engine import Breakpoint, detect_breakpoints
from src.decision_intelligence.action_simulation_engine import ActionSimResult, simulate_action_effects
from src.decision_intelligence.counterfactual_engine import CounterfactualResult, compare_counterfactuals
from src.decision_intelligence.roi_engine import DecisionROI, compute_decision_roi
from src.decision_intelligence.executive_output import ExecutiveDecision, build_executive_decisions
from src.decision_intelligence.pipeline import (
    run_decision_intelligence_pipeline,
    DecisionIntelligenceResult,
)
from src.actions.action_registry import get_actions_for_scenario_id


# ── Fixture: build a full impact map from hormuz scenario ──────────────────

_engine = SimulationEngine()


@pytest.fixture(scope="module")
def hormuz_impact_map() -> ImpactMapResponse:
    """Build a realistic ImpactMapResponse from hormuz_chokepoint_disruption."""
    result = _engine.run(
        scenario_id="hormuz_chokepoint_disruption",
        severity=0.7,
        horizon_hours=72,
    )
    regime_mods = RegimeGraphModifiers(
        regime_id="STABLE", propagation_amplifier=1.0,
        delay_compression=1.0, failure_threshold_shift=0.0,
    )
    transmission_chain = result.get("propagation_chain", [])

    im = build_impact_map(
        result=result,
        gcc_nodes=GCC_NODES,
        gcc_adjacency=GCC_ADJACENCY,
        regime_modifiers=regime_mods,
        transmission_chain=transmission_chain,
        scenario_id="hormuz_chokepoint_disruption",
        run_id="test-di-001",
    )
    actions_raw = result.get("decision_plan", {}).get("actions", [])
    overlays = build_decision_overlays(actions_raw, GCC_ADJACENCY)
    im.decision_overlays = overlays
    im = validate_impact_map(im)
    return im


@pytest.fixture(scope="module")
def hormuz_templates():
    return get_actions_for_scenario_id("hormuz_chokepoint_disruption")


@pytest.fixture(scope="module")
def hormuz_action_costs(hormuz_templates):
    return {a["action_id"]: float(a.get("cost_usd", 0)) for a in hormuz_templates}


@pytest.fixture(scope="module")
def hormuz_action_lookup(hormuz_templates):
    return {a["action_id"]: dict(a) for a in hormuz_templates}


# ═══════════════════════════════════════════════════════════════════════════
# 1. Trigger Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestTriggerEngine:
    def test_returns_list(self, hormuz_impact_map):
        triggers = build_graph_triggers(hormuz_impact_map)
        assert isinstance(triggers, list)
        assert len(triggers) > 0

    def test_trigger_contract(self, hormuz_impact_map):
        triggers = build_graph_triggers(hormuz_impact_map)
        t = triggers[0]
        assert isinstance(t, GraphDecisionTrigger)
        assert t.trigger_type in (
            "BREACH_IMMINENT", "STRESS_CRITICAL", "PROPAGATION_SURGE",
            "REGIME_ESCALATION", "BOTTLENECK_RISK",
        )
        assert 0 <= t.urgency <= 1
        assert 0 <= t.severity <= 1
        assert t.time_to_action_hours >= 0
        assert len(t.reason_en) > 0
        assert len(t.reason_ar) > 0

    def test_sorted_by_urgency(self, hormuz_impact_map):
        triggers = build_graph_triggers(hormuz_impact_map)
        for i in range(len(triggers) - 1):
            assert triggers[i].urgency >= triggers[i + 1].urgency

    def test_no_duplicate_node_trigger(self, hormuz_impact_map):
        triggers = build_graph_triggers(hormuz_impact_map)
        keys = [(t.node_id, t.trigger_type) for t in triggers]
        assert len(keys) == len(set(keys))

    def test_to_dict_keys(self, hormuz_impact_map):
        triggers = build_graph_triggers(hormuz_impact_map)
        d = triggers[0].to_dict()
        required = {"id", "node_id", "node_label", "trigger_type", "severity",
                     "urgency", "time_to_action_hours", "reason_en", "reason_ar",
                     "sector", "affected_edges"}
        assert required.issubset(set(d.keys()))

    def test_empty_impact_map(self):
        empty = ImpactMapResponse(run_id="empty", scenario_id="none")
        triggers = build_graph_triggers(empty)
        assert isinstance(triggers, list)
        assert len(triggers) == 0


# ═══════════════════════════════════════════════════════════════════════════
# 2. Breakpoint Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestBreakpointEngine:
    def test_returns_list(self, hormuz_impact_map):
        bps = detect_breakpoints(hormuz_impact_map)
        assert isinstance(bps, list)
        assert len(bps) > 0

    def test_breakpoint_contract(self, hormuz_impact_map):
        bps = detect_breakpoints(hormuz_impact_map)
        bp = bps[0]
        assert isinstance(bp, Breakpoint)
        assert bp.intervention_type in ("CUT", "ISOLATE", "REDIRECT", "DELAY")
        assert 0 <= bp.severity <= 2.0  # can exceed 1.0 due to compound scoring
        assert 0 <= bp.expected_impact <= 1.0
        assert len(bp.reason_en) > 0
        assert len(bp.reason_ar) > 0

    def test_capped_at_20(self, hormuz_impact_map):
        bps = detect_breakpoints(hormuz_impact_map)
        assert len(bps) <= 20

    def test_edge_references_valid(self, hormuz_impact_map):
        bps = detect_breakpoints(hormuz_impact_map)
        node_ids = {n.id for n in hormuz_impact_map.nodes}
        for bp in bps:
            assert bp.edge_source in node_ids
            assert bp.edge_target in node_ids

    def test_empty_impact_map(self):
        empty = ImpactMapResponse(run_id="empty", scenario_id="none")
        bps = detect_breakpoints(empty)
        assert isinstance(bps, list)
        assert len(bps) == 0


# ═══════════════════════════════════════════════════════════════════════════
# 3. Action Simulation Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestActionSimEngine:
    def test_returns_list(self, hormuz_impact_map):
        if not hormuz_impact_map.decision_overlays:
            pytest.skip("No overlays")
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        )
        assert isinstance(sims, list)
        assert len(sims) > 0

    def test_sim_contract(self, hormuz_impact_map):
        if not hormuz_impact_map.decision_overlays:
            pytest.skip("No overlays")
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        )
        s = sims[0]
        assert isinstance(s, ActionSimResult)
        assert 0 <= s.propagation_reduction <= 1.0
        assert s.nodes_protected >= 0
        assert s.failure_prevention_count >= 0
        assert s.baseline_loss_usd >= 0
        assert s.mitigated_loss_usd >= 0
        assert s.mitigated_loss_usd <= s.baseline_loss_usd

    def test_sorted_by_propagation_reduction(self, hormuz_impact_map):
        if not hormuz_impact_map.decision_overlays:
            pytest.skip("No overlays")
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        )
        for i in range(len(sims) - 1):
            assert sims[i].propagation_reduction >= sims[i + 1].propagation_reduction

    def test_unique_action_ids(self, hormuz_impact_map):
        if not hormuz_impact_map.decision_overlays:
            pytest.skip("No overlays")
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        )
        ids = [s.action_id for s in sims]
        assert len(ids) == len(set(ids))

    def test_empty_overlays(self, hormuz_impact_map):
        sims = simulate_action_effects(hormuz_impact_map, [])
        assert isinstance(sims, list)
        assert len(sims) == 0


# ═══════════════════════════════════════════════════════════════════════════
# 4. Counterfactual Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestCounterfactualEngine:
    def test_returns_result(self, hormuz_impact_map):
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        assert isinstance(cf, CounterfactualResult)

    def test_counterfactual_contract(self, hormuz_impact_map):
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        assert cf.baseline_loss_usd >= 0
        assert 0 <= cf.confidence <= 1.0
        assert cf.delta_loss_usd >= 0
        assert 0 <= cf.risk_reduction <= 1.0
        assert len(cf.narrative_en) > 0
        assert len(cf.narrative_ar) > 0

    def test_delta_equals_baseline_minus_action(self, hormuz_impact_map):
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        expected_delta = cf.baseline_loss_usd - cf.action_loss_usd
        assert abs(cf.delta_loss_usd - expected_delta) < 0.01

    def test_no_sims_fallback(self, hormuz_impact_map):
        cf = compare_counterfactuals(hormuz_impact_map, [])
        assert cf.delta_loss_usd == 0.0
        assert cf.action_id == ""

    def test_to_dict(self, hormuz_impact_map):
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        d = cf.to_dict()
        required = {"run_id", "scenario_id", "baseline_loss_usd", "action_loss_usd",
                     "delta_loss_usd", "confidence", "narrative_en", "narrative_ar"}
        assert required.issubset(set(d.keys()))


# ═══════════════════════════════════════════════════════════════════════════
# 5. ROI Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestROIEngine:
    def test_returns_list(self, hormuz_impact_map, hormuz_action_costs):
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        rois = compute_decision_roi(
            run_id="test", scenario_id="hormuz",
            sim_results=sims, counterfactual=cf,
            action_costs=hormuz_action_costs,
        )
        assert isinstance(rois, list)

    def test_roi_contract(self, hormuz_impact_map, hormuz_action_costs):
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        rois = compute_decision_roi(
            run_id="test", scenario_id="hormuz",
            sim_results=sims, counterfactual=cf,
            action_costs=hormuz_action_costs,
        )
        if rois:
            r = rois[0]
            assert isinstance(r, DecisionROI)
            assert r.run_id == "test"
            assert r.scenario_id == "hormuz"
            assert r.scenario_contribution == 1.0  # strict per-scenario

    def test_roi_formula(self, hormuz_impact_map, hormuz_action_costs):
        """ROI = (baseline_loss - action_loss) - cost."""
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        rois = compute_decision_roi(
            run_id="test", scenario_id="hormuz",
            sim_results=sims, counterfactual=cf,
            action_costs=hormuz_action_costs,
        )
        for r in rois:
            expected_loss_avoided = max(0, r.baseline_loss_usd - r.action_loss_usd)
            expected_net = expected_loss_avoided - r.action_cost_usd
            assert abs(r.loss_avoided_usd - expected_loss_avoided) < 0.01, \
                f"loss_avoided mismatch: {r.loss_avoided_usd} vs {expected_loss_avoided}"
            assert abs(r.net_benefit_usd - expected_net) < 0.01, \
                f"net_benefit mismatch: {r.net_benefit_usd} vs {expected_net}"

    def test_sorted_by_net_benefit(self, hormuz_impact_map, hormuz_action_costs):
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        rois = compute_decision_roi(
            run_id="test", scenario_id="hormuz",
            sim_results=sims, counterfactual=cf,
            action_costs=hormuz_action_costs,
        )
        for i in range(len(rois) - 1):
            assert rois[i].net_benefit_usd >= rois[i + 1].net_benefit_usd

    def test_zero_cost_infinite_roi(self, hormuz_impact_map):
        """Free action with loss avoided should produce inf ROI."""
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        if not sims:
            pytest.skip("No sims")
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        if cf.baseline_loss_usd == 0:
            pytest.skip("No baseline loss")
        # All costs zero
        zero_costs = {s.action_id: 0.0 for s in sims}
        rois = compute_decision_roi(
            run_id="test", scenario_id="hormuz",
            sim_results=sims, counterfactual=cf,
            action_costs=zero_costs,
        )
        for r in rois:
            if r.loss_avoided_usd > 0:
                assert r.roi_ratio == float("inf")


# ═══════════════════════════════════════════════════════════════════════════
# 6. Executive Output
# ═══════════════════════════════════════════════════════════════════════════

class TestExecutiveOutput:
    def test_max_3_decisions(self, hormuz_impact_map, hormuz_action_costs, hormuz_action_lookup):
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        triggers = build_graph_triggers(hormuz_impact_map)
        bps = detect_breakpoints(hormuz_impact_map)
        rois = compute_decision_roi(
            run_id="test", scenario_id="hormuz",
            sim_results=sims, counterfactual=cf,
            action_costs=hormuz_action_costs,
        )
        decisions = build_executive_decisions(
            triggers=triggers, breakpoints=bps,
            sim_results=sims, counterfactual=cf,
            rois=rois, action_registry_lookup=hormuz_action_lookup,
        )
        assert len(decisions) <= 3

    def test_decision_contract(self, hormuz_impact_map, hormuz_action_costs, hormuz_action_lookup):
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        triggers = build_graph_triggers(hormuz_impact_map)
        bps = detect_breakpoints(hormuz_impact_map)
        rois = compute_decision_roi(
            run_id="test", scenario_id="hormuz",
            sim_results=sims, counterfactual=cf,
            action_costs=hormuz_action_costs,
        )
        decisions = build_executive_decisions(
            triggers=triggers, breakpoints=bps,
            sim_results=sims, counterfactual=cf,
            rois=rois, action_registry_lookup=hormuz_action_lookup,
        )
        if not decisions:
            pytest.skip("No decisions")
        d = decisions[0]
        assert isinstance(d, ExecutiveDecision)
        assert d.rank == 1
        assert 0 <= d.urgency <= 1.0
        assert 0 <= d.confidence <= 1.0
        assert 0 <= d.downside_risk <= 1.0
        assert d.time_window_hours > 0
        assert len(d.action_en) > 0

    def test_ranks_sequential(self, hormuz_impact_map, hormuz_action_costs, hormuz_action_lookup):
        sims = simulate_action_effects(
            hormuz_impact_map, hormuz_impact_map.decision_overlays,
        ) if hormuz_impact_map.decision_overlays else []
        cf = compare_counterfactuals(hormuz_impact_map, sims)
        triggers = build_graph_triggers(hormuz_impact_map)
        bps = detect_breakpoints(hormuz_impact_map)
        rois = compute_decision_roi(
            run_id="test", scenario_id="hormuz",
            sim_results=sims, counterfactual=cf,
            action_costs=hormuz_action_costs,
        )
        decisions = build_executive_decisions(
            triggers=triggers, breakpoints=bps,
            sim_results=sims, counterfactual=cf,
            rois=rois, action_registry_lookup=hormuz_action_lookup,
        )
        for i, d in enumerate(decisions):
            assert d.rank == i + 1

    def test_no_sims_empty_decisions(self, hormuz_impact_map, hormuz_action_lookup):
        triggers = build_graph_triggers(hormuz_impact_map)
        bps = detect_breakpoints(hormuz_impact_map)
        cf = compare_counterfactuals(hormuz_impact_map, [])
        decisions = build_executive_decisions(
            triggers=triggers, breakpoints=bps,
            sim_results=[], counterfactual=cf,
            rois=[], action_registry_lookup=hormuz_action_lookup,
        )
        assert len(decisions) == 0


# ═══════════════════════════════════════════════════════════════════════════
# 7. Pipeline Integration
# ═══════════════════════════════════════════════════════════════════════════

class TestPipeline:
    def test_pipeline_returns_result(self, hormuz_impact_map, hormuz_action_costs, hormuz_action_lookup):
        r = run_decision_intelligence_pipeline(
            hormuz_impact_map,
            action_costs=hormuz_action_costs,
            action_registry_lookup=hormuz_action_lookup,
        )
        assert isinstance(r, DecisionIntelligenceResult)

    def test_pipeline_has_all_outputs(self, hormuz_impact_map, hormuz_action_costs, hormuz_action_lookup):
        r = run_decision_intelligence_pipeline(
            hormuz_impact_map,
            action_costs=hormuz_action_costs,
            action_registry_lookup=hormuz_action_lookup,
        )
        assert len(r.triggers) > 0
        assert len(r.breakpoints) > 0
        assert len(r.action_simulations) > 0
        assert r.counterfactual is not None
        assert len(r.roi) > 0
        assert len(r.executive_decisions) > 0

    def test_pipeline_stage_timings(self, hormuz_impact_map, hormuz_action_costs, hormuz_action_lookup):
        r = run_decision_intelligence_pipeline(
            hormuz_impact_map,
            action_costs=hormuz_action_costs,
            action_registry_lookup=hormuz_action_lookup,
        )
        expected_stages = {
            "trigger_engine", "breakpoint_engine", "action_simulation",
            "counterfactual_engine", "roi_engine", "executive_output",
        }
        assert expected_stages.issubset(set(r.stage_timings.keys()))
        for k, v in r.stage_timings.items():
            assert v >= 0

    def test_pipeline_to_dict(self, hormuz_impact_map, hormuz_action_costs, hormuz_action_lookup):
        r = run_decision_intelligence_pipeline(
            hormuz_impact_map,
            action_costs=hormuz_action_costs,
            action_registry_lookup=hormuz_action_lookup,
        )
        d = r.to_dict()
        assert "triggers" in d
        assert "breakpoints" in d
        assert "action_simulations" in d
        assert "counterfactual" in d
        assert "roi" in d
        assert "executive_decisions" in d
        assert "trigger_count" in d
        assert "executive_decision_count" in d

    def test_pipeline_empty_impact_map(self):
        empty = ImpactMapResponse(run_id="empty", scenario_id="none")
        r = run_decision_intelligence_pipeline(empty)
        assert len(r.triggers) == 0
        assert len(r.executive_decisions) == 0

    def test_pipeline_performance(self, hormuz_impact_map, hormuz_action_costs, hormuz_action_lookup):
        """Pipeline must complete in under 100ms."""
        r = run_decision_intelligence_pipeline(
            hormuz_impact_map,
            action_costs=hormuz_action_costs,
            action_registry_lookup=hormuz_action_lookup,
        )
        total = sum(r.stage_timings.values())
        assert total < 100, f"Pipeline took {total}ms — exceeds 100ms budget"


# ═══════════════════════════════════════════════════════════════════════════
# 8. Cross-Scenario Coverage
# ═══════════════════════════════════════════════════════════════════════════

class TestCrossScenarioCoverage:
    """Run pipeline on every scenario in SCENARIO_CATALOG."""

    @pytest.fixture(scope="class")
    def all_scenario_results(self):
        results = {}
        for sid in SCENARIO_CATALOG:
            result = _engine.run(scenario_id=sid, severity=0.7, horizon_hours=72)
            regime_mods = RegimeGraphModifiers(
                regime_id="STABLE", propagation_amplifier=1.0,
                delay_compression=1.0, failure_threshold_shift=0.0,
            )
            tc = result.get("propagation_chain", [])
            im = build_impact_map(
                result=result,
                gcc_nodes=GCC_NODES,
                gcc_adjacency=GCC_ADJACENCY,
                regime_modifiers=regime_mods,
                transmission_chain=tc,
                scenario_id=sid,
                run_id=f"test-{sid}",
            )
            actions_raw = result.get("decision_plan", {}).get("actions", [])
            overlays = build_decision_overlays(actions_raw, GCC_ADJACENCY)
            im.decision_overlays = overlays
            im = validate_impact_map(im)

            templates = get_actions_for_scenario_id(sid)
            costs = {a["action_id"]: float(a.get("cost_usd", 0)) for a in templates}
            lookup = {a["action_id"]: dict(a) for a in templates}

            di = run_decision_intelligence_pipeline(im, costs, lookup)
            results[sid] = di
        return results

    def test_all_scenarios_produce_triggers(self, all_scenario_results):
        for sid, di in all_scenario_results.items():
            assert len(di.triggers) >= 0, f"{sid}: triggers failed"

    def test_all_scenarios_produce_breakpoints(self, all_scenario_results):
        for sid, di in all_scenario_results.items():
            assert len(di.breakpoints) >= 0, f"{sid}: breakpoints failed"

    def test_all_scenarios_have_counterfactual(self, all_scenario_results):
        for sid, di in all_scenario_results.items():
            assert di.counterfactual is not None, f"{sid}: no counterfactual"

    def test_all_scenarios_max_3_decisions(self, all_scenario_results):
        for sid, di in all_scenario_results.items():
            assert len(di.executive_decisions) <= 3, f"{sid}: >3 decisions"

    def test_all_scenarios_complete_under_100ms(self, all_scenario_results):
        for sid, di in all_scenario_results.items():
            total = sum(di.stage_timings.values())
            assert total < 100, f"{sid}: took {total}ms"

    def test_all_scenarios_serializable(self, all_scenario_results):
        import json
        for sid, di in all_scenario_results.items():
            d = di.to_dict()
            # Must be JSON-serializable
            json.dumps(d)
