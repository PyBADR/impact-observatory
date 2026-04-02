"""Service 7: insurance_service — Insurance Stress (ضغط التأمين).

Wraps existing insurance_intelligence engines:
- portfolio_exposure
- claims_surge: ΔClaims = Base * (1 + 0.45*S + 0.30*Stress + 0.25*U)
- severity_projection: sigmoid(0.35*E + 0.40*I + 0.25*C - 0.50)
- underwriting_watch: loss_ratio thresholds

IFRS-17 aligned. Target users: Actuary, Risk Manager.
"""

from __future__ import annotations

import logging
import math

from src.schemas.insurance_stress import InsuranceStress
from src.schemas.financial_impact import FinancialImpact

logger = logging.getLogger(__name__)

# GCC Insurance market parameters
TOTAL_GWP_USD = 32_000_000_000  # $32B GCC gross written premium
AVERAGE_LOSS_RATIO = 0.62
AVERAGE_EXPENSE_RATIO = 0.28
RESERVE_MONTHS = 6  # Average months of reserves

INSURANCE_LINES = [
    {"id": "marine_cargo", "name": "Marine Cargo", "name_ar": "شحن بحري", "gwp_share": 0.15, "sensitivity": 0.90},
    {"id": "marine_hull", "name": "Marine Hull", "name_ar": "هياكل بحرية", "gwp_share": 0.08, "sensitivity": 0.85},
    {"id": "energy_property", "name": "Energy Property", "name_ar": "ممتلكات الطاقة", "gwp_share": 0.12, "sensitivity": 0.88},
    {"id": "trade_credit", "name": "Trade Credit", "name_ar": "ائتمان تجاري", "gwp_share": 0.10, "sensitivity": 0.75},
    {"id": "aviation", "name": "Aviation", "name_ar": "طيران", "gwp_share": 0.06, "sensitivity": 0.70},
    {"id": "business_interruption", "name": "Business Interruption", "name_ar": "انقطاع الأعمال", "gwp_share": 0.09, "sensitivity": 0.82},
    {"id": "political_risk", "name": "Political Risk", "name_ar": "مخاطر سياسية", "gwp_share": 0.04, "sensitivity": 0.95},
    {"id": "cyber", "name": "Cyber Insurance", "name_ar": "تأمين سيبراني", "gwp_share": 0.03, "sensitivity": 0.60},
]


def compute_insurance_stress(
    run_id: str,
    financial_impacts: list[FinancialImpact],
    severity: float,
    horizon_hours: int,
) -> InsuranceStress:
    """Compute insurance sector stress from financial impacts.

    Chain: Financial Impact → Portfolio Exposure → Claims Surge → Severity → UW Watch
    """
    # Portfolio exposure: sum of insured losses
    insured_impacts = [i for i in financial_impacts if i.sector in ("insurance", "maritime", "energy", "aviation")]
    portfolio_exposure = sum(i.loss_usd for i in insured_impacts) * 0.6  # ~60% insured fraction

    # Claims surge multiplier: ΔClaims = Base * (1 + χ1*S + χ2*Stress + χ3*Uncertainty)
    avg_stress = sum(i.stress_level for i in insured_impacts) / max(len(insured_impacts), 1)
    uncertainty = 0.3 + 0.2 * severity  # uncertainty rises with severity
    claims_surge = 1.0 + 0.45 * severity + 0.30 * avg_stress + 0.25 * uncertainty

    # Severity index: sigmoid(0.35*Exposure + 0.40*Impact + 0.25*Claims - 0.50)
    exposure_norm = min(portfolio_exposure / (TOTAL_GWP_USD * 0.5), 1.0)
    impact_norm = avg_stress
    claims_norm = min((claims_surge - 1.0) / 2.0, 1.0)
    severity_input = 0.35 * exposure_norm + 0.40 * impact_norm + 0.25 * claims_norm - 0.50
    severity_index = 1.0 / (1.0 + math.exp(-10.0 * severity_input))

    # Loss ratio projection
    projected_loss_ratio = AVERAGE_LOSS_RATIO * claims_surge

    # Combined ratio
    combined_ratio = projected_loss_ratio + AVERAGE_EXPENSE_RATIO

    # Underwriting status
    if combined_ratio > 1.05:
        uw_status = "critical"
    elif combined_ratio > 0.95:
        uw_status = "warning"
    elif projected_loss_ratio > 0.85:
        uw_status = "warning"
    else:
        uw_status = "normal"

    # Time to insolvency: months of reserves / burn rate acceleration
    burn_acceleration = claims_surge - 1.0  # additional burn above baseline
    if burn_acceleration > 0.01:
        months_to_deplete = RESERVE_MONTHS / (1.0 + burn_acceleration * 2)
        time_to_insolvency = months_to_deplete * 30 * 24  # convert to hours
    else:
        time_to_insolvency = float("inf")

    # Reinsurance trigger: if claims surge > 2x
    reinsurance_trigger = claims_surge > 2.0

    # IFRS-17 risk adjustment: increases proportionally to severity
    ifrs17_ra = severity_index * 5.0  # up to 5 percentage points

    # Aggregate stress
    aggregate = min(
        0.30 * severity_index + 0.25 * min(exposure_norm, 1.0) + 0.25 * (claims_surge - 1.0) / 2.0 + 0.20 * (1.0 if uw_status == "critical" else 0.5 if uw_status == "warning" else 0.0),
        1.0,
    )

    # Classification
    if aggregate > 0.7:
        classification = "CRITICAL"
    elif aggregate > 0.4:
        classification = "ELEVATED"
    elif aggregate > 0.2:
        classification = "MODERATE"
    elif aggregate > 0.05:
        classification = "LOW"
    else:
        classification = "NOMINAL"

    # Affected lines
    affected = []
    for line in INSURANCE_LINES:
        line_exposure = portfolio_exposure * line["gwp_share"] * line["sensitivity"]
        line_surge = claims_surge * line["sensitivity"]
        line_stress = min(aggregate * line["sensitivity"], 1.0)
        if line_stress > 0.05:
            affected.append({
                "id": line["id"],
                "name": line["name"],
                "name_ar": line["name_ar"],
                "exposure_usd": round(line_exposure, 2),
                "claims_surge": round(line_surge, 2),
                "stress": round(line_stress, 4),
            })

    return InsuranceStress(
        run_id=run_id,
        portfolio_exposure_usd=round(portfolio_exposure, 2),
        claims_surge_multiplier=round(claims_surge, 4),
        severity_index=round(severity_index, 4),
        loss_ratio=round(projected_loss_ratio, 4),
        combined_ratio=round(combined_ratio, 4),
        underwriting_status=uw_status,
        time_to_insolvency_hours=round(time_to_insolvency, 1),
        reinsurance_trigger=reinsurance_trigger,
        ifrs17_risk_adjustment_pct=round(ifrs17_ra, 2),
        aggregate_stress=round(aggregate, 4),
        classification=classification,
        affected_lines=affected,
    )
