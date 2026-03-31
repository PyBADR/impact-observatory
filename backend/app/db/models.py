"""
SQLAlchemy ORM models for DecisionCore Intelligence Platform.
Uses SQLAlchemy 2.0 style with async support and PostGIS geometry.
"""

from datetime import datetime
from typing import Optional
from uuid import uuid4
import json

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Boolean,
    DateTime,
    Text,
    JSON,
    ARRAY,
    ForeignKey,
    Index,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import declarative_base, mapped_column, relationship, Mapped
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM
from geoalchemy2 import Geometry

Base = declarative_base()


class Event(Base):
    """
    Event data from conflict and crisis monitoring sources.
    Includes geospatial data via PostGIS.
    """

    __tablename__ = "events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    event_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    event_type: Mapped[str] = mapped_column(String(100), index=True)
    location: Mapped[Optional[str]] = mapped_column(Geometry("POINT", srid=4326))
    location_name: Mapped[str] = mapped_column(String(500))
    country: Mapped[str] = mapped_column(String(100), index=True)
    admin1: Mapped[Optional[str]] = mapped_column(String(100))
    admin2: Mapped[Optional[str]] = mapped_column(String(100))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    fatalities: Mapped[int] = mapped_column(Integer, default=0)
    wounded: Mapped[int] = mapped_column(Integer, default=0)
    description: Mapped[str] = mapped_column(Text)
    source_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_events_event_date_country", "event_date", "country"),
        Index("ix_events_location", "location", postgresql_using="gist"),
        Index("ix_events_source", "source_id", "source_type"),
    )


class Incident(Base):
    """
    Incident aggregating related events.
    """

    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    incident_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    incident_type: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    start_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(50), default="ongoing")
    countries: Mapped[list] = mapped_column(ARRAY(String), default=list)
    actors_involved: Mapped[list] = mapped_column(ARRAY(String), default=list)
    event_count: Mapped[int] = mapped_column(Integer, default=0)
    total_fatalities: Mapped[int] = mapped_column(Integer, default=0)
    total_wounded: Mapped[int] = mapped_column(Integer, default=0)
    severity: Mapped[str] = mapped_column(String(50), default="medium")
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_incidents_type_status", "incident_type", "status"),
        Index("ix_incidents_dates", "start_date", "end_date"),
    )


class Alert(Base):
    """
    Real-time alerts triggered by signals or threshold breaches.
    """

    __tablename__ = "alerts"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    alert_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    alert_type: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text)
    severity: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(50), default="active")
    triggered_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    related_signals: Mapped[list] = mapped_column(ARRAY(String), default=list)
    geographic_scope: Mapped[list] = mapped_column(ARRAY(String), default=list)
    affected_actors: Mapped[list] = mapped_column(ARRAY(String), default=list)
    alert_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100), index=True)
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_alerts_severity_status", "severity", "status"),
        Index("ix_alerts_triggered_at", "triggered_at"),
    )


class Airport(Base):
    """
    Airport infrastructure and operational data.
    """

    __tablename__ = "airports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    icao: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    iata: Mapped[Optional[str]] = mapped_column(String(5))
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(100), index=True)
    location: Mapped[Optional[str]] = mapped_column(Geometry("POINT", srid=4326))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    elevation: Mapped[Optional[int]] = mapped_column(Integer)
    operating_status: Mapped[str] = mapped_column(String(50), default="open")
    last_status_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    infrastructure: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_airports_location", "location", postgresql_using="gist"),
        Index("ix_airports_country", "country"),
    )


class Port(Base):
    """
    Port infrastructure and maritime operational data.
    """

    __tablename__ = "ports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    port_code: Mapped[str] = mapped_column(String(10), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    country: Mapped[str] = mapped_column(String(100), index=True)
    location: Mapped[Optional[str]] = mapped_column(Geometry("POINT", srid=4326))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    port_type: Mapped[str] = mapped_column(String(50))
    operating_status: Mapped[str] = mapped_column(String(50), default="open")
    last_status_update: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    cargo_capacity: Mapped[Optional[float]] = mapped_column(Float)
    infrastructure: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_ports_location", "location", postgresql_using="gist"),
        Index("ix_ports_country", "country"),
    )


class Corridor(Base):
    """
    Geographic corridors connecting regions for trade and movement analysis.
    """

    __tablename__ = "corridors"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    corridor_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    corridor_type: Mapped[str] = mapped_column(String(50))
    start_location: Mapped[str] = mapped_column(String(255))
    end_location: Mapped[str] = mapped_column(String(255))
    countries: Mapped[list] = mapped_column(ARRAY(String), default=list)
    significance: Mapped[str] = mapped_column(String(50), default="medium")
    risk_level: Mapped[str] = mapped_column(String(50), default="low")
    corridor_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_corridors_type", "corridor_type"),
        Index("ix_corridors_risk_level", "risk_level"),
    )


class Route(Base):
    """
    Specific transport routes (air, maritime, land).
    """

    __tablename__ = "routes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    route_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    route_type: Mapped[str] = mapped_column(String(50), index=True)
    origin: Mapped[str] = mapped_column(String(255))
    destination: Mapped[str] = mapped_column(String(255))
    distance_km: Mapped[Optional[float]] = mapped_column(Float)
    typical_duration_hours: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="active")
    risk_level: Mapped[str] = mapped_column(String(50), default="low")
    route_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_routes_type_status", "route_type", "status"),
        Index("ix_routes_risk_level", "risk_level"),
    )


class Flight(Base):
    """
    Flight tracking and operational data.
    """

    __tablename__ = "flights"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    flight_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    aircraft_type: Mapped[str] = mapped_column(String(50))
    origin_airport: Mapped[str] = mapped_column(String(10), index=True)
    destination_airport: Mapped[str] = mapped_column(String(10), index=True)
    departure_time: Mapped[datetime] = mapped_column(DateTime, index=True)
    arrival_time: Mapped[Optional[datetime]] = mapped_column(DateTime)
    current_location: Mapped[Optional[str]] = mapped_column(Geometry("POINT", srid=4326))
    altitude: Mapped[Optional[float]] = mapped_column(Float)
    speed: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="scheduled")
    passengers: Mapped[int] = mapped_column(Integer, default=0)
    flight_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_flights_airports", "origin_airport", "destination_airport"),
        Index("ix_flights_departure_time", "departure_time"),
        Index("ix_flights_status", "status"),
    )


class Vessel(Base):
    """
    Maritime vessel tracking and operational data.
    """

    __tablename__ = "vessels"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    mmsi: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    imo: Mapped[Optional[str]] = mapped_column(String(20))
    call_sign: Mapped[Optional[str]] = mapped_column(String(20))
    name: Mapped[str] = mapped_column(String(255))
    vessel_type: Mapped[str] = mapped_column(String(50))
    flag: Mapped[Optional[str]] = mapped_column(String(100))
    length: Mapped[Optional[float]] = mapped_column(Float)
    width: Mapped[Optional[float]] = mapped_column(Float)
    gross_tonnage: Mapped[Optional[float]] = mapped_column(Float)
    current_location: Mapped[Optional[str]] = mapped_column(Geometry("POINT", srid=4326))
    last_port: Mapped[Optional[str]] = mapped_column(String(255))
    destination_port: Mapped[Optional[str]] = mapped_column(String(255))
    speed: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="underway")
    vessel_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_vessels_type_status", "vessel_type", "status"),
        Index("ix_vessels_location", "current_location", postgresql_using="gist"),
    )


class Actor(Base):
    """
    Individual or organizational actors in conflict/crisis events.
    """

    __tablename__ = "actors"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    actor_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    actor_type: Mapped[str] = mapped_column(String(50), index=True)
    country: Mapped[Optional[str]] = mapped_column(String(100))
    organization_id: Mapped[Optional[str]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id")
    )
    aliases: Mapped[list] = mapped_column(ARRAY(String), default=list)
    description: Mapped[str] = mapped_column(Text, default="")
    risk_profile: Mapped[dict] = mapped_column(JSONB, default=dict)
    relationships: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_actors_type", "actor_type"),
        Index("ix_actors_country", "country"),
    )


class Organization(Base):
    """
    Organization entities and their attributes.
    """

    __tablename__ = "organizations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    org_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    org_type: Mapped[str] = mapped_column(String(50), index=True)
    country: Mapped[Optional[str]] = mapped_column(String(100))
    sector: Mapped[Optional[str]] = mapped_column(String(100))
    headquarters: Mapped[Optional[str]] = mapped_column(String(255))
    founded_year: Mapped[Optional[int]] = mapped_column(Integer)
    description: Mapped[str] = mapped_column(Text, default="")
    org_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_organizations_type", "org_type"),
        Index("ix_organizations_country", "country"),
    )


class Scenario(Base):
    """
    Crisis or conflict scenarios for analysis and projection.
    """

    __tablename__ = "scenarios"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    scenario_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    scenario_type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)
    geographic_scope: Mapped[list] = mapped_column(ARRAY(String), default=list)
    temporal_scope: Mapped[dict] = mapped_column(JSONB, default=dict)
    actors: Mapped[list] = mapped_column(ARRAY(String), default=list)
    assumptions: Mapped[dict] = mapped_column(JSONB, default=dict)
    outcomes: Mapped[dict] = mapped_column(JSONB, default=dict)
    probability: Mapped[float] = mapped_column(Float, default=0.5)
    impact_assessment: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_scenarios_type", "scenario_type"),
    )


class RiskScore(Base):
    """
    Risk scoring and assessment data.
    """

    __tablename__ = "risk_scores"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    entity_id: Mapped[str] = mapped_column(String(255), index=True)
    entity_type: Mapped[str] = mapped_column(String(50), index=True)
    risk_category: Mapped[str] = mapped_column(String(100), index=True)
    score: Mapped[float] = mapped_column(Float)
    score_range: Mapped[str] = mapped_column(String(50))
    factors: Mapped[dict] = mapped_column(JSONB, default=dict)
    assessment_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    assessment_method: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_risk_scores_entity", "entity_id", "entity_type"),
        Index("ix_risk_scores_category", "risk_category"),
        Index("ix_risk_scores_assessment_date", "assessment_date"),
    )


class ImpactAssessment(Base):
    """
    Impact assessment and consequence analysis.
    """

    __tablename__ = "impact_assessments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    assessment_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    impact_type: Mapped[str] = mapped_column(String(100), index=True)
    affected_entities: Mapped[list] = mapped_column(ARRAY(String), default=list)
    geographic_scope: Mapped[list] = mapped_column(ARRAY(String), default=list)
    severity: Mapped[str] = mapped_column(String(50))
    affected_population: Mapped[int] = mapped_column(Integer, default=0)
    economic_impact: Mapped[Optional[float]] = mapped_column(Float)
    humanitarian_impact: Mapped[dict] = mapped_column(JSONB, default=dict)
    infrastructure_impact: Mapped[dict] = mapped_column(JSONB, default=dict)
    assessment_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    assessment_method: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_impact_assessments_type", "impact_type"),
        Index("ix_impact_assessments_severity", "severity"),
    )


class Signal(Base):
    """
    Early warning signals and indicators.
    """

    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    signal_code: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    signal_type: Mapped[str] = mapped_column(String(100), index=True)
    indicator: Mapped[str] = mapped_column(String(255))
    value: Mapped[float] = mapped_column(Float)
    threshold: Mapped[Optional[float]] = mapped_column(Float)
    status: Mapped[str] = mapped_column(String(50), default="normal")
    geographic_scope: Mapped[list] = mapped_column(ARRAY(String), default=list)
    signal_date: Mapped[datetime] = mapped_column(DateTime, index=True)
    interpretation: Mapped[str] = mapped_column(Text, default="")
    signal_data: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_id: Mapped[str] = mapped_column(String(100))
    source_type: Mapped[str] = mapped_column(String(50))
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    tags: Mapped[list] = mapped_column(ARRAY(String), default=list)
    provenance: Mapped[dict] = mapped_column(JSONB, default=dict)

    __table_args__ = (
        Index("ix_signals_type_status", "signal_type", "status"),
        Index("ix_signals_signal_date", "signal_date"),
    )


class SourceRecord(Base):
    """
    Source system and data ingestion metadata.
    """

    __tablename__ = "source_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_code: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    source_name: Mapped[str] = mapped_column(String(255))
    source_type: Mapped[str] = mapped_column(String(50))
    source_url: Mapped[Optional[str]] = mapped_column(String(500))
    description: Mapped[str] = mapped_column(Text, default="")
    api_status: Mapped[str] = mapped_column(String(50), default="unknown")
    last_sync: Mapped[Optional[datetime]] = mapped_column(DateTime)
    next_sync: Mapped[Optional[datetime]] = mapped_column(DateTime)
    records_ingested: Mapped[int] = mapped_column(Integer, default=0)
    records_failed: Mapped[int] = mapped_column(Integer, default=0)
    source_metadata: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    __table_args__ = (
        Index("ix_source_records_type", "source_type"),
        Index("ix_source_records_api_status", "api_status"),
    )
