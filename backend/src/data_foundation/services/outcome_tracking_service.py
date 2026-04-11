"""Outcome Tracking Service — create and link expected/actual outcomes.

Handles:
  - Creating expected outcomes from decision log context
  - Recording actual observed outcomes
  - Linking expected ↔ actual for downstream evaluation
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.models.outcome_tables import (
    DecisionActualOutcomeORM,
    DecisionExpectedOutcomeORM,
)
from src.data_foundation.repositories.actual_outcome_repo import ActualOutcomeRepository
from src.data_foundation.repositories.expected_outcome_repo import ExpectedOutcomeRepository
from src.data_foundation.schemas.outcome_schemas import (
    CreateActualOutcomeRequest,
    CreateExpectedOutcomeRequest,
    DecisionActualOutcome,
    DecisionExpectedOutcome,
)


def _uuid() -> str:
    return str(uuid4())


class OutcomeTrackingService:
    """Manages the lifecycle of expected and actual outcome records."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.expected_repo = ExpectedOutcomeRepository(session)
        self.actual_repo = ActualOutcomeRepository(session)

    async def create_expected_outcome(
        self,
        request: CreateExpectedOutcomeRequest,
    ) -> DecisionExpectedOutcome:
        """Persist a new expected outcome record."""
        outcome_id = f"EO-{_uuid()[:12]}"
        orm = DecisionExpectedOutcomeORM(
            expected_outcome_id=outcome_id,
            decision_log_id=request.decision_log_id,
            event_id=request.event_id,
            rule_id=request.rule_id,
            expected_entities=request.expected_entities,
            expected_severity=request.expected_severity,
            expected_direction=request.expected_direction,
            expected_time_horizon_hours=request.expected_time_horizon_hours,
            expected_mitigation_effect=request.expected_mitigation_effect,
            expected_notes=request.expected_notes,
            confidence_at_decision_time=request.confidence_at_decision_time,
        )
        created = await self.expected_repo.create(orm)
        return DecisionExpectedOutcome.model_validate(created)

    async def create_actual_outcome(
        self,
        request: CreateActualOutcomeRequest,
    ) -> DecisionActualOutcome:
        """Persist a new actual outcome record."""
        outcome_id = f"AO-{_uuid()[:12]}"
        orm = DecisionActualOutcomeORM(
            actual_outcome_id=outcome_id,
            expected_outcome_id=request.expected_outcome_id,
            event_id=request.event_id,
            observed_entities=request.observed_entities,
            observed_severity=request.observed_severity,
            observed_direction=request.observed_direction,
            observed_time_to_materialization_hours=request.observed_time_to_materialization_hours,
            actual_effect_value=request.actual_effect_value,
            observation_source=request.observation_source,
            observation_notes=request.observation_notes,
            observed_at=request.observed_at,
        )
        created = await self.actual_repo.create(orm)
        return DecisionActualOutcome.model_validate(created)

    async def get_expected_outcome(self, expected_outcome_id: str) -> DecisionExpectedOutcome | None:
        orm = await self.expected_repo.get_by_pk(expected_outcome_id)
        if orm is None:
            return None
        return DecisionExpectedOutcome.model_validate(orm)

    async def get_actual_outcome(self, actual_outcome_id: str) -> DecisionActualOutcome | None:
        orm = await self.actual_repo.get_by_pk(actual_outcome_id)
        if orm is None:
            return None
        return DecisionActualOutcome.model_validate(orm)

    async def get_actual_for_expected(self, expected_outcome_id: str) -> DecisionActualOutcome | None:
        orm = await self.actual_repo.find_by_expected_outcome(expected_outcome_id)
        if orm is None:
            return None
        return DecisionActualOutcome.model_validate(orm)
