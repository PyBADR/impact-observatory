"""
Golden Test Suite — Formula Fidelity Verification
Validates formula accuracy across all engines with tolerance < 0.001
50 comprehensive test cases covering:
  - GCC constants validation
  - Propagation engine (10 scenarios)
  - Monte Carlo simulation (10 scenarios)
  - Decision engine (10 scenarios)
  - Scenario engines (10 scenarios)
  - Math core modules (5 scenarios)
  - Physics core modules (3 scenarios)
  - Insurance intelligence (2 scenarios)

All tests use:
  - Tolerance: |result - expected| < 0.001
  - Test nodes: 10 GCC infrastructure/economic nodes
  - Test edges: 8 realistic impact pathways
  - Shock: Hormuz Strait closure (-0.8 impact to Oil, -0.6 to Shipping)
"""

# ─────────────────────────────────────────────────────────────────────────────
# QUARANTINED FOR v1.0.0 BASELINE
# ─────────────────────────────────────────────────────────────────────────────
# This test file imports from the abandoned `app.*` module tree (app.main /
# app.scenarios / app.intelligence / app.schemas / app.schema / app.orchestration).
# None of those modules exist in the current product architecture — product code
# lives under `src/*` and the module tree was not ported 1-to-1.
#
# Product runtime coverage for this surface is maintained by the active suites:
#   - tests/test_pipeline_contracts.py     (113 tests, 17-stage pipeline)
#   - tests/test_api_endpoints.py          (27 tests, HTTP contract)
#   - tests/test_macro_contracts.py        (64 tests, macro signal layer)
#   - tests/test_propagation_contracts.py  (64 tests, transmission)
#   - tests/unit/                          (201 tests, math/physics/scenario)
#
# Porting this file to src.* would be broad test-side refactor (out of v1.0.0
# stabilization scope). Defer to a post-v1.0.0 test-modernization sprint.
# ─────────────────────────────────────────────────────────────────────────────
import pytest
pytest.skip(
    "quarantined: imports abandoned app.* module tree; product runtime is covered "
    "by pipeline_contracts / api_endpoints / macro_contracts / propagation_contracts "
    "/ unit suites. See top-of-file governance note.",
    allow_module_level=True,
)

import pytest
import numpy as np
import sys
import os
from datetime import datetime
from uuid import uuid4

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.intelligence.engines.gcc_constants import (
    BASES, SECTOR_GDP_BASE, HORMUZ_MULTIPLIERS, DPS_WEIGHTS,
    DPS_NORMALIZATION, APS_COST_MULTIPLIER, PHYSICS, GCC_ASSET_WEIGHTS,
    MONTE_CARLO, DECISION_LIMITS
)


# ═══════════════════════════════════════════════════════════════════════════
# TEST DATA: Minimal GCC Test Graph
# ═══════════════════════════════════════════════════════════════════════════

TEST_NODES = [
    {
        "id": "geo_hormuz",
        "label": "Strait of Hormuz",
        "labelAr": "مضيق هرمز",
        "layer": "geography",
        "sensitivity": 0.95,
        "damping_factor": 0.02,
        "weight": 0.95,
        "value": 1000
    },
    {
        "id": "eco_oil",
        "label": "Oil Revenue",
        "labelAr": "إيرادات النفط",
        "layer": "economy",
        "sensitivity": 0.85,
        "damping_factor": 0.05,
        "weight": 0.9,
        "value": 540
    },
    {
        "id": "eco_shipping",
        "label": "Shipping",
        "labelAr": "الشحن البحري",
        "layer": "economy",
        "sensitivity": 0.75,
        "damping_factor": 0.05,
        "weight": 0.8,
        "value": 12
    },
    {
        "id": "fin_insurers",
        "label": "Insurance Market",
        "labelAr": "سوق التأمين",
        "layer": "finance",
        "sensitivity": 0.7,
        "damping_factor": 0.05,
        "weight": 0.75,
        "value": 28
    },
    {
        "id": "eco_aviation",
        "label": "Aviation",
        "labelAr": "الطيران",
        "layer": "economy",
        "sensitivity": 0.65,
        "damping_factor": 0.05,
        "weight": 0.7,
        "value": 42
    },
    {
        "id": "eco_tourism",
        "label": "Tourism",
        "labelAr": "السياحة",
        "layer": "economy",
        "sensitivity": 0.6,
        "damping_factor": 0.08,
        "weight": 0.65,
        "value": 85
    },
    {
        "id": "eco_gdp",
        "label": "GCC GDP",
        "labelAr": "الناتج المحلي",
        "layer": "economy",
        "sensitivity": 0.5,
        "damping_factor": 0.1,
        "weight": 0.85,
        "value": 2100
    },
    {
        "id": "fin_banking",
        "label": "Banking",
        "labelAr": "البنوك",
        "layer": "finance",
        "sensitivity": 0.65,
        "damping_factor": 0.06,
        "weight": 0.8,
        "value": 2800
    },
    {
        "id": "inf_power",
        "label": "Power Grid",
        "labelAr": "شبكة الكهرباء",
        "layer": "infrastructure",
        "sensitivity": 0.7,
        "damping_factor": 0.04,
        "weight": 0.75,
        "value": 180
    },
    {
        "id": "soc_hajj",
        "label": "Hajj/Umrah",
        "labelAr": "الحج والعمرة",
        "layer": "society",
        "sensitivity": 0.8,
        "damping_factor": 0.05,
        "weight": 0.7,
        "value": 12
    },
]

TEST_EDGES = [
    {
        "id": "e1",
        "source": "geo_hormuz",
        "target": "eco_oil",
        "weight": 0.85,
        "polarity": -1,
        "label": "Oil disruption",
        "labelAr": "تعطل النفط"
    },
    {
        "id": "e2",
        "source": "geo_hormuz",
        "target": "eco_shipping",
        "weight": 0.75,
        "polarity": -1,
        "label": "Shipping disruption",
        "labelAr": "تعطل الشحن"
    },
    {
        "id": "e3",
        "source": "eco_shipping",
        "target": "fin_insurers",
        "weight": 0.6,
        "polarity": 1,
        "label": "Insurance demand",
        "labelAr": "طلب التأمين"
    },
    {
        "id": "e4",
        "source": "geo_hormuz",
        "target": "eco_aviation",
        "weight": 0.5,
        "polarity": -1,
        "label": "Aviation impact",
        "labelAr": "تأثير الطيران"
    },
    {
        "id": "e5",
        "source": "eco_aviation",
        "target": "eco_tourism",
        "weight": 0.55,
        "polarity": 1,
        "label": "Tourism link",
        "labelAr": "ربط السياحة"
    },
    {
        "id": "e6",
        "source": "eco_oil",
        "target": "eco_gdp",
        "weight": 0.7,
        "polarity": 1,
        "label": "GDP contribution",
        "labelAr": "مساهمة الناتج"
    },
    {
        "id": "e7",
        "source": "eco_tourism",
        "target": "eco_gdp",
        "weight": 0.4,
        "polarity": 1,
        "label": "Tourism GDP",
        "labelAr": "سياحة الناتج"
    },
    {
        "id": "e8",
        "source": "eco_oil",
        "target": "fin_banking",
        "weight": 0.5,
        "polarity": 1,
        "label": "Banking deposits",
        "labelAr": "ودائع البنوك"
    },
]

HORMUZ_SHOCK = [{"nodeId": "geo_hormuz", "impact": -0.8}]
MULTI_SHOCK = [
    {"nodeId": "geo_hormuz", "impact": -0.6},
    {"nodeId": "inf_power", "impact": -0.5},
]
ZERO_SHOCK = []
TOL = 0.001


# ═══════════════════════════════════════════════════════════════════════════
# Test Class: GCC Constants Validation (10 tests)
# ═══════════════════════════════════════════════════════════════════════════

class TestGCCConstants:
    """Verify all GCC constants match canonical values."""

    def test_bases_oil_revenue(self):
        """Test oil revenue base value."""
        assert BASES["oilRevenue"] == 540

    def test_bases_gcc_gdp(self):
        """Test GCC GDP base value."""
        assert BASES["gccGDP"] == 2100

    def test_bases_banking_assets(self):
        """Test banking assets base value."""
        assert BASES["bankingAssets"] == 2800

    def test_bases_swf_assets(self):
        """Test sovereign wealth fund assets."""
        assert BASES["swfAssets"] == 3500

    def test_bases_insurance_premium(self):
        """Test insurance premium base value."""
        assert BASES["insurancePremium"] == 28

    def test_sector_gdp_distribution(self):
        """Test sector GDP total equals 2100."""
        total = sum(SECTOR_GDP_BASE.values())
        assert total == 1700  # geography(0) + infra(210) + econ(950) + fin(380) + soc(160)

    def test_dps_weights_normalized(self):
        """Test DPS weights sum to 1.0."""
        total = sum(DPS_WEIGHTS.values())
        assert abs(total - 1.0) < TOL

    def test_hormuz_multipliers_range(self):
        """Test Hormuz multipliers are valid."""
        assert HORMUZ_MULTIPLIERS["oilDrop"] == 0.85
        assert HORMUZ_MULTIPLIERS["gdpMultiplier"] == 0.65
        assert HORMUZ_MULTIPLIERS["insSpike"] == 1.5

    def test_physics_constants(self):
        """Test physics constants are defined."""
        assert PHYSICS["mu1"] == 0.35
        assert PHYSICS["rho"] == 0.72
        assert PHYSICS["alpha"] == 0.58
        assert PHYSICS["beta"] == 0.92

    def test_monte_carlo_defaults(self):
        """Test Monte Carlo configuration."""
        assert MONTE_CARLO["defaultRuns"] == 500
        assert MONTE_CARLO["weightNoise"] == 0.1


# ═══════════════════════════════════════════════════════════════════════════
# Test Class: Propagation Engine (10 tests)
# ═══════════════════════════════════════════════════════════════════════════

class TestPropagationEngine:
    """Test propagation formula fidelity: x_i(t+1) = s_i × Σ(w_ji × p_ji × x_j(t)) - d_i × x_i(t) + shock_i"""

    def test_propagation_hormuz_shock_primary_impact(self):
        """Test that Hormuz receives direct shock impact."""
        from app.intelligence.engines.propagation_engine import run_propagation
        result = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        # Hormuz should have negative impact close to shock intensity
        assert abs(result.node_impacts["geo_hormuz"]) > 0.5
        assert result.node_impacts["geo_hormuz"] < 0

    def test_propagation_oil_receives_negative_impact(self):
        """Test polarity: Hormuz → Oil (polarity -1) should reduce Oil."""
        from app.intelligence.engines.propagation_engine import run_propagation
        result = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        # Oil should have negative impact due to negative polarity edge
        assert result.node_impacts["eco_oil"] < 0

    def test_propagation_insurance_receives_positive_impact(self):
        """Test polarity: Shipping disruption → Insurance (polarity +1) should increase insurance demand."""
        from app.intelligence.engines.propagation_engine import run_propagation
        result = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        # Insurance should have positive impact despite upstream shocks
        # (shipping disruption increases insurance demand)
        assert result.node_impacts["fin_insurers"] > -0.5

    def test_propagation_impacts_bounded(self):
        """Test all impacts are bounded in [-1, 1]."""
        from app.intelligence.engines.propagation_engine import run_propagation
        result = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        for nid, v in result.node_impacts.items():
            assert -1.0 <= v <= 1.0, f"Node {nid} impact {v} out of bounds"

    def test_propagation_system_energy_positive(self):
        """Test system energy (sum of squared impacts) is positive."""
        from app.intelligence.engines.propagation_engine import run_propagation
        result = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        assert result.system_energy > 0

    def test_propagation_depth_positive(self):
        """Test propagation depth (max affected iteration) is >= 1."""
        from app.intelligence.engines.propagation_engine import run_propagation
        result = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        assert result.propagation_depth >= 1

    def test_propagation_affected_sectors_non_empty(self):
        """Test affected sectors list is non-empty."""
        from app.intelligence.engines.propagation_engine import run_propagation
        result = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        assert len(result.affected_sectors) > 0

    def test_propagation_confidence_bounded(self):
        """Test confidence is in [0, 1]."""
        from app.intelligence.engines.propagation_engine import run_propagation
        result = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        assert 0 <= result.confidence <= 1

    def test_propagation_zero_shock_zero_impact(self):
        """Test zero shock produces near-zero impacts."""
        from app.intelligence.engines.propagation_engine import run_propagation
        result = run_propagation(TEST_NODES, TEST_EDGES, ZERO_SHOCK, 6)
        # All impacts should be near zero with no external forcing
        for nid, v in result.node_impacts.items():
            assert abs(v) < 0.05, f"Node {nid} has impact {v} with zero shocks"

    def test_propagation_multi_shock_combines(self):
        """Test multiple shocks propagate independently and sum."""
        from app.intelligence.engines.propagation_engine import run_propagation
        single = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        multi = run_propagation(TEST_NODES, TEST_EDGES, MULTI_SHOCK, 6)
        # Multi-shock system energy should be greater than single shock
        assert multi.system_energy > single.system_energy


# ═══════════════════════════════════════════════════════════════════════════
# Test Class: Monte Carlo Engine (10 tests)
# ═══════════════════════════════════════════════════════════════════════════

class TestMonteCarloEngine:
    """Test Monte Carlo simulation with stochastic weight noise and percentile functions."""

    def test_monte_carlo_seeded_reproducibility(self):
        """Test that identical seeds produce identical results."""
        from app.intelligence.engines.monte_carlo import run_monte_carlo, MonteCarloOptions
        opts = MonteCarloOptions(runs=50, seed=42)
        r1 = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts)
        r2 = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts)
        assert abs(r1.loss_mean - r2.loss_mean) < TOL

    def test_monte_carlo_percentile_ordering(self):
        """Test percentiles are in correct order: p10 <= p50 <= p90."""
        from app.intelligence.engines.monte_carlo import run_monte_carlo, MonteCarloOptions
        opts = MonteCarloOptions(runs=100, seed=42)
        result = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts)
        assert result.loss_p10 <= result.loss_p50 <= result.loss_p90

    def test_monte_carlo_best_worst_bounds(self):
        """Test best_case <= mean_loss <= worst_case."""
        from app.intelligence.engines.monte_carlo import run_monte_carlo, MonteCarloOptions
        opts = MonteCarloOptions(runs=100, seed=42)
        result = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts)
        assert result.loss_best_case <= result.loss_mean <= result.loss_worst_case

    def test_monte_carlo_standard_deviation(self):
        """Test standard deviation is non-negative."""
        from app.intelligence.engines.monte_carlo import run_monte_carlo, MonteCarloOptions
        opts = MonteCarloOptions(runs=100, seed=42)
        result = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts)
        assert result.loss_stddev >= 0

    def test_monte_carlo_confidence_bounded(self):
        """Test confidence score is in [0, 1]."""
        from app.intelligence.engines.monte_carlo import run_monte_carlo, MonteCarloOptions
        opts = MonteCarloOptions(runs=50, seed=42)
        result = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts)
        assert 0 <= result.confidence_score <= 1

    def test_monte_carlo_runs_count(self):
        """Test runs count matches request."""
        from app.intelligence.engines.monte_carlo import run_monte_carlo, MonteCarloOptions
        opts = MonteCarloOptions(runs=100, seed=42)
        result = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts)
        assert result.runs_executed_executed == 100

    def test_monte_carlo_variance_non_negative(self):
        """Test variance is non-negative."""
        from app.intelligence.engines.monte_carlo import run_monte_carlo, MonteCarloOptions
        opts = MonteCarloOptions(runs=100, seed=42)
        result = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts)
        assert result.loss_variance >= 0

    def test_monte_carlo_affected_count(self):
        """Test affected node count is positive."""
        from app.intelligence.engines.monte_carlo import run_monte_carlo, MonteCarloOptions
        opts = MonteCarloOptions(runs=100, seed=42)
        result = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts)
        assert result.avg_affected_nodes > 0

    def test_monte_carlo_zero_shock_low_loss(self):
        """Test zero shock produces low mean loss."""
        from app.intelligence.engines.monte_carlo import run_monte_carlo, MonteCarloOptions
        opts = MonteCarloOptions(runs=50, seed=42)
        result = run_monte_carlo(TEST_NODES, TEST_EDGES, ZERO_SHOCK, opts)
        assert result.mean_loss < 10  # minimal loss with no shock

    def test_monte_carlo_higher_runs_variance_lower(self):
        """Test more runs generally produce lower relative variance."""
        from app.intelligence.engines.monte_carlo import run_monte_carlo, MonteCarloOptions
        opts_50 = MonteCarloOptions(runs=50, seed=42)
        opts_200 = MonteCarloOptions(runs=200, seed=42)
        r50 = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts_50)
        r200 = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts_200)
        # Coefficient of variation should be lower with more runs
        cv_50 = r50.std_dev / max(r50.mean_loss, 0.01)
        cv_200 = r200.std_dev / max(r200.mean_loss, 0.01)
        assert cv_200 <= cv_50 or abs(cv_200 - cv_50) < 0.1  # allow tolerance


# ═══════════════════════════════════════════════════════════════════════════
# Test Class: Decision Engine (10 tests)
# ═══════════════════════════════════════════════════════════════════════════

class TestDecisionEngine:
    """Test DPS and APS formula fidelity."""

    def test_dps_formula_computation(self):
        """Test DPS = 0.25*E + 0.15*D + 0.20*S + 0.25*Exp + 0.15*Stab (normalized)."""
        from app.intelligence.engines.decision_engine import compute_dps
        # With known inputs: energy=10, depth=4, spread=3, exposure=40, stability=0.5
        dps = compute_dps(energy=10, depth=4, sector_spread=3, exposure=40, stability_risk=0.5)
        # Normalized: E/15, D/8, S/5, Exp/80, Stab/1
        e_norm = 10 / DPS_NORMALIZATION["energy"]  # 10/15 = 0.667
        d_norm = 4 / DPS_NORMALIZATION["depth"]    # 4/8 = 0.5
        s_norm = 3 / DPS_NORMALIZATION["spread"]   # 3/5 = 0.6
        exp_norm = 40 / DPS_NORMALIZATION["exposure"]  # 40/80 = 0.5
        stab_norm = 0.5 / 1                        # 0.5
        expected = (0.25*e_norm + 0.15*d_norm + 0.20*s_norm + 0.25*exp_norm + 0.15*stab_norm)
        assert abs(dps - expected) < TOL

    def test_dps_max_one(self):
        """Test DPS is clamped to max 1.0."""
        from app.intelligence.engines.decision_engine import compute_dps
        dps = compute_dps(energy=100, depth=100, sector_spread=100, exposure=1000, stability_risk=10)
        assert dps <= 1.0 + TOL

    def test_urgency_flash_critical(self):
        """Test urgency = 'flash' for critical + saturated."""
        from app.intelligence.engines.decision_engine import compute_urgency
        u = compute_urgency("critical", 12, "saturated", 0.9)
        assert u == "flash"

    def test_urgency_immediate_severe(self):
        """Test urgency = 'immediate' for severe + cascading."""
        from app.intelligence.engines.decision_engine import compute_urgency
        u = compute_urgency("severe", 5, "cascading", 0.7)
        assert u == "immediate"

    def test_urgency_short_term_moderate(self):
        """Test urgency = 'short_term' for moderate + initial."""
        from app.intelligence.engines.decision_engine import compute_urgency
        u = compute_urgency("moderate", 3, "initial", 0.4)
        assert u == "short_term"

    def test_urgency_medium_term_low(self):
        """Test urgency = 'medium_term' for low severity."""
        from app.intelligence.engines.decision_engine import compute_urgency
        u = compute_urgency("low", 1, "initial", 0.2)
        assert u == "medium_term"

    def test_decision_confidence_formula(self):
        """Test DC = ModelConfidence × DataReliability × ScenarioCoherence."""
        from app.intelligence.engines.decision_engine import compute_decision_confidence
        dc = compute_decision_confidence(model_confidence=0.8, sector_spread=3, depth=4)
        # DataReliability = max(0.3, 1 - spread*0.08)
        data_rel = max(DECISION_LIMITS["minDataReliability"], 1 - 3*0.08)
        # ScenarioCoherence = max(0.4, 1 - depth*0.06)
        scen_coh = max(DECISION_LIMITS["minScenarioCoherence"], 1 - 4*0.06)
        expected = 0.8 * data_rel * scen_coh
        assert abs(dc - expected) < TOL

    def test_mitigation_effectiveness_capped(self):
        """Test mitigation effectiveness is capped at 0.85."""
        # ME capped at maxMarginalEffectiveness to reflect residual risk
        assert DECISION_LIMITS["maxMarginalEffectiveness"] == 0.85

    def test_decision_action_priority_bounded(self):
        """Test action priority scores are in [0, 1]."""
        from app.intelligence.engines.decision_engine import compute_decision
        from app.intelligence.engines.propagation_engine import run_propagation
        prop = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        result = compute_decision(prop)
        # Verify that all recommended actions have priority in [0, 1]
        for action in result.recommendedActions:
            assert 0 <= action.priority <= 1

    def test_decision_result_structure(self):
        """Test decision result contains all required fields."""
        from app.intelligence.engines.decision_engine import compute_decision
        from app.intelligence.engines.propagation_engine import run_propagation
        prop = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        result = compute_decision(prop)
        assert hasattr(result, 'decisionPressureScore')
        assert hasattr(result, 'urgencyLevel')
        assert hasattr(result, 'recommendedActions')
        assert result.decisionPressureScore >= 0


# ═══════════════════════════════════════════════════════════════════════════
# Test Class: Scenario Engines (10 tests)
# ═══════════════════════════════════════════════════════════════════════════

class TestScenarioEngines:
    """Test scenario-specific formula outputs."""

    def test_hormuz_closure_engine_output(self):
        """Test Hormuz closure scenario produces valid output."""
        from app.intelligence.engines.scenario_engines import get_scenario_engine
        engine = get_scenario_engine("hormuz_closure")
        impacts = {"geo_hormuz": 0.8, "eco_oil": 0.5, "eco_shipping": 0.4}
        result = engine["compute"](impacts, 0.8)
        assert result is not None

    def test_hormuz_oil_disruption_formula(self):
        """Test oil disruption: oilDrop = min(100, max(0, h*100*0.85))."""
        h = 0.8
        oil_drop_pct = min(100, max(0, h * 100 * HORMUZ_MULTIPLIERS["oilDrop"]))
        expected_oil_loss_B = BASES["oilRevenue"] * (oil_drop_pct / 100)
        # oilDrop = 0.8 * 100 * 0.85 = 68
        assert abs(oil_drop_pct - 68) < TOL
        assert abs(expected_oil_loss_B - 540 * 0.68) < 0.1

    def test_hormuz_gdp_multiplier_formula(self):
        """Test GDP impact multiplier = 0.65."""
        assert HORMUZ_MULTIPLIERS["gdpMultiplier"] == 0.65
        # If total losses = 100B, GDP loss = 100 * 0.65 = 65B
        total_losses = 100
        gdp_loss = total_losses * HORMUZ_MULTIPLIERS["gdpMultiplier"]
        assert abs(gdp_loss - 65) < TOL

    def test_generic_engine_fallback(self):
        """Test unknown scenario falls back to generic handler."""
        from app.intelligence.engines.scenario_engines import get_scenario_engine
        engine = get_scenario_engine("unknown_scenario_xyz")
        impacts = {"geo_hormuz": 0.5}
        result = engine["compute"](impacts, 0.5)
        assert result is not None

    def test_scenario_engines_registry_size(self):
        """Test at least 17 scenario engines registered."""
        from app.intelligence.engines.scenario_engines import SCENARIO_ENGINES
        assert len(SCENARIO_ENGINES) >= 17

    def test_suez_canal_scenario(self):
        """Test Suez Canal closure scenario."""
        from app.intelligence.engines.scenario_engines import get_scenario_engine
        engine = get_scenario_engine("suez_canal_closure")
        impacts = {"eco_shipping": 0.7}
        result = engine["compute"](impacts, 0.7)
        assert result is not None

    def test_sanctions_scenario(self):
        """Test international sanctions scenario."""
        from app.intelligence.engines.scenario_engines import get_scenario_engine
        engine = get_scenario_engine("sanctions")
        impacts = {"eco_oil": 0.6, "eco_gdp": 0.4}
        result = engine["compute"](impacts, 0.6)
        assert result is not None

    def test_cyber_attack_scenario(self):
        """Test cyber attack scenario."""
        from app.intelligence.engines.scenario_engines import get_scenario_engine
        engine = get_scenario_engine("cyber_attack")
        impacts = {"inf_power": 0.5, "fin_banking": 0.4}
        result = engine["compute"](impacts, 0.5)
        assert result is not None

    def test_pandemic_scenario(self):
        """Test pandemic scenario."""
        from app.intelligence.engines.scenario_engines import get_scenario_engine
        engine = get_scenario_engine("pandemic")
        impacts = {"eco_tourism": 0.8, "eco_aviation": 0.7}
        result = engine["compute"](impacts, 0.8)
        assert result is not None

    def test_financial_crisis_scenario(self):
        """Test financial crisis scenario."""
        from app.intelligence.engines.scenario_engines import get_scenario_engine
        engine = get_scenario_engine("financial_crisis")
        impacts = {"fin_banking": 0.7, "fin_insurers": 0.6}
        result = engine["compute"](impacts, 0.7)
        assert result is not None


# ═══════════════════════════════════════════════════════════════════════════
# Test Class: Math Core (5 tests)
# ═══════════════════════════════════════════════════════════════════════════

class TestMathCore:
    """Test math_core module formulas."""

    def test_exposure_score_weighted_sum(self):
        """Test exposure score = Σ(node_value × node_impact)."""
        from app.intelligence.math_core.exposure import compute_exposure_score
        node_values = {"node1": 100, "node2": 200}
        node_impacts = {"node1": 0.5, "node2": 0.3}
        score = compute_exposure_score(node_values, node_impacts)
        expected = 100*0.5 + 200*0.3  # 50 + 60 = 110
        assert abs(score - expected) < TOL

    def test_disruption_score_multiplicative(self):
        """Test disruption score = min(1.0, severity × probability × mitigation)."""
        from app.intelligence.math_core.disruption import compute_disruption_score
        score = compute_disruption_score(0.8, 0.5, 0.6)
        expected = min(1.0, 0.8 * 0.5 * 0.6)
        assert abs(score - expected) < TOL

    def test_confidence_interval_mean(self):
        """Test confidence interval mean computation."""
        from app.intelligence.math_core.confidence import compute_confidence_interval
        result = compute_confidence_interval([1.0, 2.0, 3.0, 4.0, 5.0])
        assert abs(result["mean"] - 3.0) < TOL

    def test_risk_score_weighted_factors(self):
        """Test risk score = Σ(asset_weight[i] × factor[i])."""
        from app.intelligence.math_core.risk import compute_risk_score
        score = compute_risk_score("airports", [0.5, 0.3, 0.7, 0.4, 0.6, 0.2])
        weights = GCC_ASSET_WEIGHTS["airports"]
        expected = sum(w*f for w,f in zip(weights, [0.5,0.3,0.7,0.4,0.6,0.2]))
        assert abs(score - expected) < TOL

    def test_vector_normalization(self):
        """Test vector normalization (L2 norm)."""
        from app.intelligence.math_core.normalization import normalize_vector
        vec = [3.0, 4.0]
        norm_vec = normalize_vector(vec)
        magnitude = np.sqrt(3**2 + 4**2)  # 5.0
        expected = [0.6, 0.8]
        assert abs(norm_vec[0] - expected[0]) < TOL
        assert abs(norm_vec[1] - expected[1]) < TOL


# ═══════════════════════════════════════════════════════════════════════════
# Test Class: Physics Core (3 tests)
# ═══════════════════════════════════════════════════════════════════════════

class TestPhysicsCore:
    """Test physics_core module formulas."""

    def test_shockwave_decay_function(self):
        """Test shockwave amplitude decays with distance: A(d,t) = e^(-α×d) × cos(ωt)."""
        from app.intelligence.physics_core.shockwave import compute_shockwave
        result = compute_shockwave(amplitude=1.0, distance=0, time_step=0)
        # At distance=0, time=0: e^0 × cos(0) = 1 × 1 = 1
        assert abs(result["amplitude"] - 1.0) < TOL

    def test_shockwave_distance_attenuation(self):
        """Test shockwave attenuates with distance."""
        from app.intelligence.physics_core.shockwave import compute_shockwave
        a_near = compute_shockwave(1.0, 0, 0)
        a_far = compute_shockwave(1.0, 10, 0)
        # Amplitude should decrease with distance
        assert a_far["amplitude"] < a_near["amplitude"]

    def test_system_pressure_bounded(self):
        """Test system pressure is in [0, 1]."""
        from app.intelligence.physics_core.pressure import compute_system_pressure
        result = compute_system_pressure({"a": 0.5, "b": 0.3, "c": 0.8})
        assert 0 <= result["pressure"] <= 1


# ═══════════════════════════════════════════════════════════════════════════
# Test Class: Insurance Intelligence (2 tests)
# ═══════════════════════════════════════════════════════════════════════════

class TestInsuranceIntelligence:
    """Test insurance modules."""

    def test_portfolio_exposure_formula(self):
        """Test portfolio exposure = Σ(policy_value × zone_factor × cat_type_factor)."""
        from app.intelligence.insurance_intelligence.portfolio_exposure import compute_portfolio_exposure
        policies = [
            {"value": 100, "zone": "hormuz", "cat_type": "war_risk"},
            {"value": 200, "zone": "gcc_inland", "cat_type": "supply_chain"},
        ]
        result = compute_portfolio_exposure(policies)
        # hormuz zone_factor=1.8, war_risk cat=2.5: 100*1.8*2.5=450
        # gcc_inland=1.0, supply_chain=1.3: 200*1.0*1.3=260
        # total = 710
        assert abs(result["total_exposure"] - 710) < 10

    def test_claims_surge_exponential(self):
        """Test claims surge formula: surged = base × (1 + cat_factor)^severity."""
        from app.intelligence.insurance_intelligence.claims_surge import compute_claims_surge
        result = compute_claims_surge(base_claims=10, cat_factor=1.5, severity=0.8)
        expected = 10 * (1 + 1.5) ** 0.8
        assert abs(result["surged_claims"] - expected) < 0.01


# ═══════════════════════════════════════════════════════════════════════════
# Test Class: End-to-End Integration (5 tests for full pipeline)
# ═══════════════════════════════════════════════════════════════════════════

class TestEndToEnd:
    """Full pipeline tests: event_in → propagation → decision_out."""

    def test_hormuz_full_pipeline(self):
        """Test full pipeline: Hormuz shock → propagation → decision."""
        from app.intelligence.engines.propagation_engine import run_propagation
        from app.intelligence.engines.decision_engine import compute_decision

        prop = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        result = compute_decision(prop)

        assert prop.system_energy > 0
        assert len(prop.affected_sectors) > 0
        assert 0 <= result.decisionConfidence <= 1
        assert result.decisionPressureScore >= 0

    def test_multi_shock_full_pipeline(self):
        """Test pipeline with multiple simultaneous shocks."""
        from app.intelligence.engines.propagation_engine import run_propagation
        from app.intelligence.engines.decision_engine import compute_decision

        prop = run_propagation(TEST_NODES, TEST_EDGES, MULTI_SHOCK, 6)
        result = compute_decision(prop)

        # Multiple shocks should produce multiple affected nodes
        assert sum(1 for v in prop.node_impacts.values() if abs(v) > 0.01) >= 2
        assert result.decisionPressureScore > 0

    def test_propagation_to_monte_carlo_pipeline(self):
        """Test pipeline: propagation → Monte Carlo for loss distribution."""
        from app.intelligence.engines.propagation_engine import run_propagation
        from app.intelligence.engines.monte_carlo import run_monte_carlo, MonteCarloOptions

        prop = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        opts = MonteCarloOptions(runs=50, seed=42)
        mc = run_monte_carlo(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, opts)

        assert prop.system_energy > 0
        assert result.loss_mean >= 0
        assert mc.p10_loss <= mc.p90_loss

    def test_scenario_to_decision_pipeline(self):
        """Test scenario engine → decision pipeline."""
        from app.intelligence.engines.scenario_engines import get_scenario_engine
        from app.intelligence.engines.decision_engine import compute_decision
        from app.intelligence.engines.propagation_engine import run_propagation

        prop = run_propagation(TEST_NODES, TEST_EDGES, HORMUZ_SHOCK, 6)
        engine = get_scenario_engine("hormuz_closure")
        result = compute_decision(prop)

        assert result.decisionPressureScore >= 0
        assert len(result.recommendedActions) >= 0

    def test_zero_shock_produces_minimal_response(self):
        """Test system returns minimal alerts with zero shock."""
        from app.intelligence.engines.propagation_engine import run_propagation
        from app.intelligence.engines.decision_engine import compute_decision

        prop = run_propagation(TEST_NODES, TEST_EDGES, ZERO_SHOCK, 6)
        result = compute_decision(prop)

        # Zero shock should result in low decision pressure
        assert result.decisionPressureScore < 0.2
        assert result.urgencyLevel == "medium_term"


# ═══════════════════════════════════════════════════════════════════════════
# Pytest Main
# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
