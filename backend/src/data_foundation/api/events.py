"""Event Signals API routes."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.api.deps import get_session
from src.data_foundation.models.converters import event_to_orm, event_from_orm
from src.data_foundation.repositories.event_repo import EventRepository
from src.data_foundation.schemas.event_signals import EventSignal

router = APIRouter(prefix="/foundation/events", tags=["Data Foundation — Events"])


@router.get("", response_model=list[dict])
async def list_events(
    category: Optional[str] = Query(None),
    min_severity: Optional[float] = Query(None, ge=0.0, le=1.0),
    is_ongoing: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    repo = EventRepository(session)
    if min_severity is not None:
        rows = await repo.find_by_severity(min_severity, limit=limit)
    elif category:
        rows = await repo.find_by_category(category, limit=limit)
    elif is_ongoing:
        rows = await repo.find_ongoing()
    else:
        rows = await repo.list_all(limit=limit, offset=offset)
    return [event_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/recent")
async def recent_events(
    hours: int = Query(24, ge=1, le=720),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    repo = EventRepository(session)
    since = datetime.utcnow().replace(hour=0, minute=0) if hours >= 24 else None
    rows = await repo.find_recent(since=since, limit=limit)
    return [event_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/{event_id}")
async def get_event(event_id: str, session: AsyncSession = Depends(get_session)):
    repo = EventRepository(session)
    row = await repo.get_by_pk(event_id)
    if not row:
        raise HTTPException(404, f"Event '{event_id}' not found")
    return event_from_orm(row).model_dump(mode="json")


@router.post("", status_code=201)
async def create_event(body: EventSignal, session: AsyncSession = Depends(get_session)):
    repo = EventRepository(session)
    existing = await repo.get_by_pk(body.event_id)
    if existing:
        raise HTTPException(409, f"Event '{body.event_id}' already exists")
    orm = event_to_orm(body)
    await repo.create(orm)
    await session.commit()
    return event_from_orm(orm).model_dump(mode="json")
