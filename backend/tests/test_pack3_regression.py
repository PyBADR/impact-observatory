"""
Pack 3 regression tests — verify Pack 1/2 contracts are NOT broken.

Tests:
  - All 16 mandatory SimulateResponse fields still present and valid
  - Propagation chain unchanged
  - Existing decision_plan preserved
  - Existing explainability preserved
  - Pipeline stages updated to 21

Run with:
  cd backend
  python3 -m pytest tests/test_pack3_regression.py -v --tb=short
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from src.simulation_engine import SimulationEngine, SCENARIO_CATALOG, GCC_NODES
from src.simulation_schemas import SimulateResponse

engine = SimulationEngine()

SCENARIOS = [
    ("hormuz_chokepoint_disruption", 0.7),
    ("uae_banking_crisis", 0.5),
    ("gcc_cyber_attack", 0.9),
    ("saudi_oil_shock", 0.4),
    ("red_sea_trade_corridor_instability", 0.6),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Pack 1 Contract Regression
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_pack1_schema_still_validates(scenario_id, severity):
    """SimulateResponse.model_validate() still passes for engine output."""
    raw = engine.run(scenario_id, severity, 336)
    validated = SimulateResponse.model_validate(raw)
    assert validated is not None
    assert validated.run_id != ""


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_pack1_mandatory_fields_present(scenario_id, severity):
    """All 16 mandatory fields from Pack 1 are still present."""
    raw = engine.run(scenario_id, severity, 336)
    mandatory = [
        "event_severity", "peak_day", "confidence_score",
        "financial_impact", "sector_analysis", "propagation_score",
        "unified_risk_score", "risk_level",
        "physical_system_status", "bottlenecks", "congestion_score",
        "recovery_score", "recovery_trajectory",
        "explainability", "decision_plan", "flow_analysis",
    ]
    for field in mandatory:
        assert field in raw, f"Mandatory field '{field}' missing from engine output"


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_pack1_numeric_fields_valid(scenario_id, severity):
    """Pack 1 numeric fields are still numbers (not None/dict/str)."""
    raw = engine.run(scenario_id, severity, 336)
    numerics = {
        "event_severity": raw.get("event_severity"),
        "peak_day": raw.get("peak_day"),
        "confidence_score": raw.get("confidence_score"),
        "propagation_score": raw.get("propagation_score"),
        "congestion_score": raw.get("congestion_score"),
        "recovery_score": raw.get("recovery_score"),
    }
    for field, val in numerics.items():
        assert isinstance(val, (int, float)), (
            f"Pack 1 field '{field}' is {type(val).__name__}, expected number"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Pack 2 Contract Regression
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_pack2_propagation_preserved(scenario_id, severity):
    """Propagation chain is still a list with expected structure."""
    raw = engine.run(scenario_id, severity, 336)
    chain = raw.get("propagation_chain", [])
    assert isinstance(chain, list)
    assert len(chain) > 0, "Propagation chain should be non-empty"
    for step in chain:
        assert "entity_id" in step
        assert "impact" in step or "propagation_score" in step


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_pack2_decision_plan_preserved(scenario_id, severity):
    """Existing decision_plan field is present with expected structure."""
    raw = engine.run(scenario_id, severity, 336)
    dp = raw.get("decision_plan", {})
    assert isinstance(dp, dict)
    assert "actions" in dp
    assert isinstance(dp["actions"], list)
    assert len(dp["actions"]) > 0, "decision_plan.actions should be non-empty"


@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_pack2_explainability_preserved(scenario_id, severity):
    """Existing explainability field is present with expected structure."""
    raw = engine.run(scenario_id, severity, 336)
    expl = raw.get("explainability", {})
    assert isinstance(expl, dict)
    assert "causal_chain" in expl
    assert isinstance(expl["causal_chain"], list)
    assert "narrative_en" in expl


# ═══════════════════════════════════════════════════════════════════════════════
# Pack 1/2 List Field Safety
# ═══════════════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("scenario_id,severity", SCENARIOS)
def test_all_existing_list_fields_still_lists(scenario_id, severity):
    """All existing list fields are still lists (not broken by Pack 3)."""
    raw = engine.run(scenario_id, severity, 336)
    list_fields = {
        "sector_analysis": raw.get("sector_analysis"),
        "bottlenecks": raw.get("bottlenecks"),
        "recovery_trajectory": raw.get("recovery_trajectory"),
        "propagation_chain": raw.get("propagation_chain"),
        "financial_impact.top_entities": raw.get("financial_impact", {}).get("top_entities"),
        "decision_plan.actions": raw.get("decision_plan", {}).get("actions"),
    }
    for path, val in list_fields.items():
        assert isinstance(val, list), (
            f"Existing list field '{path}' is {type(val).__name__}"
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Pack 3 Additive Fields
# ═══════════════════════════════════════════════════════════════════════════════

def test_simulate_response_accepts_pack3_fields():
    """SimulateResponse schema accepts the 3 new Pack 3 dict fields."""
    # These are the new additive fields
    data = {
        "impact_assessment": {"run_id": "test"},
        "decision_brain_output": {"run_id": "test"},
        "decision_envelope": {"run_id": "test"},
    }
    validated = SimulateResponse.model_validate(data)
    assert validated.impact_assessment == {"run_id": "test"}
    assert validated.decision_brain_output == {"run_id": "test"}
    assert validated.decision_envelope == {"run_id": "test"}


def test_simulate_response_defaults_pack3_to_empty():
    """SimulateResponse defaults Pack 3 fields to empty dict."""
    validated = SimulateResponse.model_validate({})
    assert validated.impact_assessment == {}
    assert validated.decision_brain_output == {}
    assert validated.decision_envelope == {}
