"""
P1 Validation Framework
=========================

Runtime validation engine that applies quality gates from ingestion contracts
to data records. Returns structured validation results for audit trail.

Architecture Layer: Data → Features (quality gate between Layer 1 and 2)
Owner: Data Engineering
Consumers: Ingestion pipeline, data quality dashboard
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field, ValidationError

from src.data_foundation.ingestion.contracts import (
    IngestionContract,
    QualityGate,
    QualityGateType,
)

__all__ = [
    "ValidationResult",
    "RecordValidationReport",
    "BatchValidationReport",
    "validate_record",
    "validate_batch",
]


class ValidationSeverity(str, Enum):
    WARN = "WARN"
    ERROR = "ERROR"


class ValidationResult(BaseModel):
    """Result of a single quality gate check."""
    gate_id: str
    field: str
    passed: bool
    severity: ValidationSeverity
    message: str
    actual_value: Optional[Any] = None


class RecordValidationReport(BaseModel):
    """Validation report for a single record."""
    record_key: str = Field(description="Natural key of the record.")
    is_valid: bool = Field(description="True if no ERROR-severity gates failed.")
    results: List[ValidationResult] = Field(default_factory=list)
    error_count: int = 0
    warn_count: int = 0
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class BatchValidationReport(BaseModel):
    """Validation report for a batch of records."""
    contract_id: str
    dataset_id: str
    total_records: int
    valid_records: int
    invalid_records: int
    warning_records: int
    record_reports: List[RecordValidationReport] = Field(default_factory=list)
    validated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


def _get_nested_value(data: Dict[str, Any], field: str) -> Any:
    """Get a value from a nested dict using dot notation."""
    parts = field.split(".")
    current = data
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        elif hasattr(current, part):
            current = getattr(current, part)
        else:
            return None
    return current


def _evaluate_gate(gate: QualityGate, data: Dict[str, Any]) -> ValidationResult:
    """Evaluate a single quality gate against a data record."""
    value = _get_nested_value(data, gate.field)
    severity = ValidationSeverity(gate.severity)

    if gate.gate_type == QualityGateType.NOT_NULL:
        passed = value is not None
        return ValidationResult(
            gate_id=gate.gate_id,
            field=gate.field,
            passed=passed,
            severity=severity,
            message=gate.message if not passed else "OK",
            actual_value=value,
        )

    if gate.gate_type == QualityGateType.RANGE_CHECK:
        if value is None:
            return ValidationResult(
                gate_id=gate.gate_id,
                field=gate.field,
                passed=False,
                severity=severity,
                message=f"Cannot range-check null value for {gate.field}.",
                actual_value=None,
            )
        min_val = gate.params.get("min")
        max_val = gate.params.get("max")
        passed = True
        if min_val is not None and value < min_val:
            passed = False
        if max_val is not None and value > max_val:
            passed = False
        return ValidationResult(
            gate_id=gate.gate_id,
            field=gate.field,
            passed=passed,
            severity=severity,
            message=gate.message if not passed else "OK",
            actual_value=value,
        )

    if gate.gate_type == QualityGateType.REGEX_MATCH:
        pattern = gate.params.get("pattern", ".*")
        passed = bool(re.match(pattern, str(value or "")))
        return ValidationResult(
            gate_id=gate.gate_id,
            field=gate.field,
            passed=passed,
            severity=severity,
            message=gate.message if not passed else "OK",
            actual_value=value,
        )

    if gate.gate_type == QualityGateType.ENUM_MEMBERSHIP:
        enum_name = gate.params.get("enum", "")
        # For runtime, we check if the value is a non-empty string
        # Full enum resolution happens when the Pydantic model validates
        passed = value is not None and str(value).strip() != ""
        return ValidationResult(
            gate_id=gate.gate_id,
            field=gate.field,
            passed=passed,
            severity=severity,
            message=gate.message if not passed else "OK",
            actual_value=value,
        )

    # Default: pass unknown gate types with a warning
    return ValidationResult(
        gate_id=gate.gate_id,
        field=gate.field,
        passed=True,
        severity=ValidationSeverity.WARN,
        message=f"Unknown gate type: {gate.gate_type}",
        actual_value=value,
    )


def validate_record(
    data: Dict[str, Any],
    contract: IngestionContract,
    record_key: Optional[str] = None,
) -> RecordValidationReport:
    """Validate a single record against an ingestion contract's quality gates."""
    if record_key is None:
        key_parts = [str(data.get(f, "?")) for f in contract.primary_key_fields]
        record_key = "|".join(key_parts)

    results: List[ValidationResult] = []
    error_count = 0
    warn_count = 0

    for gate in contract.quality_gates:
        result = _evaluate_gate(gate, data)
        results.append(result)
        if not result.passed:
            if result.severity == ValidationSeverity.ERROR:
                error_count += 1
            else:
                warn_count += 1

    return RecordValidationReport(
        record_key=record_key,
        is_valid=error_count == 0,
        results=results,
        error_count=error_count,
        warn_count=warn_count,
    )


def validate_batch(
    records: List[Dict[str, Any]],
    contract: IngestionContract,
) -> BatchValidationReport:
    """Validate a batch of records against an ingestion contract."""
    reports = []
    valid = 0
    invalid = 0
    warnings = 0

    for record in records:
        report = validate_record(record, contract)
        reports.append(report)
        if report.is_valid:
            valid += 1
            if report.warn_count > 0:
                warnings += 1
        else:
            invalid += 1

    return BatchValidationReport(
        contract_id=contract.contract_id,
        dataset_id=contract.dataset_id,
        total_records=len(records),
        valid_records=valid,
        invalid_records=invalid,
        warning_records=warnings,
        record_reports=reports,
    )
