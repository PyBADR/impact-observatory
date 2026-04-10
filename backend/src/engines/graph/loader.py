"""Neo4j graph loader — writes canonical entities as nodes and relationships.

Graph schema:
    (Event)-[:OCCURRED_IN]->(Region)
    (Event)-[:LOCATED_AT]->(GeoPoint)
    (Event)-[:INVOLVES]->(Actor)
    (Event)-[:AFFECTS]->(Infrastructure)
    (Event)-[:DISRUPTS]->(Route)
    (Event)-[:ELEVATES_RISK_FOR]->(Airport)
    (Event)-[:ELEVATES_RISK_FOR]->(Port)
    (Flight)-[:DEPARTS_FROM]->(Airport)
    (Flight)-[:ARRIVES_AT]->(Airport)
    (Flight)-[:OPERATED_BY]->(Operator)
    (Vessel)-[:CALLS_AT]->(Port)
    (Vessel)-[:TRAVELS_IN]->(Corridor)
    (Route)-[:CONNECTS]->(Airport|Port|Region)
    (Region)-[:ADJACENT_TO]->(Region)
    (Scenario)-[:SIMULATES]->(Event|Route|Region)
    (ImpactAssessment)-[:FOR]->(Region|Airport|Port|Corridor)
"""

from __future__ import annotations

from typing import Any

from src.db.neo4j import get_neo4j_session


async def upsert_node(label: str, node_id: str, properties: dict[str, Any]) -> None:
    """Create or update a node in Neo4j."""
    props = {k: v for k, v in properties.items() if v is not None}
    async with get_neo4j_session() as session:
        await session.run(
            f"MERGE (n:{label} {{id: $id}}) SET n += $props",
            id=node_id,
            props=props,
        )


async def upsert_relationship(
    from_label: str,
    from_id: str,
    to_label: str,
    to_id: str,
    rel_type: str,
    properties: dict[str, Any] | None = None,
) -> None:
    """Create or update a relationship between two nodes."""
    props = properties or {}
    query = (
        f"MATCH (a:{from_label} {{id: $from_id}}), (b:{to_label} {{id: $to_id}}) "
        f"MERGE (a)-[r:{rel_type}]->(b) SET r += $props"
    )
    async with get_neo4j_session() as session:
        await session.run(query, from_id=from_id, to_id=to_id, props=props)


async def load_event(event: dict[str, Any]) -> None:
    """Load an event node and its relationships."""
    await upsert_node("Event", event["id"], {
        "title": event.get("title"),
        "event_type": event.get("event_type"),
        "severity_score": event.get("severity_score"),
        "lat": event.get("location", {}).get("lat") if event.get("location") else None,
        "lng": event.get("location", {}).get("lng") if event.get("location") else None,
    })

    if event.get("region_id"):
        await upsert_relationship("Event", event["id"], "Region", event["region_id"], "OCCURRED_IN")

    for entity_id in event.get("affected_entity_ids", []):
        await upsert_relationship("Event", event["id"], "Infrastructure", entity_id, "AFFECTS")


async def load_flight(flight: dict[str, Any]) -> None:
    """Load a flight node and its relationships."""
    await upsert_node("Flight", flight["id"], {
        "flight_number": flight.get("flight_number"),
        "status": flight.get("status"),
        "aircraft_type": flight.get("aircraft_type"),
    })

    if flight.get("origin_airport_id"):
        await upsert_relationship("Flight", flight["id"], "Airport", flight["origin_airport_id"], "DEPARTS_FROM")
    if flight.get("destination_airport_id"):
        await upsert_relationship("Flight", flight["id"], "Airport", flight["destination_airport_id"], "ARRIVES_AT")
    if flight.get("operator_id"):
        await upsert_relationship("Flight", flight["id"], "Operator", flight["operator_id"], "OPERATED_BY")


async def load_vessel(vessel: dict[str, Any]) -> None:
    """Load a vessel node and its relationships."""
    await upsert_node("Vessel", vessel["id"], {
        "name": vessel.get("name"),
        "mmsi": vessel.get("mmsi"),
        "vessel_type": vessel.get("vessel_type"),
        "speed_knots": vessel.get("speed_knots"),
    })

    if vessel.get("destination_port_id"):
        await upsert_relationship("Vessel", vessel["id"], "Port", vessel["destination_port_id"], "CALLS_AT")


async def load_region(region: dict[str, Any]) -> None:
    """Load a region node."""
    await upsert_node("Region", region["id"], {
        "name": region.get("name"),
        "name_ar": region.get("name_ar"),
        "iso_code": region.get("iso_code"),
    })


async def load_airport(airport: dict[str, Any]) -> None:
    """Load an airport node."""
    await upsert_node("Airport", airport["id"], {
        "iata": airport.get("iata"),
        "icao": airport.get("icao"),
        "name": airport.get("name"),
        "operational_criticality": airport.get("operational_criticality"),
        "lat": airport.get("location", {}).get("lat") if airport.get("location") else None,
        "lng": airport.get("location", {}).get("lng") if airport.get("location") else None,
    })

    if airport.get("country_id"):
        await upsert_relationship("Airport", airport["id"], "Region", airport["country_id"], "LOCATED_IN")


async def load_port(port: dict[str, Any]) -> None:
    """Load a port node."""
    await upsert_node("Port", port["id"], {
        "code": port.get("code"),
        "name": port.get("name"),
        "operational_criticality": port.get("operational_criticality"),
        "lat": port.get("location", {}).get("lat") if port.get("location") else None,
        "lng": port.get("location", {}).get("lng") if port.get("location") else None,
    })

    if port.get("country_id"):
        await upsert_relationship("Port", port["id"], "Region", port["country_id"], "LOCATED_IN")


async def load_corridor(corridor: dict[str, Any]) -> None:
    """Load a corridor node."""
    await upsert_node("Corridor", corridor["id"], {
        "name": corridor.get("name"),
        "corridor_type": corridor.get("corridor_type"),
        "chokepoint": corridor.get("chokepoint"),
        "resistance": corridor.get("resistance"),
    })


async def query_risk_propagation_path(
    start_node_id: str,
    max_hops: int = 5,
) -> list[dict[str, Any]]:
    """Find risk propagation paths from a given node up to max_hops."""
    query = (
        "MATCH path = (start {id: $start_id})-[*1.." + str(max_hops) + "]->(end) "
        "RETURN [n IN nodes(path) | n.id] AS node_ids, "
        "[r IN relationships(path) | type(r)] AS rel_types, "
        "length(path) AS hops "
        "ORDER BY hops "
        "LIMIT 50"
    )
    async with get_neo4j_session() as session:
        result = await session.run(query, start_id=start_node_id)
        records = [dict(r) async for r in result]
    return records


async def query_chokepoint_concentration(threshold: float = 0.7) -> list[dict[str, Any]]:
    """Find nodes with high in-degree (chokepoint risk)."""
    query = (
        "MATCH (n)<-[r]-() "
        "WITH n, count(r) AS in_degree "
        "WHERE in_degree > 3 "
        "RETURN n.id AS node_id, n.name AS name, in_degree "
        "ORDER BY in_degree DESC "
        "LIMIT 20"
    )
    async with get_neo4j_session() as session:
        result = await session.run(query)
        records = [dict(r) async for r in result]
    return records


async def query_reroute_alternatives(
    disrupted_route_id: str,
) -> list[dict[str, Any]]:
    """Find alternative routes when a route is disrupted."""
    query = (
        "MATCH (route:Route {id: $route_id})-[:CONNECTS]->(dest) "
        "MATCH (alt:Route)-[:CONNECTS]->(dest) "
        "WHERE alt.id <> $route_id "
        "RETURN alt.id AS alternative_id, alt.name AS name, dest.id AS destination "
        "LIMIT 10"
    )
    async with get_neo4j_session() as session:
        result = await session.run(query, route_id=disrupted_route_id)
        records = [dict(r) async for r in result]
    return records
