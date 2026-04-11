"""Decision Evaluation repository — domain-specific queries."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.outcome_tables import DecisionEvaluationORM
from src.data_foundation.repositories.base import BaseRepository


class EvaluationRepository(BaseRepository[DecisionEvaluationORM]):
    model_class = DecisionEvaluationORM
    pk_field = "evaluation_id"

    async def find_by_decision_log(self, decision_log_id: str) -> Sequence[DecisionEvaluationORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_log_id == decision_log_id)
            .order_by(self.model_class.evaluated_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_status(self, status: str, *, limit: int = 100) -> Sequence[DecisionEvaluationORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.evaluation_status == status)
            .order_by(self.model_class.evaluated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_rule(self, rule_id: str, *, limit: int = 100) -> Sequence[DecisionEvaluationORM]:
        """Find evaluations linked to a specific rule via expected outcomes."""
        # Join through expected_outcome to get rule_id
        from src.data_foundation.models.outcome_tables import DecisionExpectedOutcomeORM
        stmt = (
            select(self.model_class)
            .join(
                DecisionExpectedOutcomeORM,
                self.model_class.expected_outcome_id == DecisionExpectedOutcomeORM.expected_outcome_id,
            )
            .where(DecisionExpectedOutcomeORM.rule_id == rule_id)
            .order_by(self.model_class.evaluated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_expected_and_actual(
        self,
        expected_outcome_id: str,
        actual_outcome_id: str,
    ) -> Optional[DecisionEvaluationORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.expected_outcome_id == expected_outcome_id)
            .where(self.model_class.actual_outcome_id == actual_outcome_id)
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
