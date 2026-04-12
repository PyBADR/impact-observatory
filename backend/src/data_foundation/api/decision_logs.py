"""Decision Logs API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.api.deps import get_session
from src.data_foundation.models.converters import dlog_to_orm, dlog_from_orm
from src.data_foundation.repositories.dlog_repo import DecisionLogRepository
from src.data_foundation.schemas.decision_logs import DecisionLogEntry

router = APIRouter(prefix="/foundation/decision-logs", tags=["Data Foundation — Decision Logs"])


@router.get("", response_model=list[dict])
async def list_logs(
    rule_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    repo = DecisionLogRepository(session)
    if rule_id:
        rows = await repo.find_by_rule(rule_id, limit=limit)
    elif status:
        rows = await repo.find_by_status(status, limit=limit)
    else:
        rows = await repo.list_all(limit=limit, offset=offset)
    return [dlog_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/pending")
async def pending_approvals(session: AsyncSession = Depends(get_session)):
    repo = DecisionLogRepository(session)
    rows = await repo.find_pending_approval()
    return [dlog_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/{log_id}")
async def get_log(log_id: str, session: AsyncSession = Depends(get_session)):
    repo = DecisionLogRepository(session)
    row = await repo.get_by_pk(log_id)
    if not row:
        raise HTTPException(404, f"Decision log '{log_id}' not found")
    return dlog_from_orm(row).model_dump(mode="json")


@router.post("", status_code=201)
async def create_log(body: DecisionLogEntry, session: AsyncSession = Depends(get_session)):
    repo = DecisionLogRepository(session)
    orm = dlog_to_orm(body)
    await repo.create(orm)
    await session.commit()
    return dlog_from_orm(orm).model_dump(mode="json")


@router.patch("/{log_id}/approve")
async def approve_log(
    log_id: str,
    reviewed_by: str = Query(...),
    notes: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    repo = DecisionLogRepository(session)
    from datetime import datetime, timezone
    row = await repo.update_fields(
        log_id,
        status="APPROVED",
        reviewed_by=reviewed_by,
        reviewed_at=datetime.now(timezone.utc),
        review_notes=notes,
    )
    if not row:
        raise HTTPException(404, f"Decision log '{log_id}' not found")
    await session.commit()
    return {"log_id": log_id, "status": "APPROVED"}


@router.patch("/{log_id}/reject")
async def reject_log(
    log_id: str,
    reviewed_by: str = Query(...),
    notes: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    repo = DecisionLogRepository(session)
    from datetime import datetime, timezone
    row = await repo.update_fields(
        log_id,
        status="REJECTED",
        reviewed_by=reviewed_by,
        reviewed_at=datetime.now(timezone.utc),
        review_notes=notes,
    )
    if not row:
        raise HTTPException(404, f"Decision log '{log_id}' not found")
    await session.commit()
    return {"log_id": log_id, "status": "REJECTED"}
