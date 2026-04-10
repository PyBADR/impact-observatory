"""
Decision Ranking Engine — multi-factor decision ranking.

Rules:
  - High ROI alone is NOT sufficient for top rank
  - Penalize high risk / low feasibility actions
  - Promote fast-impact decisions in crisis regimes
  - Incorporate action_quality_score from AuditEngine
  - Final rank is deterministic and reproducible

Ranking formula:
  composite = (
      0.20 × urgency_norm
    + 0.20 × impact_norm
    + 0.15 × action_quality_score
    + 0.15 × feasibility_score
    + 0.10 × roi_norm
    + 0.10 × (1 - downside_risk)
    + 0.05 × (1 - regulatory_complexity)
    + 0.05 × reversibility_bonus
  )

Consumed by: Stage 70 pipeline
Input: list[FormattedExecutiveDecision], list[ActionAuditResult], regime_amplifier
Output: list[RankedDecision]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.formatter_engine import FormattedExecutiveDecision
from src.decision_calibration.audit_engine import ActionAuditResult

logger = logging.getLogger(__name__)

# ── Ranking weights ───────────────────────────────────────────────────────

_W_URGENCY:     float = 0.20
_W_IMPACT:      float = 0.20
_W_QUALITY:     float = 0.15
_W_FEASIBILITY: float = 0.15
_W_ROI:         float = 0.10
_W_DOWNSIDE:    float = 0.10
_W_REGULATORY:  float = 0.05
_W_REVERSIBILITY: float = 0.05

# ── Reversibility bonus map ───────────────────────────────────────────────

_REVERSIBILITY_BONUS: dict[str, float] = {
    "reversible":           1.00,
    "partially_reversible": 0.60,
    "irreversible":         0.20,
}

# ── Crisis regime urgency boost ───────────────────────────────────────────

_CRISIS_AMPLIFIER_THRESHOLD: float = 1.3
_CRISIS_URGENCY_BOOST: float = 0.12


@dataclass(frozen=True, slots=True)
class RankingFactor:
    """Individual ranking factor contribution."""
    factor: str
    raw_value: float
    weight: float
    weighted_score: float
    label_en: str
    label_ar: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "factor": self.factor,
            "raw_value": round(self.raw_value, 4),
            "weight": self.weight,
            "weighted_score": round(self.weighted_score, 4),
            "label_en": self.label_en,
            "label_ar": self.label_ar,
        }


@dataclass(frozen=True, slots=True)
class RankedDecision:
    """A decision with multi-factor ranking."""
    decision_id: str
    action_id: str

    # Final rank (1-based, lower is better)
    calibrated_rank: int
    ranking_score: float           # [0-1] composite

    # Previous rank from Stage 60
    previous_rank: int
    rank_delta: int                # previous - calibrated (positive = improved)

    # Factor breakdown
    factors: list[RankingFactor] = field(default_factory=list)

    # Regime adjustment
    crisis_boost_applied: bool = False
    crisis_boost_amount: float = 0.0

    # Notes
    ranking_notes: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "calibrated_rank": self.calibrated_rank,
            "ranking_score": round(self.ranking_score, 4),
            "previous_rank": self.previous_rank,
            "rank_delta": self.rank_delta,
            "factors": [f.to_dict() for f in self.factors],
            "crisis_boost_applied": self.crisis_boost_applied,
            "crisis_boost_amount": round(self.crisis_boost_amount, 4),
            "ranking_notes": self.ranking_notes,
        }


def rank_decisions(
    decisions: list[FormattedExecutiveDecision],
    audit_results: list[ActionAuditResult],
    regime_amplifier: float,
    action_registry_lookup: dict[str, dict[str, Any]],
) -> list[RankedDecision]:
    """
    Rank decisions using multi-factor scoring.

    Args:
        decisions:              FormattedExecutiveDecision list from Stage 60.
        audit_results:          ActionAuditResult list from AuditEngine.
        regime_amplifier:       Current regime propagation amplifier.
        action_registry_lookup: dict[action_id → ActionTemplate dict].

    Returns:
        list[RankedDecision] — sorted by ranking_score descending.
    """
    audit_map: dict[str, ActionAuditResult] = {a.action_id: a for a in audit_results}

    is_crisis = regime_amplifier > _CRISIS_AMPLIFIER_THRESHOLD

    # Compute raw scores for each decision
    scored: list[tuple[FormattedExecutiveDecision, float, list[RankingFactor], list[dict[str, str]], float]] = []

    for dec in decisions:
        audit = audit_map.get(dec.action_id)
        meta = action_registry_lookup.get(dec.action_id, {})

        notes: list[dict[str, str]] = []
        factors: list[RankingFactor] = []

        # ── 1. Urgency ───────────────────────────────────────────────────
        urgency_raw = dec.urgency
        factors.append(RankingFactor(
            factor="urgency", raw_value=urgency_raw, weight=_W_URGENCY,
            weighted_score=urgency_raw * _W_URGENCY,
            label_en="Time pressure", label_ar="ضغط الوقت",
        ))

        # ── 2. Impact ────────────────────────────────────────────────────
        impact_raw = dec.impact
        factors.append(RankingFactor(
            factor="impact", raw_value=impact_raw, weight=_W_IMPACT,
            weighted_score=impact_raw * _W_IMPACT,
            label_en="Loss mitigation impact", label_ar="تأثير تخفيف الخسائر",
        ))

        # ── 3. Action quality (from audit) ────────────────────────────────
        quality_raw = audit.action_quality_score if audit else 0.50
        factors.append(RankingFactor(
            factor="action_quality", raw_value=quality_raw, weight=_W_QUALITY,
            weighted_score=quality_raw * _W_QUALITY,
            label_en="Contextual quality", label_ar="الجودة السياقية",
        ))

        # ── 4. Feasibility ───────────────────────────────────────────────
        feasibility_raw = meta.get("feasibility", 0.70)
        factors.append(RankingFactor(
            factor="feasibility", raw_value=feasibility_raw, weight=_W_FEASIBILITY,
            weighted_score=feasibility_raw * _W_FEASIBILITY,
            label_en="Execution feasibility", label_ar="جدوى التنفيذ",
        ))

        # ── 5. ROI (capped at 1.0) ──────────────────────────────────────
        roi_raw = min(1.0, max(0.0, dec.roi_ratio / 10.0))  # normalize: 10× ROI = perfect
        factors.append(RankingFactor(
            factor="roi", raw_value=roi_raw, weight=_W_ROI,
            weighted_score=roi_raw * _W_ROI,
            label_en="Return on intervention", label_ar="عائد التدخل",
        ))

        # ── 6. Downside risk (inverted — lower risk = higher score) ──────
        downside_inv = 1.0 - dec.downside_risk
        factors.append(RankingFactor(
            factor="downside_safety", raw_value=downside_inv, weight=_W_DOWNSIDE,
            weighted_score=downside_inv * _W_DOWNSIDE,
            label_en="Downside safety", label_ar="أمان الجانب السلبي",
        ))

        # ── 7. Regulatory complexity (inverted) ──────────────────────────
        reg_risk = meta.get("regulatory_risk", 0.50)
        reg_inv = 1.0 - reg_risk
        factors.append(RankingFactor(
            factor="regulatory_simplicity", raw_value=reg_inv, weight=_W_REGULATORY,
            weighted_score=reg_inv * _W_REGULATORY,
            label_en="Regulatory simplicity", label_ar="بساطة التنظيم",
        ))

        # ── 8. Reversibility ─────────────────────────────────────────────
        rev_bonus = _REVERSIBILITY_BONUS.get(dec.reversibility, 0.60)
        factors.append(RankingFactor(
            factor="reversibility", raw_value=rev_bonus, weight=_W_REVERSIBILITY,
            weighted_score=rev_bonus * _W_REVERSIBILITY,
            label_en="Reversibility", label_ar="قابلية العكس",
        ))

        # ── Composite ────────────────────────────────────────────────────
        composite = sum(f.weighted_score for f in factors)

        # ── Crisis regime boost ──────────────────────────────────────────
        crisis_boost = 0.0
        if is_crisis and dec.decision_type == "emergency":
            crisis_boost = _CRISIS_URGENCY_BOOST
            composite = min(1.0, composite + crisis_boost)
            notes.append({
                "type": "CRISIS_BOOST",
                "message_en": f"Emergency action boosted +{crisis_boost:.2f} in crisis regime",
                "message_ar": f"تم تعزيز الإجراء الطارئ +{crisis_boost:.2f} في نظام الأزمات",
                "severity": "info",
            })

        # ── Category error penalty ───────────────────────────────────────
        if audit and audit.category_error_flag:
            penalty = composite * 0.40
            composite -= penalty
            notes.append({
                "type": "CATEGORY_PENALTY",
                "message_en": f"Ranking penalized by {penalty:.3f} due to category error",
                "message_ar": f"تم تخفيض التصنيف بمقدار {penalty:.3f} بسبب خطأ التصنيف",
                "severity": "warning",
            })

        scored.append((dec, composite, factors, notes, crisis_boost))

    # Sort by composite score descending
    scored.sort(key=lambda x: -x[1])

    # Build ranked results
    results: list[RankedDecision] = []
    for rank_idx, (dec, composite, factors, notes, crisis_boost) in enumerate(scored):
        calibrated_rank = rank_idx + 1
        rank_delta = dec.rank - calibrated_rank  # positive = moved up

        if rank_delta != 0:
            direction = "improved" if rank_delta > 0 else "declined"
            direction_ar = "تحسن" if rank_delta > 0 else "تراجع"
            notes.append({
                "type": "RANK_CHANGE",
                "message_en": f"Rank {direction} from #{dec.rank} to #{calibrated_rank}",
                "message_ar": f"الترتيب {direction_ar} من #{dec.rank} إلى #{calibrated_rank}",
                "severity": "info",
            })

        results.append(RankedDecision(
            decision_id=dec.decision_id,
            action_id=dec.action_id,
            calibrated_rank=calibrated_rank,
            ranking_score=composite,
            previous_rank=dec.rank,
            rank_delta=rank_delta,
            factors=factors,
            crisis_boost_applied=crisis_boost > 0,
            crisis_boost_amount=crisis_boost,
            ranking_notes=notes,
        ))

    logger.info(
        "[RankingEngine] Ranked %d decisions, crisis=%s",
        len(results), is_crisis,
    )
    return results
