"""v1 Outcomes API — outcome lifecycle management.

POST /api/v1/outcomes                        — create outcome
GET  /api/v1/outcomes                        — list outcomes (filtered)
GET  /api/v1/outcomes/{outcome_id}           — single outcome
POST /api/v1/outcomes/{outcome_id}/observe   — transition to OBSERVED
POST /api/v1/outcomes/{outcome_id}/confirm   — transition to CONFIRMED
POST /api/v1/outcomes/{outcome_id}/dispute   — transition to DISPUTED
POST /api/v1/outcomes/{outcome_id}/close     — transition to CLOSED

Lifecycle: PENDING_OBSERVATION → OBSERVED → CONFIRMED → DISPUTED → CLOSED/FAILED
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from src.services import outcome_store
from src.schemas.operator_decision import (
    Outcome,
    OutcomeListResponse,
    CreateOutcomeRequest,
    ObserveOutcomeRequest,
    ConfirmOutcomeRequest,
    DisputeOutcomeRequest,
    CloseOutcomeRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/outcomes", tags=["outcomes"])


@router.post("", status_code=201)
async def create_outcome(body: CreateOutcomeRequest):
    """Create an outcome linked to a decision and/or run."""
    body_dict = body.model_dump(exclude_unset=True)
    out = outcome_store.create(body_dict)
    logger.info(
        "Outcome %s created (decision=%s, run=%s)",
        out["outcome_id"], out.get("source_decision_id"), out.get("source_run_id"),
    )
    return out


@router.get("")
async def list_outcomes(
    decision_id: str | None = Query(None, description="Filter by source_decision_id"),
    run_id: str | None      = Query(None, description="Filter by source_run_id"),
    status: str | None      = Query(None, description="Filter by outcome_status"),
    limit: int              = Query(100, ge=1, le=500),
    offset: int             = Query(0, ge=0),
):
    """List outcomes with optional filtering. Warms cache from DB if empty."""
    items = await outcome_store.alist_outcomes(
        decision_id=decision_id,
        run_id=run_id,
        status=status,
        limit=limit,
        offset=offset,
    )
    return {"outcomes": items, "count": len(items)}


@router.get("/{outcome_id}")
async def get_outcome(outcome_id: str):
    """Get a single outcome by ID."""
    out = outcome_store.get(outcome_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"Outcome {outcome_id} not found")
    return out


@router.post("/{outcome_id}/observe")
async def observe_outcome(outcome_id: str, body: ObserveOutcomeRequest):
    """Transition outcome to OBSERVED status with evidence."""
    out = outcome_store.get(outcome_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"Outcome {outcome_id} not found")
    if out["outcome_status"] != "PENDING_OBSERVATION":
        raise HTTPException(
            status_code=409,
            detail=f"Cannot observe outcome in {out['outcome_status']} status",
        )
    updated = outcome_store.observe(outcome_id, body.model_dump(exclude_unset=True))
    return updated


@router.post("/{outcome_id}/confirm")
async def confirm_outcome(outcome_id: str, body: ConfirmOutcomeRequest):
    """Transition outcome to CONFIRMED status with classification."""
    out = outcome_store.get(outcome_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"Outcome {outcome_id} not found")
    if out["outcome_status"] not in ("PENDING_OBSERVATION", "OBSERVED"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot confirm outcome in {out['outcome_status']} status",
        )
    updated = outcome_store.confirm(outcome_id, body.model_dump(exclude_unset=True))
    return updated


@router.post("/{outcome_id}/dispute")
async def dispute_outcome(outcome_id: str, body: DisputeOutcomeRequest):
    """Transition outcome to DISPUTED status."""
    out = outcome_store.get(outcome_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"Outcome {outcome_id} not found")
    if out["outcome_status"] not in ("OBSERVED", "CONFIRMED"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot dispute outcome in {out['outcome_status']} status",
        )
    updated = outcome_store.dispute(outcome_id, body.model_dump(exclude_unset=True))
    return updated


@router.post("/{outcome_id}/close")
async def close_outcome(outcome_id: str, body: CloseOutcomeRequest):
    """Transition outcome to CLOSED status."""
    out = outcome_store.get(outcome_id)
    if out is None:
        raise HTTPException(status_code=404, detail=f"Outcome {outcome_id} not found")
    if out["outcome_status"] == "CLOSED":
        raise HTTPException(status_code=409, detail="Outcome already closed")
    updated = outcome_store.close(outcome_id, body.model_dump(exclude_unset=True))
    return updated
