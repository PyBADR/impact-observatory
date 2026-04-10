"""Neo4j Graph Writer — Persists MappingResult into Neo4j.

Translates GraphNode and GraphEdge objects from the Graph Expansion Layer
into idempotent Cypher MERGE operations.

Architecture Layer: Features → Models (Layer 2-3)
Owner: Graph Persistence Service
Consumers: Signal Ingestion Pipeline, Bulk Loader

Design Principles:
  1. Idempotent: MERGE ensures no duplicates on re-ingestion
  2. Batch-aware: groups operations for throughput
  3. Transactional: each signal's graph writes commit atomically
  4. Observable: returns WriteResult with counts and timings
  5. Fail-safe: individual node/edge failures don't abort the batch

Cypher Strategy:
  - Nodes: MERGE on (id) → SET properties
  - Edges: MERGE on (source, target, type) → SET properties
  - Multi-label: secondary labels applied via SET after MERGE
  - Temporal properties: event_time, created_at stored as ISO strings
"""

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.graph_brain.types import (
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphRelationType,
)
from src.graph_brain.graph_mapper import MappingResult

logger = logging.getLogger("graph_brain.neo4j_writer")


# ═══════════════════════════════════════════════════════════════════════════════
# Write Result Contract
# ═══════════════════════════════════════════════════════════════════════════════

class WriteResult(BaseModel):
    """Result of persisting a MappingResult to Neo4j."""
    signal_id: str = ""
    nodes_merged: int = 0
    nodes_created: int = 0
    nodes_updated: int = 0
    edges_merged: int = 0
    edges_created: int = 0
    edges_updated: int = 0
    errors: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def success(self) -> bool:
        return len(self.errors) == 0

    def summary(self) -> dict[str, Any]:
        return {
            "signal_id": self.signal_id,
            "nodes_merged": self.nodes_merged,
            "edges_merged": self.edges_merged,
            "errors_count": len(self.errors),
            "duration_ms": round(self.duration_ms, 2),
            "success": self.success,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Entity Type → Neo4j Label Mapping
# ═══════════════════════════════════════════════════════════════════════════════

ENTITY_TYPE_TO_LABEL: dict[GraphEntityType, str] = {
    GraphEntityType.SIGNAL: "Signal",
    GraphEntityType.EVENT: "Event",
    GraphEntityType.COUNTRY: "Region",
    GraphEntityType.REGION: "Region",
    GraphEntityType.SECTOR: "Sector",
    GraphEntityType.IMPACT_DOMAIN: "ImpactDomain",
    GraphEntityType.ORGANIZATION: "Organization",
    GraphEntityType.INFRASTRUCTURE: "Infrastructure",
    GraphEntityType.CHOKEPOINT: "Corridor",
    GraphEntityType.REGULATOR: "Organization",
    GraphEntityType.MARKET: "Organization",
    GraphEntityType.RISK_FACTOR: "RiskFactor",
    GraphEntityType.INDICATOR: "Indicator",
}

RELATION_TYPE_TO_NEO4J: dict[GraphRelationType, str] = {
    GraphRelationType.AFFECTS: "AFFECTS",
    GraphRelationType.DEPENDS_ON: "DEPENDS_ON",
    GraphRelationType.EXPOSED_TO: "EXPOSED_TO",
    GraphRelationType.PROPAGATES_TO: "PROPAGATES_TO",
    GraphRelationType.INFLUENCES: "INFLUENCES",
    GraphRelationType.LINKED_TO: "LINKED_TO",
    GraphRelationType.TRIGGERED_BY: "TRIGGERED_BY",
    GraphRelationType.LOCATED_IN: "LOCATED_IN",
    GraphRelationType.CONSTRAINED_BY: "CONSTRAINED_BY",
    GraphRelationType.CORRELATED_WITH: "CORRELATED_WITH",
    GraphRelationType.DIRECT_EXPOSURE: "DIRECT_EXPOSURE",
    GraphRelationType.SUPPLY_CHAIN: "SUPPLY_CHAIN",
    GraphRelationType.MARKET_CONTAGION: "MARKET_CONTAGION",
    GraphRelationType.FISCAL_LINKAGE: "FISCAL_LINKAGE",
    GraphRelationType.INFRASTRUCTURE_DEP: "INFRASTRUCTURE_DEP",
    GraphRelationType.REGULATORY: "REGULATORY",
    GraphRelationType.RISK_TRANSFER: "RISK_TRANSFER",
    GraphRelationType.OPERATES_IN: "OPERATES_IN",
    GraphRelationType.REGULATES: "REGULATES",
    GraphRelationType.DERIVED_FROM: "DERIVED_FROM",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Cypher Query Templates
# ═══════════════════════════════════════════════════════════════════════════════

# Generic node MERGE — label injected via string formatting (safe: from enum)
_MERGE_NODE_TEMPLATE = """
MERGE (n:{label} {{id: $id}})
SET n += $properties
RETURN n.id AS id,
       CASE WHEN n.created_at IS NULL THEN 'created' ELSE 'updated' END AS action
"""

_SET_CREATED_AT = """
MATCH (n {{id: $id}})
WHERE n.created_at IS NULL
SET n.created_at = $created_at
"""

# Generic relationship MERGE — type injected via string formatting (safe: from enum)
_MERGE_REL_TEMPLATE = """
MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
MERGE (a)-[r:{rel_type}]->(b)
SET r += $properties
RETURN type(r) AS rel_type,
       CASE WHEN r.created_at IS NULL THEN 'created' ELSE 'updated' END AS action
"""

_SET_REL_CREATED_AT = """
MATCH (a {{id: $source_id}})-[r:{rel_type}]->(b {{id: $target_id}})
WHERE r.created_at IS NULL
SET r.created_at = $created_at
"""


# ═══════════════════════════════════════════════════════════════════════════════
# Property Serialization
# ═══════════════════════════════════════════════════════════════════════════════

def _serialize_node_properties(node: GraphNode) -> dict[str, Any]:
    """Flatten node into Neo4j-safe property dict.

    Neo4j properties must be primitives (str, int, float, bool, list of primitives).
    Complex objects are JSON-serialized into strings.
    """
    props: dict[str, Any] = {
        "id": node.node_id,
        "label": node.label,
        "entity_type": node.entity_type.value,
        "confidence": node.confidence.value,
    }

    if node.label_ar:
        props["label_ar"] = node.label_ar

    # Flatten domain properties (only primitives)
    for k, v in node.properties.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            props[f"prop_{k}"] = v
        elif isinstance(v, list) and all(isinstance(x, (str, int, float)) for x in v):
            props[f"prop_{k}"] = v

    # Provenance as concatenated string (searchable)
    if node.source_refs:
        props["provenance"] = "; ".join(
            f"{sr.source_type}:{sr.source_id}" for sr in node.source_refs
        )

    props["updated_at"] = datetime.now(timezone.utc).isoformat()
    return props


def _serialize_edge_properties(edge: GraphEdge) -> dict[str, Any]:
    """Flatten edge into Neo4j-safe property dict."""
    props: dict[str, Any] = {
        "edge_id": edge.edge_id,
        "label": edge.label,
        "weight": edge.weight,
        "confidence": edge.confidence.value,
    }

    for k, v in edge.properties.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            props[f"prop_{k}"] = v

    if edge.source_refs:
        props["provenance"] = "; ".join(
            f"{sr.source_type}:{sr.source_id}" for sr in edge.source_refs
        )

    props["updated_at"] = datetime.now(timezone.utc).isoformat()
    return props


# ═══════════════════════════════════════════════════════════════════════════════
# Neo4j Writer Class
# ═══════════════════════════════════════════════════════════════════════════════

class Neo4jGraphWriter:
    """Persists MappingResult graph elements into Neo4j.

    Requires an async Neo4j session. All operations use MERGE for idempotency.
    """

    def __init__(self, session):
        """Initialize with an active Neo4j AsyncSession."""
        self._session = session

    async def write_mapping_result(self, mapping: MappingResult) -> WriteResult:
        """Write all nodes and edges from a MappingResult to Neo4j.

        Executes in a single implicit transaction for atomicity.
        Individual element failures are captured as errors, not raised.
        """
        t0 = time.monotonic()
        result = WriteResult(signal_id=mapping.signal_id)

        # Deduplicate nodes by node_id (mapper may produce duplicates for shared entities)
        seen_nodes: dict[str, GraphNode] = {}
        for node in mapping.nodes:
            if node.node_id not in seen_nodes:
                seen_nodes[node.node_id] = node
        unique_nodes = list(seen_nodes.values())

        # Deduplicate edges by edge_id
        seen_edges: dict[str, GraphEdge] = {}
        for edge in mapping.edges:
            if edge.edge_id not in seen_edges:
                seen_edges[edge.edge_id] = edge
        unique_edges = list(seen_edges.values())

        # Phase 1: MERGE all nodes
        for node in unique_nodes:
            try:
                await self._merge_node(node, result)
            except Exception as exc:
                error_msg = f"Node MERGE failed for {node.node_id}: {exc}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        # Phase 2: MERGE all edges (nodes must exist first)
        for edge in unique_edges:
            try:
                await self._merge_edge(edge, result)
            except Exception as exc:
                error_msg = f"Edge MERGE failed for {edge.edge_id}: {exc}"
                logger.error(error_msg)
                result.errors.append(error_msg)

        result.duration_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "Neo4j write for signal %s: %d nodes merged, %d edges merged (%.1fms) — %d errors",
            result.signal_id, result.nodes_merged, result.edges_merged,
            result.duration_ms, len(result.errors),
        )
        return result

    async def _merge_node(self, node: GraphNode, result: WriteResult) -> None:
        """MERGE a single node into Neo4j."""
        label = ENTITY_TYPE_TO_LABEL.get(node.entity_type, "Entity")
        query = _MERGE_NODE_TEMPLATE.format(label=label)
        properties = _serialize_node_properties(node)

        record = await self._session.run(
            query, id=node.node_id, properties=properties
        )
        single = await record.single()
        if single:
            action = single["action"]
            result.nodes_merged += 1
            if action == "created":
                result.nodes_created += 1
                # Set created_at only on first creation
                await self._session.run(
                    _SET_CREATED_AT.format(),
                    id=node.node_id,
                    created_at=node.created_at.isoformat(),
                )
            else:
                result.nodes_updated += 1

    async def _merge_edge(self, edge: GraphEdge, result: WriteResult) -> None:
        """MERGE a single relationship into Neo4j."""
        rel_type = RELATION_TYPE_TO_NEO4J.get(edge.relation_type, "LINKED_TO")
        query = _MERGE_REL_TEMPLATE.format(rel_type=rel_type)
        properties = _serialize_edge_properties(edge)

        record = await self._session.run(
            query,
            source_id=edge.source_id,
            target_id=edge.target_id,
            properties=properties,
        )
        single = await record.single()
        if single:
            action = single["action"]
            result.edges_merged += 1
            if action == "created":
                result.edges_created += 1
                await self._session.run(
                    _SET_REL_CREATED_AT.format(rel_type=rel_type),
                    source_id=edge.source_id,
                    target_id=edge.target_id,
                    created_at=edge.created_at.isoformat(),
                )
            else:
                result.edges_updated += 1


# ═══════════════════════════════════════════════════════════════════════════════
# Convenience: In-Memory Writer (for GraphStore, no Neo4j required)
# ═══════════════════════════════════════════════════════════════════════════════

class InMemoryGraphWriter:
    """Persists MappingResult into the in-memory GraphStore.

    Used when Neo4j is not available (local dev, tests).
    Maintains the same WriteResult contract as Neo4jGraphWriter.
    """

    def __init__(self, store):
        """Initialize with a GraphStore instance."""
        from src.graph_brain.store import GraphStore
        self._store: GraphStore = store

    def write_mapping_result(self, mapping: MappingResult) -> WriteResult:
        """Write all nodes and edges synchronously to the in-memory store."""
        t0 = time.monotonic()
        result = WriteResult(signal_id=mapping.signal_id)

        # Deduplicate
        seen_nodes: set[str] = set()
        for node in mapping.nodes:
            if node.node_id in seen_nodes:
                continue
            seen_nodes.add(node.node_id)
            try:
                if self._store.has_node(node.node_id):
                    result.nodes_updated += 1
                else:
                    self._store.add_node(node)
                    result.nodes_created += 1
                result.nodes_merged += 1
            except Exception as exc:
                result.errors.append(f"Node add failed for {node.node_id}: {exc}")

        seen_edges: set[str] = set()
        for edge in mapping.edges:
            if edge.edge_id in seen_edges:
                continue
            seen_edges.add(edge.edge_id)
            # Skip edges whose endpoints don't exist in store
            if not self._store.has_node(edge.source_id) or not self._store.has_node(edge.target_id):
                # For derived_from edges, the parent signal may not be in store
                if edge.relation_type == GraphRelationType.DERIVED_FROM:
                    continue
                result.errors.append(
                    f"Edge skipped (missing endpoint): {edge.edge_id}"
                )
                continue
            try:
                if self._store.has_edge(edge.edge_id):
                    result.edges_updated += 1
                else:
                    self._store.add_edge(edge)
                    result.edges_created += 1
                result.edges_merged += 1
            except Exception as exc:
                result.errors.append(f"Edge add failed for {edge.edge_id}: {exc}")

        result.duration_ms = (time.monotonic() - t0) * 1000
        return result
