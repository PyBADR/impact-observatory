"""
Decision Quality Layer — Contract Tests (7 engines + pipeline).

Tests validate:
  - Each engine's data contract (types, bounds, required fields)
  - Cross-engine integration via pipeline
  - Cross-scenario coverage (all 20 scenarios)
  - Validity gates (missing owner, missing deadline, etc.)
  - Multi-dimensional confidence (NOT a single number)

Run: .venv/bin/python -m pytest tests/test_decision_quality.py -v
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pytest

from src.simulation_engine import SimulationEngine, GCC_NODES, GCC_ADJACENCY, SCENARIO_CATALOG
from src.engines.impact_map_engine import build_impact_map
from src.engines.decision_overlay_engine import build_decision_overlays
from src.engines.impact_map_validator import validate_impact_map
from src.schemas.impact_map import ImpactMapResponse
from src.regime.regime_graph_adapter import RegimeGraphModifiers

from src.decision_intelligence.pipeline import (
    run_decision_intelligence_pipeline,
    DecisionIntelligenceResult,
)
from src.actions.action_registry import get_actions_for_scenario_id

from src.decision_quality.anchoring_engine import AnchoredDecision, anchor_decisions
from src.decision_quality.pathway_engine import ActionPathway, build_action_pathways
from src.decision_quality.gate_engine import DecisionGate, apply_decision_gates
from src.decision_quality.confidence_engine import DecisionConfidence, compute_decision_confidence
from src.decision_quality.formatter_engine import FormattedExecutiveDecision, format_executive_decisions
from src.decision_quality.outcome_engine import DecisionOutcome, build_outcome_expectations
from src.decision_quality.pipeline import run_decision_quality_pipeline, DecisionQualityResult


# ── Fixtures ───────────────────────────────────────────────────────────────

_engine = SimulationEngine()
_FIXED_TS = datetime(2026, 4, 10, 12, 0, 0, tzinfo=timezone.utc)


def _build_di_result(scenario_id: str) -> tuple[DecisionIntelligenceResult, dict]:
    """Build a full DI result for a given scenario."""
    result = _engine.run(scenario_id=scenario_id, severity=0.7, horizon_hours=72)
    regime_mods = RegimeGraphModifiers(
        regime_id="STABLE", propagation_amplifier=1.0,
        delay_compression=1.0, failure_threshold_shift=0.0,
    )
    tc = result.get("propagation_chain", [])
    im = build_impact_map(
        result=result, gcc_nodes=GCC_NODES, gcc_adjacency=GCC_ADJACENCY,
        regime_modifiers=regime_mods, transmission_chain=tc,
        scenario_id=scenario_id, run_id=f"test-{scenario_id}",
    )
    actions_raw = result.get("decision_plan", {}).get("actions", [])
    overlays = build_decision_overlays(actions_raw, GCC_ADJACENCY)
    im.decision_overlays = overlays
    im = validate_impact_map(im)

    templates = get_actions_for_scenario_id(scenario_id)
    costs = {a["action_id"]: float(a.get("cost_usd", 0)) for a in templates}
    lookup = {a["action_id"]: dict(a) for a in templates}

    di = run_decision_intelligence_pipeline(im, costs, lookup)
    return di, lookup


@pytest.fixture(scope="module")
def hormuz_di():
    return _build_di_result("hormuz_chokepoint_disruption")


@pytest.fixture(scope="module")
def hormuz_di_result(hormuz_di):
    return hormuz_di[0]


@pytest.fixture(scope="module")
def hormuz_lookup(hormuz_di):
    return hormuz_di[1]


# ═══════════════════════════════════════════════════════════════════════════
# 1. Anchoring Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestAnchoringEngine:
    def test_returns_list(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        assert isinstance(anchored, list)
        assert len(anchored) > 0

    def test_every_decision_has_owner(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        for a in anchored:
            if a.is_valid:
                assert a.decision_owner, f"{a.decision_id} missing owner"

    def test_every_decision_has_deadline(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        for a in anchored:
            if a.is_valid:
                assert a.decision_deadline, f"{a.decision_id} missing deadline"
                # Must be valid ISO 8601
                datetime.fromisoformat(a.decision_deadline)

    def test_decision_type_enum(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        for a in anchored:
            assert a.decision_type in ("operational", "strategic", "emergency")

    def test_tradeoffs_present(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        # At least one decision should have tradeoffs (hormuz has high-cost actions)
        has_tradeoffs = any(len(a.tradeoffs) > 0 for a in anchored)
        assert has_tradeoffs, "Expected at least one decision with tradeoffs"

    def test_deadline_after_created(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        for a in anchored:
            created = datetime.fromisoformat(a.created_at)
            deadline = datetime.fromisoformat(a.decision_deadline)
            assert deadline > created, f"{a.decision_id}: deadline before creation"

    def test_to_dict_keys(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        d = anchored[0].to_dict()
        required = {
            "decision_id", "decision_owner", "decision_deadline",
            "decision_type", "action_id", "urgency", "impact",
            "is_valid", "tradeoffs",
        }
        assert required.issubset(set(d.keys()))

    def test_empty_input(self):
        anchored = anchor_decisions([], {}, _FIXED_TS)
        assert anchored == []


# ═══════════════════════════════════════════════════════════════════════════
# 2. Pathway Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestPathwayEngine:
    def test_returns_list(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        pathways = build_action_pathways(
            anchored, hormuz_lookup,
            hormuz_di_result.triggers, hormuz_di_result.breakpoints,
        )
        assert isinstance(pathways, list)
        assert len(pathways) > 0

    def test_pathway_type_enum(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        pathways = build_action_pathways(
            anchored, hormuz_lookup,
            hormuz_di_result.triggers, hormuz_di_result.breakpoints,
        )
        for p in pathways:
            assert p.pathway_type in ("IMMEDIATE", "CONDITIONAL", "STRATEGIC")

    def test_actions_have_required_fields(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        pathways = build_action_pathways(
            anchored, hormuz_lookup,
            hormuz_di_result.triggers, hormuz_di_result.breakpoints,
        )
        for p in pathways:
            for a in p.actions:
                assert a.action_id
                assert a.priority_level >= 1
                assert a.trigger_condition
                assert 0 <= a.expected_impact <= 1.0
                assert a.reversibility in ("reversible", "partially_reversible", "irreversible")

    def test_total_cost_sums_correctly(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        pathways = build_action_pathways(
            anchored, hormuz_lookup,
            hormuz_di_result.triggers, hormuz_di_result.breakpoints,
        )
        for p in pathways:
            expected = sum(a.cost_estimate_usd for a in p.actions)
            assert abs(p.total_cost_usd - expected) < 0.01


# ═══════════════════════════════════════════════════════════════════════════
# 3. Gate Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestGateEngine:
    def test_returns_list(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        gates = apply_decision_gates(anchored, hormuz_di_result.triggers)
        assert isinstance(gates, list)
        assert len(gates) > 0

    def test_gate_status_enum(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        gates = apply_decision_gates(anchored, hormuz_di_result.triggers)
        for g in gates:
            assert g.current_status in (
                "DRAFT", "PENDING_APPROVAL", "APPROVED",
                "EXECUTED", "REJECTED", "OBSERVATION",
            )

    def test_emergency_requires_approval(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        gates = apply_decision_gates(anchored, hormuz_di_result.triggers)
        for a, g in zip(anchored, gates):
            if a.decision_type == "emergency":
                assert g.approval_required, f"{g.decision_id}: emergency should require approval"
                assert g.current_status == "PENDING_APPROVAL"

    def test_escalation_target_present(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        gates = apply_decision_gates(anchored, hormuz_di_result.triggers)
        for g in gates:
            assert g.escalation_target_en
            assert g.escalation_target_ar

    def test_to_dict_keys(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        gates = apply_decision_gates(anchored, hormuz_di_result.triggers)
        d = gates[0].to_dict()
        required = {
            "decision_id", "current_status", "approval_required",
            "decision_owner", "escalation_threshold",
            "auto_escalation_trigger", "gate_reason_en",
        }
        assert required.issubset(set(d.keys()))


# ═══════════════════════════════════════════════════════════════════════════
# 4. Confidence Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestConfidenceEngine:
    def test_returns_list(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        confs = compute_decision_confidence(
            anchored, hormuz_di_result.counterfactual, hormuz_di_result.action_simulations,
        )
        assert isinstance(confs, list)
        assert len(confs) > 0

    def test_confidence_is_multi_dimensional(self, hormuz_di_result, hormuz_lookup):
        """Confidence MUST NOT be a single number — it must have dimensions."""
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        confs = compute_decision_confidence(
            anchored, hormuz_di_result.counterfactual, hormuz_di_result.action_simulations,
        )
        for c in confs:
            assert len(c.dimensions) == 4, f"{c.decision_id}: expected 4 dimensions, got {len(c.dimensions)}"
            dim_names = {d.dimension for d in c.dimensions}
            assert dim_names == {
                "data_quality", "model_reliability",
                "action_feasibility", "causal_strength",
            }

    def test_dimension_bounds(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        confs = compute_decision_confidence(
            anchored, hormuz_di_result.counterfactual, hormuz_di_result.action_simulations,
        )
        for c in confs:
            assert 0 <= c.composite_score <= 1.0
            for d in c.dimensions:
                assert 0 <= d.score <= 1.0, f"{c.decision_id}.{d.dimension}: score {d.score} out of bounds"

    def test_model_dependency_classification(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        confs = compute_decision_confidence(
            anchored, hormuz_di_result.counterfactual, hormuz_di_result.action_simulations,
        )
        for c in confs:
            assert c.model_dependency in ("low", "moderate", "high")

    def test_has_bilingual_labels(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        confs = compute_decision_confidence(
            anchored, hormuz_di_result.counterfactual, hormuz_di_result.action_simulations,
        )
        for c in confs:
            for d in c.dimensions:
                assert d.label_en
                assert d.label_ar


# ═══════════════════════════════════════════════════════════════════════════
# 5. Outcome Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestOutcomeEngine:
    def test_returns_list(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        outcomes = build_outcome_expectations(
            anchored, hormuz_di_result.action_simulations, hormuz_di_result.counterfactual,
        )
        assert isinstance(outcomes, list)
        assert len(outcomes) > 0

    def test_has_measurable_kpi(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        outcomes = build_outcome_expectations(
            anchored, hormuz_di_result.action_simulations, hormuz_di_result.counterfactual,
        )
        for o in outcomes:
            assert o.measurable_kpi_en, f"{o.decision_id}: missing KPI"
            assert o.measurable_kpi_ar, f"{o.decision_id}: missing Arabic KPI"

    def test_has_expected_outcomes(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        outcomes = build_outcome_expectations(
            anchored, hormuz_di_result.action_simulations, hormuz_di_result.counterfactual,
        )
        for o in outcomes:
            assert len(o.expected_outcomes) >= 1, f"{o.decision_id}: no expected outcomes"

    def test_has_learning_signals(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        outcomes = build_outcome_expectations(
            anchored, hormuz_di_result.action_simulations, hormuz_di_result.counterfactual,
        )
        for o in outcomes:
            assert len(o.learning_signals) >= 1, f"{o.decision_id}: no learning signals"
            for ls in o.learning_signals:
                assert ls.signal_type in ("CALIBRATION", "MODEL_UPDATE", "THRESHOLD_ADJUSTMENT")
                assert ls.target_component

    def test_review_deadline_is_iso(self, hormuz_di_result, hormuz_lookup):
        anchored = anchor_decisions(
            hormuz_di_result.executive_decisions, hormuz_lookup, _FIXED_TS,
        )
        outcomes = build_outcome_expectations(
            anchored, hormuz_di_result.action_simulations, hormuz_di_result.counterfactual,
        )
        for o in outcomes:
            if o.review_deadline:
                datetime.fromisoformat(o.review_deadline)  # must not raise


# ═══════════════════════════════════════════════════════════════════════════
# 6. Formatter Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestFormatterEngine:
    def test_max_3_decisions(self, hormuz_di_result, hormuz_lookup):
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        assert len(dq.executive_decisions) <= 3

    def test_ranks_sequential(self, hormuz_di_result, hormuz_lookup):
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        for i, d in enumerate(dq.executive_decisions):
            assert d.rank == i + 1

    def test_enriched_with_gate(self, hormuz_di_result, hormuz_lookup):
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        for d in dq.executive_decisions:
            assert d.gate_status in (
                "DRAFT", "PENDING_APPROVAL", "APPROVED",
                "EXECUTED", "REJECTED", "OBSERVATION",
            )

    def test_enriched_with_confidence(self, hormuz_di_result, hormuz_lookup):
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        for d in dq.executive_decisions:
            assert 0 <= d.confidence_composite <= 1.0
            assert len(d.confidence_dimensions) == 4

    def test_enriched_with_pathway(self, hormuz_di_result, hormuz_lookup):
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        for d in dq.executive_decisions:
            assert d.pathway_type in ("IMMEDIATE", "CONDITIONAL", "STRATEGIC")

    def test_enriched_with_outcome(self, hormuz_di_result, hormuz_lookup):
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        for d in dq.executive_decisions:
            assert d.measurable_kpi


# ═══════════════════════════════════════════════════════════════════════════
# 7. Pipeline Integration
# ═══════════════════════════════════════════════════════════════════════════

class TestPipeline:
    def test_returns_result(self, hormuz_di_result, hormuz_lookup):
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        assert isinstance(dq, DecisionQualityResult)

    def test_has_all_outputs(self, hormuz_di_result, hormuz_lookup):
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        assert len(dq.anchored_decisions) > 0
        assert len(dq.action_pathways) > 0
        assert len(dq.decision_gates) > 0
        assert len(dq.confidences) > 0
        assert len(dq.outcomes) > 0
        assert len(dq.executive_decisions) > 0

    def test_stage_timings(self, hormuz_di_result, hormuz_lookup):
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        expected_stages = {
            "anchoring_engine", "pathway_engine", "gate_engine",
            "confidence_engine", "outcome_engine", "formatter_engine",
        }
        assert expected_stages.issubset(set(dq.stage_timings.keys()))

    def test_to_dict_serializable(self, hormuz_di_result, hormuz_lookup):
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        d = dq.to_dict()
        json.dumps(d)  # must not raise

    def test_to_dict_counts(self, hormuz_di_result, hormuz_lookup):
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        d = dq.to_dict()
        assert "anchored_count" in d
        assert "valid_count" in d
        assert "pathway_count" in d
        assert "gate_count" in d
        assert "executive_decision_count" in d

    def test_performance(self, hormuz_di_result, hormuz_lookup):
        """Pipeline must complete in under 50ms."""
        dq = run_decision_quality_pipeline(hormuz_di_result, hormuz_lookup, _FIXED_TS)
        total = sum(dq.stage_timings.values())
        assert total < 50, f"Pipeline took {total}ms — exceeds 50ms budget"

    def test_empty_di_result(self):
        empty_di = DecisionIntelligenceResult()
        dq = run_decision_quality_pipeline(empty_di, {}, _FIXED_TS)
        assert len(dq.executive_decisions) == 0


# ═══════════════════════════════════════════════════════════════════════════
# 8. Cross-Scenario Coverage
# ═══════════════════════════════════════════════════════════════════════════

class TestCrossScenarioCoverage:
    @pytest.fixture(scope="class")
    def all_scenario_dq_results(self):
        results = {}
        for sid in SCENARIO_CATALOG:
            di, lookup = _build_di_result(sid)
            dq = run_decision_quality_pipeline(di, lookup, _FIXED_TS)
            results[sid] = dq
        return results

    def test_all_scenarios_produce_anchored(self, all_scenario_dq_results):
        for sid, dq in all_scenario_dq_results.items():
            # At least some anchored decisions (could be 0 if no exec decisions from Stage 50)
            assert isinstance(dq.anchored_decisions, list), f"{sid}: anchored failed"

    def test_all_scenarios_max_3_decisions(self, all_scenario_dq_results):
        for sid, dq in all_scenario_dq_results.items():
            assert len(dq.executive_decisions) <= 3, f"{sid}: >3 decisions"

    def test_all_scenarios_all_valid_have_owner(self, all_scenario_dq_results):
        for sid, dq in all_scenario_dq_results.items():
            for a in dq.anchored_decisions:
                if a.is_valid:
                    assert a.decision_owner, f"{sid}/{a.decision_id}: missing owner"

    def test_all_scenarios_confidence_is_multi_dim(self, all_scenario_dq_results):
        for sid, dq in all_scenario_dq_results.items():
            for c in dq.confidences:
                assert len(c.dimensions) == 4, f"{sid}/{c.decision_id}: confidence not multi-dimensional"

    def test_all_scenarios_complete_under_50ms(self, all_scenario_dq_results):
        for sid, dq in all_scenario_dq_results.items():
            total = sum(dq.stage_timings.values())
            assert total < 50, f"{sid}: took {total}ms"

    def test_all_scenarios_serializable(self, all_scenario_dq_results):
        for sid, dq in all_scenario_dq_results.items():
            d = dq.to_dict()
            json.dumps(d)
