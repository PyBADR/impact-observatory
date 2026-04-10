"""
Decision Explainability Engine — causal explanation for every decision.

Explains WHY a decision exists by tracing:
  1. causal_path — which propagation events triggered the need
  2. trigger_reason — what threshold was breached
  3. propagation_summary — how the shock reached the affected sector
  4. regime_context — what regime state amplified or compressed the impact
  5. ranking_reason — why this decision ranked where it did
  6. rejection_reason — if rejected, why (from ValidationEngine)

Rules:
  - Every decision MUST be explainable
  - Explanation MUST reference propagation + regime
  - Every field bilingual (EN/AR)
  - No decision may pass to output without an explanation attached

Consumed by: Stage 80 pipeline
Input: decisions + impact_map + validation_results + ranked_decisions + scenario_validation
Output: list[DecisionExplanation]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.formatter_engine import FormattedExecutiveDecision
from src.schemas.impact_map import ImpactMapResponse
from src.decision_trust.validation_engine import ValidationResult
from src.decision_calibration.ranking_engine import RankedDecision
from src.decision_trust.scenario_enforcement_engine import ScenarioValidation

logger = logging.getLogger(__name__)

# ── Regime → impact description ───────────────────────────────────────────

_REGIME_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "STABLE": {
        "en": "System in stable regime — normal propagation dynamics",
        "ar": "النظام في نظام مستقر — ديناميكيات انتشار عادية",
    },
    "VOLATILE": {
        "en": "System in volatile regime — amplified propagation, compressed delays",
        "ar": "النظام في نظام متقلب — انتشار مضخم، تأخيرات مضغوطة",
    },
    "CRISIS": {
        "en": "System in crisis regime — maximum propagation, cascading failures likely",
        "ar": "النظام في نظام أزمة — انتشار أقصى، الإخفاقات المتتالية محتملة",
    },
    "RECOVERY": {
        "en": "System in recovery regime — declining propagation, stabilization underway",
        "ar": "النظام في نظام تعافي — انتشار متناقص، الاستقرار جارٍ",
    },
}

# ── Decision type → urgency explanation ───────────────────────────────────

_TYPE_EXPLANATIONS: dict[str, dict[str, str]] = {
    "emergency": {
        "en": "Emergency classification — urgency ≥ 0.80, immediate action window",
        "ar": "تصنيف طوارئ — إلحاح ≥ 0.80، نافذة عمل فورية",
    },
    "operational": {
        "en": "Operational classification — standard action window, departmental execution",
        "ar": "تصنيف تشغيلي — نافذة عمل قياسية، تنفيذ إداري",
    },
    "strategic": {
        "en": "Strategic classification — extended timeline, board-level governance",
        "ar": "تصنيف استراتيجي — جدول زمني ممتد، حوكمة على مستوى مجلس الإدارة",
    },
}


@dataclass(frozen=True, slots=True)
class CausalStep:
    """A single step in the causal explanation path."""
    step: int
    event_en: str
    event_ar: str
    mechanism: str
    severity_contribution: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "step": self.step,
            "event_en": self.event_en,
            "event_ar": self.event_ar,
            "mechanism": self.mechanism,
            "severity_contribution": round(self.severity_contribution, 4),
        }


@dataclass(frozen=True, slots=True)
class DecisionExplanation:
    """Complete causal explanation for a decision."""
    decision_id: str
    action_id: str

    # Why this decision exists
    trigger_reason_en: str
    trigger_reason_ar: str

    # Causal propagation path
    causal_path: list[CausalStep] = field(default_factory=list)

    # Propagation summary
    propagation_summary_en: str = ""
    propagation_summary_ar: str = ""

    # Regime context
    regime_context_en: str = ""
    regime_context_ar: str = ""

    # Ranking reason
    ranking_reason_en: str = ""
    ranking_reason_ar: str = ""

    # Rejection reason (if REJECTED)
    rejection_reason_en: str = ""
    rejection_reason_ar: str = ""

    # Scenario classification context
    scenario_classification_en: str = ""
    scenario_classification_ar: str = ""

    # Human-readable narrative
    narrative_en: str = ""
    narrative_ar: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "trigger_reason_en": self.trigger_reason_en,
            "trigger_reason_ar": self.trigger_reason_ar,
            "causal_path": [s.to_dict() for s in self.causal_path],
            "propagation_summary_en": self.propagation_summary_en,
            "propagation_summary_ar": self.propagation_summary_ar,
            "regime_context_en": self.regime_context_en,
            "regime_context_ar": self.regime_context_ar,
            "ranking_reason_en": self.ranking_reason_en,
            "ranking_reason_ar": self.ranking_reason_ar,
            "rejection_reason_en": self.rejection_reason_en,
            "rejection_reason_ar": self.rejection_reason_ar,
            "scenario_classification_en": self.scenario_classification_en,
            "scenario_classification_ar": self.scenario_classification_ar,
            "narrative_en": self.narrative_en,
            "narrative_ar": self.narrative_ar,
        }


def explain_decisions(
    decisions: list[FormattedExecutiveDecision],
    impact_map: ImpactMapResponse,
    validation_results: list[ValidationResult],
    ranked_decisions: list[RankedDecision],
    scenario_validation: ScenarioValidation,
) -> list[DecisionExplanation]:
    """
    Generate causal explanations for every decision.

    Args:
        decisions:           FormattedExecutiveDecision list from Stage 60.
        impact_map:          ImpactMapResponse for propagation context.
        validation_results:  ValidationResult list from ValidationEngine.
        ranked_decisions:    RankedDecision list from Stage 70 RankingEngine.
        scenario_validation: ScenarioValidation from ScenarioEnforcementEngine.

    Returns:
        list[DecisionExplanation] — one per decision, never empty explanations.
    """
    validation_map = {v.action_id: v for v in validation_results}
    rank_map = {r.action_id: r for r in ranked_decisions}

    # Build propagation context
    breached_nodes = [n for n in impact_map.nodes if n.state in ("FAILING", "BREACHED")]
    stressed_nodes = [n for n in impact_map.nodes if n.stress_level > 0.50]

    results: list[DecisionExplanation] = []

    for dec in decisions:
        val = validation_map.get(dec.action_id)
        ranked = rank_map.get(dec.action_id)

        # ── 1. Trigger reason ────────────────────────────────────────────
        trigger_en, trigger_ar = _build_trigger_reason(dec, breached_nodes, stressed_nodes)

        # ── 2. Causal path ───────────────────────────────────────────────
        causal_path = _build_causal_path(dec, impact_map, breached_nodes)

        # ── 3. Propagation summary ───────────────────────────────────────
        prop_en, prop_ar = _build_propagation_summary(impact_map, dec.sector)

        # ── 4. Regime context ────────────────────────────────────────────
        regime_id = impact_map.regime.regime_id
        regime_desc = _REGIME_DESCRIPTIONS.get(regime_id, _REGIME_DESCRIPTIONS["STABLE"])
        regime_en = f"{regime_desc['en']} (amplifier: {impact_map.regime.propagation_amplifier:.2f})"
        regime_ar = f"{regime_desc['ar']} (مضخم: {impact_map.regime.propagation_amplifier:.2f})"

        # ── 5. Ranking reason ────────────────────────────────────────────
        rank_en, rank_ar = _build_ranking_reason(ranked)

        # ── 6. Rejection reason ──────────────────────────────────────────
        reject_en, reject_ar = _build_rejection_reason(val)

        # ── 7. Scenario classification context ───────────────────────────
        sc_en = f"Scenario classified as {scenario_validation.scenario_type}"
        sc_ar = f"السيناريو مصنف كـ {scenario_validation.scenario_type_ar}"
        if scenario_validation.fallback_applied:
            sc_en += f" (via {scenario_validation.fallback_method}, confidence: {scenario_validation.classification_confidence:.0%})"
            sc_ar += f" (عبر {scenario_validation.fallback_method}، ثقة: {scenario_validation.classification_confidence:.0%})"

        # ── 8. Narrative ─────────────────────────────────────────────────
        narrative_en, narrative_ar = _build_narrative(
            dec, trigger_en, trigger_ar, prop_en, prop_ar, regime_en, regime_ar,
            scenario_validation, reject_en,
        )

        results.append(DecisionExplanation(
            decision_id=dec.decision_id,
            action_id=dec.action_id,
            trigger_reason_en=trigger_en,
            trigger_reason_ar=trigger_ar,
            causal_path=causal_path,
            propagation_summary_en=prop_en,
            propagation_summary_ar=prop_ar,
            regime_context_en=regime_en,
            regime_context_ar=regime_ar,
            ranking_reason_en=rank_en,
            ranking_reason_ar=rank_ar,
            rejection_reason_en=reject_en,
            rejection_reason_ar=reject_ar,
            scenario_classification_en=sc_en,
            scenario_classification_ar=sc_ar,
            narrative_en=narrative_en,
            narrative_ar=narrative_ar,
        ))

    logger.info("[ExplainabilityEngine] Generated %d explanations", len(results))
    return results


# ── Builder helpers ───────────────────────────────────────────────────────

def _build_trigger_reason(
    dec: FormattedExecutiveDecision,
    breached: list,
    stressed: list,
) -> tuple[str, str]:
    """Build trigger reason from decision context."""
    type_desc = _TYPE_EXPLANATIONS.get(dec.decision_type, _TYPE_EXPLANATIONS["operational"])

    if breached:
        breach_ids = [n.id for n in breached[:3]]
        en = f"Triggered by node breach ({', '.join(breach_ids)}). {type_desc['en']}. Loss at risk: {dec.loss_avoided_formatted}."
        ar = f"تم التحفيز بسبب اختراق العقد ({', '.join(breach_ids)}). {type_desc['ar']}. الخسارة المعرضة للخطر: {dec.loss_avoided_formatted}."
    elif stressed:
        stress_ids = [n.id for n in stressed[:3]]
        en = f"Triggered by high stress ({', '.join(stress_ids)}). {type_desc['en']}. Urgency: {dec.urgency:.2f}."
        ar = f"تم التحفيز بسبب ضغط عالٍ ({', '.join(stress_ids)}). {type_desc['ar']}. إلحاح: {dec.urgency:.2f}."
    else:
        en = f"Triggered by scenario severity. {type_desc['en']}. Urgency: {dec.urgency:.2f}."
        ar = f"تم التحفيز بسبب شدة السيناريو. {type_desc['ar']}. إلحاح: {dec.urgency:.2f}."

    return en, ar


def _build_causal_path(
    dec: FormattedExecutiveDecision,
    impact_map: ImpactMapResponse,
    breached: list,
) -> list[CausalStep]:
    """Build simplified causal path from propagation events."""
    steps: list[CausalStep] = []

    # Step 1: Scenario onset
    steps.append(CausalStep(
        step=1,
        event_en=f"Scenario onset — initial shock propagation begins",
        event_ar=f"بداية السيناريو — يبدأ انتشار الصدمة الأولية",
        mechanism="initial_shock",
        severity_contribution=0.0,
    ))

    # Step 2: Propagation through edges (use first few propagation events)
    for i, event in enumerate(impact_map.propagation_events[:3]):
        steps.append(CausalStep(
            step=i + 2,
            event_en=f"Propagation: {event.source_id} → {event.target_id} at hour {event.arrival_hour:.1f} ({event.mechanism})",
            event_ar=f"انتشار: {event.source_id} → {event.target_id} في الساعة {event.arrival_hour:.1f} ({event.mechanism_ar or event.mechanism})",
            mechanism=event.mechanism,
            severity_contribution=event.severity_at_arrival,
        ))

    # Step 3: Sector impact
    sector_nodes = [n for n in impact_map.nodes if n.sector == dec.sector and n.stress_level > 0.20]
    if sector_nodes:
        max_stress = max(n.stress_level for n in sector_nodes)
        steps.append(CausalStep(
            step=len(steps) + 1,
            event_en=f"Sector '{dec.sector}' reaches stress {max_stress:.2f} across {len(sector_nodes)} nodes",
            event_ar=f"القطاع '{dec.sector}' يصل ضغط {max_stress:.2f} عبر {len(sector_nodes)} عقد",
            mechanism="sector_accumulation",
            severity_contribution=max_stress,
        ))

    # Step 4: Decision triggered
    steps.append(CausalStep(
        step=len(steps) + 1,
        event_en=f"Decision triggered: {dec.action_en[:80]}",
        event_ar=f"تم تحفيز القرار: {dec.action_ar[:80]}",
        mechanism="decision_trigger",
        severity_contribution=dec.urgency,
    ))

    return steps


def _build_propagation_summary(
    impact_map: ImpactMapResponse,
    sector: str,
) -> tuple[str, str]:
    """Build propagation summary for the decision's sector."""
    total_nodes = len(impact_map.nodes)
    stressed = sum(1 for n in impact_map.nodes if n.stress_level > 0.20)
    breached = sum(1 for n in impact_map.nodes if n.state in ("FAILING", "BREACHED"))
    sector_stressed = sum(1 for n in impact_map.nodes if n.sector == sector and n.stress_level > 0.20)

    en = (
        f"Propagation chain: {stressed}/{total_nodes} nodes stressed, "
        f"{breached} breached. Sector '{sector}': {sector_stressed} nodes affected. "
        f"Amplifier: {impact_map.regime.propagation_amplifier:.2f}."
    )
    ar = (
        f"سلسلة الانتشار: {stressed}/{total_nodes} عقد متأثرة، "
        f"{breached} مخترقة. القطاع '{sector}': {sector_stressed} عقد متأثرة. "
        f"المضخم: {impact_map.regime.propagation_amplifier:.2f}."
    )
    return en, ar


def _build_ranking_reason(ranked: RankedDecision | None) -> tuple[str, str]:
    """Build ranking explanation from factor breakdown."""
    if not ranked:
        return "Ranking data unavailable", "بيانات التصنيف غير متوفرة"

    top_factors = sorted(ranked.factors, key=lambda f: -f.weighted_score)[:3]
    factor_desc = ", ".join(f"{f.label_en} ({f.weighted_score:.3f})" for f in top_factors)
    factor_desc_ar = ", ".join(f"{f.label_ar} ({f.weighted_score:.3f})" for f in top_factors)

    en = f"Ranked #{ranked.calibrated_rank} (score: {ranked.ranking_score:.3f}). Top factors: {factor_desc}."
    ar = f"مرتبة #{ranked.calibrated_rank} (نتيجة: {ranked.ranking_score:.3f}). أعلى العوامل: {factor_desc_ar}."

    if ranked.rank_delta != 0:
        direction = "improved" if ranked.rank_delta > 0 else "declined"
        direction_ar = "تحسن" if ranked.rank_delta > 0 else "تراجع"
        en += f" Rank {direction} by {abs(ranked.rank_delta)} from Stage 60."
        ar += f" الترتيب {direction_ar} بمقدار {abs(ranked.rank_delta)} من المرحلة 60."

    return en, ar


def _build_rejection_reason(val: ValidationResult | None) -> tuple[str, str]:
    """Build rejection reason from validation result."""
    if not val or val.validation_status != "REJECTED":
        return "", ""

    reasons_en = "; ".join(r.get("reason_en", "") for r in val.rejection_reasons)
    reasons_ar = "; ".join(r.get("reason_ar", "") for r in val.rejection_reasons)
    return reasons_en, reasons_ar


def _build_narrative(
    dec: FormattedExecutiveDecision,
    trigger_en: str, trigger_ar: str,
    prop_en: str, prop_ar: str,
    regime_en: str, regime_ar: str,
    sv: ScenarioValidation,
    reject_en: str,
) -> tuple[str, str]:
    """Build human-readable narrative combining all explanation dimensions."""
    en_parts = [
        f"Decision '{dec.action_en[:60]}' for {dec.sector} sector.",
        trigger_en,
        prop_en,
        regime_en,
    ]
    ar_parts = [
        f"القرار '{dec.action_ar[:60]}' لقطاع {dec.sector}.",
        trigger_ar,
        prop_ar,
        regime_ar,
    ]

    if sv.fallback_applied:
        en_parts.append(f"Note: Scenario type resolved via {sv.fallback_method} (confidence: {sv.classification_confidence:.0%}).")
        ar_parts.append(f"ملاحظة: تم حل نوع السيناريو عبر {sv.fallback_method} (ثقة: {sv.classification_confidence:.0%}).")

    if reject_en:
        en_parts.append(f"REJECTED: {reject_en}")
        ar_parts.append(f"مرفوض: {reject_en}")

    return " ".join(en_parts), " ".join(ar_parts)
