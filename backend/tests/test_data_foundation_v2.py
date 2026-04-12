"""
P1 Data Foundation — V2 Tests (Phases 2-7)
=============================================

Tests for:
  - Ingestion pipeline (pipeline.py, loaders.py)
  - Decision layer (impact_chain.py, rule_engine.py)
  - Referential integrity (integrity.py)
  - Validation entrypoint (entrypoint.py)
  - Decision logs seed data
"""

import json
from datetime import datetime, timezone

import pytest

# ── Ingestion Pipeline Tests ─────────────────────────────────────────────────

from src.data_foundation.ingestion.pipeline import (
    map_fields,
    compute_dedup_key,
    tag_provenance,
    run_ingestion_pipeline,
    IngestionResult,
)
from src.data_foundation.ingestion.contracts import (
    FieldMapping,
    IngestionContract,
    P1_INGESTION_CONTRACTS,
    QualityGate,
    QualityGateType,
    TransformType,
)
from src.data_foundation.ingestion.loaders import (
    APILoader,
    CSVLoader,
    ManualLoader,
    DerivedLoader,
    LoaderConfig,
    get_loader,
)


class TestFieldMapper:
    def test_passthrough(self):
        raw = {"indicator_id": "X", "value": 42.0}
        result = map_fields(raw, [])
        assert result["indicator_id"] == "X"

    def test_transform_bps_to_pct(self):
        mapping = FieldMapping(
            source_field="rate_bps",
            target_field="rate_pct",
            transform=TransformType.BPS_TO_PCT,
            required=True,
        )
        result = map_fields({"rate_bps": 425}, [mapping])
        assert result["rate_pct"] == 4.25

    def test_transform_to_uppercase(self):
        mapping = FieldMapping(
            source_field="country",
            target_field="country",
            transform=TransformType.TO_UPPERCASE,
        )
        result = map_fields({"country": "kw"}, [mapping])
        assert result["country"] == "KW"

    def test_required_field_missing_raises(self):
        mapping = FieldMapping(
            source_field="missing_field",
            target_field="target",
            required=True,
        )
        with pytest.raises(ValueError, match="Required field"):
            map_fields({}, [mapping])

    def test_default_value_used(self):
        mapping = FieldMapping(
            source_field="missing",
            target_field="target",
            default_value="DEFAULT",
        )
        result = map_fields({}, [mapping])
        assert result["target"] == "DEFAULT"


class TestDedupKey:
    def test_deterministic(self):
        record = {"a": "1", "b": "2"}
        k1 = compute_dedup_key(record, ["a", "b"])
        k2 = compute_dedup_key(record, ["a", "b"])
        assert k1 == k2

    def test_order_independent(self):
        record = {"a": "1", "b": "2"}
        k1 = compute_dedup_key(record, ["a", "b"])
        k2 = compute_dedup_key(record, ["b", "a"])
        assert k1 == k2  # sorted internally

    def test_different_data_different_key(self):
        k1 = compute_dedup_key({"a": "1"}, ["a"])
        k2 = compute_dedup_key({"a": "2"}, ["a"])
        assert k1 != k2


class TestProvenanceTagger:
    def test_adds_provenance_fields(self):
        contract = P1_INGESTION_CONTRACTS[0]
        record = {"indicator_id": "TEST", "value": 1.0, "country": "KW"}
        tagged = tag_provenance(record, contract, ingestion_run_id="RUN-001")
        assert tagged["_ingested_at"] is not None
        assert tagged["_source_id"] == contract.source_id
        assert tagged["_contract_id"] == contract.contract_id
        assert tagged["_provenance_hash"] is not None
        assert len(tagged["_provenance_hash"]) == 64
        assert tagged["_ingestion_run_id"] == "RUN-001"


class TestIngestionPipeline:
    def test_full_pipeline_valid_records(self):
        contract = next(c for c in P1_INGESTION_CONTRACTS
                        if c.dataset_id == "p1_macro_indicators")
        records = [
            {"indicator_id": "1", "value": 2.3, "country": "KW"},
            {"indicator_id": "2", "value": 3.1, "country": "SA"},
        ]
        result = run_ingestion_pipeline(records, contract, ingestion_run_id="TEST-RUN")
        assert isinstance(result, IngestionResult)
        assert result.total_raw == 2
        assert result.validated == 2
        assert result.rejected == 0
        assert len(result.accepted_records) == 2
        # Provenance tagged
        assert result.accepted_records[0]["_contract_id"] == contract.contract_id

    def test_pipeline_rejects_invalid(self):
        contract = next(c for c in P1_INGESTION_CONTRACTS
                        if c.dataset_id == "p1_macro_indicators")
        records = [
            {"indicator_id": "1", "value": 2.3, "country": "KW"},
            {"indicator_id": "2", "value": None, "country": "SA"},  # fails NOT_NULL gate
        ]
        result = run_ingestion_pipeline(records, contract)
        assert result.validated == 1
        assert result.rejected == 1

    def test_pipeline_deduplication(self):
        contract = next(c for c in P1_INGESTION_CONTRACTS
                        if c.dataset_id == "p1_macro_indicators")
        records = [
            {"indicator_id": "1", "value": 2.3, "country": "KW",
             "indicator_code": "GDP_REAL", "period_start": "2024-01-01"},
            {"indicator_id": "1", "value": 2.3, "country": "KW",
             "indicator_code": "GDP_REAL", "period_start": "2024-01-01"},  # duplicate
        ]
        result = run_ingestion_pipeline(records, contract)
        assert result.validated == 1
        assert result.rejected == 1


# ── Loader Tests ──────────────────────────────────────────────────────────────

class TestLoaders:
    def _config(self):
        return LoaderConfig(source_id="test-source", dataset_id="test-dataset")

    def test_csv_loader_from_content(self):
        loader = CSVLoader(self._config())
        csv_content = "indicator_id,value,country\nKW-GDP-1,2.3,KW\nSA-GDP-1,4.1,SA"
        result = loader.fetch(content=csv_content)
        assert result.record_count == 2
        assert result.records[0]["indicator_id"] == "KW-GDP-1"

    def test_csv_loader_missing_file(self):
        loader = CSVLoader(self._config())
        result = loader.fetch(file_path="/nonexistent/file.csv")
        assert result.record_count == 0
        assert len(result.errors) > 0

    def test_manual_loader(self):
        loader = ManualLoader(self._config())
        result = loader.fetch(records=[{"rule_id": "RULE-001"}])
        assert result.record_count == 1

    def test_manual_loader_no_records(self):
        loader = ManualLoader(self._config())
        result = loader.fetch()
        assert result.record_count == 0
        assert len(result.errors) > 0

    def test_api_loader_with_test_data(self):
        loader = APILoader(self._config())
        result = loader.fetch(response_data=[{"key": "value"}])
        assert result.record_count == 1

    def test_api_loader_not_connected(self):
        loader = APILoader(self._config())
        result = loader.fetch(url="https://api.example.com")
        assert result.record_count == 0
        assert "not yet connected" in result.errors[0]

    def test_derived_loader(self):
        loader = DerivedLoader(self._config())
        def double_values(data):
            return [{"value": d["value"] * 2} for d in data]
        result = loader.fetch(compute_fn=double_values, input_data=[{"value": 5}])
        assert result.record_count == 1
        assert result.records[0]["value"] == 10

    def test_loader_factory(self):
        config = self._config()
        assert isinstance(get_loader("API", config), APILoader)
        assert isinstance(get_loader("CSV_UPLOAD", config), CSVLoader)
        assert isinstance(get_loader("MANUAL", config), ManualLoader)
        assert isinstance(get_loader("INTERNAL_MODEL", config), DerivedLoader)

    def test_loader_factory_unknown_type(self):
        with pytest.raises(ValueError, match="No loader registered"):
            get_loader("UNKNOWN_TYPE", self._config())


# ── Decision Layer Tests ──────────────────────────────────────────────────────

from src.data_foundation.decision.impact_chain import (
    SignalDetection,
    TransmissionPath,
    ExposureAssessment,
    DecisionProposal,
    ImpactChain,
)
from src.data_foundation.decision.rule_engine import (
    DataState,
    evaluate_rule,
    evaluate_all_rules,
)
from src.data_foundation.schemas.decision_rules import DecisionRule, RuleCondition
from src.data_foundation.schemas.enums import (
    DecisionAction,
    RiskLevel,
    SignalSeverity,
    GCCCountry,
    Sector,
)
from src.data_foundation.metadata.loader import load_seed_data


class TestImpactChain:
    def test_signal_detection_model(self):
        signal = SignalDetection(
            signal_ref_id="EVT-HORMUZ-001",
            signal_dataset="p1_event_signals",
            signal_type="GEOPOLITICAL_EVENT",
            severity=SignalSeverity.HIGH,
            severity_score=0.72,
            detected_at=datetime.now(timezone.utc),
            countries_affected=[GCCCountry.KW, GCCCountry.SA],
            sectors_affected=[Sector.MARITIME, Sector.ENERGY],
        )
        assert signal.severity_score == 0.72

    def test_full_chain(self):
        chain = ImpactChain(
            chain_id="CHAIN-001",
            signal=SignalDetection(
                signal_ref_id="EVT-001",
                signal_dataset="p1_event_signals",
                signal_type="OIL_PRICE_SHOCK",
                severity=SignalSeverity.SEVERE,
                severity_score=0.85,
                detected_at=datetime.now(timezone.utc),
            ),
            created_at=datetime.now(timezone.utc),
        )
        assert chain.chain_status == "ACTIVE"
        assert chain.signal.severity == SignalSeverity.SEVERE


class TestRuleEngine:
    def _make_rule(self, field="oil_energy_signals.change_pct", op="lt", threshold=-30.0):
        return DecisionRule(
            rule_id="TEST-RULE",
            rule_name="Test Rule",
            description="Test rule for unit tests.",
            version=1,
            is_active=True,
            conditions=[
                RuleCondition(
                    field=field,
                    operator=op,
                    threshold=threshold,
                    schema_version="1.0.0",
                )
            ],
            action=DecisionAction.ALERT,
            escalation_level=RiskLevel.HIGH,
            cooldown_minutes=0,
            requires_human_approval=False,
        )

    def test_rule_triggers(self):
        rule = self._make_rule()
        state = DataState(values={"oil_energy_signals.change_pct": -35.0})
        result = evaluate_rule(rule, state)
        assert result.triggered is True
        assert result.action == DecisionAction.ALERT

    def test_rule_does_not_trigger(self):
        rule = self._make_rule()
        state = DataState(values={"oil_energy_signals.change_pct": -10.0})
        result = evaluate_rule(rule, state)
        assert result.triggered is False

    def test_inactive_rule_skipped(self):
        rule = self._make_rule()
        rule.is_active = False
        state = DataState(values={"oil_energy_signals.change_pct": -35.0})
        result = evaluate_rule(rule, state)
        assert result.triggered is False
        assert "inactive" in result.reason.lower()

    def test_missing_field_does_not_trigger(self):
        rule = self._make_rule()
        state = DataState(values={})
        result = evaluate_rule(rule, state)
        assert result.triggered is False

    def test_cooldown_blocks(self):
        rule = self._make_rule()
        rule.cooldown_minutes = 9999
        state = DataState(values={"oil_energy_signals.change_pct": -35.0})
        last_triggers = {"TEST-RULE": datetime.now(timezone.utc)}
        result = evaluate_rule(rule, state, last_trigger_times=last_triggers)
        assert result.triggered is True
        assert result.cooldown_blocked is True

    def test_evaluate_all_rules(self):
        rules = load_seed_data("decision_rules", DecisionRule)
        state = DataState(values={
            "oil_energy_signals.change_pct": -35.0,
            "banking_sector_profiles.npl_ratio_pct": 6.2,
            "banking_sector_profiles.is_dsib": True,
            "event_signals.severity_score": 0.72,
            "event_signals.scenario_ids": ["hormuz_chokepoint_disruption"],
            "fx_signals.deviation_from_peg_bps": 55,
            "insurance_sector_profiles.combined_ratio_pct": 125.0,
        })
        output = evaluate_all_rules(rules, state)
        assert output.total_evaluated == len(rules)
        assert output.total_triggered > 0
        assert len(output.data_state_hash) == 64

    def test_eq_operator(self):
        rule = self._make_rule(field="x", op="eq", threshold=True)
        state = DataState(values={"x": True})
        result = evaluate_rule(rule, state)
        assert result.triggered is True

    def test_gte_operator(self):
        rule = self._make_rule(field="x", op="gte", threshold=5.0)
        state = DataState(values={"x": 5.0})
        result = evaluate_rule(rule, state)
        assert result.triggered is True


# ── Referential Integrity Tests ───────────────────────────────────────────────

from src.data_foundation.validation.integrity import check_referential_integrity


class TestReferentialIntegrity:
    def test_clean_data_passes(self):
        report = check_referential_integrity(
            entity_ids={"KW-CBK", "KW-NBK"},
            source_ids={"cbk-statistical-bulletin"},
            dataset_ids={"p1_macro_indicators"},
            rule_ids=set(),
            records_by_dataset={
                "macro_indicators": [
                    {"indicator_id": "1", "source_id": "cbk-statistical-bulletin"},
                ],
            },
        )
        assert report.is_clean

    def test_dangling_source_id(self):
        report = check_referential_integrity(
            entity_ids=set(),
            source_ids={"valid-source"},
            dataset_ids=set(),
            rule_ids=set(),
            records_by_dataset={
                "macro_indicators": [
                    {"indicator_id": "1", "source_id": "nonexistent-source"},
                ],
            },
        )
        assert not report.is_clean
        assert report.violation_count == 1
        assert report.violations[0].referenced_value == "nonexistent-source"

    def test_dangling_entity_id(self):
        report = check_referential_integrity(
            entity_ids={"KW-CBK"},
            source_ids={"src-1"},
            dataset_ids=set(),
            rule_ids=set(),
            records_by_dataset={
                "banking_profiles": [
                    {"profile_id": "1", "entity_id": "NONEXISTENT-BANK", "source_id": "src-1"},
                ],
            },
        )
        assert not report.is_clean
        assert any(v.field == "entity_id" for v in report.violations)


# ── Validation Entrypoint Tests ───────────────────────────────────────────────

from src.data_foundation.validation.entrypoint import validate_all_p1


class TestValidationEntrypoint:
    def test_full_validation_runs(self):
        result = validate_all_p1()
        assert "overall_pass" in result
        assert "schema_results" in result
        assert "integrity_report" in result
        assert result["summary"]["total_datasets"] >= 13

    def test_all_schemas_pass(self):
        result = validate_all_p1()
        for ds_name, ds_result in result["schema_results"].items():
            assert ds_result["status"] in ("PASS", "SKIP"), \
                f"Schema validation failed for {ds_name}: {ds_result}"


# ── Decision Logs Seed Tests ─────────────────────────────────────────────────

from src.data_foundation.schemas.decision_logs import DecisionLogEntry


class TestDecisionLogsSeed:
    def test_decision_logs_load(self):
        logs = load_seed_data("decision_logs", DecisionLogEntry)
        assert len(logs) == 3

    def test_decision_logs_have_trigger_context(self):
        logs = load_seed_data("decision_logs", DecisionLogEntry)
        for log in logs:
            assert log.trigger_context is not None
            assert log.rule_id is not None

    def test_decision_logs_reference_valid_rules(self):
        logs = load_seed_data("decision_logs", DecisionLogEntry)
        rules = load_seed_data("decision_rules", DecisionRule)
        rule_ids = {r.rule_id for r in rules}
        for log in logs:
            assert log.rule_id in rule_ids, \
                f"Decision log {log.log_id} references unknown rule {log.rule_id}"
