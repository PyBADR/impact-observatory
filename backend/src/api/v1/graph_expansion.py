"""Graph Expansion API — Routes for Signal-to-KG transformation.

Endpoints:
  POST  /api/v1/graph/expand          — expand a MacroSignal into KG entities
  POST  /api/v1/graph/expand/batch    — expand a batch of MacroSignals
  POST  /api/v1/graph/expand/preview  — dry-run: map without persisting
  GET   /api/v1/graph/expand/stats    — expansion pipeline statistics

These routes extend the existing /api/v1/macro/graph/* endpoints.
No breaking changes — additive only.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from src.graph_brain.graph_expansion_service import (
    GraphExpansionResult,
    GraphExpansionService,
    get_graph_expansion_service,
)
from src.graph_brain.graph_mapper import MappingResult, map_signal_to_graph

router = APIRouter(prefix="/api/v1/graph/expand", tags=["graph-expansion"])


# ── Request/Response Models ───────────────────────────────────────────────────

class ExpandSignalRequest(BaseModel):
    """Request body for signal expansion. Accepts the full MacroSignal dict."""
    signal: dict = Field(
        ...,
        description="MacroSignal serialized as dict (from .model_dump())",
    )


class ExpandBatchRequest(BaseModel):
    """Request body for batch expansion."""
    signals: list[dict] = Field(
        ...,
        min_length=1,
        max_length=100,
        description="List of MacroSignal dicts",
    )


class PreviewResponse(BaseModel):
    """Dry-run response: mapping result without persistence."""
    signal_id: str = ""
    nodes: list[dict] = Field(default_factory=list)
    edges: list[dict] = Field(default_factory=list)
    decisions: list[dict] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    payload_type: str = ""
    duration_ms: float = 0.0
    node_count: int = 0
    edge_count: int = 0
    hybrid_stats: dict = Field(default_factory=dict, description="Hybrid merge stats (if AI enabled)")


# ── POST /expand — Expand Single Signal ──────────────────────────────────────

@router.post(
    "",
    response_model=GraphExpansionResult,
    summary="Expand a MacroSignal into Knowledge Graph entities",
    description=(
        "Transforms a MacroSignal into entities, relationships, and event expansions. "
        "Persists to the in-memory graph store. Returns mapping decisions and write results."
    ),
)
async def expand_signal(
    request: ExpandSignalRequest,
    service: GraphExpansionService = Depends(get_graph_expansion_service),
) -> GraphExpansionResult:
    signal = request.signal
    if not signal.get("signal_id"):
        raise HTTPException(status_code=400, detail="signal.signal_id is required")
    if not signal.get("signal_type"):
        raise HTTPException(status_code=400, detail="signal.signal_type is required")

    result = service.expand_signal(signal)
    return result


# ── POST /expand/batch — Expand Multiple Signals ─────────────────────────────

@router.post(
    "/batch",
    summary="Expand a batch of MacroSignals into KG entities",
    description="Processes up to 100 signals per request.",
)
async def expand_batch(
    request: ExpandBatchRequest,
    service: GraphExpansionService = Depends(get_graph_expansion_service),
) -> dict[str, Any]:
    results = service.expand_batch(request.signals)
    succeeded = sum(1 for r in results if r.success)
    return {
        "total": len(results),
        "succeeded": succeeded,
        "failed": len(results) - succeeded,
        "results": [r.model_dump() for r in results],
        "store_stats": service.get_expansion_stats(),
    }


# ── POST /expand/preview — Dry-Run (no persistence) ──────────────────────────

@router.post(
    "/preview",
    response_model=PreviewResponse,
    summary="Preview signal-to-graph mapping without persisting",
    description=(
        "Runs the full mapping pipeline but does NOT write to the graph store. "
        "Useful for debugging mapping decisions before committing."
    ),
)
async def preview_expansion(
    request: ExpandSignalRequest,
    use_ai: bool = Query(False, description="Enable AI hybrid mapping in preview"),
) -> PreviewResponse:
    signal = request.signal
    if not signal.get("signal_id"):
        raise HTTPException(status_code=400, detail="signal.signal_id is required")

    hybrid_stats: dict = {}

    if use_ai:
        # Use hybrid mapper for AI-augmented preview
        try:
            service = get_graph_expansion_service()
            if service._hybrid_mapper is not None:
                hybrid_result = service._hybrid_mapper.map_signal(signal)
                mapping = hybrid_result.mapping
                hybrid_stats = hybrid_result.merge_stats.summary()
            else:
                mapping = map_signal_to_graph(signal)
                hybrid_stats = {"ai_enabled": False, "reason": "AI not configured"}
        except Exception as exc:
            mapping = map_signal_to_graph(signal)
            hybrid_stats = {"ai_enabled": False, "error": str(exc)}
    else:
        mapping = map_signal_to_graph(signal)

    return PreviewResponse(
        signal_id=mapping.signal_id,
        nodes=[n.model_dump(mode="json") for n in mapping.nodes],
        edges=[e.model_dump(mode="json") for e in mapping.edges],
        decisions=[d.model_dump() for d in mapping.decisions],
        warnings=mapping.warnings,
        payload_type=mapping.payload_type,
        duration_ms=mapping.duration_ms,
        node_count=mapping.node_count,
        edge_count=mapping.edge_count,
        hybrid_stats=hybrid_stats,
    )


# ── GET /expand/stats — Pipeline Statistics ───────────────────────────────────

@router.get(
    "/stats",
    summary="Graph expansion pipeline statistics",
)
async def expansion_stats(
    service: GraphExpansionService = Depends(get_graph_expansion_service),
) -> dict[str, Any]:
    return service.get_expansion_stats()
