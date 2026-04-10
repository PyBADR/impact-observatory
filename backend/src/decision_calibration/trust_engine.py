"""
Decision Trust Engine — composite institutional trust scoring.

TrustScore = weighted combination of:
  - action_quality_score (from AuditEngine)
  - ranking_score (from RankingEngine)
  - confidence_composite (from Stage 60 ConfidenceEngine)
  - calibration_confidence (from CalibrationEngine)
  - data_quality dimension (from Stage 60 confidence dimensions)

Trust levels:
  - LOW   (< 0.40) → require human validation before execution
  - MEDIUM (0.40-0.70) → conditional approval, monitoring required
  - HIGH  (≥ 0.70) → auto-executable with standard audit trail

Rules:
  - Category error → force LOW trust
  - High model dependency → cap at MEDIUM
  - External validation required → cap at MEDIUM
  - Cross-border coordination → minimum MEDIUM (never auto-execute)

Consumed by: Stage 70 pipeline (final engine)
Input: all Stage 70 engine outputs
Output: list[TrustResult]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.formatter_engine import FormattedExecutiveDecision
from src.decision_calibration.audit_engine import ActionAuditResult
from src.decision_calibration.ranking_engine import RankedDecision
from src.decision_calibration.calibration_engine import CalibrationResult
from src.decision_calibration.authority_engine import AuthorityAssignment

logger = logging.getLogger(__name__)

# ── Trust weights ─────────────────────────────────────────────────────────

_W_ACTION_QUALITY:  float = 0.25
_W_RANKING:         float = 0.20
_W_CONFIDENCE:      float = 0.25
_W_CALIBRATION:     float = 0.20
_W_DATA_QUALITY:    float = 0.10

# ── Trust level thresholds ────────────────────────────────────────────────

_HIGH_TRUST_THRESHOLD:   float = 0.70
_MEDIUM_TRUST_THRESHOLD: float = 0.40


@dataclass(frozen=True, slots=True)
class TrustDimension:
    """A single dimension contributing to trust score."""
    dimension: str
    score: float
    weight: float
    weighted_score: float
    label_en: str
    label_ar: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension,
            "score": round(self.score, 4),
            "weight": self.weight,
            "weighted_score": round(self.weighted_score, 4),
            "label_en": self.label_en,
            "label_ar": self.label_ar,
        }


@dataclass(frozen=True, slots=True)
class TrustResult:
    """Institutional trust assessment for a decision."""
    decision_id: str
    action_id: str

    # Trust score [0-1]
    trust_score: float

    # Trust level classification
    trust_level: str              # "LOW" | "MEDIUM" | "HIGH"
    trust_level_ar: str

    # Execution recommendation
    execution_mode: str           # "BLOCKED" | "HUMAN_REQUIRED" | "CONDITIONAL" | "AUTO_EXECUTABLE"
    execution_mode_ar: str
    execution_rationale_en: str
    execution_rationale_ar: str

    # Dimension breakdown
    dimensions: list[TrustDimension] = field(default_factory=list)

    # Constraints applied
    constraints_applied: list[dict[str, str]] = field(default_factory=list)

    # Notes
    trust_notes: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "trust_score": round(self.trust_score, 4),
            "trust_level": self.trust_level,
            "trust_level_ar": self.trust_level_ar,
            "execution_mode": self.execution_mode,
            "execution_mode_ar": self.execution_mode_ar,
            "execution_rationale_en": self.execution_rationale_en,
            "execution_rationale_ar": self.execution_rationale_ar,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "constraints_applied": self.constraints_applied,
            "trust_notes": self.trust_notes,
        }


def compute_trust_scores(
    decisions: list[FormattedExecutiveDecision],
    audit_results: list[ActionAuditResult],
    ranked_results: list[RankedDecision],
    calibration_results: list[CalibrationResult],
    authority_results: list[AuthorityAssignment],
) -> list[TrustResult]:
    """
    Compute institutional trust scores for each decision.

    Args:
        decisions:            FormattedExecutiveDecision list from Stage 60.
        audit_results:        ActionAuditResult list from AuditEngine.
        ranked_results:       RankedDecision list from RankingEngine.
        calibration_results:  CalibrationResult list from CalibrationEngine.
        authority_results:    AuthorityAssignment list from AuthorityEngine.

    Returns:
        list[TrustResult] — one per decision.
    """
    audit_map = {a.action_id: a for a in audit_results}
    rank_map = {r.action_id: r for r in ranked_results}
    cal_map = {c.action_id: c for c in calibration_results}
    auth_map = {a.action_id: a for a in authority_results}

    results: list[TrustResult] = []

    for dec in decisions:
        audit = audit_map.get(dec.action_id)
        ranked = rank_map.get(dec.action_id)
        cal = cal_map.get(dec.action_id)
        auth = auth_map.get(dec.action_id)

        notes: list[dict[str, str]] = []
        constraints: list[dict[str, str]] = []

        # ── Compute dimensions ───────────────────────────────────────────
        dims: list[TrustDimension] = []

        # 1. Action quality
        aq_score = audit.action_quality_score if audit else 0.50
        dims.append(TrustDimension(
            dimension="action_quality", score=aq_score, weight=_W_ACTION_QUALITY,
            weighted_score=aq_score * _W_ACTION_QUALITY,
            label_en="Action quality", label_ar="جودة الإجراء",
        ))

        # 2. Ranking score
        rk_score = ranked.ranking_score if ranked else 0.50
        dims.append(TrustDimension(
            dimension="ranking", score=rk_score, weight=_W_RANKING,
            weighted_score=rk_score * _W_RANKING,
            label_en="Ranking strength", label_ar="قوة التصنيف",
        ))

        # 3. Confidence composite
        cf_score = dec.confidence_composite
        dims.append(TrustDimension(
            dimension="confidence", score=cf_score, weight=_W_CONFIDENCE,
            weighted_score=cf_score * _W_CONFIDENCE,
            label_en="Model confidence", label_ar="ثقة النموذج",
        ))

        # 4. Calibration confidence
        cl_score = cal.calibration_confidence if cal else 0.50
        dims.append(TrustDimension(
            dimension="calibration", score=cl_score, weight=_W_CALIBRATION,
            weighted_score=cl_score * _W_CALIBRATION,
            label_en="Calibration quality", label_ar="جودة المعايرة",
        ))

        # 5. Data quality (extract from confidence dimensions if available)
        dq_score = _extract_data_quality(dec)
        dims.append(TrustDimension(
            dimension="data_quality", score=dq_score, weight=_W_DATA_QUALITY,
            weighted_score=dq_score * _W_DATA_QUALITY,
            label_en="Data quality", label_ar="جودة البيانات",
        ))

        # ── Raw composite ────────────────────────────────────────────────
        raw_trust = sum(d.weighted_score for d in dims)

        # ── Apply hard constraints ───────────────────────────────────────

        # Category error → force LOW
        if audit and audit.category_error_flag:
            raw_trust = min(raw_trust, 0.30)
            constraints.append({
                "constraint": "CATEGORY_ERROR",
                "effect_en": "Trust capped at 0.30 due to category error",
                "effect_ar": "تم تحديد الثقة عند 0.30 بسبب خطأ التصنيف",
            })

        # High model dependency → cap at MEDIUM
        if dec.model_dependency == "high":
            raw_trust = min(raw_trust, 0.65)
            constraints.append({
                "constraint": "HIGH_MODEL_DEPENDENCY",
                "effect_en": "Trust capped at 0.65 due to high model dependency",
                "effect_ar": "تم تحديد الثقة عند 0.65 بسبب الاعتماد العالي على النموذج",
            })

        # External validation required → cap at MEDIUM
        if dec.external_validation_required:
            raw_trust = min(raw_trust, 0.60)
            constraints.append({
                "constraint": "EXTERNAL_VALIDATION_REQUIRED",
                "effect_en": "Trust capped at 0.60 — external validation pending",
                "effect_ar": "تم تحديد الثقة عند 0.60 — التحقق الخارجي معلق",
            })

        # Cross-border → never auto-execute
        cross_border = auth.requires_cross_border_coordination if auth else False
        if cross_border:
            raw_trust = min(raw_trust, 0.68)
            constraints.append({
                "constraint": "CROSS_BORDER_COORDINATION",
                "effect_en": "Trust capped at 0.68 — cross-border coordination required",
                "effect_ar": "تم تحديد الثقة عند 0.68 — يتطلب تنسيقاً عابراً للحدود",
            })

        raw_trust = max(0.0, min(1.0, raw_trust))

        # ── Trust level classification ───────────────────────────────────
        trust_level, trust_level_ar = _classify_trust(raw_trust)

        # ── Execution mode ───────────────────────────────────────────────
        exec_mode, exec_mode_ar, rationale_en, rationale_ar = _determine_execution_mode(
            raw_trust, trust_level, audit, dec, cross_border,
        )

        results.append(TrustResult(
            decision_id=dec.decision_id,
            action_id=dec.action_id,
            trust_score=raw_trust,
            trust_level=trust_level,
            trust_level_ar=trust_level_ar,
            execution_mode=exec_mode,
            execution_mode_ar=exec_mode_ar,
            execution_rationale_en=rationale_en,
            execution_rationale_ar=rationale_ar,
            dimensions=dims,
            constraints_applied=constraints,
            trust_notes=notes,
        ))

    logger.info(
        "[TrustEngine] Computed trust for %d decisions: %s",
        len(results),
        {r.trust_level: sum(1 for x in results if x.trust_level == r.trust_level) for r in results},
    )
    return results


# ── Helpers ───────────────────────────────────────────────────────────────

def _extract_data_quality(dec: FormattedExecutiveDecision) -> float:
    """Extract data_quality score from confidence dimensions."""
    for dim in dec.confidence_dimensions:
        if isinstance(dim, dict) and dim.get("dimension") == "data_quality":
            return dim.get("score", 0.50)
    return 0.50


def _classify_trust(score: float) -> tuple[str, str]:
    """Classify trust level."""
    if score >= _HIGH_TRUST_THRESHOLD:
        return "HIGH", "عالي"
    if score >= _MEDIUM_TRUST_THRESHOLD:
        return "MEDIUM", "متوسط"
    return "LOW", "منخفض"


def _determine_execution_mode(
    trust_score: float,
    trust_level: str,
    audit: ActionAuditResult | None,
    dec: FormattedExecutiveDecision,
    cross_border: bool,
) -> tuple[str, str, str, str]:
    """Determine execution mode and rationale."""

    # Category error → BLOCKED
    if audit and audit.category_error_flag:
        return (
            "BLOCKED", "محظور",
            "Decision blocked — action does not match scenario type",
            "القرار محظور — الإجراء لا يتطابق مع نوع السيناريو",
        )

    # LOW trust → HUMAN_REQUIRED
    if trust_level == "LOW":
        return (
            "HUMAN_REQUIRED", "يتطلب تدخل بشري",
            f"Low trust ({trust_score:.2f}) — human validation required before execution",
            f"ثقة منخفضة ({trust_score:.2f}) — يتطلب التحقق البشري قبل التنفيذ",
        )

    # MEDIUM trust or cross-border → CONDITIONAL
    if trust_level == "MEDIUM" or cross_border:
        conditions = []
        conditions_ar = []
        if dec.approval_required:
            conditions.append("pending approval")
            conditions_ar.append("بانتظار الموافقة")
        if cross_border:
            conditions.append("cross-border coordination")
            conditions_ar.append("تنسيق عابر للحدود")
        if dec.external_validation_required:
            conditions.append("external validation")
            conditions_ar.append("تحقق خارجي")
        if not conditions:
            conditions.append("monitoring required")
            conditions_ar.append("مراقبة مطلوبة")

        return (
            "CONDITIONAL", "مشروط",
            f"Conditional execution — {', '.join(conditions)}",
            f"تنفيذ مشروط — {', '.join(conditions_ar)}",
        )

    # HIGH trust → AUTO_EXECUTABLE
    return (
        "AUTO_EXECUTABLE", "قابل للتنفيذ التلقائي",
        f"High trust ({trust_score:.2f}) — standard audit trail sufficient",
        f"ثقة عالية ({trust_score:.2f}) — مسار التدقيق القياسي كافٍ",
    )
