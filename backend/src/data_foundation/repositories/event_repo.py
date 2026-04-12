"""Event Signals repository — domain-specific queries."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.tables import EventSignalORM
from src.data_foundation.repositories.base import BaseRepository


class EventRepository(BaseRepository[EventSignalORM]):
    model_class = EventSignalORM
    pk_field = "event_id"

    async def find_by_severity(
        self,
        min_score: float = 0.5,
        *,
        limit: int = 100,
    ) -> Sequence[EventSignalORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.severity_score >= min_score)
            .order_by(self.model_class.severity_score.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_category(
        self,
        category: str,
        *,
        limit: int = 100,
    ) -> Sequence[EventSignalORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.category == category)
            .order_by(self.model_class.event_time.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_recent(
        self,
        *,
        since: Optional[datetime] = None,
        limit: int = 50,
    ) -> Sequence[EventSignalORM]:
        stmt = select(self.model_class).order_by(self.model_class.event_time.desc())
        if since:
            stmt = stmt.where(self.model_class.event_time >= since)
        stmt = stmt.limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_ongoing(self) -> Sequence[EventSignalORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_ongoing == True)  # noqa: E712
            .order_by(self.model_class.severity_score.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
