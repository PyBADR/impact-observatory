"""
Governance Layer — Typed Async Repositories
=============================================

7 repositories extending BaseRepository for each governance ORM model.
Each adds domain-specific query methods beyond basic CRUD.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.repositories.base import BaseRepository

from .orm_models import (
    GovernancePolicyORM,
    RuleLifecycleEventORM,
    TruthValidationPolicyORM,
    TruthValidationResultORM,
    CalibrationTriggerORM,
    CalibrationEventORM,
    GovernanceAuditEntryORM,
)


class GovernancePolicyRepo(BaseRepository[GovernancePolicyORM]):
    model_class = GovernancePolicyORM
    pk_field = "policy_id"

    async def get_active_by_type(self, policy_type: str) -> Sequence[GovernancePolicyORM]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.policy_type == policy_type,
                self.model_class.is_active.is_(True),
            )
            .order_by(self.model_class.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_applicable(
        self,
        policy_type: str,
        risk_level: Optional[str] = None,
        action: Optional[str] = None,
        country: Optional[str] = None,
    ) -> Sequence[GovernancePolicyORM]:
        """Get active policies that could apply to the given context.

        Scope arrays are permissive: empty scope means "applies to all".
        Filtering by JSON containment is deferred to the engine layer
        because JSONB array-contains varies by DB. This returns all
        active policies of the given type for further in-memory filtering.
        """
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.policy_type == policy_type,
                self.model_class.is_active.is_(True),
            )
            .order_by(self.model_class.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class RuleLifecycleEventRepo(BaseRepository[RuleLifecycleEventORM]):
    model_class = RuleLifecycleEventORM
    pk_field = "event_id"

    async def get_by_spec(
        self, spec_id: str, limit: int = 100
    ) -> Sequence[RuleLifecycleEventORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.spec_id == spec_id)
            .order_by(self.model_class.occurred_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_for_spec(
        self, spec_id: str
    ) -> Optional[RuleLifecycleEventORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.spec_id == spec_id)
            .order_by(self.model_class.occurred_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_transition_type(
        self, transition_type: str, limit: int = 100
    ) -> Sequence[RuleLifecycleEventORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.transition_type == transition_type)
            .order_by(self.model_class.occurred_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class TruthValidationPolicyRepo(BaseRepository[TruthValidationPolicyORM]):
    model_class = TruthValidationPolicyORM
    pk_field = "policy_id"

    async def get_active_for_dataset(
        self, target_dataset: str
    ) -> Optional[TruthValidationPolicyORM]:
        """Get the active truth policy for a dataset. Returns latest if multiple."""
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.target_dataset == target_dataset,
                self.model_class.is_active.is_(True),
            )
            .order_by(self.model_class.created_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_active(self) -> Sequence[TruthValidationPolicyORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_active.is_(True))
            .order_by(self.model_class.target_dataset)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class TruthValidationResultRepo(BaseRepository[TruthValidationResultORM]):
    model_class = TruthValidationResultORM
    pk_field = "result_id"

    async def get_by_policy(
        self, policy_id: str, limit: int = 100
    ) -> Sequence[TruthValidationResultORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.policy_id == policy_id)
            .order_by(self.model_class.validated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_record(
        self, target_dataset: str, record_id: str
    ) -> Sequence[TruthValidationResultORM]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.target_dataset == target_dataset,
                self.model_class.record_id == record_id,
            )
            .order_by(self.model_class.validated_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_failures(
        self, policy_id: str, limit: int = 100
    ) -> Sequence[TruthValidationResultORM]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.policy_id == policy_id,
                self.model_class.is_valid.is_(False),
            )
            .order_by(self.model_class.validated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class CalibrationTriggerRepo(BaseRepository[CalibrationTriggerORM]):
    model_class = CalibrationTriggerORM
    pk_field = "trigger_id"

    async def get_active(self) -> Sequence[CalibrationTriggerORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_active.is_(True))
            .order_by(self.model_class.trigger_type)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_type(
        self, trigger_type: str
    ) -> Sequence[CalibrationTriggerORM]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.trigger_type == trigger_type,
                self.model_class.is_active.is_(True),
            )
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class CalibrationEventRepo(BaseRepository[CalibrationEventORM]):
    model_class = CalibrationEventORM
    pk_field = "event_id"

    async def get_by_rule(
        self, rule_id: str, limit: int = 50
    ) -> Sequence[CalibrationEventORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.rule_id == rule_id)
            .order_by(self.model_class.triggered_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_unresolved(self) -> Sequence[CalibrationEventORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.status == "TRIGGERED")
            .order_by(self.model_class.triggered_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_trigger_and_rule(
        self, trigger_id: str, rule_id: str
    ) -> Sequence[CalibrationEventORM]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.trigger_id == trigger_id,
                self.model_class.rule_id == rule_id,
            )
            .order_by(self.model_class.triggered_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class GovernanceAuditEntryRepo(BaseRepository[GovernanceAuditEntryORM]):
    model_class = GovernanceAuditEntryORM
    pk_field = "entry_id"

    async def get_by_subject(
        self, subject_type: str, subject_id: str, limit: int = 100
    ) -> Sequence[GovernanceAuditEntryORM]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.subject_type == subject_type,
                self.model_class.subject_id == subject_id,
            )
            .order_by(self.model_class.occurred_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_actor(
        self, actor: str, limit: int = 100
    ) -> Sequence[GovernanceAuditEntryORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.actor == actor)
            .order_by(self.model_class.occurred_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_event_type(
        self, event_type: str, limit: int = 100
    ) -> Sequence[GovernanceAuditEntryORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.event_type == event_type)
            .order_by(self.model_class.occurred_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest(self) -> Optional[GovernanceAuditEntryORM]:
        """Get the most recent audit entry (for hash chaining)."""
        stmt = (
            select(self.model_class)
            .order_by(self.model_class.occurred_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_chain(
        self, start_entry_id: str, limit: int = 100
    ) -> Sequence[GovernanceAuditEntryORM]:
        """Get the audit chain starting from a specific entry, ordered chronologically."""
        start = await self.get_by_pk(start_entry_id)
        if start is None:
            return []
        stmt = (
            select(self.model_class)
            .where(self.model_class.occurred_at >= start.occurred_at)
            .order_by(self.model_class.occurred_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
