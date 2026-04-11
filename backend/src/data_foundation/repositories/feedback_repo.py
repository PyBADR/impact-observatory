"""Analyst Feedback repository — domain-specific queries."""

from __future__ import annotations

from typing import Sequence

from sqlalchemy import select

from src.data_foundation.models.outcome_tables import AnalystFeedbackRecordORM
from src.data_foundation.repositories.base import BaseRepository


class FeedbackRepository(BaseRepository[AnalystFeedbackRecordORM]):
    model_class = AnalystFeedbackRecordORM
    pk_field = "feedback_id"

    async def find_by_decision_log(self, decision_log_id: str) -> Sequence[AnalystFeedbackRecordORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_log_id == decision_log_id)
            .order_by(self.model_class.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_evaluation(self, evaluation_id: str) -> Sequence[AnalystFeedbackRecordORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.evaluation_id == evaluation_id)
            .order_by(self.model_class.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_verdict(self, verdict: str, *, limit: int = 100) -> Sequence[AnalystFeedbackRecordORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.verdict == verdict)
            .order_by(self.model_class.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_analyst(self, analyst_name: str, *, limit: int = 100) -> Sequence[AnalystFeedbackRecordORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.analyst_name == analyst_name)
            .order_by(self.model_class.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
