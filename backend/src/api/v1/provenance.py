"""v1 Metrics Provenance API — exposes the 5 explainability engines.

GET /api/v1/runs/{run_id}/metrics-provenance  — why this number
GET /api/v1/runs/{run_id}/factor-breakdown    — top drivers
GET /api/v1/runs/{run_id}/metric-ranges       — uncertainty bands
GET /api/v1/runs/{run_id}/decision-reasoning  — why this decision
GET /api/v1/runs/{run_id}/data-basis          — data period + freshness
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from src.core.rbac import enforce_permission, get_role_from_request
from src.services import run_store
from src.schemas.provenance_models import (
    MetricsProvenanceResponse,
    FactorBreakdownResponse,
    MetricRangesResponse,
    DecisionReasoningResponse,
    DataBasisResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/runs", tags=["provenance"])


def _get_org_from_request(request: Request) -> str:
    """Extract org from JWT token, default to 'default' for API key auth."""
    from src.services.auth_service import verify_token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[7:]
        payload = verify_token(token)
        if payload:
            return payload.get("org", "default")
    return "default"


async def _load_run(run_id: str, request: Request) -> dict:
    """Load run result or raise 404."""
    result = await run_store.aget_for_org(run_id, org=_get_org_from_request(request))
    if not result:
        raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
    return result


def _get_provenance_data(result: dict, run_id: str) -> dict:
    """Extract pre-computed provenance layer data from run result.

    If provenance was not pre-computed (legacy runs), compute on-the-fly.
    """
    prov = result.get("provenance_layer")
    if prov:
        return prov

    # Fallback: compute on the fly for legacy runs
    from src.metrics_provenance.pipeline import run_provenance_pipeline
    prov_result = run_provenance_pipeline(result)
    return prov_result.to_dict()


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/v1/runs/{run_id}/metrics-provenance
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{run_id}/metrics-provenance",
    response_model=MetricsProvenanceResponse,
    summary="Metric provenance — why this number",
    description=(
        "For each major metric, returns the formula, source data, "
        "contributing factors, model basis, and confidence notes."
    ),
)
async def get_metrics_provenance(run_id: str, request: Request):
    """Get metric provenance for all major metrics in a run."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await _load_run(run_id, request)

    prov = _get_provenance_data(result, run_id)
    metrics = prov.get("metric_provenance", [])

    return MetricsProvenanceResponse(
        run_id=run_id,
        scenario_id=result.get("scenario_id", ""),
        metrics=metrics,
        total_metrics=len(metrics),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/v1/runs/{run_id}/factor-breakdown
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{run_id}/factor-breakdown",
    response_model=FactorBreakdownResponse,
    summary="Factor breakdown — what drove this number",
    description=(
        "Decomposes every major metric into its top contributing factors. "
        "Factors sum coherently — no unexplained residuals."
    ),
)
async def get_factor_breakdown(run_id: str, request: Request):
    """Get factor breakdowns for all major metrics in a run."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await _load_run(run_id, request)

    prov = _get_provenance_data(result, run_id)
    breakdowns = prov.get("factor_breakdowns", [])

    return FactorBreakdownResponse(
        run_id=run_id,
        scenario_id=result.get("scenario_id", ""),
        breakdowns=breakdowns,
        total_metrics=len(breakdowns),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/v1/runs/{run_id}/metric-ranges
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{run_id}/metric-ranges",
    response_model=MetricRangesResponse,
    summary="Metric ranges — uncertainty bands",
    description=(
        "Replaces false-precision fixed points with honest uncertainty bands. "
        "Each metric has [min, expected, max] tied to severity and confidence."
    ),
)
async def get_metric_ranges(run_id: str, request: Request):
    """Get uncertainty ranges for all major metrics in a run."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await _load_run(run_id, request)

    prov = _get_provenance_data(result, run_id)
    ranges = prov.get("metric_ranges", [])

    return MetricRangesResponse(
        run_id=run_id,
        scenario_id=result.get("scenario_id", ""),
        ranges=ranges,
        total_metrics=len(ranges),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/v1/runs/{run_id}/decision-reasoning
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{run_id}/decision-reasoning",
    response_model=DecisionReasoningResponse,
    summary="Decision reasoning — why this decision, why this rank",
    description=(
        "For each decision: why it was recommended, why now, "
        "why it ranks where it does, propagation link, regime link, "
        "trust link, and tradeoff summary."
    ),
)
async def get_decision_reasoning(run_id: str, request: Request):
    """Get reasoning explanations for all decisions in a run."""
    enforce_permission(get_role_from_request(request), "run:explanation")
    result = await _load_run(run_id, request)

    prov = _get_provenance_data(result, run_id)
    reasonings = prov.get("decision_reasonings", [])

    return DecisionReasoningResponse(
        run_id=run_id,
        scenario_id=result.get("scenario_id", ""),
        reasonings=reasonings,
        total_decisions=len(reasonings),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/v1/runs/{run_id}/data-basis
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{run_id}/data-basis",
    response_model=DataBasisResponse,
    summary="Data basis — what data period backs this metric",
    description=(
        "For each metric: historical analog, scenario model basis, "
        "calibration period, freshness assessment. "
        "Weak freshness is explicitly flagged."
    ),
)
async def get_data_basis(run_id: str, request: Request):
    """Get data basis records for all metrics in a run."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await _load_run(run_id, request)

    prov = _get_provenance_data(result, run_id)
    bases = prov.get("data_bases", [])

    weak_count = sum(1 for b in bases if b.get("freshness_weak", False))

    return DataBasisResponse(
        run_id=run_id,
        scenario_id=result.get("scenario_id", ""),
        data_bases=bases,
        total_metrics=len(bases),
        weak_freshness_count=weak_count,
    )
