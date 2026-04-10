"""Underwriting watch list generation.

Flags policies/portfolios that require underwriting review based on
risk threshold breaches, exposure concentration, and claims surge.

Watch triggers:
    1. Risk score > threshold (default 0.6)
    2. Exposure classification = CRITICAL
    3. Claims surge classification = SEVERE or HIGH
    4. Chokepoint dependency > 0.7
    5. Multiple concurrent triggers = escalated priority
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

import numpy as np


class WatchPriority(StrEnum):
    IMMEDIATE = "IMMEDIATE"
    URGENT = "URGENT"
    ELEVATED = "ELEVATED"
    ROUTINE = "ROUTINE"


@dataclass
class WatchTrigger:
    """A specific reason for watch listing."""
    trigger_type: str
    value: float
    threshold: float
    detail: str


@dataclass
class UnderwritingWatchItem:
    """A single item on the underwriting watch list."""
    entity_id: str
    priority: WatchPriority
    triggers: list[WatchTrigger]
    risk_score: float
    exposure_score: float
    surge_score: float
    recommended_action: str


@dataclass
class UnderwritingWatchList:
    """Complete watch list with summary."""
    items: list[UnderwritingWatchItem]
    total_flagged: int
    immediate_count: int
    urgent_count: int
    elevated_count: int
    summary: str


def evaluate_watch(
    entity_id: str,
    risk_score: float,
    exposure_score: float,
    surge_score: float,
    chokepoint_dependency: float = 0.0,
    portfolio_concentration: float = 0.0,
    risk_threshold: float = 0.6,
    exposure_threshold: float = 0.7,
    surge_threshold: float = 0.5,
    chokepoint_threshold: float = 0.7,
    concentration_threshold: float = 0.8,
) -> UnderwritingWatchItem | None:
    """Evaluate whether an entity should be watch-listed."""
    triggers: list[WatchTrigger] = []

    if risk_score > risk_threshold:
        triggers.append(WatchTrigger(
            "risk_breach", risk_score, risk_threshold,
            f"Risk score {risk_score:.2f} exceeds {risk_threshold}",
        ))

    if exposure_score >= exposure_threshold:
        triggers.append(WatchTrigger(
            "exposure_critical", exposure_score, exposure_threshold,
            f"Exposure {exposure_score:.2f} at CRITICAL level",
        ))

    if surge_score >= surge_threshold:
        triggers.append(WatchTrigger(
            "claims_surge", surge_score, surge_threshold,
            f"Claims surge {surge_score:.2f} at HIGH/SEVERE level",
        ))

    if chokepoint_dependency > chokepoint_threshold:
        triggers.append(WatchTrigger(
            "chokepoint_dependency", chokepoint_dependency, chokepoint_threshold,
            f"Chokepoint dependency {chokepoint_dependency:.2f} exceeds threshold",
        ))

    if portfolio_concentration > concentration_threshold:
        triggers.append(WatchTrigger(
            "concentration_risk", portfolio_concentration, concentration_threshold,
            f"Portfolio concentration {portfolio_concentration:.2f} exceeds limit",
        ))

    if not triggers:
        return None

    # Priority based on trigger count and severity
    n_triggers = len(triggers)
    max_severity = max(t.value for t in triggers)

    if n_triggers >= 3 or max_severity > 0.85:
        priority = WatchPriority.IMMEDIATE
        action = "Suspend new policies. Initiate portfolio rebalancing. Escalate to senior underwriter."
    elif n_triggers >= 2 or max_severity > 0.7:
        priority = WatchPriority.URGENT
        action = "Review all active policies. Consider premium adjustment. Flag for reinsurance review."
    elif max_severity > 0.5:
        priority = WatchPriority.ELEVATED
        action = "Increase monitoring frequency. Review renewal terms. Flag for next committee."
    else:
        priority = WatchPriority.ROUTINE
        action = "Note for next scheduled review cycle."

    return UnderwritingWatchItem(
        entity_id=entity_id,
        priority=priority,
        triggers=triggers,
        risk_score=risk_score,
        exposure_score=exposure_score,
        surge_score=surge_score,
        recommended_action=action,
    )


def generate_watch_list(
    entity_ids: list[str],
    risk_scores: list[float],
    exposure_scores: list[float],
    surge_scores: list[float],
    chokepoint_deps: list[float] | None = None,
    concentrations: list[float] | None = None,
) -> UnderwritingWatchList:
    """Generate the full underwriting watch list."""
    n = len(entity_ids)
    choke = chokepoint_deps or [0.0] * n
    conc = concentrations or [0.0] * n

    items: list[UnderwritingWatchItem] = []
    for i in range(n):
        item = evaluate_watch(
            entity_ids[i], risk_scores[i], exposure_scores[i],
            surge_scores[i], choke[i], conc[i],
        )
        if item is not None:
            items.append(item)

    # Sort by priority
    priority_order = {
        WatchPriority.IMMEDIATE: 0,
        WatchPriority.URGENT: 1,
        WatchPriority.ELEVATED: 2,
        WatchPriority.ROUTINE: 3,
    }
    items.sort(key=lambda x: (priority_order[x.priority], -x.risk_score))

    imm = sum(1 for i in items if i.priority == WatchPriority.IMMEDIATE)
    urg = sum(1 for i in items if i.priority == WatchPriority.URGENT)
    elev = sum(1 for i in items if i.priority == WatchPriority.ELEVATED)

    summary = f"{len(items)} entities flagged: {imm} IMMEDIATE, {urg} URGENT, {elev} ELEVATED."

    return UnderwritingWatchList(
        items=items,
        total_flagged=len(items),
        immediate_count=imm,
        urgent_count=urg,
        elevated_count=elev,
        summary=summary,
    )
