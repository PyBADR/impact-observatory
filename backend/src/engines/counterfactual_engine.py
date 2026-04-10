"""
Impact Observatory | مرصد الأثر
Counterfactual Calibration Engine — ensures decision recommendations
are logically consistent with their numeric outcomes.

Architecture Layer: Agents → APIs (Layer 4→5)
Data Flow: decision_plan + financial_impact + headline → CalibratedCounterfactual

Problem solved:
  When recommended_outcome.loss > baseline.loss, the recommendation text
  says "reduces risk" but the numbers say otherwise. This engine detects
  and corrects that inconsistency.

Rules:
  1. Logical Consistency: recommended loss must be ≤ baseline loss
     (or label is changed to "protective but costly")
  2. Delta Clarity: delta = baseline - recommended is always computed
  3. Decision Alignment: text + numbers + delta must all agree
"""
from __future__ import annotations

import logging
from typing import Any

from src.config import CF_MITIGATION_FACTOR, CF_ALTERNATIVE_PENALTY, CF_COST_TOLERANCE

logger = logging.getLogger(__name__)


def calibrate_counterfactual(
    scenario_id: str,
    severity: float,
    total_loss_usd: float,
    decision_plan: dict[str, Any],
    headline: dict[str, Any],
    risk_level: str,
    confidence_score: float,
) -> dict[str, Any]:
    """Produce a calibrated counterfactual analysis.

    Builds three scenarios:
      - baseline:     No action taken — full projected loss.
      - recommended:  Primary recommended actions executed — mitigated loss.
      - alternative:  Alternative strategy — different cost/risk tradeoff.

    Then validates logical consistency and computes deltas.

    Args:
        scenario_id:      Active scenario identifier.
        severity:         Base severity [0.0–1.0].
        total_loss_usd:   Aggregate projected loss from simulation.
        decision_plan:    Full decision plan dict from pipeline.
        headline:         Headline KPI dict.
        risk_level:       Classified risk level (NOMINAL..SEVERE).
        confidence_score: Model confidence [0.0–1.0].

    Returns:
        Dict with baseline, recommended, alternative, delta, narrative.
    """
    actions = decision_plan.get("actions", [])
    immediate_actions = decision_plan.get("immediate_actions", [])

    # ── Baseline outcome (no intervention) ───────────────────────────────
    baseline = _compute_baseline(
        total_loss_usd=total_loss_usd,
        severity=severity,
        headline=headline,
        risk_level=risk_level,
    )

    # ── Recommended outcome (primary actions executed) ───────────────────
    recommended = _compute_recommended(
        total_loss_usd=total_loss_usd,
        severity=severity,
        actions=actions,
        immediate_actions=immediate_actions,
        risk_level=risk_level,
        confidence_score=confidence_score,
    )

    # ── Alternative outcome (different strategy) ─────────────────────────
    alternative = _compute_alternative(
        total_loss_usd=total_loss_usd,
        severity=severity,
        actions=actions,
        risk_level=risk_level,
    )

    # ── Rule 1: Logical consistency check ────────────────────────────────
    recommended, consistency_flag = _enforce_logical_consistency(
        baseline, recommended
    )

    # ── Rule 2: Delta computation ────────────────────────────────────────
    delta = _compute_delta(baseline, recommended, alternative)

    # ── Rule 3: Decision alignment — narrative must match numbers ────────
    narrative = _build_narrative(
        baseline, recommended, alternative, delta,
        consistency_flag, risk_level, scenario_id,
    )

    result = {
        "scenario_id": scenario_id,
        "baseline": baseline,
        "recommended": recommended,
        "alternative": alternative,
        "delta": delta,
        "narrative": narrative["en"],
        "narrative_ar": narrative["ar"],
        "consistency_flag": consistency_flag,
        "confidence_score": round(confidence_score, 4),
    }

    logger.info(
        "[CounterfactualEngine] Calibrated: baseline=$%.0f recommended=$%.0f delta=$%.0f flag=%s",
        baseline["projected_loss_usd"],
        recommended["projected_loss_usd"],
        delta["loss_reduction_usd"],
        consistency_flag,
    )

    return result


def _compute_baseline(
    total_loss_usd: float,
    severity: float,
    headline: dict,
    risk_level: str,
) -> dict[str, Any]:
    """Baseline: no action, full projected loss."""
    recovery_days = int(headline.get("max_recovery_days", 14))
    peak_day = int(headline.get("peak_day", 3))

    return {
        "label": "No Action Baseline",
        "label_ar": "خط الأساس بدون إجراء",
        "projected_loss_usd": round(total_loss_usd, 2),
        "projected_loss_formatted": _format_usd(total_loss_usd),
        "risk_level": risk_level,
        "recovery_days": recovery_days,
        "peak_day": peak_day,
        "operational_cost_usd": 0.0,
        "severity": round(severity, 4),
    }


def _compute_recommended(
    total_loss_usd: float,
    severity: float,
    actions: list[dict],
    immediate_actions: list[dict],
    risk_level: str,
    confidence_score: float,
) -> dict[str, Any]:
    """Recommended: execute primary actions to mitigate loss."""
    # Sum loss_avoided from actions (capped at total_loss)
    loss_avoided = sum(
        float(a.get("loss_avoided_usd", 0.0))
        for a in actions[:5]
        if isinstance(a, dict)
    )

    # If actions don't specify loss_avoided, use config-based mitigation
    if loss_avoided < 1.0:
        loss_avoided = total_loss_usd * CF_MITIGATION_FACTOR

    # Cap at total loss — can't avoid more than total
    loss_avoided = min(loss_avoided, total_loss_usd * 0.85)

    # Sum operational cost
    operational_cost = sum(
        float(a.get("cost_usd", 0.0))
        for a in actions[:5]
        if isinstance(a, dict)
    )

    mitigated_loss = max(0.0, total_loss_usd - loss_avoided)

    # Faster recovery with immediate actions
    base_recovery = 14
    if immediate_actions:
        base_recovery = max(5, base_recovery - len(immediate_actions) * 2)

    # Improved risk level
    improved_risk = _improve_risk_level(risk_level)

    return {
        "label": "Recommended Actions",
        "label_ar": "الإجراءات الموصى بها",
        "projected_loss_usd": round(mitigated_loss, 2),
        "projected_loss_formatted": _format_usd(mitigated_loss),
        "loss_avoided_usd": round(loss_avoided, 2),
        "loss_avoided_formatted": _format_usd(loss_avoided),
        "operational_cost_usd": round(operational_cost, 2),
        "operational_cost_formatted": _format_usd(operational_cost),
        "risk_level": improved_risk,
        "recovery_days": base_recovery,
        "actions_count": len(actions),
        "severity": round(severity * (1.0 - CF_MITIGATION_FACTOR), 4),
        "confidence_adjusted": round(confidence_score * 0.95, 4),
    }


def _compute_alternative(
    total_loss_usd: float,
    severity: float,
    actions: list[dict],
    risk_level: str,
) -> dict[str, Any]:
    """Alternative: different strategy — less mitigation, lower cost."""
    # Alternative avoids less loss but costs less
    alt_mitigation = CF_MITIGATION_FACTOR * 0.5
    loss_avoided = total_loss_usd * alt_mitigation
    mitigated_loss = total_loss_usd - loss_avoided

    # Lower operational cost
    operational_cost = sum(
        float(a.get("cost_usd", 0.0)) * 0.3
        for a in actions[:3]
        if isinstance(a, dict)
    )

    # Penalty: longer recovery
    alt_recovery = max(7, 14 + 5)

    return {
        "label": "Alternative Strategy",
        "label_ar": "استراتيجية بديلة",
        "projected_loss_usd": round(mitigated_loss, 2),
        "projected_loss_formatted": _format_usd(mitigated_loss),
        "loss_avoided_usd": round(loss_avoided, 2),
        "loss_avoided_formatted": _format_usd(loss_avoided),
        "operational_cost_usd": round(operational_cost, 2),
        "operational_cost_formatted": _format_usd(operational_cost),
        "risk_level": risk_level,
        "recovery_days": alt_recovery,
        "actions_count": min(3, len(actions)),
        "severity": round(severity * (1.0 - alt_mitigation), 4),
    }


def _enforce_logical_consistency(
    baseline: dict, recommended: dict
) -> tuple[dict, str]:
    """Rule 1: recommended loss MUST NOT exceed baseline loss.

    If it does, either:
      a) Recalculate using mitigation factor (preferred)
      b) Relabel as "protective but costly"
    """
    baseline_loss = baseline["projected_loss_usd"]
    recommended_loss = recommended["projected_loss_usd"]

    if recommended_loss > baseline_loss:
        # Check if this is due to high operational cost
        op_cost = recommended.get("operational_cost_usd", 0.0)
        net_recommended = recommended_loss + op_cost

        if op_cost > baseline_loss * CF_COST_TOLERANCE:
            # Case B: Protective but costly — relabel
            recommended["label"] = "Protective But Costly"
            recommended["label_ar"] = "وقائي ولكن مكلف"
            # Recalculate loss using mitigation
            corrected_loss = baseline_loss * (1.0 - CF_MITIGATION_FACTOR)
            recommended["projected_loss_usd"] = round(corrected_loss, 2)
            recommended["projected_loss_formatted"] = _format_usd(corrected_loss)
            recommended["loss_avoided_usd"] = round(baseline_loss - corrected_loss, 2)
            recommended["loss_avoided_formatted"] = _format_usd(baseline_loss - corrected_loss)
            return recommended, "CORRECTED_COSTLY"
        else:
            # Case A: Pure inconsistency — recalculate
            corrected_loss = baseline_loss * (1.0 - CF_MITIGATION_FACTOR)
            recommended["projected_loss_usd"] = round(corrected_loss, 2)
            recommended["projected_loss_formatted"] = _format_usd(corrected_loss)
            recommended["loss_avoided_usd"] = round(baseline_loss - corrected_loss, 2)
            recommended["loss_avoided_formatted"] = _format_usd(baseline_loss - corrected_loss)
            return recommended, "CORRECTED_INCONSISTENCY"

    return recommended, "CONSISTENT"


def _compute_delta(
    baseline: dict, recommended: dict, alternative: dict
) -> dict[str, Any]:
    """Rule 2: Always compute delta = baseline - recommended."""
    b_loss = baseline["projected_loss_usd"]
    r_loss = recommended["projected_loss_usd"]
    a_loss = alternative["projected_loss_usd"]

    loss_reduction = b_loss - r_loss
    loss_reduction_pct = (loss_reduction / max(b_loss, 1.0)) * 100.0

    alt_reduction = b_loss - a_loss
    alt_reduction_pct = (alt_reduction / max(b_loss, 1.0)) * 100.0

    r_cost = recommended.get("operational_cost_usd", 0.0)
    a_cost = alternative.get("operational_cost_usd", 0.0)

    r_recovery = recommended.get("recovery_days", 14)
    b_recovery = baseline.get("recovery_days", 14)
    a_recovery = alternative.get("recovery_days", 14)

    # Net benefit = loss avoided - cost
    r_net = loss_reduction - r_cost
    a_net = alt_reduction - a_cost

    # Determine which is better
    if r_net > a_net:
        recommendation = "recommended"
    elif a_net > r_net:
        recommendation = "alternative"
    else:
        recommendation = "equivalent"

    # Determine if it's a "tail risk reduction" or "direct loss reduction"
    is_tail_risk = r_cost > loss_reduction * 0.5

    delta_explained = (
        "Reduces tail risk but increases short-term cost"
        if is_tail_risk
        else f"Reduces projected loss by {loss_reduction_pct:.1f}% with acceptable cost"
    )
    delta_explained_ar = (
        "يقلل من مخاطر الذيل ولكن يزيد التكلفة قصيرة الأجل"
        if is_tail_risk
        else f"يقلل الخسارة المتوقعة بنسبة {loss_reduction_pct:.1f}% بتكلفة مقبولة"
    )

    return {
        "loss_reduction_usd": round(loss_reduction, 2),
        "loss_reduction_pct": round(loss_reduction_pct, 2),
        "loss_reduction_formatted": _format_usd(loss_reduction),
        "alt_reduction_usd": round(alt_reduction, 2),
        "alt_reduction_pct": round(alt_reduction_pct, 2),
        "recommended_net_benefit_usd": round(r_net, 2),
        "alternative_net_benefit_usd": round(a_net, 2),
        "recovery_improvement_days": b_recovery - r_recovery,
        "best_option": recommendation,
        "delta_explained": delta_explained,
        "delta_explained_ar": delta_explained_ar,
    }


def _build_narrative(
    baseline: dict,
    recommended: dict,
    alternative: dict,
    delta: dict,
    consistency_flag: str,
    risk_level: str,
    scenario_id: str,
) -> dict[str, str]:
    """Rule 3: Narrative must align with numeric outcomes."""
    r_label = recommended["label"]
    reduction_pct = delta["loss_reduction_pct"]
    best = delta["best_option"]

    if consistency_flag == "CORRECTED_COSTLY":
        en = (
            f"For scenario '{scenario_id}' at risk level {risk_level}: "
            f"the recommended actions are protective but carry significant operational cost. "
            f"Net loss reduction is {reduction_pct:.1f}% ($"
            f"{delta['loss_reduction_usd']:,.0f}), but execution cost partially offsets gains. "
            f"{delta['delta_explained']}."
        )
        ar = (
            f"للسيناريو '{scenario_id}' عند مستوى مخاطر {risk_level}: "
            f"الإجراءات الموصى بها وقائية ولكنها تحمل تكلفة تشغيلية كبيرة. "
            f"صافي تخفيض الخسارة {reduction_pct:.1f}%. "
            f"{delta['delta_explained_ar']}."
        )
    elif consistency_flag == "CORRECTED_INCONSISTENCY":
        en = (
            f"For scenario '{scenario_id}' at risk level {risk_level}: "
            f"counterfactual recalibrated — original projection contained logical inconsistency. "
            f"Corrected net reduction: {reduction_pct:.1f}% ($"
            f"{delta['loss_reduction_usd']:,.0f}). "
            f"{delta['delta_explained']}."
        )
        ar = (
            f"للسيناريو '{scenario_id}': تمت إعادة معايرة التحليل المضاد — "
            f"الإسقاط الأصلي يحتوي على تناقض منطقي. "
            f"التخفيض المصحح: {reduction_pct:.1f}%. "
            f"{delta['delta_explained_ar']}."
        )
    else:
        en = (
            f"For scenario '{scenario_id}' at risk level {risk_level}: "
            f"executing recommended actions reduces projected loss by {reduction_pct:.1f}% "
            f"(${delta['loss_reduction_usd']:,.0f}). "
            f"Recovery improves by {delta['recovery_improvement_days']} days. "
            f"The {best} strategy yields the highest net benefit. "
            f"{delta['delta_explained']}."
        )
        ar = (
            f"للسيناريو '{scenario_id}' عند مستوى مخاطر {risk_level}: "
            f"تنفيذ الإجراءات الموصى بها يقلل الخسارة المتوقعة بنسبة {reduction_pct:.1f}%. "
            f"يتحسن التعافي بمقدار {delta['recovery_improvement_days']} أيام. "
            f"{delta['delta_explained_ar']}."
        )

    return {"en": en, "ar": ar}


def _improve_risk_level(risk_level: str) -> str:
    """Step risk level down one notch when actions are taken."""
    hierarchy = ["NOMINAL", "LOW", "GUARDED", "ELEVATED", "HIGH", "SEVERE"]
    try:
        idx = hierarchy.index(risk_level)
        return hierarchy[max(0, idx - 1)]
    except ValueError:
        return risk_level


def _format_usd(amount: float) -> str:
    """Format USD amount for display."""
    if abs(amount) >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.2f}B"
    elif abs(amount) >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    elif abs(amount) >= 1_000:
        return f"${amount / 1_000:.0f}K"
    else:
        return f"${amount:,.0f}"
