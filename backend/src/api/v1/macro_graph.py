"""Graph Brain Shadow Layer — Internal API Routes.

Minimal inspection endpoints for the Graph Brain shadow layer.
These are internal/diagnostic — not part of the public API contract.

Endpoints:
  POST  /api/v1/macro/graph/ingest/{signal_id}  — ingest a registered signal into graph
  GET   /api/v1/macro/graph/node/{node_id}       — get a graph node by ID
  GET   /api/v1/macro/graph/path                  — trace path between two nodes
  GET   /api/v1/macro/graph/connected/{node_id}   — get connected entities
  GET   /api/v1/macro/graph/explain               — explain relationship between two nodes
  GET   /api/v1/macro/graph/stats                 — graph store statistics

No business logic here. Routes delegate entirely to GraphBrainService.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from src.graph_brain.service import GraphBrainService, get_graph_brain_service
from src.graph_brain.types import GraphEntityType
from src.macro.macro_signal_service import MacroSignalService, get_signal_service

router = APIRouter(prefix="/api/v1/macro/graph", tags=["graph-brain"])


# ── POST /ingest/{signal_id} — Ingest Signal Into Graph ────────────────────

@router.post(
    "/ingest/{signal_id}",
    summary="Ingest a registered signal into the graph store",
    description=(
        "Looks up the signal by signal_id in the macro signal registry, "
        "then ingests it into the Graph Brain shadow layer. "
        "Idempotent: re-ingesting the same signal is a no-op for existing elements."
    ),
    status_code=200,
)
async def ingest_signal_to_graph(
    signal_id: UUID,
    signal_service: MacroSignalService = Depends(get_signal_service),
    graph_service: GraphBrainService = Depends(get_graph_brain_service),
) -> dict[str, Any]:
    # Look up the signal in Pack 1 registry
    entry = signal_service.get_by_signal_id(signal_id)
    if entry is None:
        raise HTTPException(
            status_code=404,
            detail=f"Signal '{signal_id}' not found in registry",
        )

    # Ingest into graph
    result = graph_service.ingest(entry.signal)

    return {
        "signal_id": str(signal_id),
        "nodes_created": result.nodes_created,
        "nodes_existing": result.nodes_existing,
        "edges_created": result.edges_created,
        "edges_existing": result.edges_existing,
        "total_nodes": result.total_nodes,
        "total_edges": result.total_edges,
        "store_stats": graph_service.stats(),
        "message": "Signal ingested into Graph Brain",
    }


# ── GET /node/{node_id} — Get Graph Node ───────────────────────────────────

@router.get(
    "/node/{node_id:path}",
    summary="Get a graph node by ID",
    description="Returns the full GraphNode including properties and provenance.",
)
async def get_graph_node(
    node_id: str,
    graph_service: GraphBrainService = Depends(get_graph_brain_service),
) -> dict[str, Any]:
    node = graph_service.get_node(node_id)
    if node is None:
        raise HTTPException(
            status_code=404,
            detail=f"Node '{node_id}' not found in graph store",
        )
    return node.model_dump(mode="json")


# ── GET /path — Trace Path Between Nodes ────────────────────────────────────

@router.get(
    "/path",
    summary="Trace paths between two graph nodes",
    description=(
        "BFS path tracing between start and end nodes. "
        "Returns all paths up to max_depth, sorted by total weight."
    ),
)
async def trace_graph_path(
    start: str = Query(..., description="Start node ID (e.g. 'signal:abc')"),
    end: str = Query(..., description="End node ID (e.g. 'impact_domain:banking')"),
    max_depth: int = Query(5, ge=1, le=10, description="Maximum path depth"),
    graph_service: GraphBrainService = Depends(get_graph_brain_service),
) -> dict[str, Any]:
    # Validate nodes exist
    if not graph_service.get_node(start):
        raise HTTPException(status_code=404, detail=f"Start node '{start}' not found")
    if not graph_service.get_node(end):
        raise HTTPException(status_code=404, detail=f"End node '{end}' not found")

    paths = graph_service.trace(start, end, max_depth=max_depth)

    return {
        "start": start,
        "end": end,
        "max_depth": max_depth,
        "paths_found": len(paths),
        "paths": [p.model_dump(mode="json") for p in paths],
    }


# ── GET /connected/{node_id} — Connected Entities ──────────────────────────

@router.get(
    "/connected/{node_id:path}",
    summary="Get entities connected to a node",
    description="Returns all nodes connected within max_depth hops.",
)
async def get_connected(
    node_id: str,
    max_depth: int = Query(2, ge=1, le=5),
    direction: str = Query("both", regex="^(outgoing|incoming|both)$"),
    graph_service: GraphBrainService = Depends(get_graph_brain_service),
) -> dict[str, Any]:
    if not graph_service.get_node(node_id):
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")

    connected = graph_service.connected(node_id, max_depth=max_depth, direction=direction)

    return {
        "node_id": node_id,
        "direction": direction,
        "max_depth": max_depth,
        "connected_count": len(connected),
        "connected": [n.model_dump(mode="json") for n in connected],
    }


# ── GET /explain — Explain Relationship ─────────────────────────────────────

@router.get(
    "/explain",
    summary="Explain the relationship between two nodes",
    description=(
        "Returns a structured GraphExplanation with paths, "
        "reasoning summary, confidence, and provenance."
    ),
)
async def explain_relationship(
    start: str = Query(..., description="Start node ID"),
    end: str = Query(..., description="End node ID"),
    max_depth: int = Query(5, ge=1, le=10),
    graph_service: GraphBrainService = Depends(get_graph_brain_service),
) -> dict[str, Any]:
    if not graph_service.get_node(start):
        raise HTTPException(status_code=404, detail=f"Start node '{start}' not found")
    if not graph_service.get_node(end):
        raise HTTPException(status_code=404, detail=f"End node '{end}' not found")

    explanation = graph_service.explain_relationship(start, end, max_depth=max_depth)
    return explanation.model_dump(mode="json")


# ── GET /stats — Graph Store Statistics ─────────────────────────────────────

@router.get(
    "/stats",
    summary="Graph store statistics",
    description="Returns node/edge counts and breakdown by entity type.",
)
async def get_graph_stats(
    graph_service: GraphBrainService = Depends(get_graph_brain_service),
) -> dict[str, Any]:
    return graph_service.stats()
