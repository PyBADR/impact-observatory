"""Rule Performance Snapshot repository — domain-specific queries."""

from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.outcome_tables import RulePerformanceSnapshotORM
from src.data_foundation.repositories.base import BaseRepository


class RulePerformanceRepository(BaseRepository[RulePerformanceSnapshotORM]):
    model_class = RulePerformanceSnapshotORM
    pk_field = "snapshot_id"

    async def find_by_rule(
        self,
        rule_id: str,
        *,
        limit: int = 50,
    ) -> Sequence[RulePerformanceSnapshotORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.rule_id == rule_id)
            .order_by(self.model_class.snapshot_date.desc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_latest_for_rule(self, rule_id: str) -> Optional[RulePerformanceSnapshotORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.rule_id == rule_id)
            .order_by(self.model_class.snapshot_date.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def find_by_date_range(
        self,
        start: datetime,
        end: datetime,
        *,
        rule_id: Optional[str] = None,
    ) -> Sequence[RulePerformanceSnapshotORM]:
        stmt = (
            select(self.model_class)
            .where(self.model_class.snapshot_date >= start)
            .where(self.model_class.snapshot_date <= end)
        )
        if rule_id:
            stmt = stmt.where(self.model_class.rule_id == rule_id)
        stmt = stmt.order_by(self.model_class.snapshot_date.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()
