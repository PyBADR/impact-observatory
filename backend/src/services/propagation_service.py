"""Service 3: propagation_service — Impact Chain (سلسلة الأثر).

BFS/multi-hop propagation through the entity graph.
Uses sigmoid clamping: impact = 1 / (1 + exp(-steepness*(x - midpoint)))
"""

from __future__ import annotations

import logging
import math

logger = logging.getLogger(__name__)

STEEPNESS = 10.0
MIDPOINT = 0.5
DECAY_PER_HOP = 0.6  # Each hop retains 60% of parent impact


def sigmoid_clamp(x: float) -> float:
    """Clamp value through sigmoid: 1 / (1 + exp(-k*(x - m)))."""
    return 1.0 / (1.0 + math.exp(-STEEPNESS * (x - MIDPOINT)))


def propagate_impacts(
    entities: list[dict],
    edges: list[dict],
    shock_nodes: list[str],
    severity: float,
    max_hops: int = 6,
) -> list[dict]:
    """BFS propagation from shock nodes through entity graph.

    Returns list of {entity_id, impact, hop, path, classification}.
    """
    # Build adjacency with weights
    adj: dict[str, list[tuple[str, float]]] = {e["id"]: [] for e in entities}
    for edge in edges:
        src = edge.get("source") or edge.get("source_id", "")
        tgt = edge.get("target") or edge.get("target_id", "")
        weight = edge.get("weight", 1.0)
        if src in adj:
            adj[src].append((tgt, weight))

    # BFS
    impacts: dict[str, dict] = {}
    queue: list[tuple[str, float, int, list[str]]] = []

    for nid in shock_nodes:
        if nid in adj:
            raw = severity
            clamped = sigmoid_clamp(raw)
            impacts[nid] = {
                "entity_id": nid,
                "impact": round(clamped, 4),
                "raw_impact": round(raw, 4),
                "hop": 0,
                "path": [nid],
            }
            queue.append((nid, raw, 0, [nid]))

    while queue:
        current, parent_impact, hop, path = queue.pop(0)
        if hop >= max_hops:
            continue

        for neighbor, weight in adj.get(current, []):
            child_impact = parent_impact * DECAY_PER_HOP * weight
            if child_impact < 0.01:
                continue

            clamped = sigmoid_clamp(child_impact)
            new_path = path + [neighbor]

            # Only update if this path gives higher impact
            existing = impacts.get(neighbor)
            if existing is None or clamped > existing["impact"]:
                impacts[neighbor] = {
                    "entity_id": neighbor,
                    "impact": round(clamped, 4),
                    "raw_impact": round(child_impact, 4),
                    "hop": hop + 1,
                    "path": new_path,
                }
                queue.append((neighbor, child_impact, hop + 1, new_path))

    # Classify and sort
    result = []
    for entry in impacts.values():
        imp = entry["impact"]
        entry["classification"] = (
            "CRITICAL" if imp > 0.7
            else "ELEVATED" if imp > 0.4
            else "MODERATE" if imp > 0.2
            else "LOW" if imp > 0.05
            else "NOMINAL"
        )
        result.append(entry)

    result.sort(key=lambda x: x["impact"], reverse=True)
    return result
