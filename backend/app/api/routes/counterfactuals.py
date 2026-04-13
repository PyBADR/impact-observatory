"""
Impact Observatory | مرصد الأثر — Phase 2 Counterfactuals API Route

POST /api/v1/counterfactuals/{slug}

Runs the base scenario, then simulates "what if" branches for each
fired decision. Returns the no_action baseline plus per-decision
counterfactual branches showing loss reduction.
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from app.domain.simulation.counterfactual_engine import (
    CounterfactualEngine,
    CounterfactualResult,
)
from app.domain.simulation.scenario_registry import get_scenario
from app.domain.simulation.schemas import (
    CountryImpact,
    DecisionAction,
    RiskLevel,
    SectorImpact,
    Urgency,
)

logger = logging.getLogger("observatory.counterfactuals")

router = APIRouter(
    prefix="/counterfactuals",
    tags=["counterfactuals-phase2"],
)

_engine = CounterfactualEngine()


# ═══════════════════════════════════════════════════════════════════════════════
# Request / Response Schemas
# ═══════════════════════════════════════════════════════════════════════════════

class CounterfactualRequest(BaseModel):
    severity: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    horizon_hours: Optional[int] = Field(default=None, ge=1, le=8760)
    extra_params: dict[str, Any] = Field(default_factory=dict)


class BranchResponse(BaseModel):
    """Wire format for a single counterfactual branch."""
    action: str
    owner: str
    timing: str
    total_loss_usd: float
    loss_reduction_usd: float
    loss_reduction_pct: float
    risk_level: RiskLevel
    confidence: float
    top_country_code: str | None = None
    top_country_loss_usd: float | None = None
    top_sector: str | None = None
    top_sector_stress: float | None = None
    pathway_headline: str
    downside_risk: str


class NoActionResponse(BaseModel):
    total_loss_usd: float
    risk_level: RiskLevel
    confidence: float
    decision_count: int
    pathway_headlines: list[str]


class CounterfactualResponse(BaseModel):
    scenario_slug: str
    severity: float
    horizon_hours: int
    no_action: NoActionResponse
    branches: list[BranchResponse]
    best_action: str | None = None
    best_action_saves_usd: float | None = None
    combined_max_avoidable_usd: float
    combined_max_avoidable_pct: float


# ═══════════════════════════════════════════════════════════════════════════════
# Route
# ═══════════════════════════════════════════════════════════════════════════════

@router.post(
    "/{slug}",
    response_model=CounterfactualResponse,
    summary="Run counterfactual analysis for a scenario",
    description=(
        "Runs the baseline scenario, then re-simulates with each decision applied. "
        "Returns no_action + per-decision branches with loss reduction metrics."
    ),
)
async def run_counterfactual(slug: str, request: CounterfactualRequest) -> CounterfactualResponse:
    """Execute counterfactual analysis."""

    try:
        get_scenario(slug)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))

    try:
        result = _engine.analyze(
            slug,
            severity=request.severity,
            horizon_hours=request.horizon_hours,
            **request.extra_params,
        )

        # ── Map to wire format ───────────────────────────────────────────
        branches_out: list[BranchResponse] = []
        for b in result.branches:
            branches_out.append(BranchResponse(
                action=b.decision.action,
                owner=b.decision.owner,
                timing=b.decision.timing.value,
                total_loss_usd=b.total_loss_usd,
                loss_reduction_usd=b.loss_reduction_usd,
                loss_reduction_pct=b.loss_reduction_pct,
                risk_level=b.risk_level,
                confidence=b.confidence,
                top_country_code=(
                    b.top_country.country_code.value if b.top_country else None
                ),
                top_country_loss_usd=(
                    b.top_country.loss_usd if b.top_country else None
                ),
                top_sector=(
                    b.top_sector.sector_label if b.top_sector else None
                ),
                top_sector_stress=(
                    b.top_sector.stress if b.top_sector else None
                ),
                pathway_headline=b.pathway_headline,
                downside_risk=b.decision.downside_risk,
            ))

        return CounterfactualResponse(
            scenario_slug=result.scenario_slug,
            severity=result.severity,
            horizon_hours=result.horizon_hours,
            no_action=NoActionResponse(
                total_loss_usd=result.no_action.total_loss_usd,
                risk_level=result.no_action.risk_level,
                confidence=result.no_action.confidence,
                decision_count=len(result.no_action.decisions),
                pathway_headlines=result.no_action.pathway_headlines,
            ),
            branches=branches_out,
            best_action=(
                result.best_single_action.decision.action
                if result.best_single_action else None
            ),
            best_action_saves_usd=(
                result.best_single_action.loss_reduction_usd
                if result.best_single_action else None
            ),
            combined_max_avoidable_usd=result.combined_max_avoidable_usd,
            combined_max_avoidable_pct=result.combined_max_avoidable_pct,
        )

    except Exception as e:
        logger.exception("Counterfactual '%s' failed: %s", slug, str(e))
        raise HTTPException(status_code=500, detail=f"Counterfactual engine error: {str(e)}")
