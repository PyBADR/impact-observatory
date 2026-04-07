"""Graph Brain Shadow Layer — Graph Query Service.

Provides deterministic graph queries over the GraphStore:
  - find_connected: all entities connected to a node
  - find_upstream: all nodes that influence a target (reverse traversal)
  - find_downstream: all nodes influenced by a source (forward traversal)
  - trace_path: find path(s) between two nodes
  - find_by_relation: find all edges of a given relation type

All queries return typed results. No raw dicts.

Design:
  - Pure functions operating on a GraphStore instance
  - BFS-based traversal with configurable depth limits
  - Deterministic: same store state + same query → same result
  - All paths are weighted (product of edge weights)
"""

from __future__ import annotations

from collections import deque
from typing import Optional

from src.graph_brain.store import GraphStore
from src.graph_brain.types import (
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphPath,
    GraphRelationType,
)


# ── Connected Entities ──────────────────────────────────────────────────────

def find_connected(
    store: GraphStore,
    node_id: str,
    max_depth: int = 3,
    direction: str = "both",
    relation_filter: Optional[set[GraphRelationType]] = None,
    entity_type_filter: Optional[set[GraphEntityType]] = None,
) -> list[GraphNode]:
    """Find all entities connected to a node within max_depth hops.

    Args:
        store: The GraphStore to query.
        node_id: Starting node ID.
        max_depth: Maximum traversal depth.
        direction: "outgoing", "incoming", or "both".
        relation_filter: If set, only traverse edges of these relation types.
        entity_type_filter: If set, only return nodes of these entity types.

    Returns:
        List of connected GraphNodes (excluding the start node).
    """
    if not store.has_node(node_id):
        return []

    visited: set[str] = {node_id}
    queue: deque[tuple[str, int]] = deque([(node_id, 0)])
    results: list[GraphNode] = []

    while queue:
        current_id, depth = queue.popleft()
        if depth >= max_depth:
            continue

        neighbors = _get_adjacent(store, current_id, direction, relation_filter)
        for neighbor_id in neighbors:
            if neighbor_id in visited:
                continue
            visited.add(neighbor_id)

            node = store.get_node(neighbor_id)
            if node is None:
                continue

            if entity_type_filter is None or node.entity_type in entity_type_filter:
                results.append(node)

            queue.append((neighbor_id, depth + 1))

    return results


# ── Upstream Dependencies ───────────────────────────────────────────────────

def find_upstream(
    store: GraphStore,
    node_id: str,
    max_depth: int = 4,
    relation_filter: Optional[set[GraphRelationType]] = None,
) -> list[GraphNode]:
    """Find all upstream nodes that influence a target node.

    Traverses edges in reverse (incoming direction).
    """
    return find_connected(
        store, node_id,
        max_depth=max_depth,
        direction="incoming",
        relation_filter=relation_filter,
    )


# ── Downstream Impact Targets ──────────────────────────────────────────────

def find_downstream(
    store: GraphStore,
    node_id: str,
    max_depth: int = 4,
    relation_filter: Optional[set[GraphRelationType]] = None,
) -> list[GraphNode]:
    """Find all downstream nodes influenced by a source node.

    Traverses edges in forward (outgoing direction).
    """
    return find_connected(
        store, node_id,
        max_depth=max_depth,
        direction="outgoing",
        relation_filter=relation_filter,
    )


# ── Path Tracing ────────────────────────────────────────────────────────────

def trace_paths(
    store: GraphStore,
    start_id: str,
    end_id: str,
    max_depth: int = 5,
    max_paths: int = 10,
    direction: str = "outgoing",
    min_weight: float = 0.0,
) -> list[GraphPath]:
    """Find all paths between two nodes using BFS.

    Args:
        store: The GraphStore to query.
        start_id: Starting node ID.
        end_id: Target node ID.
        max_depth: Maximum path length (number of edges).
        max_paths: Maximum number of paths to return.
        direction: "outgoing" for forward traversal, "incoming" for reverse.
        min_weight: Minimum cumulative weight for a path to be included.

    Returns:
        List of GraphPath instances, sorted by total_weight descending.
    """
    if not store.has_node(start_id) or not store.has_node(end_id):
        return []

    if start_id == end_id:
        node = store.get_node_strict(start_id)
        return [GraphPath(nodes=[node], edges=[], total_weight=1.0)]

    # BFS with path tracking
    # Queue items: (current_node_id, path_node_ids, path_edge_ids, cumulative_weight)
    queue: deque[tuple[str, list[str], list[str], float]] = deque()
    queue.append((start_id, [start_id], [], 1.0))
    found_paths: list[GraphPath] = []

    while queue and len(found_paths) < max_paths:
        current_id, path_nids, path_eids, cum_weight = queue.popleft()

        if len(path_eids) >= max_depth:
            continue

        edges = (
            store.get_outgoing_edges(current_id)
            if direction == "outgoing"
            else store.get_incoming_edges(current_id)
        )

        for edge in edges:
            next_id = edge.target_id if direction == "outgoing" else edge.source_id

            # Avoid cycles within this path
            if next_id in path_nids:
                continue

            new_weight = cum_weight * edge.weight
            new_nids = path_nids + [next_id]
            new_eids = path_eids + [edge.edge_id]

            if next_id == end_id:
                # Found a path
                if new_weight >= min_weight:
                    path_nodes = [store.get_node_strict(nid) for nid in new_nids]
                    path_edges = [store.get_edge(eid) for eid in new_eids if store.get_edge(eid)]
                    found_paths.append(GraphPath(
                        nodes=path_nodes,
                        edges=path_edges,
                        total_weight=round(new_weight, 6),
                    ))
            else:
                queue.append((next_id, new_nids, new_eids, new_weight))

    # Sort by weight descending (strongest path first)
    found_paths.sort(key=lambda p: p.total_weight, reverse=True)
    return found_paths


# ── Relation Query ──────────────────────────────────────────────────────────

def find_by_relation(
    store: GraphStore,
    relation_type: GraphRelationType,
) -> list[GraphEdge]:
    """Find all edges of a given relation type."""
    return [
        e for e in store.all_edges()
        if e.relation_type == relation_type
    ]


# ── Subgraph Extraction ────────────────────────────────────────────────────

def extract_subgraph(
    store: GraphStore,
    root_id: str,
    max_depth: int = 3,
    direction: str = "outgoing",
) -> tuple[list[GraphNode], list[GraphEdge]]:
    """Extract a subgraph rooted at a node within max_depth hops.

    Returns:
        Tuple of (nodes, edges) in the subgraph.
    """
    if not store.has_node(root_id):
        return [], []

    visited_nodes: set[str] = {root_id}
    visited_edges: set[str] = set()
    queue: deque[tuple[str, int]] = deque([(root_id, 0)])

    while queue:
        current_id, depth = queue.popleft()
        if depth >= max_depth:
            continue

        edges = (
            store.get_outgoing_edges(current_id)
            if direction == "outgoing"
            else store.get_incoming_edges(current_id)
            if direction == "incoming"
            else store.get_outgoing_edges(current_id) + store.get_incoming_edges(current_id)
        )

        for edge in edges:
            visited_edges.add(edge.edge_id)
            next_id = (
                edge.target_id
                if edge.source_id == current_id
                else edge.source_id
            )
            if next_id not in visited_nodes:
                visited_nodes.add(next_id)
                queue.append((next_id, depth + 1))

    nodes = [store.get_node_strict(nid) for nid in visited_nodes]
    edges = [store.get_edge(eid) for eid in visited_edges if store.get_edge(eid)]

    return nodes, edges


# ── Internal Helpers ────────────────────────────────────────────────────────

def _get_adjacent(
    store: GraphStore,
    node_id: str,
    direction: str,
    relation_filter: Optional[set[GraphRelationType]],
) -> list[str]:
    """Get adjacent node IDs respecting direction and relation filter."""
    neighbor_ids: list[str] = []

    if direction in ("outgoing", "both"):
        for edge in store.get_outgoing_edges(node_id):
            if relation_filter and edge.relation_type not in relation_filter:
                continue
            neighbor_ids.append(edge.target_id)

    if direction in ("incoming", "both"):
        for edge in store.get_incoming_edges(node_id):
            if relation_filter and edge.relation_type not in relation_filter:
                continue
            neighbor_ids.append(edge.source_id)

    return neighbor_ids
