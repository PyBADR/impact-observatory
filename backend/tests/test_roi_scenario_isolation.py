"""Test ROI isolation by scenario_id threading through Phase 4 engines."""
import pytest
from src.engines.value_attribution_engine import compute_all_attributions
from src.engines.effectiveness_engine import compute_all_effectiveness
from src.engines.portfolio_engine import aggregate_portfolio


def test_scenario_id_threading_through_value_attribution():
    """Verify compute_all_attributions returns scenario_id in each result."""
    expected_actuals = [
        {
            "decision_id": "d1",
            "expected_outcome": 100.0,
            "actual_outcome": 110.0,
            "delta": 10.0,
            "variance_ratio": 0.10,
        },
        {
            "decision_id": "d2",
            "expected_outcome": 50.0,
            "actual_outcome": 40.0,
            "delta": -10.0,
            "variance_ratio": 0.20,
        },
    ]
    
    results = compute_all_attributions(
        expected_actuals=expected_actuals,
        scenario_id="test_scenario_a",
    )
    
    assert len(results) == 2
    assert results[0]["scenario_id"] == "test_scenario_a"
    assert results[1]["scenario_id"] == "test_scenario_a"
    assert results[0]["decision_id"] == "d1"
    assert results[1]["decision_id"] == "d2"


def test_scenario_id_threading_through_effectiveness():
    """Verify compute_all_effectiveness returns scenario_id in each result."""
    expected_actuals = [
        {
            "decision_id": "d1",
            "expected_outcome": 100.0,
            "actual_outcome": 110.0,
            "delta": 10.0,
            "variance_ratio": 0.10,
        },
    ]
    
    value_attributions = [
        {
            "decision_id": "d1",
            "value_created": 110.0,
            "attribution_confidence": 0.85,
        },
    ]
    
    results = compute_all_effectiveness(
        expected_actuals=expected_actuals,
        value_attributions=value_attributions,
        scenario_id="test_scenario_b",
    )
    
    assert len(results) == 1
    assert results[0]["scenario_id"] == "test_scenario_b"
    assert results[0]["decision_id"] == "d1"


def test_portfolio_filters_by_scenario_id():
    """Verify aggregate_portfolio correctly isolates data by scenario_id."""
    # Mixed data: 3 decisions total, 2 in scenario_a, 1 in scenario_b
    expected_actuals = [
        {"decision_id": "d1", "expected_outcome": 100.0, "actual_outcome": 120.0, "delta": 20.0, "variance_ratio": 0.20, "scenario_id": "scenario_a"},
        {"decision_id": "d2", "expected_outcome": 200.0, "actual_outcome": 180.0, "delta": -20.0, "variance_ratio": 0.10, "scenario_id": "scenario_a"},
        {"decision_id": "d3", "expected_outcome": 150.0, "actual_outcome": 130.0, "delta": -20.0, "variance_ratio": 0.13, "scenario_id": "scenario_b"},
    ]
    
    value_attributions = [
        {"decision_id": "d1", "value_created": 120.0, "attribution_confidence": 0.90, "scenario_id": "scenario_a"},
        {"decision_id": "d2", "value_created": 180.0, "attribution_confidence": 0.80, "scenario_id": "scenario_a"},
        {"decision_id": "d3", "value_created": 130.0, "attribution_confidence": 0.75, "scenario_id": "scenario_b"},
    ]
    
    effectiveness_results = [
        {"decision_id": "d1", "score": 0.60, "classification": "SUCCESS", "scenario_id": "scenario_a"},
        {"decision_id": "d2", "score": 0.45, "classification": "NEUTRAL", "scenario_id": "scenario_a"},
        {"decision_id": "d3", "score": 0.43, "classification": "NEUTRAL", "scenario_id": "scenario_b"},
    ]
    
    # Test scenario_a isolation
    portfolio_a = aggregate_portfolio(
        expected_actuals=expected_actuals,
        value_attributions=value_attributions,
        effectiveness_results=effectiveness_results,
        scenario_id="scenario_a",
    )
    
    assert portfolio_a["total_decisions"] == 2
    assert portfolio_a["total_value_created"] == 300.0  # 120 + 180
    assert portfolio_a["success_count"] == 1
    assert portfolio_a["neutral_count"] == 1
    assert portfolio_a["scenario_id"] == "scenario_a"
    
    # Test scenario_b isolation
    portfolio_b = aggregate_portfolio(
        expected_actuals=expected_actuals,
        value_attributions=value_attributions,
        effectiveness_results=effectiveness_results,
        scenario_id="scenario_b",
    )
    
    assert portfolio_b["total_decisions"] == 1
    assert portfolio_b["total_value_created"] == 130.0
    assert portfolio_b["neutral_count"] == 1
    assert portfolio_b["scenario_id"] == "scenario_b"


def test_portfolio_with_empty_scenario_id_backward_compatibility():
    """Verify aggregate_portfolio includes all data when scenario_id is empty (backward compat)."""
    expected_actuals = [
        {"decision_id": "d1", "expected_outcome": 100.0, "actual_outcome": 120.0, "delta": 20.0, "variance_ratio": 0.20},
        {"decision_id": "d2", "expected_outcome": 200.0, "actual_outcome": 180.0, "delta": -20.0, "variance_ratio": 0.10},
    ]
    
    value_attributions = [
        {"decision_id": "d1", "value_created": 120.0, "attribution_confidence": 0.90},
        {"decision_id": "d2", "value_created": 180.0, "attribution_confidence": 0.80},
    ]
    
    effectiveness_results = [
        {"decision_id": "d1", "score": 0.60, "classification": "SUCCESS"},
        {"decision_id": "d2", "score": 0.45, "classification": "NEUTRAL"},
    ]
    
    portfolio = aggregate_portfolio(
        expected_actuals=expected_actuals,
        value_attributions=value_attributions,
        effectiveness_results=effectiveness_results,
        scenario_id="",  # Empty = include all
    )
    
    assert portfolio["total_decisions"] == 2
    assert portfolio["total_value_created"] == 300.0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
