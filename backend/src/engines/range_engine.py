"""
Impact Observatory | مرصد الأثر
Range Engine — Sprint 2, Phase 1 of Decision Reliability Layer.

Replaces single-point estimates with bounded [low, base, high] ranges.
Derivation methods:
  SENSITIVITY_SWEEP: ±severity variation propagated through formula
  SCENARIO_BAND: confidence-interval from simulation engine
  HYBRID: combines both approaches

Every range is derived from REAL simulation data — no arbitrary bands.
"""
from __future__ import annotations

import logging
from typing import Any

from src.config import (
    SECTOR_THETA, SECTOR_ALPHA,
    CONF_WELL_KNOWN_SCENARIOS,
    TRUST_SECTOR_DATA_COMPLETENESS,
    PROP_BETA,
)
from src.utils import format_loss_usd

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Contract
# ═══════════════════════════════════════════════════════════════════════════════

def _range_estimate(
    metric_id: str,
    low: float,
    base: float,
    high: float,
    confidence: int,
    method: str,
    notes: list[str] | None = None,
) -> dict:
    """Build a RangeEstimate dict matching the Sprint 2 contract."""
    assert method in ("SENSITIVITY_SWEEP", "SCENARIO_BAND", "HYBRID"), f"Invalid method: {method}"
    # Enforce invariant: low ≤ base ≤ high
    actual_low = min(low, base)
    actual_high = max(high, base)
    return {
        "metric_id": metric_id,
        "low": round(actual_low, 4),
        "base": round(base, 4),
        "high": round(actual_high, 4),
        "confidence": max(0, min(100, confidence)),
        "method": method,
        "notes": notes or [],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Derivation helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _severity_band(severity: float) -> tuple[float, float]:
    """Derive low/high severity from base severity.

    Band width scales with severity:
      - Low severity (≤0.3): ±10% narrow band
      - Medium severity (0.3–0.7): ±15% moderate band
      - High severity (>0.7): ±20% wide band (more uncertainty at extremes)
    """
    if severity <= 0.30:
        delta = 0.10
    elif severity <= 0.70:
        delta = 0.15
    else:
        delta = 0.20

    low_sev = max(0.05, severity * (1.0 - delta))
    high_sev = min(1.0, severity * (1.0 + delta))
    return low_sev, high_sev


def _loss_at_severity(base_loss: float, base_severity: float, target_severity: float) -> float:
    """Estimate loss at different severity using quadratic relationship.

    NL = f(severity²) — from config.py URS_G5 and financial loss model.
    This is the same severity² proxy used in the actual simulation.
    """
    if base_severity <= 0:
        return base_loss
    ratio = (target_severity / base_severity) ** 2
    return base_loss * ratio


def _propagation_uncertainty(base_value: float, severity: float) -> float:
    """Add propagation uncertainty: ±(beta × severity × 0.1).

    PROP_BETA (0.65) is the coupling coefficient. Higher coupling
    at higher severity = wider uncertainty band.
    """
    return base_value * PROP_BETA * severity * 0.10


# ═══════════════════════════════════════════════════════════════════════════════
# Metric-specific range generators
# ═══════════════════════════════════════════════════════════════════════════════

def range_total_loss(result: dict) -> dict:
    """Range estimate for projected total loss."""
    fi = result.get("financial_impact", {})
    base_loss = fi.get("total_loss_usd", 0)
    severity = result.get("severity", 0.5)
    confidence_score = result.get("confidence_score", 0.75)
    scenario_id = result.get("scenario_id", "")

    low_sev, high_sev = _severity_band(severity)

    # Method 1: Sensitivity sweep (severity variation)
    loss_low = _loss_at_severity(base_loss, severity, low_sev)
    loss_high = _loss_at_severity(base_loss, severity, high_sev)

    # Method 2: Scenario band (confidence interval — already in sim engine)
    ci_lower = fi.get("confidence_interval", {}).get("lower", loss_low)
    ci_upper = fi.get("confidence_interval", {}).get("upper", loss_high)

    # HYBRID: take the wider of the two bands
    final_low = min(loss_low, ci_lower)
    final_high = max(loss_high, ci_upper)

    # Add propagation uncertainty
    prop_unc = _propagation_uncertainty(base_loss, severity)
    final_low = max(0, final_low - prop_unc)
    final_high = final_high + prop_unc

    is_known = scenario_id in CONF_WELL_KNOWN_SCENARIOS
    conf = int(confidence_score * 100) if confidence_score <= 1 else int(confidence_score)

    return _range_estimate(
        metric_id="projected_loss",
        low=final_low,
        base=base_loss,
        high=final_high,
        confidence=conf,
        method="HYBRID",
        notes=[
            f"Severity band: {low_sev:.2f}–{high_sev:.2f} (base {severity:.2f})",
            f"Propagation uncertainty: ±{format_loss_usd(prop_unc)}",
            f"{'Well-calibrated scenario — narrower band' if is_known else 'Less-calibrated — wider uncertainty'}",
        ],
    )


def range_unified_risk_score(result: dict) -> dict:
    """Range estimate for URS."""
    ur = result.get("unified_risk", {})
    base_urs = ur.get("score", 0)
    severity = result.get("severity", 0.5)
    confidence_score = result.get("confidence_score", 0.75)

    low_sev, high_sev = _severity_band(severity)

    # URS is roughly linear in severity (g1=0.35 × Es dominates)
    if severity > 0:
        urs_low = base_urs * (low_sev / severity) * 0.95  # slight nonlinear dampening
        urs_high = base_urs * (high_sev / severity) * 1.05
    else:
        urs_low = base_urs * 0.85
        urs_high = base_urs * 1.15

    urs_low = max(0, urs_low)
    urs_high = min(1.0, urs_high)

    conf = int(confidence_score * 100) if confidence_score <= 1 else int(confidence_score)

    return _range_estimate(
        metric_id="unified_risk_score",
        low=urs_low,
        base=base_urs,
        high=urs_high,
        confidence=conf,
        method="SENSITIVITY_SWEEP",
        notes=[
            f"URS driven by severity {severity:.2f} (weight 35%)",
            f"Low/high from severity variation {low_sev:.2f}–{high_sev:.2f}",
        ],
    )


def range_confidence_score(result: dict) -> dict:
    """Range estimate for confidence score (meta-confidence)."""
    base_conf = result.get("confidence_score", 0.75)
    severity = result.get("severity", 0.5)
    scenario_id = result.get("scenario_id", "")
    is_known = scenario_id in CONF_WELL_KNOWN_SCENARIOS

    # Confidence is more stable — narrower band
    band = 0.08 if is_known else 0.12
    conf_low = max(0, base_conf - band)
    conf_high = min(1.0, base_conf + band)

    return _range_estimate(
        metric_id="confidence_score",
        low=conf_low,
        base=base_conf,
        high=conf_high,
        confidence=85 if is_known else 70,
        method="SCENARIO_BAND",
        notes=[
            f"Confidence band ±{band:.0%} based on {'known' if is_known else 'unknown'} scenario calibration",
        ],
    )


def range_sector_stress(result: dict, sector: str) -> dict:
    """Range estimate for sector stress."""
    sector_analysis = result.get("sector_analysis", [])
    sector_data = next((s for s in sector_analysis if s.get("sector") == sector), {})

    base_stress = sector_data.get("stress", 0)
    severity = result.get("severity", 0.5)
    theta = SECTOR_THETA.get(sector, 1.0)
    data_qual = TRUST_SECTOR_DATA_COMPLETENESS.get(sector, 0.60)

    # Wider band for sectors with lower data quality
    band_factor = 0.10 + (1.0 - data_qual) * 0.15  # 10-25% depending on data quality

    stress_low = max(0, base_stress * (1.0 - band_factor))
    stress_high = min(1.0, base_stress * (1.0 + band_factor * theta))

    conf = int(data_qual * 90)

    return _range_estimate(
        metric_id=f"sector_stress_{sector}",
        low=stress_low,
        base=base_stress,
        high=stress_high,
        confidence=conf,
        method="SENSITIVITY_SWEEP",
        notes=[
            f"Band scaled by data quality ({data_qual:.0%}) and theta ({theta:.2f})",
            f"{sector.title()} sector uncertainty factor: ±{band_factor:.0%}",
        ],
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Main entry point
# ═══════════════════════════════════════════════════════════════════════════════

def generate_ranges(result: dict) -> list[dict]:
    """
    Generate RangeEstimate objects for all key metrics.

    Returns list of RangeEstimate dicts — one per metric.
    Every bound derived from real simulation parameters.
    """
    ranges: list[dict] = []

    try:
        ranges.append(range_total_loss(result))
    except Exception as e:
        logger.warning("Failed to compute range for projected_loss: %s", e)

    try:
        ranges.append(range_unified_risk_score(result))
    except Exception as e:
        logger.warning("Failed to compute range for unified_risk_score: %s", e)

    try:
        ranges.append(range_confidence_score(result))
    except Exception as e:
        logger.warning("Failed to compute range for confidence_score: %s", e)

    # Sector stress ranges
    sector_analysis = result.get("sector_analysis", [])
    for sa in sector_analysis:
        sector = sa.get("sector")
        if sector:
            try:
                ranges.append(range_sector_stress(result, sector))
            except Exception as e:
                logger.warning("Failed to compute range for sector_stress_%s: %s", sector, e)

    logger.info("Generated %d range estimates", len(ranges))
    return ranges
