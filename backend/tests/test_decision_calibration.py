"""
Decision Quality Calibration Layer — Contract Tests (5 engines + pipeline).

Tests validate:
  - AuditEngine: scenario match, sector alignment, category error detection
  - RankingEngine: multi-factor scoring, ranking stability, crisis boost
  - AuthorityEngine: GCC-realistic authority assignment, cross-border detection
  - CalibrationEngine: calibration confidence, grades, baselines
  - TrustEngine: trust levels, execution modes, hard constraints
  - Pipeline: end-to-end chaining, timing, serialization
  - Cross-scenario: all 20 scenarios produce valid CalibrationLayerResult

Run: .venv/bin/python -m pytest tests/test_decision_calibration.py -v
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
from src.config import SCENARIO_TAXONOMY

from src.decision_intelligence.pipeline import (
    run_decision_intelligence_pipeline,
    DecisionIntelligenceResult,
)
from src.decision_quality.pipeline import (
    run_decision_quality_pipeline,
    DecisionQualityResult,
)
from src.actions.action_registry import get_actions_for_scenario_id

from src.decision_calibration.audit_engine import ActionAuditResult, audit_decision_quality
from src.decision_calibration.ranking_engine import RankedDecision, rank_decisions
from src.decision_calibration.authority_engine import AuthorityAssignment, assign_authorities
from src.decision_calibration.calibration_engine import CalibrationResult, calibrate_outcomes
from src.decision_calibration.trust_engine import TrustResult, compute_trust_scores
from src.decision_calibration.pipeline import run_calibration_pipeline, CalibrationLayerResult


# ── Fixtures ───────────────────────────────────────────────────────────────

_engine = SimulationEngine()
_FIXED_TS = datetime(2026, 4, 10, 12, 0, 0, tzinfo=timezone.utc)


def _build_full_context(scenario_id: str) -> tuple[
    DecisionQualityResult, ImpactMapResponse, dict, str,
]:
    """Build DQ result + impact_map + lookup for a scenario."""
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
    dq = run_decision_quality_pipeline(di, lookup, _FIXED_TS)
    return dq, im, lookup, scenario_id


@pytest.fixture(scope="module")
def hormuz_ctx():
    return _build_full_context("hormuz_chokepoint_disruption")


@pytest.fixture(scope="module")
def hormuz_dq(hormuz_ctx):
    return hormuz_ctx[0]


@pytest.fixture(scope="module")
def hormuz_im(hormuz_ctx):
    return hormuz_ctx[1]


@pytest.fixture(scope="module")
def hormuz_lookup(hormuz_ctx):
    return hormuz_ctx[2]


@pytest.fixture(scope="module")
def hormuz_scenario_id(hormuz_ctx):
    return hormuz_ctx[3]


# ═══════════════════════════════════════════════════════════════════════════
# 1. Audit Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestAuditEngine:
    def test_returns_list(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        results = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        assert isinstance(results, list)
        assert len(results) > 0

    def test_scores_bounded(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        results = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        for r in results:
            assert 0.0 <= r.scenario_match_score <= 1.0
            assert 0.0 <= r.sector_alignment_score <= 1.0
            assert 0.0 <= r.propagation_relevance_score <= 1.0
            assert 0.0 <= r.regime_consistency_score <= 1.0
            assert 0.0 <= r.action_quality_score <= 1.0

    def test_composite_is_weighted(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        results = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        for r in results:
            if not r.category_error_flag:
                expected = (
                    0.35 * r.scenario_match_score
                    + 0.25 * r.sector_alignment_score
                    + 0.25 * r.propagation_relevance_score
                    + 0.15 * r.regime_consistency_score
                )
                assert abs(r.action_quality_score - expected) < 0.001

    def test_category_error_caps_score(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        results = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        for r in results:
            if r.category_error_flag:
                assert r.action_quality_score <= 0.30

    def test_to_dict_keys(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        results = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        required_keys = {
            "decision_id", "action_id", "scenario_match_score",
            "sector_alignment_score", "propagation_relevance_score",
            "regime_consistency_score", "action_quality_score",
            "category_error_flag", "category_error_reason",
            "category_error_reason_ar", "audit_notes",
        }
        for r in results:
            assert required_keys.issubset(r.to_dict().keys())


# ═══════════════════════════════════════════════════════════════════════════
# 2. Ranking Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestRankingEngine:
    def test_returns_list(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        audit = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        ranked = rank_decisions(
            hormuz_dq.executive_decisions, audit,
            hormuz_im.regime.propagation_amplifier, hormuz_lookup,
        )
        assert isinstance(ranked, list)
        assert len(ranked) > 0

    def test_ranks_sequential(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        audit = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        ranked = rank_decisions(
            hormuz_dq.executive_decisions, audit,
            hormuz_im.regime.propagation_amplifier, hormuz_lookup,
        )
        ranks = [r.calibrated_rank for r in ranked]
        assert ranks == list(range(1, len(ranked) + 1))

    def test_ranking_score_bounded(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        audit = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        ranked = rank_decisions(
            hormuz_dq.executive_decisions, audit,
            hormuz_im.regime.propagation_amplifier, hormuz_lookup,
        )
        for r in ranked:
            assert 0.0 <= r.ranking_score <= 1.0

    def test_has_8_factors(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        audit = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        ranked = rank_decisions(
            hormuz_dq.executive_decisions, audit,
            hormuz_im.regime.propagation_amplifier, hormuz_lookup,
        )
        for r in ranked:
            assert len(r.factors) == 8
            factor_names = {f.factor for f in r.factors}
            expected = {
                "urgency", "impact", "action_quality", "feasibility",
                "roi", "downside_safety", "regulatory_simplicity", "reversibility",
            }
            assert factor_names == expected

    def test_rank_delta_correct(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        audit = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        ranked = rank_decisions(
            hormuz_dq.executive_decisions, audit,
            hormuz_im.regime.propagation_amplifier, hormuz_lookup,
        )
        for r in ranked:
            assert r.rank_delta == r.previous_rank - r.calibrated_rank


# ═══════════════════════════════════════════════════════════════════════════
# 3. Authority Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthorityEngine:
    def test_returns_list(self, hormuz_dq, hormuz_scenario_id):
        scenario_type = SCENARIO_TAXONOMY.get(hormuz_scenario_id, "")
        results = assign_authorities(hormuz_dq.executive_decisions, scenario_type)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_every_decision_has_primary_authority(self, hormuz_dq, hormuz_scenario_id):
        scenario_type = SCENARIO_TAXONOMY.get(hormuz_scenario_id, "")
        results = assign_authorities(hormuz_dq.executive_decisions, scenario_type)
        for r in results:
            assert r.primary_authority_en, f"{r.decision_id} missing primary authority"
            assert r.primary_authority_ar, f"{r.decision_id} missing primary authority (AR)"

    def test_every_decision_has_escalation(self, hormuz_dq, hormuz_scenario_id):
        scenario_type = SCENARIO_TAXONOMY.get(hormuz_scenario_id, "")
        results = assign_authorities(hormuz_dq.executive_decisions, scenario_type)
        for r in results:
            assert r.escalation_target_en, f"{r.decision_id} missing escalation target"

    def test_seniority_enum(self, hormuz_dq, hormuz_scenario_id):
        scenario_type = SCENARIO_TAXONOMY.get(hormuz_scenario_id, "")
        results = assign_authorities(hormuz_dq.executive_decisions, scenario_type)
        valid_seniorities = {"C-Suite", "Department Head", "Board"}
        for r in results:
            assert r.seniority in valid_seniorities, f"Invalid seniority: {r.seniority}"

    def test_maritime_scenario_is_cross_border(self, hormuz_dq, hormuz_scenario_id):
        """MARITIME scenarios should require cross-border coordination."""
        scenario_type = SCENARIO_TAXONOMY.get(hormuz_scenario_id, "")
        assert scenario_type == "MARITIME"
        results = assign_authorities(hormuz_dq.executive_decisions, scenario_type)
        for r in results:
            assert r.requires_cross_border_coordination

    def test_to_dict_keys(self, hormuz_dq, hormuz_scenario_id):
        scenario_type = SCENARIO_TAXONOMY.get(hormuz_scenario_id, "")
        results = assign_authorities(hormuz_dq.executive_decisions, scenario_type)
        required_keys = {
            "decision_id", "action_id", "primary_authority_en",
            "primary_authority_ar", "operational_authority_en",
            "operational_authority_ar", "escalation_target_en",
            "escalation_target_ar", "oversight_body_en",
            "oversight_body_ar", "authority_level_en",
            "authority_level_ar", "seniority", "seniority_ar",
            "requires_cross_border_coordination",
            "coordination_bodies", "authority_notes",
        }
        for r in results:
            assert required_keys.issubset(r.to_dict().keys())


# ═══════════════════════════════════════════════════════════════════════════
# 4. Calibration Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestCalibrationEngine:
    def test_returns_list(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        audit = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        ranked = rank_decisions(
            hormuz_dq.executive_decisions, audit,
            hormuz_im.regime.propagation_amplifier, hormuz_lookup,
        )
        results = calibrate_outcomes(hormuz_dq.executive_decisions, audit, ranked)
        assert isinstance(results, list)
        assert len(results) > 0

    def test_calibration_confidence_bounded(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        audit = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        ranked = rank_decisions(
            hormuz_dq.executive_decisions, audit,
            hormuz_im.regime.propagation_amplifier, hormuz_lookup,
        )
        results = calibrate_outcomes(hormuz_dq.executive_decisions, audit, ranked)
        for r in results:
            assert 0.0 <= r.calibration_confidence <= 1.0
            assert 0.0 <= r.expected_calibration_error <= 1.0

    def test_adjustment_factor_range(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        audit = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        ranked = rank_decisions(
            hormuz_dq.executive_decisions, audit,
            hormuz_im.regime.propagation_amplifier, hormuz_lookup,
        )
        results = calibrate_outcomes(hormuz_dq.executive_decisions, audit, ranked)
        for r in results:
            assert 0.50 <= r.adjustment_factor <= 1.50

    def test_grade_valid(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        audit = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        ranked = rank_decisions(
            hormuz_dq.executive_decisions, audit,
            hormuz_im.regime.propagation_amplifier, hormuz_lookup,
        )
        results = calibrate_outcomes(hormuz_dq.executive_decisions, audit, ranked)
        valid_grades = {"A", "B", "C", "D"}
        for r in results:
            assert r.calibration_grade in valid_grades

    def test_has_baselines(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        audit = audit_decision_quality(
            hormuz_dq.executive_decisions, hormuz_im,
            hormuz_scenario_id, hormuz_lookup,
        )
        ranked = rank_decisions(
            hormuz_dq.executive_decisions, audit,
            hormuz_im.regime.propagation_amplifier, hormuz_lookup,
        )
        results = calibrate_outcomes(hormuz_dq.executive_decisions, audit, ranked)
        for r in results:
            # At minimum, stress_reduction baseline should exist
            assert len(r.baselines) >= 1


# ═══════════════════════════════════════════════════════════════════════════
# 5. Trust Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestTrustEngine:
    def test_returns_list(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        assert isinstance(cal_result.trust_results, list)
        assert len(cal_result.trust_results) > 0

    def test_trust_score_bounded(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        for t in cal_result.trust_results:
            assert 0.0 <= t.trust_score <= 1.0

    def test_trust_level_enum(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        valid_levels = {"LOW", "MEDIUM", "HIGH"}
        for t in cal_result.trust_results:
            assert t.trust_level in valid_levels

    def test_execution_mode_enum(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        valid_modes = {"BLOCKED", "HUMAN_REQUIRED", "CONDITIONAL", "AUTO_EXECUTABLE"}
        for t in cal_result.trust_results:
            assert t.execution_mode in valid_modes

    def test_has_5_dimensions(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        for t in cal_result.trust_results:
            assert len(t.dimensions) == 5
            dim_names = {d.dimension for d in t.dimensions}
            expected = {"action_quality", "ranking", "confidence", "calibration", "data_quality"}
            assert dim_names == expected

    def test_bilingual_labels(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        for t in cal_result.trust_results:
            assert t.trust_level_ar
            assert t.execution_mode_ar
            assert t.execution_rationale_en
            assert t.execution_rationale_ar


# ═══════════════════════════════════════════════════════════════════════════
# 6. Pipeline
# ═══════════════════════════════════════════════════════════════════════════

class TestPipeline:
    def test_returns_result(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        assert isinstance(cal_result, CalibrationLayerResult)

    def test_has_all_outputs(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        assert len(cal_result.audit_results) > 0
        assert len(cal_result.ranked_decisions) > 0
        assert len(cal_result.authority_assignments) > 0
        assert len(cal_result.calibration_results) > 0
        assert len(cal_result.trust_results) > 0

    def test_stage_timings(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        expected_stages = {"audit", "ranking", "authority", "calibration", "trust"}
        assert expected_stages.issubset(cal_result.stage_timings.keys())

    def test_to_dict_serializable(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        d = cal_result.to_dict()
        serialized = json.dumps(d)
        assert len(serialized) > 100

    def test_to_dict_counts(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        counts = cal_result.to_dict()["counts"]
        assert counts["audited"] > 0
        assert counts["ranked"] > 0
        assert counts["authorities_assigned"] > 0
        assert counts["calibrated"] > 0
        assert counts["trust_scored"] > 0

    def test_performance(self, hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        """Stage 70 pipeline should complete in under 50ms."""
        cal_result = run_calibration_pipeline(
            hormuz_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        assert cal_result.total_time_ms < 50, f"Pipeline too slow: {cal_result.total_time_ms:.2f}ms"

    def test_empty_dq_result(self, hormuz_im, hormuz_scenario_id, hormuz_lookup):
        """Empty DQ result → empty CalibrationLayerResult."""
        empty_dq = DecisionQualityResult()
        cal_result = run_calibration_pipeline(
            empty_dq, hormuz_im, hormuz_scenario_id, hormuz_lookup,
        )
        assert len(cal_result.audit_results) == 0
        assert len(cal_result.trust_results) == 0


# ═══════════════════════════════════════════════════════════════════════════
# 7. Cross-Scenario Coverage
# ═══════════════════════════════════════════════════════════════════════════

class TestCrossScenarioCoverage:
    """Validate Stage 70 works across all 20 scenarios."""

    @pytest.fixture(scope="class")
    def all_scenarios(self):
        results = {}
        for sid in SCENARIO_CATALOG:
            try:
                dq, im, lookup, sid_out = _build_full_context(sid)
                cal = run_calibration_pipeline(dq, im, sid_out, lookup)
                results[sid] = cal
            except Exception as exc:
                pytest.fail(f"Scenario {sid} failed: {exc}")
        return results

    def test_all_scenarios_produce_results(self, all_scenarios):
        assert len(all_scenarios) == len(SCENARIO_CATALOG)

    def test_all_have_trust_results(self, all_scenarios):
        for sid, cal in all_scenarios.items():
            # Some scenarios may produce 0 decisions → 0 trust results
            # but if we have decisions, we must have trust results
            if cal.audit_results:
                assert len(cal.trust_results) > 0, f"{sid} missing trust results"

    def test_trust_levels_valid(self, all_scenarios):
        valid = {"LOW", "MEDIUM", "HIGH"}
        for sid, cal in all_scenarios.items():
            for t in cal.trust_results:
                assert t.trust_level in valid, f"{sid}: invalid trust level {t.trust_level}"

    def test_execution_modes_valid(self, all_scenarios):
        valid = {"BLOCKED", "HUMAN_REQUIRED", "CONDITIONAL", "AUTO_EXECUTABLE"}
        for sid, cal in all_scenarios.items():
            for t in cal.trust_results:
                assert t.execution_mode in valid, f"{sid}: invalid mode {t.execution_mode}"

    def test_performance_under_50ms(self, all_scenarios):
        for sid, cal in all_scenarios.items():
            assert cal.total_time_ms < 50, f"{sid}: too slow at {cal.total_time_ms:.2f}ms"

    def test_json_serializable(self, all_scenarios):
        for sid, cal in all_scenarios.items():
            d = cal.to_dict()
            serialized = json.dumps(d)
            assert len(serialized) > 50, f"{sid}: serialization too small"
