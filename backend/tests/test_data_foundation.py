"""
P1 Data Foundation — Integration Tests
=========================================

Validates that:
1. All 14 P1 schemas can be imported and instantiated
2. All seed data files load and validate against their schemas
3. Ingestion contracts are well-formed
4. Validation framework produces correct results
5. Provenance hashes are computed correctly
"""

import json
from pathlib import Path

import pytest

# ── Schema Imports ────────────────────────────────────────────────────────────

from src.data_foundation.schemas.enums import (
    GCCCountry, Sector, EntityType, DatasetPriority, SourceReliability,
    SignalSeverity, Currency, RiskLevel, DecisionAction, EventCategory,
)
from src.data_foundation.schemas.base import FoundationModel, GeoCoordinate
from src.data_foundation.schemas.dataset_registry import DatasetRegistryEntry
from src.data_foundation.schemas.source_registry import SourceRegistryEntry
from src.data_foundation.schemas.entity_registry import EntityRegistryEntry
from src.data_foundation.schemas.macro_indicators import MacroIndicatorRecord
from src.data_foundation.schemas.interest_rate_signals import InterestRateSignal
from src.data_foundation.schemas.oil_energy_signals import OilEnergySignal
from src.data_foundation.schemas.fx_signals import FXSignal
from src.data_foundation.schemas.cbk_indicators import CBKIndicatorRecord
from src.data_foundation.schemas.event_signals import EventSignal
from src.data_foundation.schemas.banking_sector_profiles import BankingSectorProfile
from src.data_foundation.schemas.insurance_sector_profiles import InsuranceSectorProfile
from src.data_foundation.schemas.logistics_nodes import LogisticsNode
from src.data_foundation.schemas.decision_rules import DecisionRule
from src.data_foundation.schemas.decision_logs import DecisionLogEntry

from src.data_foundation.metadata.loader import load_seed_data, load_seed_json, SEED_FILE_MAP
from src.data_foundation.ingestion.contracts import P1_INGESTION_CONTRACTS
from src.data_foundation.validation.validators import validate_record, validate_batch


# ── Enum Tests ────────────────────────────────────────────────────────────────

class TestEnums:
    def test_gcc_countries_count(self):
        assert len(GCCCountry) == 6

    def test_gcc_countries_values(self):
        codes = {c.value for c in GCCCountry}
        assert codes == {"SA", "AE", "KW", "QA", "BH", "OM"}

    def test_sectors_include_simulation_engine_keys(self):
        """Sectors must include all keys from config.py SECTOR_ALPHA."""
        required = {"energy", "maritime", "banking", "insurance", "fintech",
                     "logistics", "infrastructure", "government", "healthcare"}
        actual = {s.value for s in Sector}
        assert required.issubset(actual)

    def test_severity_levels_match_urs(self):
        expected = {"NOMINAL", "LOW", "GUARDED", "ELEVATED", "HIGH", "SEVERE"}
        actual = {s.value for s in SignalSeverity}
        assert expected == actual


# ── Base Model Tests ──────────────────────────────────────────────────────────

class TestFoundationModel:
    def test_provenance_hash_computed(self):
        model = FoundationModel(schema_version="1.0.0")
        assert model.provenance_hash is not None
        assert len(model.provenance_hash) == 64  # SHA-256

    def test_provenance_hash_deterministic(self):
        m1 = FoundationModel(schema_version="1.0.0", tenant_id="test")
        m2 = FoundationModel(schema_version="1.0.0", tenant_id="test")
        assert m1.provenance_hash == m2.provenance_hash

    def test_provenance_hash_changes_with_data(self):
        m1 = FoundationModel(schema_version="1.0.0", tenant_id="a")
        m2 = FoundationModel(schema_version="1.0.0", tenant_id="b")
        assert m1.provenance_hash != m2.provenance_hash

    def test_geo_coordinate_validation(self):
        geo = GeoCoordinate(latitude=29.3759, longitude=47.9774)
        assert geo.latitude == 29.3759

    def test_geo_coordinate_out_of_range(self):
        with pytest.raises(Exception):
            GeoCoordinate(latitude=100.0, longitude=47.9774)


# ── Seed Data Validation Tests ────────────────────────────────────────────────

SEED_SCHEMA_MAP = {
    "dataset_registry": DatasetRegistryEntry,
    "source_registry": SourceRegistryEntry,
    "entity_registry": EntityRegistryEntry,
    "macro_indicators": MacroIndicatorRecord,
    "interest_rate_signals": InterestRateSignal,
    "oil_energy_signals": OilEnergySignal,
    "fx_signals": FXSignal,
    "cbk_indicators": CBKIndicatorRecord,
    "event_signals": EventSignal,
    "banking_profiles": BankingSectorProfile,
    "insurance_profiles": InsuranceSectorProfile,
    "logistics_nodes": LogisticsNode,
    "decision_rules": DecisionRule,
}


class TestSeedDataLoading:
    @pytest.mark.parametrize("dataset_name", list(SEED_SCHEMA_MAP.keys()))
    def test_seed_file_exists(self, dataset_name):
        """Every dataset in the map must have a seed file."""
        raw = load_seed_json(dataset_name)
        assert len(raw) > 0, f"Seed file for {dataset_name} is empty"

    @pytest.mark.parametrize("dataset_name,model_class", list(SEED_SCHEMA_MAP.items()))
    def test_seed_data_validates(self, dataset_name, model_class):
        """Every seed record must validate against its Pydantic schema."""
        records = load_seed_data(dataset_name, model_class)
        assert len(records) > 0
        for record in records:
            assert record.schema_version == "1.0.0"
            assert record.provenance_hash is not None

    def test_entity_registry_has_required_entities(self):
        entities = load_seed_data("entity_registry", EntityRegistryEntry)
        ids = {e.entity_id for e in entities}
        required = {"KW-CBK", "KW-NBK", "SA-SAMA", "AE-CBUAE", "AE-JEBEL-ALI"}
        assert required.issubset(ids)

    def test_entity_registry_countries(self):
        entities = load_seed_data("entity_registry", EntityRegistryEntry)
        countries = {e.country for e in entities}
        assert GCCCountry.KW in countries
        assert GCCCountry.SA in countries
        assert GCCCountry.AE in countries

    def test_source_registry_has_authoritative_sources(self):
        sources = load_seed_data("source_registry", SourceRegistryEntry)
        authoritative = [s for s in sources if s.reliability == SourceReliability.AUTHORITATIVE]
        assert len(authoritative) >= 3

    def test_banking_profiles_have_prudential_ratios(self):
        profiles = load_seed_data("banking_profiles", BankingSectorProfile)
        for p in profiles:
            assert p.car_pct is not None and p.car_pct > 0
            assert p.total_assets is not None and p.total_assets > 0


# ── Ingestion Contract Tests ─────────────────────────────────────────────────

class TestIngestionContracts:
    def test_all_contracts_have_primary_keys(self):
        for contract in P1_INGESTION_CONTRACTS:
            assert len(contract.primary_key_fields) > 0, \
                f"Contract {contract.contract_id} missing primary keys"

    def test_all_contracts_have_quality_gates(self):
        for contract in P1_INGESTION_CONTRACTS:
            assert len(contract.quality_gates) > 0, \
                f"Contract {contract.contract_id} has no quality gates"

    def test_contract_count(self):
        assert len(P1_INGESTION_CONTRACTS) == 10

    def test_contract_ids_unique(self):
        ids = [c.contract_id for c in P1_INGESTION_CONTRACTS]
        assert len(ids) == len(set(ids))


# ── Validation Framework Tests ────────────────────────────────────────────────

class TestValidation:
    def test_valid_macro_record(self):
        contract = next(c for c in P1_INGESTION_CONTRACTS
                        if c.dataset_id == "p1_macro_indicators")
        record = {"indicator_id": "KW-GDP-2024Q4", "value": 2.3, "country": "KW"}
        report = validate_record(record, contract)
        assert report.is_valid

    def test_null_value_fails_not_null_gate(self):
        contract = next(c for c in P1_INGESTION_CONTRACTS
                        if c.dataset_id == "p1_macro_indicators")
        record = {"indicator_id": "KW-GDP-2024Q4", "value": None, "country": "KW"}
        report = validate_record(record, contract)
        assert not report.is_valid
        assert report.error_count > 0

    def test_range_check_pass(self):
        contract = next(c for c in P1_INGESTION_CONTRACTS
                        if c.dataset_id == "p1_interest_rate_signals")
        record = {"signal_id": "test", "rate_value_bps": 425}
        report = validate_record(record, contract)
        assert report.is_valid

    def test_range_check_fail(self):
        contract = next(c for c in P1_INGESTION_CONTRACTS
                        if c.dataset_id == "p1_interest_rate_signals")
        record = {"signal_id": "test", "rate_value_bps": 9999}
        report = validate_record(record, contract)
        assert not report.is_valid

    def test_batch_validation(self):
        contract = next(c for c in P1_INGESTION_CONTRACTS
                        if c.dataset_id == "p1_macro_indicators")
        records = [
            {"indicator_id": "1", "value": 2.3, "country": "KW"},
            {"indicator_id": "2", "value": None, "country": "SA"},
            {"indicator_id": "3", "value": 3.5, "country": "AE"},
        ]
        report = validate_batch(records, contract)
        assert report.total_records == 3
        assert report.valid_records == 2
        assert report.invalid_records == 1
