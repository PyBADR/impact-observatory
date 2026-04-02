"""Severity projection — forward-looking loss estimation.

Projects future claims severity based on current risk trajectory,
system stress trends, and scenario outcomes.

Severity_proj(t+Δ) = CurrentSeverity * (1 + trend_factor * Δ)
                    + scenario_uplift * scenario_probability
                    + stress_acceleration * stress_delta

Time horizons: 24h, 7d, 30d, 90d
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray


@dataclass
class SeverityProjection:
    """Projected severity at a future time horizon."""
    horizon_label: str
    horizon_hours: float
    projected_severity: float
    current_severity: float
    trend_component: float
    scenario_component: float
    stress_component: float
    confidence: float
    classification: str


@dataclass
class SeverityProjectionReport:
    """Full severity projection across all horizons."""
    entity_id: str
    current_severity: float
    projections: list[SeverityProjection]
    worst_case_severity: float
    worst_case_horizon: str
    trend_direction: str  # ESCALATING / STABLE / DECLINING
    recommendations: list[str]


# Standard projection horizons
HORIZONS = [
    ("24h", 24.0),
    ("7d", 168.0),
    ("30d", 720.0),
    ("90d", 2160.0),
]


def project_severity(
    entity_id: str,
    current_severity: float,
    trend_factor: float = 0.0,
    scenario_uplift: float = 0.0,
    scenario_probability: float = 0.0,
    stress_current: float = 0.0,
    stress_previous: float = 0.0,
    base_confidence: float = 0.8,
) -> SeverityProjectionReport:
    """Project severity across standard time horizons.

    Args:
        current_severity: current claims severity [0, 1]
        trend_factor: per-hour trend (positive = escalating)
        scenario_uplift: additional severity if scenario materializes
        scenario_probability: probability of scenario [0, 1]
        stress_current: current system stress
        stress_previous: previous system stress (for acceleration)
        base_confidence: confidence in projection
    """
    stress_delta = stress_current - stress_previous
    stress_accel = max(stress_delta, 0.0) * 0.5  # only escalation accelerates

    projections: list[SeverityProjection] = []
    for label, hours in HORIZONS:
        trend_comp = trend_factor * hours
        scenario_comp = scenario_uplift * scenario_probability * min(hours / 168.0, 1.0)
        stress_comp = stress_accel * min(hours / 24.0, 1.0)

        projected = current_severity * (1.0 + trend_comp) + scenario_comp + stress_comp
        projected = float(np.clip(projected, 0.0, 1.0))

        # Confidence decays with horizon
        conf = base_confidence * np.exp(-0.0005 * hours)

        if projected >= 0.7:
            cls = "CRITICAL"
        elif projected >= 0.5:
            cls = "ELEVATED"
        elif projected >= 0.3:
            cls = "MODERATE"
        else:
            cls = "LOW"

        projections.append(SeverityProjection(
            horizon_label=label,
            horizon_hours=hours,
            projected_severity=projected,
            current_severity=current_severity,
            trend_component=trend_comp,
            scenario_component=scenario_comp,
            stress_component=stress_comp,
            confidence=float(conf),
            classification=cls,
        ))

    worst = max(projections, key=lambda p: p.projected_severity)

    if trend_factor > 0.001:
        direction = "ESCALATING"
    elif trend_factor < -0.001:
        direction = "DECLINING"
    else:
        direction = "STABLE"

    recs = []
    if worst.projected_severity > 0.7:
        recs.append(f"CRITICAL severity projected at {worst.horizon_label} ({worst.projected_severity:.2f}). Activate loss mitigation.")
    if direction == "ESCALATING":
        recs.append(f"Escalating trend detected (factor={trend_factor:.4f}/hr). Review portfolio exposure.")
    if scenario_probability > 0.5 and scenario_uplift > 0.2:
        recs.append(f"High-probability scenario (p={scenario_probability:.0%}) with significant uplift ({scenario_uplift:.2f}).")
    if stress_delta > 0.1:
        recs.append(f"System stress accelerating (+{stress_delta:.2f}). May amplify claims.")
    if not recs:
        recs.append("Severity projections within normal bounds.")

    return SeverityProjectionReport(
        entity_id=entity_id,
        current_severity=current_severity,
        projections=projections,
        worst_case_severity=worst.projected_severity,
        worst_case_horizon=worst.horizon_label,
        trend_direction=direction,
        recommendations=recs,
    )
