"""
P1 Ingestion Pipeline — Runtime Engine
=========================================

Executes ingestion contracts: raw → normalize → validate → tag → emit.

This is the HOW counterpart to contracts.py (the WHAT).

Data Flow:
  RawRecord (dict from source)
    → FieldMapper (apply contract field_mappings)
    → Normalizer (type coercion, enum mapping, dedup key)
    → QualityGateRunner (apply contract quality_gates)
    → ProvenanceTagger (SHA-256 hash, timestamps, source lineage)
    → ValidatedRecord (Pydantic model instance, ready for storage)

Architecture Layer: Data → Features (Layer 1-2 boundary)
Owner: Data Engineering
Consumers: Scheduled jobs, manual import CLI, API ingest endpoints
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, ValidationError

from src.data_foundation.ingestion.contracts import (
    FieldMapping,
    IngestionContract,
    TransformType,
)
from src.data_foundation.validation.validators import (
    BatchValidationReport,
    RecordValidationReport,
    validate_batch,
    validate_record,
)

T = TypeVar("T", bound=BaseModel)


# ═══════════════════════════════════════════════════════════════════════════════
# Transform Functions
# ═══════════════════════════════════════════════════════════════════════════════

def _apply_transform(value: Any, transform: TransformType, params: Optional[Dict] = None) -> Any:
    """Apply a field-level transformation to a value."""
    if value is None:
        return None

    if transform == TransformType.PASSTHROUGH:
        return value
    if transform == TransformType.TO_FLOAT:
        return float(value)
    if transform == TransformType.TO_INT:
        return int(value)
    if transform == TransformType.TO_DATE:
        if isinstance(value, str):
            from datetime import date
            return date.fromisoformat(value)
        return value
    if transform == TransformType.TO_DATETIME:
        if isinstance(value, str):
            return datetime.fromisoformat(value)
        return value
    if transform == TransformType.TO_UPPERCASE:
        return str(value).upper()
    if transform == TransformType.TO_LOWERCASE:
        return str(value).lower()
    if transform == TransformType.STRIP:
        return str(value).strip()
    if transform == TransformType.BPS_TO_PCT:
        return float(value) / 100.0
    if transform == TransformType.PCT_TO_BPS:
        return int(float(value) * 100)
    if transform == TransformType.MAP_ENUM:
        enum_map = (params or {}).get("mapping", {})
        return enum_map.get(str(value), value)
    if transform == TransformType.COMPUTE_HASH:
        return hashlib.sha256(str(value).encode("utf-8")).hexdigest()

    return value  # CUSTOM and unknown: pass through


# ═══════════════════════════════════════════════════════════════════════════════
# Field Mapper
# ═══════════════════════════════════════════════════════════════════════════════

def map_fields(raw: Dict[str, Any], mappings: List[FieldMapping]) -> Dict[str, Any]:
    """Apply field mappings from an ingestion contract to a raw record.

    For each mapping:
      1. Read source_field from raw record (or use default_value)
      2. Apply transform
      3. Write to target_field in output
    """
    output: Dict[str, Any] = {}

    # Start with all raw fields (passthrough for unmapped fields)
    output.update(raw)

    for mapping in mappings:
        source_val = raw.get(mapping.source_field)

        if source_val is None:
            if mapping.required:
                raise ValueError(
                    f"Required field '{mapping.source_field}' missing from raw record."
                )
            source_val = mapping.default_value

        transformed = _apply_transform(source_val, mapping.transform, mapping.transform_params)
        output[mapping.target_field] = transformed

    return output


# ═══════════════════════════════════════════════════════════════════════════════
# Deduplication Key
# ═══════════════════════════════════════════════════════════════════════════════

def compute_dedup_key(record: Dict[str, Any], dedup_fields: List[str]) -> str:
    """Compute a deterministic dedup key from specified fields."""
    parts = [str(record.get(f, "")) for f in sorted(dedup_fields)]
    combined = "|".join(parts)
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()[:16]


# ═══════════════════════════════════════════════════════════════════════════════
# Provenance Tagger
# ═══════════════════════════════════════════════════════════════════════════════

def tag_provenance(
    record: Dict[str, Any],
    contract: IngestionContract,
    ingestion_run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Attach provenance metadata to a record at ingestion time.

    Adds:
      _ingested_at:       UTC timestamp of ingestion
      _source_id:         Source identifier from the contract
      _contract_id:       Ingestion contract ID
      _contract_version:  Contract version
      _ingestion_run_id:  Batch run identifier (for traceability)
      _dedup_key:         Deterministic dedup hash
      _provenance_hash:   SHA-256 of the entire record (excluding provenance fields)
    """
    now = datetime.now(timezone.utc).isoformat()

    # Compute provenance hash BEFORE attaching provenance fields
    canonical = json.dumps(
        {k: v for k, v in record.items() if not k.startswith("_")},
        sort_keys=True,
        default=str,
    )
    prov_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    record["_ingested_at"] = now
    record["_source_id"] = contract.source_id
    record["_contract_id"] = contract.contract_id
    record["_contract_version"] = contract.version
    record["_ingestion_run_id"] = ingestion_run_id
    record["_dedup_key"] = compute_dedup_key(record, contract.dedup_fields) if contract.dedup_fields else None
    record["_provenance_hash"] = prov_hash

    return record


# ═══════════════════════════════════════════════════════════════════════════════
# Ingestion Result
# ═══════════════════════════════════════════════════════════════════════════════

class IngestionResult(BaseModel):
    """Result of ingesting a batch of records through the pipeline."""
    contract_id: str
    dataset_id: str
    ingestion_run_id: Optional[str] = None
    total_raw: int
    mapped: int
    validated: int
    rejected: int
    warnings: int
    accepted_records: List[Dict[str, Any]]
    rejected_records: List[Dict[str, Any]]
    validation_report: Optional[BatchValidationReport] = None
    started_at: datetime
    completed_at: datetime
    duration_ms: float


# ═══════════════════════════════════════════════════════════════════════════════
# Pipeline Executor
# ═══════════════════════════════════════════════════════════════════════════════

def run_ingestion_pipeline(
    raw_records: List[Dict[str, Any]],
    contract: IngestionContract,
    ingestion_run_id: Optional[str] = None,
    dedup_store: Optional[set] = None,
) -> IngestionResult:
    """Execute the full ingestion pipeline for a batch of records.

    Steps:
      1. Field mapping (contract.field_mappings)
      2. Quality gate validation (contract.quality_gates)
      3. Deduplication (contract.dedup_fields)
      4. Provenance tagging
      5. Emit accepted + rejected lists

    Args:
        raw_records:       List of raw dicts from the source
        contract:          Ingestion contract defining the pipeline
        ingestion_run_id:  Optional batch identifier
        dedup_store:       Optional set of already-seen dedup keys

    Returns:
        IngestionResult with accepted/rejected records and metrics
    """
    started_at = datetime.now(timezone.utc)
    if dedup_store is None:
        dedup_store = set()

    mapped_records: List[Dict[str, Any]] = []
    mapping_errors: List[Dict[str, Any]] = []

    # Step 1: Field mapping
    for raw in raw_records:
        try:
            mapped = map_fields(raw, contract.field_mappings)
            mapped_records.append(mapped)
        except (ValueError, KeyError, TypeError) as e:
            raw["_mapping_error"] = str(e)
            mapping_errors.append(raw)

    # Step 2: Quality gate validation
    validation_report = validate_batch(mapped_records, contract)

    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []

    for record, report in zip(mapped_records, validation_report.record_reports):
        if not report.is_valid:
            record["_validation_errors"] = [
                r.model_dump() for r in report.results if not r.passed
            ]
            rejected.append(record)
            continue

        # Step 3: Deduplication
        if contract.dedup_fields:
            dedup_key = compute_dedup_key(record, contract.dedup_fields)
            if dedup_key in dedup_store:
                record["_rejected_reason"] = "duplicate"
                rejected.append(record)
                continue
            dedup_store.add(dedup_key)

        # Step 4: Provenance tagging
        tagged = tag_provenance(record, contract, ingestion_run_id)
        accepted.append(tagged)

    # Combine mapping errors into rejected
    rejected.extend(mapping_errors)

    completed_at = datetime.now(timezone.utc)
    duration_ms = (completed_at - started_at).total_seconds() * 1000

    return IngestionResult(
        contract_id=contract.contract_id,
        dataset_id=contract.dataset_id,
        ingestion_run_id=ingestion_run_id,
        total_raw=len(raw_records),
        mapped=len(mapped_records),
        validated=len(accepted),
        rejected=len(rejected),
        warnings=validation_report.warning_records,
        accepted_records=accepted,
        rejected_records=rejected,
        validation_report=validation_report,
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=duration_ms,
    )
