"""Generic async repository for data_foundation ORM models."""

from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, Sequence, Type, TypeVar

from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres import Base

M = TypeVar("M", bound=Base)


class BaseRepository(Generic[M]):
    """Async CRUD repository for a single ORM model.

    Subclass and set `model_class` + `pk_field` to get typed CRUD for free.
    """

    model_class: Type[M]
    pk_field: str  # e.g. "entity_id", "event_id"

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── CREATE ───────────────────────────────────────────────────────────

    async def create(self, obj: M) -> M:
        self.session.add(obj)
        await self.session.flush()
        return obj

    async def create_many(self, objs: List[M]) -> List[M]:
        self.session.add_all(objs)
        await self.session.flush()
        return objs

    async def upsert(self, obj: M) -> M:
        """Merge (insert or update) based on primary key."""
        merged = await self.session.merge(obj)
        await self.session.flush()
        return merged

    # ── READ ─────────────────────────────────────────────────────────────

    async def get_by_pk(self, pk_value: str) -> Optional[M]:
        pk_col = getattr(self.model_class, self.pk_field)
        stmt = select(self.model_class).where(pk_col == pk_value)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self,
        *,
        limit: int = 100,
        offset: int = 0,
        tenant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> Sequence[M]:
        stmt = select(self.model_class)
        if tenant_id is not None:
            stmt = stmt.where(self.model_class.tenant_id == tenant_id)
        if filters:
            for col_name, val in filters.items():
                col = getattr(self.model_class, col_name, None)
                if col is not None:
                    stmt = stmt.where(col == val)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count(
        self,
        *,
        tenant_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> int:
        pk_col = getattr(self.model_class, self.pk_field)
        stmt = select(func.count(pk_col))
        if tenant_id is not None:
            stmt = stmt.where(self.model_class.tenant_id == tenant_id)
        if filters:
            for col_name, val in filters.items():
                col = getattr(self.model_class, col_name, None)
                if col is not None:
                    stmt = stmt.where(col == val)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ── UPDATE ───────────────────────────────────────────────────────────

    async def update_fields(self, pk_value: str, **kwargs: Any) -> Optional[M]:
        pk_col = getattr(self.model_class, self.pk_field)
        stmt = (
            update(self.model_class)
            .where(pk_col == pk_value)
            .values(**kwargs)
            .returning(self.model_class)
        )
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.scalar_one_or_none()

    # ── DELETE ───────────────────────────────────────────────────────────

    async def delete_by_pk(self, pk_value: str) -> bool:
        pk_col = getattr(self.model_class, self.pk_field)
        stmt = delete(self.model_class).where(pk_col == pk_value)
        result = await self.session.execute(stmt)
        await self.session.flush()
        return result.rowcount > 0
