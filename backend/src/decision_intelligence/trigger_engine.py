"""
Graph Decision Trigger Engine — generates decisions from ImpactMapResponse.

Reads node stress, time_to_breach, propagation severity, and regime state
directly from the typed ImpactMapResponse. No raw dict parsing.

Trigger rules:
  IF time_to_breach < threshold AND stress_level high AND propagation accelerating
  THEN → trigger decision

Output: List[GraphDecisionTrigger] ordered by urgency.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.schemas.impact_map import ImpactMapResponse, ImpactMapNode, PropagationEvent

logger = logging.getLogger(__name__)


# ── Trigger thresholds ────────────────────────────────────────────────────────

_BREACH_CRITICAL_HOURS = 24.0    # time_to_breach below this → CRITICAL trigger
_BREACH_WARNING_HOURS = 72.0     # time_to_breach below this → WARNING trigger
_STRESS_CRITICAL = 0.65          # stress above this → trigger
_STRESS_WARNING = 0.40           # stress above this + other signal → trigger
_PROPAGATION_ACCELERATION = 0.15 # severity jump per hop > this → accelerating


@dataclass(frozen=True, slots=True)
class GraphDecisionTrigger:
    """A decision trigger derived from graph state."""
    id: str
    node_id: str
    node_label: str
    trigger_type: str          # "BREACH_IMMINENT" | "STRESS_CRITICAL" | "PROPAGATION_SURGE" | "REGIME_ESCALATION" | "BOTTLENECK_RISK"
    severity: float            # 0-1
    urgency: float             # 0-1
    time_to_action_hours: float
    reason_en: str
    reason_ar: str
    sector: str = ""
    affected_edges: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "node_id": self.node_id,
            "node_label": self.node_label,
            "trigger_type": self.trigger_type,
            "severity": round(self.severity, 4),
            "urgency": round(self.urgency, 4),
            "time_to_action_hours": round(self.time_to_action_hours, 1),
            "reason_en": self.reason_en,
            "reason_ar": self.reason_ar,
            "sector": self.sector,
            "affected_edges": self.affected_edges,
        }


def build_graph_triggers(impact_map: ImpactMapResponse) -> list[GraphDecisionTrigger]:
    """
    Scan ImpactMapResponse and generate decision triggers.

    Trigger sources:
      1. BREACH_IMMINENT — node time_to_breach < threshold
      2. STRESS_CRITICAL — node stress above critical threshold
      3. PROPAGATION_SURGE — severity acceleration across hops
      4. REGIME_ESCALATION — regime amplifier > 1.3
      5. BOTTLENECK_RISK — bottleneck node under stress

    Returns: List[GraphDecisionTrigger] sorted by urgency descending.
    """
    triggers: list[GraphDecisionTrigger] = []
    idx = 0

    # ── Source 1: Breach-imminent nodes ─────────────────────────────────────
    for node in impact_map.nodes:
        if node.time_to_breach_hours is not None and node.time_to_breach_hours <= _BREACH_WARNING_HOURS:
            is_critical = node.time_to_breach_hours <= _BREACH_CRITICAL_HOURS
            ttb = max(0.1, node.time_to_breach_hours)
            urgency = min(1.0, 0.7 + (1.0 - ttb / _BREACH_WARNING_HOURS) * 0.3)
            if is_critical:
                urgency = min(1.0, urgency + 0.15)

            idx += 1
            triggers.append(GraphDecisionTrigger(
                id=f"GT-{idx:03d}",
                node_id=node.id,
                node_label=node.label,
                trigger_type="BREACH_IMMINENT",
                severity=node.stress_level,
                urgency=urgency,
                time_to_action_hours=max(0.5, ttb * 0.5),  # act before breach
                reason_en=f"{node.label} breach in {ttb:.1f}h (stress={node.stress_level:.2f})",
                reason_ar=f"{node.label_ar or node.label} اختراق خلال {ttb:.1f} ساعة (ضغط={node.stress_level:.2f})",
                sector=node.sector,
            ))

    # ── Source 2: Critical stress nodes ─────────────────────────────────────
    for node in impact_map.nodes:
        if node.stress_level >= _STRESS_CRITICAL and node.state in ("DEGRADED", "FAILING", "BREACHED"):
            idx += 1
            urgency = min(1.0, 0.5 + node.stress_level * 0.5)
            triggers.append(GraphDecisionTrigger(
                id=f"GT-{idx:03d}",
                node_id=node.id,
                node_label=node.label,
                trigger_type="STRESS_CRITICAL",
                severity=node.stress_level,
                urgency=urgency,
                time_to_action_hours=max(1.0, (1.0 - node.stress_level) * 24),
                reason_en=f"{node.label} under critical stress ({node.stress_level:.2f}, state={node.state})",
                reason_ar=f"{node.label_ar or node.label} تحت ضغط حرج ({node.stress_level:.2f}، حالة={node.state})",
                sector=node.sector,
            ))

    # ── Source 3: Propagation surge ─────────────────────────────────────────
    if len(impact_map.propagation_events) >= 3:
        # Check for severity acceleration across consecutive events
        events = impact_map.propagation_events
        for i in range(2, len(events)):
            sev_jump = events[i].severity_at_arrival - events[i-1].severity_at_arrival
            if sev_jump > _PROPAGATION_ACCELERATION:
                idx += 1
                triggers.append(GraphDecisionTrigger(
                    id=f"GT-{idx:03d}",
                    node_id=events[i].target_id,
                    node_label=events[i].target_id,
                    trigger_type="PROPAGATION_SURGE",
                    severity=events[i].severity_at_arrival,
                    urgency=min(1.0, 0.6 + sev_jump),
                    time_to_action_hours=max(1.0, events[i].arrival_hour - events[i-1].arrival_hour),
                    reason_en=f"Propagation accelerating: +{sev_jump:.2f} severity at hop {events[i].hop}",
                    reason_ar=f"تسارع الانتشار: +{sev_jump:.2f} شدة عند القفزة {events[i].hop}",
                    sector="",
                ))
                break  # one surge trigger is enough

    # ── Source 4: Regime escalation ─────────────────────────────────────────
    regime = impact_map.regime
    if regime.propagation_amplifier > 1.3:
        idx += 1
        urgency = min(1.0, 0.5 + (regime.propagation_amplifier - 1.0) * 0.5)
        triggers.append(GraphDecisionTrigger(
            id=f"GT-{idx:03d}",
            node_id="SYSTEM",
            node_label=regime.regime_label,
            trigger_type="REGIME_ESCALATION",
            severity=regime.propagation_amplifier / 2.0,  # normalize to [0,1]
            urgency=urgency,
            time_to_action_hours=max(1.0, 24.0 * regime.delay_compression),
            reason_en=f"Regime {regime.regime_id}: amplifier={regime.propagation_amplifier:.2f}, "
                      f"delay_compression={regime.delay_compression:.2f}",
            reason_ar=f"النظام {regime.regime_label_ar}: مضاعف={regime.propagation_amplifier:.2f}",
            sector="",
        ))

    # ── Source 5: Bottleneck under stress ───────────────────────────────────
    for node in impact_map.nodes:
        if node.is_bottleneck and node.stress_level >= _STRESS_WARNING:
            # Find edges through this bottleneck
            affected = [
                f"{e.source}→{e.target}"
                for e in impact_map.edges
                if (e.source == node.id or e.target == node.id) and e.is_active
            ]
            idx += 1
            triggers.append(GraphDecisionTrigger(
                id=f"GT-{idx:03d}",
                node_id=node.id,
                node_label=node.label,
                trigger_type="BOTTLENECK_RISK",
                severity=node.stress_level,
                urgency=min(1.0, 0.5 + node.stress_level * 0.4),
                time_to_action_hours=max(2.0, (1.0 - node.stress_level) * 48),
                reason_en=f"Bottleneck {node.label} under stress ({node.stress_level:.2f}), {len(affected)} active edges",
                reason_ar=f"اختناق {node.label_ar or node.label} تحت ضغط ({node.stress_level:.2f})، {len(affected)} حواف نشطة",
                sector=node.sector,
                affected_edges=affected[:10],
            ))

    # Sort by urgency descending
    triggers.sort(key=lambda t: -t.urgency)

    # Deduplicate by node_id + trigger_type (keep highest urgency)
    seen: set[str] = set()
    deduped: list[GraphDecisionTrigger] = []
    for t in triggers:
        key = f"{t.node_id}:{t.trigger_type}"
        if key not in seen:
            seen.add(key)
            deduped.append(t)

    logger.info("[TriggerEngine] Generated %d triggers from impact map", len(deduped))
    return deduped
