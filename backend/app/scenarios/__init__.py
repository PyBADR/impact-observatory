"""
Scenario Engine Module - Phase 6
Complete scenario analysis and simulation framework for Impact Observatory
"""

from app.scenarios.templates import (
    ScenarioTemplate,
    DisruptionType,
    ScenarioDomain,
    SCENARIO_TEMPLATES,
    get_template,
    list_templates,
    get_templates_by_disruption_type,
    get_templates_by_domain
)

from app.scenarios.baseline import (
    BaselineSnapshot,
    BaselineCaptureRequest,
    BaselineCaptureResult
)

from app.scenarios.shock import (
    ShockEvent,
    CascadeEffect,
    ShockApplicationResult,
    ShockInjector
)

from app.scenarios.simulator import (
    SimulationStep,
    SimulationStepResult,
    ScenarioSimulationResult,
    ScenarioSimulator
)

from app.scenarios.delta import (
    NodeDeltaAnalysis,
    DeltaMetrics,
    DeltaCalculator
)

from app.scenarios.explainer import (
    ScenarioExplanation,
    ExplanationGenerator
)

from app.scenarios.engine import (
    ScenarioExecutionRequest,
    ScenarioExecutionResult,
    ScenarioEngine
)

__all__ = [
    # Templates
    'ScenarioTemplate',
    'DisruptionType',
    'ScenarioDomain',
    'SCENARIO_TEMPLATES',
    'get_template',
    'list_templates',
    'get_templates_by_disruption_type',
    'get_templates_by_domain',
    
    # Baseline
    'BaselineSnapshot',
    'BaselineCaptureRequest',
    'BaselineCaptureResult',
    
    # Shock
    'ShockEvent',
    'CascadeEffect',
    'ShockApplicationResult',
    'ShockInjector',
    
    # Simulator
    'SimulationStep',
    'SimulationStepResult',
    'ScenarioSimulationResult',
    'ScenarioSimulator',
    
    # Delta
    'NodeDeltaAnalysis',
    'DeltaMetrics',
    'DeltaCalculator',
    
    # Explainer
    'ScenarioExplanation',
    'ExplanationGenerator',
    
    # Engine
    'ScenarioExecutionRequest',
    'ScenarioExecutionResult',
    'ScenarioEngine'
]
