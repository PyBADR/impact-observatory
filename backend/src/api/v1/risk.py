"""Risk Assessment API — Decision Layer endpoints.

Endpoints:
  GET  /api/v1/risk/{entity_id}       — Single entity risk assessment
  POST /api/v1/risk/portfolio          — Multi-entity portfolio assessment
  GET  /api/v1/risk/type/{entity_type} — All entities of a type
  GET  /api/v1/risk/heatmap            — Full risk heatmap data
  GET  /api/v1/risk/stats              — Decision layer status

Architecture Layer: APIs (Layer 5)
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Path, Query
from pydantic import BaseModel, Field

from src.graph_brain.decision.risk_service import get_risk_service
from src.graph_brain.decision.risk_models import RiskResult, PortfolioRiskResult

logger = logging.getLogger("api.risk")

router = APIRouter(prefix="/risk", tags=["Risk Assessment"])


# ── Request / Response Models ─────────────────────────────────────────────────

class PortfolioRequest(BaseModel):
    """Request to assess multiple entities."""
    entity_ids: list[str] = Field(
        ..., min_length=1, max_length=50,
        description="List of GraphNode node_ids to assess",
    )


class RiskResponse(BaseModel):
    """Single entity risk assessment response."""
    entity_id: str = ""
    entity_label: str = ""
    entity_type: str = ""
    risk_score: float = 0.0
    risk_level: str = "NOMINAL"
    confidence: float = 0.5
    drivers: list[dict] = Field(default_factory=list)
    propagation_paths: list[dict] = Field(default_factory=list)
    exposed_sectors: list[str] = Field(default_factory=list)
    active_scenarios: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    graph_stats: dict = Field(default_factory=dict)
    duration_ms: float = 0.0
    audit_hash: str = ""


class PortfolioResponse(BaseModel):
    """Portfolio risk assessment response."""
    entities: list[RiskResponse] = Field(default_factory=list)
    portfolio_risk_score: float = 0.0
    portfolio_risk_level: str = "NOMINAL"
    systemic_risk_score: float = 0.0
    contagion_channels: list[str] = Field(default_factory=list)
    top_risks: list[dict] = Field(default_factory=list)
    total_duration_ms: float = 0.0
    audit_hash: str = ""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _result_to_response(r: RiskResult) -> RiskResponse:
    return RiskResponse(
        entity_id=r.entity_id,
        entity_label=r.entity_label,
        entity_type=r.entity_type,
        risk_score=r.risk_score,
        risk_level=r.risk_level.value,
        confidence=r.confidence,
        drivers=[d.model_dump() for d in r.drivers],
        propagation_paths=[p.model_dump() for p in r.propagation_paths],
        exposed_sectors=r.exposed_sectors,
        active_scenarios=r.active_scenarios,
        recommendations=r.recommendations,
        graph_stats=r.graph_stats,
        duration_ms=r.duration_ms,
        audit_hash=r.audit_hash,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/{entity_id:path}", response_model=RiskResponse)
async def assess_entity(
    entity_id: str = Path(..., description="GraphNode node_id (e.g., chokepoint:hormuz_strait)"),
) -> RiskResponse:
    """Assess risk for a single entity.

    Pipeline: Graph traversal → factor collection → URS scoring →
    scenario matching → recommendation generation
    """
    try:
        service = get_risk_service()
        result = service.assess_entity(entity_id)
        return _result_to_response(result)
    except Exception as exc:
        logger.error("Risk assessment failed for %s: %s", entity_id, exc)
        raise HTTPException(status_code=500, detail=f"Risk assessment error: {exc}")


@router.post("/portfolio", response_model=PortfolioResponse)
async def assess_portfolio(request: PortfolioRequest) -> PortfolioResponse:
    """Assess risk across multiple entities with systemic risk overlay."""
    try:
        service = get_risk_service()
        result = service.assess_portfolio(request.entity_ids)

        return PortfolioResponse(
            entities=[_result_to_response(r) for r in result.entity_results],
            portfolio_risk_score=result.portfolio_risk_score,
            portfolio_risk_level=result.portfolio_risk_level.value,
            systemic_risk_score=result.systemic_risk_score,
            contagion_channels=result.contagion_channels,
            top_risks=[d.model_dump() for d in result.top_risks],
            total_duration_ms=result.total_duration_ms,
            audit_hash=result.audit_hash,
        )
    except Exception as exc:
        logger.error("Portfolio assessment failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Portfolio assessment error: {exc}")


@router.get("/type/{entity_type}", response_model=PortfolioResponse)
async def assess_by_type(
    entity_type: str = Path(..., description="GraphEntityType value (e.g., country, sector)"),
) -> PortfolioResponse:
    """Assess all entities of a given type."""
    try:
        service = get_risk_service()
        result = service.assess_by_type(entity_type)

        return PortfolioResponse(
            entities=[_result_to_response(r) for r in result.entity_results],
            portfolio_risk_score=result.portfolio_risk_score,
            portfolio_risk_level=result.portfolio_risk_level.value,
            systemic_risk_score=result.systemic_risk_score,
            contagion_channels=result.contagion_channels,
            top_risks=[d.model_dump() for d in result.top_risks],
            total_duration_ms=result.total_duration_ms,
            audit_hash=result.audit_hash,
        )
    except Exception as exc:
        logger.error("Type assessment failed for %s: %s", entity_type, exc)
        raise HTTPException(status_code=500, detail=f"Type assessment error: {exc}")


@router.get("/heatmap", response_model=dict)
async def risk_heatmap() -> dict[str, Any]:
    """Generate risk heatmap data across all entity types."""
    try:
        service = get_risk_service()
        return service.risk_heatmap()
    except Exception as exc:
        logger.error("Heatmap generation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Heatmap error: {exc}")
