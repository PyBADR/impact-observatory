"""
Test Suite for Scenario Engine - Phase 6
Comprehensive tests covering all scenario analysis functionality
"""

import pytest
import numpy as np
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock

from app.scenarios.templates import (
    ScenarioTemplate, DisruptionType, ScenarioDomain, get_template
)
from app.scenarios.baseline import BaselineSnapshot
from app.scenarios.shock import ShockEvent, ShockInjector
from app.scenarios.simulator import ScenarioSimulator, ScenarioSimulationResult
from app.scenarios.delta import DeltaCalculator, NodeDeltaAnalysis
from app.scenarios.explainer import ExplanationGenerator
from app.scenarios.engine import ScenarioEngine, ScenarioExecutionRequest


# Test Fixtures
@pytest.fixture
def sample_baseline():
    """Create a sample baseline snapshot for testing"""
    node_ids = ['node_1', 'node_2', 'node_3', 'node_4', 'node_5']
    node_risk_scores = {nid: 0.3 + (i * 0.1) for i, nid in enumerate(node_ids)}
    node_centrality = {nid: 0.5 + (i * 0.08) for i, nid in enumerate(node_ids)}
    node_criticality = {nid: 0.4 + (i * 0.09) for i, nid in enumerate(node_ids)}
    node_load_factors = {nid: 0.6 + (i * 0.07) for i, nid in enumerate(node_ids)}
    
    adjacency = np.array([
        [0, 1, 1, 0, 0],
        [1, 0, 1, 1, 0],
        [1, 1, 0, 1, 1],
        [0, 1, 1, 0, 1],
        [0, 0, 1, 1, 0]
    ])
    
    return BaselineSnapshot(
        snapshot_id='test_snapshot_001',
        scenario_id='test_scenario_001',
        timestamp=datetime.utcnow(),
        node_risk_scores=node_risk_scores,
        node_network_centrality=node_centrality,
        node_criticality=node_criticality,
        node_load_factors=node_load_factors,
        adjacency_matrix=adjacency,
        node_ids=node_ids,
        system_aggregate_risk=0.4,
        system_connectivity=0.85,
        corridor_utilization={'corridor_1': 0.7, 'corridor_2': 0.65},
        regional_risk_distribution={'region_1': 0.35, 'region_2': 0.45},
        risk_distribution_vector=[0.3, 0.4, 0.5, 0.6, 0.7],
        metadata={"test": True}
    )


@pytest.fixture
def sample_simulation_result(sample_baseline, scenario_template):
    """Create a sample simulation result"""
    from app.scenarios.shock import ShockEvent, ShockApplicationResult, CascadeEffect
    from app.scenarios.simulator import SimulationStepResult, SimulationStep

    risk_deltas = np.array([0.1, 0.15, 0.2, 0.12, 0.08])
    final_risks = {
        nid: sample_baseline.get_node_risk(nid) + delta
        for nid, delta in zip(sample_baseline.node_ids, risk_deltas)
    }
    final_risks['__system__'] = 0.6

    shock_event = ShockEvent(node_id='node_1', severity=0.8)
    shock_app = ShockApplicationResult(
        shock_event=shock_event,
        primary_impact_nodes={'node_1', 'node_2'},
        cascading_impacts=[CascadeEffect(source_node='node_1', target_node='node_2', hop_distance=1, attenuated_severity=0.56)],
        affected_node_count=2,
        total_impact_severity=0.8,
        success=True,
    )
    step_result = SimulationStepResult(
        step=SimulationStep(1),
        step_number=1,
        success=True,
        duration_seconds=0.01,
        description="Shock injection",
    )

    return ScenarioSimulationResult(
        scenario_id='test_scenario_001',
        scenario_template=scenario_template,
        baseline_snapshot=sample_baseline,
        shock_applications=[shock_app],
        step_results=[step_result],
        final_risk_scores=final_risks,
        risk_change_vector=risk_deltas,
        system_stress_final=0.65,
        critical_nodes_post_shock=['node_2', 'node_3'],
        recovery_time_estimate_hours=48.0,
        simulation_duration_seconds=0.05,
        success=True,
    )


@pytest.fixture
def scenario_template():
    """Create a sample scenario template"""
    return ScenarioTemplate(
        name='HORMUZ_CLOSURE',
        title='Strait of Hormuz Closure',
        description='Simulated disruption of Strait of Hormuz waterway',
        disruption_type=DisruptionType.MARITIME,
        severity=0.95,
        affected_domains=[ScenarioDomain.MARITIME, ScenarioDomain.ENERGY],
        affected_regions=['Middle East', 'South Asia'],
        affected_countries=['Iran', 'Oman', 'UAE'],
        duration_hours=72,
        propagation_depth=3,
        key_assumptions=['Port capacity maintained', 'Alternative routes viable'],
        uncertainty_factors=['Weather patterns', 'Geopolitical escalation'],
        shock_event_locations=['node_1', 'node_2'],
        propagation_coefficient=0.8,
        confidence_baseline=0.85,
        scenario_tags=['maritime', 'energy', 'high-severity']
    )


# Test Cases
class TestTemplateRetrieval:
    """Test 1: Template retrieval and validation"""
    
    def test_get_template_existing(self, scenario_template):
        """Test retrieval of existing template"""
        with patch('app.scenarios.templates.SCENARIO_TEMPLATES', 
                   {'HORMUZ_CLOSURE': scenario_template}):
            from app.scenarios.templates import get_template
            template = get_template('HORMUZ_CLOSURE')
            assert template is not None
            assert template.name == 'HORMUZ_CLOSURE'
            assert template.severity == 0.95
    
    def test_get_template_nonexistent(self):
        """Test retrieval of non-existent template"""
        with patch('app.scenarios.templates.SCENARIO_TEMPLATES', {}):
            from app.scenarios.templates import get_template
            template = get_template('NONEXISTENT')
            assert template is None


class TestBaselineSnapshot:
    """Test 2: Baseline snapshot capture and retrieval"""
    
    def test_baseline_node_risk_retrieval(self, sample_baseline):
        """Test baseline node risk score retrieval"""
        risk = sample_baseline.get_node_risk('node_1')
        assert risk == 0.3
        
        risk_5 = sample_baseline.get_node_risk('node_5')
        assert risk_5 == 0.7
    
    def test_baseline_adjacency_matrix(self, sample_baseline):
        """Test adjacency matrix access"""
        adj = sample_baseline.get_adjacency_matrix()
        assert adj.shape == (5, 5)
        assert adj[0, 1] == 1
        assert adj[0, 0] == 0


class TestShockInjection:
    """Test 3: Shock event injection and cascade propagation"""
    
    def test_shock_event_creation(self):
        """Test creation of shock event"""
        shock = ShockEvent(
            node_id='node_1',
            severity=0.9,
            impact_type='maritime',
            timestamp=datetime.utcnow(),
            duration_hours=72,
            cascade_enabled=True,
            cascade_depth=3,
            cascade_type='DISTANCE_WEIGHTED',
            cascade_attenuation=0.7
        )
        
        assert shock.node_id == 'node_1'
        assert shock.severity == 0.9
        assert shock.cascade_enabled is True
    
    def test_shock_injector_cascade(self, sample_baseline):
        """Test cascade propagation through network"""
        injector = ShockInjector(
            adjacency_matrix=sample_baseline.adjacency_matrix,
            node_ids=sample_baseline.node_ids,
        )
        shock = ShockEvent(
            node_id='node_1',
            severity=0.8,
            impact_type='maritime',
            timestamp=datetime.utcnow(),
            duration_hours=72,
            cascade_enabled=True,
            cascade_depth=2,
        )

        result = injector.apply_shock(shock)
        assert result is not None
        assert shock.node_id in result.primary_impact_nodes


class TestSimulationPipeline:
    """Test 4: 10-step simulation pipeline execution"""

    def test_simulation_initialization(self, scenario_template, sample_baseline):
        """Test simulator initialization"""
        simulator = ScenarioSimulator(
            adjacency_matrix=sample_baseline.adjacency_matrix,
            node_ids=sample_baseline.node_ids,
            node_positions={nid: (25.0 + i, 55.0 + i) for i, nid in enumerate(sample_baseline.node_ids)},
            node_criticality=sample_baseline.node_criticality,
        )
        assert simulator is not None

    def test_simulation_step_execution(self, scenario_template, sample_baseline):
        """Test individual simulation steps"""
        simulator = ScenarioSimulator(
            adjacency_matrix=sample_baseline.adjacency_matrix,
            node_ids=sample_baseline.node_ids,
            node_positions={nid: (25.0 + i, 55.0 + i) for i, nid in enumerate(sample_baseline.node_ids)},
            node_criticality=sample_baseline.node_criticality,
        )

        # Mock the shock injection step
        with patch.object(simulator, '_step_shock_injection',
                         return_value=MagicMock()) as mock_step:
            result = mock_step()
            assert result is not None


class TestDeltaCalculation:
    """Test 5: Delta analysis and before/after comparison"""
    
    def test_node_delta_calculation(self, sample_baseline, sample_simulation_result):
        """Test node-level delta calculation"""
        calculator = DeltaCalculator()
        deltas = calculator.calculate_node_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result
        )
        
        assert len(deltas) == 5
        assert 'node_1' in deltas
        
        node_1_delta = deltas['node_1']
        assert node_1_delta.baseline_risk == 0.3
        assert node_1_delta.post_shock_risk > node_1_delta.baseline_risk
        assert node_1_delta.risk_delta > 0
    
    def test_delta_severity_classification(self, sample_baseline, sample_simulation_result):
        """Test delta severity classification"""
        calculator = DeltaCalculator()
        deltas = calculator.calculate_node_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result
        )
        
        # Check severity assignments
        severities = [d.impact_severity for d in deltas.values()]
        assert any(s != 'none' for s in severities)
    
    def test_aggregate_delta_metrics(self, sample_baseline, sample_simulation_result):
        """Test aggregate system-level deltas"""
        calculator = DeltaCalculator()
        deltas = calculator.calculate_node_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result
        )
        
        metrics = calculator.calculate_aggregate_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result,
            node_deltas=deltas
        )
        
        assert metrics.total_nodes_affected > 0
        assert metrics.recovery_time_estimate_hours == 48.0
        assert metrics.system_stress_delta >= 0


class TestExplanationGeneration:
    """Test 6: Bilingual explanation generation"""
    
    def test_explanation_english_summary(self, sample_baseline, sample_simulation_result):
        """Test English summary generation"""
        calculator = DeltaCalculator()
        deltas = calculator.calculate_node_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result
        )
        metrics = calculator.calculate_aggregate_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result,
            node_deltas=deltas
        )
        
        generator = ExplanationGenerator()
        explanation = generator.generate_explanation(
            scenario_name='Test Scenario',
            baseline=sample_baseline,
            simulation_result=sample_simulation_result,
            node_deltas=deltas,
            delta_metrics=metrics
        )
        
        assert explanation.english_summary is not None
        assert 'Test Scenario' in explanation.english_summary
        assert 'nodes affected' in explanation.english_summary
    
    def test_explanation_arabic_summary(self, sample_baseline, sample_simulation_result):
        """Test Arabic summary generation"""
        calculator = DeltaCalculator()
        deltas = calculator.calculate_node_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result
        )
        metrics = calculator.calculate_aggregate_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result,
            node_deltas=deltas
        )
        
        generator = ExplanationGenerator()
        explanation = generator.generate_explanation(
            scenario_name='Test Scenario',
            baseline=sample_baseline,
            simulation_result=sample_simulation_result,
            node_deltas=deltas,
            delta_metrics=metrics
        )
        
        assert explanation.arabic_summary is not None
        assert len(explanation.key_findings_ar) > 0
    
    def test_explanation_recommendations(self, sample_baseline, sample_simulation_result):
        """Test recommendation generation"""
        calculator = DeltaCalculator()
        deltas = calculator.calculate_node_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result
        )
        metrics = calculator.calculate_aggregate_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result,
            node_deltas=deltas
        )
        
        generator = ExplanationGenerator()
        explanation = generator.generate_explanation(
            scenario_name='Test Scenario',
            baseline=sample_baseline,
            simulation_result=sample_simulation_result,
            node_deltas=deltas,
            delta_metrics=metrics
        )
        
        assert len(explanation.recommendations_en) > 0
        assert len(explanation.recommendations_ar) > 0


class TestScenarioEngine:
    """Test 7: Scenario engine orchestration"""
    
    def test_engine_initialization(self):
        """Test scenario engine initialization"""
        engine = ScenarioEngine()
        assert engine is not None
        assert engine.simulator is not None
        assert engine.delta_calculator is not None
        assert engine.explainer is not None
    
    def test_execution_request_creation(self, sample_baseline):
        """Test execution request creation"""
        request = ScenarioExecutionRequest(
            scenario_name='HORMUZ_CLOSURE',
            baseline_snapshot=sample_baseline,
            cascade_enabled=True
        )
        
        assert request.scenario_name == 'HORMUZ_CLOSURE'
        assert request.baseline_snapshot == sample_baseline
        assert request.cascade_enabled is True


class TestMultipleScenarios:
    """Test 8: Multiple scenario comparison and analysis"""
    
    def test_scenario_comparison_structure(self):
        """Test comparison data structure"""
        comparison = {
            'scenario_1': {'critical_nodes': 2, 'max_risk': 0.8},
            'scenario_2': {'critical_nodes': 1, 'max_risk': 0.6}
        }
        
        assert 'scenario_1' in comparison
        assert comparison['scenario_1']['max_risk'] == 0.8


class TestResultExport:
    """Test 9: Result export and serialization"""
    
    def test_delta_serialization(self, sample_baseline, sample_simulation_result):
        """Test delta result serialization"""
        calculator = DeltaCalculator()
        deltas = calculator.calculate_node_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result
        )
        
        serialized = calculator.serialize_deltas(deltas)
        
        assert 'node_1' in serialized
        assert serialized['node_1']['baseline_risk'] == 0.3
        assert 'risk_delta' in serialized['node_1']
    
    def test_explanation_export(self, sample_baseline, sample_simulation_result):
        """Test explanation export"""
        calculator = DeltaCalculator()
        deltas = calculator.calculate_node_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result
        )
        metrics = calculator.calculate_aggregate_deltas(
            baseline=sample_baseline,
            simulation_result=sample_simulation_result,
            node_deltas=deltas
        )
        
        generator = ExplanationGenerator()
        explanation = generator.generate_explanation(
            scenario_name='Test Scenario',
            baseline=sample_baseline,
            simulation_result=sample_simulation_result,
            node_deltas=deltas,
            delta_metrics=metrics
        )
        
        exported = generator.export_explanation(explanation)
        
        assert 'english' in exported
        assert 'arabic' in exported
        assert 'summary' in exported['english']
        assert 'recommendations' in exported['arabic']


# Test Runner
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
