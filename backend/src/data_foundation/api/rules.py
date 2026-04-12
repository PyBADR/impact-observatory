"""Decision Rules API routes."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.api.deps import get_session
from src.data_foundation.models.converters import rule_to_orm, rule_from_orm
from src.data_foundation.repositories.rule_repo import RuleRepository
from src.data_foundation.schemas.decision_rules import DecisionRule

router = APIRouter(prefix="/foundation/rules", tags=["Data Foundation — Decision Rules"])


@router.get("", response_model=list[dict])
async def list_rules(
    active_only: bool = Query(False),
    action: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    repo = RuleRepository(session)
    if active_only:
        rows = await repo.find_active()
    elif action:
        rows = await repo.find_by_action(action)
    else:
        rows = await repo.list_all(limit=limit, offset=offset)
    return [rule_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/{rule_id}")
async def get_rule(rule_id: str, session: AsyncSession = Depends(get_session)):
    repo = RuleRepository(session)
    row = await repo.get_by_pk(rule_id)
    if not row:
        raise HTTPException(404, f"Rule '{rule_id}' not found")
    return rule_from_orm(row).model_dump(mode="json")


@router.post("", status_code=201)
async def create_rule(body: DecisionRule, session: AsyncSession = Depends(get_session)):
    repo = RuleRepository(session)
    existing = await repo.get_by_pk(body.rule_id)
    if existing:
        raise HTTPException(409, f"Rule '{body.rule_id}' already exists")
    orm = rule_to_orm(body)
    await repo.create(orm)
    await session.commit()
    return rule_from_orm(orm).model_dump(mode="json")


@router.put("/{rule_id}")
async def upsert_rule(
    rule_id: str,
    body: DecisionRule,
    session: AsyncSession = Depends(get_session),
):
    if body.rule_id != rule_id:
        raise HTTPException(400, "rule_id in path and body must match")
    repo = RuleRepository(session)
    orm = rule_to_orm(body)
    merged = await repo.upsert(orm)
    await session.commit()
    return rule_from_orm(merged).model_dump(mode="json")


@router.patch("/{rule_id}/activate", status_code=200)
async def activate_rule(rule_id: str, session: AsyncSession = Depends(get_session)):
    repo = RuleRepository(session)
    row = await repo.update_fields(rule_id, is_active=True)
    if not row:
        raise HTTPException(404, f"Rule '{rule_id}' not found")
    await session.commit()
    return {"rule_id": rule_id, "is_active": True}


@router.patch("/{rule_id}/deactivate", status_code=200)
async def deactivate_rule(rule_id: str, session: AsyncSession = Depends(get_session)):
    repo = RuleRepository(session)
    row = await repo.update_fields(rule_id, is_active=False)
    if not row:
        raise HTTPException(404, f"Rule '{rule_id}' not found")
    await session.commit()
    return {"rule_id": rule_id, "is_active": False}
