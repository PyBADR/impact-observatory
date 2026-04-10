"""GCC-tuned disruption scoring.

D_i(t) = v1*R_i(t) + v2*C_i(t) + v3*A_i(t) + v4*K_i(t) + v5*B_i(t)

Where:
    R = Risk score
    C = Congestion (flow-based)
    A = Accessibility loss
    K = Reroute penalty
    B = Boundary restriction
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import DISRUPTION, DisruptionWeights


@dataclass
class DisruptionBreakdown:
    """Explainable disruption score for one node."""
    node_id: str
    disruption_score: float
    risk_component: float
    congestion_component: float
    accessibility_loss: float
    reroute_penalty: float
    boundary_restriction: float
    dominant_factor: str


def compute_disruption_score(
    node_id: str,
    risk: float,
    congestion: float = 0.0,
    accessibility_loss: float = 0.0,
    reroute_penalty: float = 0.0,
    boundary_restriction: float = 0.0,
    weights: DisruptionWeights | None = None,
) -> DisruptionBreakdown:
    """D_i(t) = v1*R + v2*C + v3*A + v4*K + v5*B"""
    w = weights or DISRUPTION

    components = {
        "risk": (risk, w.risk),
        "congestion": (congestion, w.congestion),
        "accessibility_loss": (accessibility_loss, w.accessibility_loss),
        "reroute_penalty": (reroute_penalty, w.reroute_penalty),
        "boundary_restriction": (boundary_restriction, w.boundary_restriction),
    }

    score = sum(
        float(np.clip(val, 0.0, 1.0)) * wt
        for val, wt in components.values()
    )
    score = float(np.clip(score, 0.0, 1.0))

    weighted = {k: v * wt for k, (v, wt) in components.items()}
    dominant = max(weighted, key=weighted.get)

    return DisruptionBreakdown(
        node_id=node_id,
        disruption_score=score,
        risk_component=risk,
        congestion_component=congestion,
        accessibility_loss=accessibility_loss,
        reroute_penalty=reroute_penalty,
        boundary_restriction=boundary_restriction,
        dominant_factor=dominant,
    )


def compute_disruption_vector(
    node_ids: list[str],
    risk_vector: NDArray[np.float64],
    congestion_vector: NDArray[np.float64] | None = None,
    accessibility_vector: NDArray[np.float64] | None = None,
    reroute_vector: NDArray[np.float64] | None = None,
    boundary_vector: NDArray[np.float64] | None = None,
) -> tuple[NDArray[np.float64], list[DisruptionBreakdown]]:
    """Batch disruption scoring for all nodes."""
    n = len(node_ids)
    cong = congestion_vector if congestion_vector is not None else np.zeros(n)
    acc = accessibility_vector if accessibility_vector is not None else np.zeros(n)
    rer = reroute_vector if reroute_vector is not None else np.zeros(n)
    bnd = boundary_vector if boundary_vector is not None else np.zeros(n)

    breakdowns = []
    for i, nid in enumerate(node_ids):
        bd = compute_disruption_score(
            nid, risk_vector[i], cong[i], acc[i], rer[i], bnd[i]
        )
        breakdowns.append(bd)

    vector = np.array([b.disruption_score for b in breakdowns], dtype=np.float64)
    return vector, breakdowns
