"""
GCC Risk Score Computation.

Implements the canonical risk equation:
    R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U

Where:
    G = geopolitical_threat
    P = proximity_score
    N = network_centrality
    L = logistics_pressure
    T = temporal_persistence
    U = uncertainty
    w1..w6 = per-asset-class GCC weights
"""

from __future__ import annotations

import math
from typing import Optional

from app.intelligence.math_core.gcc_weights import (
    ASSET_CLASS_WEIGHTS,
    AIRPORT_WEIGHTS,
    SIGMOID_OFFSET,
    SIGMOID_SCALE,
)


def compute_gcc_risk_score(
    geopolitical_threat: float,
    proximity_score: float,
    network_centrality: float,
    logistics_pressure: float,
    temporal_persistence: float,
    uncertainty: float,
    asset_class: str = "airport",
    normalize: bool = True,
    regional_multiplier: float = 1.0,
) -> dict:
    """
    Compute GCC-tuned composite risk score.

    R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U

    Args:
        geopolitical_threat: G ∈ [0,1] — event-driven threat level
        proximity_score: P ∈ [0,1] — spatial proximity to threat source
        network_centrality: N ∈ [0,1] — graph centrality of asset
        logistics_pressure: L ∈ [0,1] — supply chain stress
        temporal_persistence: T ∈ [0,1] — temporal decay factor
        uncertainty: U ∈ [0,1] — data quality inverse
        asset_class: one of airport, seaport/port, air_corridor, maritime_corridor, etc.
        normalize: apply sigmoid normalization to final score
        regional_multiplier: GCC regional adjustment (KW=1.05, SA=1.15, AE=1.20, etc.)

    Returns:
        dict with raw_score, normalized_score, components, weights, asset_class
    """
    weights = ASSET_CLASS_WEIGHTS.get(asset_class, AIRPORT_WEIGHTS)
    w1, w2, w3, w4, w5, w6 = weights

    components = [
        geopolitical_threat,
        proximity_score,
        network_centrality,
        logistics_pressure,
        temporal_persistence,
        uncertainty,
    ]

    # Clamp all inputs to [0, 1]
    components = [max(0.0, min(1.0, c)) for c in components]

    # Weighted linear combination
    raw_score = (
        w1 * components[0]
        + w2 * components[1]
        + w3 * components[2]
        + w4 * components[3]
        + w5 * components[4]
        + w6 * components[5]
    )

    # Apply regional multiplier
    raw_score *= regional_multiplier

    # Sigmoid normalization: σ(S * (x - offset))
    if normalize:
        normalized_score = _sigmoid(raw_score, scale=SIGMOID_SCALE, offset=SIGMOID_OFFSET)
    else:
        normalized_score = max(0.0, min(1.0, raw_score))

    # Severity band
    severity = _severity_band(normalized_score)

    return {
        "raw_score": round(raw_score, 6),
        "normalized_score": round(normalized_score, 6),
        "severity": severity,
        "components": {
            "geopolitical_threat": round(components[0], 6),
            "proximity_score": round(components[1], 6),
            "network_centrality": round(components[2], 6),
            "logistics_pressure": round(components[3], 6),
            "temporal_persistence": round(components[4], 6),
            "uncertainty": round(components[5], 6),
        },
        "weights": {
            "w1_geopolitical": w1,
            "w2_proximity": w2,
            "w3_centrality": w3,
            "w4_logistics": w4,
            "w5_temporal": w5,
            "w6_uncertainty": w6,
        },
        "asset_class": asset_class,
        "regional_multiplier": regional_multiplier,
    }


def compute_risk_score_batch(
    entities: list[dict],
    asset_class: str = "airport",
    regional_multiplier: float = 1.0,
) -> list[dict]:
    """Compute risk scores for a batch of entities.

    Each entity dict must have keys: geopolitical_threat, proximity_score,
    network_centrality, logistics_pressure, temporal_persistence, uncertainty.
    """
    results = []
    for entity in entities:
        result = compute_gcc_risk_score(
            geopolitical_threat=entity.get("geopolitical_threat", 0.0),
            proximity_score=entity.get("proximity_score", 0.0),
            network_centrality=entity.get("network_centrality", 0.0),
            logistics_pressure=entity.get("logistics_pressure", 0.0),
            temporal_persistence=entity.get("temporal_persistence", 0.0),
            uncertainty=entity.get("uncertainty", 0.0),
            asset_class=asset_class,
            regional_multiplier=regional_multiplier,
        )
        result["entity_id"] = entity.get("entity_id", "unknown")
        results.append(result)
    return results


def _sigmoid(x: float, scale: float = SIGMOID_SCALE, offset: float = SIGMOID_OFFSET) -> float:
    """Sigmoid normalization: 1 / (1 + exp(-scale * (x - offset/scale)))."""
    z = scale * (x - offset / scale)
    # Clamp to prevent overflow
    z = max(-500.0, min(500.0, z))
    return 1.0 / (1.0 + math.exp(-z))


def _severity_band(score: float) -> str:
    """Map normalized score to severity band."""
    if score >= 0.85:
        return "critical"
    elif score >= 0.65:
        return "high"
    elif score >= 0.40:
        return "medium"
    elif score >= 0.20:
        return "low"
    else:
        return "info"
