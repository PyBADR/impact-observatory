"""Neo4j node type definitions as Python dataclasses."""

from dataclasses import dataclass, asdict, field
from typing import Optional
from datetime import datetime


@dataclass
class EventNode:
    """Represents an event in the GCC DIP graph."""

    id: str
    event_type: str
    severity: str
    lat: float
    lon: float
    description: str
    timestamp: str
    source_type: str
    confidence: float

    @classmethod
    def label(cls) -> str:
        """Get Neo4j node label."""
        return "Event"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return asdict(self)


@dataclass
class AirportNode:
    """Represents an airport in the GCC DIP graph."""

    id: str
    icao: str
    iata: str
    name: str
    lat: float
    lon: float
    country: str
    operational_status: str
    capacity: int

    @classmethod
    def label(cls) -> str:
        """Get Neo4j node label."""
        return "Airport"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return asdict(self)


@dataclass
class PortNode:
    """Represents a maritime port in the GCC DIP graph."""

    id: str
    unlocode: str
    name: str
    lat: float
    lon: float
    country: str
    port_type: str
    capacity: int

    @classmethod
    def label(cls) -> str:
        """Get Neo4j node label."""
        return "Port"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return asdict(self)


@dataclass
class CorridorNode:
    """Represents a trade corridor in the GCC DIP graph."""

    id: str
    name: str
    corridor_type: str
    risk_level: str

    @classmethod
    def label(cls) -> str:
        """Get Neo4j node label."""
        return "Corridor"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return asdict(self)


@dataclass
class RouteNode:
    """Represents a transportation route in the GCC DIP graph."""

    id: str
    name: str
    route_type: str
    origin_id: str
    destination_id: str
    distance_km: float
    status: str

    @classmethod
    def label(cls) -> str:
        """Get Neo4j node label."""
        return "Route"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return asdict(self)


@dataclass
class FlightNode:
    """Represents a commercial flight in the GCC DIP graph."""

    id: str
    flight_number: str
    operator: str
    departure_airport: str
    arrival_airport: str
    status: str
    departure_time: str

    @classmethod
    def label(cls) -> str:
        """Get Neo4j node label."""
        return "Flight"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return asdict(self)


@dataclass
class VesselNode:
    """Represents a maritime vessel in the GCC DIP graph."""

    id: str
    mmsi: str
    imo: str
    name: str
    vessel_type: str
    flag_state: str
    lat: float
    lon: float
    speed: float
    heading: float

    @classmethod
    def label(cls) -> str:
        """Get Neo4j node label."""
        return "Vessel"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return asdict(self)


@dataclass
class ActorNode:
    """Represents an actor (state, organization, individual) in the GCC DIP graph."""

    id: str
    name: str
    actor_type: str
    threat_level: str
    country: str

    @classmethod
    def label(cls) -> str:
        """Get Neo4j node label."""
        return "Actor"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return asdict(self)


@dataclass
class RegionNode:
    """Represents a geographical region in the GCC DIP graph."""

    id: str
    name: str
    name_ar: str
    country: str
    lat: float
    lon: float
    risk_baseline: float

    @classmethod
    def label(cls) -> str:
        """Get Neo4j node label."""
        return "Region"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return asdict(self)


@dataclass
class ScenarioNode:
    """Represents a decision scenario in the GCC DIP graph."""

    id: str
    name: str
    description: str
    status: str
    created_at: str

    @classmethod
    def label(cls) -> str:
        """Get Neo4j node label."""
        return "Scenario"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return asdict(self)


@dataclass
class OrganizationNode:
    """Represents an organization in the GCC DIP graph."""

    id: str
    name: str
    org_type: str
    country: str
    sector: str

    @classmethod
    def label(cls) -> str:
        """Get Neo4j node label."""
        return "Organization"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return asdict(self)
