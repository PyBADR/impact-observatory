"""Replay Run repository — domain-specific queries."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select

from src.data_foundation.models.outcome_tables import ReplayRunORM
from src.data_foundation.repositories.base import BaseRepository


class ReplayRunRepository(BaseRepository[ReplayRunORM]):
    model_class = ReplayRunORM
    pk_field = "replay_run_id"

    async def find_by_event(self, source_event_id: str) -> Sequence[ReplayRunORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.source_event_id == source_event_id)
            .order_by(self.model_class.started_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_status(self, status: str, *, limit: int = 50) -> Sequence[ReplayRunORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.replay_status == status)
            .order_by(self.model_class.started_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_version(self, source_event_id: str) -> int:
        """Get the highest replay_version for a given event."""
        from sqlalchemy import func
        stmt = (
            select(func.coalesce(func.max(self.model_class.replay_version), 0))
            .where(self.model_class.source_event_id == source_event_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one()
