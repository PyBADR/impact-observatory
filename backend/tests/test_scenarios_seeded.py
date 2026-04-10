"""
Regression test suite for seeded GCC scenario execution.
Validates all 15 predefined scenarios against expected outputs using ScenarioRunner.

GCC-calibrated ranges reflect the production cascade model output.
"""

import pytest
import sys
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.scenarios.runner import ScenarioRunner
from seeds.scenario_seeds import list_scenario_ids

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


@pytest.fixture
def scenario_runner():
    """Initialize ScenarioRunner with expected outputs."""
    expected_outputs_dir = Path(__file__).parent.parent / "seeds" / "expected_outputs"
    return ScenarioRunner(expected_outputs_dir=str(expected_outputs_dir))


class TestScenarioExecution:
    """Test execution and validation of all 15 seeded scenarios."""

    def test_hormuz_closure_affects_gulf_ports(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("hormuz_closure")
        assert result.scenario_id == "hormuz_closure"
        assert result.risk_increase >= 0.70
        assert result.affected_ports >= 5
        assert result.affected_corridors >= 3
        assert 2 <= result.cascade_depth <= 5

    def test_gcc_airspace_closure_reroutes_flights(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("gcc_airspace_closure")
        assert result.scenario_id == "gcc_airspace_closure"
        assert result.risk_increase >= 0.55
        assert result.affected_airports >= 5
        assert result.confidence_adjustment < 0
        assert 1 <= result.cascade_depth <= 5

    def test_missile_escalation_damages_infrastructure(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("missile_escalation")
        assert result.scenario_id == "missile_escalation"
        assert result.risk_increase >= 0.70
        assert result.nodes_affected_total >= 5
        assert len(result.critical_nodes_impacted) > 0
        assert 2 <= result.cascade_depth <= 6

    def test_airport_shutdown_disrupts_aviation(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("airport_shutdown")
        assert result.scenario_id == "airport_shutdown"
        assert result.risk_increase >= 0.65
        assert result.affected_airports >= 3
        assert result.logistics_delay_hours > 0
        assert 1 <= result.cascade_depth <= 5

    def test_port_congestion_delays_logistics(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("port_congestion")
        assert result.scenario_id == "port_congestion"
        assert result.risk_increase >= 0.55
        assert result.affected_ports >= 5
        assert result.logistics_delay_hours >= 50
        assert 2 <= result.cascade_depth <= 6

    def test_conflict_spillover_multi_domain(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("conflict_spillover")
        assert result.scenario_id == "conflict_spillover"
        assert result.risk_increase >= 0.70
        assert result.affected_ports >= 2
        assert result.affected_airports >= 2
        assert 2 <= result.cascade_depth <= 6

    def test_maritime_risk_surge_insurance(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("maritime_risk_surge")
        assert result.scenario_id == "maritime_risk_surge"
        assert result.risk_increase >= 0.40
        assert result.insurance_surge > 0
        assert 1 <= result.cascade_depth <= 5

    def test_combined_disruption_cascades(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("combined_disruption")
        assert result.scenario_id == "combined_disruption"
        assert result.risk_increase >= 0.70
        assert result.affected_ports >= 3
        assert result.affected_airports >= 2
        assert result.affected_corridors >= 2
        assert 3 <= result.cascade_depth <= 6
        assert result.nodes_affected_total >= 10

    def test_insurance_surge_rate_spike(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("insurance_surge")
        assert result.scenario_id == "insurance_surge"
        assert result.risk_increase >= 0.35
        assert result.insurance_surge >= 0.15
        assert result.nodes_affected_total >= 5
        assert 1 <= result.cascade_depth <= 4

    def test_executive_board_economic_pressure(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("executive_board")
        assert result.scenario_id == "executive_board"
        assert result.risk_increase >= 0.50
        assert result.nodes_affected_total >= 5
        assert 1 <= result.cascade_depth <= 6

    def test_red_sea_diversion_corridor(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("red_sea_diversion")
        assert result.scenario_id == "red_sea_diversion"
        assert result.risk_increase >= 0.65
        assert result.affected_corridors >= 3
        assert result.logistics_delay_hours > 0
        assert 2 <= result.cascade_depth <= 6

    def test_dual_disruption_maritime_air(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("dual_disruption")
        assert result.scenario_id == "dual_disruption"
        assert result.risk_increase >= 0.70
        assert result.affected_ports >= 2
        assert result.affected_airports >= 2
        assert 2 <= result.cascade_depth <= 6

    def test_oil_corridor_risk_fuel(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("oil_corridor_risk")
        assert result.scenario_id == "oil_corridor_risk"
        assert result.risk_increase >= 0.45
        assert result.nodes_affected_total >= 6
        assert 2 <= result.cascade_depth <= 5

    def test_false_signal_minimal_impact(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("false_signal")
        assert result.scenario_id == "false_signal"
        assert result.risk_increase >= 0.10
        assert result.risk_increase <= 0.60  # Still bounded — it's a false alarm
        assert result.nodes_affected_total >= 2
        assert 0 <= result.cascade_depth <= 2

    def test_cascading_reroute_secondary_effects(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("cascading_reroute")
        assert result.scenario_id == "cascading_reroute"
        assert result.risk_increase >= 0.55
        assert result.affected_airports >= 3
        assert 1 <= result.cascade_depth <= 4


class TestScenarioValidation:
    """Test validation framework against expected outputs."""

    def test_all_scenarios_list(self, scenario_runner):
        scenario_ids = list_scenario_ids()
        assert len(scenario_ids) == 15
        expected_ids = [
            "hormuz_closure", "gcc_airspace_closure", "missile_escalation",
            "airport_shutdown", "port_congestion", "conflict_spillover",
            "maritime_risk_surge", "combined_disruption", "insurance_surge",
            "executive_board", "red_sea_diversion", "dual_disruption",
            "oil_corridor_risk", "false_signal", "cascading_reroute",
        ]
        assert sorted(scenario_ids) == sorted(expected_ids)

    def test_scenario_result_has_required_fields(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("hormuz_closure")
        required_fields = [
            "scenario_id", "risk_increase", "confidence_adjustment",
            "system_stress_level", "affected_ports", "affected_airports",
            "affected_corridors", "insurance_surge", "logistics_delay_hours",
            "cascade_depth", "cascade_events", "propagation_factor",
            "nodes_affected_total", "critical_nodes_impacted",
            "time_horizon_status", "validation_passed", "validation_errors",
        ]
        for field in required_fields:
            assert hasattr(result, field), f"Missing field: {field}"

    def test_cascade_events_structure(self, scenario_runner):
        result = scenario_runner.run_seeded_scenario("combined_disruption")
        assert len(result.cascade_events) > 0
        for event in result.cascade_events:
            assert hasattr(event, "event_type")
            assert hasattr(event, "source_node")
            assert hasattr(event, "affected_nodes")
            assert hasattr(event, "propagation_distance")
            assert hasattr(event, "stress_increase")
            assert hasattr(event, "timestamp")

    def test_confidence_adjustment_decreases_with_cascade(self, scenario_runner):
        high_cascade = scenario_runner.run_seeded_scenario("combined_disruption")
        low_cascade = scenario_runner.run_seeded_scenario("false_signal")
        assert high_cascade.confidence_adjustment < 0
        assert low_cascade.confidence_adjustment < 0
        assert high_cascade.confidence_adjustment < low_cascade.confidence_adjustment


class TestRunAllScenarios:
    """Test batch execution of all scenarios."""

    def test_run_all_scenarios(self, scenario_runner):
        results = scenario_runner.run_all_scenarios()
        assert len(results) == 15
        assert all(isinstance(sid, str) for sid in results.keys())
        assert all(hasattr(r, "scenario_id") for r in results.values())

    def test_export_results_to_json(self, scenario_runner, tmp_path):
        results = scenario_runner.run_all_scenarios()
        output_file = tmp_path / "scenario_results.json"
        scenario_runner.export_results_json(results, str(output_file))
        assert output_file.exists()
        assert output_file.stat().st_size > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
