"""
Outcome Calibration Engine — expected vs actual outcome comparison.

Closes the feedback loop between predicted outcomes (Stage 60) and
realized outcomes (post-execution tracking).

Since we operate pre-execution (no actual outcomes yet), this engine:
  1. Establishes calibration baselines from current predictions
  2. Computes calibration confidence based on prediction consistency
  3. Identifies where historical calibration adjustments would apply
  4. Generates adjustment factors for future confidence tuning

Rules:
  - If prediction spread is wide → lower calibration confidence
  - If action_quality_score is low → expect higher calibration error
  - Consistent predictions across similar actions → increase confidence
  - Store calibration metadata for post-execution comparison

Consumed by: Stage 70 pipeline
Input: list[FormattedExecutiveDecision], list[ActionAuditResult], list[RankedDecision]
Output: list[CalibrationResult]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.formatter_engine import FormattedExecutiveDecision
from src.decision_calibration.audit_engine import ActionAuditResult
from src.decision_calibration.ranking_engine import RankedDecision

logger = logging.getLogger(__name__)

# ── Calibration thresholds ────────────────────────────────────────────────

_HIGH_CONFIDENCE_THRESHOLD = 0.75    # above this → high calibration confidence
_LOW_CONFIDENCE_THRESHOLD = 0.45     # below this → low calibration confidence
_QUALITY_PENALTY_THRESHOLD = 0.50    # action_quality below this → penalize calibration
_SPREAD_PENALTY_FACTOR = 0.30        # how much prediction spread penalizes confidence


@dataclass(frozen=True, slots=True)
class CalibrationBaseline:
    """Pre-execution calibration baseline for a single prediction."""
    metric: str
    predicted_value: float
    unit: str
    confidence_band_low: float
    confidence_band_high: float
    measurement_window_hours: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "predicted_value": round(self.predicted_value, 4),
            "unit": self.unit,
            "confidence_band_low": round(self.confidence_band_low, 4),
            "confidence_band_high": round(self.confidence_band_high, 4),
            "measurement_window_hours": round(self.measurement_window_hours, 1),
        }


@dataclass(frozen=True, slots=True)
class CalibrationResult:
    """Calibration assessment for a single decision."""
    decision_id: str
    action_id: str

    # Calibration confidence [0-1] — how trustworthy are the predictions?
    calibration_confidence: float

    # Adjustment factor [0.5-1.5] — multiply future confidence by this
    adjustment_factor: float

    # Expected calibration error [0-1] — predicted mismatch magnitude
    expected_calibration_error: float

    # Classification
    calibration_grade: str          # "A" | "B" | "C" | "D"
    calibration_grade_ar: str

    # Baselines for post-execution comparison
    baselines: list[CalibrationBaseline] = field(default_factory=list)

    # Notes
    calibration_notes: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "calibration_confidence": round(self.calibration_confidence, 4),
            "adjustment_factor": round(self.adjustment_factor, 4),
            "expected_calibration_error": round(self.expected_calibration_error, 4),
            "calibration_grade": self.calibration_grade,
            "calibration_grade_ar": self.calibration_grade_ar,
            "baselines": [b.to_dict() for b in self.baselines],
            "calibration_notes": self.calibration_notes,
        }


def calibrate_outcomes(
    decisions: list[FormattedExecutiveDecision],
    audit_results: list[ActionAuditResult],
    ranked_results: list[RankedDecision],
) -> list[CalibrationResult]:
    """
    Compute calibration baselines and expected calibration quality.

    Args:
        decisions:      FormattedExecutiveDecision list from Stage 60.
        audit_results:  ActionAuditResult list from AuditEngine.
        ranked_results: RankedDecision list from RankingEngine.

    Returns:
        list[CalibrationResult] — one per decision.
    """
    audit_map: dict[str, ActionAuditResult] = {a.action_id: a for a in audit_results}
    rank_map: dict[str, RankedDecision] = {r.action_id: r for r in ranked_results}

    results: list[CalibrationResult] = []

    for dec in decisions:
        audit = audit_map.get(dec.action_id)
        ranked = rank_map.get(dec.action_id)

        notes: list[dict[str, str]] = []

        # ── 1. Compute calibration confidence ────────────────────────────
        cal_confidence = _compute_calibration_confidence(dec, audit, ranked, notes)

        # ── 2. Compute expected calibration error ────────────────────────
        expected_error = _compute_expected_error(dec, audit, cal_confidence)

        # ── 3. Compute adjustment factor ─────────────────────────────────
        adjustment = _compute_adjustment_factor(cal_confidence, expected_error)

        # ── 4. Grade assignment ──────────────────────────────────────────
        grade, grade_ar = _assign_grade(cal_confidence)

        # ── 5. Build calibration baselines ───────────────────────────────
        baselines = _build_baselines(dec)

        results.append(CalibrationResult(
            decision_id=dec.decision_id,
            action_id=dec.action_id,
            calibration_confidence=cal_confidence,
            adjustment_factor=adjustment,
            expected_calibration_error=expected_error,
            calibration_grade=grade,
            calibration_grade_ar=grade_ar,
            baselines=baselines,
            calibration_notes=notes,
        ))

    logger.info(
        "[CalibrationEngine] Calibrated %d decisions: grades=%s",
        len(results),
        {r.calibration_grade: sum(1 for x in results if x.calibration_grade == r.calibration_grade) for r in results},
    )
    return results


# ── Computation helpers ───────────────────────────────────────────────────

def _compute_calibration_confidence(
    dec: FormattedExecutiveDecision,
    audit: ActionAuditResult | None,
    ranked: RankedDecision | None,
    notes: list[dict[str, str]],
) -> float:
    """
    Calibration confidence = f(confidence_composite, action_quality, ranking_score).

    Higher when: high model confidence + high action quality + high ranking
    Lower when: any dimension is weak.
    """
    base = dec.confidence_composite  # from Stage 60

    # Action quality amplifier/dampener
    if audit:
        quality = audit.action_quality_score
        if quality < _QUALITY_PENALTY_THRESHOLD:
            penalty = (1.0 - quality / _QUALITY_PENALTY_THRESHOLD) * _SPREAD_PENALTY_FACTOR
            base -= penalty
            notes.append({
                "type": "LOW_QUALITY_PENALTY",
                "message_en": f"Calibration penalized by {penalty:.3f} due to low action quality ({quality:.2f})",
                "message_ar": f"تم تخفيض المعايرة بمقدار {penalty:.3f} بسبب جودة الإجراء المنخفضة ({quality:.2f})",
                "severity": "warning",
            })
        else:
            # High quality slightly boosts confidence
            base += quality * 0.10

    # Ranking consistency check
    if ranked:
        # Large rank changes indicate instability → lower confidence
        if abs(ranked.rank_delta) >= 2:
            base -= 0.08
            notes.append({
                "type": "RANK_INSTABILITY",
                "message_en": f"Rank changed by {abs(ranked.rank_delta)} positions — prediction may be unstable",
                "message_ar": f"تغير الترتيب بمقدار {abs(ranked.rank_delta)} مراكز — قد يكون التنبؤ غير مستقر",
                "severity": "info",
            })

    # Model dependency consideration
    if dec.model_dependency == "high":
        base -= 0.10
        notes.append({
            "type": "HIGH_MODEL_DEPENDENCY",
            "message_en": "High model dependency reduces calibration confidence",
            "message_ar": "الاعتماد العالي على النموذج يقلل من ثقة المعايرة",
            "severity": "warning",
        })

    return max(0.0, min(1.0, base))


def _compute_expected_error(
    dec: FormattedExecutiveDecision,
    audit: ActionAuditResult | None,
    cal_confidence: float,
) -> float:
    """Expected error = inverse of calibration confidence, modulated by quality."""
    base_error = 1.0 - cal_confidence

    # Category errors dramatically increase expected error
    if audit and audit.category_error_flag:
        base_error = min(1.0, base_error + 0.30)

    # External validation requirement suggests higher uncertainty
    if dec.external_validation_required:
        base_error = min(1.0, base_error + 0.10)

    return max(0.0, min(1.0, base_error))


def _compute_adjustment_factor(cal_confidence: float, expected_error: float) -> float:
    """
    Adjustment factor for future confidence tuning.

    Range: [0.50, 1.50]
    - High confidence + low error → factor near 1.0 (no adjustment needed)
    - Low confidence + high error → factor < 1.0 (reduce future confidence)
    - Very high confidence → factor slightly > 1.0 (can increase future confidence)
    """
    if cal_confidence >= _HIGH_CONFIDENCE_THRESHOLD and expected_error < 0.25:
        # Well-calibrated — slight boost
        return min(1.50, 1.0 + (cal_confidence - _HIGH_CONFIDENCE_THRESHOLD) * 0.5)

    if cal_confidence < _LOW_CONFIDENCE_THRESHOLD:
        # Poorly calibrated — reduce
        return max(0.50, 0.70 + cal_confidence * 0.30)

    # Moderate — proportional adjustment
    return max(0.50, min(1.50, 0.80 + cal_confidence * 0.30))


def _assign_grade(cal_confidence: float) -> tuple[str, str]:
    """Assign calibration grade A/B/C/D."""
    if cal_confidence >= 0.80:
        return "A", "أ"
    if cal_confidence >= 0.60:
        return "B", "ب"
    if cal_confidence >= 0.40:
        return "C", "ج"
    return "D", "د"


def _build_baselines(dec: FormattedExecutiveDecision) -> list[CalibrationBaseline]:
    """Build pre-execution calibration baselines."""
    baselines: list[CalibrationBaseline] = []

    # Loss reduction baseline
    if dec.expected_loss_reduction_pct > 0:
        predicted = dec.expected_loss_reduction_pct
        # Confidence band: ±20% of prediction
        band = predicted * 0.20
        baselines.append(CalibrationBaseline(
            metric="loss_reduction_pct",
            predicted_value=predicted,
            unit="percent",
            confidence_band_low=max(0.0, predicted - band),
            confidence_band_high=min(100.0, predicted + band),
            measurement_window_hours=dec.time_window_hours * 3,
        ))

    # ROI baseline
    if dec.roi_ratio > 0:
        predicted_roi = dec.roi_ratio
        roi_band = predicted_roi * 0.25
        baselines.append(CalibrationBaseline(
            metric="roi_ratio",
            predicted_value=predicted_roi,
            unit="ratio",
            confidence_band_low=max(0.0, predicted_roi - roi_band),
            confidence_band_high=predicted_roi + roi_band,
            measurement_window_hours=dec.time_window_hours * 4,
        ))

    # Impact baseline
    baselines.append(CalibrationBaseline(
        metric="stress_reduction",
        predicted_value=dec.impact,
        unit="score",
        confidence_band_low=max(0.0, dec.impact - 0.15),
        confidence_band_high=min(1.0, dec.impact + 0.10),
        measurement_window_hours=dec.time_window_hours * 2,
    ))

    return baselines
