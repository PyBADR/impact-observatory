"""
OPA-style internal policy engine for Deevo Decision Intelligence.

Three policy domains:
  - scenario_policy: Validates scenario context, determines canonical type
  - action_policy:   Filters/scores actions based on scenario type + urgency
  - executive_policy: Dynamic executive classification with scenario-type awareness
"""

from src.policies.scenario_policy import PolicyContext, PolicyDecision, evaluate_scenario_policy
from src.policies.action_policy import evaluate_action_policy, ActionPolicyResult
from src.policies.executive_policy import evaluate_executive_policy, ExecutivePolicyResult

__all__ = [
    "PolicyContext",
    "PolicyDecision",
    "evaluate_scenario_policy",
    "evaluate_action_policy",
    "ActionPolicyResult",
    "evaluate_executive_policy",
    "ExecutivePolicyResult",
]
