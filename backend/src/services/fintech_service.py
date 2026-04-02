"""Service 8: fintech_service — Fintech Disruption (اضطراب الفنتك).

Computes fintech/payments sector stress: payment volumes, settlement delays,
API availability, cross-border disruption.
Target users: Ops, Risk Manager.

Time dynamics: Time to Payment Failure = base / (disruption_index * severity)
"""

from __future__ import annotations

import logging
import math

from src.schemas.fintech_stress import FintechStress
from src.schemas.financial_impact import FinancialImpact

logger = logging.getLogger(__name__)

# GCC Fintech parameters
DAILY_PAYMENT_VOLUME_USD = 12_000_000_000  # $12B daily
BASE_SETTLEMENT_HOURS = 4.0  # T+0 to T+1
BASE_PAYMENT_FAILURE_HOURS = 168  # 7 days baseline

FINTECH_PLATFORMS = [
    {"id": "stc_pay", "name": "STC Pay", "name_ar": "STC Pay", "country": "SA", "volume_share": 0.15, "cross_border": 0.20},
    {"id": "apple_pay_gcc", "name": "Apple Pay GCC", "name_ar": "Apple Pay الخليج", "country": "GCC", "volume_share": 0.12, "cross_border": 0.10},
    {"id": "benefit_pay", "name": "BenefitPay", "name_ar": "بنفت باي", "country": "BH", "volume_share": 0.05, "cross_border": 0.30},
    {"id": "mada", "name": "mada", "name_ar": "مدى", "country": "SA", "volume_share": 0.25, "cross_border": 0.05},
    {"id": "uae_pass_pay", "name": "UAE Pass Pay", "name_ar": "UAE Pass Pay", "country": "AE", "volume_share": 0.10, "cross_border": 0.15},
    {"id": "swift_gcc", "name": "SWIFT GCC Hub", "name_ar": "سويفت الخليج", "country": "GCC", "volume_share": 0.20, "cross_border": 0.90},
    {"id": "buna", "name": "Buna (Arab Payment Platform)", "name_ar": "بنى", "country": "GCC", "volume_share": 0.08, "cross_border": 0.85},
]


def compute_fintech_stress(
    run_id: str,
    financial_impacts: list[FinancialImpact],
    severity: float,
    horizon_hours: int,
) -> FintechStress:
    """Compute fintech sector stress from financial impacts.

    Chain: Financial Impact → Payment Volume Drop → Settlement Delay →
           API Disruption → Cross-Border Failure → Time to Payment Failure
    """
    # Fintech-relevant impacts
    fintech_impacts = [i for i in financial_impacts if i.sector in ("fintech", "banking", "trade")]
    total_fintech_loss = sum(i.loss_usd for i in fintech_impacts)
    avg_stress = sum(i.stress_level for i in fintech_impacts) / max(len(fintech_impacts), 1)

    # Payment volume impact: driven by banking stress and trade disruption
    trade_impacts = [i for i in financial_impacts if i.sector in ("trade", "maritime")]
    trade_loss_ratio = sum(i.loss_usd for i in trade_impacts) / (DAILY_PAYMENT_VOLUME_USD * 30)  # monthly
    payment_volume_impact = min(
        0.4 * severity + 0.3 * avg_stress + 0.3 * trade_loss_ratio * 100,
        80.0,  # max 80% drop
    )

    # Settlement delay: base + additional hours from disruption
    disruption_factor = severity * avg_stress
    settlement_delay = BASE_SETTLEMENT_HOURS * disruption_factor * 3  # up to 3x base delay additional

    # API availability: infrastructure-dependent
    infra_impacts = [i for i in financial_impacts if i.sector in ("fintech", "banking")]
    infra_stress = sum(i.stress_level for i in infra_impacts) / max(len(infra_impacts), 1)
    api_availability = max(100.0 - (severity * 30 + infra_stress * 20), 50.0)  # min 50%

    # Cross-border disruption: SWIFT and correspondent banking
    cross_border = min(
        0.35 * severity + 0.30 * avg_stress + 0.35 * (payment_volume_impact / 100),
        1.0,
    )

    # Digital banking stress
    digital_stress = min(
        0.4 * (1.0 - api_availability / 100) + 0.3 * severity + 0.3 * disruption_factor,
        1.0,
    )

    # Time to payment failure
    disruption_index = max(payment_volume_impact / 100 * severity, 0.01)
    time_to_payment_failure = BASE_PAYMENT_FAILURE_HOURS / disruption_index

    # Aggregate stress
    aggregate = min(
        0.25 * (payment_volume_impact / 100)
        + 0.20 * min(settlement_delay / 24, 1.0)
        + 0.20 * (1.0 - api_availability / 100)
        + 0.20 * cross_border
        + 0.15 * digital_stress,
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

    # Affected platforms
    affected = []
    for platform in FINTECH_PLATFORMS:
        p_stress = aggregate * (0.5 + 0.5 * platform["volume_share"])
        p_cross_border_hit = cross_border * platform["cross_border"]
        p_total = min(p_stress + p_cross_border_hit * 0.5, 1.0)
        if p_total > 0.05:
            affected.append({
                "id": platform["id"],
                "name": platform["name"],
                "name_ar": platform["name_ar"],
                "country": platform["country"],
                "volume_impact_pct": round(payment_volume_impact * platform["volume_share"], 2),
                "cross_border_stress": round(p_cross_border_hit, 4),
                "stress": round(p_total, 4),
            })

    return FintechStress(
        run_id=run_id,
        payment_volume_impact_pct=round(payment_volume_impact, 2),
        settlement_delay_hours=round(settlement_delay, 2),
        api_availability_pct=round(api_availability, 2),
        cross_border_disruption=round(cross_border, 4),
        digital_banking_stress=round(digital_stress, 4),
        time_to_payment_failure_hours=round(time_to_payment_failure, 1),
        aggregate_stress=round(aggregate, 4),
        classification=classification,
        affected_platforms=affected,
    )
