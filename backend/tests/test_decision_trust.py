"""
Decision Trust Layer — Contract Tests (6 engines + pipeline).

Tests validate:
  - ValidationEngine: structural pass/fail, category errors, rejection reasons
  - ScenarioEnforcementEngine: taxonomy resolution, fallback methods, confidence
  - AuthorityRealismEngine: country-level specificity, escalation chains
  - ExplainabilityEngine: causal paths, narratives, bilingual
  - LearningClosureEngine: adjustment recommendations, learning velocity
  - TrustOverrideEngine: final safety gate, override chain audit trail
  - Pipeline: end-to-end, timing, serialization
  - Cross-scenario: all 20 scenarios

Run: .venv/bin/python -m pytest tests/test_decision_trust.py -v
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

from src.decision_intelligence.pipeline import run_decision_intelligence_pipeline
from src.decision_quality.pipeline import run_decision_quality_pipeline, DecisionQualityResult
from src.decision_calibration.pipeline import run_calibration_pipeline, CalibrationLayerResult
from src.actions.action_registry import get_actions_for_scenario_id

from src.decision_trust.validation_engine import ValidationResult, validate_actions
from src.decision_trust.scenario_enforcement_engine import ScenarioValidation, enforce_scenario_taxonomy
from src.decision_trust.authority_realism_engine import AuthorityProfile, refine_authority_realism
from src.decision_trust.explainability_engine import DecisionExplanation, explain_decisions
from src.decision_trust.learning_closure_engine import LearningUpdate, compute_learning_updates
from src.decision_trust.trust_override_engine import OverrideResult, apply_trust_overrides
from src.decision_trust.pipeline import run_trust_pipeline, TrustLayerResult


# ── Fixtures ───────────────────────────────────────────────────────────────

_engine = SimulationEngine()
_FIXED_TS = datetime(2026, 4, 10, 12, 0, 0, tzinfo=timezone.utc)


def _build_full_context(scenario_id: str) -> tuple[
    DecisionQualityResult, CalibrationLayerResult, ImpactMapResponse, dict, str,
]:
    """Build DQ + calibration + impact_map + lookup for a scenario."""
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
    cal = run_calibration_pipeline(dq, im, scenario_id, lookup)
    return dq, cal, im, lookup, scenario_id


@pytest.fixture(scope="module")
def hormuz_ctx():
    return _build_full_context("hormuz_chokepoint_disruption")


@pytest.fixture(scope="module")
def hormuz_dq(hormuz_ctx):
    return hormuz_ctx[0]


@pytest.fixture(scope="module")
def hormuz_cal(hormuz_ctx):
    return hormuz_ctx[1]


@pytest.fixture(scope="module")
def hormuz_im(hormuz_ctx):
    return hormuz_ctx[2]


@pytest.fixture(scope="module")
def hormuz_lookup(hormuz_ctx):
    return hormuz_ctx[3]


@pytest.fixture(scope="module")
def hormuz_sid(hormuz_ctx):
    return hormuz_ctx[4]


# ═══════════════════════════════════════════════════════════════════════════
# 1. Scenario Enforcement Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestScenarioEnforcementEngine:
    def test_known_scenario_returns_taxonomy(self):
        sv = enforce_scenario_taxonomy("hormuz_chokepoint_disruption")
        assert sv.taxonomy_valid is True
        assert sv.scenario_type == "MARITIME"
        assert sv.fallback_applied is False
        assert sv.classification_confidence == 1.0

    def test_unknown_scenario_uses_fallback(self):
        sv = enforce_scenario_taxonomy("gcc_power_grid_failure")
        assert sv.taxonomy_valid is False
        assert sv.fallback_applied is True
        assert sv.scenario_type in ("CYBER", "ENERGY", "LIQUIDITY", "MARITIME", "REGULATORY")
        assert sv.classification_confidence < 1.0

    def test_completely_unknown_scenario_defaults(self):
        sv = enforce_scenario_taxonomy("totally_unknown_scenario_xyz")
        assert sv.taxonomy_valid is False
        assert sv.fallback_applied is True
        assert sv.scenario_type != ""  # Never empty

    def test_scenario_type_never_empty(self):
        """Every possible input produces a non-empty type."""
        for sid in list(SCENARIO_CATALOG.keys()) + ["fake_scenario"]:
            sv = enforce_scenario_taxonomy(sid)
            assert sv.scenario_type, f"{sid} produced empty type"
            assert sv.scenario_type in ("MARITIME", "ENERGY", "LIQUIDITY", "CYBER", "REGULATORY")

    def test_all_catalog_scenarios_resolved(self):
        for sid in SCENARIO_CATALOG:
            sv = enforce_scenario_taxonomy(sid, SCENARIO_CATALOG.get(sid))
            assert sv.scenario_type != "", f"{sid} not resolved"
            assert sv.classification_confidence > 0.0

    def test_to_dict_keys(self):
        sv = enforce_scenario_taxonomy("hormuz_chokepoint_disruption")
        d = sv.to_dict()
        required = {"scenario_id", "scenario_type", "scenario_type_ar", "taxonomy_valid",
                     "fallback_applied", "fallback_method", "classification_confidence", "enforcement_notes"}
        assert required.issubset(d.keys())


# ═══════════════════════════════════════════════════════════════════════════
# 2. Validation Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestValidationEngine:
    def test_returns_list(self, hormuz_dq, hormuz_im, hormuz_sid, hormuz_lookup):
        results = validate_actions(
            hormuz_dq.executive_decisions, hormuz_im, hormuz_sid, hormuz_lookup,
        )
        assert isinstance(results, list)
        assert len(results) > 0

    def test_validation_status_enum(self, hormuz_dq, hormuz_im, hormuz_sid, hormuz_lookup):
        results = validate_actions(
            hormuz_dq.executive_decisions, hormuz_im, hormuz_sid, hormuz_lookup,
        )
        valid_statuses = {"VALID", "CONDITIONALLY_VALID", "REJECTED"}
        for r in results:
            assert r.validation_status in valid_statuses

    def test_scenario_valid_for_maritime(self, hormuz_dq, hormuz_im, hormuz_sid, hormuz_lookup):
        """Hormuz = MARITIME — maritime actions should be scenario_valid."""
        results = validate_actions(
            hormuz_dq.executive_decisions, hormuz_im, hormuz_sid, hormuz_lookup,
        )
        for r in results:
            if not r.category_error_flag:
                assert r.scenario_valid

    def test_coverage_ratio_bounded(self, hormuz_dq, hormuz_im, hormuz_sid, hormuz_lookup):
        results = validate_actions(
            hormuz_dq.executive_decisions, hormuz_im, hormuz_sid, hormuz_lookup,
        )
        for r in results:
            assert 0.0 <= r.coverage_ratio <= 1.0

    def test_rejection_has_reasons(self, hormuz_dq, hormuz_im, hormuz_sid, hormuz_lookup):
        results = validate_actions(
            hormuz_dq.executive_decisions, hormuz_im, hormuz_sid, hormuz_lookup,
        )
        for r in results:
            if r.validation_status == "REJECTED":
                assert len(r.rejection_reasons) > 0


# ═══════════════════════════════════════════════════════════════════════════
# 3. Authority Realism Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestAuthorityRealismEngine:
    def test_returns_list(self, hormuz_dq, hormuz_cal, hormuz_sid):
        results = refine_authority_realism(
            hormuz_dq.executive_decisions, hormuz_cal.authority_assignments,
            hormuz_sid, "MARITIME",
        )
        assert isinstance(results, list)
        assert len(results) > 0

    def test_country_is_uae_for_hormuz(self, hormuz_dq, hormuz_cal, hormuz_sid):
        results = refine_authority_realism(
            hormuz_dq.executive_decisions, hormuz_cal.authority_assignments,
            hormuz_sid, "MARITIME",
        )
        for r in results:
            assert r.country == "UAE"

    def test_named_institutions(self, hormuz_dq, hormuz_cal, hormuz_sid):
        """Institutions should be named (not generic)."""
        results = refine_authority_realism(
            hormuz_dq.executive_decisions, hormuz_cal.authority_assignments,
            hormuz_sid, "MARITIME",
        )
        for r in results:
            assert r.primary_owner_en != ""
            assert r.regulator_en != ""
            # Should contain actual institution names, not generic
            assert any(word in r.primary_owner_en for word in
                       ("CBUAE", "SAMA", "CBB", "CBK", "CBO", "QCB", "ADNOC", "Aramco",
                        "Port", "DP World", "Mawani", "Cybersecurity", "ADGM", "SCA",
                        "Insurance", "Council", "Ministry"))

    def test_escalation_chain_has_4_levels(self, hormuz_dq, hormuz_cal, hormuz_sid):
        results = refine_authority_realism(
            hormuz_dq.executive_decisions, hormuz_cal.authority_assignments,
            hormuz_sid, "MARITIME",
        )
        for r in results:
            assert len(r.escalation_chain) == 4

    def test_bilingual_authorities(self, hormuz_dq, hormuz_cal, hormuz_sid):
        results = refine_authority_realism(
            hormuz_dq.executive_decisions, hormuz_cal.authority_assignments,
            hormuz_sid, "MARITIME",
        )
        for r in results:
            assert r.primary_owner_ar
            assert r.regulator_ar
            assert r.country_ar


# ═══════════════════════════════════════════════════════════════════════════
# 4. Explainability Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestExplainabilityEngine:
    def test_returns_list(self, hormuz_dq, hormuz_im, hormuz_cal, hormuz_sid, hormuz_lookup):
        sv = enforce_scenario_taxonomy(hormuz_sid)
        val = validate_actions(
            hormuz_dq.executive_decisions, hormuz_im, hormuz_sid, hormuz_lookup,
        )
        results = explain_decisions(
            hormuz_dq.executive_decisions, hormuz_im, val,
            hormuz_cal.ranked_decisions, sv,
        )
        assert isinstance(results, list)
        assert len(results) > 0

    def test_every_decision_has_trigger_reason(self, hormuz_dq, hormuz_im, hormuz_cal, hormuz_sid, hormuz_lookup):
        sv = enforce_scenario_taxonomy(hormuz_sid)
        val = validate_actions(
            hormuz_dq.executive_decisions, hormuz_im, hormuz_sid, hormuz_lookup,
        )
        results = explain_decisions(
            hormuz_dq.executive_decisions, hormuz_im, val,
            hormuz_cal.ranked_decisions, sv,
        )
        for r in results:
            assert r.trigger_reason_en, f"{r.decision_id} missing trigger reason"
            assert r.trigger_reason_ar, f"{r.decision_id} missing trigger reason (AR)"

    def test_every_decision_has_causal_path(self, hormuz_dq, hormuz_im, hormuz_cal, hormuz_sid, hormuz_lookup):
        sv = enforce_scenario_taxonomy(hormuz_sid)
        val = validate_actions(
            hormuz_dq.executive_decisions, hormuz_im, hormuz_sid, hormuz_lookup,
        )
        results = explain_decisions(
            hormuz_dq.executive_decisions, hormuz_im, val,
            hormuz_cal.ranked_decisions, sv,
        )
        for r in results:
            assert len(r.causal_path) >= 2, f"{r.decision_id} causal path too short"

    def test_narrative_is_non_empty(self, hormuz_dq, hormuz_im, hormuz_cal, hormuz_sid, hormuz_lookup):
        sv = enforce_scenario_taxonomy(hormuz_sid)
        val = validate_actions(
            hormuz_dq.executive_decisions, hormuz_im, hormuz_sid, hormuz_lookup,
        )
        results = explain_decisions(
            hormuz_dq.executive_decisions, hormuz_im, val,
            hormuz_cal.ranked_decisions, sv,
        )
        for r in results:
            assert r.narrative_en, f"{r.decision_id} missing narrative"
            assert r.narrative_ar, f"{r.decision_id} missing narrative (AR)"

    def test_regime_context_present(self, hormuz_dq, hormuz_im, hormuz_cal, hormuz_sid, hormuz_lookup):
        sv = enforce_scenario_taxonomy(hormuz_sid)
        val = validate_actions(
            hormuz_dq.executive_decisions, hormuz_im, hormuz_sid, hormuz_lookup,
        )
        results = explain_decisions(
            hormuz_dq.executive_decisions, hormuz_im, val,
            hormuz_cal.ranked_decisions, sv,
        )
        for r in results:
            assert r.regime_context_en
            assert "amplifier" in r.regime_context_en.lower()


# ═══════════════════════════════════════════════════════════════════════════
# 5. Learning Closure Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestLearningClosureEngine:
    def test_returns_list(self, hormuz_dq, hormuz_cal):
        results = compute_learning_updates(
            hormuz_dq.executive_decisions,
            hormuz_cal.calibration_results,
            hormuz_cal.audit_results,
            hormuz_cal.ranked_decisions,
        )
        assert isinstance(results, list)
        assert len(results) > 0

    def test_action_adjustment_enum(self, hormuz_dq, hormuz_cal):
        results = compute_learning_updates(
            hormuz_dq.executive_decisions,
            hormuz_cal.calibration_results,
            hormuz_cal.audit_results,
            hormuz_cal.ranked_decisions,
        )
        valid = {"MAINTAIN", "UPGRADE", "DOWNGRADE", "BLOCK"}
        for r in results:
            assert r.action_adjustment in valid

    def test_learning_velocity_enum(self, hormuz_dq, hormuz_cal):
        results = compute_learning_updates(
            hormuz_dq.executive_decisions,
            hormuz_cal.calibration_results,
            hormuz_cal.audit_results,
            hormuz_cal.ranked_decisions,
        )
        valid = {"FAST", "MODERATE", "SLOW"}
        for r in results:
            assert r.learning_velocity in valid

    def test_adjustments_bounded(self, hormuz_dq, hormuz_cal):
        results = compute_learning_updates(
            hormuz_dq.executive_decisions,
            hormuz_cal.calibration_results,
            hormuz_cal.audit_results,
            hormuz_cal.ranked_decisions,
        )
        for r in results:
            assert -0.20 <= r.ranking_adjustment <= 0.20
            assert -0.30 <= r.confidence_adjustment <= 0.10

    def test_calibration_error_bounded(self, hormuz_dq, hormuz_cal):
        results = compute_learning_updates(
            hormuz_dq.executive_decisions,
            hormuz_cal.calibration_results,
            hormuz_cal.audit_results,
            hormuz_cal.ranked_decisions,
        )
        for r in results:
            assert 0.0 <= r.calibration_error <= 1.0


# ═══════════════════════════════════════════════════════════════════════════
# 6. Trust Override Engine
# ═══════════════════════════════════════════════════════════════════════════

class TestTrustOverrideEngine:
    def test_returns_list(self, hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        trust = run_trust_pipeline(
            hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
            SCENARIO_CATALOG.get(hormuz_sid),
        )
        assert isinstance(trust.override_results, list)
        assert len(trust.override_results) > 0

    def test_final_status_enum(self, hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        trust = run_trust_pipeline(
            hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
            SCENARIO_CATALOG.get(hormuz_sid),
        )
        valid = {"BLOCKED", "HUMAN_REQUIRED", "CONDITIONAL", "AUTO_EXECUTABLE"}
        for o in trust.override_results:
            assert o.final_status in valid

    def test_override_chain_present(self, hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        trust = run_trust_pipeline(
            hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
            SCENARIO_CATALOG.get(hormuz_sid),
        )
        for o in trust.override_results:
            assert len(o.override_chain) >= 1, f"{o.decision_id} missing override chain"

    def test_bilingual_reasons(self, hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        trust = run_trust_pipeline(
            hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
            SCENARIO_CATALOG.get(hormuz_sid),
        )
        for o in trust.override_results:
            assert o.override_reason_en
            assert o.override_reason_ar
            assert o.final_status_ar

    def test_override_rule_present(self, hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        trust = run_trust_pipeline(
            hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
            SCENARIO_CATALOG.get(hormuz_sid),
        )
        for o in trust.override_results:
            assert o.override_rule, f"{o.decision_id} missing override rule"


# ═══════════════════════════════════════════════════════════════════════════
# 7. Pipeline
# ═══════════════════════════════════════════════════════════════════════════

class TestPipeline:
    def test_returns_result(self, hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        trust = run_trust_pipeline(
            hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
            SCENARIO_CATALOG.get(hormuz_sid),
        )
        assert isinstance(trust, TrustLayerResult)

    def test_has_all_outputs(self, hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        trust = run_trust_pipeline(
            hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
            SCENARIO_CATALOG.get(hormuz_sid),
        )
        assert trust.scenario_validation is not None
        assert len(trust.validation_results) > 0
        assert len(trust.authority_profiles) > 0
        assert len(trust.explanations) > 0
        assert len(trust.learning_updates) > 0
        assert len(trust.override_results) > 0

    def test_stage_timings(self, hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        trust = run_trust_pipeline(
            hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
            SCENARIO_CATALOG.get(hormuz_sid),
        )
        expected = {"scenario_enforcement", "validation", "authority_realism",
                     "explainability", "learning_closure", "trust_override"}
        assert expected.issubset(trust.stage_timings.keys())

    def test_to_dict_serializable(self, hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        trust = run_trust_pipeline(
            hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
            SCENARIO_CATALOG.get(hormuz_sid),
        )
        d = trust.to_dict()
        serialized = json.dumps(d)
        assert len(serialized) > 200

    def test_to_dict_counts(self, hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        trust = run_trust_pipeline(
            hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
            SCENARIO_CATALOG.get(hormuz_sid),
        )
        counts = trust.to_dict()["counts"]
        assert counts["validated"] > 0
        assert counts["explanations_generated"] > 0
        assert counts["taxonomy_valid"] is True

    def test_performance(self, hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        trust = run_trust_pipeline(
            hormuz_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
            SCENARIO_CATALOG.get(hormuz_sid),
        )
        assert trust.total_time_ms < 50, f"Pipeline too slow: {trust.total_time_ms:.2f}ms"

    def test_empty_dq_result(self, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup):
        empty_dq = DecisionQualityResult()
        trust = run_trust_pipeline(
            empty_dq, hormuz_cal, hormuz_im, hormuz_sid, hormuz_lookup,
        )
        assert len(trust.override_results) == 0


# ═══════════════════════════════════════════════════════════════════════════
# 8. Cross-Scenario Coverage
# ═══════════════════════════════════════════════════════════════════════════

class TestCrossScenarioCoverage:
    @pytest.fixture(scope="class")
    def all_scenarios(self):
        results = {}
        for sid in SCENARIO_CATALOG:
            try:
                dq, cal, im, lookup, sid_out = _build_full_context(sid)
                trust = run_trust_pipeline(
                    dq, cal, im, sid_out, lookup, SCENARIO_CATALOG.get(sid),
                )
                results[sid] = trust
            except Exception as exc:
                pytest.fail(f"Scenario {sid} failed: {exc}")
        return results

    def test_all_scenarios_produce_results(self, all_scenarios):
        assert len(all_scenarios) == len(SCENARIO_CATALOG)

    def test_all_have_scenario_validation(self, all_scenarios):
        for sid, trust in all_scenarios.items():
            assert trust.scenario_validation is not None
            assert trust.scenario_validation.scenario_type != ""

    def test_all_have_override_results(self, all_scenarios):
        for sid, trust in all_scenarios.items():
            if trust.validation_results:
                assert len(trust.override_results) > 0

    def test_override_statuses_valid(self, all_scenarios):
        valid = {"BLOCKED", "HUMAN_REQUIRED", "CONDITIONAL", "AUTO_EXECUTABLE"}
        for sid, trust in all_scenarios.items():
            for o in trust.override_results:
                assert o.final_status in valid

    def test_performance_under_50ms(self, all_scenarios):
        for sid, trust in all_scenarios.items():
            assert trust.total_time_ms < 50, f"{sid}: {trust.total_time_ms:.2f}ms"

    def test_json_serializable(self, all_scenarios):
        for sid, trust in all_scenarios.items():
            d = trust.to_dict()
            serialized = json.dumps(d)
            assert len(serialized) > 50
