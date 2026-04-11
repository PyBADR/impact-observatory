"""Actual Outcome repository — domain-specific queries."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.outcome_tables import DecisionActualOutcomeORM
from src.data_foundation.repositories.base import BaseRepository


class ActualOutcomeRepository(BaseRepository[DecisionActualOutcomeORM]):
    model_class = DecisionActualOutcomeORM
    pk_field = "actual_outcome_id"

    async def find_by_expected_outcome(self, expected_outcome_id: str) -> Optional[DecisionActualOutcomeORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.expected_outcome_id == expected_outcome_id)
            .order_by(self.model_class.observed_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_event(self, event_id: str) -> Sequence[DecisionActualOutcomeORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.event_id == event_id)
            .order_by(self.model_class.observed_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
