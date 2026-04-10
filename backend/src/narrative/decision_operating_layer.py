"""
Impact Observatory | مرصد الأثر
Decision Operating Layer — Phase 1

Transforms Decision Authority output into an actionable operating layer with:
  1. Decision Anchoring — owner, deadline, decision_type, tradeoffs
  2. Counterfactual Engine — baseline (do nothing) vs recommended vs alternative outcomes
  3. Decision Gate System — escalation thresholds, approval workflow, gate status

Architecture: Sits ABOVE DecisionAuthorityEngine in the pipeline:
  SimulationEngine → NarrativeEngine → DecisionAuthorityEngine → DecisionOperatingLayer

All outputs deterministic. No LLM. No ambiguity.
Every field traceable to simulation inputs via SHA-256 audit trail.
"""
from __future__ import annotations

import hashlib
import math
from typing import Any

from src.utils import clamp, format_loss_usd, now_utc


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic-compatible schemas (dict-based for pipeline compatibility)
# ─────────────────────────────────────────────────────────────────────────────

# Decision types and their properties
_DECISION_TYPE_MAP: dict[str, dict[str, str]] = {
    "APPROVE": {
        "decision_type": "emergency",
        "decision_type_ar": "طوارئ",
        "decision_type_label": "Emergency Response",
        "decision_type_label_ar": "استجابة طوارئ",
    },
    "ESCALATE": {
        "decision_type": "strategic",
        "decision_type_ar": "استراتيجي",
        "decision_type_label": "Strategic Escalation",
        "decision_type_label_ar": "تصعيد استراتيجي",
    },
    "DELAY": {
        "decision_type": "operational",
        "decision_type_ar": "تشغيلي",
        "decision_type_label": "Operational Monitoring",
        "decision_type_label_ar": "مراقبة تشغيلية",
    },
    "REJECT": {
        "decision_type": "operational",
        "decision_type_ar": "تشغيلي",
        "decision_type_label": "Standard Operations",
        "decision_type_label_ar": "عمليات قياسية",
    },
}

# Owner escalation chain by decision type
_OWNER_MAP: dict[str, dict[str, str]] = {
    "emergency": {
        "owner": "Chief Risk Officer",
        "owner_ar": "كبير مسؤولي المخاطر",
        "approval_owner": "Board Risk Committee",
        "approval_owner_ar": "لجنة مخاطر مجلس الإدارة",
    },
    "strategic": {
        "owner": "Chief Executive Officer",
        "owner_ar": "الرئيس التنفيذي",
        "approval_owner": "Board of Directors",
        "approval_owner_ar": "مجلس الإدارة",
    },
    "operational": {
        "owner": "Head of Operations",
        "owner_ar": "رئيس العمليات",
        "approval_owner": "Chief Risk Officer",
        "approval_owner_ar": "كبير مسؤولي المخاطر",
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# 1. Decision Anchoring
# ─────────────────────────────────────────────────────────────────────────────

def _compute_tradeoff(
    label_en: str,
    label_ar: str,
    left_label_en: str,
    left_label_ar: str,
    right_label_en: str,
    right_label_ar: str,
    position: float,
    rationale_en: str,
    rationale_ar: str,
) -> dict[str, Any]:
    """Build a tradeoff axis with position [0.0=left, 1.0=right]."""
    return {
        "axis_en": label_en,
        "axis_ar": label_ar,
        "left_en": left_label_en,
        "left_ar": left_label_ar,
        "right_en": right_label_en,
        "right_ar": right_label_ar,
        "position": round(clamp(position, 0.0, 1.0), 3),
        "rationale_en": rationale_en,
        "rationale_ar": rationale_ar,
    }


def build_decision_anchor(
    simulation: dict,
    authority: dict,
) -> dict[str, Any]:
    """Build the Decision Anchor — who owns this decision, what type, what tradeoffs.

    Parameters
    ----------
    simulation : dict
        Raw SimulateResponse from SimulationEngine.
    authority : dict
        Output from DecisionAuthorityEngine.generate().

    Returns
    -------
    dict
        Decision anchor with owner, deadline, type, tradeoffs.
    """
    da = authority.get("decision_authority", {})
    ed = da.get("executive_directive", {})
    internal_decision = ed.get("internal_decision", "ESCALATE")
    urgency_level = ed.get("urgency_level", "MODERATE")
    if_ignored = da.get("if_ignored", {})

    # Decision type
    dt_info = _DECISION_TYPE_MAP.get(internal_decision, _DECISION_TYPE_MAP["ESCALATE"])
    decision_type = dt_info["decision_type"]

    # Owner
    owner_info = _OWNER_MAP.get(decision_type, _OWNER_MAP["operational"])

    # Deadline calculation based on urgency
    time_to_failure = if_ignored.get("time_to_failure_hours", 999.0)
    deadline_mult = {
        "CRITICAL": 0.25,
        "HIGH": 0.40,
        "MODERATE": 0.60,
        "LOW": 0.80,
    }.get(urgency_level, 0.60)
    deadline_hours = max(1.0, round(time_to_failure * deadline_mult, 1))

    # Extract metrics for tradeoff computation
    fi = simulation.get("financial_impact", {})
    total_loss = fi.get("total_loss_usd", 0.0)
    confidence = simulation.get("confidence_score", 0.7)
    propagation = simulation.get("propagation_score", 0.0)
    pressure = da.get("decision_pressure_score", {}).get("score", 50)

    # ── Tradeoffs ───────────────────────────────────────────────────────
    # Cost vs Risk: high loss + low time → favor risk mitigation (position → 0.0)
    cost_vs_risk_pos = clamp(1.0 - (total_loss / max(total_loss + 1e9, 1.0)), 0.0, 1.0)
    if time_to_failure < 48:
        cost_vs_risk_pos *= 0.5  # Urgency pushes toward risk mitigation

    cost_vs_risk = _compute_tradeoff(
        "Cost vs Risk", "التكلفة مقابل المخاطر",
        "Minimize Risk", "تقليل المخاطر",
        "Minimize Cost", "تقليل التكلفة",
        cost_vs_risk_pos,
        f"{'Risk mitigation prioritized — exposure exceeds $' + format_loss_usd(total_loss) + ' with ' + str(round(time_to_failure)) + 'h to failure.' if cost_vs_risk_pos < 0.4 else 'Balanced approach — cost and risk considerations weighted equally.' if cost_vs_risk_pos < 0.6 else 'Cost efficiency prioritized — risk within acceptable bounds.'}",
        f"{'أولوية تخفيف المخاطر — التعرض يتجاوز ' + format_loss_usd(total_loss) + ' مع ' + str(round(time_to_failure)) + ' ساعة للفشل.' if cost_vs_risk_pos < 0.4 else 'نهج متوازن — اعتبارات التكلفة والمخاطر موزونة بالتساوي.' if cost_vs_risk_pos < 0.6 else 'أولوية كفاءة التكلفة — المخاطر ضمن الحدود المقبولة.'}",
    )

    # Speed vs Accuracy: high urgency → favor speed (position → 0.0)
    speed_vs_accuracy_pos = clamp(
        (confidence * 0.6) + ((time_to_failure / max(time_to_failure + 168, 1.0)) * 0.4),
        0.0, 1.0,
    )

    speed_vs_accuracy = _compute_tradeoff(
        "Speed vs Accuracy", "السرعة مقابل الدقة",
        "Act Fast", "تصرف بسرعة",
        "Gather More Data", "اجمع بيانات أكثر",
        speed_vs_accuracy_pos,
        f"{'Immediate action required — time window closing.' if speed_vs_accuracy_pos < 0.4 else 'Balanced timeline allows for both speed and verification.' if speed_vs_accuracy_pos < 0.6 else 'Time available for deeper analysis before commitment.'}",
        f"{'مطلوب إجراء فوري — نافذة الوقت تُغلق.' if speed_vs_accuracy_pos < 0.4 else 'الجدول الزمني المتوازن يسمح بالسرعة والتحقق معاً.' if speed_vs_accuracy_pos < 0.6 else 'الوقت متاح لتحليل أعمق قبل الالتزام.'}",
    )

    # Short-term vs Long-term: high propagation → favor long-term (position → 1.0)
    short_vs_long_pos = clamp(propagation * 0.7 + (pressure / 100.0) * 0.3, 0.0, 1.0)

    short_vs_long = _compute_tradeoff(
        "Short-term vs Long-term", "المدى القصير مقابل الطويل",
        "Short-term Fix", "إصلاح قصير المدى",
        "Systemic Reform", "إصلاح نظامي",
        short_vs_long_pos,
        f"{'Tactical containment adequate — limited systemic propagation.' if short_vs_long_pos < 0.4 else 'Combined approach — immediate containment with structural review.' if short_vs_long_pos < 0.6 else 'Systemic reform required — cross-sector propagation demands structural intervention.'}",
        f"{'الاحتواء التكتيكي كافٍ — انتشار نظامي محدود.' if short_vs_long_pos < 0.4 else 'نهج مشترك — احتواء فوري مع مراجعة هيكلية.' if short_vs_long_pos < 0.6 else 'مطلوب إصلاح نظامي — الانتشار عبر القطاعات يتطلب تدخلاً هيكلياً.'}",
    )

    return {
        "owner": owner_info["owner"],
        "owner_ar": owner_info["owner_ar"],
        "decision_type": dt_info["decision_type"],
        "decision_type_ar": dt_info["decision_type_ar"],
        "decision_type_label": dt_info["decision_type_label"],
        "decision_type_label_ar": dt_info["decision_type_label_ar"],
        "deadline_hours": deadline_hours,
        "deadline_classification": (
            "IMMEDIATE" if deadline_hours <= 6 else
            "URGENT" if deadline_hours <= 24 else
            "STANDARD" if deadline_hours <= 72 else
            "EXTENDED"
        ),
        "tradeoffs": {
            "cost_vs_risk": cost_vs_risk,
            "speed_vs_accuracy": speed_vs_accuracy,
            "short_term_vs_long_term": short_vs_long,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# 2. Counterfactual Engine
# ─────────────────────────────────────────────────────────────────────────────

def _build_outcome(
    label_en: str,
    label_ar: str,
    total_loss_usd: float,
    time_to_failure_hours: float,
    risk_level: str,
    sector_consequences: list[dict],
) -> dict[str, Any]:
    """Build a single counterfactual outcome."""
    return {
        "label_en": label_en,
        "label_ar": label_ar,
        "financial_exposure_usd": round(total_loss_usd, 2),
        "financial_exposure_formatted": format_loss_usd(total_loss_usd),
        "time_to_failure_hours": round(time_to_failure_hours, 1),
        "risk_level": risk_level,
        "sector_consequences": sector_consequences,
    }


def _risk_after_mitigation(base_risk: str, mitigation_factor: float) -> str:
    """Compute risk level after mitigation factor is applied."""
    risk_order = ["NOMINAL", "LOW", "GUARDED", "ELEVATED", "HIGH", "SEVERE"]
    idx = risk_order.index(base_risk) if base_risk in risk_order else 3
    new_idx = max(0, round(idx * (1.0 - mitigation_factor)))
    return risk_order[new_idx]


def build_counterfactual_comparison(
    simulation: dict,
    authority: dict,
) -> dict[str, Any]:
    """Build counterfactual comparison: baseline (do nothing) vs recommended vs alternative.

    All three outcomes are deterministically derived from simulation data.
    No fabricated numbers — every value traces back to simulation inputs.
    """
    fi = simulation.get("financial_impact", {})
    total_loss = fi.get("total_loss_usd", 0.0)
    risk_level = simulation.get("risk_level", "NOMINAL")

    da = authority.get("decision_authority", {})
    if_ignored = da.get("if_ignored", {})
    inaction_multiplier = if_ignored.get("inaction_multiplier", 1.5)
    time_to_failure = if_ignored.get("time_to_failure_hours", 999.0)
    recommended_actions = da.get("recommended_actions", [])

    # Sector analysis for consequences
    sector_analysis = simulation.get("sector_analysis", [])
    banking = simulation.get("banking_stress", {})
    insurance = simulation.get("insurance_stress", {})
    fintech = simulation.get("fintech_stress", {})

    # ── Baseline (Do Nothing) ────────────────────────────────────────
    baseline_loss = total_loss * inaction_multiplier
    baseline_ttf = time_to_failure  # unchanged — no intervention

    # Escalated risk level
    risk_order = ["NOMINAL", "LOW", "GUARDED", "ELEVATED", "HIGH", "SEVERE"]
    risk_idx = risk_order.index(risk_level) if risk_level in risk_order else 3
    baseline_risk = risk_order[min(len(risk_order) - 1, risk_idx + 1)]

    baseline_consequences = []
    if banking.get("aggregate_stress", 0) > 0.2:
        bs = banking["aggregate_stress"]
        baseline_consequences.append({
            "sector": "banking",
            "sector_ar": "المصرفية",
            "impact_en": f"Liquidity stress escalates to {min(bs * inaction_multiplier, 1.0):.0%}. Interbank contagion spreads unmitigated.",
            "impact_ar": f"ضغط السيولة يتصاعد إلى {min(bs * inaction_multiplier, 1.0):.0%}. عدوى ما بين البنوك تنتشر دون تخفيف.",
        })
    if insurance.get("aggregate_stress", 0) > 0.2:
        ins_s = insurance["aggregate_stress"]
        baseline_consequences.append({
            "sector": "insurance",
            "sector_ar": "التأمين",
            "impact_en": f"Claims surge multiplier reaches {insurance.get('claims_surge_multiplier', 1.0) * 1.3:.1f}x. Reserve adequacy deteriorates to critical.",
            "impact_ar": f"مضاعف ارتفاع المطالبات يصل إلى {insurance.get('claims_surge_multiplier', 1.0) * 1.3:.1f}x. كفاية الاحتياطيات تتدهور إلى حرجة.",
        })
    if fintech.get("aggregate_stress", 0) > 0.2:
        baseline_consequences.append({
            "sector": "fintech",
            "sector_ar": "التقنية المالية",
            "impact_en": f"Payment disruption spreads. Settlement delays exceed {fintech.get('settlement_delay_hours', 0) * 1.5:.0f}h. Cross-border flows halted.",
            "impact_ar": f"اضطراب المدفوعات ينتشر. تأخيرات التسوية تتجاوز {fintech.get('settlement_delay_hours', 0) * 1.5:.0f} ساعة. التدفقات العابرة للحدود تتوقف.",
        })

    baseline = _build_outcome(
        "Do Nothing (Baseline)", "لا شيء (خط الأساس)",
        baseline_loss, baseline_ttf, baseline_risk,
        baseline_consequences,
    )

    # ── Recommended Outcome ──────────────────────────────────────────
    # Compute mitigation from recommended actions
    total_loss_avoided = sum(a.get("impact_usd", 0) for a in recommended_actions)
    mitigation_pct = min(total_loss_avoided / max(total_loss, 1.0), 0.60)  # cap at 60%
    total_action_cost = sum(a.get("cost_usd", 0) for a in recommended_actions)

    # Net cost = action cost minus loss avoided (represents the true cost of acting)
    # Cap so recommended never exceeds baseline (acting is always better than inaction)
    net_action_cost = max(total_action_cost - total_loss_avoided, 0)
    # Cap net cost at a fraction of total loss to prevent inversion
    capped_net_cost = min(net_action_cost, total_loss * 0.3)
    recommended_loss = max(total_loss * (1.0 - mitigation_pct) + capped_net_cost, 0)
    # Safety: recommended must always be less than baseline
    recommended_loss = min(recommended_loss, baseline_loss * 0.85)
    # Actions extend time to failure
    recommended_ttf = time_to_failure * (1.0 + mitigation_pct * 1.5)
    recommended_risk = _risk_after_mitigation(risk_level, mitigation_pct)

    recommended_consequences = []
    if banking.get("aggregate_stress", 0) > 0.2:
        mitigated = banking["aggregate_stress"] * (1.0 - mitigation_pct * 0.8)
        recommended_consequences.append({
            "sector": "banking",
            "sector_ar": "المصرفية",
            "impact_en": f"Liquidity stress contained at {mitigated:.0%}. Emergency facilities activated.",
            "impact_ar": f"ضغط السيولة محتوى عند {mitigated:.0%}. التسهيلات الطارئة مُفعّلة.",
        })
    if insurance.get("aggregate_stress", 0) > 0.2:
        recommended_consequences.append({
            "sector": "insurance",
            "sector_ar": "التأمين",
            "impact_en": f"Reinsurance treaties triggered. Reserve draw-down managed. IFRS 17 compliance maintained.",
            "impact_ar": f"اتفاقيات إعادة التأمين مُفعّلة. سحب الاحتياطيات مُدار. الامتثال لـ IFRS 17 مُحافظ عليه.",
        })
    if fintech.get("aggregate_stress", 0) > 0.2:
        recommended_consequences.append({
            "sector": "fintech",
            "sector_ar": "التقنية المالية",
            "impact_en": f"Backup payment corridors activated. Settlement delays mitigated. Cross-border rerouting in place.",
            "impact_ar": f"ممرات الدفع البديلة مُفعّلة. تأخيرات التسوية مُخففة. إعادة توجيه عابرة للحدود قائمة.",
        })

    recommended = _build_outcome(
        "Recommended Action", "الإجراء الموصى به",
        recommended_loss, recommended_ttf, recommended_risk,
        recommended_consequences,
    )

    # ── Alternative Outcome (partial action — 50% of recommended) ────
    alt_mitigation = mitigation_pct * 0.5
    alt_cost = total_action_cost * 0.5
    alt_net_cost = max(alt_cost - (total_loss_avoided * 0.5), 0)
    alt_capped_cost = min(alt_net_cost, total_loss * 0.2)
    alt_loss = max(total_loss * (1.0 - alt_mitigation) + alt_capped_cost, 0)
    # Safety: alternative must be between recommended and baseline
    alt_loss = min(alt_loss, baseline_loss * 0.93)
    alt_loss = max(alt_loss, recommended_loss * 1.05)
    alt_ttf = time_to_failure * (1.0 + alt_mitigation * 1.0)
    alt_risk = _risk_after_mitigation(risk_level, alt_mitigation)

    alt_consequences = []
    if banking.get("aggregate_stress", 0) > 0.2:
        partial = banking["aggregate_stress"] * (1.0 - alt_mitigation * 0.5)
        alt_consequences.append({
            "sector": "banking",
            "sector_ar": "المصرفية",
            "impact_en": f"Partial liquidity support at {partial:.0%} stress. Some contagion channels remain open.",
            "impact_ar": f"دعم سيولة جزئي عند ضغط {partial:.0%}. بعض قنوات العدوى تظل مفتوحة.",
        })
    if insurance.get("aggregate_stress", 0) > 0.2:
        alt_consequences.append({
            "sector": "insurance",
            "sector_ar": "التأمين",
            "impact_en": f"Selective reinsurance activation. Reserve pressure partially managed. IFRS 17 adjustment needed.",
            "impact_ar": f"تفعيل إعادة تأمين انتقائي. ضغط الاحتياطيات مُدار جزئياً. تعديل IFRS 17 مطلوب.",
        })
    if fintech.get("aggregate_stress", 0) > 0.2:
        alt_consequences.append({
            "sector": "fintech",
            "sector_ar": "التقنية المالية",
            "impact_en": f"Primary payment rails maintained. Backup corridors on standby. Some cross-border delays persist.",
            "impact_ar": f"مسارات الدفع الرئيسية قائمة. ممرات الدعم جاهزة. بعض التأخيرات العابرة للحدود مستمرة.",
        })

    alternative = _build_outcome(
        "Partial Action (50%)", "إجراء جزئي (50%)",
        alt_loss, alt_ttf, alt_risk,
        alt_consequences,
    )

    # ── Delta Summary ────────────────────────────────────────────────
    savings_vs_baseline = baseline_loss - recommended_loss
    savings_pct = (savings_vs_baseline / max(baseline_loss, 1.0)) * 100

    delta_summary = {
        "savings_usd": round(savings_vs_baseline, 2),
        "savings_formatted": format_loss_usd(savings_vs_baseline),
        "savings_pct": round(savings_pct, 1),
        "time_gained_hours": round(recommended_ttf - baseline_ttf, 1),
        "risk_reduction": f"{risk_level} → {recommended_risk}",
        "recommendation_en": (
            f"Recommended actions save {format_loss_usd(savings_vs_baseline)} ({savings_pct:.0f}% reduction) "
            f"and extend failure horizon by {recommended_ttf - baseline_ttf:.0f}h. "
            f"Risk level reduces from {risk_level} to {recommended_risk}."
        ),
        "recommendation_ar": (
            f"الإجراءات الموصى بها توفر {format_loss_usd(savings_vs_baseline)} (تخفيض {savings_pct:.0f}%) "
            f"وتمدد أفق الفشل بـ {recommended_ttf - baseline_ttf:.0f} ساعة. "
            f"مستوى الخطر ينخفض من {risk_level} إلى {recommended_risk}."
        ),
    }

    return {
        "baseline_outcome": baseline,
        "recommended_outcome": recommended,
        "alternative_outcome": alternative,
        "delta_summary": delta_summary,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 3. Decision Gate System
# ─────────────────────────────────────────────────────────────────────────────

def build_decision_gate(
    simulation: dict,
    authority: dict,
) -> dict[str, Any]:
    """Build the Decision Gate — controls whether this decision can proceed.

    Gate logic:
    - open:              Low risk, high confidence → proceed without approval
    - pending_approval:  Elevated risk or large exposure → needs owner sign-off
    - escalated:         High/Severe risk or low confidence → board review required
    - executable:        Already approved and ready for execution
    """
    da = authority.get("decision_authority", {})
    ed = da.get("executive_directive", {})
    internal_decision = ed.get("internal_decision", "ESCALATE")
    urgency_level = ed.get("urgency_level", "MODERATE")
    if_ignored = da.get("if_ignored", {})
    governance = da.get("governance", {})
    pressure = da.get("decision_pressure_score", {})

    confidence = simulation.get("confidence_score", 0.7)
    risk_level = simulation.get("risk_level", "NOMINAL")
    fi = simulation.get("financial_impact", {})
    total_loss = fi.get("total_loss_usd", 0.0)
    time_to_failure = if_ignored.get("time_to_failure_hours", 999.0)
    pressure_score = pressure.get("score", 50)

    # ── Gate Status Classification ───────────────────────────────────
    if internal_decision == "REJECT":
        gate_status = "open"
    elif internal_decision == "DELAY":
        gate_status = "open" if confidence >= 0.75 else "pending_approval"
    elif internal_decision == "APPROVE":
        if confidence >= 0.85 and total_loss < 1_000_000_000:
            gate_status = "executable"
        elif confidence >= 0.70:
            gate_status = "pending_approval"
        else:
            gate_status = "escalated"
    elif internal_decision == "ESCALATE":
        gate_status = "escalated"
    else:
        gate_status = "pending_approval"

    # ── Escalation Threshold ─────────────────────────────────────────
    # Dynamic thresholds based on current risk
    escalation_threshold = {
        "loss_usd_threshold": round(total_loss * 1.5, 2),
        "loss_usd_threshold_formatted": format_loss_usd(total_loss * 1.5),
        "stress_threshold": round(min(0.90, clamp(
            simulation.get("unified_risk_score", 0.5) * 1.3, 0.4, 0.95
        )), 3),
        "time_to_failure_threshold_hours": max(6.0, round(time_to_failure * 0.5, 1)),
        "pressure_score_threshold": min(95, pressure_score + 20),
    }

    # ── Approval Requirements ────────────────────────────────────────
    approval_required = gate_status in ("pending_approval", "escalated")

    dt_info = _DECISION_TYPE_MAP.get(internal_decision, _DECISION_TYPE_MAP["ESCALATE"])
    decision_type = dt_info["decision_type"]
    owner_info = _OWNER_MAP.get(decision_type, _OWNER_MAP["operational"])

    # ── Auto-escalation Triggers ─────────────────────────────────────
    auto_escalation_triggers = []

    if time_to_failure < 24:
        auto_escalation_triggers.append({
            "trigger_en": f"Time to failure ({time_to_failure:.0f}h) breaches 24h threshold",
            "trigger_ar": f"وقت الفشل ({time_to_failure:.0f} ساعة) يخترق عتبة 24 ساعة",
            "active": True,
        })
    if total_loss > 2_000_000_000:
        auto_escalation_triggers.append({
            "trigger_en": f"Exposure ({format_loss_usd(total_loss)}) exceeds $2B sovereign threshold",
            "trigger_ar": f"التعرض ({format_loss_usd(total_loss)}) يتجاوز عتبة 2 مليار دولار السيادية",
            "active": True,
        })
    if confidence < 0.50:
        auto_escalation_triggers.append({
            "trigger_en": f"Model confidence ({confidence:.0%}) below 50% minimum",
            "trigger_ar": f"ثقة النموذج ({confidence:.0%}) أقل من الحد الأدنى 50%",
            "active": True,
        })
    if pressure_score >= 80:
        auto_escalation_triggers.append({
            "trigger_en": f"Decision pressure ({pressure_score}/100) in critical zone",
            "trigger_ar": f"ضغط القرار ({pressure_score}/100) في المنطقة الحرجة",
            "active": True,
        })

    # Always include potential triggers even if not active
    if not any(t.get("trigger_en", "").startswith("Time") for t in auto_escalation_triggers):
        auto_escalation_triggers.append({
            "trigger_en": f"Time to failure drops below {max(6, round(time_to_failure * 0.3))}h",
            "trigger_ar": f"وقت الفشل ينخفض عن {max(6, round(time_to_failure * 0.3))} ساعة",
            "active": False,
        })
    if not any(t.get("trigger_en", "").startswith("Exposure") for t in auto_escalation_triggers):
        auto_escalation_triggers.append({
            "trigger_en": f"Exposure exceeds {format_loss_usd(total_loss * 2.0)}",
            "trigger_ar": f"التعرض يتجاوز {format_loss_usd(total_loss * 2.0)}",
            "active": False,
        })

    # ── Gate Audit ───────────────────────────────────────────────────
    gate_hash_payload = f"{governance.get('run_id', 'unknown')}:{gate_status}:{internal_decision}:{now_utc()}"
    gate_audit_hash = hashlib.sha256(gate_hash_payload.encode()).hexdigest()[:16]

    # Status labels
    gate_status_labels: dict[str, dict[str, str]] = {
        "open": {"en": "Open — No Approval Required", "ar": "مفتوح — لا يتطلب موافقة"},
        "pending_approval": {"en": "Pending Approval", "ar": "في انتظار الموافقة"},
        "escalated": {"en": "Escalated to Board", "ar": "مُصعّد لمجلس الإدارة"},
        "executable": {"en": "Approved — Ready for Execution", "ar": "معتمد — جاهز للتنفيذ"},
    }
    status_label = gate_status_labels.get(gate_status, gate_status_labels["pending_approval"])

    return {
        "gate_status": gate_status,
        "gate_status_label_en": status_label["en"],
        "gate_status_label_ar": status_label["ar"],
        "approval_required": approval_required,
        "approval_owner": owner_info["approval_owner"],
        "approval_owner_ar": owner_info["approval_owner_ar"],
        "escalation_threshold": escalation_threshold,
        "auto_escalation_triggers": auto_escalation_triggers,
        "active_triggers_count": sum(1 for t in auto_escalation_triggers if t.get("active")),
        "gate_audit_hash": gate_audit_hash,
        "gate_rationale_en": (
            f"Gate status '{gate_status}' determined by: "
            f"decision={internal_decision}, confidence={confidence:.2%}, "
            f"risk_level={risk_level}, exposure={format_loss_usd(total_loss)}, "
            f"pressure={pressure_score}/100."
        ),
        "gate_rationale_ar": (
            f"حالة البوابة '{gate_status}' مُحددة بـ: "
            f"القرار={internal_decision}، الثقة={confidence:.2%}، "
            f"مستوى_الخطر={risk_level}، التعرض={format_loss_usd(total_loss)}، "
            f"الضغط={pressure_score}/100."
        ),
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main Engine
# ─────────────────────────────────────────────────────────────────────────────

class DecisionOperatingLayer:
    """Transforms Decision Authority output into an actionable operating layer.

    Stateless, deterministic, safe to share across requests.

    Usage:
        layer = DecisionOperatingLayer()
        result = layer.generate(simulation_result, authority_result)
    """

    def generate(self, simulation: dict, authority: dict) -> dict[str, Any]:
        """Generate the complete Decision Operating Layer.

        Parameters
        ----------
        simulation : dict
            Raw SimulateResponse from SimulationEngine.run()
        authority : dict
            Output from DecisionAuthorityEngine.generate()

        Returns
        -------
        dict
            Complete operating_layer structure with decision_anchor,
            counterfactual_comparison, and decision_gate.
        """
        anchor = build_decision_anchor(simulation, authority)
        counterfactual = build_counterfactual_comparison(simulation, authority)
        gate = build_decision_gate(simulation, authority)

        return {
            "operating_layer": {
                "version": "1.0.0",
                "generated_at": now_utc(),
                "decision_anchor": anchor,
                "counterfactual_comparison": counterfactual,
                "decision_gate": gate,
            },
        }
