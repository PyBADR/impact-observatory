"""Graph Brain Shadow Layer — Explainability Engine.

Produces structured GraphExplanation outputs from graph queries.
Every explanation includes:
  - start/end nodes
  - paths traversed
  - all nodes and edges visited
  - reasoning summary (human-readable)
  - confidence (minimum across traversed edges)
  - provenance (aggregated source references)
  - audit hash (SHA-256)

Design:
  - Pure functions: deterministic output from store + query params
  - Reasoning summaries are constructed from graph structure, not LLM-generated
  - Confidence is conservatively computed (minimum edge confidence on best path)
"""

from __future__ import annotations

from src.graph_brain.query import (
    extract_subgraph,
    find_downstream,
    find_upstream,
    trace_paths,
)
from src.graph_brain.store import GraphStore
from src.graph_brain.types import (
    CONFIDENCE_WEIGHTS,
    GraphConfidence,
    GraphEdge,
    GraphExplanation,
    GraphNode,
    GraphPath,
    GraphSourceRef,
)


# ── Path Explanation ────────────────────────────────────────────────────────

def explain_path(
    store: GraphStore,
    start_id: str,
    end_id: str,
    max_depth: int = 5,
    max_paths: int = 5,
) -> GraphExplanation:
    """Explain the relationship between two nodes by tracing paths.

    Returns a GraphExplanation with all paths, traversed elements,
    and a human-readable reasoning summary.
    """
    start_node = store.get_node_strict(start_id)
    end_node = store.get_node_strict(end_id)

    paths = trace_paths(store, start_id, end_id, max_depth=max_depth, max_paths=max_paths)

    # Collect unique traversed nodes and edges
    all_nodes: dict[str, GraphNode] = {}
    all_edges: dict[str, GraphEdge] = {}
    all_refs: list[GraphSourceRef] = []

    for path in paths:
        for node in path.nodes:
            all_nodes[node.node_id] = node
            all_refs.extend(node.source_refs)
        for edge in path.edges:
            all_edges[edge.edge_id] = edge
            all_refs.extend(edge.source_refs)

    # Compute confidence (minimum edge confidence on best path)
    confidence = _compute_path_confidence(paths)

    # Build reasoning summary
    reasoning = _build_path_reasoning(start_node, end_node, paths)

    return GraphExplanation(
        query_description=f"Explain relationship: {start_node.label} → {end_node.label}",
        start_node=start_node,
        end_node=end_node,
        paths=paths,
        nodes_traversed=list(all_nodes.values()),
        edges_traversed=list(all_edges.values()),
        reasoning_summary=reasoning,
        confidence=confidence,
        provenance=_dedupe_refs(all_refs),
    )


# ── Impact Explanation ──────────────────────────────────────────────────────

def explain_impact(
    store: GraphStore,
    source_id: str,
    max_depth: int = 4,
) -> GraphExplanation:
    """Explain the downstream impact of a node.

    Traces all downstream entities and builds an explanation
    of how impact propagates from the source.
    """
    source_node = store.get_node_strict(source_id)
    downstream_nodes = find_downstream(store, source_id, max_depth=max_depth)

    # Build paths to each downstream node
    all_paths: list[GraphPath] = []
    all_nodes_map: dict[str, GraphNode] = {source_id: source_node}
    all_edges_map: dict[str, GraphEdge] = {}
    all_refs: list[GraphSourceRef] = list(source_node.source_refs)

    for target_node in downstream_nodes:
        paths = trace_paths(
            store, source_id, target_node.node_id,
            max_depth=max_depth, max_paths=3,
        )
        all_paths.extend(paths)
        for path in paths:
            for node in path.nodes:
                all_nodes_map[node.node_id] = node
                all_refs.extend(node.source_refs)
            for edge in path.edges:
                all_edges_map[edge.edge_id] = edge
                all_refs.extend(edge.source_refs)

    confidence = _compute_path_confidence(all_paths)

    # Build impact reasoning
    if downstream_nodes:
        targets = ", ".join(n.label for n in downstream_nodes[:10])
        suffix = f" (and {len(downstream_nodes) - 10} more)" if len(downstream_nodes) > 10 else ""
        reasoning = (
            f"'{source_node.label}' ({source_node.entity_type.value}) has downstream impact "
            f"on {len(downstream_nodes)} entities within {max_depth} hops: {targets}{suffix}. "
            f"Found {len(all_paths)} propagation paths. "
            f"Strongest path weight: {all_paths[0].total_weight:.4f}."
            if all_paths else
            f"'{source_node.label}' has {len(downstream_nodes)} downstream entities but no direct paths found."
        )
    else:
        reasoning = (
            f"'{source_node.label}' ({source_node.entity_type.value}) has no downstream "
            f"impact within {max_depth} hops."
        )

    return GraphExplanation(
        query_description=f"Downstream impact of: {source_node.label}",
        start_node=source_node,
        end_node=None,
        paths=all_paths,
        nodes_traversed=list(all_nodes_map.values()),
        edges_traversed=list(all_edges_map.values()),
        reasoning_summary=reasoning,
        confidence=confidence,
        provenance=_dedupe_refs(all_refs),
    )


# ── Dependency Explanation ──────────────────────────────────────────────────

def explain_dependencies(
    store: GraphStore,
    target_id: str,
    max_depth: int = 4,
) -> GraphExplanation:
    """Explain what a node depends on (upstream analysis).

    Traces all upstream entities and builds an explanation
    of what influences the target.
    """
    target_node = store.get_node_strict(target_id)
    upstream_nodes = find_upstream(store, target_id, max_depth=max_depth)

    all_paths: list[GraphPath] = []
    all_nodes_map: dict[str, GraphNode] = {target_id: target_node}
    all_edges_map: dict[str, GraphEdge] = {}
    all_refs: list[GraphSourceRef] = list(target_node.source_refs)

    for source_node in upstream_nodes:
        paths = trace_paths(
            store, source_node.node_id, target_id,
            max_depth=max_depth, max_paths=3,
        )
        all_paths.extend(paths)
        for path in paths:
            for node in path.nodes:
                all_nodes_map[node.node_id] = node
                all_refs.extend(node.source_refs)
            for edge in path.edges:
                all_edges_map[edge.edge_id] = edge
                all_refs.extend(edge.source_refs)

    confidence = _compute_path_confidence(all_paths)

    if upstream_nodes:
        sources = ", ".join(n.label for n in upstream_nodes[:10])
        suffix = f" (and {len(upstream_nodes) - 10} more)" if len(upstream_nodes) > 10 else ""
        reasoning = (
            f"'{target_node.label}' ({target_node.entity_type.value}) depends on "
            f"{len(upstream_nodes)} upstream entities within {max_depth} hops: {sources}{suffix}. "
            f"Found {len(all_paths)} dependency paths."
        )
    else:
        reasoning = (
            f"'{target_node.label}' ({target_node.entity_type.value}) has no upstream "
            f"dependencies within {max_depth} hops."
        )

    return GraphExplanation(
        query_description=f"Dependencies of: {target_node.label}",
        start_node=target_node,
        end_node=None,
        paths=all_paths,
        nodes_traversed=list(all_nodes_map.values()),
        edges_traversed=list(all_edges_map.values()),
        reasoning_summary=reasoning,
        confidence=confidence,
        provenance=_dedupe_refs(all_refs),
    )


# ── Internal Helpers ────────────────────────────────────────────────────────

def _compute_path_confidence(paths: list[GraphPath]) -> GraphConfidence:
    """Compute overall confidence from paths.

    Strategy: minimum edge confidence on the strongest (first) path.
    If no paths, returns SPECULATIVE.
    """
    if not paths:
        return GraphConfidence.SPECULATIVE

    best_path = paths[0]  # already sorted by weight desc
    if not best_path.edges:
        return GraphConfidence.DEFINITIVE

    min_weight = min(
        CONFIDENCE_WEIGHTS.get(e.confidence, 0.5)
        for e in best_path.edges
    )

    # Map back to confidence level
    for level in [
        GraphConfidence.DEFINITIVE,
        GraphConfidence.HIGH,
        GraphConfidence.MODERATE,
        GraphConfidence.LOW,
        GraphConfidence.SPECULATIVE,
    ]:
        if min_weight >= CONFIDENCE_WEIGHTS[level]:
            return level

    return GraphConfidence.SPECULATIVE


def _build_path_reasoning(
    start: GraphNode,
    end: GraphNode,
    paths: list[GraphPath],
) -> str:
    """Build human-readable reasoning from traced paths."""
    if not paths:
        return (
            f"No paths found between '{start.label}' ({start.entity_type.value}) "
            f"and '{end.label}' ({end.entity_type.value})."
        )

    best = paths[0]
    hops = best.total_hops
    weight = best.total_weight

    if hops == 0:
        return f"'{start.label}' and '{end.label}' are the same node."

    # Build step-by-step description
    steps: list[str] = []
    for edge in best.edges:
        source_node_label = start.label  # fallback
        target_node_label = end.label
        for n in best.nodes:
            if n.node_id == edge.source_id:
                source_node_label = n.label
            if n.node_id == edge.target_id:
                target_node_label = n.label
        steps.append(
            f"{source_node_label} --[{edge.relation_type.value}, "
            f"weight={edge.weight:.2f}]--> {target_node_label}"
        )

    path_desc = "; ".join(steps)

    return (
        f"'{start.label}' ({start.entity_type.value}) is connected to "
        f"'{end.label}' ({end.entity_type.value}) via {hops} hop(s) "
        f"with cumulative weight {weight:.4f}. "
        f"Best path: {path_desc}. "
        f"Total paths found: {len(paths)}."
    )


def _dedupe_refs(refs: list[GraphSourceRef]) -> list[GraphSourceRef]:
    """Deduplicate source references by (source_type, source_id)."""
    seen: set[tuple[str, str]] = set()
    deduped: list[GraphSourceRef] = []
    for ref in refs:
        key = (ref.source_type, ref.source_id)
        if key not in seen:
            seen.add(key)
            deduped.append(ref)
    return deduped
