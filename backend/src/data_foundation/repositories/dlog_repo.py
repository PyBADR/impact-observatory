"""Decision Logs repository — domain-specific queries."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.tables import DecisionLogORM
from src.data_foundation.repositories.base import BaseRepository


class DecisionLogRepository(BaseRepository[DecisionLogORM]):
    model_class = DecisionLogORM
    pk_field = "log_id"

    async def find_by_rule(
        self,
        rule_id: str,
        *,
        limit: int = 50,
    ) -> Sequence[DecisionLogORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.rule_id == rule_id)
            .order_by(self.model_class.triggered_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_by_status(
        self,
        status: str,
        *,
        limit: int = 100,
    ) -> Sequence[DecisionLogORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.status == status)
            .order_by(self.model_class.triggered_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_pending_approval(self) -> Sequence[DecisionLogORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.status == "PROPOSED")
            .where(self.model_class.requires_approval == True)  # noqa: E712
            .order_by(self.model_class.triggered_at.desc())
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_hash(self) -> Optional[str]:
        """Get the audit_hash of the most recent log entry for chain linking."""
        stmt = (
            select(self.model_class.audit_hash)
            .order_by(self.model_class.triggered_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
