"""
P1 Ingestion Contracts
========================

Each IngestionContract defines the interface between a raw data source
and a normalized P1 dataset schema. Contracts are declarative — they
specify WHAT to ingest, not HOW (the runtime ingestion engine interprets them).

Architecture Layer: Data → Features (Layer 1-2)
Owner: Data Engineering
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "FieldMapping",
    "QualityGate",
    "IngestionContract",
    "P1_INGESTION_CONTRACTS",
]


class TransformType(str, Enum):
    """Supported field-level transformations."""
    PASSTHROUGH = "passthrough"
    TO_FLOAT = "to_float"
    TO_INT = "to_int"
    TO_DATE = "to_date"
    TO_DATETIME = "to_datetime"
    TO_UPPERCASE = "to_uppercase"
    TO_LOWERCASE = "to_lowercase"
    STRIP = "strip"
    MAP_ENUM = "map_enum"
    COMPUTE_HASH = "compute_hash"
    CURRENCY_CONVERT = "currency_convert"
    BPS_TO_PCT = "bps_to_pct"
    PCT_TO_BPS = "pct_to_bps"
    CUSTOM = "custom"


class QualityGateType(str, Enum):
    """Types of quality gates applied during ingestion."""
    NOT_NULL = "not_null"
    RANGE_CHECK = "range_check"
    REGEX_MATCH = "regex_match"
    ENUM_MEMBERSHIP = "enum_membership"
    UNIQUE = "unique"
    FOREIGN_KEY = "foreign_key"
    CUSTOM = "custom"


class FieldMapping(BaseModel):
    """Maps a raw source field to a normalized schema field."""

    source_field: str = Field(
        ...,
        description="Field name in the raw source data.",
    )
    target_field: str = Field(
        ...,
        description="Field name in the P1 schema.",
    )
    transform: TransformType = Field(
        default=TransformType.PASSTHROUGH,
        description="Transformation to apply.",
    )
    transform_params: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Parameters for the transformation.",
    )
    required: bool = Field(
        default=False,
        description="Whether the source field must be present.",
    )
    default_value: Optional[Any] = Field(
        default=None,
        description="Default value if source field is missing.",
    )

    model_config = ConfigDict(frozen=True)


class QualityGate(BaseModel):
    """A validation gate applied during ingestion."""

    gate_id: str = Field(
        ...,
        description="Unique gate identifier.",
    )
    field: str = Field(
        ...,
        description="Schema field this gate applies to.",
    )
    gate_type: QualityGateType = Field(...)
    params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Gate parameters (e.g., min/max for range_check).",
    )
    severity: str = Field(
        default="ERROR",
        description="WARN = log and continue, ERROR = reject record.",
        examples=["WARN", "ERROR"],
    )
    message: str = Field(
        default="",
        description="Human-readable error message.",
    )

    model_config = ConfigDict(frozen=True)


class IngestionContract(BaseModel):
    """Declarative contract for ingesting a P1 dataset."""

    contract_id: str = Field(
        ...,
        description="Unique contract identifier.",
    )
    dataset_id: str = Field(
        ...,
        description="FK to dataset_registry.",
    )
    source_id: str = Field(
        ...,
        description="FK to source_registry.",
    )
    schema_module: str = Field(
        ...,
        description="Python import path to the target Pydantic model.",
    )
    description: str = Field(default="")
    version: str = Field(default="1.0.0")

    field_mappings: List[FieldMapping] = Field(
        default_factory=list,
        description="Field-level source→target mappings.",
    )
    quality_gates: List[QualityGate] = Field(
        default_factory=list,
        description="Quality gates applied during ingestion.",
    )
    dedup_fields: List[str] = Field(
        default_factory=list,
        description="Fields used for deduplication.",
    )
    primary_key_fields: List[str] = Field(
        ...,
        description="Fields that form the natural key.",
    )
    partition_field: Optional[str] = Field(
        default=None,
        description="Field used for time-based partitioning.",
    )
    batch_size: int = Field(
        default=1000,
        ge=1,
        description="Recommended batch size for ingestion.",
    )

    model_config = ConfigDict(frozen=True)


# ═══════════════════════════════════════════════════════════════════════════════
# P1 Ingestion Contract Definitions
# ═══════════════════════════════════════════════════════════════════════════════

P1_INGESTION_CONTRACTS: List[IngestionContract] = [
    IngestionContract(
        contract_id="IC-MACRO-INDICATORS",
        dataset_id="p1_macro_indicators",
        source_id="imf-weo",
        schema_module="src.data_foundation.schemas.macro_indicators.MacroIndicatorRecord",
        description="Ingest GCC macro indicators from IMF WEO, World Bank, and central bank APIs.",
        primary_key_fields=["indicator_id"],
        dedup_fields=["country", "indicator_code", "period_start"],
        partition_field="period_start",
        quality_gates=[
            QualityGate(
                gate_id="QG-MACRO-001",
                field="value",
                gate_type=QualityGateType.NOT_NULL,
                severity="ERROR",
                message="Macro indicator value cannot be null.",
            ),
            QualityGate(
                gate_id="QG-MACRO-002",
                field="country",
                gate_type=QualityGateType.ENUM_MEMBERSHIP,
                params={"enum": "GCCCountry"},
                severity="ERROR",
                message="Country must be a valid GCC country code.",
            ),
        ],
    ),
    IngestionContract(
        contract_id="IC-INTEREST-RATES",
        dataset_id="p1_interest_rate_signals",
        source_id="gcc-central-banks",
        schema_module="src.data_foundation.schemas.interest_rate_signals.InterestRateSignal",
        description="Ingest policy rates and interbank rates from GCC central banks.",
        primary_key_fields=["signal_id"],
        dedup_fields=["country", "rate_type", "effective_date"],
        partition_field="effective_date",
        quality_gates=[
            QualityGate(
                gate_id="QG-IR-001",
                field="rate_value_bps",
                gate_type=QualityGateType.RANGE_CHECK,
                params={"min": -100, "max": 5000},
                severity="ERROR",
                message="Interest rate must be between -1% and 50%.",
            ),
        ],
    ),
    IngestionContract(
        contract_id="IC-OIL-ENERGY",
        dataset_id="p1_oil_energy_signals",
        source_id="opec-momr",
        schema_module="src.data_foundation.schemas.oil_energy_signals.OilEnergySignal",
        description="Ingest oil prices, production volumes, and energy signals.",
        primary_key_fields=["signal_id"],
        dedup_fields=["signal_type", "benchmark", "observation_date"],
        partition_field="observation_date",
        quality_gates=[
            QualityGate(
                gate_id="QG-OIL-001",
                field="value",
                gate_type=QualityGateType.RANGE_CHECK,
                params={"min": 0, "max": 500},
                severity="WARN",
                message="Oil price outside expected range.",
            ),
        ],
    ),
    IngestionContract(
        contract_id="IC-FX-SIGNALS",
        dataset_id="p1_fx_signals",
        source_id="reuters-fx-feed",
        schema_module="src.data_foundation.schemas.fx_signals.FXSignal",
        description="Ingest FX rates for GCC currency pairs.",
        primary_key_fields=["signal_id"],
        dedup_fields=["base_currency", "quote_currency", "observation_date"],
        partition_field="observation_date",
        quality_gates=[
            QualityGate(
                gate_id="QG-FX-001",
                field="rate",
                gate_type=QualityGateType.RANGE_CHECK,
                params={"min": 0.001, "max": 10000},
                severity="ERROR",
                message="FX rate outside valid range.",
            ),
        ],
    ),
    IngestionContract(
        contract_id="IC-CBK-INDICATORS",
        dataset_id="p1_cbk_indicators",
        source_id="cbk-statistical-bulletin",
        schema_module="src.data_foundation.schemas.cbk_indicators.CBKIndicatorRecord",
        description="Ingest Kuwait CBK monetary and banking indicators.",
        primary_key_fields=["indicator_id"],
        dedup_fields=["indicator_code", "period_start"],
        partition_field="period_start",
        quality_gates=[
            QualityGate(
                gate_id="QG-CBK-001",
                field="value",
                gate_type=QualityGateType.NOT_NULL,
                severity="ERROR",
                message="CBK indicator value cannot be null.",
            ),
        ],
    ),
    IngestionContract(
        contract_id="IC-EVENT-SIGNALS",
        dataset_id="p1_event_signals",
        source_id="acled-api",
        schema_module="src.data_foundation.schemas.event_signals.EventSignal",
        description="Ingest geopolitical and economic event signals.",
        primary_key_fields=["event_id"],
        dedup_fields=["title", "event_time", "source_id"],
        partition_field="event_time",
        quality_gates=[
            QualityGate(
                gate_id="QG-EVT-001",
                field="severity_score",
                gate_type=QualityGateType.RANGE_CHECK,
                params={"min": 0.0, "max": 1.0},
                severity="ERROR",
                message="Severity score must be [0.0, 1.0].",
            ),
            QualityGate(
                gate_id="QG-EVT-002",
                field="category",
                gate_type=QualityGateType.ENUM_MEMBERSHIP,
                params={"enum": "EventCategory"},
                severity="ERROR",
                message="Event category must be a valid EventCategory.",
            ),
        ],
    ),
    IngestionContract(
        contract_id="IC-BANKING-PROFILES",
        dataset_id="p1_banking_sector_profiles",
        source_id="bank-annual-reports",
        schema_module="src.data_foundation.schemas.banking_sector_profiles.BankingSectorProfile",
        description="Ingest bank financial profiles from annual/quarterly reports.",
        primary_key_fields=["profile_id"],
        dedup_fields=["entity_id", "reporting_date"],
        partition_field="reporting_date",
        quality_gates=[
            QualityGate(
                gate_id="QG-BANK-001",
                field="car_pct",
                gate_type=QualityGateType.RANGE_CHECK,
                params={"min": 0, "max": 100},
                severity="WARN",
                message="CAR ratio outside expected range.",
            ),
        ],
    ),
    IngestionContract(
        contract_id="IC-INSURANCE-PROFILES",
        dataset_id="p1_insurance_sector_profiles",
        source_id="insurance-regulator-filings",
        schema_module="src.data_foundation.schemas.insurance_sector_profiles.InsuranceSectorProfile",
        description="Ingest insurer financial profiles.",
        primary_key_fields=["profile_id"],
        dedup_fields=["entity_id", "reporting_date"],
        partition_field="reporting_date",
        quality_gates=[
            QualityGate(
                gate_id="QG-INS-001",
                field="combined_ratio_pct",
                gate_type=QualityGateType.RANGE_CHECK,
                params={"min": 0, "max": 500},
                severity="WARN",
                message="Combined ratio outside expected range.",
            ),
        ],
    ),
    IngestionContract(
        contract_id="IC-LOGISTICS-NODES",
        dataset_id="p1_logistics_nodes",
        source_id="port-authority-data",
        schema_module="src.data_foundation.schemas.logistics_nodes.LogisticsNode",
        description="Ingest GCC logistics node data.",
        primary_key_fields=["node_id"],
        dedup_fields=["node_id"],
        quality_gates=[
            QualityGate(
                gate_id="QG-LOG-001",
                field="geo.latitude",
                gate_type=QualityGateType.RANGE_CHECK,
                params={"min": 10.0, "max": 35.0},
                severity="ERROR",
                message="Latitude must be within GCC bounds.",
            ),
            QualityGate(
                gate_id="QG-LOG-002",
                field="geo.longitude",
                gate_type=QualityGateType.RANGE_CHECK,
                params={"min": 35.0, "max": 60.0},
                severity="ERROR",
                message="Longitude must be within GCC bounds.",
            ),
        ],
    ),
    IngestionContract(
        contract_id="IC-DECISION-RULES",
        dataset_id="p1_decision_rules",
        source_id="analyst-desk",
        schema_module="src.data_foundation.schemas.decision_rules.DecisionRule",
        description="Ingest decision rules from analyst configuration.",
        primary_key_fields=["rule_id"],
        dedup_fields=["rule_id", "version"],
        quality_gates=[
            QualityGate(
                gate_id="QG-DR-001",
                field="conditions",
                gate_type=QualityGateType.NOT_NULL,
                severity="ERROR",
                message="Decision rule must have at least one condition.",
            ),
        ],
    ),
]
