"""P2 Data Foundation — SQLAlchemy ORM table definitions.

Maps 1:1 to Pydantic schemas in src/data_foundation/schemas/.
All tables share:
  - schema_version, tenant_id, created_at, updated_at, provenance_hash (FoundationModel)
  - Strategic indexes on frequently queried columns
  - JSONB for flexible nested data (geo coords, lists, metadata)

Design decisions:
  - Enum columns stored as VARCHAR(64) — Postgres native ENUMs cause migration pain
  - List/Dict fields stored as JSONB — avoids junction tables for P2 simplicity
  - GeoCoordinate flattened to geo_lat/geo_lng — avoids PostGIS dependency for P2
  - Primary keys match Pydantic field names (entity_id, event_id, etc.) — not synthetic UUIDs
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.db.postgres import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ═══════════════════════════════════════════════════════════════════════════════
# Mixin: columns shared by every P1 table (mirrors FoundationModel)
# ═══════════════════════════════════════════════════════════════════════════════

class _FoundationMixin:
    """Columns present on every data_foundation table."""
    schema_version: Mapped[str] = mapped_column(String(16), default="1.0.0", nullable=False)
    tenant_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow, nullable=False)
    provenance_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)


class _AuditMixin:
    """Columns for auditable entities (mirrors AuditMixin)."""
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approved_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    audit_notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_entity_registry
# Schema: EntityRegistryEntry
# ═══════════════════════════════════════════════════════════════════════════════

class EntityRegistryORM(_FoundationMixin, Base):
    __tablename__ = "df_entity_registry"

    entity_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    entity_name: Mapped[str] = mapped_column(String(256), nullable=False)
    entity_name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    entity_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    country: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    sector: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    parent_entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    geo_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    geo_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    gdp_weight: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    criticality_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    systemic_importance: Mapped[str | None] = mapped_column(String(64), nullable=True)
    regulatory_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    swift_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    lei_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    website: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    related_entity_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_df_entity_criticality", "criticality_score"),
        Index("ix_df_entity_type_country", "entity_type", "country"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_event_signals
# Schema: EventSignal
# ═══════════════════════════════════════════════════════════════════════════════

class EventSignalORM(_FoundationMixin, Base):
    __tablename__ = "df_event_signals"

    event_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    title_ar: Mapped[str | None] = mapped_column(String(512), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    subcategory: Mapped[str | None] = mapped_column(String(64), nullable=True)
    severity: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    severity_score: Mapped[float] = mapped_column(Float, nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    countries_affected: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    sectors_affected: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    entity_ids_affected: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    scenario_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    geo_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    geo_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    source_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    confidence_method: Mapped[str] = mapped_column(String(64), default="DEFAULT", nullable=False)
    corroborating_source_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_ongoing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    parent_event_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_df_event_severity_score", "severity_score"),
        Index("ix_df_event_category_severity", "category", "severity"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_macro_indicators
# Schema: MacroIndicatorRecord
# ═══════════════════════════════════════════════════════════════════════════════

class MacroIndicatorORM(_FoundationMixin, Base):
    __tablename__ = "df_macro_indicators"

    indicator_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    country: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    indicator_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    indicator_name: Mapped[str] = mapped_column(String(256), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str | None] = mapped_column(String(4), nullable=True)
    period_start: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    frequency: Mapped[str] = mapped_column(String(32), nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    source_reliability: Mapped[str] = mapped_column(String(32), default="HIGH", nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.8, nullable=False)
    confidence_method: Mapped[str] = mapped_column(String(64), default="SOURCE_DECLARED", nullable=False)
    is_provisional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    yoy_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_df_macro_country_code", "country", "indicator_code"),
        Index("ix_df_macro_period", "period_start", "period_end"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_interest_rate_signals
# Schema: InterestRateSignal
# ═══════════════════════════════════════════════════════════════════════════════

class InterestRateSignalORM(_FoundationMixin, Base):
    __tablename__ = "df_interest_rate_signals"

    signal_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    country: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    issuer_entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    rate_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    rate_value_bps: Mapped[int] = mapped_column(Integer, nullable=False)
    rate_value_pct: Mapped[float] = mapped_column(Float, nullable=False)
    effective_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    previous_rate_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    change_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    reference_rate: Mapped[str | None] = mapped_column(String(64), nullable=True)
    spread_to_reference_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    currency: Mapped[str] = mapped_column(String(4), default="USD", nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    confidence_method: Mapped[str] = mapped_column(String(64), default="SOURCE_DECLARED", nullable=False)
    is_scheduled_decision: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    next_decision_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_oil_energy_signals
# Schema: OilEnergySignal
# ═══════════════════════════════════════════════════════════════════════════════

class OilEnergySignalORM(_FoundationMixin, Base):
    __tablename__ = "df_oil_energy_signals"

    signal_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    benchmark: Mapped[str | None] = mapped_column(String(64), nullable=True)
    country: Mapped[str | None] = mapped_column(String(4), nullable=True, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(4), default="USD", nullable=False)
    observation_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    fiscal_breakeven_price: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)
    confidence_method: Mapped[str] = mapped_column(String(64), default="SOURCE_DECLARED", nullable=False)


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_fx_signals
# Schema: FXSignal
# ═══════════════════════════════════════════════════════════════════════════════

class FXSignalORM(_FoundationMixin, Base):
    __tablename__ = "df_fx_signals"

    signal_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    base_currency: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    quote_currency: Mapped[str] = mapped_column(String(4), nullable=False)
    country: Mapped[str | None] = mapped_column(String(4), nullable=True)
    rate: Mapped[float] = mapped_column(Float, nullable=False)
    rate_type: Mapped[str] = mapped_column(String(32), default="SPOT", nullable=False)
    observation_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    peg_rate: Mapped[float | None] = mapped_column(Float, nullable=True)
    deviation_from_peg_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bid: Mapped[float | None] = mapped_column(Float, nullable=True)
    ask: Mapped[float | None] = mapped_column(Float, nullable=True)
    spread_bps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    daily_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    previous_close: Mapped[float | None] = mapped_column(Float, nullable=True)
    change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.90, nullable=False)
    confidence_method: Mapped[str] = mapped_column(String(64), default="SOURCE_DECLARED", nullable=False)


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_cbk_indicators
# Schema: CBKIndicatorRecord
# ═══════════════════════════════════════════════════════════════════════════════

class CBKIndicatorORM(_FoundationMixin, Base):
    __tablename__ = "df_cbk_indicators"

    indicator_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    indicator_code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    indicator_name: Mapped[str] = mapped_column(String(256), nullable=False)
    indicator_name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    unit: Mapped[str] = mapped_column(String(64), nullable=False)
    currency: Mapped[str] = mapped_column(String(4), default="KWD", nullable=False)
    period_start: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    period_end: Mapped[datetime] = mapped_column(Date, nullable=False)
    frequency: Mapped[str] = mapped_column(String(32), default="monthly", nullable=False)
    source_id: Mapped[str] = mapped_column(String(128), default="cbk-statistical-bulletin", nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.95, nullable=False)
    confidence_method: Mapped[str] = mapped_column(String(64), default="SOURCE_DECLARED", nullable=False)
    is_provisional: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    previous_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    yoy_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    mom_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    regulatory_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)
    breach_status: Mapped[str | None] = mapped_column(String(32), nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_banking_profiles
# Schema: BankingSectorProfile
# ═══════════════════════════════════════════════════════════════════════════════

class BankingProfileORM(_FoundationMixin, Base):
    __tablename__ = "df_banking_profiles"

    profile_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_name: Mapped[str] = mapped_column(String(256), nullable=False)
    country: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    reporting_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    reporting_period: Mapped[str] = mapped_column(String(16), nullable=False)
    currency: Mapped[str] = mapped_column(String(4), default="KWD", nullable=False)
    # Size metrics
    total_assets: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_deposits: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_loans: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Profitability
    net_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    roe_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    roa_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    cost_to_income_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    nim_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Asset quality
    npl_ratio_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    npl_coverage_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    loan_loss_provision: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Capital adequacy
    car_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    cet1_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    tier1_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    leverage_ratio_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Liquidity
    lcr_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    nsfr_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    loan_to_deposit_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Systemic
    is_dsib: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dsib_buffer_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Metadata
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.85, nullable=False)
    confidence_method: Mapped[str] = mapped_column(String(64), default="SOURCE_DECLARED", nullable=False)
    is_audited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    auditor: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_insurance_profiles
# Schema: InsuranceSectorProfile
# ═══════════════════════════════════════════════════════════════════════════════

class InsuranceProfileORM(_FoundationMixin, Base):
    __tablename__ = "df_insurance_profiles"

    profile_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_name: Mapped[str] = mapped_column(String(256), nullable=False)
    country: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    insurance_type: Mapped[str] = mapped_column(String(32), nullable=False)
    reporting_date: Mapped[datetime] = mapped_column(Date, nullable=False, index=True)
    reporting_period: Mapped[str] = mapped_column(String(16), nullable=False)
    currency: Mapped[str] = mapped_column(String(4), default="KWD", nullable=False)
    # Premium
    gwp: Mapped[float | None] = mapped_column(Float, nullable=True)
    nwp: Mapped[float | None] = mapped_column(Float, nullable=True)
    nep: Mapped[float | None] = mapped_column(Float, nullable=True)
    retention_ratio_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Claims
    net_claims_incurred: Mapped[float | None] = mapped_column(Float, nullable=True)
    loss_ratio_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    combined_ratio_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    expense_ratio_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    underwriting_result: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Investment
    investment_income: Mapped[float | None] = mapped_column(Float, nullable=True)
    investment_yield_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_investments: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Solvency
    total_assets: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_equity: Mapped[float | None] = mapped_column(Float, nullable=True)
    solvency_ratio_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    minimum_capital_required: Mapped[float | None] = mapped_column(Float, nullable=True)
    solvency_capital_required: Mapped[float | None] = mapped_column(Float, nullable=True)
    # IFRS 17
    ifrs17_adopted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    csm_balance: Mapped[float | None] = mapped_column(Float, nullable=True)
    risk_adjustment: Mapped[float | None] = mapped_column(Float, nullable=True)
    insurance_revenue: Mapped[float | None] = mapped_column(Float, nullable=True)
    # Rating
    am_best_rating: Mapped[str | None] = mapped_column(String(8), nullable=True)
    sp_rating: Mapped[str | None] = mapped_column(String(8), nullable=True)
    # Metadata
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.80, nullable=False)
    confidence_method: Mapped[str] = mapped_column(String(64), default="SOURCE_DECLARED", nullable=False)
    is_audited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_logistics_nodes
# Schema: LogisticsNode
# ═══════════════════════════════════════════════════════════════════════════════

class LogisticsNodeORM(_FoundationMixin, Base):
    __tablename__ = "df_logistics_nodes"

    node_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    node_name: Mapped[str] = mapped_column(String(256), nullable=False)
    node_name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    country: Mapped[str] = mapped_column(String(4), nullable=False, index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    transport_mode: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    port_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    geo_lat: Mapped[float] = mapped_column(Float, nullable=False)
    geo_lng: Mapped[float] = mapped_column(Float, nullable=False)
    # Capacity
    annual_capacity_teu: Mapped[int | None] = mapped_column(Integer, nullable=True)
    annual_throughput_teu: Mapped[int | None] = mapped_column(Integer, nullable=True)
    utilization_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    annual_cargo_tonnage: Mapped[float | None] = mapped_column(Float, nullable=True)
    vessel_calls_annual: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pax_annual: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Connectivity
    connected_node_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    chokepoint_dependency: Mapped[str | None] = mapped_column(String(64), nullable=True)
    hinterland_coverage: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    # Operational
    operational_status: Mapped[str] = mapped_column(String(32), default="OPERATIONAL", nullable=False)
    criticality_score: Mapped[float] = mapped_column(Float, default=0.5, nullable=False)
    last_disruption_date: Mapped[datetime | None] = mapped_column(Date, nullable=True)
    # Metadata
    operator: Mapped[str | None] = mapped_column(String(256), nullable=True)
    free_zone_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    source_id: Mapped[str] = mapped_column(String(128), nullable=False)
    confidence_score: Mapped[float] = mapped_column(Float, default=0.80, nullable=False)
    confidence_method: Mapped[str] = mapped_column(String(64), default="SOURCE_DECLARED", nullable=False)
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_decision_rules
# Schema: DecisionRule
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionRuleORM(_FoundationMixin, _AuditMixin, Base):
    __tablename__ = "df_decision_rules"

    rule_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    rule_name: Mapped[str] = mapped_column(String(256), nullable=False)
    rule_name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    # Conditions stored as JSONB (list of RuleCondition dicts)
    conditions: Mapped[dict] = mapped_column(JSONB, nullable=False)
    condition_logic: Mapped[str] = mapped_column(String(8), default="AND", nullable=False)
    # Action
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action_params: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    escalation_level: Mapped[str] = mapped_column(String(32), default="ELEVATED", nullable=False)
    # Scope
    applicable_countries: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    applicable_sectors: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    applicable_scenarios: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    # Governance
    requires_human_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cooldown_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    # Metadata
    source_dataset_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    tags: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    __table_args__ = (
        Index("ix_df_rule_active_action", "is_active", "action"),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Table: df_decision_logs
# Schema: DecisionLogEntry
# ═══════════════════════════════════════════════════════════════════════════════

class DecisionLogORM(_FoundationMixin, Base):
    __tablename__ = "df_decision_logs"

    log_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    rule_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    rule_version: Mapped[int] = mapped_column(Integer, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    action: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), default="PROPOSED", nullable=False, index=True)
    # Context
    trigger_context: Mapped[dict] = mapped_column(JSONB, nullable=False)  # TriggerContext dict
    country: Mapped[str | None] = mapped_column(String(4), nullable=True)
    entity_ids: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # List[str]
    # Human-in-the-loop
    requires_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reviewed_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Execution
    executed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    execution_result: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    # Supersession
    superseded_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    # Audit chain
    audit_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)
    previous_log_hash: Mapped[str | None] = mapped_column(String(128), nullable=True)

    __table_args__ = (
        Index("ix_df_dlog_rule_triggered", "rule_id", "triggered_at"),
        Index("ix_df_dlog_status_action", "status", "action"),
    )
