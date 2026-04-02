"""Scenario Engine Package
Orchestrates scenario analysis: baseline -> shock -> propagate -> quantify -> decide
"""

from .baseline import compute_baseline
from .inject import inject_shocks
from .delta import compute_delta
from .explanation import generate_explanation
from .runner import run_scenario

__all__ = [
    "compute_baseline",
    "inject_shocks",
    "compute_delta",
    "generate_explanation",
    "run_scenario",
]
