"""Canonical unified data model for all intelligence sources.

Every external source normalizes into these schemas before storage or processing.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class SourceType(StrEnum):
    CONFLICT = "conflict"
    AVIATION = "aviation"
    MARITIME = "maritime"
    GEOSPATIAL = "geospatial"
    MANUAL = "manual"


class SeverityLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EntityLayer(StrEnum):
    GEOGRAPHY = "geography"
    INFRASTRUCTURE = "infrastructure"
    ECONOMY = "economy"
    FINANCE = "finance"
    SOCIETY = "society"
    TRANSPORT = "transport"
    MILITARY = "military"


class DisruptionType(StrEnum):
    CLOSURE = "closure"
    REROUTE = "reroute"
    DELAY = "delay"
    CONGESTION = "congestion"
    BLOCKADE = "blockade"
    DAMAGE = "damage"
    ESCALATION = "escalation"


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Provenance(BaseModel):
    source_type: SourceType
    source_name: str
    source_id: str | None = None
    ingested_at: datetime = Field(default_factory=datetime.utcnow)
    raw_payload: dict[str, Any] | None = None


class ConfidenceMeta(BaseModel):
    score: float = Field(ge=0.0, le=1.0, description="0=no confidence, 1=full confidence")
    source_quality: float = Field(ge=0.0, le=1.0, default=0.5)
    corroboration_count: int = Field(ge=0, default=0)
    data_freshness: float = Field(ge=0.0, le=1.0, default=1.0)
    signal_agreement: float = Field(ge=0.0, le=1.0, default=0.5)


class CanonicalBase(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    provenance: Provenance
    confidence: ConfidenceMeta = Field(default_factory=lambda: ConfidenceMeta(score=0.5))
    tags: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Geospatial primitives
# ---------------------------------------------------------------------------

class GeoPoint(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    alt_m: float | None = None


class GeoZone(BaseModel):
    id: str
    name: str
    name_ar: str = ""
    boundary_geojson: dict[str, Any] | None = None
    center: GeoPoint | None = None


class Region(CanonicalBase):
    name: str
    name_ar: str = ""
    iso_code: str | None = None
    layer: EntityLayer = EntityLayer.GEOGRAPHY
    center: GeoPoint | None = None
    boundary_geojson: dict[str, Any] | None = None
    parent_region_id: str | None = None


class Country(Region):
    iso_alpha2: str = ""
    iso_alpha3: str = ""


# ---------------------------------------------------------------------------
# Infrastructure
# ---------------------------------------------------------------------------

class Airport(CanonicalBase):
    iata: str
    icao: str = ""
    name: str
    name_ar: str = ""
    location: GeoPoint
    country_id: str | None = None
    operational_criticality: float = Field(ge=0.0, le=1.0, default=0.5)
    passenger_throughput: float = 0.0
    cargo_throughput: float = 0.0


class Port(CanonicalBase):
    code: str
    name: str
    name_ar: str = ""
    location: GeoPoint
    country_id: str | None = None
    operational_criticality: float = Field(ge=0.0, le=1.0, default=0.5)
    vessel_capacity: int = 0
    daily_throughput_teu: float = 0.0


class Corridor(CanonicalBase):
    name: str
    name_ar: str = ""
    corridor_type: str = "maritime"  # maritime | air | land
    waypoints: list[GeoPoint] = Field(default_factory=list)
    chokepoint: bool = False
    resistance: float = Field(ge=0.0, le=1.0, default=0.1, description="Friction coefficient")
    capacity: float = 1.0


class Route(CanonicalBase):
    name: str
    route_type: str  # flight | shipping | land
    origin_id: str
    destination_id: str
    via_corridors: list[str] = Field(default_factory=list)
    distance_km: float = 0.0
    typical_duration_h: float = 0.0
    dependency_weight: float = Field(ge=0.0, le=1.0, default=0.5)


class Infrastructure(CanonicalBase):
    name: str
    name_ar: str = ""
    infra_type: str  # pipeline | refinery | power_plant | telecom | port_facility
    location: GeoPoint
    country_id: str | None = None
    operational_criticality: float = Field(ge=0.0, le=1.0, default=0.5)
    value_at_risk_usd: float = 0.0


# ---------------------------------------------------------------------------
# Events and incidents
# ---------------------------------------------------------------------------

class Event(CanonicalBase):
    title: str
    title_ar: str = ""
    description: str = ""
    description_ar: str = ""
    event_type: str  # conflict | political | natural | economic | security
    severity: SeverityLevel = SeverityLevel.MEDIUM
    severity_score: float = Field(ge=0.0, le=1.0, default=0.5)
    location: GeoPoint | None = None
    region_id: str | None = None
    affected_entity_ids: list[str] = Field(default_factory=list)
    start_time: datetime | None = None
    end_time: datetime | None = None
    active: bool = True


class Incident(Event):
    fatalities: int = 0
    actor_ids: list[str] = Field(default_factory=list)
    weapon_type: str | None = None


class Alert(CanonicalBase):
    title: str
    severity: SeverityLevel
    source_event_id: str | None = None
    affected_entity_ids: list[str] = Field(default_factory=list)
    message: str = ""
    expires_at: datetime | None = None


# ---------------------------------------------------------------------------
# Actors and organizations
# ---------------------------------------------------------------------------

class Actor(CanonicalBase):
    name: str
    name_ar: str = ""
    actor_type: str  # state | non_state | organization | individual
    affiliated_country_ids: list[str] = Field(default_factory=list)


class Organization(CanonicalBase):
    name: str
    name_ar: str = ""
    org_type: str  # government | military | airline | shipping_co | energy | financial
    country_id: str | None = None
    assets: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Transport entities
# ---------------------------------------------------------------------------

class Flight(CanonicalBase):
    flight_number: str
    operator_id: str | None = None
    origin_airport_id: str
    destination_airport_id: str
    departure_time: datetime | None = None
    arrival_time: datetime | None = None
    status: str = "scheduled"  # scheduled | departed | en_route | arrived | cancelled | diverted
    aircraft_type: str = ""
    route_id: str | None = None
    current_position: GeoPoint | None = None


class Vessel(CanonicalBase):
    mmsi: str = ""
    imo: str = ""
    name: str
    vessel_type: str  # tanker | cargo | container | bulk | passenger
    flag_country_id: str | None = None
    operator_id: str | None = None
    current_position: GeoPoint | None = None
    destination_port_id: str | None = None
    speed_knots: float = 0.0
    heading: float = 0.0
    route_id: str | None = None
    cargo_type: str = ""
    deadweight_tonnes: float = 0.0


# ---------------------------------------------------------------------------
# Scoring and assessment
# ---------------------------------------------------------------------------

class ScoreExplanation(BaseModel):
    factor: str
    weight: float
    contribution: float
    detail: str = ""


class RiskScore(CanonicalBase):
    entity_id: str
    entity_type: str
    score: float = Field(ge=0.0, le=1.0)
    severity: SeverityLevel = SeverityLevel.MEDIUM
    factors: list[ScoreExplanation] = Field(default_factory=list)
    valid_from: datetime = Field(default_factory=datetime.utcnow)
    valid_until: datetime | None = None


class DisruptionScore(CanonicalBase):
    entity_id: str
    entity_type: str
    score: float = Field(ge=0.0, le=1.0)
    disruption_type: DisruptionType = DisruptionType.DELAY
    reroute_cost: float = 0.0
    delay_hours: float = 0.0
    congestion_factor: float = 0.0
    factors: list[ScoreExplanation] = Field(default_factory=list)


class ImpactAssessment(CanonicalBase):
    scenario_id: str | None = None
    target_entity_id: str
    target_entity_type: str
    baseline_score: float = 0.0
    post_scenario_score: float = 0.0
    delta: float = 0.0
    economic_loss_usd: float = 0.0
    operational_impact: str = ""
    recommendations: list[str] = Field(default_factory=list)
    factors: list[ScoreExplanation] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Scenario
# ---------------------------------------------------------------------------

class ScenarioShock(BaseModel):
    target_entity_id: str
    shock_type: DisruptionType
    severity_score: float = Field(ge=0.0, le=1.0)
    description: str = ""


class Scenario(CanonicalBase):
    title: str
    title_ar: str = ""
    description: str = ""
    description_ar: str = ""
    scenario_type: str  # disruption | escalation | cascading | hypothetical
    shocks: list[ScenarioShock] = Field(default_factory=list)
    horizon_hours: float = 72.0
    baseline_snapshot_id: str | None = None
    status: str = "draft"  # draft | running | complete | archived


class ScenarioResult(CanonicalBase):
    scenario_id: str
    impacts: list[ImpactAssessment] = Field(default_factory=list)
    system_stress: float = 0.0
    total_economic_loss_usd: float = 0.0
    top_impacted_entities: list[str] = Field(default_factory=list)
    narrative: str = ""
    narrative_ar: str = ""
    recommendations: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Signal (raw normalized ingest record)
# ---------------------------------------------------------------------------

class Signal(CanonicalBase):
    source_type: SourceType
    signal_type: str  # event | movement | status_change | metric
    payload: dict[str, Any] = Field(default_factory=dict)
    entity_refs: list[str] = Field(default_factory=list)
    location: GeoPoint | None = None
    severity_score: float = Field(ge=0.0, le=1.0, default=0.0)
