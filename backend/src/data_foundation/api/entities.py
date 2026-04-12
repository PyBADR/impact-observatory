"""Entity Registry API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.api.deps import get_session
from src.data_foundation.models.converters import entity_to_orm, entity_from_orm
from src.data_foundation.repositories.entity_repo import EntityRepository
from src.data_foundation.schemas.entity_registry import EntityRegistryEntry

router = APIRouter(prefix="/foundation/entities", tags=["Data Foundation — Entities"])


@router.get("", response_model=list[dict])
async def list_entities(
    country: Optional[str] = Query(None, description="Filter by GCC country code"),
    entity_type: Optional[str] = Query(None, description="Filter by entity type"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    repo = EntityRepository(session)
    rows = await repo.search(
        country=country,
        entity_type=entity_type,
        sector=sector,
        is_active=is_active,
        limit=limit,
        offset=offset,
    )
    return [entity_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/count")
async def count_entities(
    country: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    repo = EntityRepository(session)
    filters = {}
    if country:
        filters["country"] = country
    total = await repo.count(filters=filters)
    return {"count": total}


@router.get("/{entity_id}")
async def get_entity(entity_id: str, session: AsyncSession = Depends(get_session)):
    repo = EntityRepository(session)
    row = await repo.get_by_pk(entity_id)
    if not row:
        raise HTTPException(404, f"Entity '{entity_id}' not found")
    return entity_from_orm(row).model_dump(mode="json")


@router.post("", status_code=201)
async def create_entity(body: EntityRegistryEntry, session: AsyncSession = Depends(get_session)):
    repo = EntityRepository(session)
    existing = await repo.get_by_pk(body.entity_id)
    if existing:
        raise HTTPException(409, f"Entity '{body.entity_id}' already exists")
    orm = entity_to_orm(body)
    await repo.create(orm)
    await session.commit()
    return entity_from_orm(orm).model_dump(mode="json")


@router.put("/{entity_id}")
async def upsert_entity(
    entity_id: str,
    body: EntityRegistryEntry,
    session: AsyncSession = Depends(get_session),
):
    if body.entity_id != entity_id:
        raise HTTPException(400, "entity_id in path and body must match")
    repo = EntityRepository(session)
    orm = entity_to_orm(body)
    merged = await repo.upsert(orm)
    await session.commit()
    return entity_from_orm(merged).model_dump(mode="json")


@router.delete("/{entity_id}", status_code=204)
async def delete_entity(entity_id: str, session: AsyncSession = Depends(get_session)):
    repo = EntityRepository(session)
    deleted = await repo.delete_by_pk(entity_id)
    if not deleted:
        raise HTTPException(404, f"Entity '{entity_id}' not found")
    await session.commit()
