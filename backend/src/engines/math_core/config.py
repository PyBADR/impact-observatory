"""Configuration constants for mathematical models.

All magic numbers are centralized here for auditability.
"""

from pydantic import BaseModel, Field


class DecayConfig(BaseModel):
    spatial_lambda: float = Field(default=0.005, description="Spatial decay rate (per km)")
    temporal_gamma: float = Field(default=0.01, description="Temporal decay rate (per hour)")


class RiskWeights(BaseModel):
    event_severity: float = 0.25
    source_confidence: float = 0.10
    spatial_proximity: float = 0.15
    network_centrality: float = 0.10
    route_dependency: float = 0.15
    temporal_recency: float = 0.10
    congestion_pressure: float = 0.08
    exposure_sensitivity: float = 0.07


class PropagationConfig(BaseModel):
    alpha: float = Field(default=0.6, description="Propagation coefficient (adjacency)")
    beta: float = Field(default=0.3, description="Shock sensitivity coefficient")
    epsilon: float = Field(default=0.01, description="Noise / baseline drift")
    max_steps: int = Field(default=10, description="Maximum propagation iterations")
    convergence_threshold: float = Field(
        default=1e-4, description="Stop when max delta < threshold"
    )
    damping: float = Field(default=0.15, description="Per-step damping factor")


class DisruptionWeights(BaseModel):
    risk: float = 0.30
    reroute_cost: float = 0.20
    delay_cost: float = 0.20
    congestion: float = 0.15
    uncertainty: float = 0.15


class ExposureConfig(BaseModel):
    value_weight: float = 0.4
    dependency_weight: float = 0.35
    criticality_weight: float = 0.25


# Singletons
DECAY = DecayConfig()
RISK_WEIGHTS = RiskWeights()
PROPAGATION = PropagationConfig()
DISRUPTION_WEIGHTS = DisruptionWeights()
EXPOSURE = ExposureConfig()
