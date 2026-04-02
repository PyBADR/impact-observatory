"""Service 5: financial_service — Financial Impact (الأثر المالي).

Maps propagated impacts to USD losses per entity and sector.
Uses GCC GDP data, sector weights, and exposure formulas from math_core.

ΔY_i = GDP_i * elasticity * D_i * (1 + cascading_multiplier * Σ_j(A_ij * D_j))
"""

from __future__ import annotations

import logging
import math

from src.schemas.financial_impact import FinancialImpact

logger = logging.getLogger(__name__)

# GCC GDP reference data (USD)
GCC_GDP: dict[str, float] = {
    "SA": 1_061_000_000_000,
    "AE": 507_000_000_000,
    "QA": 219_000_000_000,
    "KW": 164_000_000_000,
    "BH": 44_000_000_000,
    "OM": 104_000_000_000,
    "GCC": 2_099_000_000_000,
    "INT": 0,
    "IR": 0,
    "IR/OM": 0,
    "YE/DJ": 0,
}

# Sector loss multipliers (fraction of GDP per unit impact)
SECTOR_ELASTICITY: dict[str, float] = {
    "energy": 0.025,
    "maritime": 0.015,
    "aviation": 0.012,
    "finance": 0.020,
    "infrastructure": 0.010,
    "government": 0.005,
}

DEFAULT_ELASTICITY = 0.015


def compute_financial_impacts(
    entities: list[dict],
    propagation_results: list[dict],
    severity: float,
    horizon_hours: int,
    base_loss_usd: float,
    peak_day_offset: int,
    recovery_base_days: int,
) -> list[FinancialImpact]:
    """Compute financial impact for each affected entity.

    Maps: propagation impact → USD loss → stress level → classification.
    """
    entity_map = {e["id"]: e for e in entities}
    total_gcc_gdp = GCC_GDP["GCC"]
    results = []

    for prop in propagation_results:
        eid = prop["entity_id"]
        impact = prop["impact"]
        entity = entity_map.get(eid, {})

        if impact < 0.01:
            continue

        layer = entity.get("layer", "infrastructure")
        country = entity.get("country", "GCC")
        gdp_weight = entity.get("gdp_weight", 0.01)
        criticality = entity.get("criticality", 0.5)

        # Sector elasticity
        elasticity = SECTOR_ELASTICITY.get(layer, DEFAULT_ELASTICITY)

        # Entity GDP contribution
        country_gdp = GCC_GDP.get(country, GCC_GDP["GCC"])
        entity_gdp = country_gdp * gdp_weight if country_gdp > 0 else total_gcc_gdp * gdp_weight

        # Loss = base_loss * impact * severity * criticality * elasticity_mult
        # Also factor in the entity's GDP weight for proportional allocation
        loss_fraction = impact * severity * criticality
        entity_loss = base_loss_usd * loss_fraction * (gdp_weight + 0.01)  # +0.01 min floor

        # Alternative: GDP-based loss
        gdp_loss = entity_gdp * elasticity * impact * severity
        # Take the larger of scenario-based and GDP-based
        final_loss = max(entity_loss, gdp_loss)

        # Loss as % of total GCC GDP
        loss_pct = (final_loss / total_gcc_gdp * 100) if total_gcc_gdp > 0 else 0.0

        # Peak day: closer entities hit earlier
        hop = prop.get("hop", 0)
        peak = max(1, peak_day_offset + hop)

        # Recovery: scales with impact and hop distance
        recovery = int(recovery_base_days * impact * severity) + hop * 2

        # Stress level: normalized 0–1
        stress = min(impact * severity * criticality, 1.0)

        # Confidence decreases with hop distance
        confidence = max(0.3, 1.0 - hop * 0.15)

        # Classification
        if stress > 0.7:
            classification = "CRITICAL"
        elif stress > 0.4:
            classification = "ELEVATED"
        elif stress > 0.2:
            classification = "MODERATE"
        elif stress > 0.05:
            classification = "LOW"
        else:
            classification = "NOMINAL"

        # Map layer to sector name for output
        sector_map = {
            "energy": "energy",
            "maritime": "maritime",
            "aviation": "aviation",
            "finance": "banking",  # default finance → banking
            "infrastructure": "trade",
            "government": "government",
        }
        sector = sector_map.get(layer, "trade")
        # Override for specific entity types
        if entity.get("entity_type") == "sector":
            if "insurance" in eid:
                sector = "insurance"
            elif "fintech" in eid:
                sector = "fintech"
            elif "banking" in eid:
                sector = "banking"

        results.append(FinancialImpact(
            entity_id=eid,
            entity_label=entity.get("label", eid),
            sector=sector,
            loss_usd=round(final_loss, 2),
            loss_pct_gdp=round(loss_pct, 6),
            peak_day=peak,
            recovery_days=recovery,
            confidence=round(confidence, 2),
            stress_level=round(stress, 4),
            classification=classification,
        ))

    results.sort(key=lambda x: x.loss_usd, reverse=True)
    return results


def compute_headline_loss(impacts: list[FinancialImpact]) -> dict:
    """Compute aggregate headline numbers."""
    total_loss = sum(i.loss_usd for i in impacts)
    peak_day = max((i.peak_day for i in impacts), default=0)
    max_recovery = max((i.recovery_days for i in impacts), default=0)
    avg_stress = sum(i.stress_level for i in impacts) / len(impacts) if impacts else 0.0

    return {
        "total_loss_usd": round(total_loss, 2),
        "peak_day": peak_day,
        "max_recovery_days": max_recovery,
        "average_stress": round(avg_stress, 4),
        "affected_entities": len(impacts),
        "critical_count": sum(1 for i in impacts if i.classification == "CRITICAL"),
        "elevated_count": sum(1 for i in impacts if i.classification == "ELEVATED"),
    }
