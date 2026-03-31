"""
Composite disruption score model for integrated impact assessment.

Combines risk, cost, and operational factors into a disruption severity
classification for decision support and prioritization.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import numpy as np


@dataclass
class DisruptionResult:
    """
    Result of disruption score computation.

    Attributes:
        score: Composite disruption score in [0, 1]
        components: Dictionary of individual component scores
        severity_class: Classification (low/moderate/high/critical)
        explanation: Human-readable description of disruption factors
    """
    score: float
    components: Dict[str, float] = field(default_factory=dict)
    severity_class: str = "low"
    explanation: str = ""

    def __post_init__(self):
        """Validate score and severity class."""
        if not 0 <= self.score <= 1:
            raise ValueError(f"Disruption score must be in [0, 1], got {self.score}")

        valid_classes = {"low", "moderate", "high", "critical"}
        if self.severity_class.lower() not in valid_classes:
            raise ValueError(
                f"Severity class must be in {valid_classes}, "
                f"got {self.severity_class}"
            )


# Default weight configuration for disruption components
DEFAULT_DISRUPTION_WEIGHTS = {
    "risk_score": 0.35,           # Base risk assessment
    "reroute_cost": 0.20,         # Cost of alternative routing
    "delay_cost": 0.20,           # Duration and delay impacts
    "congestion": 0.15,           # Network congestion multiplier
    "uncertainty": 0.10,          # Uncertainty in impact estimates
}


def route_disruption_pressure(
    flow_volume: float,
    vulnerability: float,
    threat_intensity: float,
) -> float:
    """
    Calculate route disruption pressure from flow, vulnerability, and threat.

    Combines volume-vulnerability-threat interaction using multiplicative model:

    P = Flow * Vulnerability * Threat

    This captures how network load amplifies the impact of vulnerabilities
    when exposed to threats.

    Args:
        flow_volume: Traffic/flow volume on route (0-1 normalized)
        vulnerability: Vulnerability score of route (0-1)
        threat_intensity: Intensity of threat to route (0-1)

    Returns:
        Disruption pressure in [0, 1]

    Raises:
        ValueError: If any input is not in [0, 1]
    """
    inputs = {
        "flow_volume": flow_volume,
        "vulnerability": vulnerability,
        "threat_intensity": threat_intensity,
    }

    for name, value in inputs.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be in [0, 1], got {value}")

    # Multiplicative interaction
    pressure = flow_volume * vulnerability * threat_intensity
    return float(np.clip(pressure, 0.0, 1.0))


def compute_disruption(
    risk_score: float,
    reroute_cost: float,
    delay_cost: float,
    congestion: float,
    uncertainty: float,
    weights: Optional[Dict[str, float]] = None,
) -> DisruptionResult:
    """
    Compute composite disruption score combining multiple impact factors.

    The disruption score integrates risk assessment with operational costs:

    D = w_risk * R + w_reroute * C_r + w_delay * C_d + w_cong * Cg + w_unc * U

    Where:
        - R: base risk score (0-1)
        - C_r: rerouting cost (0-1)
        - C_d: delay cost (0-1)
        - Cg: congestion pressure (0-1)
        - U: uncertainty in estimates (0-1)

    Severity classification:
        - low: score < 0.25
        - moderate: 0.25 ≤ score < 0.50
        - high: 0.50 ≤ score < 0.75
        - critical: score ≥ 0.75

    Args:
        risk_score: Base risk assessment (0-1)
        reroute_cost: Cost/difficulty of rerouting traffic (0-1)
        delay_cost: Cost of delays and schedule impact (0-1)
        congestion: Network congestion multiplier (0-1)
        uncertainty: Uncertainty in impact estimates (0-1)
        weights: Custom weight dictionary. Defaults to DEFAULT_DISRUPTION_WEIGHTS.

    Returns:
        DisruptionResult with score, components, classification, and explanation.

    Raises:
        ValueError: If any input is invalid or weights don't sum to 1.0
    """
    # Validate inputs
    inputs = {
        "risk_score": risk_score,
        "reroute_cost": reroute_cost,
        "delay_cost": delay_cost,
        "congestion": congestion,
        "uncertainty": uncertainty,
    }

    for name, value in inputs.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be in [0, 1], got {value}")

    # Use default weights if none provided
    if weights is None:
        weights = DEFAULT_DISRUPTION_WEIGHTS.copy()

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
        "risk_score": risk_score * weights["risk_score"],
        "reroute_cost": reroute_cost * weights["reroute_cost"],
        "delay_cost": delay_cost * weights["delay_cost"],
        "congestion": congestion * weights["congestion"],
        "uncertainty": uncertainty * weights["uncertainty"],
    }

    # Compute composite score
    score = sum(components.values())
    score = float(np.clip(score, 0.0, 1.0))

    # Determine severity class
    if score >= 0.75:
        severity_class = "critical"
    elif score >= 0.50:
        severity_class = "high"
    elif score >= 0.25:
        severity_class = "moderate"
    else:
        severity_class = "low"

    # Build explanation
    top_factors = sorted(
        [(k, v) for k, v in components.items() if v > 0],
        key=lambda x: x[1],
        reverse=True,
    )[:3]

    factor_strs = [f"{k.replace('_', ' ').title()}: {v:.3f}" for k, v in top_factors]
    explanation = (
        f"Disruption Level: {severity_class.upper()} ({score:.3f}). "
        f"Primary drivers: {'; '.join(factor_strs) if factor_strs else 'None'}"
    )

    return DisruptionResult(
        score=score,
        components=components,
        severity_class=severity_class,
        explanation=explanation,
    )
