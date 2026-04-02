"""Unified system stress aggregator.

Combines outputs from all physics and math models into a single system health assessment.

SystemStress = w1*pressure + w2*congestion + w3*unresolved_disruption + w4*uncertainty + w5*diffusion_load

This is the top-level "energy" metric for the entire intelligence system.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from src.engines.math.propagation import (
    compute_system_confidence,
    compute_system_energy,
    compute_sector_impacts,
)
from src.models.canonical import ScoreExplanation


@dataclass
class StressWeights:
    propagation_energy: float = 0.25
    pressure_aggregate: float = 0.20
    diffusion_load: float = 0.15
    shockwave_peak: float = 0.15
    uncertainty: float = 0.10
    boundary_tension: float = 0.10
    confidence_inverse: float = 0.05


@dataclass
class SystemStressReport:
    """Full system stress assessment."""

    total_stress: float
    confidence: float
    energy: float
    sector_impacts: dict[str, float]
    dominant_sector: str
    propagation_stage: str
    stress_classification: str
    factors: list[ScoreExplanation]
    recommendations: list[str]


def compute_system_stress(
    risk_vector: NDArray[np.float64],
    node_sectors: list[str],
    pressure_values: NDArray[np.float64] | None = None,
    diffusion_state: NDArray[np.float64] | None = None,
    shockwave_peak: NDArray[np.float64] | None = None,
    boundary_tension: float = 0.0,
    weights: StressWeights | None = None,
) -> SystemStressReport:
    """Compute unified system stress from all intelligence layers.

    Args:
        risk_vector: (N,) current risk state from propagation engine.
        node_sectors: (N,) sector label for each node.
        pressure_values: (N,) optional pressure values from pressure model.
        diffusion_state: (N,) optional diffusion state.
        shockwave_peak: (N,) optional peak shockwave amplitudes.
        boundary_tension: scalar boundary tension score.
        weights: stress component weights.

    Returns:
        SystemStressReport with full explanation.
    """
    w = weights or StressWeights()
    n = len(risk_vector)

    # Component scores
    energy = compute_system_energy(risk_vector)
    confidence = compute_system_confidence(risk_vector)
    uncertainty = 1.0 - confidence

    pressure_agg = float(np.mean(pressure_values)) if pressure_values is not None else 0.0
    diffusion_load = float(np.mean(diffusion_state)) if diffusion_state is not None else 0.0
    shock_peak = float(np.mean(shockwave_peak)) if shockwave_peak is not None else 0.0

    # Weighted combination
    components = {
        "propagation_energy": (energy, w.propagation_energy),
        "pressure_aggregate": (pressure_agg, w.pressure_aggregate),
        "diffusion_load": (diffusion_load, w.diffusion_load),
        "shockwave_peak": (shock_peak, w.shockwave_peak),
        "uncertainty": (uncertainty, w.uncertainty),
        "boundary_tension": (boundary_tension, w.boundary_tension),
        "confidence_inverse": (uncertainty, w.confidence_inverse),
    }

    total = 0.0
    factors: list[ScoreExplanation] = []
    for name, (value, weight) in components.items():
        contribution = float(np.clip(value, 0.0, 1.0) * weight)
        total += contribution
        factors.append(ScoreExplanation(
            factor=name,
            weight=weight,
            contribution=contribution,
            detail=f"{name}={value:.4f} × {weight:.2f} = {contribution:.4f}",
        ))

    total_stress = float(np.clip(total, 0.0, 1.0))

    # Sector analysis
    sector_impacts = compute_sector_impacts(risk_vector, node_sectors)
    dominant_sector = max(sector_impacts, key=sector_impacts.get) if sector_impacts else "unknown"

    # Classification
    if total_stress > 0.7:
        classification = "CRITICAL"
    elif total_stress > 0.5:
        classification = "ELEVATED"
    elif total_stress > 0.3:
        classification = "MODERATE"
    elif total_stress > 0.1:
        classification = "LOW"
    else:
        classification = "NOMINAL"

    # Propagation stage
    if energy > 0.5:
        stage = "active_cascade"
    elif energy > 0.2:
        stage = "propagating"
    elif energy > 0.05:
        stage = "residual"
    else:
        stage = "baseline"

    # Recommendations
    recommendations = _generate_stress_recommendations(
        total_stress, classification, dominant_sector, sector_impacts, confidence
    )

    return SystemStressReport(
        total_stress=total_stress,
        confidence=confidence,
        energy=energy,
        sector_impacts=sector_impacts,
        dominant_sector=dominant_sector,
        propagation_stage=stage,
        stress_classification=classification,
        factors=factors,
        recommendations=recommendations,
    )


def _generate_stress_recommendations(
    stress: float,
    classification: str,
    dominant_sector: str,
    sector_impacts: dict[str, float],
    confidence: float,
) -> list[str]:
    recs = []

    if classification == "CRITICAL":
        recs.append(f"CRITICAL: System stress at {stress*100:.0f}%. Activate emergency protocols.")
        recs.append(f"Primary stress sector: {dominant_sector}. Prioritize mitigation.")
    elif classification == "ELEVATED":
        recs.append(f"ELEVATED: System stress at {stress*100:.0f}%. Increase monitoring frequency.")

    high_sectors = [s for s, v in sector_impacts.items() if v > 0.5]
    if high_sectors:
        recs.append(f"Sectors above 50% stress: {', '.join(high_sectors)}.")

    if confidence < 0.5:
        recs.append(f"Low confidence ({confidence*100:.0f}%). Seek additional data sources before acting.")

    if not recs:
        recs.append("System within normal parameters. Continue standard monitoring.")

    return recs
