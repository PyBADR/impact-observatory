"""
Executive Decision Output — top 3 decisions ONLY.

No dashboards. No visualizations. Only decisions.
Each decision is causal, executable, and testable.

Output: List[ExecutiveDecision] — exactly top 3 (or fewer if not enough data).
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from src.decision_intelligence.trigger_engine import GraphDecisionTrigger
from src.decision_intelligence.breakpoint_engine import Breakpoint
from src.decision_intelligence.action_simulation_engine import ActionSimResult
from src.decision_intelligence.counterfactual_engine import CounterfactualResult
from src.decision_intelligence.roi_engine import DecisionROI

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ExecutiveDecision:
    """A single executive-level decision recommendation."""
    decision_id: str
    rank: int                       # 1, 2, or 3

    # What to do
    action_id: str
    action_en: str
    action_ar: str
    sector: str
    owner: str

    # Why now
    urgency: float                  # [0-1]
    trigger_type: str               # from GraphDecisionTrigger
    trigger_reason_en: str
    trigger_reason_ar: str

    # Expected impact
    impact_score: float             # [0-1] composite
    loss_avoided_usd: float
    loss_avoided_formatted: str
    nodes_protected: int
    breaches_prevented: int

    # Confidence and risk
    confidence: float               # [0-1]
    downside_risk: float            # [0-1] what happens if action fails
    roi_ratio: float                # net benefit / cost

    # Timing
    time_window_hours: float        # hours before action becomes less effective

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "rank": self.rank,
            "action_id": self.action_id,
            "action_en": self.action_en,
            "action_ar": self.action_ar,
            "sector": self.sector,
            "owner": self.owner,
            "urgency": round(self.urgency, 4),
            "trigger_type": self.trigger_type,
            "trigger_reason_en": self.trigger_reason_en,
            "trigger_reason_ar": self.trigger_reason_ar,
            "impact_score": round(self.impact_score, 4),
            "loss_avoided_usd": round(self.loss_avoided_usd, 2),
            "loss_avoided_formatted": self.loss_avoided_formatted,
            "nodes_protected": self.nodes_protected,
            "breaches_prevented": self.breaches_prevented,
            "confidence": round(self.confidence, 4),
            "downside_risk": round(self.downside_risk, 4),
            "roi_ratio": round(self.roi_ratio, 4),
            "time_window_hours": round(self.time_window_hours, 1),
        }


def build_executive_decisions(
    triggers: list[GraphDecisionTrigger],
    breakpoints: list[Breakpoint],
    sim_results: list[ActionSimResult],
    counterfactual: CounterfactualResult,
    rois: list[DecisionROI],
    action_registry_lookup: dict[str, dict[str, Any]],
) -> list[ExecutiveDecision]:
    """
    Synthesize all decision intelligence into top 3 executive decisions.

    Ranking formula:
      score = 0.3×urgency + 0.25×impact + 0.2×roi_norm + 0.15×confidence + 0.1×(1-downside)

    Args:
        triggers:                 From trigger_engine.
        breakpoints:              From breakpoint_engine.
        sim_results:              From action_simulation_engine.
        counterfactual:           From counterfactual_engine.
        rois:                     From roi_engine.
        action_registry_lookup:   dict[action_id → ActionTemplate] for metadata.

    Returns:
        List of top 3 ExecutiveDecision objects.
    """
    if not sim_results:
        logger.warning("[ExecutiveOutput] No sim results — returning empty decisions")
        return []

    # Build lookup maps
    roi_map: dict[str, DecisionROI] = {r.action_id: r for r in rois}
    trigger_map: dict[str, GraphDecisionTrigger] = {}
    for t in triggers:
        # Map trigger to action by sector match
        trigger_map.setdefault(t.sector, t)
        trigger_map.setdefault(t.trigger_type, t)

    # Score each action
    candidates: list[tuple[float, ActionSimResult]] = []

    for sim in sim_results:
        roi = roi_map.get(sim.action_id)
        action_meta = action_registry_lookup.get(sim.action_id, {})

        # Urgency: from trigger or default
        urgency = 0.5
        sector = action_meta.get("sector", "")
        if sector in trigger_map:
            urgency = trigger_map[sector].urgency
        elif triggers:
            urgency = triggers[0].urgency

        # Impact: propagation_reduction normalized
        impact = min(1.0, sim.propagation_reduction * 3.0)  # scale up — typical values are 0.01-0.3

        # ROI normalized
        roi_norm = 0.5
        if roi and roi.roi_ratio != float("inf"):
            roi_norm = min(1.0, max(0, roi.roi_ratio) / 5.0)  # normalize to [0,1] with 5x being max
        elif roi and roi.roi_ratio == float("inf"):
            roi_norm = 1.0

        # Confidence from counterfactual
        confidence = counterfactual.confidence

        # Downside risk: inverse of feasibility + regime severity
        feasibility = action_meta.get("feasibility", 0.7)
        reg_risk = action_meta.get("regulatory_risk", 0.5)
        downside = min(1.0, (1.0 - feasibility) * 0.5 + reg_risk * 0.5)

        # Composite score
        score = (
            0.30 * urgency +
            0.25 * impact +
            0.20 * roi_norm +
            0.15 * confidence +
            0.10 * (1.0 - downside)
        )

        candidates.append((score, sim))

    # Sort by score descending, take top 3
    candidates.sort(key=lambda c: -c[0])
    top_3 = candidates[:3]

    decisions: list[ExecutiveDecision] = []

    for rank, (score, sim) in enumerate(top_3, 1):
        roi = roi_map.get(sim.action_id)
        action_meta = action_registry_lookup.get(sim.action_id, {})

        # Find best matching trigger
        sector = action_meta.get("sector", "")
        trigger = trigger_map.get(sector) or (triggers[0] if triggers else None)

        # Time window from trigger or default
        time_window = trigger.time_to_action_hours if trigger else 24.0

        # Downside risk
        feasibility = action_meta.get("feasibility", 0.7)
        reg_risk = action_meta.get("regulatory_risk", 0.5)
        downside = min(1.0, (1.0 - feasibility) * 0.5 + reg_risk * 0.5)

        decisions.append(ExecutiveDecision(
            decision_id=f"EXD-{rank:03d}",
            rank=rank,
            action_id=sim.action_id,
            action_en=action_meta.get("action_en", sim.action_label),
            action_ar=action_meta.get("action_ar", ""),
            sector=action_meta.get("sector", ""),
            owner=action_meta.get("owner", ""),
            urgency=trigger.urgency if trigger else 0.5,
            trigger_type=trigger.trigger_type if trigger else "STRESS_CRITICAL",
            trigger_reason_en=trigger.reason_en if trigger else "System under stress",
            trigger_reason_ar=trigger.reason_ar if trigger else "النظام تحت ضغط",
            impact_score=score,
            loss_avoided_usd=roi.loss_avoided_usd if roi else 0.0,
            loss_avoided_formatted=_format_usd(roi.loss_avoided_usd if roi else 0.0),
            nodes_protected=sim.nodes_protected,
            breaches_prevented=sim.failure_prevention_count,
            confidence=counterfactual.confidence,
            downside_risk=downside,
            roi_ratio=roi.roi_ratio if roi and roi.roi_ratio != float("inf") else 999.0,
            time_window_hours=time_window,
        ))

    logger.info("[ExecutiveOutput] Built %d executive decisions", len(decisions))
    return decisions


def _format_usd(v: float) -> str:
    if v >= 1_000_000_000:
        return f"${v / 1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"${v / 1_000_000:.1f}M"
    if v >= 1_000:
        return f"${v / 1_000:.0f}K"
    return f"${v:.0f}"
