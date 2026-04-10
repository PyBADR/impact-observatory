"""
Impact Observatory | مرصد الأثر
Phase 4 Decision Value Engine — Acceptance Tests

Tests cover:
  1. Expected vs Actual Engine   → every decision has expected/actual, delta computed
  2. Value Attribution Engine    → value_created, attribution_type, confidence
  3. Decision Effectiveness      → SUCCESS/NEUTRAL/FAILURE classification, score 0-1
  4. Portfolio Value Aggregator   → aggregates match sum of parts, ROI ratio
  5. Full pipeline integration   → all 4 outputs present in orchestrator, no regression
"""
from __future__ import annotations

import pytest

from src.engines.expected_actual_engine import compute_expected_vs_actual, compute_all_expected_actual
from src.engines.value_attribution_engine import compute_value_attribution, compute_all_attributions
from src.engines.effectiveness_engine import compute_effectiveness, compute_all_effectiveness
from src.engines.portfolio_engine import aggregate_portfolio


# ═══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def sample_actions():
    return [
        {
            "id": "act_001",
            "label": "Activate force majeure clause on marine policies",
            "urgency": 0.90,
            "confidence": 0.85,
            "sector": "insurance",
            "reversibility": "LOW",
            "loss_avoided_usd": 350_000_000,
            "cost_usd": 15_000_000,
        },
        {
            "id": "act_002",
            "label": "Increase reinsurance reserves by 20%",
            "urgency": 0.60,
            "confidence": 0.70,
            "sector": "insurance",
            "reversibility": "MEDIUM",
            "loss_avoided_usd": 200_000_000,
            "cost_usd": 40_000_000,
        },
        {
            "id": "act_003",
            "label": "Deploy liquidity buffer for CBUAE compliance",
            "urgency": 0.80,
            "confidence": 0.90,
            "sector": "banking",
            "reversibility": "HIGH",
            "loss_avoided_usd": 500_000_000,
            "cost_usd": 25_000_000,
        },
    ]


@pytest.fixture
def sample_counterfactual():
    return {
        "baseline": {"projected_loss_usd": 5_000_000_000},
        "recommended": {"projected_loss_usd": 2_000_000_000},
    }


@pytest.fixture
def sample_lifecycles():
    return [
        {"decision_id": "act_001", "status": "EXECUTED"},
        {"decision_id": "act_002", "status": "APPROVED"},
        {"decision_id": "act_003", "status": "COMPLETED"},
    ]


@pytest.fixture
def sample_action_confidences():
    return [
        {"action_id": "act_001", "confidence_score": 0.85},
        {"action_id": "act_002", "confidence_score": 0.70},
        {"action_id": "act_003", "confidence_score": 0.90},
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Expected vs Actual Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestExpectedActualEngine:
    """Every decision must have expected/actual outcomes with valid delta."""

    def test_single_decision_returns_all_fields(self, sample_actions, sample_counterfactual):
        result = compute_expected_vs_actual(
            sample_actions[0],
            counterfactual=sample_counterfactual,
            lifecycle={"status": "EXECUTED"},
            total_loss_usd=5_000_000_000,
            severity=0.75,
        )
        assert "decision_id" in result
        assert "expected_outcome" in result
        assert "actual_outcome" in result
        assert "delta" in result
        assert "variance_ratio" in result

    def test_delta_is_actual_minus_expected(self, sample_actions, sample_counterfactual):
        result = compute_expected_vs_actual(
            sample_actions[0],
            counterfactual=sample_counterfactual,
            lifecycle={"status": "EXECUTED"},
            total_loss_usd=5_000_000_000,
            severity=0.75,
        )
        assert abs(result["delta"] - (result["actual_outcome"] - result["expected_outcome"])) < 1.0

    def test_batch_returns_one_per_action(self, sample_actions, sample_counterfactual, sample_lifecycles):
        results = compute_all_expected_actual(
            sample_actions,
            counterfactual=sample_counterfactual,
            lifecycles=sample_lifecycles,
            total_loss_usd=5_000_000_000,
            severity=0.75,
        )
        assert len(results) == len(sample_actions)
        ids = {r["decision_id"] for r in results}
        assert ids == {"act_001", "act_002", "act_003"}

    def test_no_actions_returns_empty(self, sample_counterfactual):
        results = compute_all_expected_actual(
            [],
            counterfactual=sample_counterfactual,
            total_loss_usd=0,
            severity=0.5,
        )
        assert results == []

    def test_executed_status_has_higher_actual_ratio(self, sample_actions, sample_counterfactual):
        executed = compute_expected_vs_actual(
            sample_actions[0],
            counterfactual=sample_counterfactual,
            lifecycle={"status": "EXECUTED"},
            total_loss_usd=5_000_000_000,
            severity=0.75,
        )
        issued = compute_expected_vs_actual(
            sample_actions[0],
            counterfactual=sample_counterfactual,
            lifecycle={"status": "ISSUED"},
            total_loss_usd=5_000_000_000,
            severity=0.75,
        )
        # EXECUTED should realize more than ISSUED
        assert executed["actual_outcome"] > issued["actual_outcome"]

    def test_expected_outcome_is_positive(self, sample_actions, sample_counterfactual):
        result = compute_expected_vs_actual(
            sample_actions[0],
            counterfactual=sample_counterfactual,
            lifecycle={"status": "EXECUTED"},
            total_loss_usd=5_000_000_000,
            severity=0.75,
        )
        assert result["expected_outcome"] >= 0


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Value Attribution Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestValueAttributionEngine:
    """Value created per decision with attribution confidence."""

    def test_single_attribution_returns_all_fields(self):
        ea = {"decision_id": "act_001", "expected_outcome": 100, "actual_outcome": 90, "delta": -10}
        result = compute_value_attribution(
            ea, action={"id": "act_001", "confidence": 0.85}, trust_confidence=0.85
        )
        assert "decision_id" in result
        assert "value_created" in result
        assert "attribution_confidence" in result
        assert "attribution_type" in result

    def test_attribution_type_is_valid(self):
        ea = {"decision_id": "act_001", "expected_outcome": 100, "actual_outcome": 90, "delta": -10}
        result = compute_value_attribution(ea, action={"id": "act_001"})
        assert result["attribution_type"] in ("DIRECT", "PARTIAL", "LOW_CONFIDENCE")

    def test_attribution_confidence_bounded_0_1(self):
        ea = {"decision_id": "act_001", "expected_outcome": 100, "actual_outcome": 90, "delta": -10}
        result = compute_value_attribution(ea, action={"id": "act_001"}, trust_confidence=0.95)
        assert 0 <= result["attribution_confidence"] <= 1.0

    def test_batch_returns_one_per_action(self, sample_actions, sample_counterfactual, sample_lifecycles, sample_action_confidences):
        expected_actuals = compute_all_expected_actual(
            sample_actions,
            counterfactual=sample_counterfactual,
            lifecycles=sample_lifecycles,
            total_loss_usd=5_000_000_000,
            severity=0.75,
        )
        results = compute_all_attributions(
            expected_actuals,
            actions=sample_actions,
            action_confidences=sample_action_confidences,
        )
        assert len(results) == len(sample_actions)

    def test_high_confidence_single_action_is_direct(self):
        ea = {"decision_id": "act_001", "expected_outcome": 100, "actual_outcome": 90, "delta": -10}
        result = compute_value_attribution(
            ea, action={"id": "act_001", "confidence": 0.90}, trust_confidence=0.90, total_actions=1
        )
        assert result["attribution_type"] == "DIRECT"


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Decision Effectiveness Engine
# ═══════════════════════════════════════════════════════════════════════════════

class TestEffectivenessEngine:
    """Classification into SUCCESS/NEUTRAL/FAILURE with score."""

    def test_single_effectiveness_returns_all_fields(self):
        ea = {"decision_id": "act_001", "expected_outcome": 100, "actual_outcome": 120, "delta": 20}
        va = {"decision_id": "act_001", "value_created": 500, "attribution_confidence": 0.85}
        result = compute_effectiveness(ea, va)
        assert "decision_id" in result
        assert "score" in result
        assert "classification" in result

    def test_classification_is_valid(self):
        ea = {"decision_id": "act_001", "expected_outcome": 100, "actual_outcome": 120, "delta": 20}
        va = {"decision_id": "act_001", "value_created": 500, "attribution_confidence": 0.85}
        result = compute_effectiveness(ea, va)
        assert result["classification"] in ("SUCCESS", "NEUTRAL", "FAILURE")

    def test_score_bounded_0_1(self):
        ea = {"decision_id": "act_001", "expected_outcome": 100, "actual_outcome": 120, "delta": 20}
        va = {"decision_id": "act_001", "value_created": 500, "attribution_confidence": 0.85}
        result = compute_effectiveness(ea, va)
        assert 0 <= result["score"] <= 1.0

    def test_positive_delta_positive_value_is_success(self):
        ea = {"decision_id": "act_001", "expected_outcome": 100, "actual_outcome": 150, "delta": 50}
        va = {"decision_id": "act_001", "value_created": 1000, "attribution_confidence": 0.90}
        result = compute_effectiveness(ea, va)
        assert result["classification"] == "SUCCESS"

    def test_negative_delta_negative_value_is_failure(self):
        ea = {"decision_id": "act_001", "expected_outcome": 100, "actual_outcome": 30, "delta": -70}
        va = {"decision_id": "act_001", "value_created": -500, "attribution_confidence": 0.90}
        result = compute_effectiveness(ea, va)
        assert result["classification"] == "FAILURE"

    def test_batch_returns_one_per_action(self):
        eas = [
            {"decision_id": "act_001", "expected_outcome": 100, "actual_outcome": 120, "delta": 20},
            {"decision_id": "act_002", "expected_outcome": 80, "actual_outcome": 60, "delta": -20},
        ]
        vas = [
            {"decision_id": "act_001", "value_created": 500, "attribution_confidence": 0.85},
            {"decision_id": "act_002", "value_created": -200, "attribution_confidence": 0.70},
        ]
        results = compute_all_effectiveness(eas, vas)
        assert len(results) == 2


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Portfolio Value Aggregator
# ═══════════════════════════════════════════════════════════════════════════════

class TestPortfolioAggregator:
    """Portfolio aggregation: totals, rates, best/worst."""

    def test_empty_portfolio(self):
        result = aggregate_portfolio([], [], [])
        assert result["total_decisions"] == 0
        assert result["total_value_created"] == 0.0
        assert result["success_rate"] == 0.0
        assert result["roi_ratio"] == 0.0

    def test_aggregation_matches_individual_sums(self):
        eas = [
            {"decision_id": "act_001", "expected_outcome": 100, "actual_outcome": 120},
            {"decision_id": "act_002", "expected_outcome": 80, "actual_outcome": 70},
        ]
        vas = [
            {"decision_id": "act_001", "value_created": 500, "attribution_confidence": 0.85},
            {"decision_id": "act_002", "value_created": -200, "attribution_confidence": 0.70},
        ]
        effs = [
            {"decision_id": "act_001", "score": 0.80, "classification": "SUCCESS"},
            {"decision_id": "act_002", "score": 0.30, "classification": "FAILURE"},
        ]
        result = aggregate_portfolio(eas, vas, effs)
        assert result["total_decisions"] == 2
        assert result["total_expected"] == 180.0
        assert result["total_actual"] == 190.0
        assert abs(result["total_value_created"] - 300.0) < 0.01
        assert result["success_count"] == 1
        assert result["failure_count"] == 1

    def test_success_rate_is_ratio(self):
        eas = [{"expected_outcome": 100, "actual_outcome": 120}] * 3
        effs = [
            {"classification": "SUCCESS", "score": 0.8},
            {"classification": "SUCCESS", "score": 0.7},
            {"classification": "FAILURE", "score": 0.2},
        ]
        result = aggregate_portfolio(eas, [], effs)
        assert abs(result["success_rate"] - 2 / 3) < 0.01

    def test_best_worst_decision_ids(self):
        vas = [
            {"decision_id": "act_001", "value_created": 500},
            {"decision_id": "act_002", "value_created": -200},
            {"decision_id": "act_003", "value_created": 300},
        ]
        result = aggregate_portfolio([{}, {}, {}], vas, [{}, {}, {}])
        assert result["best_decision_id"] == "act_001"
        assert result["worst_decision_id"] == "act_002"

    def test_roi_ratio_computed(self):
        eas = [
            {"expected_outcome": 1000, "actual_outcome": 1200},
        ]
        vas = [
            {"decision_id": "act_001", "value_created": 500},
        ]
        result = aggregate_portfolio(eas, vas, [{"score": 0.8, "classification": "SUCCESS"}])
        assert result["roi_ratio"] == round(500 / 1000, 4)

    def test_net_delta_is_actual_minus_expected(self):
        eas = [
            {"expected_outcome": 100, "actual_outcome": 130},
            {"expected_outcome": 200, "actual_outcome": 180},
        ]
        result = aggregate_portfolio(eas, [], [])
        # total_actual=310, total_expected=300, net_delta=10
        assert abs(result["net_delta"] - 10.0) < 0.01


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Full Pipeline Integration
# ═══════════════════════════════════════════════════════════════════════════════

class TestFullPipelineIntegration:
    """End-to-end: actions → expected_actual → attribution → effectiveness → portfolio."""

    def test_full_pipeline_produces_all_outputs(self, sample_actions, sample_counterfactual, sample_lifecycles, sample_action_confidences):
        # Stage 29: Expected vs Actual
        expected_actuals = compute_all_expected_actual(
            sample_actions,
            counterfactual=sample_counterfactual,
            lifecycles=sample_lifecycles,
            total_loss_usd=5_000_000_000,
            severity=0.75,
        )
        assert len(expected_actuals) == 3

        # Stage 30: Value Attribution
        value_attributions = compute_all_attributions(
            expected_actuals,
            actions=sample_actions,
            action_confidences=sample_action_confidences,
        )
        assert len(value_attributions) == 3

        # Stage 31: Effectiveness
        effectiveness_results = compute_all_effectiveness(expected_actuals, value_attributions)
        assert len(effectiveness_results) == 3

        # Stage 32: Portfolio Aggregation
        portfolio = aggregate_portfolio(expected_actuals, value_attributions, effectiveness_results)
        assert portfolio["total_decisions"] == 3
        assert portfolio["total_value_created"] != 0  # not zero for 3 real actions
        assert portfolio["best_decision_id"] is not None
        assert portfolio["worst_decision_id"] is not None
        assert 0 <= portfolio["success_rate"] <= 1.0

    def test_pipeline_with_single_action(self, sample_counterfactual):
        actions = [{"id": "solo_001", "label": "Single action test", "loss_avoided_usd": 100_000_000, "cost_usd": 5_000_000, "confidence": 0.80}]
        lifecycles = [{"decision_id": "solo_001", "status": "EXECUTED"}]

        eas = compute_all_expected_actual(actions, counterfactual=sample_counterfactual, lifecycles=lifecycles, total_loss_usd=1_000_000_000, severity=0.5)
        vas = compute_all_attributions(eas, actions=actions)
        effs = compute_all_effectiveness(eas, vas)
        port = aggregate_portfolio(eas, vas, effs)

        assert port["total_decisions"] == 1
        assert port["best_decision_id"] == "solo_001"
        assert port["worst_decision_id"] == "solo_001"

    def test_no_regression_on_stage_count(self):
        """Pipeline must be at 32 stages after Phase 4."""
        from src.services.run_orchestrator import execute_run
        from src.simulation_schemas import SimulateRequest
        params = SimulateRequest(
            scenario_id="hormuz_chokepoint_disruption",
            severity=0.5,
        )
        result = execute_run(params)
        assert result["pipeline_stages_completed"] == 41
