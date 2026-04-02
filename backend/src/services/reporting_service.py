"""Service 11: reporting_service — Report Generation.

Generates structured reports in three modes:
- Executive Mode: headline numbers, top 3 actions
- Analyst Mode: full causal chain, all metrics
- Regulatory Brief Mode: compliance-focused, IFRS-17/Basel III aligned
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone

from src.schemas.financial_impact import FinancialImpact
from src.schemas.banking_stress import BankingStress
from src.schemas.insurance_stress import InsuranceStress
from src.schemas.fintech_stress import FintechStress
from src.schemas.decision import DecisionPlan
from src.schemas.explanation import ExplanationPack
from src.i18n.labels import get_label

logger = logging.getLogger(__name__)


def generate_executive_report(
    run_id: str,
    financial_impacts: list[FinancialImpact],
    banking: BankingStress,
    insurance: InsuranceStress,
    fintech: FintechStress,
    decision_plan: DecisionPlan,
    explanation: ExplanationPack,
    lang: str = "en",
) -> dict:
    """Executive Mode: headline numbers + top 3 actions.

    Designed for: Board, C-suite, Government advisors.
    """
    total_loss = sum(i.loss_usd for i in financial_impacts)
    peak_day = max((i.peak_day for i in financial_impacts), default=0)
    time_to_failure = min(
        banking.time_to_liquidity_breach_hours,
        insurance.time_to_insolvency_hours,
        fintech.time_to_payment_failure_hours,
    )

    return {
        "mode": "executive",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lang": lang,
        "headline": {
            get_label("headline_loss", lang): f"${total_loss/1e9:.2f}B",
            get_label("peak_day", lang): f"Day {peak_day}",
            get_label("time_to_failure", lang): f"{time_to_failure:.0f}h" if time_to_failure < float("inf") else "N/A",
        },
        "sector_stress": {
            get_label("banking_stress", lang): {
                "level": banking.classification,
                "score": banking.aggregate_stress,
            },
            get_label("insurance_stress", lang): {
                "level": insurance.classification,
                "score": insurance.aggregate_stress,
            },
            get_label("fintech_stress", lang): {
                "level": fintech.classification,
                "score": fintech.aggregate_stress,
            },
        },
        get_label("decision_actions", lang): [
            {
                "action": a.action if lang == "en" else (a.action_ar or a.action),
                "owner": a.owner,
                "priority": a.priority,
                "urgency": a.urgency,
            }
            for a in decision_plan.actions[:3]
        ],
        "narrative": explanation.narrative_en if lang == "en" else explanation.narrative_ar,
    }


def generate_analyst_report(
    run_id: str,
    financial_impacts: list[FinancialImpact],
    banking: BankingStress,
    insurance: InsuranceStress,
    fintech: FintechStress,
    decision_plan: DecisionPlan,
    explanation: ExplanationPack,
    lang: str = "en",
) -> dict:
    """Analyst Mode: full causal chain, all metrics, all entities.

    Designed for: Risk analysts, data scientists, quants.
    """
    return {
        "mode": "analyst",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lang": lang,
        "financial_impacts": [i.model_dump() for i in financial_impacts],
        "banking": banking.model_dump(),
        "insurance": insurance.model_dump(),
        "fintech": fintech.model_dump(),
        "decisions": decision_plan.model_dump(),
        "explanation": explanation.model_dump(),
        "causal_chain": [s.model_dump() for s in explanation.causal_chain],
    }


def generate_regulatory_brief(
    run_id: str,
    financial_impacts: list[FinancialImpact],
    banking: BankingStress,
    insurance: InsuranceStress,
    fintech: FintechStress,
    decision_plan: DecisionPlan,
    explanation: ExplanationPack,
    lang: str = "en",
) -> dict:
    """Regulatory Brief Mode: compliance-focused.

    Designed for: Central banks (SAMA, CBUAE), regulators (CMA), insurance authorities.
    Includes: Basel III/IFRS-17 metrics, time-to-breach, capital adequacy.
    """
    total_loss = sum(i.loss_usd for i in financial_impacts)
    critical_entities = [i for i in financial_impacts if i.classification == "CRITICAL"]

    return {
        "mode": "regulatory_brief",
        "run_id": run_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lang": lang,
        "classification": "CONFIDENTIAL",
        "summary": {
            "total_projected_loss_usd": round(total_loss, 2),
            "critical_entities": len(critical_entities),
            "earliest_failure_hours": min(
                banking.time_to_liquidity_breach_hours,
                insurance.time_to_insolvency_hours,
                fintech.time_to_payment_failure_hours,
            ),
        },
        "basel_iii_metrics": {
            "capital_adequacy_impact_pct": banking.capital_adequacy_impact_pct,
            "liquidity_coverage_stress": banking.liquidity_stress,
            "net_stable_funding_stress": banking.credit_stress * 0.8,
            "leverage_ratio_impact": banking.aggregate_stress * 0.5,
        },
        "ifrs17_metrics": {
            "risk_adjustment_change_pct": insurance.ifrs17_risk_adjustment_pct,
            "loss_ratio_projected": insurance.loss_ratio,
            "combined_ratio_projected": insurance.combined_ratio,
            "reinsurance_trigger": insurance.reinsurance_trigger,
        },
        "payment_system_metrics": {
            "payment_volume_impact_pct": fintech.payment_volume_impact_pct,
            "settlement_delay_hours": fintech.settlement_delay_hours,
            "cross_border_disruption": fintech.cross_border_disruption,
        },
        "recommended_regulatory_actions": [
            {
                "action": a.action if lang == "en" else (a.action_ar or a.action),
                "owner": a.owner,
                "urgency": a.urgency,
                "regulatory_risk": a.regulatory_risk,
            }
            for a in decision_plan.all_actions
            if a.regulatory_risk > 0.5
        ],
        "affected_institutions": banking.affected_institutions,
        "affected_insurance_lines": insurance.affected_lines,
    }
