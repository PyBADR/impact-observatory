"""GCC-tuned graph propagation with exact shockwave equation.

Shockwave propagation:
    R(t+1) = α*A*R(t) + β*S(t) + δ*E

Where:
    α = 0.58  (adjacency propagation)
    β = 0.92  (shock sensitivity)
    δ = 0.47  (external perturbation)
    A = weighted adjacency matrix
    S = shock vector
    E = external event vector

Pressure accumulation:
    C_i(t+1) = ρ*C_i(t) + κ*Inflow - ω*Outflow + ξ*Shock

Where:
    ρ = 0.72  (persistence)
    κ = 0.18  (inflow coefficient)
    ω = 0.14  (outflow coefficient)
    ξ = 0.30  (shock coefficient)
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import (
    SHOCKWAVE,
    PRESSURE,
    ShockwaveParams,
    PressureParams,
)


@dataclass
class PropagationResult:
    """Result of multi-step propagation."""
    final_state: NDArray[np.float64]
    steps: int
    converged: bool
    energy_history: list[float]
    peak_risk: float
    peak_node_index: int


@dataclass
class PressureResult:
    """Result of pressure accumulation."""
    pressure_state: NDArray[np.float64]
    steps: int
    peak_pressure: float
    peak_node_index: int
    congestion_nodes: list[int]  # indices where pressure > threshold


def propagation_step(
    adjacency: NDArray[np.float64],
    risk_state: NDArray[np.float64],
    shock: NDArray[np.float64],
    external: NDArray[np.float64] | None = None,
    params: ShockwaveParams | None = None,
) -> NDArray[np.float64]:
    """Single propagation step: R(t+1) = α*A*R(t) + β*S(t) + δ*E"""
    p = params or SHOCKWAVE
    ext = external if external is not None else np.zeros_like(risk_state)

    next_state = p.alpha * (adjacency @ risk_state) + p.beta * shock + p.delta * ext
    return np.clip(next_state, 0.0, 1.0)


def propagate_multi_step(
    adjacency: NDArray[np.float64],
    initial_risk: NDArray[np.float64],
    shock: NDArray[np.float64],
    external: NDArray[np.float64] | None = None,
    max_steps: int = 20,
    convergence_threshold: float = 1e-4,
    params: ShockwaveParams | None = None,
) -> PropagationResult:
    """Run propagation until convergence or max_steps.

    Convergence = max change in risk vector < threshold.
    """
    p = params or SHOCKWAVE
    state = initial_risk.copy()
    energy_history: list[float] = [float(np.sum(state ** 2))]

    converged = False
    steps = 0

    for step in range(max_steps):
        next_state = propagation_step(adjacency, state, shock, external, p)
        delta = float(np.max(np.abs(next_state - state)))
        state = next_state
        steps = step + 1
        energy_history.append(float(np.sum(state ** 2)))

        # Decay shock after first step
        shock = shock * 0.5

        if delta < convergence_threshold:
            converged = True
            break

    peak_idx = int(np.argmax(state))
    return PropagationResult(
        final_state=state,
        steps=steps,
        converged=converged,
        energy_history=energy_history,
        peak_risk=float(state[peak_idx]),
        peak_node_index=peak_idx,
    )


def pressure_step(
    pressure: NDArray[np.float64],
    inflow: NDArray[np.float64],
    outflow: NDArray[np.float64],
    shock: NDArray[np.float64],
    params: PressureParams | None = None,
) -> NDArray[np.float64]:
    """Single pressure step: C(t+1) = ρ*C(t) + κ*In - ω*Out + ξ*Shock"""
    p = params or PRESSURE
    next_p = p.rho * pressure + p.kappa * inflow - p.omega * outflow + p.xi * shock
    return np.clip(next_p, 0.0, 1.0)


def accumulate_pressure(
    initial_pressure: NDArray[np.float64],
    inflow_series: list[NDArray[np.float64]],
    outflow_series: list[NDArray[np.float64]],
    shock_series: list[NDArray[np.float64]],
    congestion_threshold: float = 0.7,
    params: PressureParams | None = None,
) -> PressureResult:
    """Run pressure accumulation over multiple time steps."""
    p = params or PRESSURE
    state = initial_pressure.copy()
    steps = len(inflow_series)

    for t in range(steps):
        state = pressure_step(state, inflow_series[t], outflow_series[t], shock_series[t], p)

    peak_idx = int(np.argmax(state))
    congestion = [int(i) for i in np.where(state > congestion_threshold)[0]]

    return PressureResult(
        pressure_state=state,
        steps=steps,
        peak_pressure=float(state[peak_idx]) if len(state) > 0 else 0.0,
        peak_node_index=peak_idx,
        congestion_nodes=congestion,
    )


def compute_system_energy(risk_vector: NDArray[np.float64]) -> float:
    """System energy = normalized L2 norm of risk vector."""
    if len(risk_vector) == 0:
        return 0.0
    return float(np.sqrt(np.sum(risk_vector ** 2)) / max(len(risk_vector), 1))


def build_adjacency_matrix(
    node_ids: list[str],
    edges: list[dict],
) -> NDArray[np.float64]:
    """Build weighted adjacency from edge list.

    Each edge: {"source": str, "target": str, "weight": float}
    """
    n = len(node_ids)
    idx = {nid: i for i, nid in enumerate(node_ids)}
    adj = np.zeros((n, n), dtype=np.float64)

    for e in edges:
        src = e.get("source", "")
        tgt = e.get("target", "")
        w = e.get("weight", 1.0)
        if src in idx and tgt in idx:
            adj[idx[src], idx[tgt]] = w
            if not e.get("directed", False):
                adj[idx[tgt], idx[src]] = w

    # Row-normalize to prevent explosion
    row_sums = adj.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    adj = adj / row_sums

    return adj
