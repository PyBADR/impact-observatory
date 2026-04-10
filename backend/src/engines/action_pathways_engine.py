"""
Impact Observatory | مرصد الأثر
Action Pathways Engine — converts flat action lists into
decision-ready execution structures with typed categories.

Architecture Layer: Agents → APIs (Layer 4→5)
Data Flow: decision_plan.actions → Classified Action[]

Categories:
  IMMEDIATE   — time-sensitive, prevents escalation, no trigger condition
  CONDITIONAL — depends on a measurable trigger (e.g., "liquidity < 20%")
  STRATEGIC   — long-term structural mitigation

Each action gets:
  - type classification
  - trigger_condition (CONDITIONAL only, None for IMMEDIATE)
  - reversibility (HIGH | MEDIUM | LOW)
  - expected_impact (0.0–1.0)
  - deadline (ISO-style relative)
"""
from __future__ import annotations

import logging
from typing import Any

from src.config import (
    AP_IMMEDIATE_THRESHOLD_HOURS,
    AP_CONDITIONAL_THRESHOLD_HOURS,
    AP_REVERSIBILITY_COST_RATIO,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Trigger condition templates — matched by sector + action keywords
# ---------------------------------------------------------------------------
_TRIGGER_TEMPLATES: dict[str, list[tuple[str, str]]] = {
    "banking": [
        ("liquidity", "liquidity_ratio < 20%"),
        ("capital", "capital_adequacy_ratio < 10.5%"),
        ("lcr", "lcr_ratio < 100%"),
        ("repo", "interbank_rate_spread > 150bps"),
        ("outflow", "deposit_outflow_rate > 5%/day"),
    ],
    "energy": [
        ("reserve", "strategic_reserve_days < 15"),
        ("production", "production_capacity < 60%"),
        ("price", "crude_price_change > ±15%/day"),
        ("pipeline", "pipeline_throughput < 50%"),
    ],
    "maritime": [
        ("congestion", "port_utilization > 90%"),
        ("divert", "transit_delay > 48h"),
        ("tonnage", "available_tonnage < 40%"),
    ],
    "insurance": [
        ("claims", "claims_surge_multiplier > 2.0x"),
        ("solvency", "solvency_ratio < 150%"),
        ("reserve", "reserve_adequacy < 80%"),
        ("ratio", "combined_ratio > 110%"),
    ],
    "fintech": [
        ("payment", "settlement_delay > 4h"),
        ("api", "api_availability < 95%"),
        ("fraud", "fraud_rate > 0.5%"),
        ("velocity", "transaction_velocity > 3x_baseline"),
    ],
    "logistics": [
        ("throughput", "warehouse_throughput < 50%"),
        ("delay", "delivery_delay > 72h"),
    ],
    "infrastructure": [
        ("capacity", "grid_capacity < 70%"),
        ("outage", "service_outage_hours > 6"),
    ],
    "government": [
        ("fiscal", "fiscal_buffer_months < 3"),
        ("response", "crisis_response_time > 12h"),
    ],
}


def classify_actions(
    actions: list[dict[str, Any]],
    scenario_id: str,
    severity: float,
    risk_level: str,
    liquidity_stress: dict[str, Any] | None = None,
    insurance_stress: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Classify a flat action list into IMMEDIATE / CONDITIONAL / STRATEGIC.

    Args:
        actions:           List of action dicts from decision_plan.actions.
        scenario_id:       Active scenario identifier.
        severity:          Base severity [0.0–1.0].
        risk_level:        Current risk level string.
        liquidity_stress:  Banking stress dict (for trigger thresholds).
        insurance_stress:  Insurance stress dict (for trigger thresholds).

    Returns:
        Dict with:
          - immediate: list[ClassifiedAction]
          - conditional: list[ClassifiedAction]
          - strategic: list[ClassifiedAction]
          - total_actions: int
          - summary: str
          - summary_ar: str
    """
    immediate: list[dict] = []
    conditional: list[dict] = []
    strategic: list[dict] = []

    for i, action in enumerate(actions):
        if not isinstance(action, dict):
            continue

        classified = _classify_single_action(
            action=action,
            index=i,
            severity=severity,
            risk_level=risk_level,
            liquidity_stress=liquidity_stress or {},
            insurance_stress=insurance_stress or {},
        )

        action_type = classified["type"]
        if action_type == "IMMEDIATE":
            immediate.append(classified)
        elif action_type == "CONDITIONAL":
            conditional.append(classified)
        else:
            strategic.append(classified)

    # Sort each bucket by priority
    immediate.sort(key=lambda x: -x.get("expected_impact", 0))
    conditional.sort(key=lambda x: -x.get("expected_impact", 0))
    strategic.sort(key=lambda x: -x.get("expected_impact", 0))

    total = len(immediate) + len(conditional) + len(strategic)
    summary = (
        f"{len(immediate)} immediate, {len(conditional)} conditional, "
        f"{len(strategic)} strategic actions for {scenario_id} "
        f"at severity {severity:.2f} ({risk_level})"
    )
    summary_ar = (
        f"{len(immediate)} فوري، {len(conditional)} مشروط، "
        f"{len(strategic)} استراتيجي للسيناريو {scenario_id} "
        f"عند شدة {severity:.2f} ({risk_level})"
    )

    result = {
        "immediate": immediate,
        "conditional": conditional,
        "strategic": strategic,
        "total_actions": total,
        "scenario_id": scenario_id,
        "severity": severity,
        "risk_level": risk_level,
        "summary": summary,
        "summary_ar": summary_ar,
    }

    logger.info(
        "[ActionPathwaysEngine] Classified %d actions: %d immediate, %d conditional, %d strategic",
        total, len(immediate), len(conditional), len(strategic),
    )

    return result


def _classify_single_action(
    action: dict[str, Any],
    index: int,
    severity: float,
    risk_level: str,
    liquidity_stress: dict,
    insurance_stress: dict,
) -> dict[str, Any]:
    """Classify and enrich a single action."""
    action_id = action.get("action_id", f"action_{index}")
    sector = action.get("sector", "cross-sector")
    time_to_act = int(action.get("time_to_act_hours", 24))
    urgency = float(action.get("urgency", 0.5))
    priority_score = float(action.get("priority_score", 0.0))
    loss_avoided = float(action.get("loss_avoided_usd", 0.0))
    cost = float(action.get("cost_usd", 0.0))
    action_text = action.get("action", action.get("action_en", ""))
    action_ar = action.get("action_ar", "")
    owner = action.get("owner", "")

    # ── Classification logic ─────────────────────────────────────────────
    action_type = _determine_type(time_to_act, urgency, severity, risk_level)

    # ── Trigger condition (CONDITIONAL only) ─────────────────────────────
    trigger_condition = None
    if action_type == "CONDITIONAL":
        trigger_condition = _match_trigger(sector, action_text, liquidity_stress, insurance_stress)

    # ── Reversibility ────────────────────────────────────────────────────
    reversibility = _compute_reversibility(cost, loss_avoided, action_type, action_text)

    # ── Expected impact ──────────────────────────────────────────────────
    expected_impact = _compute_expected_impact(
        loss_avoided, cost, urgency, priority_score, severity
    )

    # ── Deadline ─────────────────────────────────────────────────────────
    deadline = _compute_deadline(time_to_act, action_type)

    return {
        "id": action_id,
        "label": action_text,
        "label_ar": action_ar,
        "type": action_type,
        "owner": owner,
        "sector": sector,
        "deadline": deadline,
        "trigger_condition": trigger_condition,
        "reversibility": reversibility,
        "expected_impact": round(expected_impact, 4),
        "priority_score": round(priority_score, 4),
        "urgency": round(urgency, 4),
        "loss_avoided_usd": round(loss_avoided, 2),
        "cost_usd": round(cost, 2),
        "time_to_act_hours": time_to_act,
        # Preserve original action fields for backward compat
        "original_action": action,
    }


def _determine_type(
    time_to_act: int, urgency: float, severity: float, risk_level: str
) -> str:
    """Determine action type from temporal and risk signals.

    IMMEDIATE:
      - time_to_act ≤ AP_IMMEDIATE_THRESHOLD_HOURS (6h)
      - OR urgency ≥ 0.85 AND risk_level in (HIGH, SEVERE)

    CONDITIONAL:
      - AP_IMMEDIATE_THRESHOLD_HOURS < time_to_act ≤ AP_CONDITIONAL_THRESHOLD_HOURS (48h)
      - AND not classified as IMMEDIATE

    STRATEGIC:
      - Everything else (long-term, structural)
    """
    # IMMEDIATE: very short window or extreme urgency under high risk
    if time_to_act <= AP_IMMEDIATE_THRESHOLD_HOURS:
        return "IMMEDIATE"
    if urgency >= 0.85 and risk_level in ("HIGH", "SEVERE"):
        return "IMMEDIATE"

    # CONDITIONAL: medium window
    if time_to_act <= AP_CONDITIONAL_THRESHOLD_HOURS:
        return "CONDITIONAL"

    # STRATEGIC: everything else
    return "STRATEGIC"


def _match_trigger(
    sector: str,
    action_text: str,
    liquidity_stress: dict,
    insurance_stress: dict,
) -> str | None:
    """Match a trigger condition from templates based on sector + keywords."""
    text_lower = action_text.lower()
    templates = _TRIGGER_TEMPLATES.get(sector, [])

    for keyword, condition in templates:
        if keyword in text_lower:
            return condition

    # Fallback: sector-level triggers
    fallback_triggers = {
        "banking": f"aggregate_banking_stress > {liquidity_stress.get('aggregate_stress', 0.5):.2f}",
        "insurance": f"severity_index > {insurance_stress.get('severity_index', 0.5):.2f}",
        "fintech": f"payment_disruption > {liquidity_stress.get('aggregate_stress', 0.5) * 0.75:.2f}",
    }

    if sector in fallback_triggers:
        return fallback_triggers[sector]

    # Generic fallback for any sector
    return f"sector_stress_{sector} > threshold"


def _compute_reversibility(
    cost: float, loss_avoided: float, action_type: str, action_text: str
) -> str:
    """Compute reversibility rating.

    HIGH:   Low cost relative to benefit, or easily undone
    MEDIUM: Moderate cost, partially reversible
    LOW:    High cost ratio or irreversible language detected
    """
    # Irreversible language check
    irreversible_keywords = [
        "force majeure", "suspend", "terminate", "close",
        "liquidate", "declare", "permanent",
    ]
    text_lower = action_text.lower()
    has_irreversible = any(kw in text_lower for kw in irreversible_keywords)

    if has_irreversible:
        return "LOW"

    # Cost ratio check
    if loss_avoided > 0:
        ratio = cost / loss_avoided
        if ratio > AP_REVERSIBILITY_COST_RATIO:
            return "LOW"
        elif ratio > AP_REVERSIBILITY_COST_RATIO * 0.5:
            return "MEDIUM"
        else:
            return "HIGH"

    # Type-based default
    if action_type == "IMMEDIATE":
        return "MEDIUM"
    elif action_type == "CONDITIONAL":
        return "HIGH"
    else:
        return "LOW"


def _compute_expected_impact(
    loss_avoided: float,
    cost: float,
    urgency: float,
    priority_score: float,
    severity: float,
) -> float:
    """Compute expected impact score [0.0–1.0]."""
    if priority_score > 0:
        return min(1.0, priority_score)

    # Fallback: weighted formula
    net_benefit = max(0.0, loss_avoided - cost)
    if loss_avoided > 0:
        benefit_ratio = min(1.0, net_benefit / loss_avoided)
    else:
        benefit_ratio = 0.3

    impact = 0.4 * urgency + 0.4 * benefit_ratio + 0.2 * severity
    return min(1.0, max(0.0, impact))


def _compute_deadline(time_to_act: int, action_type: str) -> str:
    """Compute human-readable deadline string."""
    if action_type == "IMMEDIATE":
        if time_to_act <= 1:
            return "Within 1 hour"
        elif time_to_act <= 4:
            return f"Within {time_to_act} hours"
        else:
            return f"Within {time_to_act} hours (urgent)"
    elif action_type == "CONDITIONAL":
        if time_to_act <= 24:
            return f"Within {time_to_act} hours upon trigger"
        else:
            days = time_to_act // 24
            return f"Within {days} day{'s' if days > 1 else ''} upon trigger"
    else:
        if time_to_act <= 72:
            days = max(1, time_to_act // 24)
            return f"Within {days} day{'s' if days > 1 else ''}"
        elif time_to_act <= 336:
            weeks = max(1, time_to_act // 168)
            return f"Within {weeks} week{'s' if weeks > 1 else ''}"
        else:
            return "Long-term (30+ days)"
