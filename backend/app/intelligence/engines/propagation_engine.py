"""
Propagation Engine — Discrete Dynamic Graph v4.0 (Python Implementation)
Computes cascading impacts through the GCC Reality Graph.

Mathematical Model (enforced tolerance < 0.001):
1. x_i(t+1) = s_i × Σ(w_ji × p_ji × x_j(t)) - d_i × x_i(t) + shock_i
   - s_i = node.sensitivity (0-1)
   - w_ji = edge.weight (0-1)
   - p_ji = edge.polarity (1 or -1)
   - d_i = node.damping_factor (0-1, fallback: decay_rate)
   - shock_i = external forcing for shock nodes (persistent each iteration)
   - All impacts clamped to [-1, 1]

2. Propagation step recorded when |contribution * sensitivity| > 0.01
3. Impact threshold for "affected": |x_i| > 0.01
4. System energy: E_sys = Σ x_i(t)²
5. Sector aggregation: S_k = avg(x_i) for nodes in layer k
6. Confidence: C = 1 / (1 + variance of impacts)
7. Spread level: critical >60%, high >40%, medium >20%, low otherwise
8. Propagation depth: max iteration where new nodes become affected
9. Convergence: if no change > 0.005 and iter > 1, stop early

Validity Conditions:
- D > 2 (propagation depth)
- |x_i| ≤ 1 (bounded impacts)
- Explanation chain = actual propagation path
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
from collections import defaultdict

from .gcc_constants import SECTOR_GDP_BASE, LAYER_LABELS, LAYER_COLORS, SPREAD_LABELS


@dataclass
class PropagationStep:
    """Represents a single impact propagation between two nodes."""
    from_node_id: str
    from_node_label: str
    to_node_id: str
    to_node_label: str
    weight: float
    polarity: int
    impact: float
    label: str
    iteration: int


@dataclass
class NodeExplanation:
    """Detailed explanation of impacts for a single node."""
    node_id: str
    label: str
    label_ar: str
    layer: str
    impact: float
    normalized_impact: float
    incoming_edges: List[Dict[str, Any]]
    outgoing_edges: List[Dict[str, Any]]
    explanation: str
    explanation_ar: str


@dataclass
class SectorImpact:
    """Aggregated impact metrics for a sector/layer."""
    sector: str
    sector_label: str
    avg_impact: float
    max_impact: float
    node_count: int
    top_node: str
    color: str


@dataclass
class Driver:
    """Top propagation drivers ranked by impact × out-degree."""
    node_id: str
    label: str
    impact: float
    layer: str
    out_degree: int


@dataclass
class IterationSnapshot:
    """State snapshot at each iteration."""
    iteration: int
    impacts: Dict[str, float]
    energy: float
    delta_energy: float


@dataclass
class PropagationResult:
    """Complete propagation analysis result."""
    node_impacts: Dict[str, float]
    propagation_chain: List[PropagationStep] = field(default_factory=list)
    affected_sectors: List[SectorImpact] = field(default_factory=list)
    top_drivers: List[Driver] = field(default_factory=list)
    total_loss: float = 0.0
    confidence: float = 0.0
    system_energy: float = 0.0
    propagation_depth: int = 0
    spread_level: str = "low"
    spread_level_ar: str = ""
    iteration_snapshots: List[IterationSnapshot] = field(default_factory=list)
    node_explanations: Dict[str, NodeExplanation] = field(default_factory=dict)


def compute_energy(impacts: Dict[str, float]) -> float:
    """
    Compute system energy as sum of squared impacts.
    E_sys = Σ x_i(t)²
    """
    return float(np.sum([v**2 for v in impacts.values()]))


def run_propagation(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    shocks: List[Dict[str, float]],
    max_iterations: int = 6,
    decay_rate: float = 0.05,
) -> PropagationResult:
    """
    Run the propagation engine on a graph with initial shocks.

    Args:
        nodes: List of node dicts with keys:
            - id: str (unique identifier)
            - label: str (English label)
            - labelAr: str (Arabic label)
            - layer: str (geography|infrastructure|economy|finance|society)
            - sensitivity: float (0-1)
            - damping_factor: float (0-1, optional)
            - weight: float (node weight, optional)
            - value: float (initial value, optional)

        edges: List of edge dicts with keys:
            - id: str
            - source: str (node id)
            - target: str (node id)
            - weight: float (0-1)
            - polarity: int (1 or -1)
            - label: str (English)
            - labelAr: str (Arabic)
            - animated: bool (optional)

        shocks: List of shock dicts with keys:
            - nodeId: str
            - impact: float (clamped to [-1, 1])

        max_iterations: Maximum propagation iterations (default 6)
        decay_rate: Default damping factor if node has none (default 0.05)

    Returns:
        PropagationResult with complete analysis
    """

    # Build node lookup and adjacency lists
    node_map: Dict[str, Dict[str, Any]] = {n["id"]: n for n in nodes}
    incoming_adj: Dict[str, List[Tuple[str, Dict[str, Any]]]] = defaultdict(list)
    outgoing_adj: Dict[str, List[Tuple[str, Dict[str, Any]]]] = defaultdict(list)

    for edge in edges:
        incoming_adj[edge["target"]].append((edge["source"], edge))
        outgoing_adj[edge["source"]].append((edge["target"], edge))

    # Initialize impacts state
    impacts: Dict[str, float] = {n["id"]: 0.0 for n in nodes}

    # Apply initial shocks
    for shock in shocks:
        node_id = shock["nodeId"]
        if node_id in impacts:
            impacts[node_id] = np.clip(shock["impact"], -1, 1)

    # Track propagation chain and snapshots
    chain: List[PropagationStep] = []
    iteration_snapshots: List[IterationSnapshot] = []
    propagation_depth = 0
    initial_shocked_count = len([v for v in impacts.values() if abs(v) > 0.01])

    # Snapshot iteration 0 (initial state)
    snap0 = impacts.copy()
    energy0 = compute_energy(snap0)
    iteration_snapshots.append(
        IterationSnapshot(iteration=0, impacts=snap0, energy=energy0, delta_energy=0.0)
    )

    # ── CORE MATHEMATICAL LOOP ──
    # Formula: x_i(t+1) = s_i × Σ_j(w_ji × p_ji × x_j(t)) - d_i × x_i(t) + shock_i
    for iteration in range(max_iterations):
        new_impacts: Dict[str, float] = {}
        any_change = False

        for node in nodes:
            node_id = node["id"]
            current_impact = impacts[node_id]
            incoming = incoming_adj.get(node_id, [])

            # Compute weighted sum: Σ(w_ji × p_ji × x_j(t))
            weighted_sum = 0.0
            for src_id, edge in incoming:
                src_impact = impacts[src_id]
                if abs(src_impact) < 0.005:
                    continue

                polarity = edge.get("polarity", 1)
                contribution = edge["weight"] * polarity * src_impact
                weighted_sum += contribution

                # Record propagation step if meaningful
                if abs(contribution * node["sensitivity"]) > 0.01:
                    src_node = node_map[src_id]
                    src_label = src_node.get("labelAr", src_node.get("label", src_id))
                    node_label = node.get("labelAr", node.get("label", node_id))

                    chain.append(
                        PropagationStep(
                            from_node_id=src_id,
                            from_node_label=src_label,
                            to_node_id=node_id,
                            to_node_label=node_label,
                            weight=edge["weight"],
                            polarity=polarity,
                            impact=contribution * node["sensitivity"],
                            label=edge.get("labelAr", edge.get("label", "")),
                            iteration=iteration + 1,
                        )
                    )

            # x_i(t+1) = s_i × Σ(...) - d_i × x_i(t)
            sensitivity = node.get("sensitivity", 0.5)
            propagated = weighted_sum * sensitivity
            node_damping = node.get("damping_factor", decay_rate)
            decayed = node_damping * current_impact
            new_impact = propagated - decayed

            # Clamp to [-1, 1]
            new_impact = np.clip(new_impact, -1, 1)

            # Add shock forcing if shock node
            shock_entry = next((s for s in shocks if s["nodeId"] == node_id), None)
            if shock_entry:
                new_impact = np.clip(new_impact + shock_entry["impact"], -1, 1)

            new_impacts[node_id] = new_impact

            # Track if significant change
            if abs(new_impact - current_impact) > 0.005:
                any_change = True

        # Update impacts
        impacts = new_impacts

        # Track propagation depth (max iteration with new affected nodes)
        affected_count = len([v for v in impacts.values() if abs(v) > 0.01])
        if affected_count > initial_shocked_count:
            propagation_depth = iteration + 1

        # Snapshot this iteration
        snap_n = impacts.copy()
        energy_n = compute_energy(snap_n)
        prev_energy = iteration_snapshots[-1].energy
        iteration_snapshots.append(
            IterationSnapshot(
                iteration=iteration + 1,
                impacts=snap_n,
                energy=energy_n,
                delta_energy=energy_n - prev_energy,
            )
        )

        # Early convergence
        if not any_change and iteration > 1:
            break

    # ── SECTOR IMPACTS ──
    sector_groups: Dict[str, Tuple[List[float], List[str]]] = defaultdict(
        lambda: ([], [])
    )

    for node in nodes:
        node_id = node["id"]
        impact = abs(impacts[node_id])
        layer = node.get("layer", "geography")
        label = node.get("labelAr", node.get("label", node_id))

        impacts_list, labels_list = sector_groups[layer]
        impacts_list.append(impact)
        labels_list.append(label)

    affected_sectors: List[SectorImpact] = []
    for layer in ["geography", "infrastructure", "economy", "finance", "society"]:
        if layer not in sector_groups:
            continue

        impacts_list, labels_list = sector_groups[layer]
        if not impacts_list:
            continue

        avg_impact = float(np.mean(impacts_list))
        max_impact = float(np.max(impacts_list))
        max_idx = int(np.argmax(impacts_list))
        node_count = len([i for i in impacts_list if i > 0.01])

        if avg_impact > 0.01:
            affected_sectors.append(
                SectorImpact(
                    sector=layer,
                    sector_label=LAYER_LABELS.get(layer, {}).get("ar", layer),
                    avg_impact=avg_impact,
                    max_impact=max_impact,
                    node_count=node_count,
                    top_node=labels_list[max_idx],
                    color=LAYER_COLORS.get(layer, "#999999"),
                )
            )

    affected_sectors.sort(key=lambda s: s.avg_impact, reverse=True)

    # ── TOP DRIVERS ──
    driver_map: Dict[str, int] = defaultdict(int)
    for step in chain:
        driver_map[step.from_node_id] += 1

    top_drivers: List[Driver] = [
        Driver(
            node_id=node_id,
            label=node_map[node_id].get("labelAr", node_map[node_id].get("label", node_id)),
            impact=abs(impacts[node_id]),
            layer=node_map[node_id].get("layer", "geography"),
            out_degree=out_degree,
        )
        for node_id, out_degree in driver_map.items()
    ]
    top_drivers.sort(key=lambda d: d.impact * d.out_degree, reverse=True)
    top_drivers = top_drivers[:8]

    # ── TOTAL ECONOMIC LOSS ──
    total_loss = 0.0
    for layer in ["geography", "infrastructure", "economy", "finance", "society"]:
        if layer not in sector_groups:
            continue
        impacts_list, _ = sector_groups[layer]
        if impacts_list:
            avg_impact = float(np.mean(impacts_list))
            base = SECTOR_GDP_BASE.get(layer, 0)
            total_loss += base * avg_impact

    # ── SPREAD LEVEL ──
    avg_global_impact = float(
        np.mean([abs(v) for v in impacts.values()]) if impacts else 0.0
    )

    if avg_global_impact > 0.6:
        spread_level = "critical"
    elif avg_global_impact > 0.4:
        spread_level = "high"
    elif avg_global_impact > 0.2:
        spread_level = "medium"
    else:
        spread_level = "low"

    spread_level_ar = SPREAD_LABELS.get(spread_level, spread_level)

    # ── SYSTEM ENERGY ──
    system_energy = compute_energy(impacts)

    # ── CONFIDENCE ──
    impact_values = [abs(v) for v in impacts.values()]
    mean_impact = float(np.mean(impact_values)) if impact_values else 0.0
    impact_variance = (
        float(np.var(impact_values)) if len(impact_values) > 1 else 0.0
    )
    confidence = 1.0 / (1.0 + impact_variance)
    confidence = float(np.clip(confidence, 0.0, 1.0))

    # ── NODE EXPLANATIONS ──
    max_impact_val = max([abs(v) for v in impacts.values()] + [0.001])
    node_explanations: Dict[str, NodeExplanation] = {}

    for node in nodes:
        node_id = node["id"]
        impact = impacts[node_id]
        normalized_impact = impact / max_impact_val
        layer = node.get("layer", "geography")

        # Incoming edges
        incoming = []
        for src_id, edge in incoming_adj.get(node_id, []):
            src_node = node_map[src_id]
            src_impact = impacts[src_id]
            polarity = edge.get("polarity", 1)
            contribution = edge["weight"] * polarity * src_impact * node.get("sensitivity", 0.5)

            if abs(contribution) > 0.005:
                incoming.append({
                    "from": src_id,
                    "fromLabel": src_node.get("labelAr", src_node.get("label", src_id)),
                    "weight": edge["weight"],
                    "polarity": polarity,
                    "contribution": contribution,
                })

        incoming.sort(key=lambda x: abs(x["contribution"]), reverse=True)
        incoming = incoming[:3]

        # Outgoing edges
        outgoing = []
        for tgt_id, edge in outgoing_adj.get(node_id, []):
            tgt_node = node_map[tgt_id]
            polarity = edge.get("polarity", 1)
            outgoing.append({
                "to": tgt_id,
                "toLabel": tgt_node.get("labelAr", tgt_node.get("label", tgt_id)),
                "weight": edge["weight"],
                "polarity": polarity,
            })

        # Build explanations
        node_label = node.get("label", node_id)
        node_label_ar = node.get("labelAr", node_label)
        layer_label = LAYER_LABELS.get(layer, {}).get("en", layer)
        layer_label_ar = LAYER_LABELS.get(layer, {}).get("ar", layer)
        impact_pct = abs(impact) * 100

        if abs(impact) < 0.01:
            explanation = f"{node_label} is not significantly affected in this scenario."
            explanation_ar = f"{node_label_ar} غير متأثر بشكل ملحوظ في هذا السيناريو."
        else:
            if incoming:
                top_src = incoming[0]
                explanation = (
                    f"{node_label} ({layer_label}) is {impact_pct:.0f}% impacted. "
                    f"Primary driver: {top_src['fromLabel']} (contribution: {top_src['contribution'] * 100:.0f}%). "
                    f"Sensitivity: {node.get('sensitivity', 0.5) * 100:.0f}%. "
                    f"Feeds into {len(outgoing)} downstream node{'s' if len(outgoing) != 1 else ''}."
                )
                explanation_ar = (
                    f"{node_label_ar} ({layer_label_ar}) متأثر بنسبة {impact_pct:.0f}%. "
                    f"المحرك الرئيسي: {top_src['fromLabel']} (مساهمة: {top_src['contribution'] * 100:.0f}%). "
                    f"الحساسية: {node.get('sensitivity', 0.5) * 100:.0f}%. "
                    f"يغذي {len(outgoing)} عقدة{'.' if len(outgoing) == 1 else '.'}"
                )
            else:
                # Shock node
                explanation = (
                    f"{node_label} is a shock origin with {impact_pct:.0f}% direct impact. "
                    f"Feeds into {len(outgoing)} downstream node{'s' if len(outgoing) != 1 else ''}."
                )
                explanation_ar = (
                    f"{node_label_ar} نقطة صدمة أصلية بتأثير مباشر {impact_pct:.0f}%. "
                    f"يغذي {len(outgoing)} عقدة{'.' if len(outgoing) == 1 else '.'}"
                )

        node_explanations[node_id] = NodeExplanation(
            node_id=node_id,
            label=node_label,
            label_ar=node_label_ar,
            layer=layer,
            impact=impact,
            normalized_impact=normalized_impact,
            incoming_edges=incoming,
            outgoing_edges=outgoing,
            explanation=explanation,
            explanation_ar=explanation_ar,
        )

    # Build result
    return PropagationResult(
        node_impacts=impacts,
        propagation_chain=chain,
        affected_sectors=affected_sectors,
        top_drivers=top_drivers,
        total_loss=total_loss,
        confidence=confidence,
        system_energy=system_energy,
        propagation_depth=propagation_depth,
        spread_level=spread_level,
        spread_level_ar=spread_level_ar,
        iteration_snapshots=iteration_snapshots,
        node_explanations=node_explanations,
    )


def result_to_dict(result: PropagationResult) -> Dict[str, Any]:
    """Convert PropagationResult to dict for JSON serialization."""
    return {
        "nodeImpacts": result.node_impacts,
        "propagationChain": [
            {
                "from": step.from_node_id,
                "fromLabel": step.from_node_label,
                "to": step.to_node_id,
                "toLabel": step.to_node_label,
                "weight": step.weight,
                "polarity": step.polarity,
                "impact": step.impact,
                "label": step.label,
                "iteration": step.iteration,
            }
            for step in result.propagation_chain
        ],
        "affectedSectors": [
            {
                "sector": sector.sector,
                "sectorLabel": sector.sector_label,
                "avgImpact": sector.avg_impact,
                "maxImpact": sector.max_impact,
                "nodeCount": sector.node_count,
                "topNode": sector.top_node,
                "color": sector.color,
            }
            for sector in result.affected_sectors
        ],
        "topDrivers": [
            {
                "nodeId": driver.node_id,
                "label": driver.label,
                "impact": driver.impact,
                "layer": driver.layer,
                "outDegree": driver.out_degree,
            }
            for driver in result.top_drivers
        ],
        "totalLoss": result.total_loss,
        "confidence": result.confidence,
        "systemEnergy": result.system_energy,
        "propagationDepth": result.propagation_depth,
        "spreadLevel": result.spread_level,
        "spreadLevelAr": result.spread_level_ar,
        "iterationSnapshots": [
            {
                "iteration": snap.iteration,
                "impacts": snap.impacts,
                "energy": snap.energy,
                "deltaEnergy": snap.delta_energy,
            }
            for snap in result.iteration_snapshots
        ],
        "nodeExplanations": {
            node_id: {
                "nodeId": expl.node_id,
                "label": expl.label,
                "labelAr": expl.label_ar,
                "layer": expl.layer,
                "impact": expl.impact,
                "normalizedImpact": expl.normalized_impact,
                "incomingEdges": expl.incoming_edges,
                "outgoingEdges": expl.outgoing_edges,
                "explanation": expl.explanation,
                "explanationAr": expl.explanation_ar,
            }
            for node_id, expl in result.node_explanations.items()
        },
    }
