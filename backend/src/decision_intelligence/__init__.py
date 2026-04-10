"""
Decision Intelligence System — transforms Impact Intelligence into executable decisions.

Pipeline: ImpactMap → Triggers → Breakpoints → ActionSim → Counterfactual → ROI → Executive

All engines consume ImpactMapResponse as input. No graph rebuild.
"""
from src.decision_intelligence.trigger_engine import GraphDecisionTrigger, build_graph_triggers
from src.decision_intelligence.breakpoint_engine import Breakpoint, detect_breakpoints
from src.decision_intelligence.action_simulation_engine import ActionSimResult, simulate_action_effects
from src.decision_intelligence.counterfactual_engine import CounterfactualResult, compare_counterfactuals
from src.decision_intelligence.roi_engine import DecisionROI, compute_decision_roi
from src.decision_intelligence.executive_output import ExecutiveDecision, build_executive_decisions
from src.decision_intelligence.pipeline import run_decision_intelligence_pipeline

__all__ = [
    "GraphDecisionTrigger", "build_graph_triggers",
    "Breakpoint", "detect_breakpoints",
    "ActionSimResult", "simulate_action_effects",
    "CounterfactualResult", "compare_counterfactuals",
    "DecisionROI", "compute_decision_roi",
    "ExecutiveDecision", "build_executive_decisions",
    "run_decision_intelligence_pipeline",
]
