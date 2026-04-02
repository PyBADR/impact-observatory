"""
Impact Observatory | مرصد الأثر — Regulatory Engine (v4 §3.11)
Aggregate regulatory state computation with breach level classification.
"""

from datetime import datetime, timezone
from typing import List

from ...domain.models.scenario import Scenario
from ...domain.models.banking_stress import BankingStress
from ...domain.models.insurance_stress import InsuranceStress
from ...domain.models.fintech_stress import FintechStress
from ...domain.models.regulatory_state import RegulatoryState
from ...core.constants import LCR_MIN, CAR_MIN, SOLVENCY_MIN


def compute_regulatory_state(
    run_id: str,
    scenario: Scenario,
    banking_stresses: List[BankingStress],
    insurance_stresses: List[InsuranceStress],
    fintech_stresses: List[FintechStress],
) -> RegulatoryState:
    """
    v4 §3.11 — Compute aggregate regulatory state.

    Aggregates per-entity breach flags into system-wide breach level
    and determines mandatory regulatory actions.
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    # Aggregate LCR/NSFR from banking
    n_bank = len(banking_stresses) or 1
    agg_lcr = sum(s.lcr for s in banking_stresses) / n_bank if banking_stresses else 1.35
    agg_nsfr = sum(s.nsfr for s in banking_stresses) / n_bank if banking_stresses else 1.15
    agg_car = sum(s.capital_adequacy_ratio for s in banking_stresses) / n_bank if banking_stresses else 0.175

    # Aggregate solvency from insurance
    n_ins = len(insurance_stresses) or 1
    agg_solvency = sum(s.solvency_ratio for s in insurance_stresses) / n_ins if insurance_stresses else 1.8

    # Count total breaches across all sectors
    banking_breaches = sum(
        sum([s.breach_flags.lcr_breach, s.breach_flags.nsfr_breach,
             s.breach_flags.cet1_breach, s.breach_flags.car_breach])
        for s in banking_stresses
    )
    insurance_breaches = sum(
        sum([s.breach_flags.solvency_breach, s.breach_flags.reserve_breach,
             s.breach_flags.liquidity_breach])
        for s in insurance_stresses
    )
    fintech_breaches = sum(
        sum([s.breach_flags.availability_breach, s.breach_flags.settlement_breach,
             s.breach_flags.operational_risk_breach])
        for s in fintech_stresses
    )
    total_breaches = banking_breaches + insurance_breaches + fintech_breaches

    # Breach level classification
    if total_breaches >= 6:
        breach_level = "critical"
    elif total_breaches >= 4:
        breach_level = "major"
    elif total_breaches >= 2:
        breach_level = "minor"
    else:
        breach_level = "none"

    # Mandatory actions
    mandatory_actions: List[str] = []
    if agg_lcr < LCR_MIN:
        mandatory_actions.append("BASEL3_LCR_REMEDIATION")
    if agg_car < CAR_MIN:
        mandatory_actions.append("BASEL3_CONSERVATION_BUFFER")
    if agg_solvency < SOLVENCY_MIN:
        mandatory_actions.append("SOLVENCY_CAPITAL_REQUIREMENT")
    if breach_level in ("major", "critical"):
        mandatory_actions.append("SAMA_ALERT_" + breach_level.upper())
        mandatory_actions.append("IFRS17_LOSS_RECOGNITION")

    reporting_required = breach_level != "none"

    return RegulatoryState(
        run_id=run_id,
        timestamp=now,
        jurisdiction=scenario.regulatory_profile.jurisdiction,
        regulatory_version="2.4.0",
        aggregate_lcr=round(agg_lcr, 4),
        aggregate_nsfr=round(agg_nsfr, 4),
        aggregate_solvency_ratio=round(agg_solvency, 4),
        aggregate_capital_adequacy_ratio=round(agg_car, 4),
        breach_level=breach_level,
        mandatory_actions=mandatory_actions,
        reporting_required=reporting_required,
    )
