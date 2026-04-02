"""Neo4j graph schema — node labels, relationship types, constraints, and indexes.

Implements the full GCC Decision Intelligence graph model with all mandatory
relationships from the platform specification.
"""

from __future__ import annotations

from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Node labels
# ---------------------------------------------------------------------------

NODE_LABELS = [
    "Event",
    "Region",
    "Country",
    "City",
    "Airport",
    "Port",
    "Corridor",
    "Route",
    "Flight",
    "Vessel",
    "Actor",
    "Operator",
    "Organization",
    "Infrastructure",
    "Scenario",
    "ImpactAssessment",
    "RiskScore",
    "GeoZone",
    "Signal",
    "Policy",
]

# ---------------------------------------------------------------------------
# Relationship types
# ---------------------------------------------------------------------------

RELATIONSHIP_TYPES = [
    # Event relationships
    "OCCURRED_IN",       # (Event)-[:OCCURRED_IN]->(Region)
    "LOCATED_AT",        # (Event)-[:LOCATED_AT]->(GeoPoint)
    "INVOLVES",          # (Event)-[:INVOLVES]->(Actor)
    "AFFECTS",           # (Event)-[:AFFECTS]->(Infrastructure)
    "DISRUPTS",          # (Event)-[:DISRUPTS]->(Route)
    "ELEVATES_RISK_FOR", # (Event)-[:ELEVATES_RISK_FOR]->(Airport|Port|Corridor)

    # Flight relationships
    "DEPARTS_FROM",      # (Flight)-[:DEPARTS_FROM]->(Airport)
    "ARRIVES_AT",        # (Flight)-[:ARRIVES_AT]->(Airport)
    "OPERATED_BY",       # (Flight|Vessel)-[:OPERATED_BY]->(Operator)
    "FOLLOWS",           # (Flight)-[:FOLLOWS]->(Route)

    # Vessel relationships
    "CALLS_AT",          # (Vessel)-[:CALLS_AT]->(Port)
    "TRAVELS_IN",        # (Vessel)-[:TRAVELS_IN]->(Corridor)

    # Route relationships
    "CONNECTS",          # (Route)-[:CONNECTS]->(Airport|Port)
    "PASSES_THROUGH",    # (Route)-[:PASSES_THROUGH]->(Corridor)

    # Region relationships
    "ADJACENT_TO",       # (Region)-[:ADJACENT_TO]->(Region)
    "CONTAINS",          # (Region)-[:CONTAINS]->(Airport|Port|Infrastructure)

    # Actor relationships
    "CONNECTED_TO",      # (Actor)-[:CONNECTED_TO]->(Actor)
    "CONTROLS",          # (Actor)-[:CONTROLS]->(Infrastructure)

    # Scenario relationships
    "SIMULATES",         # (Scenario)-[:SIMULATES]->(Event)
    "TARGETS",           # (Scenario)-[:TARGETS]->(Region)

    # Impact assessment
    "FOR",               # (ImpactAssessment)-[:FOR]->(Region|Airport|Port|Corridor|Operator)

    # Risk linkage
    "HAS_RISK_SCORE",   # (any)-[:HAS_RISK_SCORE]->(RiskScore)
]


# ---------------------------------------------------------------------------
# Constraint & index DDL
# ---------------------------------------------------------------------------

CONSTRAINTS: list[str] = [
    "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (e:Event) REQUIRE e.id IS UNIQUE",
    "CREATE CONSTRAINT region_id IF NOT EXISTS FOR (r:Region) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT airport_id IF NOT EXISTS FOR (a:Airport) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT port_id IF NOT EXISTS FOR (p:Port) REQUIRE p.id IS UNIQUE",
    "CREATE CONSTRAINT corridor_id IF NOT EXISTS FOR (c:Corridor) REQUIRE c.id IS UNIQUE",
    "CREATE CONSTRAINT route_id IF NOT EXISTS FOR (r:Route) REQUIRE r.id IS UNIQUE",
    "CREATE CONSTRAINT flight_id IF NOT EXISTS FOR (f:Flight) REQUIRE f.id IS UNIQUE",
    "CREATE CONSTRAINT vessel_id IF NOT EXISTS FOR (v:Vessel) REQUIRE v.id IS UNIQUE",
    "CREATE CONSTRAINT actor_id IF NOT EXISTS FOR (a:Actor) REQUIRE a.id IS UNIQUE",
    "CREATE CONSTRAINT operator_id IF NOT EXISTS FOR (o:Operator) REQUIRE o.id IS UNIQUE",
    "CREATE CONSTRAINT infra_id IF NOT EXISTS FOR (i:Infrastructure) REQUIRE i.id IS UNIQUE",
    "CREATE CONSTRAINT scenario_id IF NOT EXISTS FOR (s:Scenario) REQUIRE s.id IS UNIQUE",
    "CREATE CONSTRAINT impact_id IF NOT EXISTS FOR (ia:ImpactAssessment) REQUIRE ia.id IS UNIQUE",
    "CREATE CONSTRAINT risk_id IF NOT EXISTS FOR (rs:RiskScore) REQUIRE rs.id IS UNIQUE",
    "CREATE CONSTRAINT organization_id IF NOT EXISTS FOR (o:Organization) REQUIRE o.id IS UNIQUE",
    "CREATE CONSTRAINT signal_id IF NOT EXISTS FOR (s:Signal) REQUIRE s.id IS UNIQUE",
]

INDEXES: list[str] = [
    "CREATE INDEX event_type_idx IF NOT EXISTS FOR (e:Event) ON (e.event_type)",
    "CREATE INDEX event_severity_idx IF NOT EXISTS FOR (e:Event) ON (e.severity_score)",
    "CREATE INDEX region_name_idx IF NOT EXISTS FOR (r:Region) ON (r.name)",
    "CREATE INDEX airport_iata_idx IF NOT EXISTS FOR (a:Airport) ON (a.iata)",
    "CREATE INDEX port_name_idx IF NOT EXISTS FOR (p:Port) ON (p.name)",
    "CREATE INDEX flight_number_idx IF NOT EXISTS FOR (f:Flight) ON (f.flight_number)",
    "CREATE INDEX vessel_mmsi_idx IF NOT EXISTS FOR (v:Vessel) ON (v.mmsi)",
    "CREATE INDEX corridor_type_idx IF NOT EXISTS FOR (c:Corridor) ON (c.corridor_type)",
    "CREATE INDEX risk_entity_idx IF NOT EXISTS FOR (rs:RiskScore) ON (rs.entity_id)",
]


async def apply_schema(session) -> dict[str, int]:
    """Apply all constraints and indexes to Neo4j.

    Args:
        session: An active Neo4j AsyncSession.

    Returns:
        Count of constraints and indexes applied.
    """
    applied_constraints = 0
    applied_indexes = 0

    for cypher in CONSTRAINTS:
        await session.run(cypher)
        applied_constraints += 1

    for cypher in INDEXES:
        await session.run(cypher)
        applied_indexes += 1

    return {
        "constraints_applied": applied_constraints,
        "indexes_applied": applied_indexes,
    }
