"""Replay Run Result repository — domain-specific queries."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select

from src.data_foundation.models.outcome_tables import ReplayRunResultORM
from src.data_foundation.repositories.base import BaseRepository


class ReplayResultRepository(BaseRepository[ReplayRunResultORM]):
    model_class = ReplayRunResultORM
    pk_field = "replay_result_id"

    async def find_by_run(self, replay_run_id: str) -> Sequence[ReplayRunResultORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.replay_run_id == replay_run_id)
            .order_by(self.model_class.created_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_event(self, event_id: str) -> Sequence[ReplayRunResultORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.event_id == event_id)
            .order_by(self.model_class.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
