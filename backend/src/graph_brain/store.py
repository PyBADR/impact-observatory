"""Graph Brain Shadow Layer — In-Memory Graph Store.

Lightweight, traversal-ready graph store. No external dependencies.
Stores GraphNode and GraphEdge instances with O(1) lookup and
adjacency-list traversal.

Design:
  - Thread-safe for single-writer / multi-reader (Python GIL)
  - Deterministic iteration order (insertion order)
  - Supports add/get/query for nodes and edges
  - Forward adjacency (outgoing) and reverse adjacency (incoming)
  - Snapshot-safe: can export full state for audit/persistence

Invariants:
  - No duplicate node_id
  - No duplicate edge_id
  - Edge source_id and target_id must reference existing nodes
  - No self-loop edges (enforced by GraphEdge validator)
"""

from __future__ import annotations

import logging
from collections import defaultdict
from typing import Optional

from src.graph_brain.types import (
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphRelationType,
)

logger = logging.getLogger(__name__)


class GraphStoreError(Exception):
    """Base error for graph store operations."""


class NodeNotFoundError(GraphStoreError):
    """Raised when a referenced node does not exist."""


class DuplicateNodeError(GraphStoreError):
    """Raised when inserting a node with an existing node_id."""


class DuplicateEdgeError(GraphStoreError):
    """Raised when inserting an edge with an existing edge_id."""


class DanglingEdgeError(GraphStoreError):
    """Raised when an edge references a non-existent node."""


class GraphStore:
    """In-memory knowledge graph store.

    Provides O(1) node/edge lookup and O(degree) adjacency traversal.
    """

    def __init__(self) -> None:
        # Primary storage
        self._nodes: dict[str, GraphNode] = {}
        self._edges: dict[str, GraphEdge] = {}

        # Adjacency indices
        self._outgoing: dict[str, list[str]] = defaultdict(list)  # node_id → [edge_id]
        self._incoming: dict[str, list[str]] = defaultdict(list)  # node_id → [edge_id]

        # Secondary indices
        self._nodes_by_type: dict[GraphEntityType, list[str]] = defaultdict(list)

    # ── Node Operations ─────────────────────────────────────────────────────

    def add_node(self, node: GraphNode, *, upsert: bool = False) -> GraphNode:
        """Add a node to the store.

        Args:
            node: The GraphNode to add.
            upsert: If True, overwrite existing node with same node_id.
                    If False (default), raise DuplicateNodeError.

        Returns:
            The stored node.
        """
        if node.node_id in self._nodes:
            if not upsert:
                raise DuplicateNodeError(
                    f"Node '{node.node_id}' already exists. Use upsert=True to overwrite."
                )
            # Remove from type index before overwrite
            old = self._nodes[node.node_id]
            if old.entity_type in self._nodes_by_type:
                try:
                    self._nodes_by_type[old.entity_type].remove(node.node_id)
                except ValueError:
                    pass

        self._nodes[node.node_id] = node
        self._nodes_by_type[node.entity_type].append(node.node_id)
        return node

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Get a node by ID. Returns None if not found."""
        return self._nodes.get(node_id)

    def get_node_strict(self, node_id: str) -> GraphNode:
        """Get a node by ID. Raises NodeNotFoundError if not found."""
        node = self._nodes.get(node_id)
        if node is None:
            raise NodeNotFoundError(f"Node '{node_id}' not found")
        return node

    def has_node(self, node_id: str) -> bool:
        """Check if a node exists."""
        return node_id in self._nodes

    def get_nodes_by_type(self, entity_type: GraphEntityType) -> list[GraphNode]:
        """Get all nodes of a given entity type."""
        return [
            self._nodes[nid]
            for nid in self._nodes_by_type.get(entity_type, [])
            if nid in self._nodes
        ]

    def all_nodes(self) -> list[GraphNode]:
        """Return all nodes in insertion order."""
        return list(self._nodes.values())

    @property
    def node_count(self) -> int:
        return len(self._nodes)

    # ── Edge Operations ─────────────────────────────────────────────────────

    def add_edge(self, edge: GraphEdge, *, upsert: bool = False) -> GraphEdge:
        """Add an edge to the store.

        Both source_id and target_id must reference existing nodes.

        Args:
            edge: The GraphEdge to add.
            upsert: If True, overwrite existing edge with same edge_id.

        Returns:
            The stored edge.
        """
        # Validate endpoints exist
        if not self.has_node(edge.source_id):
            raise DanglingEdgeError(
                f"Edge '{edge.edge_id}' source '{edge.source_id}' not found in store"
            )
        if not self.has_node(edge.target_id):
            raise DanglingEdgeError(
                f"Edge '{edge.edge_id}' target '{edge.target_id}' not found in store"
            )

        if edge.edge_id in self._edges:
            if not upsert:
                raise DuplicateEdgeError(
                    f"Edge '{edge.edge_id}' already exists. Use upsert=True to overwrite."
                )
            # Remove from adjacency before overwrite
            old = self._edges[edge.edge_id]
            self._remove_from_adjacency(old)

        self._edges[edge.edge_id] = edge
        self._outgoing[edge.source_id].append(edge.edge_id)
        self._incoming[edge.target_id].append(edge.edge_id)
        return edge

    def get_edge(self, edge_id: str) -> Optional[GraphEdge]:
        """Get an edge by ID. Returns None if not found."""
        return self._edges.get(edge_id)

    def has_edge(self, edge_id: str) -> bool:
        """Check if an edge exists."""
        return edge_id in self._edges

    def all_edges(self) -> list[GraphEdge]:
        """Return all edges in insertion order."""
        return list(self._edges.values())

    @property
    def edge_count(self) -> int:
        return len(self._edges)

    # ── Adjacency Queries ───────────────────────────────────────────────────

    def get_outgoing_edges(self, node_id: str) -> list[GraphEdge]:
        """Get all edges originating from a node."""
        return [
            self._edges[eid]
            for eid in self._outgoing.get(node_id, [])
            if eid in self._edges
        ]

    def get_incoming_edges(self, node_id: str) -> list[GraphEdge]:
        """Get all edges pointing to a node."""
        return [
            self._edges[eid]
            for eid in self._incoming.get(node_id, [])
            if eid in self._edges
        ]

    def get_neighbors(
        self,
        node_id: str,
        direction: str = "both",
    ) -> list[GraphNode]:
        """Get neighboring nodes.

        Args:
            node_id: Source node.
            direction: "outgoing", "incoming", or "both".

        Returns:
            List of unique neighboring nodes.
        """
        neighbor_ids: set[str] = set()

        if direction in ("outgoing", "both"):
            for edge in self.get_outgoing_edges(node_id):
                neighbor_ids.add(edge.target_id)

        if direction in ("incoming", "both"):
            for edge in self.get_incoming_edges(node_id):
                neighbor_ids.add(edge.source_id)

        return [self._nodes[nid] for nid in neighbor_ids if nid in self._nodes]

    def get_edges_between(
        self,
        source_id: str,
        target_id: str,
    ) -> list[GraphEdge]:
        """Get all edges from source to target."""
        return [
            e for e in self.get_outgoing_edges(source_id)
            if e.target_id == target_id
        ]

    # ── Bulk Operations ─────────────────────────────────────────────────────

    def add_nodes(self, nodes: list[GraphNode], *, upsert: bool = False) -> int:
        """Add multiple nodes. Returns count of nodes added."""
        count = 0
        for node in nodes:
            self.add_node(node, upsert=upsert)
            count += 1
        return count

    def add_edges(self, edges: list[GraphEdge], *, upsert: bool = False) -> int:
        """Add multiple edges. Returns count of edges added."""
        count = 0
        for edge in edges:
            self.add_edge(edge, upsert=upsert)
            count += 1
        return count

    def clear(self) -> None:
        """Remove all nodes and edges."""
        self._nodes.clear()
        self._edges.clear()
        self._outgoing.clear()
        self._incoming.clear()
        self._nodes_by_type.clear()

    # ── Snapshot ────────────────────────────────────────────────────────────

    def snapshot(self) -> dict:
        """Export full store state for audit or persistence.

        Returns a serializable dict with all nodes and edges.
        """
        return {
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "nodes": [n.model_dump(mode="json") for n in self._nodes.values()],
            "edges": [e.model_dump(mode="json") for e in self._edges.values()],
        }

    # ── Internal ────────────────────────────────────────────────────────────

    def _remove_from_adjacency(self, edge: GraphEdge) -> None:
        """Remove an edge from adjacency indices."""
        out_list = self._outgoing.get(edge.source_id, [])
        if edge.edge_id in out_list:
            out_list.remove(edge.edge_id)
        in_list = self._incoming.get(edge.target_id, [])
        if edge.edge_id in in_list:
            in_list.remove(edge.edge_id)

    def __repr__(self) -> str:
        return f"GraphStore(nodes={self.node_count}, edges={self.edge_count})"
