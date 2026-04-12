"""Decision Rules repository — domain-specific queries."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select

from src.data_foundation.models.tables import DecisionRuleORM
from src.data_foundation.repositories.base import BaseRepository


class RuleRepository(BaseRepository[DecisionRuleORM]):
    model_class = DecisionRuleORM
    pk_field = "rule_id"

    async def find_active(self) -> Sequence[DecisionRuleORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_active == True)  # noqa: E712
            .order_by(self.model_class.escalation_level.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_action(self, action: str) -> Sequence[DecisionRuleORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.action == action)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
