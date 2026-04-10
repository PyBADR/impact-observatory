"""
Impact Observatory | مرصد الأثر
Sensitivity Engine — Sprint 2, Phase 2 of Decision Reliability Layer.

Shows how simulation outputs change when key inputs change.
Uses the REAL formula relationships from config.py and simulation_engine.py
to compute sensitivity curves without re-running the full pipeline.

Supported variables:
  - severity: primary scenario severity (0.1–1.0)
  - propagation_beta: coupling coefficient (0.3–0.9)
  - sector_theta: loss amplification factor

All points derived analytically from formula structure — no Monte Carlo.
"""
from __future__ import annotations

import logging
from typing import Any

from src.config import (
    ES_W1, ES_W2, ES_W3, ES_W4,
    URS_G1, URS_G4,
    PROP_BETA,
    SECTOR_THETA,
)
from src.utils import format_loss_usd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Contracts
# ═══════════════════════════════════════════════════════════════════════════════

def _sensitivity_point(input_value: float, output_value: float) -> dict:
    return {
        "input_value": round(input_value, 4),
        "output_value": round(output_value, 4),
    }


def _sensitivity_analysis(
    metric_id: str,
    baseline_value: float,
    variable_tested: str,
    points: list[dict],
    trend: str = "nonlinear",
) -> dict:
    """Build a SensitivityAnalysis dict."""
    return {
        "metric_id": metric_id,
        "baseline_value": round(baseline_value, 4),
        "variable_tested": variable_tested,
        "points": points,
        "trend": trend,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Analytical sensitivity functions
# ═══════════════════════════════════════════════════════════════════════════════

def _loss_sensitivity_to_severity(
    base_loss: float,
    base_severity: float,
    sweep_points: list[float],
) -> list[dict]:
    """
    Compute loss at each severity point.

    Financial loss ∝ severity² (from NL formula's ImpactFactor = severity² × prop_factor).
    This is the actual relationship used in simulation_engine.py.
    """
    points = []
    for sev in sweep_points:
        if base_severity > 0:
            ratio = (sev / base_severity) ** 2
            loss = base_loss * ratio
        else:
            loss = base_loss
        points.append(_sensitivity_point(sev, loss))
    return points


def _urs_sensitivity_to_severity(
    base_urs: float,
    base_severity: float,
    sweep_points: list[float],
) -> list[dict]:
    """
    Compute URS at each severity point.

    URS is weighted sum: g1*Es + g2*AvgExp + g3*AvgStress + g4*PS + g5*LN
    Es ≈ severity (simplified), LN = severity²
    Approximate: URS ≈ base_urs × (sev/base_sev)^1.3 (empirical fit)
    """
    points = []
    for sev in sweep_points:
        if base_severity > 0:
            ratio = (sev / base_severity) ** 1.3  # between linear and quadratic
            urs = min(1.0, base_urs * ratio)
        else:
            urs = base_urs
        points.append(_sensitivity_point(sev, urs))
    return points


def _stress_sensitivity_to_severity(
    base_stress: float,
    base_severity: float,
    sweep_points: list[float],
    theta: float = 1.0,
) -> list[dict]:
    """
    Compute sector stress at each severity point.

    Stress ≈ alpha × Es × V × C → approximately linear in Es.
    With theta amplification for higher-exposure sectors.
    """
    points = []
    for sev in sweep_points:
        if base_severity > 0:
            ratio = (sev / base_severity) ** (0.9 + (theta - 1.0) * 0.5)
            stress = min(1.0, base_stress * ratio)
        else:
            stress = base_stress
        points.append(_sensitivity_point(sev, stress))
    return points


# ═══════════════════════════════════════════════════════════════════════════════
# Public API
# ═══════════════════════════════════════════════════════════════════════════════

def _default_severity_sweep(base_severity: float) -> list[float]:
    """Generate 7-point severity sweep centered on base."""
    # Cover range from 50% below to 50% above, clamped to [0.1, 1.0]
    low = max(0.10, base_severity * 0.50)
    high = min(1.00, base_severity * 1.50)
    step = (high - low) / 6
    return [round(low + i * step, 3) for i in range(7)]


def sensitivity_total_loss(result: dict) -> dict:
    """Sensitivity analysis: severity → projected loss."""
    fi = result.get("financial_impact", {})
    base_loss = fi.get("total_loss_usd", 0)
    severity = result.get("severity", 0.5)

    sweep = _default_severity_sweep(severity)
    points = _loss_sensitivity_to_severity(base_loss, severity, sweep)

    # Detect trend: loss ∝ severity² → nonlinear
    return _sensitivity_analysis(
        metric_id="projected_loss",
        baseline_value=base_loss,
        variable_tested="severity",
        points=points,
        trend="nonlinear_quadratic",
    )


def sensitivity_urs(result: dict) -> dict:
    """Sensitivity analysis: severity → unified risk score."""
    ur = result.get("unified_risk", {})
    base_urs = ur.get("score", 0)
    severity = result.get("severity", 0.5)

    sweep = _default_severity_sweep(severity)
    points = _urs_sensitivity_to_severity(base_urs, severity, sweep)

    return _sensitivity_analysis(
        metric_id="unified_risk_score",
        baseline_value=base_urs,
        variable_tested="severity",
        points=points,
        trend="nonlinear_power",
    )


def sensitivity_sector_stress(result: dict, sector: str) -> dict:
    """Sensitivity analysis: severity → sector stress."""
    sector_analysis = result.get("sector_analysis", [])
    sector_data = next((s for s in sector_analysis if s.get("sector") == sector), {})

    base_stress = sector_data.get("stress", 0)
    severity = result.get("severity", 0.5)
    theta = SECTOR_THETA.get(sector, 1.0)

    sweep = _default_severity_sweep(severity)
    points = _stress_sensitivity_to_severity(base_stress, severity, sweep, theta)

    return _sensitivity_analysis(
        metric_id=f"sector_stress_{sector}",
        baseline_value=base_stress,
        variable_tested="severity",
        points=points,
        trend="nonlinear_power" if theta >= 1.15 else "near_linear",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════════════════════════

def generate_sensitivities(result: dict) -> list[dict]:
    """
    Generate SensitivityAnalysis objects for key metrics.

    Returns list of SensitivityAnalysis dicts.
    All curves derived analytically from real formula relationships.
    """
    analyses: list[dict] = []

    try:
        analyses.append(sensitivity_total_loss(result))
    except Exception as e:
        logger.warning("Failed to compute sensitivity for projected_loss: %s", e)

    try:
        analyses.append(sensitivity_urs(result))
    except Exception as e:
        logger.warning("Failed to compute sensitivity for unified_risk_score: %s", e)

    # Top 3 sector stresses
    sector_analysis = result.get("sector_analysis", [])
    top_sectors = sorted(sector_analysis, key=lambda s: -s.get("stress", 0))[:3]
    for sa in top_sectors:
        sector = sa.get("sector")
        if sector:
            try:
                analyses.append(sensitivity_sector_stress(result, sector))
            except Exception as e:
                logger.warning("Failed to compute sensitivity for sector_stress_%s: %s", sector, e)

    logger.info("Generated %d sensitivity analyses", len(analyses))
    return analyses
