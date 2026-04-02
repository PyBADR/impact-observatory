"""
Physics-inspired intelligence module for GCC Decision Intelligence Platform.

This module provides computational metaphors grounded in physics:
- Threat fields model spatial threat distribution via Gaussian decay
- Flow fields represent mobility corridors and congestion
- Pressure nodes capture capacity constraints and load redistribution
- Shockwaves model rapid event propagation
- Diffusion models threat spread across regional networks
- Potential fields enable risk-aware routing
- Friction models capture multi-factor route resistance
- System stress aggregates multi-dimensional disruption metrics

GCC Defaults:
All modules use consolidated physics parameters from gcc_physics_config.
Parameters follow Impact Observatory calibration with production
values for threat field, shockwave, pressure, friction, routing, and stress.
"""

from .threat_field import ThreatSource, ThreatField
from .flow_field import FlowVector, FlowField
from .pressure import PressureNode, compute_pressure, accumulate_pressure, system_pressure, accumulate_pressure_dynamics
from .shockwave import ShockEvent, ShockwaveEngine
from .diffusion import diffuse_threat, compute_laplacian, DiffusionResult
from .routing import compute_route_cost, find_lowest_cost_route, RouteResult
from .friction import compute_friction, batch_compute_friction, classify_friction, FrictionClass
from .potential_routing import (
    compute_route_cost as compute_potential_route_cost,
    find_optimal_route,
    compute_threat_integral_along_route,
    OptimalRouteResult,
    ViabilityClass
)
from .system_stress import compute_system_stress, SystemStressResult, StressLevel
from .gcc_physics_config import (
    get_threat_field_config,
    get_shockwave_config,
    get_pressure_config,
    get_friction_config,
    get_routing_config,
    get_stress_config,
    get_all_config
)

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
    "accumulate_pressure_dynamics",
    "system_pressure",
    # Shockwave
    "ShockEvent",
    "ShockwaveEngine",
    # Diffusion
    "diffuse_threat",
    "compute_laplacian",
    "DiffusionResult",
    # Routing (legacy)
    "compute_route_cost",
    "find_lowest_cost_route",
    "RouteResult",
    # Friction
    "compute_friction",
    "batch_compute_friction",
    "classify_friction",
    "FrictionClass",
    # Potential routing (GCC)
    "compute_potential_route_cost",
    "find_optimal_route",
    "compute_threat_integral_along_route",
    "OptimalRouteResult",
    "ViabilityClass",
    # System stress
    "compute_system_stress",
    "SystemStressResult",
    "StressLevel",
    # GCC Configuration
    "get_threat_field_config",
    "get_shockwave_config",
    "get_pressure_config",
    "get_friction_config",
    "get_routing_config",
    "get_stress_config",
    "get_all_config",
]
