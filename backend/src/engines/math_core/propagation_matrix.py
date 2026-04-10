"""Graph-based risk propagation engine.

Core equation:
    R_(t+1) = alpha * A * R_t + beta * S_t + epsilon

Where:
    A = adjacency / influence matrix (weighted, optionally with polarity)
    R_t = current risk vector
    S_t = shock vector (new events injected at time t)
    alpha = propagation coefficient
    beta = shock sensitivity
    epsilon = baseline drift / noise
"""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.config import PROPAGATION, PropagationConfig


def propagation_step(
    adjacency: NDArray[np.float64],
    risk_vector: NDArray[np.float64],
    shock_vector: NDArray[np.float64],
    cfg: PropagationConfig | None = None,
) -> NDArray[np.float64]:
    """Single propagation step.

    Args:
        adjacency: (N, N) weighted adjacency matrix. A[j, i] = influence of j on i.
        risk_vector: (N,) current risk state.
        shock_vector: (N,) external shock injection at this step.
        cfg: Propagation configuration.

    Returns:
        (N,) updated risk vector, clamped to [0, 1].
    """
    c = cfg or PROPAGATION
    r_next = c.alpha * (adjacency @ risk_vector) + c.beta * shock_vector + c.epsilon
    # Apply damping
    r_next = r_next * (1.0 - c.damping)
    return np.clip(r_next, 0.0, 1.0)


def propagate_multi_step(
    adjacency: NDArray[np.float64],
    initial_risk: NDArray[np.float64],
    shock_vector: NDArray[np.float64],
    cfg: PropagationConfig | None = None,
) -> tuple[NDArray[np.float64], int, list[NDArray[np.float64]]]:
    """Run propagation until convergence or max steps.

    Args:
        adjacency: (N, N) weighted adjacency matrix.
        initial_risk: (N,) starting risk state.
        shock_vector: (N,) external shocks (applied only at step 0).
        cfg: Propagation configuration.

    Returns:
        (final_risk, steps_taken, history)
        history includes the initial state at index 0.
    """
    c = cfg or PROPAGATION
    risk = initial_risk.copy()
    history = [risk.copy()]

    for step in range(c.max_steps):
        # Shock decays after first step
        s = shock_vector if step == 0 else np.zeros_like(shock_vector)
        new_risk = propagation_step(adjacency, risk, s, c)

        delta = np.max(np.abs(new_risk - risk))
        risk = new_risk
        history.append(risk.copy())

        if delta < c.convergence_threshold:
            return risk, step + 1, history

    return risk, c.max_steps, history


def build_adjacency_matrix(
    node_ids: list[str],
    edges: list[dict],
) -> NDArray[np.float64]:
    """Build an adjacency matrix from edge list.

    Each edge dict must have: source, target, weight, polarity.
    A[j, i] = weight * polarity means node j influences node i.

    Args:
        node_ids: Ordered list of node identifiers.
        edges: List of dicts with source, target, weight, polarity keys.

    Returns:
        (N, N) adjacency matrix.
    """
    n = len(node_ids)
    idx = {nid: i for i, nid in enumerate(node_ids)}
    adj = np.zeros((n, n), dtype=np.float64)

    for edge in edges:
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        if src in idx and tgt in idx:
            weight = float(edge.get("weight", 0.0))
            polarity = float(edge.get("polarity", 1.0))
            adj[idx[src], idx[tgt]] = weight * polarity

    return adj


def compute_system_energy(risk_vector: NDArray[np.float64]) -> float:
    """E_sys = Σ x_i^2. Normalized by vector length."""
    return float(np.sum(risk_vector ** 2) / max(len(risk_vector), 1))


def compute_system_confidence(risk_vector: NDArray[np.float64]) -> float:
    """C = 1 / (1 + variance(risk_vector))."""
    return float(1.0 / (1.0 + np.var(risk_vector)))


def compute_sector_impacts(
    risk_vector: NDArray[np.float64],
    node_sectors: list[str],
) -> dict[str, float]:
    """S_k = mean(x_i) for each sector k."""
    sector_sums: dict[str, list[float]] = {}
    for i, sector in enumerate(node_sectors):
        sector_sums.setdefault(sector, []).append(float(risk_vector[i]))
    return {k: float(np.mean(v)) for k, v in sector_sums.items()}


def compute_gdp_loss(
    sector_impacts: dict[str, float],
    sector_weights: dict[str, float],
) -> float:
    """GDP_loss = Σ (sector_impact_k × sector_weight_k)."""
    total = 0.0
    for sector, impact in sector_impacts.items():
        w = sector_weights.get(sector, 0.0)
        total += impact * w
    return float(np.clip(total, 0.0, 1.0))
