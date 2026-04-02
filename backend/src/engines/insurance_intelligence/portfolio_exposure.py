"""Portfolio exposure scoring.

E_ins_p = γ1*TIV_p + γ2*RouteDependency_p + γ3*RegionRisk_p + γ4*ClaimsElasticity_p

Where:
    γ1 = 0.30 (total insured value weight)
    γ2 = 0.25 (route dependency weight)
    γ3 = 0.25 (region risk weight)
    γ4 = 0.20 (claims elasticity weight)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import (
    INSURANCE_EXPOSURE,
    InsuranceExposureWeights,
)


@dataclass
class PortfolioExposureResult:
    """Exposure result for a single portfolio or policy."""
    portfolio_id: str
    exposure_score: float
    tiv_contribution: float
    route_dependency_contribution: float
    region_risk_contribution: float
    claims_elasticity_contribution: float
    classification: str  # CRITICAL / HIGH / MODERATE / LOW
    recommendations: list[str]


def compute_portfolio_exposure(
    portfolio_id: str,
    tiv_normalized: float,
    route_dependency: float,
    region_risk: float,
    claims_elasticity: float,
    weights: InsuranceExposureWeights | None = None,
) -> PortfolioExposureResult:
    """E_ins_p = γ1*TIV + γ2*RouteDep + γ3*RegionRisk + γ4*ClaimsElasticity"""
    w = weights or INSURANCE_EXPOSURE

    tiv_c = w.tiv * np.clip(tiv_normalized, 0, 1)
    rd_c = w.route_dependency * np.clip(route_dependency, 0, 1)
    rr_c = w.region_risk * np.clip(region_risk, 0, 1)
    ce_c = w.claims_elasticity * np.clip(claims_elasticity, 0, 1)

    score = float(np.clip(tiv_c + rd_c + rr_c + ce_c, 0.0, 1.0))

    if score >= 0.7:
        cls = "CRITICAL"
    elif score >= 0.5:
        cls = "HIGH"
    elif score >= 0.3:
        cls = "MODERATE"
    else:
        cls = "LOW"

    recs = []
    if tiv_c > 0.2:
        recs.append(f"High TIV concentration ({tiv_c:.2f}). Consider reinsurance diversification.")
    if rd_c > 0.15:
        recs.append(f"Route dependency elevated ({rd_c:.2f}). Monitor chokepoint alternatives.")
    if rr_c > 0.15:
        recs.append(f"Region risk high ({rr_c:.2f}). Review geographic exposure limits.")
    if not recs:
        recs.append("Exposure within policy limits.")

    return PortfolioExposureResult(
        portfolio_id=portfolio_id,
        exposure_score=score,
        tiv_contribution=float(tiv_c),
        route_dependency_contribution=float(rd_c),
        region_risk_contribution=float(rr_c),
        claims_elasticity_contribution=float(ce_c),
        classification=cls,
        recommendations=recs,
    )


def compute_portfolio_exposure_batch(
    portfolio_ids: list[str],
    tiv_values: NDArray[np.float64],
    route_deps: NDArray[np.float64],
    region_risks: NDArray[np.float64],
    claims_elasticities: NDArray[np.float64],
) -> tuple[NDArray[np.float64], list[PortfolioExposureResult]]:
    """Batch exposure scoring."""
    results = []
    for i, pid in enumerate(portfolio_ids):
        r = compute_portfolio_exposure(
            pid, tiv_values[i], route_deps[i], region_risks[i], claims_elasticities[i]
        )
        results.append(r)
    scores = np.array([r.exposure_score for r in results], dtype=np.float64)
    return scores, results
