"""Schema models for the GCC Decision Intelligence Platform.

This package contains Pydantic v2 models for all entities in the system.
"""

# Enumerations
from .enums import (
    ActorType,
    AlertStatus,
    AssetType,
    ConfidenceLevel,
    EntityType,
    EventType,
    FlightStatus,
    RiskCategory,
    ScenarioStatus,
    SeverityLevel,
    SourceType,
    TransportMode,
    VesselType,
)

# Base models
from .base import BaseEntity, SourceMetadata

# Geospatial models
from .geo import City, Country, GeoPoint, GeoZone, Region

# Event models
from .events import Alert, Event, Incident, Signal, SourceRecord

# Infrastructure models
from .infrastructure import Airport, Asset, Corridor, Infrastructure, Port, Route

# Transport models
from .transport import Flight, Operator, Vessel

# Actor models
from .actors import Actor, Organization, Policy

# Intelligence models
from .intelligence import ImpactAssessment, RiskScore, Scenario, ScenarioResult

__all__ = [
    # Enumerations
    "ActorType",
    "AlertStatus",
    "AssetType",
    "ConfidenceLevel",
    "EntityType",
    "EventType",
    "FlightStatus",
    "RiskCategory",
    "ScenarioStatus",
    "SeverityLevel",
    "SourceType",
    "TransportMode",
    "VesselType",
    # Base models
    "BaseEntity",
    "SourceMetadata",
    # Geospatial models
    "City",
    "Country",
    "GeoPoint",
    "GeoZone",
    "Region",
    # Event models
    "Alert",
    "Event",
    "Incident",
    "Signal",
    "SourceRecord",
    # Infrastructure models
    "Airport",
    "Asset",
    "Corridor",
    "Infrastructure",
    "Port",
    "Route",
    # Transport models
    "Flight",
    "Operator",
    "Vessel",
    # Actor models
    "Actor",
    "Organization",
    "Policy",
    # Intelligence models
    "ImpactAssessment",
    "RiskScore",
    "Scenario",
    "ScenarioResult",
]
