"""v1 Values API — decision value computation and querying.

POST /api/v1/values/compute              — compute value from outcome
GET  /api/v1/values                      — list values (filtered)
GET  /api/v1/values/{value_id}           — single value
POST /api/v1/values/{value_id}/recompute — recompute with updated inputs

net_value = avoided_loss - (operational_cost + decision_cost + latency_cost)
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from src.services import value_store, outcome_store
from src.schemas.operator_decision import (
    DecisionValue,
    DecisionValueListResponse,
    ComputeValueRequest,
    RecomputeValueRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/values", tags=["values"])


@router.post("/compute", status_code=201)
async def compute_value(body: ComputeValueRequest):
    """Compute a decision value from a confirmed outcome.

    Resolves the source outcome to inherit source_decision_id and source_run_id.
    """
    body_dict = body.model_dump(exclude_unset=True)
    outcome_id = body_dict.get("source_outcome_id", "")

    if not outcome_id:
        raise HTTPException(status_code=400, detail="source_outcome_id is required")

    # Resolve outcome for lineage — reject if outcome not persisted
    outcome = outcome_store.get(outcome_id)
    if outcome is None:
        raise HTTPException(
            status_code=400,
            detail=f"source_outcome_id '{outcome_id}' references an outcome that does not exist",
        )
    if not outcome.get("source_decision_id"):
        logger.warning(
            "Value computed from outcome %s with no source_decision_id — lineage incomplete",
            outcome_id,
        )

    val = value_store.compute(body_dict, outcome=outcome)
    logger.info(
        "Value %s computed: net=%.2f classification=%s (outcome=%s)",
        val["value_id"], val["net_value"], val["value_classification"], outcome_id,
    )
    return val


@router.get("")
async def list_values(
    outcome_id: str | None  = Query(None, description="Filter by source_outcome_id"),
    decision_id: str | None = Query(None, description="Filter by source_decision_id"),
    run_id: str | None      = Query(None, description="Filter by source_run_id"),
    limit: int              = Query(100, ge=1, le=500),
    offset: int             = Query(0, ge=0),
):
    """List decision values with optional filtering. Warms cache from DB if empty."""
    items = await value_store.alist_values(
        outcome_id=outcome_id,
        decision_id=decision_id,
        run_id=run_id,
        limit=limit,
        offset=offset,
    )
    return {"values": items, "count": len(items)}


@router.get("/{value_id}")
async def get_value(value_id: str):
    """Get a single value by ID."""
    val = value_store.get(value_id)
    if val is None:
        raise HTTPException(status_code=404, detail=f"Value {value_id} not found")
    return val


@router.post("/{value_id}/recompute")
async def recompute_value(value_id: str, body: RecomputeValueRequest):
    """Recompute a value with updated cost inputs."""
    val = value_store.get(value_id)
    if val is None:
        raise HTTPException(status_code=404, detail=f"Value {value_id} not found")
    updated = value_store.recompute(value_id, body.model_dump(exclude_unset=True))
    logger.info(
        "Value %s recomputed: net=%.2f → %s",
        value_id, updated["net_value"], updated["value_classification"],
    )
    return updated
