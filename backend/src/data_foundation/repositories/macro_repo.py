"""Macro Indicators repository — domain-specific queries."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select

from src.data_foundation.models.tables import MacroIndicatorORM
from src.data_foundation.repositories.base import BaseRepository


class MacroRepository(BaseRepository[MacroIndicatorORM]):
    model_class = MacroIndicatorORM
    pk_field = "indicator_id"

    async def find_by_country(
        self,
        country: str,
        *,
        indicator_code: Optional[str] = None,
        limit: int = 100,
    ) -> Sequence[MacroIndicatorORM]:
        stmt = select(self.model_class).where(self.model_class.country == country)
        if indicator_code:
            stmt = stmt.where(self.model_class.indicator_code == indicator_code)
        stmt = stmt.order_by(self.model_class.period_start.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def find_latest_by_country(
        self,
        country: str,
    ) -> Sequence[MacroIndicatorORM]:
        """Get the latest observation for each indicator code in a country."""
        # Simple approach: get all, latest first; consumer deduplicates by code
        stmt = (
            select(self.model_class)
            .where(self.model_class.country == country)
            .order_by(self.model_class.period_start.desc())
        )
        result = await self.session.execute(stmt)
        rows = result.scalars().all()
        # Deduplicate: keep first (latest) per indicator_code
        seen = set()
        unique = []
        for r in rows:
            if r.indicator_code not in seen:
                seen.add(r.indicator_code)
                unique.append(r)
        return unique
