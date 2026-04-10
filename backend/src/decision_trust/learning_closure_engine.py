"""
Learning Closure Engine — feedback loop for system adaptation.

Converts Stage 70 calibration outputs into learning signals that would
adjust future pipeline behavior. Since we operate in simulation (no real
post-execution outcomes), this engine:

  1. Computes PREDICTED calibration errors from current signals
  2. Generates adjustment recommendations for action selection, ranking, and confidence
  3. Identifies decisions that would benefit from recalibration
  4. Tracks learning velocity (how fast the system should adapt)

Learning rules:
  - High calibration error → downgrade future confidence for similar actions
  - Consistent accuracy → upgrade confidence for the action type
  - Category errors → block action for scenario type in future
  - Ranking instability → reduce ranking weight volatility

Consumed by: Stage 80 pipeline
Input: decisions + calibration_results + audit_results + ranked_decisions
Output: list[LearningUpdate]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.formatter_engine import FormattedExecutiveDecision
from src.decision_calibration.calibration_engine import CalibrationResult
from src.decision_calibration.audit_engine import ActionAuditResult
from src.decision_calibration.ranking_engine import RankedDecision

logger = logging.getLogger(__name__)

# ── Learning thresholds ───────────────────────────────────────────────────

_HIGH_ERROR_THRESHOLD: float = 0.40       # calibration error above this → downgrade
_LOW_ERROR_THRESHOLD: float = 0.15        # below this → upgrade
_CATEGORY_ERROR_PENALTY: float = -0.50    # confidence reduction for category errors
_RANK_INSTABILITY_THRESHOLD: int = 2      # rank change above this → flag instability


@dataclass(frozen=True, slots=True)
class LearningUpdate:
    """Learning signal for a single decision."""
    decision_id: str
    action_id: str

    # Predicted calibration error
    calibration_error: float        # [0-1] expected mismatch

    # Adjustment recommendations
    action_adjustment: str          # "MAINTAIN" | "UPGRADE" | "DOWNGRADE" | "BLOCK"
    action_adjustment_ar: str
    ranking_adjustment: float       # delta to apply to ranking weight [-0.2, +0.2]
    confidence_adjustment: float    # delta to apply to confidence [-0.3, +0.1]

    # Learning velocity
    learning_velocity: str          # "FAST" | "MODERATE" | "SLOW"
    learning_velocity_ar: str

    # Specific recommendations
    recommendations: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "calibration_error": round(self.calibration_error, 4),
            "action_adjustment": self.action_adjustment,
            "action_adjustment_ar": self.action_adjustment_ar,
            "ranking_adjustment": round(self.ranking_adjustment, 4),
            "confidence_adjustment": round(self.confidence_adjustment, 4),
            "learning_velocity": self.learning_velocity,
            "learning_velocity_ar": self.learning_velocity_ar,
            "recommendations": self.recommendations,
        }


def compute_learning_updates(
    decisions: list[FormattedExecutiveDecision],
    calibration_results: list[CalibrationResult],
    audit_results: list[ActionAuditResult],
    ranked_decisions: list[RankedDecision],
) -> list[LearningUpdate]:
    """
    Compute learning updates from calibration and audit signals.

    Args:
        decisions:            FormattedExecutiveDecision list from Stage 60.
        calibration_results:  CalibrationResult list from Stage 70.
        audit_results:        ActionAuditResult list from Stage 70.
        ranked_decisions:     RankedDecision list from Stage 70.

    Returns:
        list[LearningUpdate] — one per decision with adjustment recommendations.
    """
    cal_map = {c.action_id: c for c in calibration_results}
    audit_map = {a.action_id: a for a in audit_results}
    rank_map = {r.action_id: r for r in ranked_decisions}

    results: list[LearningUpdate] = []

    for dec in decisions:
        cal = cal_map.get(dec.action_id)
        audit = audit_map.get(dec.action_id)
        ranked = rank_map.get(dec.action_id)

        recs: list[dict[str, str]] = []

        # ── Calibration error ────────────────────────────────────────────
        cal_error = cal.expected_calibration_error if cal else 0.30

        # ── Action adjustment ────────────────────────────────────────────
        action_adj, action_adj_ar = _compute_action_adjustment(
            cal_error, audit, recs,
        )

        # ── Ranking adjustment ───────────────────────────────────────────
        ranking_adj = _compute_ranking_adjustment(ranked, cal_error, recs)

        # ── Confidence adjustment ────────────────────────────────────────
        confidence_adj = _compute_confidence_adjustment(
            cal_error, audit, dec, recs,
        )

        # ── Learning velocity ────────────────────────────────────────────
        velocity, velocity_ar = _compute_learning_velocity(
            cal_error, audit, ranked,
        )

        results.append(LearningUpdate(
            decision_id=dec.decision_id,
            action_id=dec.action_id,
            calibration_error=cal_error,
            action_adjustment=action_adj,
            action_adjustment_ar=action_adj_ar,
            ranking_adjustment=ranking_adj,
            confidence_adjustment=confidence_adj,
            learning_velocity=velocity,
            learning_velocity_ar=velocity_ar,
            recommendations=recs,
        ))

    upgrades = sum(1 for r in results if r.action_adjustment == "UPGRADE")
    downgrades = sum(1 for r in results if r.action_adjustment == "DOWNGRADE")
    blocks = sum(1 for r in results if r.action_adjustment == "BLOCK")
    logger.info(
        "[LearningClosureEngine] %d updates: %d UPGRADE, %d MAINTAIN, %d DOWNGRADE, %d BLOCK",
        len(results), upgrades, len(results) - upgrades - downgrades - blocks, downgrades, blocks,
    )
    return results


# ── Computation helpers ───────────────────────────────────────────────────

def _compute_action_adjustment(
    cal_error: float,
    audit: ActionAuditResult | None,
    recs: list[dict[str, str]],
) -> tuple[str, str]:
    """Determine action adjustment recommendation."""
    # Category error → BLOCK
    if audit and audit.category_error_flag:
        recs.append({
            "type": "ACTION_BLOCK",
            "message_en": "Block this action for this scenario type — category error detected",
            "message_ar": "حظر هذا الإجراء لنوع هذا السيناريو — تم اكتشاف خطأ تصنيف",
            "priority": "critical",
        })
        return "BLOCK", "حظر"

    # High error → DOWNGRADE
    if cal_error >= _HIGH_ERROR_THRESHOLD:
        recs.append({
            "type": "ACTION_DOWNGRADE",
            "message_en": f"Downgrade action confidence — calibration error ({cal_error:.2f}) exceeds threshold",
            "message_ar": f"تخفيض ثقة الإجراء — خطأ المعايرة ({cal_error:.2f}) يتجاوز الحد",
            "priority": "high",
        })
        return "DOWNGRADE", "تخفيض"

    # Low error → UPGRADE
    if cal_error <= _LOW_ERROR_THRESHOLD:
        recs.append({
            "type": "ACTION_UPGRADE",
            "message_en": f"Upgrade action confidence — calibration error ({cal_error:.2f}) is low and consistent",
            "message_ar": f"ترقية ثقة الإجراء — خطأ المعايرة ({cal_error:.2f}) منخفض ومتسق",
            "priority": "low",
        })
        return "UPGRADE", "ترقية"

    return "MAINTAIN", "الحفاظ"


def _compute_ranking_adjustment(
    ranked: RankedDecision | None,
    cal_error: float,
    recs: list[dict[str, str]],
) -> float:
    """Compute ranking weight adjustment."""
    adj = 0.0

    if ranked and abs(ranked.rank_delta) >= _RANK_INSTABILITY_THRESHOLD:
        # Reduce ranking volatility
        adj -= 0.05
        recs.append({
            "type": "RANKING_STABILIZE",
            "message_en": f"Reduce ranking volatility — rank shifted by {abs(ranked.rank_delta)} positions",
            "message_ar": f"تقليل تقلب التصنيف — تغير الترتيب بمقدار {abs(ranked.rank_delta)} مراكز",
            "priority": "medium",
        })

    if cal_error >= _HIGH_ERROR_THRESHOLD:
        adj -= 0.10
    elif cal_error <= _LOW_ERROR_THRESHOLD:
        adj += 0.05

    return max(-0.20, min(0.20, adj))


def _compute_confidence_adjustment(
    cal_error: float,
    audit: ActionAuditResult | None,
    dec: FormattedExecutiveDecision,
    recs: list[dict[str, str]],
) -> float:
    """Compute confidence delta."""
    adj = 0.0

    # Category error → large downgrade
    if audit and audit.category_error_flag:
        adj += _CATEGORY_ERROR_PENALTY
        return max(-0.30, adj)

    # High calibration error → moderate downgrade
    if cal_error >= _HIGH_ERROR_THRESHOLD:
        adj -= 0.15
        recs.append({
            "type": "CONFIDENCE_REDUCE",
            "message_en": "Reduce confidence for future similar decisions",
            "message_ar": "تقليل الثقة للقرارات المشابهة المستقبلية",
            "priority": "high",
        })

    # Low error → small upgrade
    elif cal_error <= _LOW_ERROR_THRESHOLD:
        adj += 0.05
        recs.append({
            "type": "CONFIDENCE_BOOST",
            "message_en": "Confidence well-calibrated — small boost for future runs",
            "message_ar": "الثقة معايرة بشكل جيد — تعزيز بسيط للتشغيلات المستقبلية",
            "priority": "low",
        })

    # High model dependency warning
    if dec.model_dependency == "high":
        adj -= 0.05

    return max(-0.30, min(0.10, adj))


def _compute_learning_velocity(
    cal_error: float,
    audit: ActionAuditResult | None,
    ranked: RankedDecision | None,
) -> tuple[str, str]:
    """Determine how fast the system should adapt."""
    # Category error → FAST adaptation
    if audit and audit.category_error_flag:
        return "FAST", "سريع"

    # High error or high instability → FAST
    if cal_error >= _HIGH_ERROR_THRESHOLD:
        return "FAST", "سريع"

    # Moderate error + some instability → MODERATE
    if cal_error >= _LOW_ERROR_THRESHOLD:
        if ranked and abs(ranked.rank_delta) >= 1:
            return "MODERATE", "متوسط"

    # Low error, stable → SLOW (system is well-calibrated)
    return "SLOW", "بطيء"
