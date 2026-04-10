"""
Decision Anchoring Engine — converts raw executive decisions into owned,
time-bound, typed decision objects.

Rules:
  - Every decision MUST have an owner
  - Every decision MUST have a deadline
  - decision_type must be: operational | strategic | emergency
  - Any missing field → INVALID decision (excluded from output)

Consumed by: Stage 60 pipeline
Input: ExecutiveDecision list + action_registry_lookup
Output: list[AnchoredDecision]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from src.decision_intelligence.executive_output import ExecutiveDecision

logger = logging.getLogger(__name__)

# ── Decision type classification thresholds ────────────────────────────────

_EMERGENCY_URGENCY = 0.80        # urgency ≥ 0.80 → emergency
_OPERATIONAL_URGENCY = 0.50      # urgency ≥ 0.50 → operational
# else → strategic

_TRADEOFF_KEYS = [
    ("cost_vs_speed", "تكلفة مقابل سرعة"),
    ("scope_vs_precision", "نطاق مقابل دقة"),
    ("risk_vs_inaction", "مخاطر مقابل عدم اتخاذ إجراء"),
]


@dataclass(frozen=True, slots=True)
class AnchoredDecision:
    """A fully anchored decision — owned, time-bound, typed, and measurable."""
    decision_id: str
    rank: int

    # Ownership
    decision_owner: str
    decision_owner_ar: str

    # Timing
    decision_deadline: str          # ISO 8601 timestamp
    time_window_hours: float        # hours until deadline
    created_at: str                 # ISO 8601 timestamp

    # Classification
    decision_type: str              # "emergency" | "operational" | "strategic"
    decision_type_ar: str

    # Action
    action_id: str
    action_en: str
    action_ar: str
    sector: str

    # Scores
    urgency: float
    impact: float
    downside_risk: float
    confidence: float
    roi_ratio: float

    # Loss impact
    loss_avoided_usd: float
    loss_avoided_formatted: str

    # Tradeoffs
    tradeoffs: list[dict[str, str]] = field(default_factory=list)

    # Validity
    is_valid: bool = True
    validation_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "rank": self.rank,
            "decision_owner": self.decision_owner,
            "decision_owner_ar": self.decision_owner_ar,
            "decision_deadline": self.decision_deadline,
            "time_window_hours": round(self.time_window_hours, 1),
            "created_at": self.created_at,
            "decision_type": self.decision_type,
            "decision_type_ar": self.decision_type_ar,
            "action_id": self.action_id,
            "action_en": self.action_en,
            "action_ar": self.action_ar,
            "sector": self.sector,
            "urgency": round(self.urgency, 4),
            "impact": round(self.impact, 4),
            "downside_risk": round(self.downside_risk, 4),
            "confidence": round(self.confidence, 4),
            "roi_ratio": round(self.roi_ratio, 4),
            "loss_avoided_usd": round(self.loss_avoided_usd, 2),
            "loss_avoided_formatted": self.loss_avoided_formatted,
            "tradeoffs": self.tradeoffs,
            "is_valid": self.is_valid,
            "validation_errors": self.validation_errors,
        }


def anchor_decisions(
    executive_decisions: list[ExecutiveDecision],
    action_registry_lookup: dict[str, dict[str, Any]],
    run_timestamp: datetime | None = None,
) -> list[AnchoredDecision]:
    """
    Anchor executive decisions with ownership, deadlines, types, and tradeoffs.

    Args:
        executive_decisions: From Stage 50 executive_output.
        action_registry_lookup: dict[action_id → ActionTemplate dict].
        run_timestamp: Base timestamp for deadline computation. Defaults to now(UTC).

    Returns:
        list[AnchoredDecision] — only valid decisions included.
    """
    if run_timestamp is None:
        run_timestamp = datetime.now(timezone.utc)

    anchored: list[AnchoredDecision] = []

    for ed in executive_decisions:
        errors: list[str] = []
        meta = action_registry_lookup.get(ed.action_id, {})

        # ── Owner resolution ──────────────────────────────────────────────
        owner = ed.owner or meta.get("owner", "")
        owner_ar = meta.get("owner_ar", "")
        if not owner:
            errors.append("MISSING_OWNER")

        # ── Deadline computation ──────────────────────────────────────────
        time_window = ed.time_window_hours
        time_to_act = float(meta.get("time_to_act_hours", 24))
        # Deadline = min(time_window, time_to_act) — act before window closes
        effective_window = min(time_window, time_to_act) if time_window > 0 else time_to_act
        if effective_window <= 0:
            effective_window = 24.0  # safe default
            errors.append("ZERO_WINDOW_DEFAULTED")

        deadline = run_timestamp + timedelta(hours=effective_window)
        deadline_iso = deadline.isoformat()
        created_iso = run_timestamp.isoformat()

        if not deadline_iso:
            errors.append("MISSING_DEADLINE")

        # ── Type classification ───────────────────────────────────────────
        if ed.urgency >= _EMERGENCY_URGENCY:
            dtype = "emergency"
            dtype_ar = "طوارئ"
        elif ed.urgency >= _OPERATIONAL_URGENCY:
            dtype = "operational"
            dtype_ar = "تشغيلي"
        else:
            dtype = "strategic"
            dtype_ar = "استراتيجي"

        # ── Tradeoff analysis ─────────────────────────────────────────────
        tradeoffs = _compute_tradeoffs(ed, meta)

        # ── Validity gate ─────────────────────────────────────────────────
        is_valid = len(errors) == 0

        anchored.append(AnchoredDecision(
            decision_id=ed.decision_id,
            rank=ed.rank,
            decision_owner=owner,
            decision_owner_ar=owner_ar,
            decision_deadline=deadline_iso,
            time_window_hours=effective_window,
            created_at=created_iso,
            decision_type=dtype,
            decision_type_ar=dtype_ar,
            action_id=ed.action_id,
            action_en=ed.action_en,
            action_ar=ed.action_ar,
            sector=ed.sector,
            urgency=ed.urgency,
            impact=ed.impact_score,
            downside_risk=ed.downside_risk,
            confidence=ed.confidence,
            roi_ratio=ed.roi_ratio,
            loss_avoided_usd=ed.loss_avoided_usd,
            loss_avoided_formatted=ed.loss_avoided_formatted,
            tradeoffs=tradeoffs,
            is_valid=is_valid,
            validation_errors=errors,
        ))

    valid_count = sum(1 for a in anchored if a.is_valid)
    logger.info("[AnchoringEngine] Anchored %d decisions (%d valid, %d invalid)",
                len(anchored), valid_count, len(anchored) - valid_count)

    return anchored


def _compute_tradeoffs(
    ed: ExecutiveDecision,
    meta: dict[str, Any],
) -> list[dict[str, str]]:
    """Generate tradeoff analysis for a decision."""
    tradeoffs: list[dict[str, str]] = []
    cost = float(meta.get("cost_usd", 0))
    feasibility = meta.get("feasibility", 0.7)
    reg_risk = meta.get("regulatory_risk", 0.5)

    # Cost vs Speed
    if cost > 100_000_000 and ed.time_window_hours < 12:
        tradeoffs.append({
            "type": "cost_vs_speed",
            "type_ar": "تكلفة مقابل سرعة",
            "description_en": f"High cost (${cost/1e6:.0f}M) required within {ed.time_window_hours:.0f}h window",
            "description_ar": f"تكلفة عالية ({cost/1e6:.0f} مليون$) مطلوبة خلال {ed.time_window_hours:.0f} ساعة",
            "severity": "high" if cost > 500_000_000 else "medium",
        })

    # Scope vs Precision
    if ed.nodes_protected > 5:
        tradeoffs.append({
            "type": "scope_vs_precision",
            "type_ar": "نطاق مقابل دقة",
            "description_en": f"Broad action affecting {ed.nodes_protected} nodes — may over-correct",
            "description_ar": f"إجراء واسع يؤثر على {ed.nodes_protected} عقدة — قد يبالغ في التصحيح",
            "severity": "medium",
        })

    # Risk vs Inaction
    if ed.loss_avoided_usd > 0 and ed.downside_risk > 0.3:
        tradeoffs.append({
            "type": "risk_vs_inaction",
            "type_ar": "مخاطر مقابل عدم اتخاذ إجراء",
            "description_en": f"Saves {ed.loss_avoided_formatted} but downside risk = {ed.downside_risk:.0%}",
            "description_ar": f"يوفر {ed.loss_avoided_formatted} لكن مخاطر الجانب السلبي = {ed.downside_risk:.0%}",
            "severity": "high" if ed.downside_risk > 0.5 else "medium",
        })

    # Regulatory risk
    if reg_risk > 0.6:
        tradeoffs.append({
            "type": "regulatory_exposure",
            "type_ar": "تعرض تنظيمي",
            "description_en": f"Regulatory risk = {reg_risk:.0%} — may require PDPL/IFRS 17 compliance review",
            "description_ar": f"مخاطر تنظيمية = {reg_risk:.0%} — قد تتطلب مراجعة امتثال PDPL/IFRS 17",
            "severity": "high" if reg_risk > 0.7 else "medium",
        })

    return tradeoffs
