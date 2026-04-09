"""Action synthesizer — re-ranks existing actions with impact-aware weighting.

Takes the existing decision_layer actions and enriches them with:
- impact-weighted re-ranking
- action type classification
- urgency scoring
- net benefit / ROI
- reasoning chains

All weights from config.py. Deterministic.
"""
from __future__ import annotations

from typing import Any, Optional

from src.config import (
    DB_W1, DB_W2, DB_W3, DB_W4,
    DB_URGENCY_IMMEDIATE_THRESHOLD,
    DB_URGENCY_URGENT_THRESHOLD,
    DB_URGENCY_MONITOR_THRESHOLD,
    DB_MITIGATE_THRESHOLD,
    DB_HEDGE_THRESHOLD,
    DB_TRANSFER_THRESHOLD,
    DB_ACCEPT_THRESHOLD,
)
from src.utils import clamp
from src.decision_brain.reasoning_builder import build_reasoning_chain


def _classify_urgency(score: float) -> str:
    """Map urgency score [0,1] to label."""
    if score >= DB_URGENCY_IMMEDIATE_THRESHOLD:
        return "IMMEDIATE"
    if score >= DB_URGENCY_URGENT_THRESHOLD:
        return "URGENT"
    if score >= DB_URGENCY_MONITOR_THRESHOLD:
        return "MONITOR"
    return "WATCH"


def _classify_action_type(
    composite_severity: float,
    feasibility: float,
    regulatory_risk: float,
    risk_level: str,
    time_to_first_failure: float,
) -> str:
    """Classify action type from risk score.

    ESCALATE: risk_level HIGH/SEVERE AND ttff < 12h
    MITIGATE/HEDGE/TRANSFER/ACCEPT/MONITOR: by RiskScore threshold
    """
    if risk_level in ("HIGH", "SEVERE") and time_to_first_failure < 12.0:
        return "ESCALATE"

    risk_score = composite_severity * (1 - feasibility) * regulatory_risk
    if risk_score >= DB_MITIGATE_THRESHOLD:
        return "MITIGATE"
    if risk_score >= DB_HEDGE_THRESHOLD:
        return "HEDGE"
    if risk_score >= DB_TRANSFER_THRESHOLD:
        return "TRANSFER"
    if risk_score >= DB_ACCEPT_THRESHOLD:
        return "ACCEPT"
    return "MONITOR"


def synthesize_actions(
    existing_actions: list[dict[str, Any]],
    impact_assessment: dict[str, Any],
    pipeline_output: dict[str, Any],
    graph_store: Optional[Any] = None,
) -> list[dict[str, Any]]:
    """Re-rank and enrich existing actions with impact-aware weighting.

    Returns list of RecommendedAction-compatible dicts.
    """
    composite_severity = float(impact_assessment.get("composite_severity", 0.0))
    confidence = float(impact_assessment.get("confidence", 0.0))
    risk_level = pipeline_output.get("risk_level", "NOMINAL")
    total_loss = float(impact_assessment.get("total_exposure_usd", 0.0))

    # Time to first failure
    th = impact_assessment.get("time_horizon", {})
    ttff = float(th.get("time_to_first_failure_hours", 9999.0))

    # Domain severity lookup
    domain_severity: dict[str, float] = {}
    for d in impact_assessment.get("affected_domains", []):
        domain_severity[d.get("domain", "")] = max(
            float(d.get("exposure_score", 0.0)),
            float(d.get("stress_score", 0.0)),
        )

    propagation_chain = pipeline_output.get("propagation_chain", [])
    causal_chain = pipeline_output.get("explainability", {}).get("causal_chain", [])

    recommended: list[dict[str, Any]] = []

    for action in existing_actions:
        sector = action.get("sector", "cross-sector")
        original_priority = float(action.get("priority_score", 0.0))
        loss_avoided = float(action.get("loss_avoided_usd", 0.0))
        cost = float(action.get("cost_usd", 0.0))
        feasibility = float(action.get("feasibility", 0.5))
        reg_risk = float(action.get("regulatory_risk", 0.5))
        time_hours = int(action.get("time_to_act_hours", 24))

        # ── Domain severity alignment ─────────────────────────────────────
        d_sev = domain_severity.get(sector, composite_severity * 0.5)

        # ── Net benefit ───────────────────────────────────────────────────
        net_benefit = loss_avoided - cost
        net_benefit_norm = net_benefit / max(total_loss, 1.0)

        # ── Re-rank score ─────────────────────────────────────────────────
        # ReRank = DB_W1*original + DB_W2*domain_sev + DB_W3*net_benefit_norm + DB_W4*conf
        rerank_score = clamp(
            DB_W1 * original_priority
            + DB_W2 * d_sev
            + DB_W3 * max(net_benefit_norm, 0.0)
            + DB_W4 * confidence,
            0.0,
            1.0,
        )

        # ── Urgency score ─────────────────────────────────────────────────
        # UrgencyScore = 0.40*(1 - time/168) + 0.30*composite + 0.30*reg_risk
        urgency_score = clamp(
            0.40 * (1.0 - min(time_hours, 168) / 168.0)
            + 0.30 * composite_severity
            + 0.30 * reg_risk,
            0.0,
            1.0,
        )
        urgency_label = _classify_urgency(urgency_score)

        # ── Action type ───────────────────────────────────────────────────
        action_type = _classify_action_type(
            composite_severity=composite_severity,
            feasibility=feasibility,
            regulatory_risk=reg_risk,
            risk_level=risk_level,
            time_to_first_failure=ttff,
        )

        # ── ROI ───────────────────────────────────────────────────────────
        roi = loss_avoided / max(cost, 1.0)

        # ── Reasoning chain ───────────────────────────────────────────────
        reasoning = build_reasoning_chain(
            action_sector=sector,
            impact_assessment=impact_assessment,
            propagation_chain=propagation_chain,
            causal_chain=causal_chain,
            graph_store=graph_store,
        )

        # ── Domains addressed ─────────────────────────────────────────────
        domains_addressed = [sector]
        if sector == "banking" and domain_severity.get("fintech", 0) > 0.01:
            domains_addressed.append("fintech")
        if sector == "energy" and domain_severity.get("maritime", 0) > 0.01:
            domains_addressed.append("maritime")

        recommended.append({
            "action_id": action.get("action_id", ""),
            "rank": 0,  # set after sorting
            "action_type": action_type,
            "sector": sector,
            "owner": action.get("owner", ""),
            "action": action.get("action", ""),
            "action_ar": action.get("action_ar", ""),
            "urgency": urgency_label,
            "urgency_score": round(urgency_score, 4),
            "confidence": round(confidence, 4),
            "loss_avoided_usd": round(loss_avoided, 2),
            "cost_usd": round(cost, 2),
            "net_benefit_usd": round(net_benefit, 2),
            "roi_ratio": round(roi, 2),
            "regulatory_risk": round(reg_risk, 4),
            "feasibility": round(feasibility, 4),
            "time_to_act_hours": time_hours,
            "reasoning_chain": reasoning,
            "impact_domains_addressed": domains_addressed,
            "status": action.get("status", "PENDING_REVIEW"),
            "_rerank_score": rerank_score,
        })

    # Sort by rerank_score descending
    recommended.sort(key=lambda a: -a.get("_rerank_score", 0))

    # Assign ranks, remove internal field
    for rank, rec in enumerate(recommended, start=1):
        rec["rank"] = rank
        rec.pop("_rerank_score", None)

    return recommended
