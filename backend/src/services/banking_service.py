"""Service 6: banking_service — Banking Stress (ضغط القطاع البنكي).

Computes banking sector stress: liquidity, credit, FX, interbank contagion.
Target users: CRO, Treasury.

Time dynamics:
- Time to Liquidity Breach = base_hours / (liquidity_stress * severity)
- Capital adequacy impact = CAR_base * credit_stress * severity
"""

from __future__ import annotations

import logging
import math

from src.schemas.banking_stress import BankingStress
from src.schemas.financial_impact import FinancialImpact

logger = logging.getLogger(__name__)

# GCC Banking sector parameters
TOTAL_BANKING_ASSETS_USD = 2_800_000_000_000  # $2.8T total GCC banking assets
BASE_CAR = 18.0  # Average GCC CAR percentage
BASE_LIQUIDITY_HOURS = 720  # 30 days baseline liquidity


# Banking institution templates
BANKING_INSTITUTIONS = [
    {"id": "snb", "name": "Saudi National Bank", "name_ar": "البنك الأهلي السعودي", "country": "SA", "assets_usd": 280e9, "car_pct": 19.5},
    {"id": "al_rajhi", "name": "Al Rajhi Bank", "name_ar": "مصرف الراجحي", "country": "SA", "assets_usd": 195e9, "car_pct": 20.1},
    {"id": "fab", "name": "First Abu Dhabi Bank", "name_ar": "بنك أبوظبي الأول", "country": "AE", "assets_usd": 310e9, "car_pct": 16.8},
    {"id": "emirates_nbd", "name": "Emirates NBD", "name_ar": "الإمارات دبي الوطني", "country": "AE", "assets_usd": 210e9, "car_pct": 17.2},
    {"id": "qnb", "name": "Qatar National Bank", "name_ar": "بنك قطر الوطني", "country": "QA", "assets_usd": 340e9, "car_pct": 18.5},
    {"id": "nbk", "name": "National Bank of Kuwait", "name_ar": "بنك الكويت الوطني", "country": "KW", "assets_usd": 120e9, "car_pct": 17.8},
]


def compute_banking_stress(
    run_id: str,
    financial_impacts: list[FinancialImpact],
    severity: float,
    horizon_hours: int,
) -> BankingStress:
    """Compute banking sector stress from financial impacts.

    Chain: Financial Impact → Banking Exposure → Liquidity/Credit/FX Stress → Time to Breach
    """
    # Filter banking-related impacts
    banking_impacts = [i for i in financial_impacts if i.sector in ("banking", "energy", "trade")]
    total_banking_loss = sum(i.loss_usd for i in banking_impacts)

    # Exposure as fraction of total banking assets
    exposure_ratio = total_banking_loss / TOTAL_BANKING_ASSETS_USD if TOTAL_BANKING_ASSETS_USD > 0 else 0.0

    # Liquidity stress: driven by trade disruption and payment delays
    # Higher severity + more affected entities = more liquidity pressure
    trade_impacts = [i for i in financial_impacts if i.sector in ("trade", "maritime")]
    trade_loss = sum(i.loss_usd for i in trade_impacts)
    liquidity_stress = min(
        0.3 * exposure_ratio * 100  # scale exposure
        + 0.4 * severity
        + 0.3 * (trade_loss / 1e9) * 0.01,  # trade disruption component
        1.0,
    )

    # Credit stress: driven by energy/corporate exposure
    energy_impacts = [i for i in financial_impacts if i.sector == "energy"]
    energy_loss = sum(i.loss_usd for i in energy_impacts)
    credit_stress = min(
        0.35 * exposure_ratio * 100
        + 0.35 * severity * 0.8
        + 0.30 * (energy_loss / 1e9) * 0.01,
        1.0,
    )

    # FX stress: oil price linked to GCC pegs
    fx_stress = min(severity * 0.6 + exposure_ratio * 50, 1.0)

    # Interbank contagion: network effect
    n_critical = sum(1 for i in banking_impacts if i.classification in ("CRITICAL", "ELEVATED"))
    contagion = min(0.15 * n_critical + 0.3 * severity + 0.2 * credit_stress, 1.0)

    # Time to liquidity breach (hours)
    if liquidity_stress > 0.01:
        ttlb = BASE_LIQUIDITY_HOURS / (liquidity_stress * max(severity, 0.1))
    else:
        ttlb = float("inf")

    # Capital adequacy impact (percentage points)
    car_impact = BASE_CAR * credit_stress * severity * 0.15  # max ~15% of CAR

    # Aggregate stress: weighted combination
    aggregate = min(
        0.30 * liquidity_stress + 0.30 * credit_stress + 0.20 * fx_stress + 0.20 * contagion,
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

    # Affected institutions
    affected = []
    for bank in BANKING_INSTITUTIONS:
        bank_exposure = total_banking_loss * (bank["assets_usd"] / TOTAL_BANKING_ASSETS_USD)
        bank_stress = aggregate * (bank["assets_usd"] / TOTAL_BANKING_ASSETS_USD) * 5  # scale up for visibility
        bank_stress = min(bank_stress, 1.0)
        bank_car = bank["car_pct"] - car_impact * (bank["assets_usd"] / TOTAL_BANKING_ASSETS_USD) * 3

        # V1 Liquidity stress ratio: CashOutflows / AvailableLiquidity
        # CashOutflows ~ exposure × stress_factor × 0.3
        # AvailableLiquidity ~ exposure × (1 - stress) × 0.5
        bank_cash_outflows = bank_exposure * bank_stress * 0.3
        bank_avail_liquidity = bank_exposure * (1.0 - bank_stress) * 0.5
        if bank_avail_liquidity > 0:
            bank_liq_stress_ratio = bank_cash_outflows / bank_avail_liquidity
        else:
            bank_liq_stress_ratio = float("inf") if bank_cash_outflows > 0 else 0.0

        # V1 Capital stress ratio: Loss / Capital
        # Loss = exposure × stress
        # Capital = exposure × 0.12 (Basel III minimum CAR proxy)
        bank_loss = bank_exposure * bank_stress
        bank_capital = bank_exposure * 0.12
        if bank_capital > 0:
            bank_cap_stress_ratio = bank_loss / bank_capital
        else:
            bank_cap_stress_ratio = 0.0

        # Time to liquidity breach: hours until liquidity_stress_ratio > 1.0
        # Model: ratio grows linearly from current value at rate proportional to severity
        # ratio(t) = bank_liq_stress_ratio + severity * t / horizon_hours
        # Solve for ratio(t) = 1.0
        if bank_liq_stress_ratio >= 1.0:
            bank_ttlb = 0.0
        elif severity > 0:
            growth_rate = severity / max(horizon_hours, 1)
            gap = 1.0 - bank_liq_stress_ratio
            bank_ttlb = gap / growth_rate if growth_rate > 0 else float("inf")
        else:
            bank_ttlb = float("inf")

        if bank_stress > 0.05:
            affected.append({
                "id": bank["id"],
                "name": bank["name"],
                "name_ar": bank["name_ar"],
                "country": bank["country"],
                "exposure_usd": round(bank_exposure, 2),
                "stress": round(bank_stress, 4),
                "projected_car_pct": round(max(bank_car, 0), 2),
                "liquidity_stress_ratio": round(bank_liq_stress_ratio, 4),
                "capital_stress_ratio": round(bank_cap_stress_ratio, 4),
                "time_to_liquidity_breach_hours": round(bank_ttlb, 1),
            })

    # Aggregate liquidity stress ratio: CashOutflows / AvailableLiquidity
    agg_cash_outflows = total_banking_loss * liquidity_stress * 0.3
    agg_avail_liquidity = total_banking_loss * (1.0 - liquidity_stress) * 0.5
    if agg_avail_liquidity > 0:
        agg_liq_stress_ratio = agg_cash_outflows / agg_avail_liquidity
    else:
        agg_liq_stress_ratio = float("inf") if agg_cash_outflows > 0 else 0.0

    # Aggregate capital stress ratio: Loss / Capital (Basel III 12% proxy)
    agg_loss = total_banking_loss * aggregate
    agg_capital = total_banking_loss * 0.12
    if agg_capital > 0:
        agg_cap_stress_ratio = agg_loss / agg_capital
    else:
        agg_cap_stress_ratio = 0.0

    # Aggregate time to liquidity breach (hours until ratio > 1.0)
    if agg_liq_stress_ratio >= 1.0:
        agg_ttlb_est = 0.0
    elif severity > 0:
        growth_rate = severity / max(horizon_hours, 1)
        gap = 1.0 - agg_liq_stress_ratio
        agg_ttlb_est = gap / growth_rate if growth_rate > 0 else float("inf")
    else:
        agg_ttlb_est = float("inf")

    return BankingStress(
        run_id=run_id,
        total_exposure_usd=round(total_banking_loss, 2),
        liquidity_stress=round(liquidity_stress, 4),
        credit_stress=round(credit_stress, 4),
        fx_stress=round(fx_stress, 4),
        interbank_contagion=round(contagion, 4),
        time_to_liquidity_breach_hours=round(ttlb, 1),
        capital_adequacy_impact_pct=round(car_impact, 2),
        aggregate_stress=round(aggregate, 4),
        liquidity_stress_ratio=round(agg_liq_stress_ratio, 4),
        capital_stress_ratio=round(agg_cap_stress_ratio, 4),
        time_to_liquidity_breach_estimated_hours=round(agg_ttlb_est, 1),
        classification=classification,
        affected_institutions=affected,
    )
