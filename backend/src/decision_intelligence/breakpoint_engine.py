"""
Breakpoint Detection Engine — identifies critical intervention points in the graph.

A breakpoint is an edge where severing, delaying, or redirecting would
maximally reduce downstream propagation. These are the decision surface's
"pressure valves."

Reads: ImpactMapResponse edges (is_breakable, weight, delay, transfer_ratio)
       + node stress to compute expected downstream impact.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.schemas.impact_map import ImpactMapResponse, ImpactMapEdge, ImpactMapNode

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Breakpoint:
    """A critical intervention point in the propagation graph."""
    id: str
    edge_source: str
    edge_target: str
    edge_type: str
    severity: float           # how much damage flows through this edge [0-1]
    intervention_type: str    # "CUT" | "DELAY" | "REDIRECT" | "ISOLATE"
    expected_impact: float    # estimated propagation reduction [0-1]
    delay_hours: float        # current propagation delay on this edge
    downstream_nodes: int     # count of nodes downstream that would be protected
    reason_en: str
    reason_ar: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "edge_source": self.edge_source,
            "edge_target": self.edge_target,
            "edge_type": self.edge_type,
            "severity": round(self.severity, 4),
            "intervention_type": self.intervention_type,
            "expected_impact": round(self.expected_impact, 4),
            "delay_hours": round(self.delay_hours, 2),
            "downstream_nodes": self.downstream_nodes,
            "reason_en": self.reason_en,
            "reason_ar": self.reason_ar,
        }


def detect_breakpoints(impact_map: ImpactMapResponse) -> list[Breakpoint]:
    """
    Identify critical intervention points from the ImpactMapResponse.

    Algorithm:
      1. Find all breakable edges (is_breakable=True)
      2. Score each by: source_stress × weight × transfer_ratio × downstream_count
      3. Determine best intervention type based on edge characteristics
      4. Return top breakpoints sorted by expected_impact descending

    Returns: List[Breakpoint] — top intervention points.
    """
    node_map = {n.id: n for n in impact_map.nodes}

    # Build adjacency for downstream counting
    adjacency: dict[str, list[str]] = {}
    for e in impact_map.edges:
        adjacency.setdefault(e.source, []).append(e.target)

    breakpoints: list[Breakpoint] = []
    idx = 0

    for edge in impact_map.edges:
        if not edge.is_breakable and not edge.is_active:
            continue

        src_node = node_map.get(edge.source)
        tgt_node = node_map.get(edge.target)
        if not src_node or not tgt_node:
            continue

        # Score: how much damage flows through this edge
        flow_severity = src_node.stress_level * edge.weight * edge.transfer_ratio
        if flow_severity < 0.05:
            continue  # negligible flow

        # Count downstream nodes reachable from target
        downstream = _count_downstream(edge.target, adjacency, max_depth=4)

        # Expected impact: flow_severity × (1 + downstream/10)
        # More downstream = higher impact of intervention
        expected_impact = min(1.0, flow_severity * (1.0 + downstream / 10.0))

        # Determine best intervention type
        intervention = _classify_intervention(edge, src_node, tgt_node, downstream)

        idx += 1
        breakpoints.append(Breakpoint(
            id=f"BP-{idx:03d}",
            edge_source=edge.source,
            edge_target=edge.target,
            edge_type=edge.type,
            severity=flow_severity,
            intervention_type=intervention,
            expected_impact=expected_impact,
            delay_hours=edge.delay_hours,
            downstream_nodes=downstream,
            reason_en=_build_reason_en(edge, src_node, tgt_node, intervention, downstream),
            reason_ar=_build_reason_ar(edge, src_node, tgt_node, intervention, downstream),
        ))

    # Sort by expected impact descending
    breakpoints.sort(key=lambda b: -b.expected_impact)

    # Cap at top 20 breakpoints
    breakpoints = breakpoints[:20]

    logger.info("[BreakpointEngine] Detected %d breakpoints", len(breakpoints))
    return breakpoints


def _count_downstream(start: str, adjacency: dict[str, list[str]], max_depth: int) -> int:
    """BFS count of reachable nodes from start."""
    visited: set[str] = set()
    queue = [start]
    depth = 0
    while queue and depth < max_depth:
        next_queue: list[str] = []
        for node in queue:
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    next_queue.append(neighbor)
        queue = next_queue
        depth += 1
    return len(visited)


def _classify_intervention(
    edge: ImpactMapEdge,
    src: ImpactMapNode,
    tgt: ImpactMapNode,
    downstream: int,
) -> str:
    """Determine optimal intervention type for this edge."""
    # High severity + low delay = CUT (urgent severance)
    if src.stress_level >= 0.7 and edge.delay_hours < 6.0:
        return "CUT"

    # Target is bottleneck with many downstream = ISOLATE
    if tgt.is_bottleneck and downstream >= 5:
        return "ISOLATE"

    # High delay already = REDIRECT is more effective
    if edge.delay_hours >= 12.0:
        return "REDIRECT"

    # Default: DELAY (buy time)
    return "DELAY"


def _build_reason_en(edge, src, tgt, intervention, downstream) -> str:
    return (
        f"{intervention} edge {src.label}→{tgt.label}: "
        f"severity={src.stress_level:.2f}, transfer={edge.transfer_ratio:.2f}, "
        f"{downstream} downstream nodes protected"
    )


def _build_reason_ar(edge, src, tgt, intervention, downstream) -> str:
    return (
        f"{intervention} الحافة {src.label_ar or src.label}→{tgt.label_ar or tgt.label}: "
        f"شدة={src.stress_level:.2f}، نقل={edge.transfer_ratio:.2f}، "
        f"{downstream} عقد محمية"
    )
