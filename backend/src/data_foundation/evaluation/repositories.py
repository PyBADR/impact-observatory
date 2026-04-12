"""
Evaluation Layer — Typed Async Repositories
=============================================

7 repositories extending BaseRepository for each evaluation ORM model.
Each adds domain-specific query methods beyond basic CRUD.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.repositories.base import BaseRepository

from .orm_models import (
    ExpectedOutcomeORM,
    ActualOutcomeORM,
    DecisionEvaluationORM,
    AnalystFeedbackORM,
    ReplayRunORM,
    ReplayRunResultORM,
    RulePerformanceORM,
)


class ExpectedOutcomeRepo(BaseRepository[ExpectedOutcomeORM]):
    model_class = ExpectedOutcomeORM
    pk_field = "expected_outcome_id"

    async def get_by_decision_log(self, decision_log_id: str) -> Optional[ExpectedOutcomeORM]:
        stmt = select(self.model_class).where(
            self.model_class.decision_log_id == decision_log_id
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_rule(self, rule_id: str, limit: int = 100) -> Sequence[ExpectedOutcomeORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.rule_id == rule_id)
            .order_by(self.model_class.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ActualOutcomeRepo(BaseRepository[ActualOutcomeORM]):
    model_class = ActualOutcomeORM
    pk_field = "actual_outcome_id"

    async def get_by_expected(self, expected_outcome_id: str) -> Sequence[ActualOutcomeORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.expected_outcome_id == expected_outcome_id)
            .order_by(self.model_class.observed_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_complete(self, expected_outcome_id: str) -> Optional[ActualOutcomeORM]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.expected_outcome_id == expected_outcome_id,
                self.model_class.observation_completeness == "COMPLETE",
            )
            .order_by(self.model_class.observed_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class DecisionEvaluationRepo(BaseRepository[DecisionEvaluationORM]):
    model_class = DecisionEvaluationORM
    pk_field = "evaluation_id"

    async def get_by_rule(
        self, rule_id: str, limit: int = 100
    ) -> Sequence[DecisionEvaluationORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.rule_id == rule_id)
            .order_by(self.model_class.evaluated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_rule_in_period(
        self,
        rule_id: str,
        period_start: datetime,
        period_end: datetime,
    ) -> Sequence[DecisionEvaluationORM]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.rule_id == rule_id,
                self.model_class.evaluated_at >= period_start,
                self.model_class.evaluated_at < period_end,
            )
            .order_by(self.model_class.evaluated_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_verdict(
        self, verdict: str, limit: int = 100
    ) -> Sequence[DecisionEvaluationORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.analyst_verdict == verdict)
            .order_by(self.model_class.evaluated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class AnalystFeedbackRepo(BaseRepository[AnalystFeedbackORM]):
    model_class = AnalystFeedbackORM
    pk_field = "feedback_id"

    async def get_by_evaluation(self, evaluation_id: str) -> Sequence[AnalystFeedbackORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.evaluation_id == evaluation_id)
            .order_by(self.model_class.submitted_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_analyst(
        self, analyst_id: str, limit: int = 100
    ) -> Sequence[AnalystFeedbackORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.analyst_id == analyst_id)
            .order_by(self.model_class.submitted_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def count_by_failure_mode(
        self,
        rule_id: Optional[str] = None,
        period_start: Optional[datetime] = None,
        period_end: Optional[datetime] = None,
    ) -> dict:
        """Count feedback records grouped by failure_mode.

        Returns dict: {failure_mode: count}.
        """
        from sqlalchemy import func
        stmt = (
            select(
                self.model_class.failure_mode,
                func.count(self.model_class.feedback_id),
            )
            .where(self.model_class.failure_mode.isnot(None))
            .group_by(self.model_class.failure_mode)
        )
        if rule_id:
            # Join through evaluation to get rule_id
            stmt = stmt.where(self.model_class.decision_log_id.isnot(None))
        if period_start:
            stmt = stmt.where(self.model_class.submitted_at >= period_start)
        if period_end:
            stmt = stmt.where(self.model_class.submitted_at < period_end)
        result = await self.session.execute(stmt)
        return dict(result.all())


class ReplayRunRepo(BaseRepository[ReplayRunORM]):
    model_class = ReplayRunORM
    pk_field = "replay_run_id"

    async def get_by_status(self, status: str) -> Sequence[ReplayRunORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.status == status)
            .order_by(self.model_class.initiated_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_original_decision(
        self, decision_log_id: str
    ) -> Sequence[ReplayRunORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.original_decision_log_id == decision_log_id)
            .order_by(self.model_class.initiated_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ReplayRunResultRepo(BaseRepository[ReplayRunResultORM]):
    model_class = ReplayRunResultORM
    pk_field = "replay_result_id"

    async def get_by_run(self, replay_run_id: str) -> Sequence[ReplayRunResultORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.replay_run_id == replay_run_id)
            .order_by(self.model_class.rule_id)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_triggered_by_run(self, replay_run_id: str) -> Sequence[ReplayRunResultORM]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.replay_run_id == replay_run_id,
                self.model_class.triggered.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class RulePerformanceRepo(BaseRepository[RulePerformanceORM]):
    model_class = RulePerformanceORM
    pk_field = "snapshot_id"

    async def get_latest_for_rule(self, rule_id: str) -> Optional[RulePerformanceORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.rule_id == rule_id)
            .order_by(self.model_class.period_end.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_history(
        self, rule_id: str, limit: int = 12
    ) -> Sequence[RulePerformanceORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.rule_id == rule_id)
            .order_by(self.model_class.period_end.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
