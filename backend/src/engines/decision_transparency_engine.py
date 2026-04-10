"""
Impact Observatory | مرصد الأثر
Decision Transparency Engine — Phase 2+3 of Decision Trust Layer.

Computes cost-benefit transparency and loss-inducing detection
for every decision action. All numbers come from REAL simulation outputs.

Classification logic:
  ratio = cost / benefit
  - ratio < 1        → HIGH_VALUE
  - 1 ≤ ratio ≤ 5    → ACCEPTABLE
  - 5 < ratio ≤ 20   → LOW_EFFICIENCY
  - ratio > 20 OR net_value < 0  → LOSS_INDUCING
"""
from __future__ import annotations

import logging
from typing import Any

from src.utils import format_loss_usd
from src.config import (
    DL_P_W1, DL_P_W2, DL_P_W3, DL_P_W4, DL_P_W5,
    SECTOR_LOSS_ALLOCATION,
    TRUST_DOWNSIDE_HIGH_LOSS_USD,
    TRUST_DOWNSIDE_MEDIUM_LOSS_USD,
    TRUST_TIME_CRITICAL_HOURS,
)

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════════
# Classification
# ═══════════════════════════════════════════════════════════════════════════════

def classify_action(cost_usd: float, benefit_usd: float) -> str:
    """
    Classify action economic efficiency.

    Returns: HIGH_VALUE | ACCEPTABLE | LOW_EFFICIENCY | LOSS_INDUCING
    """
    net_value = benefit_usd - cost_usd

    if net_value < 0:
        return "LOSS_INDUCING"

    if benefit_usd <= 0:
        # Zero benefit but has cost → loss-inducing
        if cost_usd > 0:
            return "LOSS_INDUCING"
        # Both zero → acceptable (no cost, no benefit = neutral)
        return "ACCEPTABLE"

    ratio = cost_usd / benefit_usd

    if ratio > 20:
        return "LOSS_INDUCING"
    if ratio > 5:
        return "LOW_EFFICIENCY"
    if ratio >= 1:
        return "ACCEPTABLE"
    return "HIGH_VALUE"


# ═══════════════════════════════════════════════════════════════════════════════
# Why-recommended reasoning (from REAL formula data)
# ═══════════════════════════════════════════════════════════════════════════════

def _build_why_recommended(action: dict, result: dict) -> list[str]:
    """Generate why-recommended reasons from actual simulation data."""
    reasons: list[str] = []

    sector = action.get("sector", "")
    urgency = action.get("urgency", 0)
    priority = action.get("priority_score", 0)
    feasibility = action.get("feasibility", 0)
    reg_risk = action.get("regulatory_risk", 0)
    loss_avoided = action.get("loss_avoided_usd", 0)
    time_hours = action.get("time_to_act_hours", 24)

    # Reason 1: Priority score breakdown
    reasons.append(
        f"Priority score {priority:.4f} computed as: "
        f"{DL_P_W1:.0%} urgency({urgency:.2f}) + "
        f"{DL_P_W2:.0%} loss-normalized + "
        f"{DL_P_W3:.0%} regulatory({reg_risk:.2f}) + "
        f"{DL_P_W4:.0%} feasibility({feasibility:.2f}) + "
        f"{DL_P_W5:.0%} time-effect"
    )

    # Reason 2: Sector relevance
    sector_alloc = SECTOR_LOSS_ALLOCATION.get(sector, 0)
    reasons.append(
        f"{sector.title()} sector carries {sector_alloc:.0%} of total loss allocation — "
        f"this action addresses {format_loss_usd(loss_avoided)} in avoidable losses"
    )

    # Reason 3: Urgency justification
    if urgency >= 0.85:
        reasons.append(f"Urgency {urgency:.2f} (CRITICAL) — action required within {time_hours}h before cascading effects compound")
    elif urgency >= 0.70:
        reasons.append(f"Urgency {urgency:.2f} (HIGH) — {time_hours}h window before secondary propagation effects")
    else:
        reasons.append(f"Urgency {urgency:.2f} (MODERATE) — {time_hours}h response window with limited compounding risk")

    # Reason 4: Regulatory risk
    if reg_risk >= 0.80:
        reasons.append(f"Regulatory risk {reg_risk:.2f} — inaction may trigger mandatory regulatory response or supervisory action")

    return reasons


def _build_tradeoffs(action: dict, classification: str, result: dict) -> list[str]:
    """Generate tradeoff analysis from actual data."""
    tradeoffs: list[str] = []

    cost = action.get("cost_usd", 0)
    loss_avoided = action.get("loss_avoided_usd", 0)
    net_value = loss_avoided - cost
    sector = action.get("sector", "")
    time_hours = action.get("time_to_act_hours", 24)

    if classification == "LOSS_INDUCING":
        tradeoffs.append(
            f"WARNING: Action cost ({format_loss_usd(cost)}) exceeds projected benefit ({format_loss_usd(loss_avoided)}) — "
            f"net destruction of {format_loss_usd(abs(net_value))}"
        )
        tradeoffs.append("Consider deferring this action unless non-financial regulatory obligations mandate execution")

    elif classification == "LOW_EFFICIENCY":
        ratio = cost / max(loss_avoided, 1)
        tradeoffs.append(
            f"Cost-to-benefit ratio of {ratio:.1f}:1 is above efficiency threshold — "
            f"consider partial execution or phased deployment to reduce cost"
        )

    if cost > 500_000_000:
        tradeoffs.append(f"Capital commitment of {format_loss_usd(cost)} requires board-level authorization and may impact liquidity reserves")

    if time_hours <= 4:
        tradeoffs.append(f"Immediate execution ({time_hours}h window) — delay risk: secondary propagation amplifies losses by estimated 15-30%")

    # Opportunity cost
    total_loss = result.get("financial_impact", {}).get("total_loss_usd", 0)
    if total_loss > 0 and loss_avoided > 0:
        coverage = loss_avoided / total_loss
        tradeoffs.append(f"This action covers {coverage:.1%} of total projected loss — remaining {1-coverage:.1%} requires other actions")

    return tradeoffs


# ═══════════════════════════════════════════════════════════════════════════════
# Sprint 1.5: Decision Risk Overlay
# ═══════════════════════════════════════════════════════════════════════════════

def _decision_risk(label: str, severity: str, description: str) -> dict:
    """Build a single decision risk entry."""
    assert severity in ("HIGH", "MEDIUM", "LOW"), f"Invalid severity: {severity}"
    return {"label": label, "severity": severity, "description": description}


def _build_decision_risks(action: dict, classification: str, result: dict) -> list[dict]:
    """
    Generate risk assessment for a decision action.

    Risks derived from REAL action properties:
    - Capital commitment magnitude (cost_usd vs thresholds from config.py)
    - Timing sensitivity (time_to_act_hours vs TRUST_TIME_CRITICAL_HOURS)
    - External dependencies (regulatory_risk, feasibility)
    - Classification-based structural risks
    - Coverage gap (loss_avoided vs total_loss)
    """
    risks: list[dict] = []

    cost = action.get("cost_usd", 0)
    loss_avoided = action.get("loss_avoided_usd", 0)
    time_hours = action.get("time_to_act_hours", 24)
    reg_risk = action.get("regulatory_risk", 0)
    feasibility = action.get("feasibility", 1.0)
    sector = action.get("sector", "")
    total_loss = result.get("financial_impact", {}).get("total_loss_usd", 0)

    # Risk 1: Capital commitment
    if cost >= TRUST_DOWNSIDE_HIGH_LOSS_USD:
        risks.append(_decision_risk(
            "High Capital Commitment", "HIGH",
            f"Action requires {format_loss_usd(cost)} — exceeds {format_loss_usd(TRUST_DOWNSIDE_HIGH_LOSS_USD)} board-level threshold. "
            f"Liquidity impact and approval chain delays are likely.",
        ))
    elif cost >= TRUST_DOWNSIDE_MEDIUM_LOSS_USD:
        risks.append(_decision_risk(
            "Significant Capital Commitment", "MEDIUM",
            f"Action requires {format_loss_usd(cost)} — above departmental authority threshold. "
            f"May require escalated approval.",
        ))

    # Risk 2: Timing sensitivity
    if time_hours <= TRUST_TIME_CRITICAL_HOURS:
        risks.append(_decision_risk(
            "Time-Critical Execution", "HIGH" if time_hours <= 6 else "MEDIUM",
            f"Must execute within {time_hours}h. Delayed execution compounds losses "
            f"by estimated 15-30% per propagation cycle.",
        ))

    # Risk 3: Regulatory exposure
    if reg_risk >= 0.80:
        risks.append(_decision_risk(
            "Regulatory Exposure", "HIGH",
            f"Regulatory risk score {reg_risk:.2f} — inaction may trigger mandatory supervisory response. "
            f"Execution also carries compliance obligations.",
        ))
    elif reg_risk >= 0.60:
        risks.append(_decision_risk(
            "Regulatory Attention", "MEDIUM",
            f"Regulatory risk score {reg_risk:.2f} — action is within regulatory awareness zone. "
            f"Documentation and reporting obligations apply.",
        ))

    # Risk 4: Feasibility constraints
    if feasibility < 0.70:
        risks.append(_decision_risk(
            "Execution Feasibility", "HIGH",
            f"Feasibility score {feasibility:.2f} — significant operational barriers may prevent or delay execution.",
        ))
    elif feasibility < 0.85:
        risks.append(_decision_risk(
            "Execution Complexity", "MEDIUM",
            f"Feasibility score {feasibility:.2f} — moderate complexity in execution path.",
        ))

    # Risk 5: Classification-based structural risk
    if classification == "LOSS_INDUCING":
        risks.append(_decision_risk(
            "Value Destruction", "HIGH",
            f"Action is classified LOSS_INDUCING — cost exceeds benefit by {format_loss_usd(abs(loss_avoided - cost))}. "
            f"Only justified if non-financial regulatory obligations mandate execution.",
        ))
    elif classification == "LOW_EFFICIENCY":
        ratio = cost / max(loss_avoided, 1)
        risks.append(_decision_risk(
            "Low Return on Capital", "MEDIUM",
            f"Cost-to-benefit ratio of {ratio:.1f}:1 indicates poor capital efficiency. "
            f"Consider phased execution or alternative approaches.",
        ))

    # Risk 6: Coverage gap
    if total_loss > 0 and loss_avoided > 0:
        coverage = loss_avoided / total_loss
        if coverage < 0.10:
            risks.append(_decision_risk(
                "Limited Impact Coverage", "MEDIUM",
                f"Action addresses only {coverage:.1%} of total projected loss — "
                f"significant residual risk remains unmitigated.",
            ))

    # Risk 7: External dependency (cross-sector)
    if sector in ("energy", "maritime") and cost > 500_000_000:
        risks.append(_decision_risk(
            "External Dependency", "MEDIUM",
            f"Action in {sector} sector depends on external counterparties (suppliers, ports, OPEC) "
            f"whose cooperation is not guaranteed.",
        ))

    return risks


# ═══════════════════════════════════════════════════════════════════════════════
# Main: compute transparency for a single action
# ═══════════════════════════════════════════════════════════════════════════════

def compute_decision_transparency(action: dict, result: dict) -> dict:
    """
    Compute full DecisionTransparency for one action.

    Returns dict matching the DecisionTransparency contract:
      action_id, cost_usd, benefit_usd, net_value_usd, cost_benefit_ratio,
      classification, why_recommended, tradeoffs
    """
    action_id = action.get("action_id", "")
    cost_usd = action.get("cost_usd", 0)
    benefit_usd = action.get("loss_avoided_usd", 0)
    net_value_usd = benefit_usd - cost_usd

    # Cost-benefit ratio (avoid division by zero)
    if benefit_usd > 0:
        cost_benefit_ratio = round(cost_usd / benefit_usd, 4)
    elif cost_usd > 0:
        cost_benefit_ratio = 999.0  # infinite cost, no benefit
    else:
        cost_benefit_ratio = 0.0  # both zero

    classification = classify_action(cost_usd, benefit_usd)
    why_recommended = _build_why_recommended(action, result)
    tradeoffs = _build_tradeoffs(action, classification, result)
    decision_risks = _build_decision_risks(action, classification, result)

    return {
        "action_id": action_id,
        "cost_usd": cost_usd,
        "cost_formatted": format_loss_usd(cost_usd) if cost_usd > 0 else "$0",
        "benefit_usd": benefit_usd,
        "benefit_formatted": format_loss_usd(benefit_usd),
        "net_value_usd": round(net_value_usd, 2),
        "net_value_formatted": format_loss_usd(abs(net_value_usd)),
        "is_net_positive": net_value_usd > 0,
        "cost_benefit_ratio": cost_benefit_ratio,
        "classification": classification,
        "why_recommended": why_recommended,
        "tradeoffs": tradeoffs,
        # Sprint 1.5: Decision Risk Overlay
        "decision_risks": decision_risks,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Batch: compute for all actions + detect loss-inducing
# ═══════════════════════════════════════════════════════════════════════════════

def compute_all_transparencies(result: dict) -> dict:
    """
    Compute DecisionTransparency for all actions in a simulation result.

    Returns:
      {
        "action_transparencies": [DecisionTransparency, ...],
        "has_loss_inducing": bool,
        "loss_inducing_count": int,
        "loss_inducing_actions": [action_id, ...],
        "warning_banner": str | None,
      }
    """
    decision_plan = result.get("decision_plan", {})
    actions = decision_plan.get("actions", [])

    if not actions:
        # Fallback: try top-level actions key
        actions = result.get("actions", [])

    transparencies: list[dict] = []
    loss_inducing_ids: list[str] = []

    for action in actions:
        t = compute_decision_transparency(action, result)
        transparencies.append(t)

        if t["classification"] == "LOSS_INDUCING":
            loss_inducing_ids.append(t["action_id"])

    has_loss_inducing = len(loss_inducing_ids) > 0

    warning_banner = None
    if has_loss_inducing:
        warning_banner = (
            f"WARNING: {len(loss_inducing_ids)} recommended action(s) may destroy value. "
            f"Review actions {', '.join(loss_inducing_ids)} before proceeding."
        )
        logger.warning("Loss-inducing actions detected: %s", loss_inducing_ids)

    logger.info(
        "Computed transparency for %d actions — %d loss-inducing",
        len(transparencies), len(loss_inducing_ids),
    )

    return {
        "action_transparencies": transparencies,
        "has_loss_inducing": has_loss_inducing,
        "loss_inducing_count": len(loss_inducing_ids),
        "loss_inducing_actions": loss_inducing_ids,
        "warning_banner": warning_banner,
    }
