"""Graph Brain Shadow Layer — Singleton Service.

Provides a global GraphStore instance and high-level operations
for the API layer. Wraps store + ingestion + query + explain.

Design:
  - Single in-memory store instance per process
  - Thread-safe under Python GIL (single writer)
  - Stateless operations delegate to pure functions
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from src.graph_brain.store import GraphStore
from src.graph_brain.ingestion import IngestionResult, ingest_signal
from src.graph_brain.query import (
    extract_subgraph,
    find_connected,
    find_downstream,
    find_upstream,
    trace_paths,
)
from src.graph_brain.explain import (
    explain_dependencies,
    explain_impact,
    explain_path,
)
from src.graph_brain.types import (
    GraphEdge,
    GraphEntityType,
    GraphExplanation,
    GraphNode,
    GraphPath,
    GraphRelationType,
)
from src.macro.macro_schemas import NormalizedSignal

logger = logging.getLogger(__name__)


class GraphBrainService:
    """High-level service wrapping the Graph Brain Shadow Layer.

    Provides store management, ingestion, queries, and explanations.
    """

    def __init__(self) -> None:
        self._store = GraphStore()

    @property
    def store(self) -> GraphStore:
        return self._store

    # ── Ingestion ───────────────────────────────────────────────────────────

    def ingest(self, signal: NormalizedSignal) -> IngestionResult:
        """Ingest a NormalizedSignal into the graph store."""
        result = ingest_signal(signal, self._store)
        logger.info(
            "Graph Brain ingested signal %s: %s",
            signal.signal_id, result,
        )
        return result

    # ── Node Queries ────────────────────────────────────────────────────────

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        return self._store.get_node(node_id)

    def get_nodes_by_type(self, entity_type: GraphEntityType) -> list[GraphNode]:
        return self._store.get_nodes_by_type(entity_type)

    # ── Traversal Queries ───────────────────────────────────────────────────

    def connected(
        self,
        node_id: str,
        max_depth: int = 3,
        direction: str = "both",
    ) -> list[GraphNode]:
        return find_connected(self._store, node_id, max_depth=max_depth, direction=direction)

    def upstream(self, node_id: str, max_depth: int = 4) -> list[GraphNode]:
        return find_upstream(self._store, node_id, max_depth=max_depth)

    def downstream(self, node_id: str, max_depth: int = 4) -> list[GraphNode]:
        return find_downstream(self._store, node_id, max_depth=max_depth)

    def trace(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5,
    ) -> list[GraphPath]:
        return trace_paths(self._store, start_id, end_id, max_depth=max_depth)

    # ── Explanations ────────────────────────────────────────────────────────

    def explain_relationship(
        self,
        start_id: str,
        end_id: str,
        max_depth: int = 5,
    ) -> GraphExplanation:
        return explain_path(self._store, start_id, end_id, max_depth=max_depth)

    def explain_downstream(self, source_id: str, max_depth: int = 4) -> GraphExplanation:
        return explain_impact(self._store, source_id, max_depth=max_depth)

    def explain_upstream(self, target_id: str, max_depth: int = 4) -> GraphExplanation:
        return explain_dependencies(self._store, target_id, max_depth=max_depth)

    # ── Stats ───────────────────────────────────────────────────────────────

    def stats(self) -> dict:
        """Return graph store statistics."""
        type_counts = {}
        for et in GraphEntityType:
            nodes = self._store.get_nodes_by_type(et)
            if nodes:
                type_counts[et.value] = len(nodes)

        return {
            "node_count": self._store.node_count,
            "edge_count": self._store.edge_count,
            "nodes_by_type": type_counts,
        }

    def snapshot(self) -> dict:
        return self._store.snapshot()


# ── Singleton ───────────────────────────────────────────────────────────────

_instance: Optional[GraphBrainService] = None


def get_graph_brain_service() -> GraphBrainService:
    """Get or create the global GraphBrainService singleton."""
    global _instance
    if _instance is None:
        _instance = GraphBrainService()
    return _instance
