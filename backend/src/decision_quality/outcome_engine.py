"""
Decision Outcome Engine — builds expected outcome framework for each decision.

Rules:
  - Must define expected vs actual comparison framework
  - Must generate measurable KPIs
  - Must provide learning signals for future decision confidence
  - Must feed into system memory (outcome → future calibration)

This engine does NOT execute decisions or measure actual outcomes —
it builds the measurement framework that will be used post-execution.

Consumed by: Stage 60 pipeline
Input: list[AnchoredDecision] + sim_results + counterfactual
Output: list[DecisionOutcome]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.anchoring_engine import AnchoredDecision
from src.decision_intelligence.action_simulation_engine import ActionSimResult
from src.decision_intelligence.counterfactual_engine import CounterfactualResult

logger = logging.getLogger(__name__)

# ── Sector-specific KPI mappings ───────────────────────────────────────────

_SECTOR_KPIS: dict[str, dict[str, str]] = {
    "maritime": {
        "kpi_en": "Port throughput recovery (TEU/day) within action window",
        "kpi_ar": "استعادة إنتاجية الميناء (TEU/يوم) ضمن نافذة العمل",
    },
    "energy": {
        "kpi_en": "Energy supply stabilization (barrels/day) within 72h",
        "kpi_ar": "استقرار إمدادات الطاقة (برميل/يوم) خلال 72 ساعة",
    },
    "banking": {
        "kpi_en": "Interbank liquidity ratio restoration within action window",
        "kpi_ar": "استعادة نسبة السيولة بين البنوك ضمن نافذة العمل",
    },
    "insurance": {
        "kpi_en": "Claims reserve adequacy ratio within 30-day horizon",
        "kpi_ar": "نسبة كفاية احتياطي المطالبات خلال أفق 30 يوماً",
    },
    "fintech": {
        "kpi_en": "Payment processing uptime restoration to 99.9%",
        "kpi_ar": "استعادة وقت تشغيل معالجة المدفوعات إلى 99.9%",
    },
    "logistics": {
        "kpi_en": "Freight routing efficiency recovery to pre-disruption baseline",
        "kpi_ar": "استعادة كفاءة توجيه الشحن إلى خط الأساس قبل التعطل",
    },
    "infrastructure": {
        "kpi_en": "Critical infrastructure uptime restoration within 48h",
        "kpi_ar": "استعادة وقت تشغيل البنية التحتية الحرجة خلال 48 ساعة",
    },
    "government": {
        "kpi_en": "Regulatory response issuance within coordination window",
        "kpi_ar": "إصدار الاستجابة التنظيمية ضمن نافذة التنسيق",
    },
}

_DEFAULT_KPI = {
    "kpi_en": "Risk score reduction to target threshold within action window",
    "kpi_ar": "خفض درجة المخاطر إلى عتبة الهدف ضمن نافذة العمل",
}


@dataclass(frozen=True, slots=True)
class ExpectedOutcome:
    """What we expect to happen if the action is executed."""
    metric_en: str
    metric_ar: str
    expected_value: float
    unit: str
    measurement_window_hours: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric_en": self.metric_en,
            "metric_ar": self.metric_ar,
            "expected_value": round(self.expected_value, 4),
            "unit": self.unit,
            "measurement_window_hours": round(self.measurement_window_hours, 1),
        }


@dataclass(frozen=True, slots=True)
class LearningSignal:
    """What the system should learn from this decision's outcome."""
    signal_type: str             # "CALIBRATION" | "MODEL_UPDATE" | "THRESHOLD_ADJUSTMENT"
    description_en: str
    description_ar: str
    target_component: str        # which engine/model to update

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "description_en": self.description_en,
            "description_ar": self.description_ar,
            "target_component": self.target_component,
        }


@dataclass(frozen=True, slots=True)
class DecisionOutcome:
    """Full outcome measurement framework for a decision."""
    decision_id: str
    action_id: str

    # Expected outcomes
    expected_loss_reduction_pct: float    # % loss reduction expected
    expected_loss_reduction_usd: float
    expected_stress_reduction: float      # absolute stress points

    # Measurable KPI
    measurable_kpi_en: str
    measurable_kpi_ar: str

    # Expected vs actual framework
    expected_outcomes: list[ExpectedOutcome] = field(default_factory=list)

    # Learning signals
    learning_signals: list[LearningSignal] = field(default_factory=list)

    # Measurement metadata
    measurement_window_hours: float = 72.0
    review_deadline: str = ""            # ISO 8601 — when to compare expected vs actual

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "expected_loss_reduction_pct": round(self.expected_loss_reduction_pct, 2),
            "expected_loss_reduction_usd": round(self.expected_loss_reduction_usd, 2),
            "expected_stress_reduction": round(self.expected_stress_reduction, 4),
            "measurable_kpi_en": self.measurable_kpi_en,
            "measurable_kpi_ar": self.measurable_kpi_ar,
            "expected_outcomes": [e.to_dict() for e in self.expected_outcomes],
            "learning_signals": [ls.to_dict() for ls in self.learning_signals],
            "measurement_window_hours": round(self.measurement_window_hours, 1),
            "review_deadline": self.review_deadline,
        }


def build_outcome_expectations(
    anchored_decisions: list[AnchoredDecision],
    sim_results: list[ActionSimResult],
    counterfactual: CounterfactualResult | None,
) -> list[DecisionOutcome]:
    """
    Build outcome measurement framework for each anchored decision.

    Args:
        anchored_decisions: From anchoring_engine.
        sim_results:        From action_simulation_engine.
        counterfactual:     From counterfactual_engine.

    Returns:
        list[DecisionOutcome] — one per valid anchored decision.
    """
    sim_map: dict[str, ActionSimResult] = {s.action_id: s for s in sim_results}
    baseline_loss = counterfactual.baseline_loss_usd if counterfactual else 0.0

    outcomes: list[DecisionOutcome] = []

    for ad in anchored_decisions:
        if not ad.is_valid:
            continue

        sim = sim_map.get(ad.action_id)

        # ── Expected loss reduction ────────────────────────────────────────
        if sim and baseline_loss > 0:
            loss_reduction_usd = max(0, baseline_loss - sim.mitigated_loss_usd)
            loss_reduction_pct = (loss_reduction_usd / baseline_loss) * 100
        else:
            loss_reduction_usd = ad.loss_avoided_usd
            loss_reduction_pct = 0.0

        # ── Expected stress reduction ──────────────────────────────────────
        stress_reduction = sim.stress_reduction_total if sim else 0.0

        # ── Sector KPI ─────────────────────────────────────────────────────
        sector_kpi = _SECTOR_KPIS.get(ad.sector, _DEFAULT_KPI)

        # ── Measurement window ─────────────────────────────────────────────
        measurement_window = max(24.0, ad.time_window_hours * 3)  # 3× action window

        # ── Expected outcomes ──────────────────────────────────────────────
        expected_outcomes = _build_expected_outcomes(ad, sim, loss_reduction_pct, measurement_window)

        # ── Learning signals ───────────────────────────────────────────────
        learning_signals = _build_learning_signals(ad, sim)

        # ── Review deadline ────────────────────────────────────────────────
        # Review at measurement_window after decision deadline
        from datetime import datetime, timedelta, timezone
        try:
            dl = datetime.fromisoformat(ad.decision_deadline)
            review = dl + timedelta(hours=measurement_window)
            review_iso = review.isoformat()
        except (ValueError, TypeError):
            review_iso = ""

        outcomes.append(DecisionOutcome(
            decision_id=ad.decision_id,
            action_id=ad.action_id,
            expected_loss_reduction_pct=loss_reduction_pct,
            expected_loss_reduction_usd=loss_reduction_usd,
            expected_stress_reduction=stress_reduction,
            measurable_kpi_en=sector_kpi["kpi_en"],
            measurable_kpi_ar=sector_kpi["kpi_ar"],
            expected_outcomes=expected_outcomes,
            learning_signals=learning_signals,
            measurement_window_hours=measurement_window,
            review_deadline=review_iso,
        ))

    logger.info("[OutcomeEngine] Built outcome frameworks for %d decisions", len(outcomes))
    return outcomes


def _build_expected_outcomes(
    ad: AnchoredDecision,
    sim: ActionSimResult | None,
    loss_pct: float,
    window: float,
) -> list[ExpectedOutcome]:
    """Build specific measurable expected outcomes."""
    outcomes: list[ExpectedOutcome] = []

    # Loss reduction outcome
    outcomes.append(ExpectedOutcome(
        metric_en="Loss reduction from baseline",
        metric_ar="خفض الخسائر من خط الأساس",
        expected_value=loss_pct,
        unit="percent",
        measurement_window_hours=window,
    ))

    # Stress reduction outcome
    if sim and sim.stress_reduction_total > 0:
        outcomes.append(ExpectedOutcome(
            metric_en="Aggregate stress reduction across affected nodes",
            metric_ar="خفض الضغط الإجمالي عبر العقد المتأثرة",
            expected_value=sim.stress_reduction_total,
            unit="stress_points",
            measurement_window_hours=window,
        ))

    # Propagation containment
    if sim and sim.propagation_reduction > 0:
        outcomes.append(ExpectedOutcome(
            metric_en="Propagation containment rate",
            metric_ar="معدل احتواء الانتشار",
            expected_value=sim.propagation_reduction * 100,
            unit="percent",
            measurement_window_hours=ad.time_window_hours,
        ))

    # Node protection
    if sim and sim.nodes_protected > 0:
        outcomes.append(ExpectedOutcome(
            metric_en="Infrastructure nodes protected from breach",
            metric_ar="عقد البنية التحتية المحمية من الاختراق",
            expected_value=float(sim.nodes_protected),
            unit="count",
            measurement_window_hours=window,
        ))

    return outcomes


def _build_learning_signals(
    ad: AnchoredDecision,
    sim: ActionSimResult | None,
) -> list[LearningSignal]:
    """Build learning signals for system memory."""
    signals: list[LearningSignal] = []

    # Always: calibrate the simulation model
    signals.append(LearningSignal(
        signal_type="CALIBRATION",
        description_en=f"Compare actual loss reduction vs expected {ad.loss_avoided_formatted} — "
                       f"adjust propagation model coefficients if delta > 20%",
        description_ar=f"مقارنة خفض الخسائر الفعلي مقابل المتوقع {ad.loss_avoided_formatted} — "
                       f"تعديل معاملات نموذج الانتشار إذا تجاوز الفرق 20%",
        target_component="action_simulation_engine",
    ))

    # If high model dependency: flag for threshold adjustment
    if ad.confidence < 0.7:
        signals.append(LearningSignal(
            signal_type="THRESHOLD_ADJUSTMENT",
            description_en="Low confidence decision — review trigger thresholds and "
                          "breakpoint scoring weights post-outcome",
            description_ar="قرار منخفض الثقة — مراجعة عتبات المحفزات و"
                          "أوزان تسجيل نقاط الانقطاع بعد النتيجة",
            target_component="trigger_engine",
        ))

    # If emergency: model update signal
    if ad.decision_type == "emergency":
        signals.append(LearningSignal(
            signal_type="MODEL_UPDATE",
            description_en="Emergency decision executed — update regime transition matrix "
                          "with actual escalation velocity data",
            description_ar="تم تنفيذ قرار طوارئ — تحديث مصفوفة انتقال النظام "
                          "ببيانات سرعة التصعيد الفعلية",
            target_component="regime_engine",
        ))

    return signals
