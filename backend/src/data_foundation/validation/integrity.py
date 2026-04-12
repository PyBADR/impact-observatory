"""
P1 Validation — Referential Integrity Checker
=================================================

Cross-dataset FK validation. Ensures that entity_ids, source_ids,
dataset_ids, and rule_ids referenced in one dataset actually exist
in their home datasets.

This is the data-layer equivalent of database foreign key constraints,
enforced at the application level for flexibility (works without Postgres).

Architecture Layer: Data quality gate (between Layer 1 and 2)
Owner: Data Engineering
Consumers: CI pipeline, data quality dashboard, pre-deployment checks
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from pydantic import BaseModel, Field


class IntegrityViolation(BaseModel):
    """A single referential integrity violation."""
    dataset: str = Field(..., description="Dataset where the violation was found.")
    record_key: str = Field(..., description="Primary key of the violating record.")
    field: str = Field(..., description="Field containing the dangling reference.")
    referenced_dataset: str = Field(..., description="Dataset the FK should point to.")
    referenced_value: str = Field(..., description="The dangling FK value.")
    severity: str = Field(default="ERROR", examples=["ERROR", "WARN"])
    message: str = Field(default="")


class IntegrityReport(BaseModel):
    """Full referential integrity report across all P1 datasets."""
    checked_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    total_checks: int = 0
    violations: List[IntegrityViolation] = Field(default_factory=list)
    violation_count: int = 0
    is_clean: bool = True
    datasets_checked: List[str] = Field(default_factory=list)


def check_referential_integrity(
    entity_ids: Set[str],
    source_ids: Set[str],
    dataset_ids: Set[str],
    rule_ids: Set[str],
    records_by_dataset: Dict[str, List[Dict[str, Any]]],
) -> IntegrityReport:
    """Check referential integrity across all P1 datasets.

    Args:
        entity_ids: Set of valid entity IDs from entity_registry
        source_ids: Set of valid source IDs from source_registry
        dataset_ids: Set of valid dataset IDs from dataset_registry
        rule_ids: Set of valid rule IDs from decision_rules
        records_by_dataset: Dict mapping dataset name → list of record dicts

    Returns:
        IntegrityReport with all violations found
    """
    violations: List[IntegrityViolation] = []
    total_checks = 0
    datasets_checked: List[str] = []

    # FK checks: which fields in which datasets reference which master set
    fk_checks = [
        # (dataset, record_key_field, fk_field, reference_set, ref_dataset, is_list)
        ("macro_indicators", "indicator_id", "source_id", source_ids, "source_registry", False),
        ("interest_rate_signals", "signal_id", "source_id", source_ids, "source_registry", False),
        ("interest_rate_signals", "signal_id", "issuer_entity_id", entity_ids, "entity_registry", False),
        ("oil_energy_signals", "signal_id", "source_id", source_ids, "source_registry", False),
        ("oil_energy_signals", "signal_id", "entity_id", entity_ids, "entity_registry", False),
        ("fx_signals", "signal_id", "source_id", source_ids, "source_registry", False),
        ("cbk_indicators", "indicator_id", "source_id", source_ids, "source_registry", False),
        ("event_signals", "event_id", "source_id", source_ids, "source_registry", False),
        ("event_signals", "event_id", "entity_ids_affected", entity_ids, "entity_registry", True),
        ("banking_profiles", "profile_id", "entity_id", entity_ids, "entity_registry", False),
        ("banking_profiles", "profile_id", "source_id", source_ids, "source_registry", False),
        ("insurance_profiles", "profile_id", "entity_id", entity_ids, "entity_registry", False),
        ("insurance_profiles", "profile_id", "source_id", source_ids, "source_registry", False),
        ("logistics_nodes", "node_id", "entity_id", entity_ids, "entity_registry", False),
        ("logistics_nodes", "node_id", "source_id", source_ids, "source_registry", False),
        ("logistics_nodes", "node_id", "connected_node_ids", None, "logistics_nodes", True),
        ("decision_rules", "rule_id", "source_dataset_ids", dataset_ids, "dataset_registry", True),
        ("decision_logs", "log_id", "rule_id", rule_ids, "decision_rules", False),
    ]

    for (ds, key_field, fk_field, ref_set, ref_ds, is_list) in fk_checks:
        records = records_by_dataset.get(ds, [])
        if not records:
            continue
        if ds not in datasets_checked:
            datasets_checked.append(ds)

        # For logistics_nodes self-reference, build the set from its own records
        if ref_set is None and ref_ds == "logistics_nodes":
            ref_set = {r.get("node_id", "") for r in records}

        for record in records:
            record_key = str(record.get(key_field, "?"))
            fk_value = record.get(fk_field)

            if fk_value is None:
                continue  # Optional FK — not a violation

            total_checks += 1

            if is_list:
                values = fk_value if isinstance(fk_value, list) else [fk_value]
                for v in values:
                    if v and str(v) not in ref_set:
                        violations.append(IntegrityViolation(
                            dataset=ds,
                            record_key=record_key,
                            field=fk_field,
                            referenced_dataset=ref_ds,
                            referenced_value=str(v),
                            message=f"'{v}' not found in {ref_ds}.",
                        ))
            else:
                if str(fk_value) not in ref_set:
                    violations.append(IntegrityViolation(
                        dataset=ds,
                        record_key=record_key,
                        field=fk_field,
                        referenced_dataset=ref_ds,
                        referenced_value=str(fk_value),
                        message=f"'{fk_value}' not found in {ref_ds}.",
                    ))

    return IntegrityReport(
        total_checks=total_checks,
        violations=violations,
        violation_count=len(violations),
        is_clean=len(violations) == 0,
        datasets_checked=datasets_checked,
    )
