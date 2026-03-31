"""Enumerations for GCC Decision Intelligence Platform."""

from enum import Enum


class EventType(str, Enum):
    """Types of events in the system."""

    WEATHER = "weather"
    GEOPOLITICAL = "geopolitical"
    ECONOMIC = "economic"
    SECURITY = "security"
    PANDEMIC = "pandemic"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"
    NATURAL_DISASTER = "natural_disaster"
    REGULATORY_CHANGE = "regulatory_change"
    PORT_CONGESTION = "port_congestion"
    AIRSPACE_CLOSURE = "airspace_closure"
    MARITIME_INCIDENT = "maritime_incident"
    FLIGHT_DISRUPTION = "flight_disruption"
    OTHER = "other"


class SeverityLevel(str, Enum):
    """Severity levels for events and incidents."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SourceType(str, Enum):
    """Types of data sources."""

    NEWS_FEED = "news_feed"
    SOCIAL_MEDIA = "social_media"
    GOVERNMENT_API = "government_api"
    COMMERCIAL_API = "commercial_api"
    SATELLITE = "satellite"
    ADS_B = "ads_b"
    AIS = "ais"
    SENSOR_NETWORK = "sensor_network"
    HUMAN_REPORT = "human_report"
    INTERNAL_SYSTEM = "internal_system"
    SIMULATION = "simulation"
    OTHER = "other"


class ConfidenceLevel(str, Enum):
    """Confidence levels for data and assessments."""

    VERIFIED = "verified"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNVERIFIED = "unverified"


class TransportMode(str, Enum):
    """Types of transport modes."""

    AIR = "air"
    SEA = "sea"
    LAND = "land"
    RAIL = "rail"
    PIPELINE = "pipeline"


class AssetType(str, Enum):
    """Types of infrastructure assets."""

    AIRPORT = "airport"
    PORT = "port"
    CORRIDOR = "corridor"
    BRIDGE = "bridge"
    POWER_PLANT = "power_plant"
    PIPELINE = "pipeline"
    RAIL_NETWORK = "rail_network"
    PORT_FACILITY = "port_facility"
    CUSTOMS_CHECKPOINT = "customs_checkpoint"
    WAREHOUSE = "warehouse"
    OTHER = "other"


class FlightStatus(str, Enum):
    """Statuses for flights."""

    SCHEDULED = "scheduled"
    ACTIVE = "active"
    DELAYED = "delayed"
    CANCELLED = "cancelled"
    DIVERTED = "diverted"
    LANDED = "landed"
    COMPLETED = "completed"


class VesselType(str, Enum):
    """Types of vessels."""

    CONTAINER_SHIP = "container_ship"
    BULK_CARRIER = "bulk_carrier"
    TANKER = "tanker"
    RO_RO = "ro_ro"
    GENERAL_CARGO = "general_cargo"
    REFRIGERATED_CARGO = "refrigerated_cargo"
    BREAKBULK = "breakbulk"
    FISHING_VESSEL = "fishing_vessel"
    PASSENGER = "passenger"
    CRUISE = "cruise"
    TUG = "tug"
    BARGE = "barge"
    OTHER = "other"


class ActorType(str, Enum):
    """Types of actors in the system."""

    GOVERNMENT = "government"
    ORGANIZATION = "organization"
    PERSON = "person"
    MOVEMENT = "movement"
    COALITION = "coalition"
    MILITIA = "militia"
    OTHER = "other"


class AlertStatus(str, Enum):
    """Statuses for alerts."""

    NEW = "new"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    MONITORING = "monitoring"


class RiskCategory(str, Enum):
    """Categories of risk."""

    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    REPUTATIONAL = "reputational"
    COMPLIANCE = "compliance"
    SUPPLY_CHAIN = "supply_chain"
    GEOPOLITICAL = "geopolitical"
    ENVIRONMENTAL = "environmental"
    SECURITY = "security"


class ScenarioStatus(str, Enum):
    """Statuses for scenarios."""

    DRAFT = "draft"
    ACTIVE = "active"
    COMPLETED = "completed"
    ARCHIVED = "archived"
    FAILED = "failed"


class EntityType(str, Enum):
    """Types of entities that can be affected."""

    FLIGHT = "flight"
    VESSEL = "vessel"
    AIRPORT = "airport"
    PORT = "port"
    CORRIDOR = "corridor"
    ROUTE = "route"
    INFRASTRUCTURE = "infrastructure"
    REGION = "region"
    COUNTRY = "country"
    ACTOR = "actor"
    ORGANIZATION = "organization"
