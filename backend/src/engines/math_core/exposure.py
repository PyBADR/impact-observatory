"""GCC-tuned exposure scoring.

Exposure measures how much a node's disruption affects the broader system,
combining network centrality, economic value, and dependency chains.

E_i = α1*betweenness + α2*degree + α3*flow_share + α4*chokepoint_dep
      + gdp_weight * economic_value

GDP loss estimation:
    ΔY_i(t) = GDP_i * elasticity * D_i(t) * (1 + cascading_multiplier * Σ_j(A_ij * D_j))
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import CENTRALITY, CentralityWeights


@dataclass
class ExposureBreakdown:
    """Explainable exposure for one node."""
    node_id: str
    exposure_score: float
    betweenness_contrib: float
    degree_contrib: float
    flow_share_contrib: float
    chokepoint_contrib: float
    economic_value: float
    gdp_loss_estimate_usd: float
    classification: str  # CRITICAL / HIGH / MODERATE / LOW


# Default GDP values for GCC nodes (USD billions, approximate)
GCC_GDP_DEFAULTS: dict[str, float] = {
    "saudi_arabia": 1_061e9,
    "uae": 507e9,
    "qatar": 219e9,
    "kuwait": 164e9,
    "bahrain": 44e9,
    "oman": 104e9,
}

DEFAULT_ELASTICITY = 0.015  # 1.5% GDP impact per unit disruption


def compute_exposure(
    node_id: str,
    betweenness: float = 0.0,
    degree: float = 0.0,
    flow_share: float = 0.0,
    chokepoint_dependency: float = 0.0,
    economic_value_usd: float = 0.0,
    disruption: float = 0.0,
    gdp_base_usd: float = 0.0,
    elasticity: float = DEFAULT_ELASTICITY,
    cascading_impact: float = 0.0,
    weights: CentralityWeights | None = None,
) -> ExposureBreakdown:
    """Compute node exposure combining network position and economic value."""
    w = weights or CENTRALITY

    network_score = (
        w.betweenness * np.clip(betweenness, 0, 1)
        + w.degree * np.clip(degree, 0, 1)
        + w.flow_share * np.clip(flow_share, 0, 1)
        + w.chokepoint_dependency * np.clip(chokepoint_dependency, 0, 1)
    )

    # Normalize economic value to [0,1] using max GCC GDP as reference
    max_gdp = max(GCC_GDP_DEFAULTS.values()) if GCC_GDP_DEFAULTS else 1e12
    econ_norm = min(economic_value_usd / max_gdp, 1.0) if max_gdp > 0 else 0.0

    exposure = float(np.clip(0.7 * network_score + 0.3 * econ_norm, 0.0, 1.0))

    # GDP loss: ΔY = GDP * elasticity * D * (1 + cascade)
    gdp_loss = gdp_base_usd * elasticity * disruption * (1.0 + cascading_impact)

    if exposure >= 0.7:
        classification = "CRITICAL"
    elif exposure >= 0.5:
        classification = "HIGH"
    elif exposure >= 0.3:
        classification = "MODERATE"
    else:
        classification = "LOW"

    return ExposureBreakdown(
        node_id=node_id,
        exposure_score=exposure,
        betweenness_contrib=w.betweenness * betweenness,
        degree_contrib=w.degree * degree,
        flow_share_contrib=w.flow_share * flow_share,
        chokepoint_contrib=w.chokepoint_dependency * chokepoint_dependency,
        economic_value=econ_norm,
        gdp_loss_estimate_usd=gdp_loss,
        classification=classification,
    )


def compute_cascading_gdp_loss(
    adjacency: NDArray[np.float64],
    disruption_vector: NDArray[np.float64],
    gdp_values: NDArray[np.float64],
    elasticity: float = DEFAULT_ELASTICITY,
) -> NDArray[np.float64]:
    """ΔY_i = GDP_i * elasticity * D_i * (1 + Σ_j A_ij * D_j)

    Vectorized GDP loss with cascading effects.
    """
    cascade = adjacency @ disruption_vector
    loss = gdp_values * elasticity * disruption_vector * (1.0 + cascade)
    return loss
