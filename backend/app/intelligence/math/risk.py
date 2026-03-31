"""
Base risk scoring model for critical infrastructure disruption assessment.

Implements composite risk scoring incorporating severity, confidence, spatial proximity,
network centrality, dependency, recency, congestion, and exposure sensitivity.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import numpy as np


@dataclass
class RiskResult:
    """
    Result of risk score computation.

    Attributes:
        score: Composite risk score in [0, 1]
        components: Dictionary of individual component scores
        explanation: Human-readable description of risk factors
    """
    score: float
    components: Dict[str, float] = field(default_factory=dict)
    explanation: str = ""

    def __post_init__(self):
        """Validate score is in valid range."""
        if not 0 <= self.score <= 1:
            raise ValueError(f"Risk score must be in [0, 1], got {self.score}")


# Default weight configuration for risk components
DEFAULT_RISK_WEIGHTS = {
    "event_severity": 0.20,           # Event impact magnitude
    "source_confidence": 0.18,         # Source credibility and corroboration
    "spatial_proximity": 0.15,  # Geographic proximity to critical assets
    "network_centrality": 0.15, # Network importance of affected node
    "route_dependency": 0.12,   # Critical route dependency factor
    "temporal_recency": 0.10,   # How recent the event data is
    "congestion_pressure": 0.06, # Current network congestion level
    "exposure_sensitivity": 0.04, # Asset vulnerability profile
}


def compute_risk_score(
    event_severity: float,
    source_confidence: float,
    spatial_proximity: float,
    network_centrality: float,
    route_dependency: float,
    temporal_recency: float,
    congestion_pressure: float,
    exposure_sensitivity: float,
    weights: Optional[Dict[str, float]] = None,
) -> RiskResult:
    """
    Compute composite risk score for infrastructure disruption event.

    The risk score combines multiple factors using weighted aggregation:

    R = w_sev * S + w_conf * C + w_spat * P + w_net * N + w_route * D +
        w_time * T + w_cong * Cg + w_exp * E

    Where:
        - S: event severity (0-1)
        - C: source confidence (0-1)
        - P: spatial proximity score (0-1)
        - N: network centrality (0-1)
        - D: route dependency weight (0-1)
        - T: temporal recency (0-1)
        - Cg: congestion pressure (0-1)
        - E: exposure sensitivity (0-1)

    Args:
        event_severity: Event magnitude/impact (0-1)
        source_confidence: Source quality/credibility (0-1)
        spatial_proximity: Geographic proximity to assets (0-1)
        network_centrality: Network criticality of affected location (0-1)
        route_dependency: Dependency on affected routes (0-1)
        temporal_recency: Freshness of threat information (0-1)
        congestion_pressure: Current congestion level (0-1)
        exposure_sensitivity: Vulnerability of assets (0-1)
        weights: Custom weight dictionary. Defaults to DEFAULT_RISK_WEIGHTS if None.

    Returns:
        RiskResult with composite score, component breakdown, and explanation.

    Raises:
        ValueError: If any input is not in [0, 1] or weights don't sum properly.
    """
    # Validate inputs
    inputs = {
        "event_severity": event_severity,
        "source_confidence": source_confidence,
        "spatial_proximity": spatial_proximity,
        "network_centrality": network_centrality,
        "route_dependency": route_dependency,
        "temporal_recency": temporal_recency,
        "congestion_pressure": congestion_pressure,
        "exposure_sensitivity": exposure_sensitivity,
    }

    for name, value in inputs.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be in [0, 1], got {value}")

    # Use default weights if none provided
    if weights is None:
        weights = DEFAULT_RISK_WEIGHTS.copy()

    # Validate weights
    weight_keys = set(weights.keys())
    expected_keys = set(inputs.keys())
    if weight_keys != expected_keys:
        raise ValueError(
            f"Weight keys {weight_keys} don't match input keys {expected_keys}"
        )

    weight_sum = sum(weights.values())
    if not np.isclose(weight_sum, 1.0, rtol=1e-6):
        raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

    # Compute weighted components
    components = {
        "event_severity": event_severity * weights["event_severity"],
        "source_confidence": source_confidence * weights["source_confidence"],
        "spatial_proximity": spatial_proximity * weights["spatial_proximity"],
        "network_centrality": network_centrality * weights["network_centrality"],
        "route_dependency": route_dependency * weights["route_dependency"],
        "temporal_recency": temporal_recency * weights["temporal_recency"],
        "congestion_pressure": congestion_pressure * weights["congestion_pressure"],
        "exposure_sensitivity": exposure_sensitivity * weights["exposure_sensitivity"],
    }

    # Compute composite score
    score = sum(components.values())
    score = float(np.clip(score, 0.0, 1.0))

    # Determine severity class for explanation
    if score >= 0.75:
        severity_class = "CRITICAL"
    elif score >= 0.50:
        severity_class = "HIGH"
    elif score >= 0.25:
        severity_class = "MODERATE"
    else:
        severity_class = "LOW"

    # Build explanation
    top_factors = sorted(
        [(k, v) for k, v in components.items() if v > 0],
        key=lambda x: x[1],
        reverse=True,
    )[:3]

    factor_strs = [f"{k.replace('_', ' ').title()}: {v:.3f}" for k, v in top_factors]
    explanation = (
        f"Risk Level: {severity_class} ({score:.3f}). "
        f"Primary drivers: {'; '.join(factor_strs)}"
    )

    return RiskResult(
        score=score,
        components=components,
        explanation=explanation,
    )
