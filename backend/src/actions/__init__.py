"""
Action Registry — scenario-type-keyed action library.

Replaces the broken index-based SCENARIO_ACTION_MATRIX + flat _ACTION_TEMPLATES
with a typed, scenario-aware action registry.

Every action declares which scenario types it serves.
No action can leak to a scenario type it doesn't belong to.
"""

from src.actions.action_registry import (
    ActionTemplate,
    SCENARIO_ACTION_REGISTRY,
    get_actions_for_scenario_type,
    get_actions_for_scenario_id,
    ALL_ACTIONS,
)

__all__ = [
    "ActionTemplate",
    "SCENARIO_ACTION_REGISTRY",
    "get_actions_for_scenario_type",
    "get_actions_for_scenario_id",
    "ALL_ACTIONS",
]
