"""Bootstrap seed data into Postgres.

Usage:
    python -m src.data_foundation.cli.seed_db            # seed all datasets
    python -m src.data_foundation.cli.seed_db --only entity_registry,decision_rules
    python -m src.data_foundation.cli.seed_db --clear     # truncate then seed

Loads JSON seed files from src/data_foundation/seed/ and converts to ORM rows
via the converter layer, then upserts into Postgres.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any, Callable, Dict, List, Type

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres import async_session_factory, Base, engine
from src.data_foundation.metadata.loader import load_seed_json

# ORM models
from src.data_foundation.models.tables import (
    EntityRegistryORM,
    EventSignalORM,
    MacroIndicatorORM,
    InterestRateSignalORM,
    OilEnergySignalORM,
    FXSignalORM,
    CBKIndicatorORM,
    BankingProfileORM,
    InsuranceProfileORM,
    LogisticsNodeORM,
    DecisionRuleORM,
    DecisionLogORM,
)

# Pydantic schemas
from src.data_foundation.schemas.entity_registry import EntityRegistryEntry
from src.data_foundation.schemas.event_signals import EventSignal
from src.data_foundation.schemas.macro_indicators import MacroIndicatorRecord
from src.data_foundation.schemas.interest_rate_signals import InterestRateSignal
from src.data_foundation.schemas.oil_energy_signals import OilEnergySignal
from src.data_foundation.schemas.fx_signals import FXSignal
from src.data_foundation.schemas.cbk_indicators import CBKIndicatorRecord
from src.data_foundation.schemas.banking_sector_profiles import BankingSectorProfile
from src.data_foundation.schemas.insurance_sector_profiles import InsuranceSectorProfile
from src.data_foundation.schemas.logistics_nodes import LogisticsNode
from src.data_foundation.schemas.decision_rules import DecisionRule
from src.data_foundation.schemas.decision_logs import DecisionLogEntry

# Converters
from src.data_foundation.models.converters import (
    entity_to_orm,
    event_to_orm,
    macro_to_orm,
    rule_to_orm,
    dlog_to_orm,
)


def _enum_val(v: Any) -> Any:
    return v.value if hasattr(v, "value") else v


def _geo_flat(obj: Any) -> Dict[str, Any]:
    geo = getattr(obj, "geo", None)
    if geo:
        return {"geo_lat": geo.latitude, "geo_lng": geo.longitude}
    return {"geo_lat": None, "geo_lng": None}


def _generic_to_orm(obj: Any, orm_class: type, field_map: Dict[str, Callable] | None = None) -> Any:
    """Generic Pydantic → ORM converter for simple datasets."""
    data = {}
    for col_name in orm_class.__table__.columns.keys():
        val = getattr(obj, col_name, None)
        if val is not None:
            data[col_name] = _enum_val(val)
        elif col_name in ("geo_lat", "geo_lng"):
            data.update(_geo_flat(obj))
        elif col_name == "metadata_json":
            data[col_name] = getattr(obj, "metadata", None)
        else:
            data[col_name] = val
    if field_map:
        for k, fn in field_map.items():
            data[k] = fn(obj)
    return orm_class(**data)


# Dataset → (seed_name, pydantic_class, orm_class, converter_fn)
SEED_REGISTRY: Dict[str, tuple] = {
    "entity_registry": (
        "entity_registry", EntityRegistryEntry, EntityRegistryORM, entity_to_orm
    ),
    "event_signals": (
        "event_signals", EventSignal, EventSignalORM, event_to_orm
    ),
    "macro_indicators": (
        "macro_indicators", MacroIndicatorRecord, MacroIndicatorORM, macro_to_orm
    ),
    "interest_rate_signals": (
        "interest_rate_signals", InterestRateSignal, InterestRateSignalORM,
        lambda obj: _generic_to_orm(obj, InterestRateSignalORM)
    ),
    "oil_energy_signals": (
        "oil_energy_signals", OilEnergySignal, OilEnergySignalORM,
        lambda obj: _generic_to_orm(obj, OilEnergySignalORM)
    ),
    "fx_signals": (
        "fx_signals", FXSignal, FXSignalORM,
        lambda obj: _generic_to_orm(obj, FXSignalORM)
    ),
    "cbk_indicators": (
        "cbk_indicators", CBKIndicatorRecord, CBKIndicatorORM,
        lambda obj: _generic_to_orm(obj, CBKIndicatorORM)
    ),
    "banking_profiles": (
        "banking_profiles", BankingSectorProfile, BankingProfileORM,
        lambda obj: _generic_to_orm(obj, BankingProfileORM)
    ),
    "insurance_profiles": (
        "insurance_profiles", InsuranceSectorProfile, InsuranceProfileORM,
        lambda obj: _generic_to_orm(obj, InsuranceProfileORM)
    ),
    "logistics_nodes": (
        "logistics_nodes", LogisticsNode, LogisticsNodeORM,
        lambda obj: _generic_to_orm(obj, LogisticsNodeORM)
    ),
    "decision_rules": (
        "decision_rules", DecisionRule, DecisionRuleORM, rule_to_orm
    ),
    "decision_logs": (
        "decision_logs", DecisionLogEntry, DecisionLogORM, dlog_to_orm
    ),
}


async def seed_dataset(
    session: AsyncSession,
    dataset_name: str,
    clear: bool = False,
) -> int:
    """Seed a single dataset. Returns row count."""
    if dataset_name not in SEED_REGISTRY:
        print(f"  ⚠️  Unknown dataset: {dataset_name}")
        return 0

    seed_name, pydantic_cls, orm_cls, converter_fn = SEED_REGISTRY[dataset_name]

    if clear:
        await session.execute(orm_cls.__table__.delete())
        await session.flush()

    raw_records = load_seed_json(seed_name)
    count = 0
    for raw in raw_records:
        pydantic_obj = pydantic_cls.model_validate(raw)
        orm_obj = converter_fn(pydantic_obj)
        await session.merge(orm_obj)
        count += 1

    await session.flush()
    return count


async def run_seed(
    datasets: List[str] | None = None,
    clear: bool = False,
) -> Dict[str, int]:
    """Seed all (or selected) datasets into Postgres."""
    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    targets = datasets if datasets else list(SEED_REGISTRY.keys())
    results = {}

    async with async_session_factory() as session:
        for ds in targets:
            try:
                count = await seed_dataset(session, ds, clear=clear)
                results[ds] = count
                print(f"  ✅ {ds}: {count} records")
            except Exception as e:
                print(f"  ❌ {ds}: {e}")
                results[ds] = 0

        await session.commit()

    return results


def main():
    parser = argparse.ArgumentParser(description="Seed P1 data foundation into Postgres")
    parser.add_argument(
        "--only",
        type=str,
        default=None,
        help="Comma-separated list of datasets to seed (default: all)",
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Truncate tables before seeding",
    )
    args = parser.parse_args()

    datasets = args.only.split(",") if args.only else None
    print("🌱 Seeding P1 Data Foundation into Postgres...")
    results = asyncio.run(run_seed(datasets=datasets, clear=args.clear))
    total = sum(results.values())
    print(f"\n✅ Seed complete: {total} records across {len(results)} datasets")


if __name__ == "__main__":
    main()
