"""
System-level stress score aggregating multiple disruption metrics.

Physics metaphor: System stress is a multi-dimensional scalar that aggregates
pressure (load on nodes), congestion (flow density), disruptions (unresolved
events), and uncertainty (epistemic limits). Like total mechanical stress in
a structure, high system stress indicates increased risk of cascading failures.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from enum import Enum
import numpy as np


class StressLevel(Enum):
    """Qualitative stress level categories."""
    NOMINAL = "nominal"
    ELEVATED = "elevated"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SystemStressResult:
    """
    Result of system stress computation.
    
    Attributes:
        stress_score: Quantitative stress [0, 1]
        level: Qualitative stress level (nominal/elevated/high/critical)
        components: Dictionary of individual component contributions
                   Keys: 'pressure', 'congestion', 'disruptions', 'uncertainty'
        narrative: Human-readable summary of stress state
    """
    stress_score: float
    level: StressLevel
    components: Dict[str, float] = field(default_factory=dict)
    narrative: str = ""


def compute_system_stress(
    pressures: Dict[str, float],
    congestion_scores: Dict[str, float],
    unresolved_disruptions: int = 0,
    uncertainty: float = 0.0,
    weights: Optional[Dict[str, float]] = None
) -> SystemStressResult:
    """
    Compute aggregate system stress from multiple metrics.
    
    Physics model: System stress combines four sources of system strain:
    1. Pressure: Sum of node load stresses (normalized)
    2. Congestion: Average flow density across corridors (normalized)
    3. Disruptions: Count of unresolved disruptions (exponential scaling)
    4. Uncertainty: Epistemic uncertainty about state (normalized)
    
    These are combined using a weighted sum:
        stress = w_p * P + w_c * C + w_d * D + w_u * U
    
    The result is clamped to [0, 1] for interpretation.
    
    Args:
        pressures: Dict mapping node_id -> pressure value
        congestion_scores: Dict mapping corridor_id -> congestion [0,1]
        unresolved_disruptions: Count of ongoing disruptions [default: 0]
        uncertainty: Epistemic uncertainty [0, 1] [default: 0.0]
        weights: Optional weights for each component
                Keys: 'pressure', 'congestion', 'disruptions', 'uncertainty'
                Default: equal weights [0.25, 0.25, 0.25, 0.25]
                
    Returns:
        SystemStressResult with stress_score, level, and component breakdown
    """
    # Default weights: equal contribution from each component
    if weights is None:
        weights = {
            'pressure': 0.25,
            'congestion': 0.25,
            'disruptions': 0.25,
            'uncertainty': 0.25
        }

    # Validate weights sum to 1
    weight_sum = sum(weights.values())
    if not np.isclose(weight_sum, 1.0, atol=0.01):
        # Normalize weights
        for key in weights:
            weights[key] /= weight_sum

    # Component 1: Pressure stress (max of all node pressures, normalized)
    if pressures:
        pressure_stress = np.mean(list(pressures.values()))
        pressure_stress = float(np.clip(pressure_stress / 2.0, 0.0, 1.0))
    else:
        pressure_stress = 0.0

    # Component 2: Congestion stress (average of all corridors)
    if congestion_scores:
        congestion_stress = np.mean(list(congestion_scores.values()))
    else:
        congestion_stress = 0.0

    # Component 3: Disruption stress (exponential with count)
    # Even a single disruption contributes meaningfully
    disruption_stress = 1.0 - np.exp(-0.5 * unresolved_disruptions)

    # Component 4: Uncertainty stress (direct normalization)
    uncertainty_stress = float(np.clip(uncertainty, 0.0, 1.0))

    # Aggregate with weights
    stress_score = (
        weights['pressure'] * pressure_stress
        + weights['congestion'] * congestion_stress
        + weights['disruptions'] * disruption_stress
        + weights['uncertainty'] * uncertainty_stress
    )

    # Determine stress level
    if stress_score < 0.25:
        level = StressLevel.NOMINAL
    elif stress_score < 0.5:
        level = StressLevel.ELEVATED
    elif stress_score < 0.75:
        level = StressLevel.HIGH
    else:
        level = StressLevel.CRITICAL

    # Build narrative
    active_components = []
    if pressure_stress > 0.1:
        active_components.append(f"node pressure {pressure_stress:.2f}")
    if congestion_stress > 0.1:
        active_components.append(f"congestion {congestion_stress:.2f}")
    if unresolved_disruptions > 0:
        active_components.append(f"{unresolved_disruptions} disruption(s)")
    if uncertainty_stress > 0.1:
        active_components.append(f"uncertainty {uncertainty_stress:.2f}")

    if active_components:
        narrative = f"System under {level.value} stress. Active stressors: {', '.join(active_components)}."
    else:
        narrative = "System nominal. All metrics within acceptable ranges."

    return SystemStressResult(
        stress_score=float(np.clip(stress_score, 0.0, 1.0)),
        level=level,
        components={
            'pressure': pressure_stress,
            'congestion': congestion_stress,
            'disruptions': disruption_stress,
            'uncertainty': uncertainty_stress
        },
        narrative=narrative
    )
