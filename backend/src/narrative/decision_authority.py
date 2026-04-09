"""
Impact Observatory | مرصد الأثر
Decision Authority Engine — transforms simulation + narrative into
executive decision directives.

This is NOT a dashboard. This is NOT a report.
This is a Chief Risk Officer AI.

Architecture Layer: Decision Authority (sits above NarrativeEngine)
Dependencies: simulation_engine, narrative.engine, config
All outputs deterministic. No LLM. No ambiguity.

Decision semantics (v2 — executive-grade):
  Internal classifier → Display label mapping:
    APPROVE  → EXECUTE
    DELAY    → MONITOR
    REJECT   → NO_ACTION
    ESCALATE → ESCALATE
  Internal labels preserved for backward compatibility.
  `display_decision` is the board-facing label.

Output contract:
  decision_authority {
    executive_directive → EXECUTE | ESCALATE | MONITOR | NO_ACTION
    why_this_decision → root cause, systemic risk, confidence
    if_ignored → financial impact, time to failure, worst case
    recommended_actions → ranked, owned, deadlined, quantified, trackable
    decision_pressure_score → 0-100 with drivers
    governance → audit, confidence, explainability
  }
"""
from __future__ import annotations

import hashlib
import math
import uuid
from datetime import datetime, timezone
from typing import Any

from src.utils import (
    clamp,
    format_loss_usd,
    classify_stress,
    now_utc,
    severity_label,
    severity_label_ar,
    risk_label_ar,
)


# ─────────────────────────────────────────────────────────────────────────────
# Decision label mapping: internal → display (executive-grade)
# ─────────────────────────────────────────────────────────────────────────────

_DECISION_DISPLAY: dict[str, str] = {
    "APPROVE": "EXECUTE",
    "DELAY": "MONITOR",
    "REJECT": "NO_ACTION",
    "ESCALATE": "ESCALATE",
}

_DECISION_DISPLAY_AR: dict[str, str] = {
    "APPROVE": "نفّذ",
    "DELAY": "راقب",
    "REJECT": "لا_إجراء",
    "ESCALATE": "صعّد",
}

# Reverse map for clients sending display labels
_DISPLAY_TO_INTERNAL: dict[str, str] = {v: k for k, v in _DECISION_DISPLAY.items()}


def map_decision(internal: str) -> str:
    """Map internal decision label to executive display label."""
    return _DECISION_DISPLAY.get(internal, internal)


def map_decision_ar(internal: str) -> str:
    """Map internal decision label to Arabic display label."""
    return _DECISION_DISPLAY_AR.get(internal, internal)


# ─────────────────────────────────────────────────────────────────────────────
# Decision classification matrix
# ─────────────────────────────────────────────────────────────────────────────

def _classify_decision(
    risk_level: str,
    time_to_failure_hours: float,
    total_loss_usd: float,
    confidence: float,
) -> str:
    """Determine executive decision: APPROVE | REJECT | ESCALATE | DELAY.

    Decision logic:
    - APPROVE: High confidence, clear action path, severe risk
    - ESCALATE: High risk but low confidence or systemic scope
    - REJECT: Insufficient evidence, low confidence, minimal risk
    - DELAY: Moderate risk, high confidence, non-critical timeline
    """
    if risk_level in ("SEVERE", "HIGH") and time_to_failure_hours < 48:
        return "APPROVE"  # Crisis requires immediate action
    if risk_level in ("SEVERE", "HIGH") and confidence < 0.60:
        return "ESCALATE"  # Severe but uncertain — need senior review
    if risk_level in ("HIGH", "ELEVATED") and total_loss_usd > 500_000_000:
        return "APPROVE"  # Material loss threshold breached
    if risk_level in ("ELEVATED",) and confidence >= 0.75:
        return "APPROVE"  # Confident elevated risk
    if risk_level in ("ELEVATED",) and confidence < 0.60:
        return "ESCALATE"  # Uncertain elevated risk
    if risk_level in ("GUARDED",) and time_to_failure_hours > 168:
        return "DELAY"  # Guarded with time buffer
    if risk_level in ("LOW", "NOMINAL"):
        return "DELAY" if confidence > 0.70 else "REJECT"
    return "ESCALATE"


def _classify_urgency(
    risk_level: str,
    time_to_failure_hours: float,
    total_loss_usd: float,
) -> str:
    """Map to CRITICAL | HIGH | MODERATE | LOW."""
    if risk_level == "SEVERE" or time_to_failure_hours < 12:
        return "CRITICAL"
    if risk_level == "HIGH" or time_to_failure_hours < 48:
        return "HIGH"
    if risk_level == "ELEVATED" or total_loss_usd > 200_000_000:
        return "MODERATE"
    return "LOW"


def _compute_pressure_score(
    risk_level: str,
    time_to_failure_hours: float,
    total_loss_usd: float,
    confidence: float,
    propagation_score: float,
    sector_count: int,
) -> tuple[int, list[str]]:
    """Compute decision pressure score (0-100) with driver breakdown."""
    score = 0.0
    drivers = []

    # Urgency pressure (0-30)
    urgency_map = {"SEVERE": 30, "HIGH": 24, "ELEVATED": 16, "GUARDED": 8, "LOW": 4, "NOMINAL": 0}
    urgency_pts = urgency_map.get(risk_level, 10)
    score += urgency_pts
    if urgency_pts >= 20:
        drivers.append(f"Risk level {risk_level} demands immediate response")

    # Time pressure (0-25)
    if time_to_failure_hours < 12:
        score += 25
        drivers.append(f"First failure in {time_to_failure_hours:.0f}h — critical timeline")
    elif time_to_failure_hours < 48:
        score += 18
        drivers.append(f"First failure in {time_to_failure_hours:.0f}h — action window closing")
    elif time_to_failure_hours < 168:
        score += 10
        drivers.append(f"Failure horizon: {time_to_failure_hours:.0f}h — monitor closely")
    else:
        score += 3

    # Financial pressure (0-25)
    if total_loss_usd > 5_000_000_000:
        score += 25
        drivers.append(f"Exposure {format_loss_usd(total_loss_usd)} — catastrophic financial risk")
    elif total_loss_usd > 1_000_000_000:
        score += 20
        drivers.append(f"Exposure {format_loss_usd(total_loss_usd)} — material sovereign risk")
    elif total_loss_usd > 200_000_000:
        score += 14
        drivers.append(f"Exposure {format_loss_usd(total_loss_usd)} — significant sector impact")
    elif total_loss_usd > 50_000_000:
        score += 8
        drivers.append(f"Exposure {format_loss_usd(total_loss_usd)} — notable financial impact")
    else:
        score += 3

    # Systemic pressure (0-10)
    if propagation_score > 0.7:
        score += 10
        drivers.append("High systemic propagation — multi-sector contagion active")
    elif propagation_score > 0.4:
        score += 6
        drivers.append("Moderate cross-sector propagation detected")

    # Breadth pressure (0-10)
    if sector_count >= 5:
        score += 10
        drivers.append(f"{sector_count} sectors under stress — broad systemic event")
    elif sector_count >= 3:
        score += 6
        drivers.append(f"{sector_count} sectors affected — spreading disruption")

    return min(100, round(score)), drivers


# ─────────────────────────────────────────────────────────────────────────────
# Risk escalation path builder
# ─────────────────────────────────────────────────────────────────────────────

_ESCALATION_TEMPLATES = {
    "CRITICAL": [
        "Immediate liquidity crisis across GCC interbank markets within 12 hours",
        "Central bank emergency facilities activated; sovereign credit watch triggered",
        "Cross-border capital flight accelerates; FX reserves draw-down begins",
        "Full settlement system failure; payment rails offline across region",
        "Sovereign rating downgrade initiated; international investor confidence collapses",
    ],
    "HIGH": [
        "Sector stress breaches regulatory thresholds within 24-48 hours",
        "Interbank contagion propagates to second-tier financial institutions",
        "Insurance and reinsurance markets reprice GCC exposure",
        "Credit committee freezes across banking sector; lending capacity contracts",
        "Government emergency fiscal measures required",
    ],
    "MODERATE": [
        "Gradual deterioration of sector-specific risk metrics over 3-7 days",
        "Market confidence erosion leads to widening credit spreads",
        "Operational disruption cascades through supply chain dependencies",
    ],
    "LOW": [
        "Continued monitoring with standard risk protocols",
        "Minor sector adjustments within normal operating parameters",
    ],
}


# ─────────────────────────────────────────────────────────────────────────────
# Decision Authority Engine
# ─────────────────────────────────────────────────────────────────────────────

class DecisionAuthorityEngine:
    """Transforms simulation + narrative into executive decision directives.

    This engine produces DECISIONS, not reports. Every output forces action.

    Usage:
        engine = DecisionAuthorityEngine()
        directive = engine.generate(simulation_result, narrative_result)
    """

    def generate(self, simulation: dict, narrative: dict) -> dict[str, Any]:
        """Generate the complete decision authority brief.

        Parameters
        ----------
        simulation : dict
            Raw SimulateResponse from SimulationEngine.run()
        narrative : dict
            Output from NarrativeEngine.generate()

        Returns
        -------
        dict
            Complete decision_authority structure per contract.
        """
        # ── Extract core metrics ─────────────────────────────────────────
        scenario_id = simulation.get("scenario_id", "unknown")
        risk_level = simulation.get("risk_level", "NOMINAL")
        confidence = simulation.get("confidence_score", 0.7)
        propagation_score = simulation.get("propagation_score", 0.0)
        peak_day = simulation.get("peak_day", 1)
        model_version = simulation.get("model_version", "2.1.0")
        run_id = simulation.get("run_id", "unknown")
        severity = simulation.get("severity", simulation.get("event_severity", 0.5))

        # Financial
        fi = simulation.get("financial_impact", {})
        total_loss_usd = fi.get("total_loss_usd", 0.0)
        total_loss_fmt = fi.get("total_loss_formatted", format_loss_usd(total_loss_usd))

        # Sector analysis
        sector_analysis = simulation.get("sector_analysis", [])
        stressed_sectors = [s for s in sector_analysis if s.get("stress", 0) > 0.2]
        sector_count = len(stressed_sectors)

        # Decision plan
        dp = simulation.get("decision_plan", {})
        time_to_failure = dp.get("time_to_first_failure_hours", 999.0)
        business_severity = dp.get("business_severity", "LOW")
        actions = dp.get("actions", [])

        # Narrative context
        es = narrative.get("executive_summary", {})
        urgency_data = es.get("urgency", {})

        # ── Classify decision ────────────────────────────────────────────
        decision = _classify_decision(risk_level, time_to_failure, total_loss_usd, confidence)
        urgency_level = _classify_urgency(risk_level, time_to_failure, total_loss_usd)
        pressure_score, pressure_drivers = _compute_pressure_score(
            risk_level, time_to_failure, total_loss_usd,
            confidence, propagation_score, sector_count,
        )

        # ── Build audit hash ─────────────────────────────────────────────
        audit_payload = f"{run_id}:{scenario_id}:{severity}:{decision}:{now_utc()}"
        audit_id = hashlib.sha256(audit_payload.encode()).hexdigest()[:16]

        # ── 1. Executive Directive ───────────────────────────────────────
        executive_directive = self._build_executive_directive(
            decision=decision,
            urgency_level=urgency_level,
            risk_level=risk_level,
            scenario_id=scenario_id,
            total_loss_fmt=total_loss_fmt,
            total_loss_usd=total_loss_usd,
            time_to_failure=time_to_failure,
            sector_count=sector_count,
            severity=severity,
        )

        # ── 2. Why This Decision ─────────────────────────────────────────
        why_this_decision = self._build_why(
            simulation=simulation,
            narrative=narrative,
            decision=decision,
            risk_level=risk_level,
            confidence=confidence,
            propagation_score=propagation_score,
            total_loss_usd=total_loss_usd,
            sector_count=sector_count,
        )

        # ── 3. If Ignored ────────────────────────────────────────────────
        if_ignored = self._build_if_ignored(
            risk_level=risk_level,
            urgency_level=urgency_level,
            total_loss_usd=total_loss_usd,
            time_to_failure=time_to_failure,
            sector_count=sector_count,
            scenario_id=scenario_id,
            severity=severity,
        )

        # ── 4. Recommended Actions ───────────────────────────────────────
        recommended_actions = self._build_recommended_actions(
            actions=actions,
            urgency_level=urgency_level,
        )

        # ── 5. Decision Pressure Score ───────────────────────────────────
        decision_pressure = {
            "score": pressure_score,
            "classification": (
                "CRITICAL" if pressure_score >= 80 else
                "HIGH" if pressure_score >= 60 else
                "ELEVATED" if pressure_score >= 40 else
                "MODERATE" if pressure_score >= 20 else
                "LOW"
            ),
            "drivers": pressure_drivers,
        }

        # ── 6. Governance ────────────────────────────────────────────────
        governance = {
            "audit_id": audit_id,
            "run_id": run_id,
            "model_version": model_version,
            "model_confidence": round(confidence, 4),
            "decision_timestamp": now_utc(),
            "explainability": (
                f"Directive '{map_decision(decision)}' (internal: {decision}) derived deterministically from: "
                f"risk_level={risk_level}, time_to_failure={time_to_failure:.1f}h, "
                f"total_loss={total_loss_fmt}, confidence={confidence:.2%}, "
                f"sectors_stressed={sector_count}. No human override applied. "
                f"SHA-256 audit trail: {audit_id}."
            ),
            "explainability_ar": (
                f"التوجيه '{map_decision_ar(decision)}' (داخلي: {decision}) مُستمد حسابياً من: "
                f"مستوى_الخطر={risk_level}، وقت_الفشل={time_to_failure:.1f}ساعة، "
                f"إجمالي_الخسارة={total_loss_fmt}، الثقة={confidence:.2%}، "
                f"القطاعات_المتوترة={sector_count}. لم يُطبَّق تجاوز بشري. "
                f"مسار التدقيق SHA-256: {audit_id}."
            ),
            "risk_classification": risk_level,
            "decision_basis": {
                "risk_level": risk_level,
                "time_to_failure_hours": round(time_to_failure, 1),
                "total_loss_usd": round(total_loss_usd, 2),
                "confidence": round(confidence, 4),
                "propagation_score": round(propagation_score, 4),
                "sectors_stressed": sector_count,
            },
        }

        return {
            "decision_authority": {
                "executive_directive": executive_directive,
                "why_this_decision": why_this_decision,
                "if_ignored": if_ignored,
                "recommended_actions": recommended_actions,
                "decision_pressure_score": decision_pressure,
                "governance": governance,
            },
        }

    # ─────────────────────────────────────────────────────────────────────
    # 1. Executive Directive
    # ─────────────────────────────────────────────────────────────────────

    def _build_executive_directive(
        self, *,
        decision: str,
        urgency_level: str,
        risk_level: str,
        scenario_id: str,
        total_loss_fmt: str,
        total_loss_usd: float,
        time_to_failure: float,
        sector_count: int,
        severity: float,
    ) -> dict:
        scenario_name = scenario_id.replace("_", " ").title()

        display = map_decision(decision)
        display_ar = map_decision_ar(decision)

        # Headline — no passive language, uses display labels
        headline_map = {
            "APPROVE": {
                "en": f"EXECUTE IMMEDIATELY: {scenario_name} threatens {total_loss_fmt} exposure across {sector_count} GCC sectors. Failure window: {time_to_failure:.0f} hours.",
                "ar": f"نفّذ فوراً: {scenario_name} يهدد بتعرض {total_loss_fmt} عبر {sector_count} قطاعات خليجية. نافذة الفشل: {time_to_failure:.0f} ساعة.",
            },
            "ESCALATE": {
                "en": f"ESCALATE TO BOARD: {scenario_name} presents {total_loss_fmt} systemic risk with insufficient confidence for autonomous execution.",
                "ar": f"صعّد لمجلس الإدارة: {scenario_name} يمثل خطراً نظامياً بقيمة {total_loss_fmt} بثقة غير كافية للتنفيذ المستقل.",
            },
            "DELAY": {
                "en": f"MONITOR: {scenario_name} — {total_loss_fmt} exposure within acceptable risk envelope. Reassess in {min(72, time_to_failure / 2):.0f} hours.",
                "ar": f"راقب: {scenario_name} — تعرض {total_loss_fmt} ضمن غلاف المخاطر المقبول. أعد التقييم خلال {min(72, time_to_failure / 2):.0f} ساعة.",
            },
            "REJECT": {
                "en": f"NO ACTION REQUIRED: {scenario_name} — risk metrics within normal operating parameters. Standard monitoring continues.",
                "ar": f"لا إجراء مطلوب: {scenario_name} — مقاييس المخاطر ضمن معايير التشغيل العادية. تستمر المراقبة القياسية.",
            },
        }

        headlines = headline_map.get(decision, headline_map["ESCALATE"])

        # Action statement — directive language only
        action_map = {
            "APPROVE": {
                "en": f"This decision must be executed within {max(1, time_to_failure / 3):.0f} hours. Activate all {sector_count} sector contingency protocols. Deploy {total_loss_fmt} exposure mitigation framework. Report execution status to Chief Risk Officer within 4 hours.",
                "ar": f"يجب تنفيذ هذا القرار خلال {max(1, time_to_failure / 3):.0f} ساعة. فعّل جميع بروتوكولات طوارئ القطاعات الـ{sector_count}. انشر إطار تخفيف التعرض بقيمة {total_loss_fmt}. أبلغ كبير مسؤولي المخاطر بحالة التنفيذ خلال 4 ساعات.",
            },
            "ESCALATE": {
                "en": f"Convene emergency risk committee within 6 hours. Present {total_loss_fmt} exposure analysis with confidence assessment. Board must determine action path for {scenario_name}. Pre-stage contingency resources pending committee decision.",
                "ar": f"اعقد لجنة المخاطر الطارئة خلال 6 ساعات. قدّم تحليل التعرض بقيمة {total_loss_fmt} مع تقييم الثقة. يجب على المجلس تحديد مسار العمل لـ{scenario_name}. جهّز موارد الطوارئ بانتظار قرار اللجنة.",
            },
            "DELAY": {
                "en": f"Maintain heightened monitoring on {sector_count} affected sectors. Set automated escalation triggers at 1.5x current stress levels. Schedule reassessment in {min(72, time_to_failure / 2):.0f} hours. No resource deployment required at this time.",
                "ar": f"حافظ على مراقبة مكثفة على {sector_count} قطاعات متأثرة. اضبط محفزات التصعيد التلقائي عند 1.5 ضعف مستويات الضغط الحالية. جدول إعادة التقييم خلال {min(72, time_to_failure / 2):.0f} ساعة. لا يلزم نشر موارد حالياً.",
            },
            "REJECT": {
                "en": f"Continue standard risk monitoring protocols. No executive action required. Next scheduled review per standard operating cadence.",
                "ar": f"استمر في بروتوكولات مراقبة المخاطر القياسية. لا يتطلب إجراء تنفيذي. المراجعة التالية المجدولة وفق الإيقاع التشغيلي القياسي.",
            },
        }

        actions = action_map.get(decision, action_map["ESCALATE"])

        return {
            "headline_en": headlines["en"],
            "headline_ar": headlines["ar"],
            "internal_decision": decision,
            "display_decision": display,
            "display_decision_ar": display_ar,
            "decision": display,  # primary field uses display label
            "urgency_level": urgency_level,
            "action_statement_en": actions["en"],
            "action_statement_ar": actions["ar"],
        }

    # ─────────────────────────────────────────────────────────────────────
    # 2. Why This Decision
    # ─────────────────────────────────────────────────────────────────────

    def _build_why(
        self, *,
        simulation: dict,
        narrative: dict,
        decision: str,
        risk_level: str,
        confidence: float,
        propagation_score: float,
        total_loss_usd: float,
        sector_count: int,
    ) -> dict:
        scenario_id = simulation.get("scenario_id", "unknown")
        es = narrative.get("executive_summary", {})
        cs = narrative.get("causal_chain_story", {})

        total_loss_fmt = format_loss_usd(total_loss_usd)

        # Determine root cause from narrative
        root_cause = cs.get("root_cause_en", "Systemic disruption propagating through GCC financial network")

        # Systemic risk assessment
        systemic_descriptors = []
        if propagation_score > 0.7:
            systemic_descriptors.append("Active multi-sector contagion")
        if sector_count >= 4:
            systemic_descriptors.append(f"{sector_count} sectors under stress simultaneously")
        if total_loss_usd > 1_000_000_000:
            systemic_descriptors.append(f"{total_loss_fmt} sovereign-level exposure")

        banking = simulation.get("banking_stress", {})
        if banking.get("aggregate_stress", 0) > 0.6:
            systemic_descriptors.append("Banking system stress exceeds prudential thresholds")

        insurance = simulation.get("insurance_stress", {})
        if insurance.get("aggregate_stress", 0) > 0.5:
            systemic_descriptors.append("Insurance sector reserves under pressure")

        systemic_risk = ". ".join(systemic_descriptors) if systemic_descriptors else "Contained disruption with limited systemic propagation"

        # Decision reason — uses display labels (EXECUTE/MONITOR/NO_ACTION/ESCALATE)
        display = map_decision(decision)
        display_ar = map_decision_ar(decision)

        reason_map = {
            "APPROVE": f"Directive EXECUTE issued because risk level {risk_level} combined with {total_loss_fmt} exposure and {sector_count} stressed sectors exceeds autonomous action threshold. Model confidence {confidence:.0%} supports immediate execution without board escalation.",
            "ESCALATE": f"Directive ESCALATE issued because model confidence ({confidence:.0%}) is insufficient for autonomous execution of {total_loss_fmt} exposure mitigation. Board oversight required for {risk_level}-level systemic risk.",
            "DELAY": f"Directive MONITOR issued because risk metrics remain within acceptable bounds. {total_loss_fmt} exposure does not trigger immediate action threshold. Active monitoring continues with automated escalation triggers.",
            "REJECT": f"Directive NO_ACTION issued because scenario risk level {risk_level} and {total_loss_fmt} exposure fall within normal operating parameters. No executive intervention required.",
        }

        reason_ar_map = {
            "APPROVE": f"صدر توجيه نفّذ لأن مستوى الخطر {risk_level} مع تعرض {total_loss_fmt} و{sector_count} قطاعات متوترة يتجاوز عتبة الإجراء المستقل. ثقة النموذج {confidence:.0%} تدعم التنفيذ الفوري دون تصعيد لمجلس الإدارة.",
            "ESCALATE": f"صدر توجيه صعّد لأن ثقة النموذج ({confidence:.0%}) غير كافية للتنفيذ المستقل لتخفيف التعرض بقيمة {total_loss_fmt}. يلزم إشراف المجلس لمخاطر نظامية بمستوى {risk_level}.",
            "DELAY": f"صدر توجيه راقب لأن مقاييس المخاطر تظل ضمن الحدود المقبولة. تعرض {total_loss_fmt} لا يُفعّل عتبة الإجراء الفوري. تستمر المراقبة النشطة مع محفزات التصعيد التلقائي.",
            "REJECT": f"صدر توجيه لا_إجراء لأن مستوى خطر السيناريو {risk_level} وتعرض {total_loss_fmt} يقعان ضمن معايير التشغيل العادية. لا يلزم تدخل تنفيذي.",
        }

        return {
            "summary_en": reason_map.get(decision, reason_map["ESCALATE"]),
            "summary_ar": reason_ar_map.get(decision, reason_ar_map["ESCALATE"]),
            "root_cause": root_cause,
            "systemic_risk": systemic_risk,
            "confidence": round(confidence, 4),
        }

    # ─────────────────────────────────────────────────────────────────────
    # 3. If Ignored
    # ─────────────────────────────────────────────────────────────────────

    def _build_if_ignored(
        self, *,
        risk_level: str,
        urgency_level: str,
        total_loss_usd: float,
        time_to_failure: float,
        sector_count: int,
        scenario_id: str,
        severity: float,
    ) -> dict:
        total_loss_fmt = format_loss_usd(total_loss_usd)

        # Escalated loss (inaction multiplier: 1.5x–3x)
        inaction_multiplier = {
            "CRITICAL": 3.0,
            "HIGH": 2.2,
            "MODERATE": 1.5,
            "LOW": 1.1,
        }.get(urgency_level, 1.5)

        escalated_loss = total_loss_usd * inaction_multiplier
        escalated_loss_fmt = format_loss_usd(escalated_loss)

        # Escalation path
        escalation_steps = _ESCALATION_TEMPLATES.get(urgency_level, _ESCALATION_TEMPLATES["MODERATE"])

        # Worst case
        worst_case_map = {
            "CRITICAL": f"Complete systemic failure across {sector_count} GCC sectors. Total exposure escalates to {escalated_loss_fmt}. Settlement systems offline. Sovereign credit downgrade. International market contagion. Recovery timeline: 6-18 months.",
            "HIGH": f"Cascading sector failures with {escalated_loss_fmt} exposure. Banking liquidity crisis triggers government intervention. Insurance market repricing. Recovery timeline: 3-9 months.",
            "MODERATE": f"Progressive deterioration of {sector_count} sectors. Exposure grows to {escalated_loss_fmt}. Market confidence erosion. Gradual recovery over 2-6 months.",
            "LOW": f"Minimal escalation. Contained sector stress with {total_loss_fmt} exposure. Self-correcting within normal market cycles.",
        }

        # Regulatory exposure
        regulatory_map = {
            "CRITICAL": "PDPL, IFRS 17, Basel III, and CBUAE prudential framework violations imminent. Regulatory enforcement action probable. Board personal liability exposure activated.",
            "HIGH": "Regulatory reporting thresholds breached. IFRS 17 risk adjustment recalculation required. Central bank notification mandatory within 48 hours.",
            "MODERATE": "Approaching regulatory thresholds. Enhanced monitoring required. Quarterly stress test results may require revision.",
            "LOW": "Within regulatory tolerance bands. Standard reporting cadence sufficient.",
        }

        # Market impact
        market_map = {
            "CRITICAL": "Immediate repricing of GCC sovereign debt. CDS spreads widen 150-300bps. Equity markets decline 8-15%. Foreign capital outflow accelerates. Rating agency downgrades within 72 hours.",
            "HIGH": "GCC bond spread widening 50-150bps. Equity correction 3-8%. Institutional investor risk committees trigger regional reviews. Insurance market hardening begins.",
            "MODERATE": "Gradual spread widening 20-50bps. Selective equity sector rotation. Increased hedging activity. Market uncertainty premium rises.",
            "LOW": "Minimal market impact. Normal volatility range. No systemic repricing expected.",
        }

        return {
            "financial_impact_usd": round(escalated_loss, 2),
            "financial_impact_formatted": escalated_loss_fmt,
            "inaction_multiplier": inaction_multiplier,
            "time_to_failure_hours": round(time_to_failure, 1),
            "risk_escalation_path": escalation_steps,
            "worst_case_scenario": worst_case_map.get(urgency_level, worst_case_map["MODERATE"]),
            "regulatory_exposure": regulatory_map.get(urgency_level, regulatory_map["MODERATE"]),
            "market_impact": market_map.get(urgency_level, market_map["MODERATE"]),
        }

    # ─────────────────────────────────────────────────────────────────────
    # 4. Recommended Actions
    # ─────────────────────────────────────────────────────────────────────

    def _build_recommended_actions(
        self, *,
        actions: list,
        urgency_level: str,
    ) -> list[dict]:
        """Transform simulation actions into trackable executive-grade directives.

        Each action is assigned a unique action_id and tracking fields:
          - status: PENDING → ACKNOWLEDGED → IN_PROGRESS → DONE | BLOCKED
          - owner_acknowledged: bool (owner has seen and accepted)
          - execution_progress: 0-100 (% complete)
          - created_at / updated_at: ISO 8601 timestamps
          - notes: list of timestamped operator notes
        """
        recommended = []
        ts_now = now_utc()

        # Urgency-based deadline multiplier
        deadline_mult = {
            "CRITICAL": 0.5,
            "HIGH": 0.75,
            "MODERATE": 1.0,
            "LOW": 2.0,
        }.get(urgency_level, 1.0)

        for i, act in enumerate(actions[:10]):
            base_hours = act.get("time_to_act_hours", 24)
            deadline = max(1, round(base_hours * deadline_mult))
            loss_avoided = act.get("loss_avoided_usd", 0)
            cost = act.get("cost_usd", 0)

            # Determine owner from sector
            sector = act.get("sector", "cross-sector")
            owner_map = {
                "banking": "Chief Banking Officer / Treasury Head",
                "insurance": "Chief Underwriting Officer / Head of Claims",
                "fintech": "CTO / Head of Digital Payments",
                "energy": "VP Energy Trading / Supply Chain Director",
                "maritime": "VP Maritime Operations / Port Authority Liaison",
                "logistics": "Head of Supply Chain / Operations Director",
                "government": "Government Relations Director / Sovereign Risk Desk",
                "infrastructure": "CIO / Infrastructure Operations Manager",
            }

            # Generate deterministic action_id from content hash
            action_text = act.get("action", f"Action {i + 1}")
            action_hash = hashlib.sha256(
                f"{action_text}:{sector}:{i}:{ts_now}".encode()
            ).hexdigest()[:12]
            action_id = f"ACT-{action_hash}"

            recommended.append({
                "action_id": action_id,
                "action": action_text,
                "action_ar": act.get("action_ar", ""),
                "owner": owner_map.get(sector, "Chief Risk Officer"),
                "sector": sector,
                "deadline_hours": deadline,
                "impact_usd": round(loss_avoided, 2),
                "impact_formatted": format_loss_usd(loss_avoided),
                "cost_usd": round(cost, 2),
                "cost_formatted": format_loss_usd(cost),
                "roi_multiple": round(loss_avoided / max(cost, 1), 1),
                "priority": i + 1,
                # ── Tracking fields ──────────────────────────────────
                "status": "PENDING",
                "owner_acknowledged": False,
                "execution_progress": 0,
                "created_at": ts_now,
                "updated_at": ts_now,
                "notes": [],
                "feasibility": act.get("feasibility", 0.8),
            })

        return recommended
