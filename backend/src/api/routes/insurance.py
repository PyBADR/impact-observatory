"""Insurance intelligence API endpoints.

/insurance/exposure     — Portfolio exposure scoring
/insurance/claims-surge — Claims surge prediction
/insurance/underwriting — Underwriting watch list
/insurance/severity     — Severity projection
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from src.engines.insurance_intelligence.portfolio_exposure import (
    compute_portfolio_exposure,
    PortfolioExposureResult,
)
from src.engines.insurance_intelligence.claims_surge import (
    compute_claims_surge,
    ClaimsSurgeResult,
)
from src.engines.insurance_intelligence.underwriting_watch import (
    evaluate_watch,
    generate_watch_list,
)
from src.engines.insurance_intelligence.severity_projection import (
    project_severity,
    SeverityProjectionReport,
)

router = APIRouter(prefix="/insurance", tags=["insurance"])


# ---- Request models ----

class ExposureRequest(BaseModel):
    portfolio_id: str
    tiv_normalized: float = Field(ge=0, le=1)
    route_dependency: float = Field(ge=0, le=1)
    region_risk: float = Field(ge=0, le=1)
    claims_elasticity: float = Field(ge=0, le=1)


class ClaimsSurgeRequest(BaseModel):
    entity_id: str
    risk: float = Field(ge=0, le=1)
    disruption: float = Field(ge=0, le=1)
    exposure: float = Field(ge=0, le=1)
    policy_sensitivity: float = Field(ge=0, le=1)
    base_claims_usd: float = Field(ge=0, default=0)
    system_stress: float = Field(ge=0, le=1, default=0)
    uncertainty: float = Field(ge=0, le=1, default=0)


class UnderwritingRequest(BaseModel):
    entity_ids: list[str]
    risk_scores: list[float]
    exposure_scores: list[float]
    surge_scores: list[float]
    chokepoint_deps: list[float] | None = None
    concentrations: list[float] | None = None


class SeverityRequest(BaseModel):
    entity_id: str
    current_severity: float = Field(ge=0, le=1)
    trend_factor: float = 0.0
    scenario_uplift: float = Field(ge=0, le=1, default=0)
    scenario_probability: float = Field(ge=0, le=1, default=0)
    stress_current: float = Field(ge=0, le=1, default=0)
    stress_previous: float = Field(ge=0, le=1, default=0)


# ---- Endpoints ----

@router.post("/exposure")
async def portfolio_exposure(req: ExposureRequest) -> dict:
    """Compute portfolio exposure score."""
    result = compute_portfolio_exposure(
        req.portfolio_id, req.tiv_normalized, req.route_dependency,
        req.region_risk, req.claims_elasticity,
    )
    return {
        "portfolio_id": result.portfolio_id,
        "exposure_score": result.exposure_score,
        "classification": result.classification,
        "tiv_contribution": result.tiv_contribution,
        "route_dependency_contribution": result.route_dependency_contribution,
        "region_risk_contribution": result.region_risk_contribution,
        "claims_elasticity_contribution": result.claims_elasticity_contribution,
        "recommendations": result.recommendations,
    }


@router.post("/claims-surge")
async def claims_surge(req: ClaimsSurgeRequest) -> dict:
    """Compute claims surge prediction."""
    result = compute_claims_surge(
        req.entity_id, req.risk, req.disruption, req.exposure,
        req.policy_sensitivity, req.base_claims_usd,
        req.system_stress, req.uncertainty,
    )
    return {
        "entity_id": result.entity_id,
        "surge_score": result.surge_score,
        "classification": result.classification,
        "claims_uplift_pct": result.claims_uplift_pct,
        "estimated_claims_delta_usd": result.estimated_claims_delta_usd,
        "risk_contribution": result.risk_contribution,
        "disruption_contribution": result.disruption_contribution,
        "exposure_contribution": result.exposure_contribution,
        "policy_sensitivity_contribution": result.policy_sensitivity_contribution,
    }


@router.post("/underwriting")
async def underwriting_watch(req: UnderwritingRequest) -> dict:
    """Generate underwriting watch list."""
    watch = generate_watch_list(
        req.entity_ids, req.risk_scores, req.exposure_scores,
        req.surge_scores, req.chokepoint_deps, req.concentrations,
    )
    return {
        "total_flagged": watch.total_flagged,
        "immediate_count": watch.immediate_count,
        "urgent_count": watch.urgent_count,
        "elevated_count": watch.elevated_count,
        "summary": watch.summary,
        "items": [
            {
                "entity_id": item.entity_id,
                "priority": item.priority.value,
                "risk_score": item.risk_score,
                "exposure_score": item.exposure_score,
                "surge_score": item.surge_score,
                "recommended_action": item.recommended_action,
                "triggers": [
                    {"type": t.trigger_type, "value": t.value,
                     "threshold": t.threshold, "detail": t.detail}
                    for t in item.triggers
                ],
            }
            for item in watch.items
        ],
    }


@router.post("/severity")
async def severity_projection(req: SeverityRequest) -> dict:
    """Project severity across time horizons."""
    report = project_severity(
        req.entity_id, req.current_severity, req.trend_factor,
        req.scenario_uplift, req.scenario_probability,
        req.stress_current, req.stress_previous,
    )
    return {
        "entity_id": report.entity_id,
        "current_severity": report.current_severity,
        "worst_case_severity": report.worst_case_severity,
        "worst_case_horizon": report.worst_case_horizon,
        "trend_direction": report.trend_direction,
        "recommendations": report.recommendations,
        "projections": [
            {
                "horizon": p.horizon_label,
                "projected_severity": p.projected_severity,
                "confidence": p.confidence,
                "classification": p.classification,
                "trend_component": p.trend_component,
                "scenario_component": p.scenario_component,
                "stress_component": p.stress_component,
            }
            for p in report.projections
        ],
    }
