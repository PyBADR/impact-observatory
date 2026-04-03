"""Composite scoring functions for risk, disruption, exposure, and confidence.

Every score returns a value in [0, 1] plus a list of factor explanations.
"""

from __future__ import annotations

import numpy as np

from src.engines.math_core.config import (
    DISRUPTION_WEIGHTS,
    EXPOSURE,
    RISK_WEIGHTS,
)
from src.models.canonical import ScoreExplanation


def composite_risk_score(
    event_severity: float,
    source_confidence: float,
    spatial_proximity: float,
    network_centrality: float,
    route_dependency: float,
    temporal_recency: float,
    congestion_pressure: float,
    exposure_sensitivity: float,
    weights: RISK_WEIGHTS.__class__ | None = None,
) -> tuple[float, list[ScoreExplanation]]:
    """Weighted linear combination of risk factors.

    Risk_i(t) = Σ (w_k * factor_k), clamped to [0, 1].

    Returns:
        (score, explanations)
    """
    w = weights or RISK_WEIGHTS
    factors = {
        "event_severity": (event_severity, w.event_severity),
        "source_confidence": (source_confidence, w.source_confidence),
        "spatial_proximity": (spatial_proximity, w.spatial_proximity),
        "network_centrality": (network_centrality, w.network_centrality),
        "route_dependency": (route_dependency, w.route_dependency),
        "temporal_recency": (temporal_recency, w.temporal_recency),
        "congestion_pressure": (congestion_pressure, w.congestion_pressure),
        "exposure_sensitivity": (exposure_sensitivity, w.exposure_sensitivity),
    }

    total = 0.0
    explanations: list[ScoreExplanation] = []

    for name, (value, weight) in factors.items():
        contribution = float(np.clip(value, 0.0, 1.0) * weight)
        total += contribution
        explanations.append(
            ScoreExplanation(
                factor=name,
                weight=weight,
                contribution=contribution,
                detail=f"{name}={value:.3f} × weight={weight:.3f} → {contribution:.4f}",
            )
        )

    score = float(np.clip(total, 0.0, 1.0))
    return score, explanations


def disruption_score(
    risk: float,
    reroute_cost: float,
    delay_cost: float,
    congestion: float,
    uncertainty: float,
    weights: DISRUPTION_WEIGHTS.__class__ | None = None,
) -> tuple[float, list[ScoreExplanation]]:
    """Composite disruption score.

    DisruptionScore = f(risk, reroute_cost, delay_cost, congestion, uncertainty)
    """
    w = weights or DISRUPTION_WEIGHTS
    factors = {
        "risk": (risk, w.risk),
        "reroute_cost": (reroute_cost, w.reroute_cost),
        "delay_cost": (delay_cost, w.delay_cost),
        "congestion": (congestion, w.congestion),
        "uncertainty": (uncertainty, w.uncertainty),
    }

    total = 0.0
    explanations: list[ScoreExplanation] = []

    for name, (value, weight) in factors.items():
        contribution = float(np.clip(value, 0.0, 1.0) * weight)
        total += contribution
        explanations.append(
            ScoreExplanation(
                factor=name,
                weight=weight,
                contribution=contribution,
                detail=f"{name}={value:.3f} × weight={weight:.3f} → {contribution:.4f}",
            )
        )

    score = float(np.clip(total, 0.0, 1.0))
    return score, explanations


def exposure_score(
    value_at_risk: float,
    dependency_weight: float,
    operational_criticality: float,
    cfg: EXPOSURE.__class__ | None = None,
) -> tuple[float, list[ScoreExplanation]]:
    """Exposure(asset) = value_at_risk * dep_w * op_crit (weighted blend).

    All inputs should be normalized to [0, 1].
    """
    c = cfg or EXPOSURE
    raw = (
        c.value_weight * value_at_risk
        + c.dependency_weight * dependency_weight
        + c.criticality_weight * operational_criticality
    )
    score = float(np.clip(raw, 0.0, 1.0))
    explanations = [
        ScoreExplanation(factor="value_at_risk", weight=c.value_weight, contribution=c.value_weight * value_at_risk),
        ScoreExplanation(factor="dependency_weight", weight=c.dependency_weight, contribution=c.dependency_weight * dependency_weight),
        ScoreExplanation(factor="operational_criticality", weight=c.criticality_weight, contribution=c.criticality_weight * operational_criticality),
    ]
    return score, explanations


def confidence_score(
    source_quality: float,
    corroboration_count: int,
    data_freshness: float,
    signal_agreement: float,
) -> tuple[float, list[ScoreExplanation]]:
    """Confidence = weighted function of quality, corroboration, freshness, agreement.

    Corroboration is log-scaled: min(1.0, log2(count+1) / 3).
    """
    corr_norm = float(min(1.0, np.log2(corroboration_count + 1) / 3.0))

    w_quality = 0.30
    w_corr = 0.25
    w_fresh = 0.25
    w_agree = 0.20

    raw = (
        w_quality * source_quality
        + w_corr * corr_norm
        + w_fresh * data_freshness
        + w_agree * signal_agreement
    )
    score = float(np.clip(raw, 0.0, 1.0))
    explanations = [
        ScoreExplanation(factor="source_quality", weight=w_quality, contribution=w_quality * source_quality),
        ScoreExplanation(factor="corroboration", weight=w_corr, contribution=w_corr * corr_norm, detail=f"count={corroboration_count} → norm={corr_norm:.3f}"),
        ScoreExplanation(factor="data_freshness", weight=w_fresh, contribution=w_fresh * data_freshness),
        ScoreExplanation(factor="signal_agreement", weight=w_agree, contribution=w_agree * signal_agreement),
    ]
    return score, explanations
