"""
Map Payload Engine — builds map_payload and graph_payload from pipeline results.

Transforms raw simulation results + GCC_NODES into the contract shapes
expected by the frontend's UnifiedRunResult type:

  map_payload: {
    impacted_entities: ImpactedEntity[]
    total_estimated_loss_usd: number
  }
  graph_payload: {
    nodes: KnowledgeGraphNode[]
    edges: KnowledgeGraphEdge[]
    categories: string[]
  }
  propagation_steps: PropagationStep[]

Called inline by run_orchestrator — NOT a separate API endpoint.
"""
from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from src.regime.regime_graph_adapter import RegimeGraphModifiers

logger = logging.getLogger(__name__)

# ── Sector → GraphLayer mapping ─────────────────────────────────────────────
_SECTOR_TO_LAYER: dict[str, str] = {
    "maritime":       "INFRASTRUCTURE",
    "energy":         "ENERGY",
    "banking":        "FINANCE",
    "insurance":      "FINANCE",
    "fintech":        "FINANCE",
    "logistics":      "INFRASTRUCTURE",
    "infrastructure": "INFRASTRUCTURE",
    "government":     "SOVEREIGN",
    "healthcare":     "INFRASTRUCTURE",
}


def _classify_stress(stress: float) -> str:
    """Map stress score to classification label."""
    if stress >= 0.80:
        return "CRITICAL"
    if stress >= 0.65:
        return "SEVERE"
    if stress >= 0.50:
        return "HIGH"
    if stress >= 0.35:
        return "ELEVATED"
    if stress >= 0.20:
        return "MODERATE"
    return "LOW"


def _apply_regime_stress(
    stress: float,
    node_id: str,
    regime_modifiers: "RegimeGraphModifiers | None",
) -> float:
    """Apply regime modifiers to a node's stress if modifiers are available."""
    if regime_modifiers is None:
        return stress
    from src.regime.regime_graph_adapter import compute_regime_adjusted_stress
    return compute_regime_adjusted_stress(stress, node_id, regime_modifiers)


def build_map_payload(
    result: dict[str, Any],
    gcc_nodes: list[dict[str, Any]],
    scenario_id: str = "",
    regime_modifiers: "RegimeGraphModifiers | None" = None,
) -> dict[str, Any]:
    """
    Build map_payload with impacted_entities from simulation result.

    Maps financial_impact entities to GCC_NODES geo-coordinates and
    enriches with stress scores from sector stress blocks.

    Args:
        result:      Complete simulation result dict.
        gcc_nodes:   GCC_NODES list from simulation_engine.
        scenario_id: For logging / context.

    Returns:
        Dict with shape: { impacted_entities: [...], total_estimated_loss_usd: float }
    """
    # Build node lookup
    node_map: dict[str, dict] = {n["id"]: n for n in gcc_nodes}

    # Collect financial entity list
    financial = result.get("financial", [])
    if isinstance(financial, dict):
        financial = financial.get("top_entities", [])
    if not isinstance(financial, list):
        financial = []

    # Sector stress lookups for enrichment
    banking = result.get("banking_stress", {}) or {}
    insurance = result.get("insurance_stress", {}) or {}
    fintech = result.get("fintech_stress", {}) or {}
    _sector_stress: dict[str, float] = {
        "banking":   banking.get("aggregate_stress", 0.0) if isinstance(banking, dict) else 0.0,
        "insurance": insurance.get("aggregate_stress", insurance.get("severity_index", 0.0)) if isinstance(insurance, dict) else 0.0,
        "fintech":   fintech.get("aggregate_stress", 0.0) if isinstance(fintech, dict) else 0.0,
    }

    # Bottleneck set for flagging
    bottleneck_ids = set()
    for b in result.get("bottlenecks", []):
        bid = b.get("node_id") if isinstance(b, dict) else ""
        if bid:
            bottleneck_ids.add(bid)

    entities: list[dict] = []
    total_loss = 0.0

    for fi in financial:
        if not isinstance(fi, dict):
            continue
        eid = fi.get("entity_id", "")
        node = node_map.get(eid)
        if not node:
            continue

        loss = float(fi.get("loss_usd", 0) or 0)
        sector = node.get("sector", "")
        raw_stress = float(fi.get("stress_score", 0) or _sector_stress.get(sector, 0.0))
        stress = _apply_regime_stress(raw_stress, eid, regime_modifiers)
        classification = fi.get("classification", _classify_stress(stress))

        entities.append({
            "node_id": eid,
            "label": fi.get("entity_label", node.get("label", eid)),
            "label_ar": node.get("label_ar", ""),
            "lat": node["lat"],
            "lng": node["lng"],
            "stress": round(stress, 4),
            "loss_usd": round(loss, 2),
            "classification": classification,
            "layer": _SECTOR_TO_LAYER.get(sector, "INFRASTRUCTURE"),
            "is_bottleneck": eid in bottleneck_ids,
        })
        total_loss += loss

    # If no financial entities matched, build from all affected nodes using
    # propagation_chain + sector_analysis for broader coverage
    if not entities:
        entities = _entities_from_propagation(result, node_map, bottleneck_ids)
        total_loss = sum(e.get("loss_usd", 0) for e in entities)

    return {
        "impacted_entities": entities,
        "total_estimated_loss_usd": round(total_loss, 2),
    }


def _entities_from_propagation(
    result: dict,
    node_map: dict[str, dict],
    bottleneck_ids: set[str],
) -> list[dict]:
    """Fallback: build entities from propagation_chain when financial list is empty.

    Handles both path-based and entity_id-based chain formats.
    """
    seen: set[str] = set()
    entities: list[dict] = []
    severity = float(result.get("event_severity", result.get("severity", 0.5)))

    for step in result.get("propagation_chain", result.get("propagation", [])):
        if not isinstance(step, dict):
            continue

        # Collect node IDs from either format
        nids: list[str] = []
        if "path" in step:
            nids = step["path"]
        elif "entity_id" in step:
            nids = [step["entity_id"]]

        hop = step.get("hop", step.get("step", 1))
        for nid in nids:
            if nid in seen or nid not in node_map:
                continue
            seen.add(nid)
            node = node_map[nid]
            sector = node.get("sector", "")
            stress = max(0.05, severity * (0.85 ** hop))
            entities.append({
                "node_id": nid,
                "label": node.get("label", nid),
                "label_ar": node.get("label_ar", ""),
                "lat": node["lat"],
                "lng": node["lng"],
                "stress": round(stress, 4),
                "loss_usd": 0,
                "classification": _classify_stress(stress),
                "layer": _SECTOR_TO_LAYER.get(sector, "INFRASTRUCTURE"),
                "is_bottleneck": nid in bottleneck_ids,
            })

    return entities


def build_graph_payload(
    result: dict[str, Any],
    gcc_nodes: list[dict[str, Any]],
    gcc_adjacency: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    """
    Build graph_payload with nodes + edges for network visualization.

    Args:
        result:         Complete simulation result dict.
        gcc_nodes:      GCC_NODES list from simulation_engine.
        gcc_adjacency:  GCC_ADJACENCY dict (node_id → [neighbor_ids]).

    Returns:
        Dict with shape: { nodes: [...], edges: [...], categories: [...] }
    """
    node_map = {n["id"]: n for n in gcc_nodes}
    severity = float(result.get("event_severity", result.get("severity", 0.5)))

    # Build stress map from propagation chain (handles both path and entity_id formats)
    node_stress: dict[str, float] = {}
    for step in result.get("propagation_chain", result.get("propagation", [])):
        if not isinstance(step, dict):
            continue
        nids = step.get("path", [])
        if not nids and "entity_id" in step:
            nids = [step["entity_id"]]
        hop = step.get("hop", step.get("step", 1))
        for nid in nids:
            stress = max(0.05, severity * (0.85 ** hop))
            node_stress[nid] = max(node_stress.get(nid, 0), stress)

    # Enrich from financial entities
    for fi in (result.get("financial", []) if isinstance(result.get("financial"), list) else []):
        if isinstance(fi, dict):
            eid = fi.get("entity_id", "")
            ss = float(fi.get("stress_score", 0) or 0)
            if eid and ss > 0:
                node_stress[eid] = max(node_stress.get(eid, 0), ss)

    # Build nodes
    categories = set()
    nodes = []
    for n in gcc_nodes:
        nid = n["id"]
        stress = node_stress.get(nid, 0.0)
        layer = _SECTOR_TO_LAYER.get(n.get("sector", ""), "INFRASTRUCTURE")
        categories.add(layer)
        nodes.append({
            "id": nid,
            "label": n.get("label", nid),
            "label_ar": n.get("label_ar", ""),
            "layer": layer,
            "type": n.get("sector", ""),
            "weight": n.get("criticality", 0.5),
            "lat": n["lat"],
            "lng": n["lng"],
            "sensitivity": n.get("criticality", 0.5),
            "stress": round(stress, 4) if stress > 0 else None,
            "classification": _classify_stress(stress) if stress > 0 else None,
        })

    # Build edges from adjacency
    edges = []
    if gcc_adjacency:
        for src_id, neighbors in gcc_adjacency.items():
            if src_id not in node_map:
                continue
            for tgt_id in neighbors:
                if tgt_id not in node_map:
                    continue
                edges.append({
                    "source": src_id,
                    "target": tgt_id,
                    "weight": 1.0,
                    "type": "DEPENDENCY",
                })

    return {
        "nodes": nodes,
        "edges": edges,
        "categories": sorted(categories),
    }


def build_propagation_steps(
    result: dict[str, Any],
    gcc_nodes: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Build propagation_steps array from propagation_chain.

    Handles TWO chain formats:
      Format A (path-based): [{path: ["hormuz", "dubai_port"], hop: 1, impact: 0.85}, ...]
      Format B (entity-based): [{step: 1, entity_id: "hormuz", impact: 1.0}, {step: 1, entity_id: "qatar_lng"}, ...]

    Returns list of: { from, to, weight, transmission, label }
    """
    node_map = {n["id"]: n for n in gcc_nodes}
    steps: list[dict] = []
    seen: set[str] = set()

    chain = result.get("propagation_chain", result.get("propagation", []))
    if not isinstance(chain, list) or not chain:
        return steps

    # Detect format
    first = chain[0] if isinstance(chain[0], dict) else {}
    has_path = "path" in first
    has_entity_id = "entity_id" in first

    if has_path:
        # Format A: path-based
        for step in chain:
            if not isinstance(step, dict):
                continue
            path = step.get("path", [])
            impact = float(step.get("impact", 0) or 0)
            for i in range(len(path) - 1):
                from_id, to_id = path[i], path[i + 1]
                key = f"{from_id}->{to_id}"
                if key in seen:
                    continue
                seen.add(key)
                from_node = node_map.get(from_id, {})
                to_node = node_map.get(to_id, {})
                steps.append({
                    "from": from_id,
                    "to": to_id,
                    "weight": round(impact, 4),
                    "transmission": round(impact * 0.72, 4),
                    "label": f"{from_node.get('label', from_id)} → {to_node.get('label', to_id)}",
                })
    elif has_entity_id:
        # Format B: entity-based sequential steps → derive from→to pairs
        # Group by step number, then connect across step boundaries
        from collections import defaultdict
        step_groups: dict[int, list[str]] = defaultdict(list)
        for entry in chain:
            if not isinstance(entry, dict):
                continue
            step_num = int(entry.get("step", 0))
            eid = entry.get("entity_id", "")
            if eid and eid in node_map:
                step_groups[step_num].append(eid)

        sorted_steps = sorted(step_groups.keys())
        for i in range(len(sorted_steps) - 1):
            from_entities = step_groups[sorted_steps[i]]
            to_entities = step_groups[sorted_steps[i + 1]]
            for from_id in from_entities:
                for to_id in to_entities:
                    if from_id == to_id:
                        continue
                    key = f"{from_id}->{to_id}"
                    if key in seen:
                        continue
                    seen.add(key)
                    from_node = node_map.get(from_id, {})
                    to_node = node_map.get(to_id, {})
                    steps.append({
                        "from": from_id,
                        "to": to_id,
                        "weight": round(1.0 / max(1, sorted_steps[i + 1]), 4),
                        "transmission": round(0.72 / max(1, sorted_steps[i + 1]), 4),
                        "label": f"{from_node.get('label', from_id)} → {to_node.get('label', to_id)}",
                    })

    return steps
