"""Scoring endpoints — risk, disruption, exposure, confidence."""

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from src.engines.math.scoring import (
    composite_risk_score,
    confidence_score,
    disruption_score,
    exposure_score,
)

router = APIRouter(prefix="/scores", tags=["scores"])


class RiskRequest(BaseModel):
    event_severity: float = Field(ge=0, le=1)
    source_confidence: float = Field(ge=0, le=1, default=0.5)
    spatial_proximity: float = Field(ge=0, le=1, default=0.5)
    network_centrality: float = Field(ge=0, le=1, default=0.5)
    route_dependency: float = Field(ge=0, le=1, default=0.5)
    temporal_recency: float = Field(ge=0, le=1, default=1.0)
    congestion_pressure: float = Field(ge=0, le=1, default=0.0)
    exposure_sensitivity: float = Field(ge=0, le=1, default=0.5)


class DisruptionRequest(BaseModel):
    risk: float = Field(ge=0, le=1)
    reroute_cost: float = Field(ge=0, le=1, default=0.0)
    delay_cost: float = Field(ge=0, le=1, default=0.0)
    congestion: float = Field(ge=0, le=1, default=0.0)
    uncertainty: float = Field(ge=0, le=1, default=0.0)


@router.post("/risk")
async def compute_risk(req: RiskRequest):
    """Compute composite risk score with full factor explanation."""
    score, factors = composite_risk_score(
        event_severity=req.event_severity,
        source_confidence=req.source_confidence,
        spatial_proximity=req.spatial_proximity,
        network_centrality=req.network_centrality,
        route_dependency=req.route_dependency,
        temporal_recency=req.temporal_recency,
        congestion_pressure=req.congestion_pressure,
        exposure_sensitivity=req.exposure_sensitivity,
    )
    return {
        "score": score,
        "factors": [f.model_dump() for f in factors],
    }


@router.post("/disruption")
async def compute_disruption(req: DisruptionRequest):
    """Compute composite disruption score with explanation."""
    score, factors = disruption_score(
        risk=req.risk,
        reroute_cost=req.reroute_cost,
        delay_cost=req.delay_cost,
        congestion=req.congestion,
        uncertainty=req.uncertainty,
    )
    return {
        "score": score,
        "factors": [f.model_dump() for f in factors],
    }


@router.get("/confidence")
async def compute_confidence(
    source_quality: float = Query(0.5, ge=0, le=1),
    corroboration_count: int = Query(1, ge=0),
    data_freshness: float = Query(1.0, ge=0, le=1),
    signal_agreement: float = Query(0.5, ge=0, le=1),
):
    """Compute confidence score with explanation."""
    score, factors = confidence_score(
        source_quality=source_quality,
        corroboration_count=corroboration_count,
        data_freshness=data_freshness,
        signal_agreement=signal_agreement,
    )
    return {
        "score": score,
        "factors": [f.model_dump() for f in factors],
    }
