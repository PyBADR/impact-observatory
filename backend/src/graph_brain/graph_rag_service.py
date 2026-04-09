"""Graph-RAG Context Retrieval Service.

Retrieves structured graph context for the AI Insights Agent.
Uses the in-memory GraphStore (primary) with optional Neo4j fallback.

Architecture Layer: Features → Models (Layer 2-3)
Owner: AI Insights Agent
Consumers: InsightsAgent

Retrieval Strategy (multi-hop, typed):
  1. Entity Resolution: map query terms → GraphNode IDs via label/type match
  2. Subgraph Extraction: BFS from resolved entities (configurable depth)
  3. Path Discovery: trace impact/dependency paths between entities
  4. Context Assembly: serialize graph context into LLM-digestible text

Design Principles:
  - Uses existing GraphBrainService (store + query + explain) — no new DB driver
  - Falls back gracefully: Neo4j offline → in-memory store still works
  - Context budget: limits serialized context to stay within LLM token budget
  - Deterministic: same store state + same query → same context
"""

import logging
import time
from typing import Any, Optional

from pydantic import BaseModel, Field

from src.graph_brain.service import GraphBrainService, get_graph_brain_service
from src.graph_brain.query import extract_subgraph, find_connected, trace_paths
from src.graph_brain.store import GraphStore
from src.graph_brain.types import (
    CONFIDENCE_WEIGHTS,
    GraphConfidence,
    GraphEdge,
    GraphEntityType,
    GraphNode,
    GraphPath,
    GraphRelationType,
)

logger = logging.getLogger("graph_brain.graph_rag")


# ═══════════════════════════════════════════════════════════════════════════════
# Retrieval Result
# ═══════════════════════════════════════════════════════════════════════════════

class ResolvedEntity(BaseModel):
    """An entity resolved from the user query against the graph."""
    node_id: str
    label: str
    entity_type: str
    confidence: float = 1.0
    match_reason: str = ""


class RetrievedContext(BaseModel):
    """Structured graph context for LLM consumption."""
    resolved_entities: list[ResolvedEntity] = Field(default_factory=list)
    subgraph_nodes: list[dict] = Field(default_factory=list)
    subgraph_edges: list[dict] = Field(default_factory=list)
    impact_paths: list[dict] = Field(default_factory=list)
    context_text: str = Field("", description="LLM-ready text serialization of graph context")
    node_count: int = 0
    edge_count: int = 0
    path_count: int = 0
    retrieval_ms: float = 0.0

    def summary(self) -> dict[str, Any]:
        return {
            "resolved_entities": len(self.resolved_entities),
            "nodes": self.node_count,
            "edges": self.edge_count,
            "paths": self.path_count,
            "context_chars": len(self.context_text),
            "retrieval_ms": round(self.retrieval_ms, 1),
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Entity Resolver — query terms → graph nodes
# ═══════════════════════════════════════════════════════════════════════════════

# GCC domain vocabulary for entity resolution
GCC_ENTITY_VOCABULARY: dict[str, list[str]] = {
    # Countries
    "saudi": ["country:SA"], "ksa": ["country:SA"], "arabia": ["country:SA"],
    "uae": ["country:AE"], "emirates": ["country:AE"], "dubai": ["country:AE"],
    "qatar": ["country:QA"], "doha": ["country:QA"],
    "bahrain": ["country:BH"], "manama": ["country:BH"],
    "kuwait": ["country:KW"],
    "oman": ["country:OM"], "muscat": ["country:OM"],
    # Chokepoints
    "hormuz": ["chokepoint:hormuz_strait"],
    "strait": ["chokepoint:hormuz_strait"],
    "bab": ["chokepoint:bab_el_mandeb"],
    "mandeb": ["chokepoint:bab_el_mandeb"],
    "suez": ["chokepoint:suez_canal"],
    # Sectors
    "oil": ["sector:energy", "indicator:brent_crude_usd"],
    "energy": ["sector:energy"],
    "banking": ["sector:banking"],
    "insurance": ["sector:insurance"],
    "maritime": ["sector:maritime"],
    "shipping": ["sector:maritime"],
    "port": ["sector:maritime"],
    "reinsurance": ["market:reinsurance"],
    "cyber": ["risk_factor:cyber_risk"],
    # Infrastructure
    "aramco": ["organization:saudi_aramco"],
    "adnoc": ["organization:adnoc"],
    "opec": ["organization:opec"],
}


class EntityResolver:
    """Resolves natural language query terms into GraphNode IDs.

    Strategy (layered, from most precise to most general):
      1. Exact node_id match: query contains a valid node_id
      2. GCC vocabulary match: domain-specific term → known node IDs
      3. Label search: fuzzy match against all node labels in the store
      4. Entity type match: query mentions a type name → all nodes of that type
    """

    def __init__(self, store: GraphStore) -> None:
        self._store = store

    def resolve(self, query: str, max_entities: int = 10) -> list[ResolvedEntity]:
        """Resolve query into graph entities."""
        results: list[ResolvedEntity] = []
        seen_ids: set[str] = set()
        query_lower = query.lower()
        query_tokens = set(query_lower.replace(",", " ").replace(".", " ").split())

        # Layer 1: Exact node_id match
        for token in query_tokens:
            node = self._store.get_node(token)
            if node and node.node_id not in seen_ids:
                results.append(ResolvedEntity(
                    node_id=node.node_id,
                    label=node.label,
                    entity_type=node.entity_type.value,
                    confidence=1.0,
                    match_reason="exact_node_id",
                ))
                seen_ids.add(node.node_id)

        # Layer 2: GCC vocabulary match
        for token in query_tokens:
            candidate_ids = GCC_ENTITY_VOCABULARY.get(token, [])
            for nid in candidate_ids:
                if nid in seen_ids:
                    continue
                node = self._store.get_node(nid)
                if node:
                    results.append(ResolvedEntity(
                        node_id=node.node_id,
                        label=node.label,
                        entity_type=node.entity_type.value,
                        confidence=0.90,
                        match_reason=f"gcc_vocabulary:{token}",
                    ))
                    seen_ids.add(node.node_id)

        # Layer 3: Label search — fuzzy substring match
        for node in self._store.all_nodes():
            if node.node_id in seen_ids:
                continue
            label_lower = node.label.lower()
            for token in query_tokens:
                if len(token) >= 3 and token in label_lower:
                    results.append(ResolvedEntity(
                        node_id=node.node_id,
                        label=node.label,
                        entity_type=node.entity_type.value,
                        confidence=0.70,
                        match_reason=f"label_match:{token}",
                    ))
                    seen_ids.add(node.node_id)
                    break

        # Layer 4: Entity type match
        for et in GraphEntityType:
            if et.value in query_tokens or et.value.replace("_", " ") in query_lower:
                for node in self._store.get_nodes_by_type(et)[:3]:
                    if node.node_id not in seen_ids:
                        results.append(ResolvedEntity(
                            node_id=node.node_id,
                            label=node.label,
                            entity_type=node.entity_type.value,
                            confidence=0.50,
                            match_reason=f"entity_type_match:{et.value}",
                        ))
                        seen_ids.add(node.node_id)

        # Sort by confidence desc, truncate
        results.sort(key=lambda r: r.confidence, reverse=True)
        return results[:max_entities]


# ═══════════════════════════════════════════════════════════════════════════════
# Context Builder — graph → LLM-digestible text
# ═══════════════════════════════════════════════════════════════════════════════

class ContextBuilder:
    """Serializes graph subgraph into LLM-digestible context text.

    Budget-aware: limits output to max_chars to stay within token budget.
    """

    def __init__(self, max_chars: int = 8000) -> None:
        self._max_chars = max_chars

    def build(
        self,
        resolved: list[ResolvedEntity],
        nodes: list[GraphNode],
        edges: list[GraphEdge],
        paths: list[GraphPath],
    ) -> str:
        """Build structured context text from graph elements."""
        parts: list[str] = []

        # Section 1: Resolved entities
        if resolved:
            parts.append("=== RESOLVED ENTITIES ===")
            for ent in resolved:
                parts.append(
                    f"• {ent.label} (type={ent.entity_type}, id={ent.node_id}, "
                    f"conf={ent.confidence:.2f}, match={ent.match_reason})"
                )

        # Section 2: Graph nodes with properties
        if nodes:
            parts.append("\n=== GRAPH ENTITIES ===")
            for node in nodes[:30]:  # cap to avoid blowup
                props_str = ""
                important_props = {
                    k: v for k, v in node.properties.items()
                    if k not in ("created_at", "updated_at") and v is not None
                }
                if important_props:
                    props_str = f" | properties: {important_props}"
                parts.append(
                    f"• [{node.entity_type.value}] {node.label} "
                    f"(id={node.node_id}, confidence={node.confidence.value}){props_str}"
                )

        # Section 3: Relationships
        if edges:
            parts.append("\n=== RELATIONSHIPS ===")
            for edge in edges[:40]:
                parts.append(
                    f"• {edge.source_id} --[{edge.relation_type.value}, "
                    f"weight={edge.weight:.2f}]--> {edge.target_id}"
                )

        # Section 4: Impact/dependency paths
        if paths:
            parts.append("\n=== IMPACT PATHS ===")
            for i, path in enumerate(paths[:5], 1):
                path_str = " → ".join(n.label for n in path.nodes)
                parts.append(
                    f"Path {i}: {path_str} "
                    f"(weight={path.total_weight:.4f}, hops={path.total_hops})"
                )

        text = "\n".join(parts)

        # Truncate to budget
        if len(text) > self._max_chars:
            text = text[:self._max_chars - 50] + "\n\n[... context truncated to fit token budget]"

        return text


# ═══════════════════════════════════════════════════════════════════════════════
# Graph-RAG Service — main orchestrator
# ═══════════════════════════════════════════════════════════════════════════════

class GraphRAGService:
    """Retrieves structured graph context for the AI Insights Agent.

    Pipeline:
      1. Entity Resolution: query → node IDs
      2. Subgraph Extraction: BFS from resolved entities
      3. Path Discovery: trace paths between resolved entities
      4. Context Assembly: serialize into LLM-ready text

    Args:
        graph_brain: GraphBrainService (uses in-memory store by default)
        max_depth: BFS traversal depth for subgraph extraction
        max_context_chars: Maximum context text length
    """

    def __init__(
        self,
        graph_brain: Optional[GraphBrainService] = None,
        max_depth: int = 3,
        max_context_chars: int = 8000,
    ) -> None:
        self._graph_brain = graph_brain or get_graph_brain_service()
        self._max_depth = max_depth
        self._resolver = EntityResolver(self._graph_brain.store)
        self._context_builder = ContextBuilder(max_chars=max_context_chars)

    def retrieve(
        self,
        query: str,
        context_limit: int = 10,
        include_paths: bool = True,
    ) -> RetrievedContext:
        """Retrieve graph context for a natural language query.

        Args:
            query: Natural language query (e.g., "impact of Hormuz closure on Saudi insurance")
            context_limit: Max entities to resolve
            include_paths: Whether to trace paths between resolved entities

        Returns:
            RetrievedContext with entities, subgraph, paths, and LLM-ready text
        """
        t0 = time.monotonic()
        result = RetrievedContext()

        # Step 1: Entity Resolution
        resolved = self._resolver.resolve(query, max_entities=context_limit)
        result.resolved_entities = resolved

        if not resolved:
            result.context_text = (
                "No entities could be resolved from the query against the knowledge graph. "
                "The graph may be empty or the query terms don't match any known entities."
            )
            result.retrieval_ms = (time.monotonic() - t0) * 1000
            return result

        # Step 2: Subgraph Extraction (BFS from each resolved entity)
        all_nodes: dict[str, GraphNode] = {}
        all_edges: dict[str, GraphEdge] = {}

        for ent in resolved:
            sub_nodes, sub_edges = extract_subgraph(
                self._graph_brain.store,
                ent.node_id,
                max_depth=self._max_depth,
                direction="both",
            )
            for n in sub_nodes:
                all_nodes[n.node_id] = n
            for e in sub_edges:
                all_edges[e.edge_id] = e

        nodes_list = list(all_nodes.values())
        edges_list = list(all_edges.values())
        result.subgraph_nodes = [
            {"node_id": n.node_id, "label": n.label, "type": n.entity_type.value}
            for n in nodes_list
        ]
        result.subgraph_edges = [
            {"edge_id": e.edge_id, "source": e.source_id, "target": e.target_id,
             "type": e.relation_type.value, "weight": e.weight}
            for e in edges_list
        ]
        result.node_count = len(nodes_list)
        result.edge_count = len(edges_list)

        # Step 3: Path Discovery (between pairs of resolved entities)
        all_paths: list[GraphPath] = []
        if include_paths and len(resolved) >= 2:
            seen_pairs: set[tuple[str, str]] = set()
            for i, src in enumerate(resolved[:5]):
                for tgt in resolved[i + 1:5]:
                    pair = (src.node_id, tgt.node_id)
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)
                    paths = trace_paths(
                        self._graph_brain.store,
                        src.node_id, tgt.node_id,
                        max_depth=self._max_depth + 1,
                        max_paths=3,
                    )
                    all_paths.extend(paths)

        result.impact_paths = [
            {"path": p.path_description, "weight": p.total_weight, "hops": p.total_hops}
            for p in all_paths
        ]
        result.path_count = len(all_paths)

        # Step 4: Context Assembly
        result.context_text = self._context_builder.build(
            resolved, nodes_list, edges_list, all_paths,
        )

        result.retrieval_ms = (time.monotonic() - t0) * 1000
        logger.info(
            "Graph-RAG retrieval: %d entities → %d nodes, %d edges, %d paths (%.1fms)",
            len(resolved), result.node_count, result.edge_count,
            result.path_count, result.retrieval_ms,
        )
        return result
