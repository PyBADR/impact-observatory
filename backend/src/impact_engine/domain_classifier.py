"""Domain classifier — maps sector analysis + exposure into AffectedDomain list.

All weights imported from config.py. No hardcoded constants.
"""
from __future__ import annotations

from typing import Any

from src.config import IE_DOMAIN_EXPOSURE_THRESHOLD, RISK_THRESHOLDS
from src.utils import classify_stress

# Sector Arabic labels (shared with explainability)
_SECTOR_ARABIC: dict[str, str] = {
    "energy":         "الطاقة",
    "maritime":       "الملاحة البحرية",
    "banking":        "الخدمات المصرفية",
    "insurance":      "التأمين",
    "fintech":        "التقنية المالية",
    "logistics":      "اللوجستيات",
    "infrastructure": "البنية التحتية",
    "government":     "الحكومة",
    "healthcare":     "الرعاية الصحية",
}


def _classify_risk(score: float) -> str:
    """Map a [0,1] score to risk classification label."""
    for label, (lo, hi) in RISK_THRESHOLDS.items():
        if lo <= score < hi:
            return label
    return "SEVERE" if score >= 0.80 else "NOMINAL"


def classify_domains(
    sector_analysis: list[dict[str, Any]],
    sector_exposure: dict[str, float],
    financial_impacts: list[dict[str, Any]],
    shock_nodes: list[str],
    node_sectors: dict[str, str],
    total_loss_usd: float,
) -> list[dict[str, Any]]:
    """Classify affected domains from sector analysis and exposure.

    Returns list of AffectedDomain-compatible dicts, sorted by loss descending.
    """
    # Identify primary-affected sectors (sectors that contain shock nodes)
    primary_sectors: set[str] = set()
    for sn in shock_nodes:
        s = node_sectors.get(sn, "")
        if s:
            primary_sectors.add(s)

    # Build sector → loss mapping from financial_impacts
    sector_loss: dict[str, float] = {}
    sector_entity_count: dict[str, int] = {}
    sector_critical_count: dict[str, int] = {}
    for fi in financial_impacts:
        s = fi.get("sector", "unknown")
        loss = float(fi.get("loss_usd", 0.0))
        sector_loss[s] = sector_loss.get(s, 0.0) + loss
        sector_entity_count[s] = sector_entity_count.get(s, 0) + 1
        if fi.get("classification") in ("HIGH", "SEVERE"):
            sector_critical_count[s] = sector_critical_count.get(s, 0) + 1

    # Build sector → stress from sector_analysis
    sector_stress: dict[str, float] = {}
    for sa in sector_analysis:
        s = sa.get("sector", "")
        sector_stress[s] = float(sa.get("stress", sa.get("exposure", 0.0)))

    # Collect all sectors
    all_sectors = set(sector_exposure.keys()) | set(sector_loss.keys()) | set(sector_stress.keys())

    domains: list[dict[str, Any]] = []
    for sector in all_sectors:
        exposure = sector_exposure.get(sector, 0.0)
        if exposure < IE_DOMAIN_EXPOSURE_THRESHOLD and sector not in primary_sectors:
            continue

        loss = sector_loss.get(sector, 0.0)
        stress = sector_stress.get(sector, 0.0)
        loss_pct = (loss / max(total_loss_usd, 1.0)) * 100.0

        domains.append({
            "domain": sector,
            "domain_ar": _SECTOR_ARABIC.get(sector, sector),
            "exposure_score": round(exposure, 4),
            "stress_score": round(stress, 4),
            "loss_usd": round(loss, 2),
            "loss_pct": round(loss_pct, 2),
            "entity_count": sector_entity_count.get(sector, 0),
            "critical_entity_count": sector_critical_count.get(sector, 0),
            "classification": _classify_risk(max(exposure, stress)),
            "is_primary_affected": sector in primary_sectors,
            "propagation_rank": 0,  # set after sorting
        })

    # Sort by loss descending
    domains.sort(key=lambda d: -d["loss_usd"])

    # Assign propagation rank
    for rank, d in enumerate(domains, start=1):
        d["propagation_rank"] = rank

    return domains
