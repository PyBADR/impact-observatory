"""Neo4j graph loader — bulk-load GCC seed data and runtime entities into Neo4j.

Loads regions, airports, ports, corridors, routes, and establishes
all mandatory relationships from the platform specification.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Cypher templates for node creation
# ---------------------------------------------------------------------------

_MERGE_REGION = """
MERGE (r:Region {id: $id})
SET r.name = $name, r.name_ar = $name_ar, r.lat = $lat, r.lng = $lng,
    r.layer = $layer, r.country = $country
"""

_MERGE_AIRPORT = """
MERGE (a:Airport {id: $id})
SET a.iata = $iata, a.icao = $icao, a.name = $name, a.name_ar = $name_ar,
    a.country = $country, a.lat = $lat, a.lng = $lng,
    a.elevation_ft = $elevation_ft, a.asset_class = 'airport'
"""

_MERGE_PORT = """
MERGE (p:Port {id: $id})
SET p.name = $name, p.name_ar = $name_ar, p.country = $country,
    p.lat = $lat, p.lng = $lng, p.port_type = $port_type,
    p.oil_terminal = $oil_terminal, p.asset_class = 'seaport'
"""

_MERGE_CORRIDOR = """
MERGE (c:Corridor {id: $id})
SET c.name = $name, c.name_ar = $name_ar, c.corridor_type = $corridor_type,
    c.length_km = $length_km, c.chokepoint = $chokepoint,
    c.asset_class = $asset_class
"""

_MERGE_EVENT = """
MERGE (e:Event {id: $id})
SET e.title = $title, e.event_type = $event_type,
    e.severity_score = $severity_score, e.confidence = $confidence,
    e.lat = $lat, e.lng = $lng, e.region_id = $region_id,
    e.is_kinetic = $is_kinetic, e.source_type = $source_type
"""

_MERGE_FLIGHT = """
MERGE (f:Flight {id: $id})
SET f.flight_number = $flight_number, f.status = $status,
    f.origin_airport_id = $origin_airport_id,
    f.destination_airport_id = $destination_airport_id,
    f.latitude = $latitude, f.longitude = $longitude
"""

_MERGE_VESSEL = """
MERGE (v:Vessel {id: $id})
SET v.name = $name, v.mmsi = $mmsi, v.vessel_type = $vessel_type,
    v.latitude = $latitude, v.longitude = $longitude,
    v.speed_knots = $speed_knots, v.heading = $heading,
    v.destination_port_id = $destination_port_id
"""

_MERGE_SCENARIO = """
MERGE (s:Scenario {id: $id})
SET s.title = $title, s.scenario_type = $scenario_type,
    s.horizon_hours = $horizon_hours, s.shock_count = $shock_count
"""

_MERGE_INFRASTRUCTURE = """
MERGE (i:Infrastructure {id: $id})
SET i.name = $name, i.name_ar = $name_ar, i.infra_type = $infra_type,
    i.layer = $layer, i.lat = $lat, i.lng = $lng
"""

# ---------------------------------------------------------------------------
# Relationship templates
# ---------------------------------------------------------------------------

_CREATE_REL = """
MATCH (a {{id: $from_id}}), (b {{id: $to_id}})
MERGE (a)-[r:{rel_type}]->(b)
SET r.weight = $weight
"""


def _rel_query(rel_type: str) -> str:
    return _CREATE_REL.format(rel_type=rel_type)


# ---------------------------------------------------------------------------
# Loader class
# ---------------------------------------------------------------------------

class GraphLoader:
    """Loads GCC entities and relationships into Neo4j."""

    def __init__(self, session):
        self._session = session

    async def load_regions(self, regions: list[dict[str, Any]]) -> int:
        count = 0
        for r in regions:
            await self._session.run(_MERGE_REGION, **_region_params(r))
            count += 1
        return count

    async def load_airports(self, airports: list[dict[str, Any]]) -> int:
        count = 0
        for a in airports:
            await self._session.run(_MERGE_AIRPORT, **a)
            count += 1
            # (Region)-[:CONTAINS]->(Airport)
            if a.get("country"):
                await self._session.run(
                    _rel_query("CONTAINS"),
                    from_id=a["country"], to_id=a["id"], weight=1.0,
                )
        return count

    async def load_ports(self, ports: list[dict[str, Any]]) -> int:
        count = 0
        for p in ports:
            await self._session.run(_MERGE_PORT, **p)
            count += 1
            if p.get("country"):
                await self._session.run(
                    _rel_query("CONTAINS"),
                    from_id=p["country"], to_id=p["id"], weight=1.0,
                )
        return count

    async def load_corridors(self, corridors: list[dict[str, Any]]) -> int:
        count = 0
        for c in corridors:
            await self._session.run(_MERGE_CORRIDOR, **c)
            count += 1
        return count

    async def load_events(self, events: list[dict[str, Any]]) -> int:
        count = 0
        for e in events:
            params = {
                "id": e["id"],
                "title": e.get("title", ""),
                "event_type": e.get("event_type", "unknown"),
                "severity_score": e.get("severity_score", 0.5),
                "confidence": e.get("confidence", 0.7),
                "lat": e.get("lat"),
                "lng": e.get("lng"),
                "region_id": e.get("region_id"),
                "is_kinetic": e.get("is_kinetic", False),
                "source_type": e.get("source_type", "manual"),
            }
            await self._session.run(_MERGE_EVENT, **params)
            count += 1

            # (Event)-[:OCCURRED_IN]->(Region)
            if e.get("region_id"):
                await self._session.run(
                    _rel_query("OCCURRED_IN"),
                    from_id=e["id"], to_id=e["region_id"], weight=1.0,
                )

            # (Event)-[:ELEVATES_RISK_FOR] for nearby infrastructure
            for infra_id in e.get("affected_infrastructure", []):
                await self._session.run(
                    _rel_query("ELEVATES_RISK_FOR"),
                    from_id=e["id"], to_id=infra_id,
                    weight=e.get("severity_score", 0.5),
                )
        return count

    async def load_flights(self, flights: list[dict[str, Any]]) -> int:
        count = 0
        for f in flights:
            params = {
                "id": f["id"],
                "flight_number": f.get("flight_number", ""),
                "status": f.get("status", "scheduled"),
                "origin_airport_id": f.get("origin_airport_id", ""),
                "destination_airport_id": f.get("destination_airport_id", ""),
                "latitude": f.get("latitude"),
                "longitude": f.get("longitude"),
            }
            await self._session.run(_MERGE_FLIGHT, **params)
            count += 1

            # (Flight)-[:DEPARTS_FROM]->(Airport)
            if f.get("origin_airport_id"):
                await self._session.run(
                    _rel_query("DEPARTS_FROM"),
                    from_id=f["id"], to_id=f["origin_airport_id"], weight=1.0,
                )
            # (Flight)-[:ARRIVES_AT]->(Airport)
            if f.get("destination_airport_id"):
                await self._session.run(
                    _rel_query("ARRIVES_AT"),
                    from_id=f["id"], to_id=f["destination_airport_id"], weight=1.0,
                )
        return count

    async def load_vessels(self, vessels: list[dict[str, Any]]) -> int:
        count = 0
        for v in vessels:
            params = {
                "id": v["id"],
                "name": v.get("name", ""),
                "mmsi": v.get("mmsi", ""),
                "vessel_type": v.get("vessel_type", "cargo"),
                "latitude": v.get("latitude"),
                "longitude": v.get("longitude"),
                "speed_knots": v.get("speed_knots"),
                "heading": v.get("heading"),
                "destination_port_id": v.get("destination_port_id"),
            }
            await self._session.run(_MERGE_VESSEL, **params)
            count += 1

            # (Vessel)-[:CALLS_AT]->(Port)
            if v.get("destination_port_id"):
                await self._session.run(
                    _rel_query("CALLS_AT"),
                    from_id=v["id"], to_id=v["destination_port_id"], weight=1.0,
                )
        return count

    async def load_scenarios(self, scenarios: list[dict[str, Any]]) -> int:
        count = 0
        for s in scenarios:
            params = {
                "id": s["id"],
                "title": s.get("title", ""),
                "scenario_type": s.get("scenario_type", "disruption"),
                "horizon_hours": s.get("horizon_hours", 72),
                "shock_count": len(s.get("shocks", [])),
            }
            await self._session.run(_MERGE_SCENARIO, **params)
            count += 1

            # (Scenario)-[:TARGETS]->(Region) for affected regions
            for target in s.get("target_regions", []):
                await self._session.run(
                    _rel_query("TARGETS"),
                    from_id=s["id"], to_id=target, weight=1.0,
                )
        return count

    async def load_infrastructure(self, infra: list[dict[str, Any]]) -> int:
        count = 0
        for item in infra:
            params = {
                "id": item["id"],
                "name": item.get("label", item.get("name", "")),
                "name_ar": item.get("label_ar", ""),
                "infra_type": item.get("infra_type", item.get("layer", "infrastructure")),
                "layer": item.get("layer", "infrastructure"),
                "lat": item.get("lat"),
                "lng": item.get("lng"),
            }
            await self._session.run(_MERGE_INFRASTRUCTURE, **params)
            count += 1
        return count

    async def load_edges(self, edges: list[dict[str, Any]]) -> int:
        """Load edges as generic weighted relationships."""
        count = 0
        for edge in edges:
            category = edge.get("category", "related_to").upper()
            # Map categories to relationship types
            rel_map = {
                "REGIONAL_CONTROL": "CONTAINS",
                "CRITICAL_PATH": "CONNECTS",
                "LOGISTICS": "CONNECTS",
                "TRADE_FLOW": "CONNECTS",
                "PRODUCTION": "CONNECTS",
                "TRANSPORT": "CONNECTS",
                "REVENUE": "CONNECTS",
                "RISK_TRANSFER": "CONNECTS",
                "MARKET_SIGNAL": "CONNECTS",
                "OPERATIONS": "CONNECTS",
                "MOBILITY": "AFFECTS",
                "WELFARE": "AFFECTS",
                "CAPITAL": "CONNECTS",
                "INFLUENCE": "AFFECTS",
                "FEEDBACK": "AFFECTS",
                "COST_PRESSURE": "AFFECTS",
                "CAPACITY": "CONNECTS",
                "CRITICAL_INFRASTRUCTURE": "CONNECTS",
            }
            rel_type = rel_map.get(category, "CONNECTS")
            await self._session.run(
                _rel_query(rel_type),
                from_id=edge["source"], to_id=edge["target"],
                weight=edge.get("weight", 0.5),
            )
            count += 1
        return count

    async def load_region_adjacency(self, adjacencies: list[tuple[str, str]]) -> int:
        count = 0
        for from_id, to_id in adjacencies:
            await self._session.run(
                _rel_query("ADJACENT_TO"),
                from_id=from_id, to_id=to_id, weight=1.0,
            )
            count += 1
        return count


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _region_params(r: dict) -> dict:
    return {
        "id": r["id"],
        "name": r.get("label", r.get("name", "")),
        "name_ar": r.get("label_ar", ""),
        "lat": r.get("lat"),
        "lng": r.get("lng"),
        "layer": r.get("layer", "geography"),
        "country": r.get("country", r.get("id", "")),
    }


# GCC region adjacency pairs
GCC_ADJACENCY = [
    ("saudi", "kuwait"),
    ("saudi", "bahrain"),
    ("saudi", "qatar"),
    ("saudi", "uae"),
    ("saudi", "oman"),
    ("kuwait", "saudi"),
    ("bahrain", "saudi"),
    ("qatar", "saudi"),
    ("uae", "saudi"),
    ("uae", "oman"),
    ("oman", "saudi"),
    ("oman", "uae"),
]
