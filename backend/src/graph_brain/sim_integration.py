"""Graph Brain Integration Pack A — Simulation Engine Bridge.

Integrates Graph Brain into the 17-stage simulation pipeline
(risk_models.py, explainability.py) without replacing existing logic.

Architecture:
  - Every function is fail-safe: exception → log + return fallback
  - Feature-flagged via SIM_GRAPH_* module-level switches
  - Graph data is ADDITIVE — it enriches, never replaces, existing logic
  - The simulation engine pipeline remains deterministic

Integration points:
  1. ensure_sim_graph_populated  — populate graph with GCC_NODES + GCC_ADJACENCY
  2. graph_cross_sector_deps     — dynamic cross-sector deps from graph edges
  3. graph_enriched_adjacency    — add graph-discovered edges to adjacency
  4. graph_explain_causal_step   — explain a causal chain step via graph paths
  5. build_graph_explanation     — full graph explanation for a simulation run

Design rules:
  - NEVER modify risk_models.py or explainability.py function signatures
  - NEVER block simulation if graph is unavailable
  - All enrichment functions accept Optional[GraphStore] and return
    sensible defaults when store is None
"""

from __future__ import annotations

import logging
from typing import Optional

from src.graph_brain.store import GraphStore, DuplicateNodeError, DanglingEdgeError
from src.graph_brain.types import (
    CONFIDENCE_WEIGHTS,
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphPath,
    GraphRelationType,
    GraphSourceRef,
)
from src.graph_brain.query import find_downstream, trace_paths

logger = logging.getLogger(__name__)

__all__ = [
    "SIM_GRAPH_ENABLED",
    "ensure_sim_graph_populated",
    "graph_cross_sector_deps",
    "graph_enriched_adjacency",
    "graph_explain_causal_step",
    "build_graph_explanation",
]


# ══════════════════════════════════════════════════════════════════════════════
# Feature Flags
# ══════════════════════════════════════════════════════════════════════════════

SIM_GRAPH_ENABLED: bool = True            # Master switch
SIM_GRAPH_CAUSAL_ENRICHMENT: bool = True  # Enrich _CROSS_SECTOR_DEPS
SIM_GRAPH_PROPAGATION_ENRICHMENT: bool = True  # Enrich adjacency matrix
SIM_GRAPH_EXPLANATION_ENRICHMENT: bool = True   # Enrich causal chain


def set_sim_graph_enabled(enabled: bool) -> None:
    """Set master switch for simulation graph integration."""
    global SIM_GRAPH_ENABLED
    SIM_GRAPH_ENABLED = enabled


def is_sim_graph_active(feature: str = "master") -> bool:
    """Check if a specific simulation graph feature is active."""
    if not SIM_GRAPH_ENABLED:
        return False
    flag_map = {
        "master": True,
        "causal": SIM_GRAPH_CAUSAL_ENRICHMENT,
        "propagation": SIM_GRAPH_PROPAGATION_ENRICHMENT,
        "explanation": SIM_GRAPH_EXPLANATION_ENRICHMENT,
    }
    return flag_map.get(feature, False)


# ══════════════════════════════════════════════════════════════════════════════
# 1. Graph Population — Ingest GCC_NODES + GCC_ADJACENCY
# ══════════════════════════════════════════════════════════════════════════════

def ensure_sim_graph_populated(
    store: GraphStore,
    gcc_nodes: list[dict],
    adjacency: dict[str, list[str]],
) -> dict:
    """Populate the GraphStore with simulation nodes and edges.

    Idempotent: existing nodes/edges are skipped (not overwritten).

    Args:
        store: Target GraphStore.
        gcc_nodes: GCC_NODES list of dicts with id, label, sector, etc.
        adjacency: GCC_ADJACENCY dict of node_id → [neighbor_ids].

    Returns:
        Summary dict: {nodes_added, edges_added, nodes_skipped, edges_skipped}
    """
    stats = {
        "nodes_added": 0,
        "nodes_skipped": 0,
        "edges_added": 0,
        "edges_skipped": 0,
    }

    # Map sector strings to entity types
    SECTOR_TO_ENTITY: dict[str, GraphEntityType] = {
        "maritime": GraphEntityType.INFRASTRUCTURE,
        "energy": GraphEntityType.INFRASTRUCTURE,
        "banking": GraphEntityType.ORGANIZATION,
        "insurance": GraphEntityType.ORGANIZATION,
        "fintech": GraphEntityType.ORGANIZATION,
        "logistics": GraphEntityType.INFRASTRUCTURE,
        "infrastructure": GraphEntityType.INFRASTRUCTURE,
        "government": GraphEntityType.REGULATOR,
        "healthcare": GraphEntityType.ORGANIZATION,
    }

    # ── Add nodes ──────────────────────────────────────────────────────────
    for node_data in gcc_nodes:
        node_id = node_data["id"]
        if store.has_node(node_id):
            stats["nodes_skipped"] += 1
            continue

        sector = node_data.get("sector", "infrastructure")
        entity_type = SECTOR_TO_ENTITY.get(sector, GraphEntityType.INFRASTRUCTURE)

        try:
            graph_node = GraphNode(
                node_id=node_id,
                entity_type=entity_type,
                label=node_data.get("label", node_id),
                label_ar=node_data.get("label_ar"),
                confidence=GraphConfidence.DEFINITIVE,
                properties={
                    "sector": sector,
                    "capacity": node_data.get("capacity", 0),
                    "current_load": node_data.get("current_load", 0),
                    "criticality": node_data.get("criticality", 0.5),
                    "redundancy": node_data.get("redundancy", 0.5),
                    "lat": node_data.get("lat"),
                    "lng": node_data.get("lng"),
                },
                source_refs=[GraphSourceRef(
                    source_type="gcc_node_registry",
                    source_id=node_id,
                )],
            )
            store.add_node(graph_node)
            stats["nodes_added"] += 1
        except Exception as e:
            logger.debug("Skipping node %s: %s", node_id, e)
            stats["nodes_skipped"] += 1

    # ── Add edges from adjacency ───────────────────────────────────────────
    for source_id, neighbors in adjacency.items():
        for target_id in neighbors:
            edge_id = f"{source_id}--adjacent-->{target_id}"
            if store.has_edge(edge_id):
                stats["edges_skipped"] += 1
                continue

            if not store.has_node(source_id) or not store.has_node(target_id):
                stats["edges_skipped"] += 1
                continue

            # Compute edge weight from criticality of target
            target_node = store.get_node(target_id)
            weight = 0.7  # default
            if target_node and "criticality" in target_node.properties:
                weight = round(
                    min(1.0, 0.5 + target_node.properties["criticality"] * 0.4),
                    4,
                )

            try:
                edge = GraphEdge(
                    edge_id=edge_id,
                    source_id=source_id,
                    target_id=target_id,
                    relation_type=GraphRelationType.PROPAGATES_TO,
                    label=f"{source_id} propagates to {target_id}",
                    weight=weight,
                    confidence=GraphConfidence.HIGH,
                    source_refs=[GraphSourceRef(
                        source_type="gcc_adjacency",
                        source_id=edge_id,
                    )],
                )
                store.add_edge(edge)
                stats["edges_added"] += 1
            except Exception as e:
                logger.debug("Skipping edge %s: %s", edge_id, e)
                stats["edges_skipped"] += 1

    logger.info(
        "Sim graph populated: %d nodes (+%d skipped), %d edges (+%d skipped)",
        stats["nodes_added"], stats["nodes_skipped"],
        stats["edges_added"], stats["edges_skipped"],
    )
    return stats


# ══════════════════════════════════════════════════════════════════════════════
# 2. Causal Enrichment — Dynamic Cross-Sector Dependencies
# ══════════════════════════════════════════════════════════════════════════════

def graph_cross_sector_deps(
    store: Optional[GraphStore],
    shocked_sectors: set[str],
    static_deps: dict[str, list[str]],
    max_depth: int = 2,
) -> dict[str, list[str]]:
    """Compute cross-sector dependencies using graph + static fallback.

    For each shocked sector, finds connected sectors via graph traversal.
    Merges graph-discovered deps with static _CROSS_SECTOR_DEPS.
    If graph is unavailable, returns static_deps unchanged.

    Args:
        store: GraphStore or None (fallback to static).
        shocked_sectors: Set of sector names that are directly shocked.
        static_deps: The existing _CROSS_SECTOR_DEPS dict.
        max_depth: Max graph traversal depth.

    Returns:
        Merged dependency dict: sector → [dependent_sectors].
    """
    if not is_sim_graph_active("causal") or store is None:
        return static_deps

    try:
        merged = {k: list(v) for k, v in static_deps.items()}  # deep copy

        for sector in shocked_sectors:
            # Find all nodes in this sector
            sector_node_ids = [
                n.node_id for n in store.all_nodes()
                if n.properties.get("sector") == sector
            ]

            graph_deps: set[str] = set()
            for node_id in sector_node_ids:
                downstream = find_downstream(
                    store, node_id,
                    max_depth=max_depth,
                    relation_filter={
                        GraphRelationType.PROPAGATES_TO,
                        GraphRelationType.AFFECTS,
                        GraphRelationType.DEPENDS_ON,
                    },
                )
                for target in downstream:
                    target_sector = target.properties.get("sector")
                    if target_sector and target_sector != sector:
                        graph_deps.add(target_sector)

            # Merge: union of static + graph-discovered
            existing = set(merged.get(sector, []))
            new_deps = graph_deps - existing
            if new_deps:
                merged[sector] = list(existing | graph_deps)
                logger.debug(
                    "Graph added cross-sector deps for %s: %s",
                    sector, new_deps,
                )

        return merged

    except Exception as e:
        logger.warning("Graph cross-sector deps failed, using static: %s", e)
        return static_deps


# ══════════════════════════════════════════════════════════════════════════════
# 3. Propagation Enrichment — Graph-Discovered Adjacency Edges
# ══════════════════════════════════════════════════════════════════════════════

def graph_enriched_adjacency(
    store: Optional[GraphStore],
    static_adjacency: dict[str, list[str]],
) -> dict[str, list[str]]:
    """Enrich the static adjacency with graph-discovered edges.

    Adds any edges in the GraphStore that are not in static_adjacency.
    Does NOT remove existing edges.

    Args:
        store: GraphStore or None.
        static_adjacency: The GCC_ADJACENCY dict.

    Returns:
        Enriched adjacency dict (new copy, never mutates input).
    """
    if not is_sim_graph_active("propagation") or store is None:
        return static_adjacency

    try:
        enriched = {k: list(v) for k, v in static_adjacency.items()}

        for edge in store.all_edges():
            if edge.relation_type not in (
                GraphRelationType.PROPAGATES_TO,
                GraphRelationType.AFFECTS,
                GraphRelationType.DEPENDS_ON,
            ):
                continue

            source = edge.source_id
            target = edge.target_id

            # Only add edges between known simulation nodes
            if source not in enriched:
                continue

            if target not in enriched[source]:
                # Only add edges with sufficient confidence
                conf_weight = CONFIDENCE_WEIGHTS.get(edge.confidence, 0.5)
                if conf_weight >= 0.45:  # LOW or above
                    enriched[source].append(target)
                    logger.debug(
                        "Graph added adjacency edge: %s → %s (conf=%s)",
                        source, target, edge.confidence.value,
                    )

        return enriched

    except Exception as e:
        logger.warning("Graph adjacency enrichment failed, using static: %s", e)
        return static_adjacency


# ══════════════════════════════════════════════════════════════════════════════
# 4. Explanation Enrichment — Graph-Backed Causal Chain Steps
# ══════════════════════════════════════════════════════════════════════════════

def graph_explain_causal_step(
    store: Optional[GraphStore],
    source_id: str,
    target_id: str,
    max_depth: int = 4,
) -> Optional[dict]:
    """Explain a single causal chain hop using graph paths.

    Returns a dict with graph_path, relationships, and reasoning_chain
    if graph evidence exists. Returns None otherwise.

    Args:
        store: GraphStore or None.
        source_id: Source node ID.
        target_id: Target node ID.
        max_depth: Max traversal depth.

    Returns:
        Dict with graph_path, relationships, reasoning_chain, confidence
        or None if no graph evidence.
    """
    if not is_sim_graph_active("explanation") or store is None:
        return None

    try:
        if not store.has_node(source_id) or not store.has_node(target_id):
            return None

        paths = trace_paths(
            store, source_id, target_id,
            max_depth=max_depth, max_paths=3,
        )
        if not paths:
            return None

        best = paths[0]
        relationships = []
        reasoning_chain = []

        for edge in best.edges:
            source_node = store.get_node(edge.source_id)
            target_node = store.get_node(edge.target_id)
            relationships.append({
                "source": edge.source_id,
                "target": edge.target_id,
                "relation": edge.relation_type.value,
                "weight": edge.weight,
                "confidence": edge.confidence.value,
                "label": edge.label,
            })
            reasoning_chain.append(
                f"{source_node.label if source_node else edge.source_id} "
                f"→[{edge.relation_type.value}]→ "
                f"{target_node.label if target_node else edge.target_id}"
            )

        # Minimum edge confidence
        min_conf = GraphConfidence.MODERATE
        if best.edges:
            min_w = min(
                CONFIDENCE_WEIGHTS.get(e.confidence, 0.5)
                for e in best.edges
            )
            for level in [
                GraphConfidence.DEFINITIVE, GraphConfidence.HIGH,
                GraphConfidence.MODERATE, GraphConfidence.LOW,
                GraphConfidence.SPECULATIVE,
            ]:
                if min_w >= CONFIDENCE_WEIGHTS[level]:
                    min_conf = level
                    break

        return {
            "graph_path": best.path_description,
            "path_weight": best.total_weight,
            "path_hops": best.total_hops,
            "relationships": relationships,
            "reasoning_chain": reasoning_chain,
            "confidence": min_conf.value,
            "paths_found": len(paths),
        }

    except Exception as e:
        logger.debug("Graph explain step %s→%s failed: %s", source_id, target_id, e)
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 5. Full Run Explanation — Graph-Backed Simulation Summary
# ══════════════════════════════════════════════════════════════════════════════

def build_graph_explanation(
    store: Optional[GraphStore],
    shock_nodes: list[str],
    propagation: list[dict],
    causal_chain: list[dict],
) -> Optional[dict]:
    """Build a full graph explanation for a simulation run.

    Returns a summary with graph paths, relationships, and reasoning
    for the entire causal chain. Returns None if graph unavailable.

    Args:
        store: GraphStore or None.
        shock_nodes: List of shock origin node IDs.
        propagation: Propagation results from compute_propagation.
        causal_chain: Causal chain from build_causal_chain.

    Returns:
        Dict with graph_paths_used, total_relationships,
        reasoning_summary, confidence, or None.
    """
    if not is_sim_graph_active("explanation") or store is None:
        return None

    try:
        step_explanations = []
        total_relationships = 0
        all_confidences = []

        # Explain each consecutive pair in the causal chain
        prev_id = None
        for step in causal_chain:
            entity_id = step.get("entity_id", "")
            # Skip synthetic sub-step IDs
            if "_sub" in entity_id:
                continue

            if prev_id is not None and prev_id != entity_id:
                explanation = graph_explain_causal_step(
                    store, prev_id, entity_id,
                )
                if explanation is not None:
                    step_explanations.append({
                        "from": prev_id,
                        "to": entity_id,
                        **explanation,
                    })
                    total_relationships += len(explanation["relationships"])
                    all_confidences.append(explanation["confidence"])

            prev_id = entity_id

        if not step_explanations:
            return None

        # Overall confidence = most common confidence level
        conf_counts: dict[str, int] = {}
        for c in all_confidences:
            conf_counts[c] = conf_counts.get(c, 0) + 1
        overall_conf = max(conf_counts, key=conf_counts.get) if conf_counts else "moderate"

        return {
            "graph_paths_used": len(step_explanations),
            "total_relationships": total_relationships,
            "step_explanations": step_explanations,
            "confidence": overall_conf,
            "reasoning_summary": (
                f"Graph Brain traced {len(step_explanations)} causal hops "
                f"with {total_relationships} total relationships. "
                f"Overall confidence: {overall_conf}."
            ),
        }

    except Exception as e:
        logger.warning("Graph full explanation failed: %s", e)
        return None
