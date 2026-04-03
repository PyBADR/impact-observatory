"""SQLAlchemy ORM models — PostgreSQL + PostGIS tables.

These models define the relational storage layer for the GCC Decision
Intelligence Platform. All spatial fields use PostGIS geometry types.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
    Index,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.db.postgres import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid.uuid4())


# ---- Events ----

class EventRecord(Base):
    __tablename__ = "events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    severity_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    region_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False, default="manual")
    source_name: Mapped[str | None] = mapped_column(String(256), nullable=True)
    source_id: Mapped[str | None] = mapped_column(String(256), nullable=True)
    is_kinetic: Mapped[bool] = mapped_column(Boolean, default=False)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)

    __table_args__ = (
        Index("ix_events_severity", "severity_score"),
        Index("ix_events_created", "created_at"),
    )


# ---- Flights ----

class FlightRecord(Base):
    __tablename__ = "flights"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    flight_number: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="scheduled")
    origin_airport_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    destination_airport_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    altitude_ft: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_knots: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    airline: Mapped[str | None] = mapped_column(String(128), nullable=True)
    aircraft_type: Mapped[str | None] = mapped_column(String(32), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# ---- Vessels ----

class VesselRecord(Base):
    __tablename__ = "vessels"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    mmsi: Mapped[str] = mapped_column(String(16), nullable=False, unique=True, index=True)
    imo: Mapped[str | None] = mapped_column(String(16), nullable=True)
    vessel_type: Mapped[str] = mapped_column(String(32), nullable=False, default="cargo")
    flag_state: Mapped[str | None] = mapped_column(String(64), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    speed_knots: Mapped[float | None] = mapped_column(Float, nullable=True)
    heading: Mapped[float | None] = mapped_column(Float, nullable=True)
    destination_port_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    risk_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, onupdate=_utcnow)


# ---- Infrastructure ----

class InfrastructureRecord(Base):
    __tablename__ = "infrastructure"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    name_ar: Mapped[str | None] = mapped_column(String(256), nullable=True)
    infra_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    asset_class: Mapped[str] = mapped_column(String(32), nullable=False, default="infrastructure")
    layer: Mapped[str] = mapped_column(String(32), nullable=False, default="infrastructure")
    lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    country: Mapped[str | None] = mapped_column(String(64), nullable=True)
    region_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    capacity: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---- Risk Scores ----

class RiskScoreRecord(Base):
    __tablename__ = "risk_scores"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(32), nullable=False)
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)
    disruption_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    asset_class: Mapped[str | None] = mapped_column(String(32), nullable=True)
    dominant_factor: Mapped[str | None] = mapped_column(String(64), nullable=True)
    breakdown_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)

    __table_args__ = (
        Index("ix_risk_entity_time", "entity_id", "computed_at"),
    )


# ---- Scenario Runs ----

class ScenarioRunRecord(Base):
    __tablename__ = "scenario_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    template_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    severity_override: Mapped[float | None] = mapped_column(Float, nullable=True)
    system_stress: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_economic_loss_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    narrative: Mapped[str | None] = mapped_column(Text, nullable=True)
    recommendations_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    impacts_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    risk_vector_json: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    executed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---- Insurance Records ----

class InsuranceAssessmentRecord(Base):
    __tablename__ = "insurance_assessments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    assessment_type: Mapped[str] = mapped_column(String(32), nullable=False)
    exposure_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    surge_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    claims_uplift_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    classification: Mapped[str | None] = mapped_column(String(32), nullable=True)
    breakdown_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    computed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow)


# ---- Pipeline Runs (v1 API) ----

class RunRecord(Base):
    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_uuid)
    run_id: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    template_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    severity: Mapped[float] = mapped_column(Float, nullable=False, default=0.5)
    horizon_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=336)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="completed", index=True)
    headline_loss_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    peak_day: Mapped[int | None] = mapped_column(Integer, nullable=True)
    severity_code: Mapped[str | None] = mapped_column(String(32), nullable=True)
    result_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_utcnow, index=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_ms: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (
        Index("ix_runs_created_desc", "created_at"),
    )
