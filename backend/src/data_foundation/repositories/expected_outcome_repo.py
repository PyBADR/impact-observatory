"""Expected Outcome repository — domain-specific queries."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select

from src.data_foundation.models.outcome_tables import DecisionExpectedOutcomeORM
from src.data_foundation.repositories.base import BaseRepository


class ExpectedOutcomeRepository(BaseRepository[DecisionExpectedOutcomeORM]):
    model_class = DecisionExpectedOutcomeORM
    pk_field = "expected_outcome_id"

    async def find_by_decision_log(self, decision_log_id: str) -> Sequence[DecisionExpectedOutcomeORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_log_id == decision_log_id)
            .order_by(self.model_class.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_rule(self, rule_id: str, *, limit: int = 100) -> Sequence[DecisionExpectedOutcomeORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.rule_id == rule_id)
            .order_by(self.model_class.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_event(self, event_id: str) -> Sequence[DecisionExpectedOutcomeORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.event_id == event_id)
            .order_by(self.model_class.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
