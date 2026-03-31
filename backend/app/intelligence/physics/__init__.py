"""
Physics-inspired intelligence module for GCC Decision Intelligence Platform.

This module provides computational metaphors grounded in physics:
- Threat fields model spatial threat distribution via Gaussian decay
- Flow fields represent mobility corridors and congestion
- Pressure nodes capture capacity constraints and load redistribution
- Shockwaves model rapid event propagation
- Diffusion models threat spread across regional networks
- Potential fields enable risk-aware routing
- System stress aggregates multi-dimensional disruption metrics
"""

from .threat_field import ThreatSource, ThreatField
from .flow_field import FlowVector, FlowField
from .pressure import PressureNode, compute_pressure, accumulate_pressure, system_pressure
from .shockwave import ShockEvent, ShockwaveEngine
from .diffusion import diffuse_threat, compute_laplacian, DiffusionResult
from .routing import compute_route_cost, find_lowest_cost_route, RouteResult
from .system_stress import compute_system_stress, SystemStressResult

__all__ = [
    # Threat field
    "ThreatSource",
    "ThreatField",
    # Flow field
    "FlowVector",
    "FlowField",
    # Pressure
    "PressureNode",
    "compute_pressure",
    "accumulate_pressure",
    "system_pressure",
    # Shockwave
    "ShockEvent",
    "ShockwaveEngine",
    # Diffusion
    "diffuse_threat",
    "compute_laplacian",
    "DiffusionResult",
    # Routing
    "compute_route_cost",
    "find_lowest_cost_route",
    "RouteResult",
    # System stress
    "compute_system_stress",
    "SystemStressResult",
]
