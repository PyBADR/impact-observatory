"""
Macro Signal Schema | مخطط إشارات الاقتصاد الكلي
=================================================

Production-grade unified signal schema for the Macro Intelligence ingestion layer.
Serves as the canonical data contract for all signals entering the Knowledge Graph
(Neo4j) and AI reasoning pipelines.

Architecture Layer: Data → Features (Layer 1-2 of the 7-layer intelligence stack)
Owner: Ingestion Pipeline / Signal Gateway
Consumers: Knowledge Graph Writer, Feature Store, Event Bus, AI Agents

Design Principles:
  1. Backward-compatible: new fields are always Optional with defaults
  2. Extensible: `payload` is a typed discriminated union; `extensions` is Dict[str, Any]
  3. Auditable: SHA-256 lineage_hash, immutable signal_id (UUIDv7)
  4. Multi-tenant: tenant_id isolates data at the schema level
  5. Temporal: event_time (when it happened) vs. ingested_at (when we learned about it)

Versioning Strategy:
  - Schema version follows SemVer: MAJOR.MINOR.PATCH
  - MAJOR: breaking field removal or type change (requires migration)
  - MINOR: new optional fields or new payload domain types
  - PATCH: description/documentation changes only
  - Current version: 1.0.0

Naming Conventions:
  - snake_case for all field names (Pydantic alias for camelCase API output)
  - ISO 8601 for all timestamps (UTC, with timezone designator)
  - UUIDv7 for all identifiers (time-sortable)
  - Enum values: UPPER_SNAKE_CASE
  - Domain prefixes: macro_, ops_, ins_ for domain-specific payload fields
"""

import hashlib
import json
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union
from uuid import uuid4

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Enumerations
# ═══════════════════════════════════════════════════════════════════════════════

class SignalDomain(str, Enum):
    """Primary domain classification for signal routing and KG node typing."""
    MACROECONOMIC = "macroeconomic"
    INSURANCE = "insurance"
    OPERATIONAL = "operational"
    GEOPOLITICAL = "geopolitical"
    FINANCIAL = "financial"
    MARITIME = "maritime"
    ENERGY = "energy"
    CYBER = "cyber"
    REGULATORY = "regulatory"
    CLIMATE = "climate"


class SignalSeverity(str, Enum):
    """Severity classification aligned with Impact Observatory URS thresholds."""
    NOMINAL = "NOMINAL"       # URS < 0.20
    LOW = "LOW"               # URS 0.20–0.35
    GUARDED = "GUARDED"       # URS 0.35–0.50
    ELEVATED = "ELEVATED"     # URS 0.50–0.65
    HIGH = "HIGH"             # URS 0.65–0.80
    SEVERE = "SEVERE"         # URS ≥ 0.80


class SignalStatus(str, Enum):
    """Lifecycle status of a signal in the ingestion pipeline."""
    RAW = "RAW"                       # Just received, no validation
    VALIDATED = "VALIDATED"           # Schema + business rules passed
    ENRICHED = "ENRICHED"             # Augmented with KG context
    CORRELATED = "CORRELATED"         # Linked to existing events/entities
    PROMOTED = "PROMOTED"             # Promoted to Event node in KG
    ARCHIVED = "ARCHIVED"             # Retained but no longer active
    REJECTED = "REJECTED"             # Failed validation or quality gate


class SourceType(str, Enum):
    """Classification of signal origin for trust scoring."""
    API = "API"                       # External REST/GraphQL API
    WEBHOOK = "WEBHOOK"               # Inbound webhook push
    MANUAL = "MANUAL"                 # Human analyst entry
    SCRAPER = "SCRAPER"               # Web/document scraper
    SENSOR = "SENSOR"                 # IoT/telemetry sensor
    SATELLITE = "SATELLITE"           # Satellite imagery/AIS
    INTERNAL_MODEL = "INTERNAL_MODEL" # Output of internal AI/ML model
    FEED = "FEED"                     # Real-time data feed (Reuters, Bloomberg)
    GOVERNMENT = "GOVERNMENT"         # Government/regulatory publication
    ACLED = "ACLED"                   # ACLED conflict data
    AIS = "AIS"                       # Automatic Identification System (maritime)


class ConfidenceMethod(str, Enum):
    """How the confidence score was determined."""
    SOURCE_DECLARED = "SOURCE_DECLARED"     # Source provided its own confidence
    MODEL_COMPUTED = "MODEL_COMPUTED"       # ML model assigned confidence
    RULE_BASED = "RULE_BASED"              # Business rules assigned confidence
    ANALYST_ASSIGNED = "ANALYST_ASSIGNED"   # Human analyst assigned confidence
    DEFAULT = "DEFAULT"                     # No confidence data; using system default


# ═══════════════════════════════════════════════════════════════════════════════
# Source Identification
# ═══════════════════════════════════════════════════════════════════════════════

class SignalSource(BaseModel):
    """Identifies the origin of a signal for trust scoring and deduplication.

    Maps to KG: (:Source) node with -[:EMITTED]-> relationship to (:Signal).
    """
    source_id: str = Field(
        ...,
        description="Stable identifier for the source system (e.g., 'acled-api-v3', 'analyst-desk-riyadh').",
        examples=["reuters-eikon-feed", "manual-analyst-gcc"],
    )
    source_type: SourceType = Field(
        ...,
        description="Classification of the source for trust scoring.",
    )
    source_name: str = Field(
        default="",
        description="Human-readable source name.",
        examples=["Reuters Eikon Real-Time Feed"],
    )
    source_url: Optional[str] = Field(
        default=None,
        description="URL or URI of the originating system or document.",
    )
    source_version: Optional[str] = Field(
        default=None,
        description="Version of the source API or system.",
    )
    trust_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Baseline trust score for this source [0.0–1.0]. "
                    "Used in confidence computation. Government sources default higher.",
    )

    model_config = ConfigDict(populate_by_name=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Confidence & Quality Indicators
# ═══════════════════════════════════════════════════════════════════════════════

class QualityIndicators(BaseModel):
    """Confidence, quality, and reliability metadata for a signal.

    These indicators drive filtering, deduplication, and KG edge weighting.
    Signals below `confidence_score` threshold (default 0.30) are quarantined.
    """
    confidence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Overall confidence in the signal's accuracy [0.0–1.0].",
    )
    confidence_method: ConfidenceMethod = Field(
        default=ConfidenceMethod.DEFAULT,
        description="How the confidence score was determined.",
    )
    data_freshness_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Hours since the underlying data was last updated. "
                    "Null = unknown. Used for staleness detection.",
    )
    completeness_score: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="Fraction of expected fields that are populated [0.0–1.0].",
    )
    corroboration_count: int = Field(
        default=0,
        ge=0,
        description="Number of independent sources confirming this signal.",
    )
    is_corroborated: bool = Field(
        default=False,
        description="True if corroboration_count >= 2.",
    )
    noise_flag: bool = Field(
        default=False,
        description="True if the signal was flagged as potentially noisy by pre-processing.",
    )
    duplicate_of: Optional[str] = Field(
        default=None,
        description="If this signal is a suspected duplicate, the signal_id of the original.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Temporal Tracking
# ═══════════════════════════════════════════════════════════════════════════════

class TemporalContext(BaseModel):
    """Temporal metadata separating event time from ingestion time.

    Critical for KG temporal queries and time-travel analysis.
    """
    event_time: datetime = Field(
        ...,
        description="When the real-world event occurred or was observed (UTC, ISO 8601).",
    )
    ingested_at: datetime = Field(
        default_factory=lambda: datetime.utcnow(),
        description="When the signal entered the ingestion pipeline (UTC, auto-set).",
    )
    reported_at: Optional[datetime] = Field(
        default=None,
        description="When the source reported/published the signal (may differ from event_time).",
    )
    valid_from: Optional[datetime] = Field(
        default=None,
        description="Start of the time window this signal is valid for (e.g., quarterly data).",
    )
    valid_until: Optional[datetime] = Field(
        default=None,
        description="End of the time window. Null = indefinitely valid until superseded.",
    )
    ttl_hours: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Time-to-live in hours. After TTL, signal is auto-archived.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Geospatial Context
# ═══════════════════════════════════════════════════════════════════════════════

class GeoContext(BaseModel):
    """Geospatial context for CesiumJS visualization and PostGIS queries."""
    lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    lng: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    region_code: Optional[str] = Field(
        default=None,
        description="ISO 3166-1 alpha-2 country code or GCC sub-region code.",
        examples=["SA", "AE", "QA", "BH", "KW", "OM"],
    )
    region_name: Optional[str] = Field(default=None, examples=["Strait of Hormuz"])
    affected_zones: List[str] = Field(
        default_factory=list,
        description="List of affected geographic zones or node_ids from the GCC node registry.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Domain-Specific Payloads (Discriminated Union)
# ═══════════════════════════════════════════════════════════════════════════════

class MacroeconomicPayload(BaseModel):
    """Payload for macroeconomic signals (GDP, oil price, FX, rates, etc.)."""
    payload_type: Literal["macroeconomic"] = "macroeconomic"

    indicator_code: str = Field(
        ...,
        description="Standardized indicator code (e.g., 'BRENT_CRUDE_USD', 'SA_GDP_QOQ').",
    )
    indicator_name: str = Field(default="", description="Human-readable indicator name.")
    value: float = Field(..., description="Observed value of the indicator.")
    unit: str = Field(default="", description="Unit of measurement (e.g., 'USD/bbl', '%', 'bps').")
    previous_value: Optional[float] = Field(default=None, description="Prior period value for delta computation.")
    delta_pct: Optional[float] = Field(default=None, description="Percent change from previous value.")
    forecast_value: Optional[float] = Field(default=None, description="Consensus forecast for comparison.")
    surprise_factor: Optional[float] = Field(
        default=None,
        description="(value - forecast) / forecast. Positive = beat, negative = miss.",
    )
    frequency: Optional[str] = Field(default=None, examples=["daily", "weekly", "monthly", "quarterly"])
    affected_sectors: List[str] = Field(default_factory=list)


class InsurancePayload(BaseModel):
    """Payload for insurance-domain signals (claims, underwriting, reserves, cat events)."""
    payload_type: Literal["insurance"] = "insurance"

    line_of_business: str = Field(
        ...,
        description="Insurance line (e.g., 'property', 'marine_cargo', 'motor', 'health').",
    )
    event_type: str = Field(
        default="",
        description="Insurance event type (e.g., 'cat_event', 'claims_surge', 'reserve_breach').",
    )
    estimated_loss_usd: float = Field(default=0.0, ge=0.0)
    insured_loss_usd: Optional[float] = Field(default=None, ge=0.0)
    total_insured_value_usd: Optional[float] = Field(default=None, ge=0.0)
    claims_count: Optional[int] = Field(default=None, ge=0)
    combined_ratio_impact: Optional[float] = Field(default=None)
    reserve_adequacy_ratio: Optional[float] = Field(default=None)
    reinsurance_triggered: bool = Field(default=False)
    ifrs17_impact: Optional[str] = Field(
        default=None,
        description="IFRS 17 classification impact (e.g., 'risk_adjustment_increase', 'csm_unlock').",
    )
    affected_entities: List[str] = Field(
        default_factory=list,
        description="Entity IDs of affected insurers/reinsurers.",
    )


class OperationalPayload(BaseModel):
    """Payload for operational/infrastructure signals (port closures, outages, disruptions)."""
    payload_type: Literal["operational"] = "operational"

    system_id: str = Field(
        ...,
        description="Identifier of the affected system or infrastructure node.",
    )
    system_name: str = Field(default="")
    incident_type: str = Field(
        default="",
        description="Type of incident (e.g., 'port_closure', 'pipeline_rupture', 'cyber_breach').",
    )
    severity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Operational severity [0.0–1.0].",
    )
    capacity_impact_pct: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Percentage of capacity lost.",
    )
    estimated_downtime_hours: Optional[float] = Field(default=None, ge=0.0)
    estimated_recovery_hours: Optional[float] = Field(default=None, ge=0.0)
    affected_flow_types: List[str] = Field(
        default_factory=list,
        description="Flow types affected (e.g., ['energy', 'logistics', 'payments']).",
    )
    upstream_dependencies: List[str] = Field(default_factory=list)
    downstream_dependents: List[str] = Field(default_factory=list)


class GeopoliticalPayload(BaseModel):
    """Payload for geopolitical signals (conflicts, sanctions, diplomatic shifts)."""
    payload_type: Literal["geopolitical"] = "geopolitical"

    event_type: str = Field(
        ...,
        description="Geopolitical event type (e.g., 'armed_conflict', 'sanction', 'treaty').",
    )
    actors: List[str] = Field(default_factory=list, description="State or non-state actors involved.")
    escalation_level: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Escalation intensity [0.0–1.0].",
    )
    fatalities: Optional[int] = Field(default=None, ge=0)
    acled_event_id: Optional[str] = Field(default=None, description="ACLED event reference if sourced from ACLED.")
    affected_trade_routes: List[str] = Field(default_factory=list)
    sanction_target: Optional[str] = Field(default=None)


# Discriminated union type for all payload variants
SignalPayload = Union[
    MacroeconomicPayload,
    InsurancePayload,
    OperationalPayload,
    GeopoliticalPayload,
]


# ═══════════════════════════════════════════════════════════════════════════════
# Entity References (for KG linking)
# ═══════════════════════════════════════════════════════════════════════════════

class EntityReference(BaseModel):
    """Reference to a known entity in the Knowledge Graph.

    Used to pre-link signals to existing KG nodes during ingestion.
    Maps to KG: -[:AFFECTS]-> or -[:MENTIONS]-> relationships.
    """
    entity_id: str = Field(..., description="KG node identifier.")
    entity_type: str = Field(
        ...,
        description="KG node label (e.g., 'Organization', 'Port', 'Pipeline', 'Country').",
    )
    entity_label: str = Field(default="", description="Human-readable entity name.")
    relationship_type: str = Field(
        default="AFFECTS",
        description="Relationship type to create in KG (e.g., 'AFFECTS', 'MENTIONS', 'ORIGINATES_FROM').",
    )
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence that this entity link is correct.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Lineage & Audit
# ═══════════════════════════════════════════════════════════════════════════════

class SignalLineage(BaseModel):
    """Audit trail and lineage tracking for compliance (PDPL, IFRS 17).

    Every signal mutation creates a new lineage entry.
    Maps to KG: -[:DERIVED_FROM]-> chain between (:Signal) nodes.
    """
    parent_signal_ids: List[str] = Field(
        default_factory=list,
        description="Signal IDs this signal was derived from (for aggregated/enriched signals).",
    )
    pipeline_version: str = Field(
        default="1.0.0",
        description="Version of the ingestion pipeline that processed this signal.",
    )
    processing_steps: List[str] = Field(
        default_factory=list,
        description="Ordered list of processing stages applied (e.g., ['validate', 'enrich', 'dedupe']).",
    )
    lineage_hash: str = Field(
        default="",
        description="SHA-256 hash of (signal_id + payload + event_time) for tamper detection.",
    )
    tenant_id: str = Field(
        default="default",
        description="Multi-tenant isolation identifier. Maps to KG partition.",
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Primary Signal Model (the unified schema)
# ═══════════════════════════════════════════════════════════════════════════════

class MacroSignal(BaseModel):
    """Unified Macro Signal — the canonical data contract for all signals
    entering the Macro Intelligence platform.

    This is the SINGLE schema that all ingestion endpoints accept.
    Domain-specific data lives in the `payload` discriminated union.
    Unknown/dynamic fields go in `extensions`.

    KG Mapping:
      - Signal → (:Signal) node
      - Signal.source → (:Source)-[:EMITTED]->(:Signal)
      - Signal.payload → properties on (:Signal) or (:Event) node
      - Signal.entity_refs → (:Signal)-[:AFFECTS]->(:Entity)
      - Signal.tags → (:Signal)-[:TAGGED_WITH]->(:Tag)
      - Signal.lineage.parent_signal_ids → (:Signal)-[:DERIVED_FROM]->(:Signal)

    CONTRACT:
      - signal_id is immutable after creation (UUIDv7 recommended)
      - schema_version must match the pipeline's expected version
      - payload.payload_type discriminator determines KG node properties
      - All timestamps are UTC ISO 8601
      - lineage_hash is computed on every mutation
    """

    # ── Identity ──────────────────────────────────────────────────────────
    signal_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique signal identifier (UUIDv7 recommended for time-sortability).",
    )
    schema_version: str = Field(
        default="1.0.0",
        description="SemVer of this schema. Consumers MUST check major version.",
    )
    signal_type: str = Field(
        ...,
        description="Machine-readable signal type for routing (e.g., 'oil_price_change', 'port_closure').",
        examples=["oil_price_shock", "claims_surge", "port_closure", "armed_conflict"],
    )
    title: str = Field(
        ...,
        max_length=256,
        description="Short human-readable title for dashboards and alerts.",
        examples=["Brent Crude drops 12% on OPEC+ disagreement"],
    )
    description: Optional[str] = Field(
        default=None,
        max_length=4096,
        description="Extended description or narrative context.",
    )

    # ── Classification ────────────────────────────────────────────────────
    domain: SignalDomain = Field(
        ...,
        description="Primary domain for routing and KG node labeling.",
    )
    severity: SignalSeverity = Field(
        default=SignalSeverity.NOMINAL,
        description="Severity classification (aligned with URS thresholds).",
    )
    severity_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Numeric severity [0.0–1.0] for continuous-scale processing.",
    )
    status: SignalStatus = Field(
        default=SignalStatus.RAW,
        description="Current lifecycle status in the ingestion pipeline.",
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Free-form tags for search and filtering (e.g., ['hormuz', 'oil', 'chokepoint']).",
    )

    # ── Temporal ──────────────────────────────────────────────────────────
    temporal: TemporalContext = Field(
        ...,
        description="Temporal metadata (event time, ingestion time, validity window).",
    )

    # ── Geospatial ────────────────────────────────────────────────────────
    geo: Optional[GeoContext] = Field(
        default=None,
        description="Geospatial context for map visualization and spatial queries.",
    )

    # ── Source ────────────────────────────────────────────────────────────
    source: SignalSource = Field(
        ...,
        description="Origin system identification for trust scoring.",
    )

    # ── Quality ───────────────────────────────────────────────────────────
    quality: QualityIndicators = Field(
        default_factory=QualityIndicators,
        description="Confidence, completeness, and reliability indicators.",
    )

    # ── Payload (domain-specific data) ────────────────────────────────────
    payload: SignalPayload = Field(
        ...,
        discriminator="payload_type",
        description="Domain-specific structured data. Type determined by payload_type discriminator.",
    )

    # ── Entity References ─────────────────────────────────────────────────
    entity_refs: List[EntityReference] = Field(
        default_factory=list,
        description="Pre-linked references to known KG entities.",
    )

    # ── Lineage & Audit ───────────────────────────────────────────────────
    lineage: SignalLineage = Field(
        default_factory=SignalLineage,
        description="Audit trail, tenant isolation, and derivation chain.",
    )

    # ── Extensions (escape hatch for unknown/dynamic fields) ──────────────
    extensions: Dict[str, Any] = Field(
        default_factory=dict,
        description="Arbitrary key-value pairs for fields not covered by the schema. "
                    "Used for prototyping new domains before promoting to typed payloads. "
                    "Keys MUST use snake_case. Values MUST be JSON-serializable.",
    )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "title": "MacroSignal",
            "description": "Unified signal schema for the Macro Intelligence ingestion layer.",
        },
    )

    # ── Validators ────────────────────────────────────────────────────────

    @field_validator("signal_type")
    @classmethod
    def signal_type_snake_case(cls, v: str) -> str:
        """Enforce snake_case for signal_type to ensure consistent routing keys."""
        v = v.strip().lower().replace("-", "_").replace(" ", "_")
        if not v:
            raise ValueError("signal_type must not be empty")
        return v

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: List[str]) -> List[str]:
        """Lowercase and deduplicate tags."""
        return list(dict.fromkeys(tag.strip().lower() for tag in v if tag.strip()))

    @model_validator(mode="after")
    def compute_lineage_hash(self):  # type: ignore[return]
        """Compute SHA-256 lineage hash for audit trail if not already set."""
        if not self.lineage.lineage_hash:
            payload_json = self.payload.model_dump_json(exclude_none=True)
            hash_input = f"{self.signal_id}|{payload_json}|{self.temporal.event_time.isoformat()}"
            self.lineage.lineage_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        return self

    @model_validator(mode="after")
    def sync_corroboration_flag(self):  # type: ignore[return]
        """Auto-set is_corroborated based on corroboration_count."""
        if self.quality.corroboration_count >= 2:
            self.quality.is_corroborated = True
        return self


# ═══════════════════════════════════════════════════════════════════════════════
# Ingestion Request / Response Wrappers
# ═══════════════════════════════════════════════════════════════════════════════

class IngestSignalRequest(BaseModel):
    """API request wrapper for POST /api/v1/signals/ingest."""
    signals: List[MacroSignal] = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="Batch of signals to ingest. Max 1000 per request.",
    )
    idempotency_key: Optional[str] = Field(
        default=None,
        description="Client-provided idempotency key for safe retries.",
    )


class IngestSignalResult(BaseModel):
    """Result for a single signal in the batch response."""
    signal_id: str = ""
    status: str = "accepted"
    kg_node_id: Optional[str] = Field(default=None, description="Neo4j node ID if immediately written.")
    errors: List[str] = Field(default_factory=list)


class IngestSignalResponse(BaseModel):
    """API response for POST /api/v1/signals/ingest."""
    accepted: int = 0
    rejected: int = 0
    results: List[IngestSignalResult] = Field(default_factory=list)
    batch_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Batch tracking ID for pipeline observability.",
    )
    processing_time_ms: int = 0
