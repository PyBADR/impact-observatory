"""
Scenario Engine - Scenario Engine Phase 6
Orchestrates complete scenario analysis workflow
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import uuid

from app.scenarios.templates import (
    ScenarioTemplate, SCENARIO_TEMPLATES, get_template, get_templates_by_disruption_type
)
from app.scenarios.baseline import BaselineSnapshot, BaselineCaptureRequest, BaselineCaptureResult
from app.scenarios.shock import ShockEvent, ShockInjector
from app.scenarios.simulator import ScenarioSimulator, ScenarioSimulationResult
from app.scenarios.delta import DeltaCalculator, NodeDeltaAnalysis, DeltaMetrics
from app.scenarios.explainer import ExplanationGenerator, ScenarioExplanation


@dataclass
class ScenarioExecutionRequest:
    """Request to execute a scenario analysis"""
    scenario_name: str
    baseline_snapshot: BaselineSnapshot
    shock_locations: Optional[List[str]] = None
    custom_severity: Optional[float] = None
    cascade_enabled: bool = True
    cascade_depth: int = 3
    cascade_type: str = 'DISTANCE_WEIGHTED'
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ScenarioExecutionResult:
    """Complete scenario execution result"""
    request_id: str
    scenario_name: str
    scenario_template: ScenarioTemplate
    baseline_snapshot: BaselineSnapshot
    simulation_result: ScenarioSimulationResult
    node_deltas: Dict[str, NodeDeltaAnalysis]
    aggregate_deltas: DeltaMetrics
    explanation: ScenarioExplanation
    execution_time_seconds: float
    status: str = 'completed'
    error_message: Optional[str] = None


class ScenarioEngine:
    """
    Orchestrates complete scenario analysis workflow
    
    Coordinates:
    1. Template retrieval and validation
    2. Baseline snapshot capture
    3. Shock event construction
    4. Simulation execution
    5. Delta analysis
    6. Bilingual explanation generation
    """
    
    def __init__(self):
        import numpy as np
        # Default 5-node placeholder — overridden by execute_scenario with actual baseline data
        _default_ids = [f'node_{i}' for i in range(1, 6)]
        _default_adj = np.zeros((5, 5))
        _default_pos = {nid: (25.0, 55.0) for nid in _default_ids}
        _default_crit = {nid: 0.5 for nid in _default_ids}
        self.simulator = ScenarioSimulator(
            adjacency_matrix=_default_adj,
            node_ids=_default_ids,
            node_positions=_default_pos,
            node_criticality=_default_crit,
        )
        self.delta_calculator = DeltaCalculator()
        self.explainer = ExplanationGenerator()
        self.shock_injector = ShockInjector(
            adjacency_matrix=_default_adj,
            node_ids=_default_ids,
        )
        self.execution_history: List[ScenarioExecutionResult] = []
    
    def execute_scenario(
        self,
        request: ScenarioExecutionRequest
    ) -> ScenarioExecutionResult:
        """
        Execute complete scenario analysis workflow
        
        Args:
            request: ScenarioExecutionRequest with scenario parameters
        
        Returns:
            ScenarioExecutionResult with all analysis outputs
        """
        
        start_time = datetime.utcnow()
        
        try:
            # Step 1: Retrieve and validate scenario template
            template = get_template(request.scenario_name)
            if not template:
                raise ValueError(f"Scenario template '{request.scenario_name}' not found")
            
            # Override severity if provided
            if request.custom_severity:
                template.severity = request.custom_severity
            
            # Step 2: Prepare shock events
            shock_events = self._prepare_shock_events(
                request, template
            )
            
            # Step 3: Run simulation
            simulation_result = self.simulator.run_simulation(
                scenario_template=template,
                baseline_snapshot=request.baseline_snapshot,
                shock_events=shock_events
            )
            
            # Step 4: Calculate deltas
            cascade_info = self._extract_cascade_info(shock_events)
            node_deltas = self.delta_calculator.calculate_node_deltas(
                baseline=request.baseline_snapshot,
                simulation_result=simulation_result,
                cascade_info=cascade_info
            )
            
            aggregate_deltas = self.delta_calculator.calculate_aggregate_deltas(
                baseline=request.baseline_snapshot,
                simulation_result=simulation_result,
                node_deltas=node_deltas
            )
            
            # Step 5: Generate explanation
            explanation = self.explainer.generate_explanation(
                scenario_name=request.scenario_name,
                baseline=request.baseline_snapshot,
                simulation_result=simulation_result,
                node_deltas=node_deltas,
                delta_metrics=aggregate_deltas
            )
            
            # Step 6: Compile results
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            
            result = ScenarioExecutionResult(
                request_id=request.request_id,
                scenario_name=request.scenario_name,
                scenario_template=template,
                baseline_snapshot=request.baseline_snapshot,
                simulation_result=simulation_result,
                node_deltas=node_deltas,
                aggregate_deltas=aggregate_deltas,
                explanation=explanation,
                execution_time_seconds=execution_time,
                status='completed'
            )
            
            # Track execution
            self.execution_history.append(result)
            
            return result
        
        except Exception as e:
            execution_time = (datetime.utcnow() - start_time).total_seconds()
            return ScenarioExecutionResult(
                request_id=request.request_id,
                scenario_name=request.scenario_name,
                scenario_template=None,
                baseline_snapshot=request.baseline_snapshot,
                simulation_result=None,
                node_deltas={},
                aggregate_deltas=None,
                explanation=None,
                execution_time_seconds=execution_time,
                status='failed',
                error_message=str(e)
            )
    
    def execute_multiple_scenarios(
        self,
        baseline_snapshot: BaselineSnapshot,
        scenario_names: List[str]
    ) -> List[ScenarioExecutionResult]:
        """
        Execute multiple scenarios against same baseline
        
        Args:
            baseline_snapshot: Common baseline for all scenarios
            scenario_names: List of scenario template names
        
        Returns:
            List of ScenarioExecutionResult objects
        """
        
        results = []
        
        for scenario_name in scenario_names:
            request = ScenarioExecutionRequest(
                scenario_name=scenario_name,
                baseline_snapshot=baseline_snapshot
            )
            result = self.execute_scenario(request)
            results.append(result)
        
        return results
    
    def compare_scenarios(
        self,
        baseline_snapshot: BaselineSnapshot,
        scenario_names: List[str]
    ) -> Dict:
        """
        Execute and compare multiple scenarios
        
        Returns:
            Dictionary with comparative analysis
        """
        
        results = self.execute_multiple_scenarios(baseline_snapshot, scenario_names)
        
        comparison = {
            'baseline_timestamp': baseline_snapshot.timestamp,
            'scenarios_analyzed': len(results),
            'scenario_results': {}
        }
        
        # Build comparison data
        for result in results:
            if result.status == 'completed':
                comparison['scenario_results'][result.scenario_name] = {
                    'critical_nodes': result.aggregate_deltas.critical_nodes,
                    'total_affected': result.aggregate_deltas.total_nodes_affected,
                    'max_risk_increase': result.aggregate_deltas.max_risk_increase,
                    'system_stress': result.simulation_result.system_stress_final,
                    'recovery_hours': result.aggregate_deltas.recovery_time_estimate_hours
                }
        
        # Identify most severe scenario
        if comparison['scenario_results']:
            most_severe = max(
                comparison['scenario_results'].items(),
                key=lambda x: x[1]['max_risk_increase']
            )
            comparison['most_severe_scenario'] = most_severe[0]
            comparison['most_severe_impact'] = most_severe[1]['max_risk_increase']
        
        return comparison
    
    def get_scenario_recommendations(
        self,
        result: ScenarioExecutionResult
    ) -> Dict:
        """
        Extract detailed recommendations from execution result
        
        Returns:
            Dictionary with prioritized recommendations
        """
        
        if result.status != 'completed':
            return {}
        
        return {
            'scenario': result.scenario_name,
            'timestamp': result.explanation.timestamp.isoformat(),
            'recommendations_english': {
                'executive': result.explanation.recommendations_en[0] if result.explanation.recommendations_en else '',
                'tactical': result.explanation.recommendations_en[1:] if len(result.explanation.recommendations_en) > 1 else []
            },
            'recommendations_arabic': {
                'executive': result.explanation.recommendations_ar[0] if result.explanation.recommendations_ar else '',
                'tactical': result.explanation.recommendations_ar[1:] if len(result.explanation.recommendations_ar) > 1 else []
            },
            'critical_nodes': {
                'english': result.explanation.critical_nodes_en,
                'arabic': result.explanation.critical_nodes_ar
            },
            'recovery_timeline': result.aggregate_deltas.recovery_time_estimate_hours
        }
    
    def _prepare_shock_events(
        self,
        request: ScenarioExecutionRequest,
        template: ScenarioTemplate
    ) -> List[ShockEvent]:
        """Prepare shock events from request and template"""
        
        shock_events = []
        
        # Use shock locations from request or template
        locations = request.shock_locations or template.shock_event_locations
        
        for location in locations:
            severity = request.custom_severity or template.severity
            
            shock = ShockEvent(
                node_id=location,
                severity=severity,
                impact_type=template.disruption_type.value,
                timestamp=request.timestamp,
                duration_hours=template.duration_hours,
                cascade_enabled=request.cascade_enabled,
                cascade_depth=request.cascade_depth,
                cascade_type=request.cascade_type,
                cascade_attenuation=template.propagation_coefficient
            )
            shock_events.append(shock)
        
        return shock_events
    
    def _extract_cascade_info(self, shock_events: List[ShockEvent]) -> Dict:
        """Extract cascade information from shock events"""
        
        cascade_info = {}
        
        for shock in shock_events:
            cascade_info[shock.node_id] = {
                'affected': True,
                'hop_distance': 0,
                'severity': shock.severity
            }
        
        return cascade_info
    
    def get_execution_history(self, limit: int = 10) -> List[ScenarioExecutionResult]:
        """Get recent execution history"""
        return self.execution_history[-limit:]
    
    def clear_history(self):
        """Clear execution history"""
        self.execution_history = []
    
    def export_result(self, result: ScenarioExecutionResult) -> Dict:
        """Export execution result to dictionary format"""
        
        if result.status != 'completed':
            return {
                'request_id': result.request_id,
                'status': result.status,
                'error_message': result.error_message
            }
        
        return {
            'request_id': result.request_id,
            'scenario_name': result.scenario_name,
            'timestamp': result.baseline_snapshot.timestamp,
            'execution_time_seconds': result.execution_time_seconds,
            'status': result.status,
            'simulation': {
                'system_stress': result.simulation_result.system_stress_final,
                'recovery_hours': result.simulation_result.recovery_time_estimate_hours,
                'critical_nodes_count': len([c for c in result.simulation_result.critical_nodes_post_shock if c is not None])
            },
            'deltas': self.delta_calculator.serialize_metrics(result.aggregate_deltas),
            'explanation': self.explainer.export_explanation(result.explanation)
        }
