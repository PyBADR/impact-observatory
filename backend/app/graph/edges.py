"""Neo4j relationship type definitions as Python dataclasses."""

from dataclasses import dataclass, asdict
from typing import Optional, Literal


@dataclass
class OccurredInEdge:
    """OCCURRED_IN relationship: Event occurred in Region."""

    event_id: str
    region_id: str
    timestamp: str

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "OCCURRED_IN"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {"timestamp": self.timestamp}

    def to_merge_cypher(
        self, src_label: str = "Event", src_key: str = "id",
        dst_label: str = "Region", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props_str = ", ".join(
            f"{k}: ${k}" for k in self.to_cypher_properties().keys()
        )
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(dst)"
        )


@dataclass
class LocatedAtEdge:
    """LOCATED_AT relationship: Entity is located at coordinates."""

    entity_id: str
    lat: float
    lon: float

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "LOCATED_AT"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {"lat": self.lat, "lon": self.lon}

    def to_merge_cypher(
        self, src_label: str = "Entity", src_key: str = "id",
        dst_label: str = "Location", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props = self.to_cypher_properties()
        props_str = ", ".join(f"{k}: ${k}" for k in props.keys())
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(:Location {{lat: ${lat}, lon: ${lon}}})"
        )


@dataclass
class InvolvesEdge:
    """INVOLVES relationship: Event involves an Actor."""

    event_id: str
    actor_id: str
    role: str

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "INVOLVES"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {"role": self.role}

    def to_merge_cypher(
        self, src_label: str = "Event", src_key: str = "id",
        dst_label: str = "Actor", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props_str = ", ".join(
            f"{k}: ${k}" for k in self.to_cypher_properties().keys()
        )
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(dst)"
        )


@dataclass
class AffectsEdge:
    """AFFECTS relationship: Event affects infrastructure."""

    event_id: str
    infrastructure_id: str
    impact_score: float

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "AFFECTS"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {"impact_score": self.impact_score}

    def to_merge_cypher(
        self, src_label: str = "Event", src_key: str = "id",
        dst_label: str = "Infrastructure", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props_str = ", ".join(
            f"{k}: ${k}" for k in self.to_cypher_properties().keys()
        )
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(dst)"
        )


@dataclass
class DisruptsEdge:
    """DISRUPTS relationship: Event disrupts a route."""

    event_id: str
    route_id: str
    severity: str
    estimated_duration_hours: float

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "DISRUPTS"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {
            "severity": self.severity,
            "estimated_duration_hours": self.estimated_duration_hours,
        }

    def to_merge_cypher(
        self, src_label: str = "Event", src_key: str = "id",
        dst_label: str = "Route", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props = self.to_cypher_properties()
        props_str = ", ".join(f"{k}: ${k}" for k in props.keys())
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(dst)"
        )


@dataclass
class ElevatesRiskForEdge:
    """ELEVATES_RISK_FOR relationship: Event elevates risk for a target."""

    event_id: str
    target_id: str
    risk_delta: float

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "ELEVATES_RISK_FOR"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {"risk_delta": self.risk_delta}

    def to_merge_cypher(
        self, src_label: str = "Event", src_key: str = "id",
        dst_label: str = "Target", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props_str = ", ".join(
            f"{k}: ${k}" for k in self.to_cypher_properties().keys()
        )
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(dst)"
        )


@dataclass
class DeparstsFromEdge:
    """DEPARTS_FROM relationship: Flight departs from airport."""

    flight_id: str
    airport_id: str

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "DEPARTS_FROM"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {}

    def to_merge_cypher(
        self, src_label: str = "Flight", src_key: str = "id",
        dst_label: str = "Airport", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}]->(dst)"
        )


@dataclass
class ArrivesAtEdge:
    """ARRIVES_AT relationship: Flight arrives at airport."""

    flight_id: str
    airport_id: str

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "ARRIVES_AT"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {}

    def to_merge_cypher(
        self, src_label: str = "Flight", src_key: str = "id",
        dst_label: str = "Airport", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}]->(dst)"
        )


@dataclass
class OperatedByEdge:
    """OPERATED_BY relationship: Entity is operated by organization."""

    entity_id: str
    operator_id: str

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "OPERATED_BY"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {}

    def to_merge_cypher(
        self, src_label: str = "Entity", src_key: str = "id",
        dst_label: str = "Organization", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}]->(dst)"
        )


@dataclass
class CallsAtEdge:
    """CALLS_AT relationship: Vessel calls at port."""

    vessel_id: str
    port_id: str
    eta: str

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "CALLS_AT"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {"eta": self.eta}

    def to_merge_cypher(
        self, src_label: str = "Vessel", src_key: str = "id",
        dst_label: str = "Port", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props_str = ", ".join(
            f"{k}: ${k}" for k in self.to_cypher_properties().keys()
        )
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(dst)"
        )


@dataclass
class TravelsInEdge:
    """TRAVELS_IN relationship: Vessel travels in corridor."""

    vessel_id: str
    corridor_id: str

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "TRAVELS_IN"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {}

    def to_merge_cypher(
        self, src_label: str = "Vessel", src_key: str = "id",
        dst_label: str = "Corridor", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}]->(dst)"
        )


@dataclass
class ConnectsEdge:
    """CONNECTS relationship: Route connects regions/airports."""

    route_id: str
    endpoint_id: str
    direction: str

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "CONNECTS"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {"direction": self.direction}

    def to_merge_cypher(
        self, src_label: str = "Route", src_key: str = "id",
        dst_label: str = "Endpoint", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props_str = ", ".join(
            f"{k}: ${k}" for k in self.to_cypher_properties().keys()
        )
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(dst)"
        )


@dataclass
class AdjacentToEdge:
    """ADJACENT_TO relationship: Region adjacent to another region."""

    region_id_a: str
    region_id_b: str
    border_type: str

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "ADJACENT_TO"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {"border_type": self.border_type}

    def to_merge_cypher(
        self, src_label: str = "Region", src_key: str = "id",
        dst_label: str = "Region", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props_str = ", ".join(
            f"{k}: ${k}" for k in self.to_cypher_properties().keys()
        )
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: $region_id_a}}), "
            f"(dst:{dst_label} {{{dst_key}: $region_id_b}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(dst)"
        )


@dataclass
class ConnectedToEdge:
    """CONNECTED_TO relationship: Actor connected to another actor."""

    actor_id_a: str
    actor_id_b: str
    connection_type: str

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "CONNECTED_TO"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {"connection_type": self.connection_type}

    def to_merge_cypher(
        self, src_label: str = "Actor", src_key: str = "id",
        dst_label: str = "Actor", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props_str = ", ".join(
            f"{k}: ${k}" for k in self.to_cypher_properties().keys()
        )
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: $actor_id_a}}), "
            f"(dst:{dst_label} {{{dst_key}: $actor_id_b}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(dst)"
        )


@dataclass
class SimulatesEdge:
    """SIMULATES relationship: Scenario simulates target entity."""

    scenario_id: str
    target_id: str
    target_type: str

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "SIMULATES"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {"target_type": self.target_type}

    def to_merge_cypher(
        self, src_label: str = "Scenario", src_key: str = "id",
        dst_label: str = "Target", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props_str = ", ".join(
            f"{k}: ${k}" for k in self.to_cypher_properties().keys()
        )
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(dst)"
        )


@dataclass
class ImpactOnEdge:
    """IMPACT_ON relationship: Assessment has impact on target."""

    assessment_id: str
    target_id: str
    score: float

    @staticmethod
    def rel_type() -> str:
        """Get Neo4j relationship type."""
        return "IMPACT_ON"

    def to_cypher_properties(self) -> dict:
        """Convert to Neo4j property dictionary."""
        return {"score": self.score}

    def to_merge_cypher(
        self, src_label: str = "Assessment", src_key: str = "id",
        dst_label: str = "Target", dst_key: str = "id"
    ) -> str:
        """Generate MERGE Cypher for relationship."""
        rel_type = self.rel_type()
        props_str = ", ".join(
            f"{k}: ${k}" for k in self.to_cypher_properties().keys()
        )
        if props_str:
            props_str = f" {{{props_str}}}"
        return (
            f"MATCH (src:{src_label} {{{src_key}: ${src_key}}}), "
            f"(dst:{dst_label} {{{dst_key}: ${dst_key}}}) "
            f"MERGE (src)-[:{rel_type}{props_str}]->(dst)"
        )
