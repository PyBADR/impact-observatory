"""Neo4j graph schema — constraints and indexes for the intelligence graph.

Run once during database initialization.
"""

from src.db.neo4j import get_neo4j_session

CONSTRAINTS = [
    "CREATE CONSTRAINT event_id IF NOT EXISTS FOR (n:Event) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT region_id IF NOT EXISTS FOR (n:Region) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT airport_id IF NOT EXISTS FOR (n:Airport) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT port_id IF NOT EXISTS FOR (n:Port) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT corridor_id IF NOT EXISTS FOR (n:Corridor) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT route_id IF NOT EXISTS FOR (n:Route) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT flight_id IF NOT EXISTS FOR (n:Flight) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT vessel_id IF NOT EXISTS FOR (n:Vessel) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT actor_id IF NOT EXISTS FOR (n:Actor) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT operator_id IF NOT EXISTS FOR (n:Operator) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT infra_id IF NOT EXISTS FOR (n:Infrastructure) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT scenario_id IF NOT EXISTS FOR (n:Scenario) REQUIRE n.id IS UNIQUE",
    "CREATE CONSTRAINT impact_id IF NOT EXISTS FOR (n:ImpactAssessment) REQUIRE n.id IS UNIQUE",
]

INDEXES = [
    "CREATE INDEX event_type_idx IF NOT EXISTS FOR (n:Event) ON (n.event_type)",
    "CREATE INDEX event_severity_idx IF NOT EXISTS FOR (n:Event) ON (n.severity_score)",
    "CREATE INDEX airport_iata_idx IF NOT EXISTS FOR (n:Airport) ON (n.iata)",
    "CREATE INDEX port_code_idx IF NOT EXISTS FOR (n:Port) ON (n.code)",
    "CREATE INDEX vessel_mmsi_idx IF NOT EXISTS FOR (n:Vessel) ON (n.mmsi)",
    "CREATE INDEX flight_number_idx IF NOT EXISTS FOR (n:Flight) ON (n.flight_number)",
    "CREATE INDEX region_iso_idx IF NOT EXISTS FOR (n:Region) ON (n.iso_code)",
]

# Relationship types documented for reference
RELATIONSHIP_TYPES = {
    "OCCURRED_IN": "Event → Region",
    "LOCATED_AT": "Event → GeoPoint | Airport → Region | Port → Region",
    "INVOLVES": "Event → Actor",
    "AFFECTS": "Event → Infrastructure",
    "DISRUPTS": "Event → Route",
    "ELEVATES_RISK_FOR": "Event → Airport | Port",
    "DEPARTS_FROM": "Flight → Airport",
    "ARRIVES_AT": "Flight → Airport",
    "OPERATED_BY": "Flight → Operator | Vessel → Operator",
    "CALLS_AT": "Vessel → Port",
    "TRAVELS_IN": "Vessel → Corridor",
    "CONNECTS": "Route → Airport | Port | Region",
    "ADJACENT_TO": "Region → Region",
    "CONNECTED_TO": "Actor → Actor",
    "SIMULATES": "Scenario → Event | Route | Region",
    "FOR": "ImpactAssessment → Region | Airport | Port | Corridor",
    "LOCATED_IN": "Airport → Region | Port → Region",
    "PROPAGATES_TO": "Infrastructure → Infrastructure (risk propagation)",
    "DEPENDS_ON": "Route → Corridor",
}


async def apply_schema() -> dict:
    """Apply all constraints and indexes. Returns counts."""
    results = {"constraints_applied": 0, "indexes_applied": 0, "errors": []}

    async with get_neo4j_session() as session:
        for stmt in CONSTRAINTS:
            try:
                await session.run(stmt)
                results["constraints_applied"] += 1
            except Exception as e:
                results["errors"].append(f"Constraint error: {e}")

        for stmt in INDEXES:
            try:
                await session.run(stmt)
                results["indexes_applied"] += 1
            except Exception as e:
                results["errors"].append(f"Index error: {e}")

    return results
