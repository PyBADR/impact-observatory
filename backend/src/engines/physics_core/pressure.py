"""GCC-tuned pressure accumulation — dynamic pressure with exact rho/kappa/omega/xi.

Uses PressureParams (rho=0.72, kappa=0.18, omega=0.14, xi=0.30) from gcc_weights.

Pressure update rule:
    P(t+1) = rho * P(t) + kappa * inflow - omega * outflow + xi * shock

Returns pressure state with congestion detection and explainability.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import (
    PRESSURE,
    PressureParams,
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class NodePressureState:
    """Pressure state for a single node."""
    node_id: str
    pressure: float
    previous_pressure: float
    inflow_contribution: float
    outflow_contribution: float
    shock_contribution: float
    persistence_contribution: float
    is_congested: bool
    congestion_severity: str  # "none", "mild", "moderate", "severe", "critical"


@dataclass
class GCCPressureResult:
    """Full pressure computation result."""
    node_pressures: dict[str, NodePressureState]
    mean_pressure: float
    max_pressure: float
    congested_nodes: list[str]
    critical_nodes: list[str]
    system_congestion_ratio: float
    params_used: dict[str, float]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _classify_congestion(pressure: float) -> tuple[bool, str]:
    """Classify congestion severity from pressure value."""
    if pressure >= 0.85:
        return True, "critical"
    if pressure >= 0.65:
        return True, "severe"
    if pressure >= 0.45:
        return True, "moderate"
    if pressure >= 0.25:
        return False, "mild"
    return False, "none"


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_gcc_pressure(
    nodes: list[str],
    inflow: dict[str, float],
    outflow: dict[str, float],
    shocks: dict[str, float] | None = None,
    previous_pressure: dict[str, float] | None = None,
    params: PressureParams | None = None,
    congestion_threshold: float = 0.45,
) -> GCCPressureResult:
    """Compute GCC-tuned pressure for a set of nodes using the recurrence relation.

    P(t+1) = rho * P(t) + kappa * inflow - omega * outflow + xi * shock

    Args:
        nodes: List of node IDs.
        inflow: {node_id: normalized inflow [0, 1+]}
        outflow: {node_id: normalized outflow [0, 1+]}
        shocks: {node_id: shock amplitude [0, 1]} optional external shocks.
        previous_pressure: {node_id: P(t)} previous pressure state. If None, starts at 0.
        params: PressureParams override (default: GCC singleton).
        congestion_threshold: pressure above which a node is flagged.

    Returns:
        GCCPressureResult with per-node pressure, congestion detection.
    """
    p = params or PRESSURE
    shock_map = shocks or {}
    prev = previous_pressure or {}

    node_pressures: dict[str, NodePressureState] = {}
    pressure_values: list[float] = []
    congested: list[str] = []
    critical: list[str] = []

    for nid in nodes:
        p_prev = prev.get(nid, 0.0)
        inf = inflow.get(nid, 0.0)
        out = outflow.get(nid, 0.0)
        shock = shock_map.get(nid, 0.0)

        # GCC pressure recurrence
        persistence_term = p.rho * p_prev
        inflow_term = p.kappa * inf
        outflow_term = p.omega * out
        shock_term = p.xi * shock

        new_pressure = persistence_term + inflow_term - outflow_term + shock_term
        new_pressure = float(np.clip(new_pressure, 0.0, 1.0))

        is_congested, severity = _classify_congestion(new_pressure)

        node_pressures[nid] = NodePressureState(
            node_id=nid,
            pressure=new_pressure,
            previous_pressure=p_prev,
            inflow_contribution=inflow_term,
            outflow_contribution=outflow_term,
            shock_contribution=shock_term,
            persistence_contribution=persistence_term,
            is_congested=is_congested,
            congestion_severity=severity,
        )

        pressure_values.append(new_pressure)
        if is_congested:
            congested.append(nid)
        if severity == "critical":
            critical.append(nid)

    arr = np.array(pressure_values) if pressure_values else np.array([0.0])
    n_total = max(len(nodes), 1)

    return GCCPressureResult(
        node_pressures=node_pressures,
        mean_pressure=float(np.mean(arr)),
        max_pressure=float(np.max(arr)),
        congested_nodes=congested,
        critical_nodes=critical,
        system_congestion_ratio=len(congested) / n_total,
        params_used={
            "rho_persistence": p.rho,
            "kappa_inflow": p.kappa,
            "omega_outflow": p.omega,
            "xi_shock": p.xi,
        },
    )
