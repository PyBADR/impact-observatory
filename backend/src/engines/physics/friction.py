"""Friction / resistance model for corridors and chokepoints.

Different corridors impose varying levels of resistance to flow.
Resistance factors: political restrictions, physical narrowness,
congestion, security conditions.

Pressure = Flow * Vulnerability * ThreatIntensity
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class FrictionModel:
    """Compute effective resistance for a corridor or route segment."""

    base_resistance: float = 0.1  # inherent corridor friction [0, 1]
    political_factor: float = 0.0  # additional political restriction
    chokepoint_factor: float = 0.0  # narrowness / capacity constraint
    security_factor: float = 0.0  # active security threat

    @property
    def total_resistance(self) -> float:
        """Total friction = base + political + chokepoint + security, clamped."""
        return float(
            np.clip(
                self.base_resistance
                + self.political_factor
                + self.chokepoint_factor
                + self.security_factor,
                0.0,
                1.0,
            )
        )

    def effective_flow(self, nominal_flow: float) -> float:
        """Flow after friction: F_eff = F_nominal * (1 - resistance)."""
        return nominal_flow * (1.0 - self.total_resistance)

    def transit_delay_factor(self) -> float:
        """Delay multiplier: 1 / (1 - resistance). Higher resistance = longer transit."""
        r = self.total_resistance
        if r >= 0.99:
            return 100.0  # effectively blocked
        return 1.0 / (1.0 - r)


def corridor_resistance(
    base: float,
    threat_intensity: float,
    is_chokepoint: bool,
    congestion_level: float = 0.0,
) -> tuple[float, dict]:
    """Calculate corridor resistance with explanation.

    Args:
        base: Inherent corridor friction [0, 1].
        threat_intensity: Current threat level near corridor [0, 1].
        is_chokepoint: Whether this is a geographic chokepoint.
        congestion_level: Current congestion [0, 1].

    Returns:
        (total_resistance, explanation_dict)
    """
    chokepoint_penalty = 0.2 if is_chokepoint else 0.0
    security_penalty = threat_intensity * 0.5
    congestion_penalty = congestion_level * 0.3

    total = float(np.clip(base + chokepoint_penalty + security_penalty + congestion_penalty, 0.0, 1.0))

    explanation = {
        "base_resistance": base,
        "chokepoint_penalty": chokepoint_penalty,
        "security_penalty": security_penalty,
        "congestion_penalty": congestion_penalty,
        "total_resistance": total,
    }
    return total, explanation
