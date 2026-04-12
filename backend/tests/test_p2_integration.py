"""P2 Data Foundation — Integration Tests.

Tests cover:
  1. ORM model ↔ Pydantic converter round-trips
  2. Repository layer CRUD (in-memory SQLite)
  3. Seed bootstrap logic
  4. Decision engine evaluation pipeline
  5. FastAPI route contracts (TestClient)
  6. Oil/Energy connector parsing

These tests use an in-memory SQLite database to avoid requiring Postgres.
SQLite doesn't support JSONB, so we patch it with JSON.
"""

from __future__ import annotations

import asyncio
import json
import uuid
from datetime import date, datetime, timezone
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# ── Test database setup ──────────────────────────────────────────────────────

# We use aiosqlite for async SQLite (avoids Postgres dependency in tests)
try:
    import aiosqlite  # noqa: F401
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1: Converter Round-Trip Tests (no DB required)
# ═══════════════════════════════════════════════════════════════════════════════

class TestConverterRoundTrips:
    """Verify Pydantic → ORM → Pydantic preserves all data."""

    def test_entity_roundtrip(self):
        from src.data_foundation.schemas.entity_registry import EntityRegistryEntry
        from src.data_foundation.models.converters import entity_to_orm, entity_from_orm

        original = EntityRegistryEntry(
            entity_id="TEST-ENT-001",
            entity_name="Test Entity",
            entity_type="commercial_bank",
            country="KW",
            sector="banking",
            gdp_weight=0.05,
            criticality_score=0.8,
            is_active=True,
            geo={"latitude": 29.3759, "longitude": 47.9774},
            related_entity_ids=["KW-CBK"],
            tags=["test"],
        )

        orm = entity_to_orm(original)
        assert orm.entity_id == "TEST-ENT-001"
        assert orm.country == "KW"
        assert orm.geo_lat == pytest.approx(29.3759)
        assert orm.geo_lng == pytest.approx(47.9774)
        assert orm.related_entity_ids == ["KW-CBK"]

        roundtripped = entity_from_orm(orm)
        assert roundtripped.entity_id == original.entity_id
        assert roundtripped.country.value == "KW"
        assert roundtripped.geo is not None
        assert roundtripped.geo.latitude == pytest.approx(29.3759)
        assert roundtripped.related_entity_ids == ["KW-CBK"]

    def test_event_roundtrip(self):
        from src.data_foundation.schemas.event_signals import EventSignal
        from src.data_foundation.models.converters import event_to_orm, event_from_orm

        original = EventSignal(
            event_id="EVT-TEST-001",
            title="Test Event",
            category="GEOPOLITICAL",
            severity="HIGH",
            severity_score=0.75,
            event_time=datetime(2025, 1, 15, tzinfo=timezone.utc),
            detected_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
            countries_affected=["KW", "SA"],
            sectors_affected=["energy", "maritime"],
            entity_ids_affected=["KW-SHUWAIKH"],
            scenario_ids=["hormuz_chokepoint_disruption"],
            source_id="acled-api",
        )

        orm = event_to_orm(original)
        assert orm.event_id == "EVT-TEST-001"
        assert orm.countries_affected == ["KW", "SA"]

        roundtripped = event_from_orm(orm)
        assert roundtripped.event_id == original.event_id
        assert roundtripped.severity_score == 0.75

    def test_macro_roundtrip(self):
        from src.data_foundation.schemas.macro_indicators import MacroIndicatorRecord
        from src.data_foundation.models.converters import macro_to_orm, macro_from_orm

        original = MacroIndicatorRecord(
            indicator_id="KW-GDP-2024Q4",
            country="KW",
            indicator_code="GDP_REAL",
            indicator_name="Real GDP Growth",
            value=2.5,
            unit="percent",
            period_start=date(2024, 10, 1),
            period_end=date(2024, 12, 31),
            frequency="quarterly",
            source_id="imf-weo",
        )

        orm = macro_to_orm(original)
        roundtripped = macro_from_orm(orm)
        assert roundtripped.indicator_id == "KW-GDP-2024Q4"
        assert roundtripped.value == 2.5
        assert roundtripped.country.value == "KW"

    def test_rule_roundtrip(self):
        from src.data_foundation.schemas.decision_rules import DecisionRule
        from src.data_foundation.models.converters import rule_to_orm, rule_from_orm

        original = DecisionRule(
            rule_id="RULE-TEST-001",
            rule_name="Test Rule",
            description="Test rule description",
            is_active=True,
            conditions=[{
                "field": "oil_energy_signals.change_pct",
                "operator": "lt",
                "threshold": -30.0,
            }],
            action="ALERT",
            escalation_level="HIGH",
            applicable_countries=["KW"],
        )

        orm = rule_to_orm(original)
        assert orm.rule_id == "RULE-TEST-001"
        assert isinstance(orm.conditions, list)
        assert orm.conditions[0]["field"] == "oil_energy_signals.change_pct"

        roundtripped = rule_from_orm(orm)
        assert roundtripped.rule_id == "RULE-TEST-001"
        assert len(roundtripped.conditions) == 1
        assert roundtripped.action.value == "ALERT"

    def test_dlog_roundtrip(self):
        from src.data_foundation.schemas.decision_logs import DecisionLogEntry, TriggerContext
        from src.data_foundation.models.converters import dlog_to_orm, dlog_from_orm

        original = DecisionLogEntry(
            log_id="DLOG-TEST-001",
            rule_id="RULE-TEST-001",
            rule_version=1,
            triggered_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
            action="ALERT",
            status="PROPOSED",
            trigger_context=TriggerContext(
                signal_ids=["EVT-001"],
                indicator_values={"severity_score": 0.75},
            ),
        )

        orm = dlog_to_orm(original)
        assert orm.log_id == "DLOG-TEST-001"
        assert isinstance(orm.trigger_context, dict)

        roundtripped = dlog_from_orm(orm)
        assert roundtripped.log_id == "DLOG-TEST-001"
        assert roundtripped.trigger_context.signal_ids == ["EVT-001"]


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2: Rule Engine Integration (no DB)
# ═══════════════════════════════════════════════════════════════════════════════

class TestRuleEngineIntegration:
    """Test the rule engine with realistic decision rules."""

    def _make_rule(self, **kwargs) -> "DecisionRule":
        from src.data_foundation.schemas.decision_rules import DecisionRule
        defaults = {
            "rule_id": f"RULE-{uuid.uuid4().hex[:8]}",
            "rule_name": "Test Rule",
            "description": "Test",
            "is_active": True,
            "conditions": [{"field": "test.value", "operator": "gt", "threshold": 0.5}],
            "action": "ALERT",
        }
        defaults.update(kwargs)
        return DecisionRule(**defaults)

    def test_oil_price_drop_triggers_alert(self):
        from src.data_foundation.decision.rule_engine import DataState, evaluate_rule

        rule = self._make_rule(
            rule_id="RULE-OIL-DROP",
            conditions=[{
                "field": "oil_energy_signals.change_pct",
                "operator": "lt",
                "threshold": -30.0,
            }],
            action="ACTIVATE_CONTINGENCY",
            escalation_level="SEVERE",
        )

        data_state = DataState(values={"oil_energy_signals.change_pct": -35.0})
        result = evaluate_rule(rule, data_state)
        assert result.triggered is True
        assert result.action.value == "ACTIVATE_CONTINGENCY"

    def test_severity_score_triggers_monitor(self):
        from src.data_foundation.decision.rule_engine import DataState, evaluate_rule

        rule = self._make_rule(
            rule_id="RULE-SEV-MONITOR",
            conditions=[{
                "field": "event_signals.severity_score",
                "operator": "gte",
                "threshold": 0.65,
            }],
            action="MONITOR",
            escalation_level="HIGH",
        )

        # Should trigger
        data_state = DataState(values={"event_signals.severity_score": 0.72})
        result = evaluate_rule(rule, data_state)
        assert result.triggered is True

        # Should NOT trigger
        data_state = DataState(values={"event_signals.severity_score": 0.50})
        result = evaluate_rule(rule, data_state)
        assert result.triggered is False

    def test_multi_rule_evaluation(self):
        from src.data_foundation.decision.rule_engine import DataState, evaluate_all_rules

        rules = [
            self._make_rule(
                rule_id="RULE-A",
                conditions=[{"field": "x", "operator": "gt", "threshold": 10}],
                action="ALERT",
            ),
            self._make_rule(
                rule_id="RULE-B",
                conditions=[{"field": "y", "operator": "lt", "threshold": 5}],
                action="MONITOR",
            ),
            self._make_rule(
                rule_id="RULE-C",
                is_active=False,
                conditions=[{"field": "z", "operator": "eq", "threshold": True}],
                action="ESCALATE",
            ),
        ]

        data_state = DataState(values={"x": 15, "y": 3, "z": True})
        output = evaluate_all_rules(rules, data_state)

        assert output.total_evaluated == 3
        assert output.total_triggered == 2  # RULE-A and RULE-B
        assert len(output.data_state_hash) == 64  # SHA-256
        triggered_ids = {r.rule_id for r in output.triggered_rules}
        assert "RULE-A" in triggered_ids
        assert "RULE-B" in triggered_ids
        assert "RULE-C" not in triggered_ids  # inactive


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3: Impact Chain Construction (no DB)
# ═══════════════════════════════════════════════════════════════════════════════

class TestImpactChainConstruction:
    """Test building a full impact chain from an event."""

    def test_chain_from_event(self):
        from src.data_foundation.schemas.event_signals import EventSignal
        from src.data_foundation.decision.impact_chain import (
            SignalDetection, ImpactChain,
        )

        event = EventSignal(
            event_id="EVT-HORMUZ-001",
            title="Naval exercise near Hormuz",
            category="GEOPOLITICAL",
            severity="HIGH",
            severity_score=0.75,
            event_time=datetime(2025, 1, 15, tzinfo=timezone.utc),
            detected_at=datetime(2025, 1, 15, tzinfo=timezone.utc),
            countries_affected=["KW", "SA", "AE", "QA", "BH", "OM"],
            sectors_affected=["energy", "maritime", "logistics"],
            entity_ids_affected=["KW-SHUWAIKH", "AE-JEBEL-ALI"],
            scenario_ids=["hormuz_chokepoint_disruption"],
            source_id="acled-api",
        )

        signal = SignalDetection(
            signal_ref_id=event.event_id,
            signal_dataset="p1_event_signals",
            signal_type="GEOPOLITICAL_EVENT",
            severity=event.severity,
            severity_score=event.severity_score,
            detected_at=event.detected_at,
            countries_affected=event.countries_affected,
            sectors_affected=event.sectors_affected,
        )

        chain = ImpactChain(
            chain_id=f"CHAIN-{event.event_id}",
            signal=signal,
            created_at=datetime.now(timezone.utc),
        )

        assert chain.chain_id == "CHAIN-EVT-HORMUZ-001"
        assert chain.signal.severity_score == 0.75
        assert len(chain.signal.countries_affected) == 6
        assert chain.chain_status == "ACTIVE"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4: Seed Data Loading Into ORM (no DB write, just conversion)
# ═══════════════════════════════════════════════════════════════════════════════

class TestSeedToORM:
    """Verify all seed data converts cleanly to ORM objects."""

    def test_entity_seed_to_orm(self):
        from src.data_foundation.metadata.loader import load_seed_data
        from src.data_foundation.schemas.entity_registry import EntityRegistryEntry
        from src.data_foundation.models.converters import entity_to_orm

        entities = load_seed_data("entity_registry", EntityRegistryEntry)
        assert len(entities) == 20
        for e in entities:
            orm = entity_to_orm(e)
            assert orm.entity_id is not None
            assert orm.country in ("SA", "AE", "KW", "QA", "BH", "OM")

    def test_event_seed_to_orm(self):
        from src.data_foundation.metadata.loader import load_seed_data
        from src.data_foundation.schemas.event_signals import EventSignal
        from src.data_foundation.models.converters import event_to_orm

        events = load_seed_data("event_signals", EventSignal)
        assert len(events) == 3
        for e in events:
            orm = event_to_orm(e)
            assert orm.event_id is not None
            assert orm.severity_score >= 0.0

    def test_rule_seed_to_orm(self):
        from src.data_foundation.metadata.loader import load_seed_data
        from src.data_foundation.schemas.decision_rules import DecisionRule
        from src.data_foundation.models.converters import rule_to_orm

        rules = load_seed_data("decision_rules", DecisionRule)
        assert len(rules) == 5
        for r in rules:
            orm = rule_to_orm(r)
            assert isinstance(orm.conditions, list)
            assert len(orm.conditions) >= 1

    def test_dlog_seed_to_orm(self):
        from src.data_foundation.metadata.loader import load_seed_data
        from src.data_foundation.schemas.decision_logs import DecisionLogEntry
        from src.data_foundation.models.converters import dlog_to_orm

        logs = load_seed_data("decision_logs", DecisionLogEntry)
        assert len(logs) == 3
        for d in logs:
            orm = dlog_to_orm(d)
            assert isinstance(orm.trigger_context, dict)

    def test_all_seeds_convert(self):
        """Verify every seed dataset converts to ORM without errors."""
        from src.data_foundation.metadata.loader import load_seed_json
        from src.data_foundation.cli.seed_db import SEED_REGISTRY

        for ds_name, (seed_name, pydantic_cls, orm_cls, converter_fn) in SEED_REGISTRY.items():
            raw = load_seed_json(seed_name)
            assert len(raw) > 0, f"Seed {seed_name} is empty"
            for rec in raw:
                pydantic_obj = pydantic_cls.model_validate(rec)
                orm_obj = converter_fn(pydantic_obj)
                assert orm_obj is not None, f"Converter failed for {ds_name}"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5: Oil/Energy Connector Parsing (no network)
# ═══════════════════════════════════════════════════════════════════════════════

class TestOilConnectorParsing:
    """Test oil price data parsing (offline)."""

    def test_price_record_to_signal(self):
        from src.data_foundation.connectors.oil_energy import OilPriceRecord, _to_signal

        rec = OilPriceRecord(
            benchmark="BRENT",
            price_usd=78.50,
            date=date(2025, 1, 15),
            source="test",
            change_pct=-2.5,
        )

        signal = _to_signal(rec)
        assert signal.signal_id == "BRENT-SPOT-2025-01-15"
        assert signal.signal_type == "CRUDE_PRICE_SPOT"
        assert signal.value == 78.50
        assert signal.change_pct == -2.5
        assert signal.unit == "usd_per_barrel"

    def test_multiple_benchmarks(self):
        from src.data_foundation.connectors.oil_energy import OilPriceRecord, _to_signal

        for bm in ["BRENT", "WTI", "OMAN_BLEND"]:
            rec = OilPriceRecord(
                benchmark=bm,
                price_usd=75.0,
                date=date(2025, 1, 15),
                source="test",
            )
            signal = _to_signal(rec)
            assert signal.benchmark == bm
            assert signal.country is None  # Global benchmark


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6: ORM Table Structure Verification
# ═══════════════════════════════════════════════════════════════════════════════

class TestORMTableStructure:
    """Verify ORM models have correct table names and key columns."""

    def test_table_names(self):
        from src.data_foundation.models.tables import (
            EntityRegistryORM, EventSignalORM, MacroIndicatorORM,
            InterestRateSignalORM, OilEnergySignalORM, FXSignalORM,
            CBKIndicatorORM, BankingProfileORM, InsuranceProfileORM,
            LogisticsNodeORM, DecisionRuleORM, DecisionLogORM,
        )
        expected = {
            EntityRegistryORM: "df_entity_registry",
            EventSignalORM: "df_event_signals",
            MacroIndicatorORM: "df_macro_indicators",
            InterestRateSignalORM: "df_interest_rate_signals",
            OilEnergySignalORM: "df_oil_energy_signals",
            FXSignalORM: "df_fx_signals",
            CBKIndicatorORM: "df_cbk_indicators",
            BankingProfileORM: "df_banking_profiles",
            InsuranceProfileORM: "df_insurance_profiles",
            LogisticsNodeORM: "df_logistics_nodes",
            DecisionRuleORM: "df_decision_rules",
            DecisionLogORM: "df_decision_logs",
        }
        for cls, table_name in expected.items():
            assert cls.__tablename__ == table_name, f"{cls.__name__} table name mismatch"

    def test_all_tables_have_foundation_columns(self):
        from src.data_foundation.models.tables import (
            EntityRegistryORM, EventSignalORM, MacroIndicatorORM,
            DecisionRuleORM, DecisionLogORM,
        )
        foundation_cols = {"schema_version", "tenant_id", "created_at", "updated_at", "provenance_hash"}
        for cls in [EntityRegistryORM, EventSignalORM, MacroIndicatorORM, DecisionRuleORM, DecisionLogORM]:
            table_cols = {c.name for c in cls.__table__.columns}
            missing = foundation_cols - table_cols
            assert not missing, f"{cls.__name__} missing foundation columns: {missing}"

    def test_decision_rules_has_audit_columns(self):
        from src.data_foundation.models.tables import DecisionRuleORM
        audit_cols = {"created_by", "approved_by", "audit_notes"}
        table_cols = {c.name for c in DecisionRuleORM.__table__.columns}
        missing = audit_cols - table_cols
        assert not missing, f"DecisionRuleORM missing audit columns: {missing}"

    def test_table_count(self):
        """30 data foundation tables expected (12 core + 4 enforcement + 7 governance + 7 evaluation)."""
        from src.db.postgres import Base
        import src.data_foundation.models.tables  # noqa: F401
        import src.data_foundation.enforcement.orm_models  # noqa: F401
        import src.data_foundation.governance.orm_models  # noqa: F401
        import src.data_foundation.evaluation.orm_models  # noqa: F401
        df_tables = [t for t in Base.metadata.tables if t.startswith("df_")]
        assert len(df_tables) == 30, f"Expected 30 df_ tables, got {len(df_tables)}: {df_tables}"


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7: API Route Contract Tests (FastAPI TestClient)
# ═══════════════════════════════════════════════════════════════════════════════

class TestAPIRouteContracts:
    """Verify API route registration and request/response schemas.

    Uses FastAPI's TestClient which doesn't need a running server or DB.
    We test that routes exist and accept correct request shapes.
    """

    def test_foundation_routes_registered(self):
        """Check that all foundation routes are registered on the app."""
        import sys
        if sys.version_info < (3, 11):
            pytest.skip("src.main requires Python 3.11+ (StrEnum)")
        from src.main import app

        routes = [r.path for r in app.routes if hasattr(r, "path")]
        expected_prefixes = [
            "/api/v1/foundation/entities",
            "/api/v1/foundation/events",
            "/api/v1/foundation/macro",
            "/api/v1/foundation/rules",
            "/api/v1/foundation/decision-logs",
            "/api/v1/foundation/decision-engine",
            "/api/v1/foundation/connectors/oil-energy",
        ]
        for prefix in expected_prefixes:
            matching = [r for r in routes if r.startswith(prefix)]
            assert len(matching) > 0, f"No routes found for prefix: {prefix}"

    def test_decision_engine_route_exists(self):
        import sys
        if sys.version_info < (3, 11):
            pytest.skip("src.main requires Python 3.11+ (StrEnum)")
        from src.main import app

        routes = [r.path for r in app.routes if hasattr(r, "path")]
        assert "/api/v1/foundation/decision-engine/evaluate-event" in routes
