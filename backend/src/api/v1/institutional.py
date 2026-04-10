"""v1 Institutional Interface API — exposes Stage 70/80 outputs.

GET /api/v1/runs/{run_id}/calibration        — Stage 70 calibration layer
GET /api/v1/runs/{run_id}/trust              — Stage 80 trust layer
GET /api/v1/runs/{run_id}/explainability     — decision explanations + overrides
GET /api/v1/runs/{run_id}/audit-trail        — SHA-256 hashed audit log
GET /api/v1/runs/{run_id}/decision-summary   — normalized decision summary
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request

from src.core.rbac import enforce_permission, get_role_from_request
from src.services import run_store
from src.schemas.institutional_interface import (
    CalibrationLayerResponse,
    TrustLayerResponse,
    ExplainabilityResponse,
    AuditTrailResponse,
    DecisionSummaryResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/runs", tags=["institutional"])


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


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/v1/runs/{run_id}/calibration
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{run_id}/calibration",
    response_model=CalibrationLayerResponse,
    summary="Stage 70 Calibration Layer output",
    description="Returns audit, ranking, authority, calibration, and trust results from Stage 70.",
)
async def get_calibration(run_id: str, request: Request):
    """Get full calibration layer output for a completed run."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await _load_run(run_id, request)

    cal = result.get("decision_calibration", {})
    if not cal:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} has no calibration data (Stage 70 may not have completed)",
        )

    return CalibrationLayerResponse(
        run_id=run_id,
        stage=70,
        audit_results=cal.get("audit_results", []),
        ranked_decisions=cal.get("ranked_decisions", []),
        authority_assignments=cal.get("authority_assignments", []),
        calibration_results=cal.get("calibration_results", []),
        trust_results=cal.get("trust_results", []),
        stage_timings=cal.get("stage_timings", {}),
        total_time_ms=cal.get("total_time_ms", 0.0),
        counts=cal.get("counts", {}),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/v1/runs/{run_id}/trust
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{run_id}/trust",
    response_model=TrustLayerResponse,
    summary="Stage 80 Trust Layer output",
    description="Returns validation, authority profiles, explanations, learning, and overrides from Stage 80.",
)
async def get_trust(run_id: str, request: Request):
    """Get full trust layer output for a completed run."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await _load_run(run_id, request)

    trust = result.get("decision_trust", {})
    if not trust:
        raise HTTPException(
            status_code=404,
            detail=f"Run {run_id} has no trust data (Stage 80 may not have completed)",
        )

    return TrustLayerResponse(
        run_id=run_id,
        stage=80,
        scenario_validation=trust.get("scenario_validation", {}),
        validation_results=trust.get("validation_results", []),
        authority_profiles=trust.get("authority_profiles", []),
        explanations=trust.get("explanations", []),
        learning_updates=trust.get("learning_updates", []),
        override_results=trust.get("override_results", []),
        stage_timings=trust.get("stage_timings", {}),
        total_time_ms=trust.get("total_time_ms", 0.0),
        counts=trust.get("counts", {}),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/v1/runs/{run_id}/explainability
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{run_id}/explainability",
    response_model=ExplainabilityResponse,
    summary="Decision explainability pack",
    description=(
        "Institutional-grade explanations for every decision. "
        "Includes causal path, propagation summary, regime context, "
        "ranking rationale, and override verdicts."
    ),
)
async def get_explainability(run_id: str, request: Request):
    """Get explainability pack for all decisions in a completed run."""
    enforce_permission(get_role_from_request(request), "run:explanation")
    result = await _load_run(run_id, request)

    trust = result.get("decision_trust", {})
    sv = trust.get("scenario_validation", {})

    overrides = trust.get("override_results", [])

    return ExplainabilityResponse(
        run_id=run_id,
        scenario_id=result.get("scenario_id", ""),
        scenario_type=sv.get("scenario_type", ""),
        taxonomy_confidence=sv.get("classification_confidence", 0.0),
        explanations=trust.get("explanations", []),
        override_summary=overrides,
        total_decisions=len(overrides),
        blocked_count=sum(1 for o in overrides if o.get("final_status") == "BLOCKED"),
        human_required_count=sum(1 for o in overrides if o.get("final_status") == "HUMAN_REQUIRED"),
        auto_executable_count=sum(1 for o in overrides if o.get("final_status") == "AUTO_EXECUTABLE"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/v1/runs/{run_id}/audit-trail
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{run_id}/audit-trail",
    response_model=AuditTrailResponse,
    summary="SHA-256 audit trail",
    description="Immutable, hash-verified audit log for all decision chain outputs.",
)
async def get_audit_trail(run_id: str, request: Request):
    """Get the institutional audit trail for a completed run."""
    enforce_permission(get_role_from_request(request), "audit:read")

    # Verify run exists
    await _load_run(run_id, request)

    from src.services.institutional_audit import (
        get_audit_trail as _get_trail,
        verify_audit_integrity,
    )

    entries = _get_trail(run_id)
    is_valid, _corrupted = verify_audit_integrity(run_id)

    return AuditTrailResponse(
        run_id=run_id,
        entries=entries,
        total_entries=len(entries),
        integrity_verified=is_valid,
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  GET /api/v1/runs/{run_id}/decision-summary
# ═══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/{run_id}/decision-summary",
    response_model=DecisionSummaryResponse,
    summary="Normalized decision summary",
    description=(
        "Bridge object between internal engine outputs and frontend display. "
        "Returns a flat, per-decision summary with trust, ranking, calibration, "
        "and execution status."
    ),
)
async def get_decision_summary(run_id: str, request: Request):
    """Get normalized decision summary for institutional display."""
    enforce_permission(get_role_from_request(request), "run:read")
    result = await _load_run(run_id, request)

    from src.services.decision_summary_builder import build_decision_summary
    summary = build_decision_summary(result)

    return DecisionSummaryResponse(**summary)
