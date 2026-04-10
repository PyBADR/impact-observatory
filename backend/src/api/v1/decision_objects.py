"""v1 Decision Objects API — decision lifecycle management.

POST /api/v1/decision_objects                    — create decision
GET  /api/v1/decision_objects                    — list decisions (filtered)
GET  /api/v1/decision_objects/{decision_id}     — single decision
PUT  /api/v1/decision_objects/{decision_id}     — update decision
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query

from src.schemas.decision_object import (
    DecisionObject,
    DecisionObjectListResponse,
    CreateDecisionObjectRequest,
    UpdateDecisionObjectRequest,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/decision_objects", tags=["decision_objects"])

# ── In-memory store (matches banking_entities pattern) ────────────────────
_decision_store: dict[str, dict] = {}


@router.post("", status_code=201)
async def create_decision_object(body: CreateDecisionObjectRequest):
    """Create a structured decision object with ownership, timing, impact, and confidence."""
    decision_id = f"dec_{uuid.uuid4().hex[:12]}"
    now = datetime.utcnow().isoformat()
    
    decision_dict = body.model_dump(exclude_unset=True)
    decision_dict.update({
        "decision_id": decision_id,
        "created_at": now,
        "updated_at": now,
        "created_by": decision_dict.get("created_by") or "system",
    })
    
    # Calculate net_value if not provided
    if "net_value_usd" not in decision_dict or decision_dict["net_value_usd"] == 0.0:
        expected_impact = decision_dict.get("expected_impact_usd", 0.0)
        cost = decision_dict.get("cost_usd", 0.0)
        decision_dict["net_value_usd"] = expected_impact - cost
    
    _decision_store[decision_id] = decision_dict
    
    logger.info(
        "DecisionObject %s created (owner=%s, sector=%s, urgency=%s)",
        decision_id,
        decision_dict.get("owner"),
        decision_dict.get("sector"),
        decision_dict.get("urgency"),
    )
    
    return decision_dict


@router.get("")
async def list_decision_objects(
    owner: str | None = Query(None, description="Filter by owner"),
    sector: str | None = Query(None, description="Filter by sector"),
    urgency: str | None = Query(None, description="Filter by urgency"),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    """List decision objects with optional filtering by owner, sector, or urgency."""
    items = list(_decision_store.values())
    
    # Apply filters
    if owner:
        items = [d for d in items if d.get("owner") == owner]
    if sector:
        items = [d for d in items if d.get("sector") == sector]
    if urgency:
        items = [d for d in items if d.get("urgency") == urgency]
    
    # Apply pagination
    total = len(items)
    items = items[offset : offset + limit]
    
    return {
        "decision_objects": items,
        "count": len(items),
        "total": total,
        "offset": offset,
        "limit": limit,
    }


@router.get("/{decision_id}")
async def get_decision_object(decision_id: str):
    """Get a single decision object by ID."""
    obj = _decision_store.get(decision_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"DecisionObject {decision_id} not found")
    return obj


@router.put("/{decision_id}")
async def update_decision_object(decision_id: str, body: UpdateDecisionObjectRequest):
    """Update a decision object with partial fields."""
    obj = _decision_store.get(decision_id)
    if obj is None:
        raise HTTPException(status_code=404, detail=f"DecisionObject {decision_id} not found")
    
    update_dict = body.model_dump(exclude_unset=True)
    obj.update(update_dict)
    obj["updated_at"] = datetime.utcnow().isoformat()
    
    # Recalculate net_value if impact or cost changed
    if "expected_impact_usd" in update_dict or "cost_usd" in update_dict:
        expected_impact = obj.get("expected_impact_usd", 0.0)
        cost = obj.get("cost_usd", 0.0)
        obj["net_value_usd"] = expected_impact - cost
    
    logger.info("DecisionObject %s updated", decision_id)
    
    return obj
