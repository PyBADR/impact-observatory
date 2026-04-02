"""GCC-tuned system stress aggregator — unified health metric with exact weights.

Uses SystemStressWeights (congestion=0.35, risk=0.30, uncertainty=0.20,
insurance_severity=0.15) from gcc_weights.

SystemStress = w1*congestion + w2*risk + w3*uncertainty + w4*insurance_severity

Returns SystemStressReport with classification and actionable recommendations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import (
    SYSTEM_STRESS,
    SystemStressWeights,
)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass
class StressFactor:
    """A single factor's contribution to system stress."""
    name: str
    raw_value: float
    weight: float
    weighted_contribution: float
    detail: str


@dataclass
class SystemStressReport:
    """Full system stress assessment with GCC weights."""
    total_stress: float
    classification: str  # NOMINAL, LOW, MODERATE, ELEVATED, CRITICAL
    factors: list[StressFactor]
    dominant_factor: str
    congestion_component: float
    risk_component: float
    uncertainty_component: float
    insurance_component: float
    recommendations: list[str]
    weights_used: dict[str, float]


# ---------------------------------------------------------------------------
# Classification and recommendations
# ---------------------------------------------------------------------------

_THRESHOLDS = [
    (0.70, "CRITICAL"),
    (0.50, "ELEVATED"),
    (0.30, "MODERATE"),
    (0.10, "LOW"),
    (0.00, "NOMINAL"),
]


def _classify(stress: float) -> str:
    for threshold, label in _THRESHOLDS:
        if stress >= threshold:
            return label
    return "NOMINAL"


def _generate_recommendations(
    total: float,
    classification: str,
    dominant: str,
    factors: dict[str, float],
    pressure_mean: float,
    shockwave_energy: float,
) -> list[str]:
    """Generate actionable recommendations based on stress state."""
    recs: list[str] = []

    if classification == "CRITICAL":
        recs.append(
            f"CRITICAL: System stress at {total * 100:.0f}%. "
            "Activate emergency monitoring and escalation protocols."
        )
        recs.append(f"Primary driver: {dominant}. Prioritize mitigation in this area.")
    elif classification == "ELEVATED":
        recs.append(
            f"ELEVATED: System stress at {total * 100:.0f}%. "
            "Increase monitoring frequency and prepare contingencies."
        )

    if factors.get("congestion", 0.0) > 0.15:
        recs.append(
            "High congestion contribution detected. "
            "Consider activating alternative routing or load-shedding."
        )

    if factors.get("risk", 0.0) > 0.15:
        recs.append(
            "Elevated risk contribution. Review active threat fields and update mitigations."
        )

    if factors.get("uncertainty", 0.0) > 0.10:
        recs.append(
            "Significant uncertainty penalty. Seek additional intelligence sources "
            "before high-stakes decisions."
        )

    if factors.get("insurance_severity", 0.0) > 0.08:
        recs.append(
            "Insurance severity component elevated. Review exposure concentrations."
        )

    if pressure_mean > 0.6:
        recs.append(
            f"Mean node pressure at {pressure_mean:.2f}. "
            "System is approaching capacity saturation."
        )

    if shockwave_energy > 0.3:
        recs.append(
            f"Active shockwave energy at {shockwave_energy:.2f}. "
            "Cascade propagation in progress — monitor downstream nodes."
        )

    if not recs:
        recs.append("System within normal parameters. Continue standard monitoring.")

    return recs


# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_gcc_system_stress(
    risk_vector: NDArray[np.float64],
    pressure: NDArray[np.float64] | None = None,
    diffusion: NDArray[np.float64] | None = None,
    shockwave: NDArray[np.float64] | None = None,
    boundary_tension: float = 0.0,
    uncertainty_score: float | None = None,
    insurance_severity: float | None = None,
    weights: SystemStressWeights | None = None,
) -> SystemStressReport:
    """Compute GCC-tuned system stress from all intelligence layers.

    The four primary factors weighted by SystemStressWeights:
    1. Congestion — derived from pressure + diffusion state
    2. Risk — derived from risk_vector mean
    3. Uncertainty — provided or derived from risk variance
    4. Insurance severity — provided or derived from risk + boundary tension

    Args:
        risk_vector: (N,) current risk state per node.
        pressure: (N,) optional pressure values per node.
        diffusion: (N,) optional diffusion state per node.
        shockwave: (N,) optional peak shockwave amplitudes per node.
        boundary_tension: scalar boundary tension score [0, 1].
        uncertainty_score: explicit uncertainty [0, 1]. If None, derived from risk variance.
        insurance_severity: explicit insurance severity [0, 1]. If None, derived.
        weights: SystemStressWeights override (default: GCC singleton).

    Returns:
        SystemStressReport with classification and recommendations.
    """
    w = weights or SYSTEM_STRESS

    # Derive component values
    risk_mean = float(np.mean(risk_vector))
    risk_max = float(np.max(risk_vector)) if len(risk_vector) > 0 else 0.0

    # Congestion: combine pressure and diffusion
    pressure_mean = float(np.mean(pressure)) if pressure is not None else 0.0
    diffusion_mean = float(np.mean(diffusion)) if diffusion is not None else 0.0
    congestion_raw = float(np.clip(
        0.5 * pressure_mean + 0.3 * diffusion_mean + 0.2 * boundary_tension,
        0.0,
        1.0,
    ))

    # Risk component
    risk_raw = float(np.clip(risk_mean, 0.0, 1.0))

    # Uncertainty: from risk variance if not provided
    if uncertainty_score is not None:
        uncertainty_raw = float(np.clip(uncertainty_score, 0.0, 1.0))
    else:
        risk_std = float(np.std(risk_vector)) if len(risk_vector) > 1 else 0.0
        uncertainty_raw = float(np.clip(risk_std * 2.0, 0.0, 1.0))

    # Insurance severity: derive from risk + boundary tension + shockwave if not provided
    if insurance_severity is not None:
        insurance_raw = float(np.clip(insurance_severity, 0.0, 1.0))
    else:
        shockwave_mean = float(np.mean(shockwave)) if shockwave is not None else 0.0
        insurance_raw = float(np.clip(
            0.4 * risk_max + 0.3 * shockwave_mean + 0.3 * boundary_tension,
            0.0,
            1.0,
        ))

    # GCC-weighted stress
    congestion_comp = w.congestion * congestion_raw
    risk_comp = w.risk * risk_raw
    uncertainty_comp = w.uncertainty * uncertainty_raw
    insurance_comp = w.insurance_severity * insurance_raw

    total = float(np.clip(congestion_comp + risk_comp + uncertainty_comp + insurance_comp, 0.0, 1.0))

    # Build factor list
    factors = [
        StressFactor(
            name="congestion",
            raw_value=congestion_raw,
            weight=w.congestion,
            weighted_contribution=congestion_comp,
            detail=f"congestion={congestion_raw:.4f} x {w.congestion:.2f} = {congestion_comp:.4f}",
        ),
        StressFactor(
            name="risk",
            raw_value=risk_raw,
            weight=w.risk,
            weighted_contribution=risk_comp,
            detail=f"risk={risk_raw:.4f} x {w.risk:.2f} = {risk_comp:.4f}",
        ),
        StressFactor(
            name="uncertainty",
            raw_value=uncertainty_raw,
            weight=w.uncertainty,
            weighted_contribution=uncertainty_comp,
            detail=f"uncertainty={uncertainty_raw:.4f} x {w.uncertainty:.2f} = {uncertainty_comp:.4f}",
        ),
        StressFactor(
            name="insurance_severity",
            raw_value=insurance_raw,
            weight=w.insurance_severity,
            weighted_contribution=insurance_comp,
            detail=f"insurance={insurance_raw:.4f} x {w.insurance_severity:.2f} = {insurance_comp:.4f}",
        ),
    ]

    # Dominant factor
    factor_contributions = {
        "congestion": congestion_comp,
        "risk": risk_comp,
        "uncertainty": uncertainty_comp,
        "insurance_severity": insurance_comp,
    }
    dominant = max(factor_contributions, key=factor_contributions.get)  # type: ignore[arg-type]

    classification = _classify(total)

    shockwave_energy = float(np.sum(shockwave ** 2)) / max(len(shockwave), 1) if shockwave is not None else 0.0

    recommendations = _generate_recommendations(
        total=total,
        classification=classification,
        dominant=dominant,
        factors=factor_contributions,
        pressure_mean=pressure_mean,
        shockwave_energy=shockwave_energy,
    )

    return SystemStressReport(
        total_stress=total,
        classification=classification,
        factors=factors,
        dominant_factor=dominant,
        congestion_component=congestion_comp,
        risk_component=risk_comp,
        uncertainty_component=uncertainty_comp,
        insurance_component=insurance_comp,
        recommendations=recommendations,
        weights_used={
            "w1_congestion": w.congestion,
            "w2_risk": w.risk,
            "w3_uncertainty": w.uncertainty,
            "w4_insurance_severity": w.insurance_severity,
        },
    )
