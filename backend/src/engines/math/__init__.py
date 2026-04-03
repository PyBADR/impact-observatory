"""Compatibility shim — all exports now live in src.engines.math_core.

Import from math_core directly for new code.
"""
from src.engines.math_core.decay import spatial_decay, temporal_decay
from src.engines.math_core.scoring import (
    composite_risk_score,
    confidence_score,
    disruption_score,
    exposure_score,
)
from src.engines.math_core.propagation_matrix import propagation_step, propagate_multi_step

__all__ = [
    "spatial_decay",
    "temporal_decay",
    "composite_risk_score",
    "confidence_score",
    "disruption_score",
    "exposure_score",
    "propagation_step",
    "propagate_multi_step",
]
