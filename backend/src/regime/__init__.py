"""
Regime Layer — system-state intelligence for the Impact Observatory.

Answers four questions:
  1. Is the system stable, stressed, or in crisis?
  2. What is the probability of transition?
  3. How should current state modify propagation behavior?
  4. When does state + propagation become a decision trigger?

Pipeline position: Signals → RegimeEngine → Graph/Propagation → DecisionTriggers → Outcomes
"""

from src.regime.regime_types import RegimeType, REGIME_DEFINITIONS
from src.regime.regime_engine import (
    classify_regime,
    classify_regime_from_result,
    build_regime_inputs,
    RegimeState,
    RegimeInputs,
)
from src.regime.regime_graph_adapter import (
    apply_regime_to_graph,
    RegimeGraphModifiers,
    compute_regime_adjusted_stress,
    compute_regime_adjusted_transfer,
)
from src.regime.decision_trigger_engine import (
    build_decision_triggers,
    build_decision_triggers_from_regime_state,
    DecisionTrigger,
)

__all__ = [
    "RegimeType",
    "REGIME_DEFINITIONS",
    "classify_regime",
    "classify_regime_from_result",
    "build_regime_inputs",
    "RegimeState",
    "RegimeInputs",
    "apply_regime_to_graph",
    "RegimeGraphModifiers",
    "compute_regime_adjusted_stress",
    "compute_regime_adjusted_transfer",
    "build_decision_triggers",
    "build_decision_triggers_from_regime_state",
    "DecisionTrigger",
]
