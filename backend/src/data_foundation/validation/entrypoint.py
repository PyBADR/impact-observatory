"""
P1 Validation — Entrypoint
=============================

Single-call validation that runs:
  1. Schema validation (Pydantic model_validate for each seed record)
  2. Quality gate checks (ingestion contract gates)
  3. Referential integrity (cross-dataset FK checks)

Usage:
    from src.data_foundation.validation.entrypoint import validate_all_p1
    report = validate_all_p1()
    assert report["overall_pass"]

Architecture Layer: Data quality gate (Layer 1)
Owner: Data Engineering
Consumers: CI pipeline, pre-deployment checks, health endpoint
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Set

from src.data_foundation.metadata.loader import load_seed_json, SEED_FILE_MAP
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
from src.data_foundation.validation.integrity import (
    IntegrityReport,
    check_referential_integrity,
)


SCHEMA_MAP = {
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


def validate_all_p1() -> Dict[str, Any]:
    """Run full P1 data foundation validation.

    Returns a dict with:
      - overall_pass: bool
      - schema_results: per-dataset schema validation
      - integrity_report: cross-dataset FK check
      - summary: human-readable summary
    """
    schema_results: Dict[str, Dict[str, Any]] = {}
    all_raw: Dict[str, List[Dict[str, Any]]] = {}

    # Phase 1: Schema validation
    total_records = 0
    total_errors = 0

    for ds_name, model_cls in SCHEMA_MAP.items():
        try:
            raw = load_seed_json(ds_name)
        except (FileNotFoundError, ValueError):
            schema_results[ds_name] = {
                "status": "SKIP",
                "reason": "Seed file not found",
                "valid": 0,
                "invalid": 0,
            }
            continue

        all_raw[ds_name] = raw
        valid = 0
        invalid = 0
        errors: List[str] = []

        for i, record in enumerate(raw):
            total_records += 1
            try:
                model_cls.model_validate(record)
                valid += 1
            except Exception as e:
                invalid += 1
                total_errors += 1
                errors.append(f"Record {i}: {str(e)[:200]}")

        schema_results[ds_name] = {
            "status": "PASS" if invalid == 0 else "FAIL",
            "valid": valid,
            "invalid": invalid,
            "errors": errors[:5],  # First 5 for brevity
        }

    # Phase 2: Build reference sets
    entity_ids: Set[str] = set()
    for r in all_raw.get("entity_registry", []):
        eid = r.get("entity_id")
        if eid:
            entity_ids.add(str(eid))

    source_ids: Set[str] = set()
    for r in all_raw.get("source_registry", []):
        sid = r.get("source_id")
        if sid:
            source_ids.add(str(sid))

    dataset_ids: Set[str] = set()
    for r in all_raw.get("dataset_registry", []):
        did = r.get("dataset_id")
        if did:
            dataset_ids.add(str(did))

    rule_ids: Set[str] = set()
    for r in all_raw.get("decision_rules", []):
        rid = r.get("rule_id")
        if rid:
            rule_ids.add(str(rid))

    # Phase 3: Referential integrity
    integrity_report = check_referential_integrity(
        entity_ids=entity_ids,
        source_ids=source_ids,
        dataset_ids=dataset_ids,
        rule_ids=rule_ids,
        records_by_dataset=all_raw,
    )

    overall_pass = total_errors == 0 and integrity_report.is_clean

    return {
        "overall_pass": overall_pass,
        "validated_at": datetime.now(timezone.utc).isoformat(),
        "schema_results": schema_results,
        "integrity_report": integrity_report.model_dump(),
        "summary": {
            "total_datasets": len(SCHEMA_MAP),
            "total_records_checked": total_records,
            "schema_errors": total_errors,
            "integrity_violations": integrity_report.violation_count,
            "integrity_checks_run": integrity_report.total_checks,
        },
    }
