"""v1 Decisions API — operator decision CRUD with full lineage tracking.

POST /api/v1/decisions                   — create operator decision (+ auto-create outcome)
GET  /api/v1/decisions                   — list decisions (filtered)
GET  /api/v1/decisions/{decision_id}     — single decision
POST /api/v1/decisions/{decision_id}/execute — transition to EXECUTED
POST /api/v1/decisions/{decision_id}/close   — transition to CLOSED

All decisions carry bidirectional linkage:
  decision → outcome_id, source_run_id, scenario_id
  outcome  → source_decision_id
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Query

from src.services import outcome_store
from src.services import decision_operator_store
from src.schemas.operator_decision import (
    OperatorDecision,
    OperatorDecisionListResponse,
    CreateOperatorDecisionRequest,
    ExecuteDecisionRequest,
    CloseDecisionRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decisions", tags=["decisions"])


@router.post("", status_code=201)
async def create_decision(body: CreateOperatorDecisionRequest):
    """Create an operator decision with auto-generated outcome.

    Establishes bidirectional linkage: decision.outcome_id ↔ outcome.source_decision_id.
    """
    body_dict = body.model_dump(exclude_unset=True)

    if not body_dict.get("source_run_id"):
        logger.warning(
            "Decision created without source_run_id — lineage incomplete (type=%s)",
            body_dict.get("decision_type", "UNKNOWN"),
        )

    # 1. Create the decision
    dec = decision_operator_store.create(body_dict)

    # 2. Auto-create a pending outcome linked to this decision
    payload = body_dict.get("decision_payload", {})
    avoided_loss = payload.get("loss_avoided_usd", 0) if isinstance(payload, dict) else 0
    outcome = outcome_store.create({
        "source_decision_id": dec["decision_id"],
        "source_run_id":      dec.get("source_run_id"),
        "source_signal_id":   dec.get("source_signal_id"),
        "source_seed_id":     dec.get("source_seed_id"),
        "expected_value":     avoided_loss if avoided_loss > 0 else None,
    })

    # 3. Bidirectional linkage: write outcome_id back to decision
    linked = decision_operator_store.update(dec["decision_id"], {
        "outcome_id": outcome["outcome_id"],
    })
    if linked is None:
        logger.error(
            "Linkage write failed: outcome_id=%s not written to decision=%s — retrying",
            outcome["outcome_id"], dec["decision_id"],
        )
        # Retry once: re-fetch from DB in case cache was stale, then update again
        retried = await decision_operator_store.aget(dec["decision_id"])
        if retried is not None:
            decision_operator_store.update(dec["decision_id"], {"outcome_id": outcome["outcome_id"]})
            logger.info("Linkage retry succeeded for decision=%s", dec["decision_id"])
        else:
            logger.error(
                "Linkage retry failed: decision=%s not found in cache or DB — outcome linkage incomplete",
                dec["decision_id"],
            )
    dec["outcome_id"] = outcome["outcome_id"]

    logger.info(
        "Decision %s created → outcome %s (run=%s, scenario=%s)",
        dec["decision_id"], outcome["outcome_id"],
        dec.get("source_run_id"), dec.get("scenario_id"),
    )
    return dec


@router.get("")
async def list_decisions(
    status: str | None        = Query(None, description="Filter by decision_status"),
    decision_type: str | None = Query(None, description="Filter by decision_type"),
    run_id: str | None        = Query(None, description="Filter by source_run_id"),
    scenario_id: str | None   = Query(None, description="Filter by scenario_id"),
    limit: int                = Query(100, ge=1, le=500),
    offset: int               = Query(0, ge=0),
):
    """List operator decisions with optional filtering. Warms cache from DB if empty."""
    items = await decision_operator_store.alist_decisions(
        status=status,
        decision_type=decision_type,
        run_id=run_id,
        scenario_id=scenario_id,
        limit=limit,
        offset=offset,
    )
    return {"decisions": items, "count": len(items)}


@router.get("/{decision_id}")
async def get_decision(decision_id: str):
    """Get a single decision by ID."""
    dec = decision_operator_store.get(decision_id)
    if dec is None:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    return dec


@router.post("/{decision_id}/execute")
async def execute_decision(decision_id: str, body: ExecuteDecisionRequest | None = None):
    """Transition a decision to EXECUTED status."""
    dec = decision_operator_store.get(decision_id)
    if dec is None:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    if dec["decision_status"] not in ("CREATED", "IN_REVIEW"):
        raise HTTPException(
            status_code=409,
            detail=f"Cannot execute decision in {dec['decision_status']} status",
        )
    updated = decision_operator_store.execute(
        decision_id,
        executed_by=body.executed_by if body else None,
        notes=body.notes if body else None,
    )

    # Keep outcome state consistent with decision state after execute.
    outcome_id = dec.get("outcome_id")
    if outcome_id:
        synced = outcome_store.update(outcome_id, {"outcome_status": "OBSERVED"})
        if synced is None:
            logger.warning(
                "Outcome sync skipped: outcome_id=%s not found in cache (decision=%s)",
                outcome_id, decision_id,
            )
        else:
            logger.debug("Synced outcome %s → OBSERVED on decision execute", outcome_id)

    return updated


@router.post("/{decision_id}/close")
async def close_decision(decision_id: str, body: CloseDecisionRequest | None = None):
    """Transition a decision to CLOSED status."""
    dec = decision_operator_store.get(decision_id)
    if dec is None:
        raise HTTPException(status_code=404, detail=f"Decision {decision_id} not found")
    if dec["decision_status"] == "CLOSED":
        raise HTTPException(status_code=409, detail="Decision already closed")
    updated = decision_operator_store.close(
        decision_id,
        outcome_status=body.outcome_status if body else None,
        closed_by=body.closed_by if body else None,
    )
    return updated
