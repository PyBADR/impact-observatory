"""
Mathematical modeling module for GCC Decision Intelligence Platform.

Provides comprehensive risk assessment, spatial/temporal analysis, network propagation,
and exposure modeling for critical infrastructure disruption intelligence.
"""

from .risk import (
    RiskResult,
    compute_risk_score,
)

from .spatial import (
    spatial_decay,
    proximity_score,
    haversine_km,
    influence_field,
)

from .temporal import (
    temporal_decay,
    freshness_score,
    time_weighted_aggregate,
)

from .propagation import (
    PropagationResult,
    propagate_risk,
)

from .exposure import (
    ExposureInput,
    ExposureResult,
    compute_exposure,
    aggregate_exposure,
)

from .disruption import (
    DisruptionResult,
    route_disruption_pressure,
    compute_disruption,
)

from .confidence import (
    ConfidenceResult,
    compute_confidence,
)

__all__ = [
    # Risk
    "RiskResult",
    "compute_risk_score",
    # Spatial
    "spatial_decay",
    "proximity_score",
    "haversine_km",
    "influence_field",
    # Temporal
    "temporal_decay",
    "freshness_score",
    "time_weighted_aggregate",
    # Propagation
    "PropagationResult",
    "propagate_risk",
    # Exposure
    "ExposureInput",
    "ExposureResult",
    "compute_exposure",
    "aggregate_exposure",
    # Disruption
    "DisruptionResult",
    "route_disruption_pressure",
    "compute_disruption",
    # Confidence
    "ConfidenceResult",
    "compute_confidence",
]
