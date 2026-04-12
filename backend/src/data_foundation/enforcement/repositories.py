"""
Enforcement Layer — Typed Async Repositories
==============================================

4 repositories extending BaseRepository for each enforcement ORM model.
Each adds domain-specific query methods beyond basic CRUD.
"""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.repositories.base import BaseRepository

from .orm_models import (
    EnforcementPolicyORM,
    EnforcementDecisionORM,
    ExecutionGateResultORM,
    ApprovalRequestORM,
)


class EnforcementPolicyRepo(BaseRepository[EnforcementPolicyORM]):
    model_class = EnforcementPolicyORM
    pk_field = "policy_id"

    async def get_active_ordered(self) -> Sequence[EnforcementPolicyORM]:
        """Get all active policies ordered by priority (lowest first = highest priority)."""
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_active.is_(True))
            .order_by(self.model_class.priority.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_action(
        self, enforcement_action: str
    ) -> Sequence[EnforcementPolicyORM]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.enforcement_action == enforcement_action,
                self.model_class.is_active.is_(True),
            )
            .order_by(self.model_class.priority.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class EnforcementDecisionRepo(BaseRepository[EnforcementDecisionORM]):
    model_class = EnforcementDecisionORM
    pk_field = "decision_id"

    async def get_by_decision_log(
        self, decision_log_id: str
    ) -> Sequence[EnforcementDecisionORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_log_id == decision_log_id)
            .order_by(self.model_class.evaluated_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_for_decision_log(
        self, decision_log_id: str
    ) -> Optional[EnforcementDecisionORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_log_id == decision_log_id)
            .order_by(self.model_class.evaluated_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_action(
        self, enforcement_action: str, limit: int = 100
    ) -> Sequence[EnforcementDecisionORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.enforcement_action == enforcement_action)
            .order_by(self.model_class.evaluated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_blocked(self, limit: int = 100) -> Sequence[EnforcementDecisionORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.is_executable.is_(False))
            .order_by(self.model_class.evaluated_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ExecutionGateResultRepo(BaseRepository[ExecutionGateResultORM]):
    model_class = ExecutionGateResultORM
    pk_field = "gate_id"

    async def get_by_decision_log(
        self, decision_log_id: str
    ) -> Optional[ExecutionGateResultORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_log_id == decision_log_id)
            .order_by(self.model_class.resolved_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_outcome(
        self, gate_outcome: str, limit: int = 100
    ) -> Sequence[ExecutionGateResultORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.gate_outcome == gate_outcome)
            .order_by(self.model_class.resolved_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()


class ApprovalRequestRepo(BaseRepository[ApprovalRequestORM]):
    model_class = ApprovalRequestORM
    pk_field = "request_id"

    async def get_pending(self) -> Sequence[ApprovalRequestORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.status == "PENDING")
            .order_by(self.model_class.requested_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_decision_log(
        self, decision_log_id: str
    ) -> Sequence[ApprovalRequestORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.decision_log_id == decision_log_id)
            .order_by(self.model_class.requested_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_by_role(
        self, required_approver_role: str, status: str = "PENDING"
    ) -> Sequence[ApprovalRequestORM]:
        stmt = (
            select(self.model_class)
            .where(
                self.model_class.required_approver_role == required_approver_role,
                self.model_class.status == status,
            )
            .order_by(self.model_class.requested_at.asc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()
