"""Entity Registry repository — domain-specific queries."""

from __future__ import annotations

from typing import List, Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.tables import EntityRegistryORM
from src.data_foundation.repositories.base import BaseRepository


class EntityRepository(BaseRepository[EntityRegistryORM]):
    model_class = EntityRegistryORM
    pk_field = "entity_id"

    async def find_by_country(self, country: str, *, limit: int = 100) -> Sequence[EntityRegistryORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.country == country)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_type(self, entity_type: str, *, limit: int = 100) -> Sequence[EntityRegistryORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.entity_type == entity_type)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_sector(self, sector: str, *, limit: int = 100) -> Sequence[EntityRegistryORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.sector == sector)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_critical(self, min_score: float = 0.7) -> Sequence[EntityRegistryORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.criticality_score >= min_score)
            .order_by(self.model_class.criticality_score.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def search(
        self,
        *,
        country: Optional[str] = None,
        entity_type: Optional[str] = None,
        sector: Optional[str] = None,
        is_active: Optional[bool] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Sequence[EntityRegistryORM]:
        stmt = select(self.model_class)
        if country:
            stmt = stmt.where(self.model_class.country == country)
        if entity_type:
            stmt = stmt.where(self.model_class.entity_type == entity_type)
        if sector:
            stmt = stmt.where(self.model_class.sector == sector)
        if is_active is not None:
            stmt = stmt.where(self.model_class.is_active == is_active)
        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()
