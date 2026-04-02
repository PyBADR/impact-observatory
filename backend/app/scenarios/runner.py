"""
ScenarioRunner - Executes GCC infrastructure disruption scenarios end-to-end.

This module provides production-grade scenario execution, cascade modeling,
risk propagation, and regression testing capabilities for Phase 11.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from seeds.scenario_seeds import (
    SCENARIO_SEEDS,
    EventType,
    ScenarioSeed,
    get_scenario_seed_by_id,
)

logger = logging.getLogger(__name__)


@dataclass
class CascadeEvent:
    """Represents a single cascade propagation event."""
    event_type: EventType
    source_node: str
    affected_nodes: List[str]
    propagation_distance: int
    stress_increase: float
    timestamp: str


@dataclass
class ScenarioResult:
    """Complete execution result for a single scenario."""
    scenario_id: str
    timestamp: str
    total_execution_time_seconds: float
    risk_increase: float
    confidence_adjustment: float
    system_stress_level: float
    affected_ports: int
    affected_airports: int
    affected_corridors: int
    insurance_surge: float
    logistics_delay_hours: float
    cascade_depth: int
    cascade_events: List[CascadeEvent]
    propagation_factor: float
    nodes_affected_total: int
    critical_nodes_impacted: List[str]
    time_horizon_status: Dict[str, Any]
    validation_passed: bool
    validation_errors: List[str]


class ScenarioRunner:
    """
    Production runner for GCC infrastructure disruption scenarios.
    
    Executes scenarios with full cascade modeling, impact calculation,
    and regression test validation.
    """

    def __init__(self, expected_outputs_dir: Optional[str] = None):
        """
        Initialize the scenario runner.
        
        Args:
            expected_outputs_dir: Path to directory containing expected output JSON files.
                                 Defaults to backend/seeds/expected_outputs/
        """
        if expected_outputs_dir is None:
            expected_outputs_dir = str(
                Path(__file__).parent.parent.parent / "seeds" / "expected_outputs"
            )
        self.expected_outputs_dir = Path(expected_outputs_dir)
        self.expected_outputs_cache: Dict[str, Dict[str, Any]] = {}
        self._load_expected_outputs()

    def _load_expected_outputs(self) -> None:
        """Load all expected output JSON files into memory."""
        if not self.expected_outputs_dir.exists():
            logger.warning(f"Expected outputs directory not found: {self.expected_outputs_dir}")
            return

        for json_file in self.expected_outputs_dir.glob("*.json"):
            scenario_id = json_file.stem
            try:
                with open(json_file, "r") as f:
                    self.expected_outputs_cache[scenario_id] = json.load(f)
                logger.info(f"Loaded expected output for {scenario_id}")
            except Exception as e:
                logger.error(f"Failed to load expected output {json_file}: {e}")

    def run_seeded_scenario(self, scenario_id: str) -> ScenarioResult:
        """
        Execute a single seeded scenario with full cascade modeling.
        
        Args:
            scenario_id: The scenario identifier (e.g., 'hormuz_closure')
            
        Returns:
            ScenarioResult containing all execution metrics and validation
            
        Raises:
            ValueError: If scenario_id not found in seed data
        """
        start_time = datetime.utcnow()
        logger.info(f"Starting scenario execution: {scenario_id}")

        # Retrieve scenario seed
        scenario_seed = get_scenario_seed_by_id(scenario_id)
        if scenario_seed is None:
            raise ValueError(f"Scenario not found: {scenario_id}")

        # Initialize impact tracking
        affected_nodes = set(scenario_seed.affected_node_ids)
        cascade_events: List[CascadeEvent] = []
        cascade_depth = 0
        propagation_factor = 0.0
        total_stress = scenario_seed.severity

        # Cascade modeling: propagate impacts through infrastructure graph
        for event in scenario_seed.inject_events:
            cascade_event = self._propagate_event(
                event=event,
                affected_nodes=affected_nodes,
                cascade_depth=cascade_depth,
                propagation_coefficient=scenario_seed.propagation_coefficient,
            )
            cascade_events.append(cascade_event)
            affected_nodes.update(cascade_event.affected_nodes)

            # Update cascade metrics
            cascade_depth = max(cascade_depth, cascade_event.propagation_distance)
            propagation_factor += cascade_event.stress_increase * (
                scenario_seed.propagation_coefficient ** cascade_event.propagation_distance
            )
            total_stress += cascade_event.stress_increase

        # Calculate impact metrics
        result = self._calculate_impact_metrics(
            scenario_seed=scenario_seed,
            affected_nodes=affected_nodes,
            cascade_events=cascade_events,
            cascade_depth=cascade_depth,
            propagation_factor=propagation_factor,
            total_stress=total_stress,
        )

        # Validate against expected outputs
        result.validation_passed, result.validation_errors = self.validate_against_expected(
            scenario_id=scenario_id,
            result=result,
        )

        # Calculate execution time
        end_time = datetime.utcnow()
        result.total_execution_time_seconds = (end_time - start_time).total_seconds()

        logger.info(
            f"Scenario {scenario_id} completed. "
            f"Risk increase: {result.risk_increase:.2f}, "
            f"Validation: {'PASSED' if result.validation_passed else 'FAILED'}"
        )

        return result

    def _propagate_event(
        self,
        event,
        affected_nodes: set,
        cascade_depth: int,
        propagation_coefficient: float,
    ) -> CascadeEvent:
        """
        Propagate a single event through the infrastructure graph.

        Args:
            event: The event (EventType enum or dict with 'event_type' key)
            affected_nodes: Current set of affected nodes
            cascade_depth: Current cascade depth
            propagation_coefficient: Coefficient controlling cascade spread

        Returns:
            CascadeEvent with propagation details
        """
        # Resolve event to EventType enum if it's a dict
        if isinstance(event, dict):
            event_type_str = event.get("event_type", "")
            try:
                event_type = EventType(event_type_str)
            except ValueError:
                event_type = None
        elif isinstance(event, EventType):
            event_type = event
        else:
            event_type = None

        # Determine secondary affected nodes based on event type
        secondary_nodes = self._get_secondary_nodes_for_event(event_type)

        # Calculate stress increase based on event type and cascade depth
        base_stress = {
            EventType.NAVAL_BLOCKADE: 0.35,
            EventType.MISSILE_THREAT: 0.32,
            EventType.AIRSPACE_CLOSURE: 0.28,
            EventType.PORT_DAMAGE: 0.30,
            EventType.AIRPORT_SHUTDOWN: 0.29,
            EventType.FLIGHT_DIVERSION: 0.18,
            EventType.VESSEL_DIVERSION: 0.16,
            EventType.CORRIDOR_RESTRICTION: 0.22,
            EventType.CONFLICT_SPILLOVER: 0.38,
            EventType.INSURANCE_RATE_SPIKE: 0.20,
            EventType.LOGISTICS_DELAY: 0.15,
            EventType.CYBER_ATTACK: 0.25,
            EventType.FUEL_SHORTAGE: 0.24,
            EventType.ECONOMIC_PRESSURE: 0.12,
        }.get(event_type, 0.15)

        stress_increase = base_stress * (propagation_coefficient ** (cascade_depth + 1))

        return CascadeEvent(
            event_type=event_type.value if event_type else "unknown",
            source_node="sys-root",
            affected_nodes=secondary_nodes,
            propagation_distance=cascade_depth + 1,
            stress_increase=stress_increase,
            timestamp=datetime.utcnow().isoformat() + "Z",
        )

    def _get_secondary_nodes_for_event(self, event: EventType) -> List[str]:
        """Get secondary nodes affected by a specific event type."""
        event_node_mapping = {
            EventType.NAVAL_BLOCKADE: ["cor-001", "cor-005", "cor-008", "prt-003", "prt-007"],
            EventType.AIRSPACE_CLOSURE: ["apt-001", "apt-004", "apt-007", "apt-012"],
            EventType.PORT_DAMAGE: ["prt-002", "prt-008", "prt-014", "cor-002"],
            EventType.AIRPORT_SHUTDOWN: ["apt-003", "apt-006", "apt-011", "prt-004"],
            EventType.MISSILE_THREAT: ["apt-005", "apt-010", "prt-006", "cor-003"],
            EventType.CORRIDOR_RESTRICTION: ["cor-004", "cor-009", "cor-012", "cor-014"],
            EventType.CONFLICT_SPILLOVER: ["prt-009", "apt-008", "apt-013", "cor-007"],
            EventType.FLIGHT_DIVERSION: ["apt-015", "apt-018", "apt-019"],
            EventType.VESSEL_DIVERSION: ["prt-010", "prt-015", "prt-016", "cor-010"],
            EventType.INSURANCE_RATE_SPIKE: ["prt-017", "apt-012", "cor-011"],
            EventType.LOGISTICS_DELAY: ["prt-011", "cor-006", "apt-014"],
            EventType.CYBER_ATTACK: ["apt-020", "prt-020", "cor-015"],
            EventType.FUEL_SHORTAGE: ["cor-001", "cor-005", "prt-018"],
            EventType.ECONOMIC_PRESSURE: ["prt-001", "apt-001"],
        }
        return event_node_mapping.get(event, [])

    def _calculate_impact_metrics(
        self,
        scenario_seed: ScenarioSeed,
        affected_nodes: set,
        cascade_events: List[CascadeEvent],
        cascade_depth: int,
        propagation_factor: float,
        total_stress: float,
    ) -> ScenarioResult:
        """Calculate all impact metrics from cascade modeling."""
        
        # Categorize affected nodes by type
        affected_ports = sum(1 for n in affected_nodes if n.startswith("prt-"))
        affected_airports = sum(1 for n in affected_nodes if n.startswith("apt-"))
        affected_corridors = sum(1 for n in affected_nodes if n.startswith("cor-"))

        # Calculate risk increase from total stress
        risk_increase = min(total_stress * 0.65, 0.85)

        # Calculate confidence adjustment based on cascade depth
        confidence_adjustment = -0.05 - (cascade_depth * 0.03)
        confidence_adjustment = max(min(confidence_adjustment, 0.15), -0.25)

        # System stress is normalized total stress
        system_stress_level = min(total_stress, 1.0)

        # Insurance surge correlates with risk and severity
        insurance_surge = scenario_seed.severity * 0.78 + risk_increase * 0.22

        # Logistics delay scales with time horizon and affected nodes
        logistics_delay_hours = scenario_seed.time_horizon_hours * (
            0.3 + (len(affected_nodes) / 20.0) * 0.7
        )

        # Propagation factor from cascade modeling
        normalized_propagation = min(propagation_factor / cascade_depth, 0.95) if cascade_depth > 0 else 0.0

        # Critical nodes are intersections of expected and actual affected nodes
        critical_nodes = list(
            set(scenario_seed.affected_node_ids) & affected_nodes
        )

        # Time horizon status
        time_horizon_status = {
            "initial_hours": 0,
            "terminal_hours": scenario_seed.time_horizon_hours,
            "peak_stress_hours": {
                "min": max(1, scenario_seed.time_horizon_hours // 10),
                "max": scenario_seed.time_horizon_hours // 3,
            },
        }

        return ScenarioResult(
            scenario_id=scenario_seed.scenario_id,
            timestamp=datetime.utcnow().isoformat() + "Z",
            total_execution_time_seconds=0.0,  # Set by caller
            risk_increase=risk_increase,
            confidence_adjustment=confidence_adjustment,
            system_stress_level=system_stress_level,
            affected_ports=affected_ports,
            affected_airports=affected_airports,
            affected_corridors=affected_corridors,
            insurance_surge=insurance_surge,
            logistics_delay_hours=logistics_delay_hours,
            cascade_depth=cascade_depth,
            cascade_events=cascade_events,
            propagation_factor=normalized_propagation,
            nodes_affected_total=len(affected_nodes),
            critical_nodes_impacted=critical_nodes,
            time_horizon_status=time_horizon_status,
            validation_passed=False,
            validation_errors=[],
        )

    def validate_against_expected(
        self,
        scenario_id: str,
        result: ScenarioResult,
    ) -> Tuple[bool, List[str]]:
        """
        Validate scenario result against expected outputs (regression test).
        
        Args:
            scenario_id: The scenario identifier
            result: The ScenarioResult to validate
            
        Returns:
            Tuple of (validation_passed, error_list)
        """
        if scenario_id not in self.expected_outputs_cache:
            return False, [f"No expected output file found for {scenario_id}"]

        expected = self.expected_outputs_cache[scenario_id]
        errors = []

        # Validate risk metrics
        risk_metrics = expected.get("risk_metrics", {})
        risk_range = risk_metrics.get("overall_risk_increase", {})
        if "min" in risk_range and "max" in risk_range:
            if not (risk_range["min"] <= result.risk_increase <= risk_range["max"]):
                errors.append(
                    f"Risk increase {result.risk_increase:.3f} outside range "
                    f"[{risk_range['min']}, {risk_range['max']}]"
                )

        # Validate impact metrics
        impact_metrics = expected.get("impact_metrics", {})
        
        ports_range = impact_metrics.get("affected_ports", {})
        if "min" in ports_range and "max" in ports_range:
            if not (ports_range["min"] <= result.affected_ports <= ports_range["max"]):
                errors.append(
                    f"Affected ports {result.affected_ports} outside range "
                    f"[{ports_range['min']}, {ports_range['max']}]"
                )

        airports_range = impact_metrics.get("affected_airports", {})
        if "min" in airports_range and "max" in airports_range:
            if not (airports_range["min"] <= result.affected_airports <= airports_range["max"]):
                errors.append(
                    f"Affected airports {result.affected_airports} outside range "
                    f"[{airports_range['min']}, {airports_range['max']}]"
                )

        corridors_range = impact_metrics.get("affected_corridors", {})
        if "min" in corridors_range and "max" in corridors_range:
            if not (corridors_range["min"] <= result.affected_corridors <= corridors_range["max"]):
                errors.append(
                    f"Affected corridors {result.affected_corridors} outside range "
                    f"[{corridors_range['min']}, {corridors_range['max']}]"
                )

        # Validate cascade metrics
        cascade_metrics = expected.get("cascade_metrics", {})
        
        depth_range = cascade_metrics.get("cascade_depth", {})
        if "min" in depth_range and "max" in depth_range:
            if not (depth_range["min"] <= result.cascade_depth <= depth_range["max"]):
                errors.append(
                    f"Cascade depth {result.cascade_depth} outside range "
                    f"[{depth_range['min']}, {depth_range['max']}]"
                )

        nodes_range = cascade_metrics.get("nodes_affected_total", {})
        if "min" in nodes_range and "max" in nodes_range:
            if not (nodes_range["min"] <= result.nodes_affected_total <= nodes_range["max"]):
                errors.append(
                    f"Total affected nodes {result.nodes_affected_total} outside range "
                    f"[{nodes_range['min']}, {nodes_range['max']}]"
                )

        return len(errors) == 0, errors

    def run_all_scenarios(self) -> Dict[str, ScenarioResult]:
        """
        Execute all 15 seeded scenarios.
        
        Returns:
            Dictionary mapping scenario_id to ScenarioResult
        """
        results = {}
        scenario_ids = [seed.scenario_id for seed in SCENARIO_SEEDS]
        
        logger.info(f"Starting execution of {len(scenario_ids)} scenarios")
        
        for scenario_id in scenario_ids:
            try:
                result = self.run_seeded_scenario(scenario_id)
                results[scenario_id] = result
            except Exception as e:
                logger.error(f"Failed to execute scenario {scenario_id}: {e}")
                raise

        logger.info(f"All {len(results)} scenarios completed")
        return results

    def export_results_json(
        self,
        results: Dict[str, ScenarioResult],
        output_path: str,
    ) -> None:
        """
        Export scenario results to JSON file.
        
        Args:
            results: Dictionary of scenario results
            output_path: Path where JSON file will be written
        """
        export_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "total_scenarios": len(results),
            "scenarios": {},
        }

        for scenario_id, result in results.items():
            export_data["scenarios"][scenario_id] = {
                "timestamp": result.timestamp,
                "execution_time_seconds": result.total_execution_time_seconds,
                "risk_increase": result.risk_increase,
                "confidence_adjustment": result.confidence_adjustment,
                "system_stress_level": result.system_stress_level,
                "affected_nodes": {
                    "ports": result.affected_ports,
                    "airports": result.affected_airports,
                    "corridors": result.affected_corridors,
                    "total": result.nodes_affected_total,
                },
                "cascade_metrics": {
                    "depth": result.cascade_depth,
                    "propagation_factor": result.propagation_factor,
                    "events": len(result.cascade_events),
                },
                "impact_metrics": {
                    "insurance_surge": result.insurance_surge,
                    "logistics_delay_hours": result.logistics_delay_hours,
                },
                "validation": {
                    "passed": result.validation_passed,
                    "errors": result.validation_errors,
                },
            }

        with open(output_path, "w") as f:
            json.dump(export_data, f, indent=2)

        logger.info(f"Results exported to {output_path}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    runner = ScenarioRunner()
    results = runner.run_all_scenarios()
    print(f"Executed {len(results)} scenarios")
    for scenario_id, result in results.items():
        print(
            f"  {scenario_id}: risk={result.risk_increase:.3f}, "
            f"validation={'PASS' if result.validation_passed else 'FAIL'}"
        )
