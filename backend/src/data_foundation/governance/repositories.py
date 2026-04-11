"""Governance & Calibration — Typed async repositories.

Seven repositories extending BaseRepository with domain-specific queries.
"""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.governance.orm_models import (
    CalibrationEventORM,
    CalibrationTriggerORM,
    GovernanceAuditEntryORM,
    GovernancePolicyORM,
    RuleLifecycleEventORM,
    TruthValidationPolicyORM,
    TruthValidationResultORM,
)
from src.data_foundation.repositories.base import BaseRepository


class GovernancePolicyRepository(BaseRepository[GovernancePolicyORM]):
    model_class = GovernancePolicyORM
    pk_field = "policy_id"

    async def find_active_by_type(self, policy_type: str) -> Sequence[GovernancePolicyORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.policy_type == policy_type)
            .where(self.model_class.is_active == True)  # noqa: E712
            .order_by(self.model_class.effective_date.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_active(self) -> Sequence[GovernancePolicyORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_active == True)  # noqa: E712
            .order_by(self.model_class.policy_type, self.model_class.effective_date.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class RuleLifecycleEventRepository(BaseRepository[RuleLifecycleEventORM]):
    model_class = RuleLifecycleEventORM
    pk_field = "event_id"

    async def find_by_spec(
        self, spec_id: str, *, limit: int = 100,
    ) -> Sequence[RuleLifecycleEventORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.spec_id == spec_id)
            .order_by(self.model_class.occurred_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_for_spec(self, spec_id: str) -> Optional[RuleLifecycleEventORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.spec_id == spec_id)
            .order_by(self.model_class.occurred_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


class TruthValidationPolicyRepository(BaseRepository[TruthValidationPolicyORM]):
    model_class = TruthValidationPolicyORM
    pk_field = "policy_id"

    async def find_active_for_dataset(self, target_dataset: str) -> Sequence[TruthValidationPolicyORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.target_dataset == target_dataset)
            .where(self.model_class.is_active == True)  # noqa: E712
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class TruthValidationResultRepository(BaseRepository[TruthValidationResultORM]):
    model_class = TruthValidationResultORM
    pk_field = "result_id"

    async def find_by_policy(
        self, policy_id: str, *, limit: int = 100,
    ) -> Sequence[TruthValidationResultORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.policy_id == policy_id)
            .order_by(self.model_class.validated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_record(self, record_id: str) -> Sequence[TruthValidationResultORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.record_id == record_id)
            .order_by(self.model_class.validated_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class CalibrationTriggerRepository(BaseRepository[CalibrationTriggerORM]):
    model_class = CalibrationTriggerORM
    pk_field = "trigger_id"

    async def find_active(self) -> Sequence[CalibrationTriggerORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_active == True)  # noqa: E712
            .order_by(self.model_class.trigger_type)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_type(self, trigger_type: str) -> Sequence[CalibrationTriggerORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.trigger_type == trigger_type)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class CalibrationEventRepository(BaseRepository[CalibrationEventORM]):
    model_class = CalibrationEventORM
    pk_field = "event_id"

    async def find_by_rule(
        self, rule_id: str, *, limit: int = 50,
    ) -> Sequence[CalibrationEventORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.rule_id == rule_id)
            .order_by(self.model_class.triggered_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_unresolved(self) -> Sequence[CalibrationEventORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.status.in_(["TRIGGERED", "ACKNOWLEDGED"]))
            .order_by(self.model_class.triggered_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class GovernanceAuditEntryRepository(BaseRepository[GovernanceAuditEntryORM]):
    model_class = GovernanceAuditEntryORM
    pk_field = "entry_id"

    async def find_by_subject(
        self, subject_type: str, subject_id: str, *, limit: int = 100,
    ) -> Sequence[GovernanceAuditEntryORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.subject_type == subject_type)
            .where(self.model_class.subject_id == subject_id)
            .order_by(self.model_class.occurred_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_chain(self, *, limit: int = 100) -> Sequence[GovernanceAuditEntryORM]:
        """Get the most recent audit chain entries."""
        stmt = (
            select(self.model_class)
            .order_by(self.model_class.occurred_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest(self) -> Optional[GovernanceAuditEntryORM]:
        stmt = (
            select(self.model_class)
            .order_by(self.model_class.occurred_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
