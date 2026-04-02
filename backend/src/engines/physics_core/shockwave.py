"""GCC-tuned shockwave propagation — network cascade with exact alpha/beta/delta.

Uses ShockwaveParams (alpha=0.58, beta=0.92, delta=0.47) from gcc_weights.

Propagation rule per time step:
    R(t+1) = alpha * A_norm^T @ R(t) + beta * S(t) + delta * E(t)

where A_norm is the row-normalized adjacency matrix, S is the shock vector,
and E is the external perturbation vector.

Returns propagation result with full energy history.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import (
    SHOCKWAVE,
    ShockwaveParams,
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class NodeShockState:
    """Final shockwave state for a single node."""
    node_index: int
    peak_amplitude: float
    final_amplitude: float
    time_to_peak: int
    was_directly_shocked: bool


@dataclass
class GCCShockwaveResult:
    """Full shockwave propagation result."""
    node_states: list[NodeShockState]
    peak_amplitudes: NDArray[np.float64]
    final_state: NDArray[np.float64]
    energy_history: list[float]
    amplitude_history: list[NDArray[np.float64]]
    n_steps: int
    total_energy_injected: float
    total_energy_final: float
    params_used: dict[str, float]


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def propagate_gcc_shockwave(
    adjacency: NDArray[np.float64],
    risk_state: NDArray[np.float64],
    shock: NDArray[np.float64] | None = None,
    external: NDArray[np.float64] | None = None,
    n_steps: int = 10,
    params: ShockwaveParams | None = None,
) -> GCCShockwaveResult:
    """Propagate a shockwave through a network using GCC coefficients.

    R(t+1) = clip(alpha * A_norm^T @ R(t) + beta * S(t) + delta * E(t), 0, 1)

    After the initial step, S and E decay by 50% each step (impulse response).

    Args:
        adjacency: (N, N) adjacency matrix (weighted or binary).
        risk_state: (N,) initial risk state vector.
        shock: (N,) shock impulse vector (one-time injections). Defaults to zeros.
        external: (N,) external perturbation vector. Defaults to zeros.
        n_steps: Number of propagation time steps.
        params: ShockwaveParams override (default: GCC singleton).

    Returns:
        GCCShockwaveResult with energy history and per-node peak analysis.
    """
    sp = params or SHOCKWAVE
    n = adjacency.shape[0]

    # Defaults
    if shock is None:
        shock = np.zeros(n, dtype=np.float64)
    if external is None:
        external = np.zeros(n, dtype=np.float64)

    # Row-normalize adjacency
    row_sums = adjacency.sum(axis=1, keepdims=True)
    row_sums = np.where(row_sums == 0, 1.0, row_sums)
    a_norm = adjacency / row_sums

    # Track which nodes received direct shocks
    directly_shocked = shock > 0.0

    # Initialize state
    r = risk_state.copy().astype(np.float64)
    s = shock.copy().astype(np.float64)
    e = external.copy().astype(np.float64)

    amplitude_history: list[NDArray[np.float64]] = [r.copy()]
    energy_history: list[float] = [float(np.sum(r ** 2))]

    total_energy_injected = float(np.sum(shock) + np.sum(external))

    # Peak tracking
    peak_amplitudes = r.copy()
    time_to_peak = np.zeros(n, dtype=np.int64)

    for t in range(1, n_steps + 1):
        # GCC propagation rule
        propagated = sp.alpha * (a_norm.T @ r)
        shock_term = sp.beta * s
        external_term = sp.delta * e

        r_new = propagated + shock_term + external_term
        r_new = np.clip(r_new, 0.0, 1.0)

        # Update peak tracking
        improved = r_new > peak_amplitudes
        peak_amplitudes = np.where(improved, r_new, peak_amplitudes)
        time_to_peak = np.where(improved, t, time_to_peak)

        r = r_new
        amplitude_history.append(r.copy())
        energy_history.append(float(np.sum(r ** 2)))

        # Decay impulse sources (shock and external are transient)
        s *= 0.5
        e *= 0.5

    # Build per-node states
    node_states: list[NodeShockState] = []
    for i in range(n):
        node_states.append(NodeShockState(
            node_index=i,
            peak_amplitude=float(peak_amplitudes[i]),
            final_amplitude=float(r[i]),
            time_to_peak=int(time_to_peak[i]),
            was_directly_shocked=bool(directly_shocked[i]),
        ))

    return GCCShockwaveResult(
        node_states=node_states,
        peak_amplitudes=peak_amplitudes,
        final_state=r,
        energy_history=energy_history,
        amplitude_history=amplitude_history,
        n_steps=n_steps,
        total_energy_injected=total_energy_injected,
        total_energy_final=float(np.sum(r ** 2)),
        params_used={
            "alpha_adjacency": sp.alpha,
            "beta_shock": sp.beta,
            "delta_external": sp.delta,
        },
    )
