"""Restructured scenario engine — modular pipeline for GCC scenario simulation.

Pipeline: baseline -> inject -> propagate -> delta -> explain
Mesa: agent-based simulation (optional, requires mesa + networkx)
"""

from src.engines.scenario_engine.baseline import BaselineSnapshot, capture_baseline
from src.engines.scenario_engine.inject import ShockInjection, inject_shock, inject_from_scenario
from src.engines.scenario_engine.runner import ScenarioRunConfig, ScenarioRunResult, run_scenario
from src.engines.scenario_engine.delta import ScenarioDelta, compute_delta, compute_economic_impact
from src.engines.scenario_engine.explanation import ScenarioExplanation, explain_scenario

# Mesa imports are lazy — mesa + networkx are optional runtime dependencies
try:
    from src.engines.scenario_engine.mesa_sim import (
        GCCNodeAgent,
        ConflictAgent,
        FlightAgent,
        VesselAgent,
        LogisticsAgent,
        GCCIntelligenceModel,
        MesaSimulationResult,
        run_mesa_simulation,
    )
except ImportError:
    GCCNodeAgent = None  # type: ignore[assignment,misc]
    ConflictAgent = None  # type: ignore[assignment,misc]
    FlightAgent = None  # type: ignore[assignment,misc]
    VesselAgent = None  # type: ignore[assignment,misc]
    LogisticsAgent = None  # type: ignore[assignment,misc]
    GCCIntelligenceModel = None  # type: ignore[assignment,misc]
    MesaSimulationResult = None  # type: ignore[assignment,misc]
    run_mesa_simulation = None  # type: ignore[assignment]

__all__ = [
    "BaselineSnapshot",
    "capture_baseline",
    "ShockInjection",
    "inject_shock",
    "inject_from_scenario",
    "ScenarioRunConfig",
    "ScenarioRunResult",
    "run_scenario",
    "ScenarioDelta",
    "compute_delta",
    "compute_economic_impact",
    "ScenarioExplanation",
    "explain_scenario",
    "GCCNodeAgent",
    "ConflictAgent",
    "FlightAgent",
    "VesselAgent",
    "LogisticsAgent",
    "GCCIntelligenceModel",
    "MesaSimulationResult",
    "run_mesa_simulation",
]
