"""GCC-tuned confidence and uncertainty scoring.

Uncertainty:
    U_i(t) = 1 - (η1*SQ + η2*CV + η3*DF + η4*SA) / (η1 + η2 + η3 + η4)

Confidence:
    Conf_i(t) = 1 - U_i(t)

System confidence is the weighted mean across all nodes, penalizing
nodes with high risk but low confidence.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import UNCERTAINTY, UncertaintyWeights


@dataclass
class ConfidenceBreakdown:
    """Explainable confidence for one node."""
    node_id: str
    confidence: float
    uncertainty: float
    source_quality: float
    cross_validation: float
    data_freshness: float
    signal_agreement: float
    classification: str  # HIGH / MODERATE / LOW / VERY_LOW


def compute_confidence(
    node_id: str,
    source_quality: float = 1.0,
    cross_validation: float = 1.0,
    data_freshness: float = 1.0,
    signal_agreement: float = 1.0,
    weights: UncertaintyWeights | None = None,
) -> ConfidenceBreakdown:
    """U_i = 1 - (η1*SQ + η2*CV + η3*DF + η4*SA) / (η1+η2+η3+η4)"""
    w = weights or UNCERTAINTY
    denom = w.source_quality + w.cross_validation + w.data_freshness + w.signal_agreement

    certainty = (
        w.source_quality * np.clip(source_quality, 0, 1)
        + w.cross_validation * np.clip(cross_validation, 0, 1)
        + w.data_freshness * np.clip(data_freshness, 0, 1)
        + w.signal_agreement * np.clip(signal_agreement, 0, 1)
    ) / denom

    uncertainty = float(np.clip(1.0 - certainty, 0.0, 1.0))
    confidence = 1.0 - uncertainty

    if confidence >= 0.8:
        classification = "HIGH"
    elif confidence >= 0.6:
        classification = "MODERATE"
    elif confidence >= 0.4:
        classification = "LOW"
    else:
        classification = "VERY_LOW"

    return ConfidenceBreakdown(
        node_id=node_id,
        confidence=confidence,
        uncertainty=uncertainty,
        source_quality=source_quality,
        cross_validation=cross_validation,
        data_freshness=data_freshness,
        signal_agreement=signal_agreement,
        classification=classification,
    )


def compute_system_confidence(
    risk_vector: NDArray[np.float64],
    confidence_vector: NDArray[np.float64],
) -> float:
    """Weighted system confidence — nodes under higher risk weight more.

    SysConf = Σ(conf_i * risk_i) / Σ(risk_i)  if any risk > 0
            = mean(conf_i)                       otherwise
    """
    total_risk = risk_vector.sum()
    if total_risk > 0:
        return float(np.dot(confidence_vector, risk_vector) / total_risk)
    return float(np.mean(confidence_vector)) if len(confidence_vector) > 0 else 1.0


def compute_confidence_vector(
    node_ids: list[str],
    source_qualities: NDArray[np.float64] | None = None,
    cross_validations: NDArray[np.float64] | None = None,
    data_freshnesses: NDArray[np.float64] | None = None,
    signal_agreements: NDArray[np.float64] | None = None,
) -> tuple[NDArray[np.float64], list[ConfidenceBreakdown]]:
    """Batch confidence scoring."""
    n = len(node_ids)
    sq = source_qualities if source_qualities is not None else np.ones(n)
    cv = cross_validations if cross_validations is not None else np.ones(n)
    df = data_freshnesses if data_freshnesses is not None else np.ones(n)
    sa = signal_agreements if signal_agreements is not None else np.ones(n)

    breakdowns = []
    for i, nid in enumerate(node_ids):
        bd = compute_confidence(nid, sq[i], cv[i], df[i], sa[i])
        breakdowns.append(bd)

    vector = np.array([b.confidence for b in breakdowns], dtype=np.float64)
    return vector, breakdowns
