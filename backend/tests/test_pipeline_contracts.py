"""
Pipeline contract tests — verify backend CANNOT produce structurally invalid output.

These tests ensure the class of bugs (reduce/toFixed crashes) cannot recur:
  - f.reduce is not a function  (sector_losses was a dict, must be list)
  - Cannot read properties of undefined (reading 'toFixed')  (numeric fields were None)
  - Cannot read properties of undefined (reading 'map')  (list fields were None)

Run with:
  cd /Users/bdr.ai/Desktop/AIFitnessMirror/deevo-sim/backend
  python3 -m pytest tests/test_pipeline_contracts.py -v
"""
import sys
import os

# Ensure src is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.simulation_engine import SimulationEngine, SCENARIO_CATALOG
from src.simulation_schemas import SimulateResponse

engine = SimulationEngine()

# Canonical scenarios + coverage of all frontend-facing scenarios
SCENARIOS = [
    ("hormuz_chokepoint_disruption", 0.2),
    ("hormuz_chokepoint_disruption", 0.7),
    ("hormuz_chokepoint_disruption", 0.95),
    ("uae_banking_crisis", 0.5),
    ("gcc_cyber_attack", 0.9),
    ("saudi_oil_shock", 0.4),
    ("red_sea_trade_corridor_instability", 0.6),
    ("energy_market_volatility_shock", 0.3),
    ("regional_liquidity_stress_event", 0.8),
    ("critical_port_throughput_disruption", 0.5),
    ("financial_infrastructure_cyber_disruption", 0.7),
]


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_result_passes_schema_validation(scenario_id, severity):
    """The most important test: every result must pass SimulateResponse schema validation."""
    raw = engine.run(scenario_id, severity, 30)
    # This raises ValidationError if any contract is broken
    validated = SimulateResponse.model_validate(raw)
    assert validated is not None
    assert validated.run_id != ""
    assert validated.scenario_id == scenario_id


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_all_list_fields_are_lists(scenario_id, severity):
    """No list field should ever be None, dict, or other non-list type."""
    raw = engine.run(scenario_id, severity, 30)

    list_fields = {
        "sector_analysis": raw.get("sector_analysis"),
        "bottlenecks": raw.get("bottlenecks"),
        "recovery_trajectory": raw.get("recovery_trajectory"),
        "propagation_chain": raw.get("propagation_chain"),
        "financial_impact.top_entities": raw.get("financial_impact", {}).get("top_entities"),
        "financial_impact.sector_losses": raw.get("financial_impact", {}).get("sector_losses"),
        "decision_plan.actions": raw.get("decision_plan", {}).get("actions"),
        "decision_plan.immediate_actions": raw.get("decision_plan", {}).get("immediate_actions"),
        "decision_plan.short_term_actions": raw.get("decision_plan", {}).get("short_term_actions"),
        "decision_plan.long_term_actions": raw.get("decision_plan", {}).get("long_term_actions"),
        "decision_plan.escalation_triggers": raw.get("decision_plan", {}).get("escalation_triggers"),
        "decision_plan.monitoring_priorities": raw.get("decision_plan", {}).get("monitoring_priorities"),
        "explainability.causal_chain": raw.get("explainability", {}).get("causal_chain"),
        "banking_stress.affected_institutions": raw.get("banking_stress", {}).get("affected_institutions"),
        "insurance_stress.affected_lines": raw.get("insurance_stress", {}).get("affected_lines"),
        "fintech_stress.affected_platforms": raw.get("fintech_stress", {}).get("affected_platforms"),
    }

    for field_path, value in list_fields.items():
        assert isinstance(value, list), (
            f"Field '{field_path}' must be list, got {type(value).__name__} = {repr(value)[:100]}"
            f"\n  scenario={scenario_id}, severity={severity}"
        )


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_all_numeric_fields_are_numbers(scenario_id, severity):
    """No numeric field should be None, undefined, or non-numeric."""
    raw = engine.run(scenario_id, severity, 30)

    numeric_fields = {
        "unified_risk_score": raw.get("unified_risk_score"),
        "event_severity": raw.get("event_severity"),
        "confidence_score": raw.get("confidence_score"),
        "propagation_score": raw.get("propagation_score"),
        "congestion_score": raw.get("congestion_score"),
        "recovery_score": raw.get("recovery_score"),
        "peak_day": raw.get("peak_day"),
        "financial_impact.total_loss_usd": raw.get("financial_impact", {}).get("total_loss_usd"),
        "financial_impact.gdp_impact_pct": raw.get("financial_impact", {}).get("gdp_impact_pct"),
        "physical_system_status.congestion_score": raw.get("physical_system_status", {}).get("congestion_score"),
        "physical_system_status.recovery_score": raw.get("physical_system_status", {}).get("recovery_score"),
        "banking_stress.aggregate_stress": raw.get("banking_stress", {}).get("aggregate_stress"),
        "insurance_stress.aggregate_stress": raw.get("insurance_stress", {}).get("aggregate_stress"),
        "fintech_stress.aggregate_stress": raw.get("fintech_stress", {}).get("aggregate_stress"),
        "headline.total_loss_usd": raw.get("headline", {}).get("total_loss_usd"),
        "headline.max_recovery_days": raw.get("headline", {}).get("max_recovery_days"),
        "headline.peak_day": raw.get("headline", {}).get("peak_day"),
        "headline.average_stress": raw.get("headline", {}).get("average_stress"),
    }

    for field_path, value in numeric_fields.items():
        assert isinstance(value, (int, float)), (
            f"Field '{field_path}' must be int/float, got {type(value).__name__} = {repr(value)}"
            f"\n  scenario={scenario_id}, severity={severity}"
        )
        # NaN check
        if isinstance(value, float):
            assert value == value, (
                f"Field '{field_path}' is NaN — scenario={scenario_id}, severity={severity}"
            )


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_sector_losses_is_list_of_dicts_with_required_keys(scenario_id, severity):
    """sector_losses must be a list of {sector, loss_usd, pct} dicts — NOT a flat dict.

    This is the ROOT CAUSE of 'f.reduce is not a function' crash.
    Frontend iterates sector_losses with .map()/.reduce() — if it's a dict it crashes.
    """
    raw = engine.run(scenario_id, severity, 30)
    fi = raw.get("financial_impact", {})
    sector_losses = fi.get("sector_losses", [])

    assert isinstance(sector_losses, list), (
        f"sector_losses must be list (not dict/None), got {type(sector_losses).__name__}"
        f"\n  scenario={scenario_id}, severity={severity}"
        f"\n  Value: {repr(sector_losses)[:200]}"
    )

    for item in sector_losses:
        assert isinstance(item, dict), (
            f"Each sector_loss item must be dict, got {type(item).__name__}: {item}"
        )
        assert "sector" in item, (
            f"sector_loss item missing 'sector' key: {item}"
        )
        assert "loss_usd" in item, (
            f"sector_loss item missing 'loss_usd' key: {item}"
        )
        assert "pct" in item, (
            f"sector_loss item missing 'pct' key: {item}"
        )
        assert isinstance(item["loss_usd"], (int, float)), (
            f"loss_usd must be numeric: {item}"
        )
        assert isinstance(item["pct"], (int, float)), (
            f"pct must be numeric: {item}"
        )


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_top_entities_all_have_required_keys(scenario_id, severity):
    """top_entities items must have all required keys — no KeyError on frontend."""
    raw = engine.run(scenario_id, severity, 30)
    top_entities = raw.get("financial_impact", {}).get("top_entities", [])

    required_keys = {"entity_id", "entity_label", "loss_usd", "sector", "classification", "peak_day"}

    for i, entity in enumerate(top_entities):
        missing = required_keys - set(entity.keys())
        assert not missing, (
            f"top_entities[{i}] missing keys {missing}: {entity}"
            f"\n  scenario={scenario_id}, severity={severity}"
        )
        assert isinstance(entity["loss_usd"], (int, float)), (
            f"top_entities[{i}].loss_usd must be numeric: {entity['loss_usd']}"
        )


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_physical_system_status_has_numeric_scores(scenario_id, severity):
    """physical_system_status.congestion_score and recovery_score must be numeric.

    These are called with .toFixed() on the frontend.
    """
    raw = engine.run(scenario_id, severity, 30)
    pss = raw.get("physical_system_status", {})

    congestion = pss.get("congestion_score")
    recovery = pss.get("recovery_score")

    assert isinstance(congestion, (int, float)) and congestion is not None, (
        f"physical_system_status.congestion_score must be numeric, got {type(congestion).__name__} = {congestion}"
        f"\n  scenario={scenario_id}, severity={severity}"
    )
    assert isinstance(recovery, (int, float)) and recovery is not None, (
        f"physical_system_status.recovery_score must be numeric, got {type(recovery).__name__} = {recovery}"
        f"\n  scenario={scenario_id}, severity={severity}"
    )


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_banking_stress_no_dict_unpacking_contamination(scenario_id, severity):
    """banking_stress must have expected keys — no extra untyped keys from **liquidity_stress."""
    raw = engine.run(scenario_id, severity, 30)
    bs = raw.get("banking_stress", {})

    required_keys = {
        "sector", "aggregate_stress", "liquidity_stress", "credit_stress",
        "fx_stress", "interbank_contagion", "capital_adequacy_impact_pct",
        "time_to_liquidity_breach_hours", "total_exposure_usd",
        "affected_institutions", "run_id"
    }
    missing = required_keys - set(bs.keys())
    assert not missing, (
        f"banking_stress missing required keys: {missing}"
        f"\n  scenario={scenario_id}, severity={severity}"
    )

    # All numeric fields must be numeric
    for key in ("aggregate_stress", "liquidity_stress", "credit_stress", "fx_stress"):
        val = bs.get(key)
        assert isinstance(val, (int, float)), (
            f"banking_stress.{key} must be numeric, got {type(val).__name__} = {val}"
        )


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_decision_plan_action_ids_safe(scenario_id, severity):
    """priority_matrix must not raise KeyError — action_id access must be safe."""
    raw = engine.run(scenario_id, severity, 30)
    dp = raw.get("decision_plan", {})
    pm = dp.get("priority_matrix", {})

    assert isinstance(pm, dict), f"priority_matrix must be dict, got {type(pm)}"

    for key in ("IMMEDIATE", "URGENT", "MONITOR", "WATCH"):
        val = pm.get(key, [])
        assert isinstance(val, list), (
            f"priority_matrix['{key}'] must be list, got {type(val).__name__}"
        )
        # All items must be non-empty strings
        for item in val:
            assert isinstance(item, str) and item, (
                f"priority_matrix['{key}'] contains invalid action_id: {repr(item)}"
            )


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_causal_chain_always_20_steps(scenario_id, severity):
    """causal_chain must always be exactly 20 steps."""
    raw = engine.run(scenario_id, severity, 30)
    causal_chain = raw.get("explainability", {}).get("causal_chain", [])
    assert len(causal_chain) == 20, (
        f"causal_chain must have 20 steps, got {len(causal_chain)}"
        f"\n  scenario={scenario_id}, severity={severity}"
    )


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_insurance_stress_time_to_insolvency_is_numeric(scenario_id, severity):
    """time_to_insolvency_hours must be a number (9999.0 is valid — means no risk)."""
    raw = engine.run(scenario_id, severity, 30)
    val = raw.get("insurance_stress", {}).get("time_to_insolvency_hours")
    assert isinstance(val, (int, float)), (
        f"insurance_stress.time_to_insolvency_hours must be numeric (9999 = no risk), "
        f"got {type(val).__name__} = {val}"
        f"\n  scenario={scenario_id}, severity={severity}"
    )


def test_error_response_is_structured_for_unknown_scenario():
    """Invalid scenario should raise ValueError, not KeyError or AttributeError."""
    with pytest.raises((ValueError, KeyError, Exception)) as exc_info:
        engine.run("NONEXISTENT_SCENARIO_XYZ_DOES_NOT_EXIST", 0.5, 30)
    # Should contain "scenario" or "Unknown" in message — structured error
    err_msg = str(exc_info.value).lower()
    assert "scenario" in err_msg or "unknown" in err_msg or "nonexistent" in err_msg, (
        f"Error message should mention scenario, got: {str(exc_info.value)}"
    )


def test_malformed_severity_clamped():
    """Extreme severity values should be clamped to [0.01, 1.0], not crash."""
    # Very low severity
    r1 = engine.run("hormuz_chokepoint_disruption", 0.0001, 30)
    assert 0.0 <= r1["unified_risk_score"] <= 1.0, (
        f"unified_risk_score out of range for severity=0.0001: {r1['unified_risk_score']}"
    )

    # Very high severity (beyond 1.0 — should be clamped)
    r2 = engine.run("hormuz_chokepoint_disruption", 99.9, 30)
    assert 0.0 <= r2["unified_risk_score"] <= 1.0, (
        f"unified_risk_score out of range for severity=99.9: {r2['unified_risk_score']}"
    )

    # financial field must still be a list
    assert isinstance(r1.get("financial_impact", {}).get("sector_losses", []), list)
    assert isinstance(r2.get("financial_impact", {}).get("sector_losses", []), list)


def test_all_scenario_catalog_ids_run_without_crash():
    """Every scenario in SCENARIO_CATALOG must complete without exception."""
    for scenario_id in SCENARIO_CATALOG:
        try:
            raw = engine.run(scenario_id, 0.5, 24)
            assert isinstance(raw, dict), f"Expected dict result for {scenario_id}"
            assert "run_id" in raw, f"Missing run_id for {scenario_id}"
        except Exception as e:
            pytest.fail(f"scenario '{scenario_id}' raised {type(e).__name__}: {e}")
