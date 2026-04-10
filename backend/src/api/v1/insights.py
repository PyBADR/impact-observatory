"""AI Insights Agent — API Routes.

Endpoints:
  POST /api/v1/insights/query     — Run the full insights pipeline
  POST /api/v1/insights/context   — Preview graph context (no LLM)
  GET  /api/v1/insights/stats     — Agent status and stats

Architecture Layer: APIs (Layer 5)
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.graph_brain.insights_agent import InsightResult, get_insights_agent
from src.graph_brain.graph_rag_service import GraphRAGService, RetrievedContext
from src.graph_brain.service import get_graph_brain_service

logger = logging.getLogger("api.insights")

router = APIRouter(prefix="/insights", tags=["AI Insights Agent"])


# ── Request / Response Models ─────────────────────────────────────────────────

class InsightQueryRequest(BaseModel):
    """Request to run the AI Insights pipeline."""
    query: str = Field(..., min_length=3, max_length=2000, description="Natural language question")
    context_limit: int = Field(10, ge=1, le=50, description="Max entities to resolve")
    include_paths: bool = Field(True, description="Include impact path discovery")


class InsightQueryResponse(BaseModel):
    """Full insights response."""
    query: str
    insights: list[dict] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    patterns: list[str] = Field(default_factory=list)
    anomalies: list[str] = Field(default_factory=list)
    summary: str = ""
    overall_confidence: float = 0.0
    graph_context: dict = Field(default_factory=dict)
    llm_model: str = ""
    duration_ms: float = 0.0
    audit_hash: str = ""


class ContextPreviewRequest(BaseModel):
    """Request to preview graph context without LLM reasoning."""
    query: str = Field(..., min_length=3, max_length=2000)
    context_limit: int = Field(10, ge=1, le=50)
    include_paths: bool = Field(True)


class ContextPreviewResponse(BaseModel):
    """Graph context preview."""
    resolved_entities: list[dict] = Field(default_factory=list)
    subgraph_nodes: list[dict] = Field(default_factory=list)
    subgraph_edges: list[dict] = Field(default_factory=list)
    impact_paths: list[dict] = Field(default_factory=list)
    context_text: str = ""
    stats: dict = Field(default_factory=dict)


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("/query", response_model=InsightQueryResponse)
async def query_insights(request: InsightQueryRequest) -> InsightQueryResponse:
    """Run the full AI Insights pipeline.

    Pipeline: Entity Resolution → Subgraph Retrieval → Path Discovery →
    Context Assembly → LLM Reasoning → Structured Output
    """
    try:
        agent = get_insights_agent()
        result: InsightResult = agent.query(
            query=request.query,
            context_limit=request.context_limit,
            include_paths=request.include_paths,
        )

        return InsightQueryResponse(
            query=result.query,
            insights=[ins.model_dump() for ins in result.insights],
            risks=result.risks,
            patterns=result.patterns,
            anomalies=result.anomalies,
            summary=result.summary,
            overall_confidence=result.overall_confidence,
            graph_context=result.graph_context_summary,
            llm_model=result.llm_model,
            duration_ms=result.duration_ms,
            audit_hash=result.audit_hash,
        )

    except Exception as exc:
        logger.error("Insights query failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Insights agent error: {exc}")


@router.post("/context", response_model=ContextPreviewResponse)
async def preview_context(request: ContextPreviewRequest) -> ContextPreviewResponse:
    """Preview graph context without LLM reasoning.

    Useful for debugging entity resolution and subgraph retrieval
    before committing LLM tokens.
    """
    try:
        graph_brain = get_graph_brain_service()
        rag = GraphRAGService(graph_brain=graph_brain)
        context: RetrievedContext = rag.retrieve(
            query=request.query,
            context_limit=request.context_limit,
            include_paths=request.include_paths,
        )

        return ContextPreviewResponse(
            resolved_entities=[ent.model_dump() for ent in context.resolved_entities],
            subgraph_nodes=context.subgraph_nodes,
            subgraph_edges=context.subgraph_edges,
            impact_paths=context.impact_paths,
            context_text=context.context_text,
            stats=context.summary(),
        )

    except Exception as exc:
        logger.error("Context preview failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Context retrieval error: {exc}")


@router.get("/stats")
async def insights_stats() -> dict[str, Any]:
    """Return AI Insights Agent status and statistics."""
    agent = get_insights_agent()
    graph_brain = get_graph_brain_service()

    return {
        "agent_available": agent.is_available,
        "graph_store": graph_brain.stats(),
        "capabilities": [
            "risk_assessment",
            "impact_analysis",
            "dependency_map",
            "anomaly_detection",
            "scenario_analysis",
            "trend_insight",
            "compliance_alert",
        ],
        "scenarios_count": 15,
        "gcc_countries": ["SA", "AE", "QA", "BH", "KW", "OM"],
    }
