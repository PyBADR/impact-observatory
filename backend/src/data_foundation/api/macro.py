"""Macro Indicators API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.api.deps import get_session
from src.data_foundation.models.converters import macro_to_orm, macro_from_orm
from src.data_foundation.repositories.macro_repo import MacroRepository
from src.data_foundation.schemas.macro_indicators import MacroIndicatorRecord

router = APIRouter(prefix="/foundation/macro", tags=["Data Foundation — Macro Indicators"])


@router.get("", response_model=list[dict])
async def list_macro(
    country: Optional[str] = Query(None),
    indicator_code: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    repo = MacroRepository(session)
    if country:
        rows = await repo.find_by_country(country, indicator_code=indicator_code, limit=limit)
    else:
        filters = {}
        if indicator_code:
            filters["indicator_code"] = indicator_code
        rows = await repo.list_all(limit=limit, offset=offset, filters=filters)
    return [macro_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/latest/{country}")
async def latest_by_country(country: str, session: AsyncSession = Depends(get_session)):
    repo = MacroRepository(session)
    rows = await repo.find_latest_by_country(country)
    return [macro_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/{indicator_id}")
async def get_macro(indicator_id: str, session: AsyncSession = Depends(get_session)):
    repo = MacroRepository(session)
    row = await repo.get_by_pk(indicator_id)
    if not row:
        raise HTTPException(404, f"Indicator '{indicator_id}' not found")
    return macro_from_orm(row).model_dump(mode="json")


@router.post("", status_code=201)
async def create_macro(body: MacroIndicatorRecord, session: AsyncSession = Depends(get_session)):
    repo = MacroRepository(session)
    orm = macro_to_orm(body)
    await repo.upsert(orm)
    await session.commit()
    return macro_from_orm(orm).model_dump(mode="json")
