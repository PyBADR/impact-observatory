"""
Action Pathway Engine — structures decisions into time-layered pathways.

Pathway types:
  IMMEDIATE    (0–24h)   — execute now, no trigger condition
  CONDITIONAL  (trigger)  — execute when trigger condition met
  STRATEGIC    (long-term) — execute as part of ongoing program

Each action has: priority_level, trigger_condition, expected_impact,
                 cost_estimate, reversibility.

Consumed by: Stage 60 pipeline
Input: list[AnchoredDecision] + action_registry_lookup + triggers
Output: list[ActionPathway]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Literal

from src.decision_quality.anchoring_engine import AnchoredDecision
from src.decision_intelligence.trigger_engine import GraphDecisionTrigger
from src.decision_intelligence.breakpoint_engine import Breakpoint

logger = logging.getLogger(__name__)

PathwayType = Literal["IMMEDIATE", "CONDITIONAL", "STRATEGIC"]

# ── Pathway classification thresholds ──────────────────────────────────────

_IMMEDIATE_WINDOW_HOURS = 24.0       # time_window ≤ 24h → IMMEDIATE
_CONDITIONAL_URGENCY = 0.60          # urgency ≥ 0.60 but window > 24h → CONDITIONAL
# else → STRATEGIC


@dataclass(frozen=True, slots=True)
class ActionDetail:
    """Detailed action within a pathway."""
    action_id: str
    priority_level: int              # 1 (highest) to 5 (lowest)
    trigger_condition: str           # what must be true to execute
    trigger_condition_ar: str
    expected_impact: float           # [0-1] normalized expected effect
    cost_estimate_usd: float
    cost_formatted: str
    reversibility: str               # "reversible" | "partially_reversible" | "irreversible"
    reversibility_ar: str
    owner: str
    owner_ar: str
    time_to_act_hours: float
    sector: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "priority_level": self.priority_level,
            "trigger_condition": self.trigger_condition,
            "trigger_condition_ar": self.trigger_condition_ar,
            "expected_impact": round(self.expected_impact, 4),
            "cost_estimate_usd": round(self.cost_estimate_usd, 2),
            "cost_formatted": self.cost_formatted,
            "reversibility": self.reversibility,
            "reversibility_ar": self.reversibility_ar,
            "owner": self.owner,
            "owner_ar": self.owner_ar,
            "time_to_act_hours": round(self.time_to_act_hours, 1),
            "sector": self.sector,
        }


@dataclass(frozen=True, slots=True)
class ActionPathway:
    """A structured pathway grouping related actions by time horizon."""
    pathway_id: str
    pathway_type: PathwayType
    pathway_label_en: str
    pathway_label_ar: str
    time_horizon_hours: float
    actions: list[ActionDetail] = field(default_factory=list)

    @property
    def action_count(self) -> int:
        return len(self.actions)

    @property
    def total_cost_usd(self) -> float:
        return sum(a.cost_estimate_usd for a in self.actions)

    def to_dict(self) -> dict[str, Any]:
        return {
            "pathway_id": self.pathway_id,
            "pathway_type": self.pathway_type,
            "pathway_label_en": self.pathway_label_en,
            "pathway_label_ar": self.pathway_label_ar,
            "time_horizon_hours": round(self.time_horizon_hours, 1),
            "action_count": self.action_count,
            "total_cost_usd": round(self.total_cost_usd, 2),
            "actions": [a.to_dict() for a in self.actions],
        }


# ── Reversibility classification ───────────────────────────────────────────

_REVERSIBLE_SECTORS = {"logistics", "maritime"}
_IRREVERSIBLE_SECTORS = {"energy", "infrastructure"}


def build_action_pathways(
    anchored_decisions: list[AnchoredDecision],
    action_registry_lookup: dict[str, dict[str, Any]],
    triggers: list[GraphDecisionTrigger],
    breakpoints: list[Breakpoint],
) -> list[ActionPathway]:
    """
    Structure anchored decisions into time-layered pathways.

    Args:
        anchored_decisions:      From anchoring_engine.
        action_registry_lookup:  dict[action_id → ActionTemplate dict].
        triggers:                From trigger_engine (for condition generation).
        breakpoints:             From breakpoint_engine (for condition enrichment).

    Returns:
        list[ActionPathway] — IMMEDIATE, CONDITIONAL, STRATEGIC.
    """
    immediate_actions: list[ActionDetail] = []
    conditional_actions: list[ActionDetail] = []
    strategic_actions: list[ActionDetail] = []

    # Build trigger lookup for condition generation
    trigger_by_sector: dict[str, GraphDecisionTrigger] = {}
    for t in triggers:
        trigger_by_sector.setdefault(t.sector, t)

    # Build breakpoint lookup for edge conditions
    bp_by_sector: dict[str, Breakpoint] = {}
    for bp in breakpoints:
        bp_by_sector.setdefault(bp.edge_type, bp)

    for ad in anchored_decisions:
        if not ad.is_valid:
            continue

        meta = action_registry_lookup.get(ad.action_id, {})
        cost = float(meta.get("cost_usd", 0))
        time_to_act = float(meta.get("time_to_act_hours", 24))

        # Classify pathway
        pathway_type = _classify_pathway(ad)

        # Generate trigger condition
        trigger_condition, trigger_condition_ar = _generate_trigger_condition(
            ad, pathway_type, trigger_by_sector, bp_by_sector,
        )

        # Classify reversibility
        reversibility, reversibility_ar = _classify_reversibility(ad.sector, cost)

        # Priority: rank maps directly
        priority_level = min(5, ad.rank)

        detail = ActionDetail(
            action_id=ad.action_id,
            priority_level=priority_level,
            trigger_condition=trigger_condition,
            trigger_condition_ar=trigger_condition_ar,
            expected_impact=ad.impact,
            cost_estimate_usd=cost,
            cost_formatted=_format_usd(cost),
            reversibility=reversibility,
            reversibility_ar=reversibility_ar,
            owner=ad.decision_owner,
            owner_ar=ad.decision_owner_ar,
            time_to_act_hours=time_to_act,
            sector=ad.sector,
        )

        if pathway_type == "IMMEDIATE":
            immediate_actions.append(detail)
        elif pathway_type == "CONDITIONAL":
            conditional_actions.append(detail)
        else:
            strategic_actions.append(detail)

    # Build pathways (only include non-empty)
    pathways: list[ActionPathway] = []

    if immediate_actions:
        pathways.append(ActionPathway(
            pathway_id="PWY-IMMEDIATE",
            pathway_type="IMMEDIATE",
            pathway_label_en="Immediate Response (0–24h)",
            pathway_label_ar="استجابة فورية (0-24 ساعة)",
            time_horizon_hours=24.0,
            actions=sorted(immediate_actions, key=lambda a: a.priority_level),
        ))

    if conditional_actions:
        pathways.append(ActionPathway(
            pathway_id="PWY-CONDITIONAL",
            pathway_type="CONDITIONAL",
            pathway_label_en="Conditional Response (trigger-based)",
            pathway_label_ar="استجابة مشروطة (على أساس المحفز)",
            time_horizon_hours=72.0,
            actions=sorted(conditional_actions, key=lambda a: a.priority_level),
        ))

    if strategic_actions:
        pathways.append(ActionPathway(
            pathway_id="PWY-STRATEGIC",
            pathway_type="STRATEGIC",
            pathway_label_en="Strategic Response (long-term)",
            pathway_label_ar="استجابة استراتيجية (طويلة المدى)",
            time_horizon_hours=168.0,
            actions=sorted(strategic_actions, key=lambda a: a.priority_level),
        ))

    logger.info(
        "[PathwayEngine] Built %d pathways: IMMEDIATE=%d, CONDITIONAL=%d, STRATEGIC=%d",
        len(pathways), len(immediate_actions), len(conditional_actions), len(strategic_actions),
    )
    return pathways


def _classify_pathway(ad: AnchoredDecision) -> PathwayType:
    """Classify a decision into a pathway type based on timing and urgency."""
    if ad.time_window_hours <= _IMMEDIATE_WINDOW_HOURS:
        return "IMMEDIATE"
    if ad.urgency >= _CONDITIONAL_URGENCY:
        return "CONDITIONAL"
    return "STRATEGIC"


def _generate_trigger_condition(
    ad: AnchoredDecision,
    pathway_type: PathwayType,
    trigger_by_sector: dict[str, GraphDecisionTrigger],
    bp_by_sector: dict[str, Breakpoint],
) -> tuple[str, str]:
    """Generate the trigger condition for executing this action."""
    if pathway_type == "IMMEDIATE":
        return (
            f"Execute immediately — deadline {ad.decision_deadline}",
            f"تنفيذ فوري — الموعد النهائي {ad.decision_deadline}",
        )

    # For conditional, use the matching trigger
    trigger = trigger_by_sector.get(ad.sector)
    if trigger:
        return (
            f"When {trigger.reason_en}",
            f"عندما {trigger.reason_ar}",
        )

    if pathway_type == "CONDITIONAL":
        return (
            f"When {ad.sector} stress exceeds critical threshold",
            f"عندما يتجاوز ضغط {ad.sector} العتبة الحرجة",
        )

    return (
        f"As part of long-term {ad.sector} resilience program",
        f"كجزء من برنامج المرونة طويل المدى لقطاع {ad.sector}",
    )


def _classify_reversibility(sector: str, cost: float) -> tuple[str, str]:
    """Classify reversibility based on sector and cost magnitude."""
    if sector in _REVERSIBLE_SECTORS and cost < 500_000_000:
        return "reversible", "قابل للعكس"
    if sector in _IRREVERSIBLE_SECTORS or cost > 1_000_000_000:
        return "irreversible", "غير قابل للعكس"
    return "partially_reversible", "قابل للعكس جزئياً"


def _format_usd(v: float) -> str:
    if v >= 1_000_000_000:
        return f"${v / 1_000_000_000:.1f}B"
    if v >= 1_000_000:
        return f"${v / 1_000_000:.0f}M"
    if v >= 1_000:
        return f"${v / 1_000:.0f}K"
    return f"${v:.0f}"
