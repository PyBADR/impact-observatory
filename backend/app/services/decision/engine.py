"""Decision Engine — 5-Factor Priority Formula for GCC Decision Intelligence

Strategic response framework module. Synthesizes sector stress signals and financial
impact to recommend top-3 priority mitigation and response actions. Implements
5-factor multi-objective optimization:

  Priority = 0.25×Urgency + 0.30×Value + 0.20×(1-RegRisk) + 0.15×Feasibility + 0.10×TimeEffect

Where:
  Urgency     = max(0, 1 - time_to_act / time_to_failure)
  Value       = (loss_avoided - cost) / loss_baseline
  RegRisk     = regulatory_risk (0-1, inverted: lower risk → higher priority)
  Feasibility = execution_probability × resource_availability
  TimeEffect  = exp(-λ × time_to_effect_hours)   [λ = 0.01]

Return: TOP 3 ACTIONS ONLY — sorted by Priority descending
"""

import math
from typing import List
from app.schemas.observatory import (
    ScenarioInput,
    FinancialImpact,
    BankingStress,
    InsuranceStress,
    FintechStress,
    DecisionAction,
)


def compute_decisions(
    scenario: ScenarioInput,
    financial_impact: FinancialImpact,
    banking: BankingStress,
    insurance: InsuranceStress,
    fintech: FintechStress,
) -> List[DecisionAction]:
    """
    Compute top 3 priority actions using multi-objective optimization.
    
    Candidate action pool includes 10 potential interventions across sectors:
    - Emergency liquidity facility (banking)
    - Reinsurance treaty activation (insurance)
    - Payment system backup activation (fintech)
    - Oil hedging position adjustment (macroeconomic)
    - Foreign reserve deployment (banking)
    - Insurance premium moratorium (insurance/regulatory)
    - Digital payment corridor activation (fintech)
    - Cross-border settlement override (fintech/regulatory)
    - Maritime insurance pool activation (insurance)
    - Emergency trade finance facility (banking)
    
    Decision priority formula (5-factor):
        Priority = 0.25×Urgency + 0.30×Value + 0.20×(1-RegRisk) + 0.15×Feasibility + 0.10×TimeEffect

    Urgency = max(0, 1 - time_to_act / time_to_failure)
    Value = (loss_avoided - cost) / loss_baseline
    
    Args:
        scenario: Event scenario
        financial_impact: Quantified financial impact
        banking: Banking sector stress
        insurance: Insurance sector stress
        fintech: Fintech sector stress
        
    Returns:
        List of top 3 DecisionAction sorted by priority (highest first)
    """
    
    # Time to failure in hours (from financial impact)
    time_to_failure_hours = financial_impact.time_to_failure_days * 24.0
    loss_baseline = max(1.0, financial_impact.headline_loss_usd)

    # Build candidate action pool with full metadata including feasibility factors
    # Each action includes:
    #   execution_probability: institutional readiness (0-1)
    #   resource_availability: funding/staff availability (0-1)
    #   time_to_effect_hours: hours until action produces measurable impact
    candidates: List[dict] = [
        {
            "id": "emg_liquidity_facility",
            "title": "Emergency Liquidity Facility",
            "title_ar": "مرفق السيولة الطارئة",
            "cost_usd": 2.5e9,
            "loss_avoided_usd": 45e9,
            "regulatory_risk": 0.15,
            "sector": "banking",
            "description": "Central bank liquidity facility providing USD/AED funding to commercial banks at emergency rates to prevent interbank market freeze.",
            "applies_when": banking.stress_level in ["HIGH", "CRITICAL"],
            "time_to_act_hours": 24,
            "execution_probability": 0.90,
            "resource_availability": 0.85,
            "time_to_effect_hours": 12,
        },
        {
            "id": "reinsurance_treaty_activation",
            "title": "Reinsurance Treaty Activation",
            "title_ar": "تفعيل معاهدة إعادة التأمين",
            "cost_usd": 800e6,
            "loss_avoided_usd": 12e9,
            "regulatory_risk": 0.20,
            "sector": "insurance",
            "description": "Activate catastrophe reinsurance treaties to transfer aggregate claim exposure and preserve insurer solvency margin.",
            "applies_when": insurance.reinsurance_trigger or insurance.stress_level in ["HIGH", "CRITICAL"],
            "time_to_act_hours": 48,
            "execution_probability": 0.85,
            "resource_availability": 0.80,
            "time_to_effect_hours": 72,
        },
        {
            "id": "payment_backup_activation",
            "title": "Payment System Backup Activation",
            "title_ar": "تفعيل نسخة احتياطية من نظام الدفع",
            "cost_usd": 350e6,
            "loss_avoided_usd": 8e9,
            "regulatory_risk": 0.10,
            "sector": "fintech",
            "description": "Activate geographic/provider redundancy for payment gateways to maintain transaction processing above 85% capacity.",
            "applies_when": fintech.stress_level in ["HIGH", "CRITICAL"],
            "time_to_act_hours": 12,
            "execution_probability": 0.95,
            "resource_availability": 0.90,
            "time_to_effect_hours": 6,
        },
        {
            "id": "oil_hedging_adjustment",
            "title": "Oil Hedging Position Adjustment",
            "title_ar": "تعديل مركز التحوط من الزيت",
            "cost_usd": 1.2e9,
            "loss_avoided_usd": 18e9,
            "regulatory_risk": 0.25,
            "sector": "macroeconomic",
            "description": "Deploy sovereign wealth fund hedging instruments (puts, collars) to establish oil price floor and stabilize fiscal revenue expectations.",
            "applies_when": financial_impact.severity_code in ["HIGH", "CRITICAL"],
            "time_to_act_hours": 72,
            "execution_probability": 0.75,
            "resource_availability": 0.70,
            "time_to_effect_hours": 120,
        },
        {
            "id": "fx_reserve_deployment",
            "title": "Foreign Reserve Deployment",
            "title_ar": "نشر احتياطيات الصرف الأجنبي",
            "cost_usd": 15e9,
            "loss_avoided_usd": 65e9,
            "regulatory_risk": 0.30,
            "sector": "banking",
            "description": "Deploy central bank FX reserves to maintain essential import cover (food, fuel, medicines) and stabilize currency peg.",
            "applies_when": banking.fx_reserve_drawdown_pct > 15,
            "time_to_act_hours": 48,
            "execution_probability": 0.80,
            "resource_availability": 0.75,
            "time_to_effect_hours": 48,
        },
        {
            "id": "insurance_premium_moratorium",
            "title": "Insurance Premium Moratorium",
            "title_ar": "وقف دفع أقساط التأمين المؤقت",
            "cost_usd": 400e6,
            "loss_avoided_usd": 5e9,
            "regulatory_risk": 0.45,
            "sector": "insurance",
            "description": "Temporary regulatory moratorium on premium payments to corporate policyholders to preserve cash flow and prevent cascade defaults.",
            "applies_when": insurance.stress_level == "CRITICAL",
            "time_to_act_hours": 24,
            "execution_probability": 0.70,
            "resource_availability": 0.60,
            "time_to_effect_hours": 48,
        },
        {
            "id": "digital_payment_corridor",
            "title": "Digital Payment Corridor Activation",
            "title_ar": "تفعيل ممر الدفع الرقمي",
            "cost_usd": 500e6,
            "loss_avoided_usd": 6e9,
            "regulatory_risk": 0.15,
            "sector": "fintech",
            "description": "Activate bilateral/multilateral digital payment corridors (instant settlement) to bypass traditional banking channels and accelerate trade settlement.",
            "applies_when": fintech.stress_level in ["HIGH", "CRITICAL"],
            "time_to_act_hours": 72,
            "execution_probability": 0.80,
            "resource_availability": 0.75,
            "time_to_effect_hours": 96,
        },
        {
            "id": "settlement_override",
            "title": "Cross-Border Settlement Override",
            "title_ar": "تجاوز تسوية الحدود",
            "cost_usd": 250e6,
            "loss_avoided_usd": 4e9,
            "regulatory_risk": 0.55,
            "sector": "fintech",
            "description": "Temporary regulatory override of settlement verification requirements to accelerate critical international trade payments.",
            "applies_when": fintech.payment_failure_rate > 0.08,
            "time_to_act_hours": 96,
            "execution_probability": 0.60,
            "resource_availability": 0.50,
            "time_to_effect_hours": 120,
        },
        {
            "id": "maritime_insurance_pool",
            "title": "Maritime Insurance Pool Activation",
            "title_ar": "تفعيل تجمع التأمين البحري",
            "cost_usd": 1.5e9,
            "loss_avoided_usd": 10e9,
            "regulatory_risk": 0.25,
            "sector": "insurance",
            "description": "Activate GCC-regional maritime insurance pool to mutually cover containerized cargo and tanker hull risks above individual capacity.",
            "applies_when": insurance.stress_level in ["HIGH", "CRITICAL"],
            "time_to_act_hours": 48,
            "execution_probability": 0.75,
            "resource_availability": 0.70,
            "time_to_effect_hours": 72,
        },
        {
            "id": "trade_finance_facility",
            "title": "Emergency Trade Finance Facility",
            "title_ar": "مرفق تمويل التجارة الطارئة",
            "cost_usd": 5e9,
            "loss_avoided_usd": 35e9,
            "regulatory_risk": 0.20,
            "sector": "banking",
            "description": "Emergency trade finance facility providing USD-denominated letters of credit at subsidized rates to maintain essential import flows.",
            "applies_when": financial_impact.time_to_failure_days < 10,
            "time_to_act_hours": 72,
            "execution_probability": 0.85,
            "resource_availability": 0.80,
            "time_to_effect_hours": 96,
        },
    ]

    # Filter applicable actions based on stress levels
    applicable = []
    for action in candidates:
        if action["applies_when"]:
            applicable.append(action)

    # If no stress-triggered actions, include top 3 by value/cost ratio
    if not applicable:
        applicable = sorted(
            candidates,
            key=lambda x: (x["loss_avoided_usd"] - x["cost_usd"]) / max(1, x["cost_usd"]),
            reverse=True
        )[:3]

    # 5-Factor Priority Formula
    # Priority = 0.25×Urgency + 0.30×Value + 0.20×(1-RegRisk) + 0.15×Feasibility + 0.10×TimeEffect
    LAMBDA = 0.01  # Time decay constant (per hour)

    for action in applicable:
        # Factor 1: Urgency — how close to failure vs. time needed to act
        urgency = max(0.0, 1.0 - (action["time_to_act_hours"] / max(1.0, time_to_failure_hours)))

        # Factor 2: Value — net benefit relative to total loss baseline
        raw_value = (action["loss_avoided_usd"] - action["cost_usd"]) / loss_baseline
        value = min(1.0, max(0.0, raw_value))

        # Factor 3: Regulatory feasibility — lower risk = higher score
        reg_feasibility = 1.0 - action["regulatory_risk"]

        # Factor 4: Feasibility — execution probability × resource availability
        feasibility = action["execution_probability"] * action["resource_availability"]

        # Factor 5: Time effect — exponential decay on time to measurable impact
        time_effect = math.exp(-LAMBDA * action["time_to_effect_hours"])

        # Weighted priority
        priority = (
            0.25 * urgency +
            0.30 * value +
            0.20 * reg_feasibility +
            0.15 * feasibility +
            0.10 * time_effect
        )

        action["priority_score"] = round(min(1.0, max(0.0, priority)), 4)
        action["urgency"] = round(urgency, 4)
        action["value"] = round(value, 4)
        action["feasibility"] = round(feasibility, 4)
        action["time_effect"] = round(time_effect, 4)

    # Sort by priority score (descending) and take top 3
    sorted_actions = sorted(applicable, key=lambda x: x["priority_score"], reverse=True)[:3]

    # Build DecisionAction instances with rank and governance status
    decisions = []
    for rank, action in enumerate(sorted_actions, start=1):
        decision = DecisionAction(
            id=action["id"],
            rank=rank,
            title=action["title"],
            title_ar=action["title_ar"],
            urgency=action["urgency"],
            value=action["value"],
            priority=action["priority_score"],
            feasibility=action["feasibility"],
            time_effect=action["time_effect"],
            cost_usd=action["cost_usd"],
            loss_avoided_usd=action["loss_avoided_usd"],
            regulatory_risk=action["regulatory_risk"],
            sector=action["sector"],
            description=action["description"],
            status="PENDING_REVIEW",
        )
        decisions.append(decision)

    return decisions
