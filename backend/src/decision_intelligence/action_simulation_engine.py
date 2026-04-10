"""
Action Simulation Engine — simulates decision effects on propagation.

Takes an ImpactMapResponse + a decision overlay and locally re-simulates
propagation to compute the delta. No full simulation re-run — applies
overlay operations (CUT/DELAY/REDIRECT/BUFFER) to the existing graph
and recalculates downstream stress.

Output: ActionSimResult with affected_nodes, propagation_reduction, etc.
"""
from __future__ import annotations

import copy
import logging
from dataclasses import dataclass, field
from typing import Any

from src.schemas.impact_map import (
    ImpactMapResponse, ImpactMapEdge, ImpactMapNode, DecisionOverlay,
)
from src.config import TX_SEVERITY_TRANSFER_RATIO

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class ActionSimResult:
    """Result of simulating a single action's effect on the graph."""
    action_id: str
    action_label: str
    overlay_operations: list[str]       # ["CUT", "BUFFER", ...]
    affected_nodes: list[str]           # node IDs with changed stress
    propagation_reduction: float        # [0-1] fraction of propagation prevented
    delay_change_hours: float           # net delay added/removed
    stress_reduction_total: float       # sum of stress deltas across affected nodes
    failure_prevention_count: int       # breaches prevented
    nodes_protected: int                # nodes whose state improved
    baseline_loss_usd: float            # loss without action
    mitigated_loss_usd: float           # loss with action applied

    def to_dict(self) -> dict[str, Any]:
        return {
            "action_id": self.action_id,
            "action_label": self.action_label,
            "overlay_operations": self.overlay_operations,
            "affected_nodes": self.affected_nodes,
            "propagation_reduction": round(self.propagation_reduction, 4),
            "delay_change_hours": round(self.delay_change_hours, 2),
            "stress_reduction_total": round(self.stress_reduction_total, 4),
            "failure_prevention_count": self.failure_prevention_count,
            "nodes_protected": self.nodes_protected,
            "baseline_loss_usd": round(self.baseline_loss_usd, 2),
            "mitigated_loss_usd": round(self.mitigated_loss_usd, 2),
        }


def simulate_action_effects(
    impact_map: ImpactMapResponse,
    overlays: list[DecisionOverlay],
) -> list[ActionSimResult]:
    """
    Simulate each action's effect on the propagation graph.

    For each unique action_id in overlays:
      1. Clone the edge/node state
      2. Apply overlay operations (CUT, DELAY, REDIRECT, BUFFER)
      3. Re-propagate stress locally (1-hop forward)
      4. Compare before vs after
      5. Return ActionSimResult

    Returns: list[ActionSimResult] — one per unique action.
    """
    # Group overlays by action_id
    action_overlays: dict[str, list[DecisionOverlay]] = {}
    for ov in overlays:
        action_overlays.setdefault(ov.action_id, []).append(ov)

    results: list[ActionSimResult] = []

    for action_id, ovs in action_overlays.items():
        result = _simulate_single_action(impact_map, action_id, ovs)
        results.append(result)

    # Sort by propagation_reduction descending
    results.sort(key=lambda r: -r.propagation_reduction)

    logger.info("[ActionSimEngine] Simulated %d actions", len(results))
    return results


def _simulate_single_action(
    impact_map: ImpactMapResponse,
    action_id: str,
    overlays: list[DecisionOverlay],
) -> ActionSimResult:
    """Simulate a single action's overlays on the graph."""

    # Build baseline state
    node_stress_before: dict[str, float] = {n.id: n.stress_level for n in impact_map.nodes}
    node_loss_before: dict[str, float] = {n.id: n.loss_usd for n in impact_map.nodes}
    node_state_before: dict[str, str] = {n.id: n.state for n in impact_map.nodes}

    # Clone edges as mutable dicts
    edges_modified: dict[str, dict] = {}
    for e in impact_map.edges:
        key = f"{e.source}→{e.target}"
        edges_modified[key] = {
            "source": e.source, "target": e.target,
            "weight": e.weight, "delay_hours": e.delay_hours,
            "transfer_ratio": e.transfer_ratio, "is_active": e.is_active,
        }

    # Build adjacency
    adjacency: dict[str, list[str]] = {}
    for e in impact_map.edges:
        adjacency.setdefault(e.source, []).append(e.target)

    # Apply overlay operations
    operations: list[str] = []
    net_delay_change = 0.0
    buffer_capacity = 0.0

    for ov in overlays:
        operations.append(ov.operation)

        if ov.operation == "CUT" and ov.target_edge:
            if ov.target_edge in edges_modified:
                edges_modified[ov.target_edge]["weight"] = 0.0
                edges_modified[ov.target_edge]["is_active"] = False

        elif ov.operation == "DELAY" and ov.target_edge:
            if ov.target_edge in edges_modified:
                edges_modified[ov.target_edge]["delay_hours"] += ov.delay_delta_hours
                net_delay_change += ov.delay_delta_hours

        elif ov.operation == "REDIRECT" and ov.target_node and ov.redirect_target:
            # Reduce weight on all edges TO the original target
            for key, edge in edges_modified.items():
                if edge["target"] == ov.target_node:
                    edge["weight"] *= 0.3  # 70% reduction

        elif ov.operation == "BUFFER" and ov.target_node:
            buffer_capacity += ov.buffer_capacity_usd

        elif ov.operation == "ISOLATE" and ov.target_node:
            for key, edge in edges_modified.items():
                if edge["target"] == ov.target_node:
                    edge["weight"] = 0.0
                    edge["is_active"] = False

    # Re-propagate: compute new stress for each node after overlay
    node_stress_after: dict[str, float] = dict(node_stress_before)

    for nid in node_stress_before:
        # Sum inbound stress from modified edges
        inbound_stress = 0.0
        inbound_count = 0
        for key, edge in edges_modified.items():
            if edge["target"] == nid and edge["is_active"] and edge["weight"] > 0:
                src_stress = node_stress_before.get(edge["source"], 0.0)
                inbound_stress += src_stress * edge["weight"] * edge["transfer_ratio"]
                inbound_count += 1

        if inbound_count > 0:
            # Blend: 60% from original stress (self), 40% from inbound after modification
            blended = node_stress_before[nid] * 0.6 + (inbound_stress / max(inbound_count, 1)) * 0.4
            node_stress_after[nid] = min(1.0, max(0.0, blended))

    # Apply buffer: reduce stress on buffered nodes
    for ov in overlays:
        if ov.operation == "BUFFER" and ov.target_node and ov.target_node in node_stress_after:
            # Buffer effect: reduce stress proportional to buffer capacity / total loss
            total_loss = sum(node_loss_before.values())
            if total_loss > 0:
                buffer_effect = min(0.3, ov.buffer_capacity_usd / max(total_loss, 1.0))
            else:
                buffer_effect = 0.1
            node_stress_after[ov.target_node] = max(
                0.0,
                node_stress_after[ov.target_node] - buffer_effect,
            )

    # Compute deltas
    affected_nodes: list[str] = []
    stress_reduction_total = 0.0
    failure_prevention_count = 0
    nodes_protected = 0

    for nid in node_stress_before:
        before = node_stress_before[nid]
        after = node_stress_after[nid]
        delta = before - after
        if abs(delta) > 0.001:
            affected_nodes.append(nid)
            stress_reduction_total += max(0, delta)
            # Check if state improved
            if before >= 0.60 and after < 0.60:
                nodes_protected += 1
            if node_state_before.get(nid) in ("FAILING", "BREACHED") and after < 0.65:
                failure_prevention_count += 1

    # Propagation reduction: fraction of total stress that was reduced
    total_stress_before = sum(node_stress_before.values())
    propagation_reduction = stress_reduction_total / max(total_stress_before, 0.001)

    # Loss computation
    baseline_loss = sum(node_loss_before.values())
    mitigated_loss = baseline_loss * (1.0 - min(0.85, propagation_reduction))

    action_label = overlays[0].action_label if overlays else action_id

    return ActionSimResult(
        action_id=action_id,
        action_label=action_label,
        overlay_operations=list(set(operations)),
        affected_nodes=affected_nodes[:20],
        propagation_reduction=propagation_reduction,
        delay_change_hours=net_delay_change,
        stress_reduction_total=stress_reduction_total,
        failure_prevention_count=failure_prevention_count,
        nodes_protected=nodes_protected,
        baseline_loss_usd=baseline_loss,
        mitigated_loss_usd=mitigated_loss,
    )
