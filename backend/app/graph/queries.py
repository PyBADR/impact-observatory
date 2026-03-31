"""Pre-built Cypher query templates for GCC DIP graph analysis."""


class GraphQueries:
    """Collection of pre-built Cypher queries for common DIP operations."""

    @staticmethod
    def nearest_impacted_assets(event_id: str, max_hops: int = 3) -> str:
        """
        Find all assets impacted by an event within N hops using BFS.

        Multi-hop traversal through AFFECTS and DISRUPTS relationships
        to identify cascading impacts from a single event.

        Args:
            event_id: ID of the event node
            max_hops: Maximum number of relationship hops to traverse

        Returns:
            Cypher query string
        """
        return f"""
MATCH (event:Event {{id: $event_id}})
CALL apoc.path.expandConfig(event, {{
  relationshipFilter: "AFFECTS|DISRUPTS",
  maxLevel: {max_hops},
  uniqueness: "NODE_GLOBAL"
}}) YIELD path
WITH DISTINCT nodes(path) AS nodes
UNWIND nodes AS asset
WHERE asset <> event:Event
RETURN DISTINCT
  asset.id AS asset_id,
  labels(asset)[0] AS asset_type,
  asset.name AS asset_name,
  asset.status AS asset_status,
  length(path) - 1 AS hops_from_event
ORDER BY hops_from_event ASC, asset.name
"""

    @staticmethod
    def risk_propagation_path(source_id: str, target_id: str, max_depth: int = 5) -> str:
        """
        Find shortest path of risk propagation between two entities.

        Uses breadth-first search through AFFECTS, ELEVATES_RISK_FOR,
        and DISRUPTS relationships to trace risk flow.

        Args:
            source_id: ID of source entity
            target_id: ID of target entity
            max_depth: Maximum path depth

        Returns:
            Cypher query string
        """
        return f"""
MATCH (source {{id: $source_id}}), (target {{id: $target_id}})
CALL apoc.algo.dijkstra(source, target,
  'AFFECTS|ELEVATES_RISK_FOR|DISRUPTS',
  'impact_score|risk_delta'
) YIELD path, weight
WITH path, weight,
     [node IN nodes(path) | {{
       id: node.id,
       type: labels(node)[0],
       name: COALESCE(node.name, node.flight_number, node.icao, node.mmsi),
       risk: COALESCE(node.risk_level, node.severity)
     }}] AS node_sequence
RETURN
  weight AS total_risk_weight,
  length(relationships(path)) AS hops,
  node_sequence AS propagation_chain
LIMIT 1
"""

    @staticmethod
    def actor_influence_chain(actor_id: str, depth: int = 3) -> str:
        """
        Recursively traverse actor network for influence analysis.

        Follows CONNECTED_TO relationships bidirectionally to identify
        networks of actors and their influence reach.

        Args:
            actor_id: ID of the root actor
            depth: Maximum recursion depth

        Returns:
            Cypher query string
        """
        return f"""
MATCH (root:Actor {{id: $actor_id}})
CALL apoc.path.expandConfig(root, {{
  relationshipFilter: "CONNECTED_TO",
  maxLevel: {depth},
  uniqueness: "RELATIONSHIP_GLOBAL"
}}) YIELD path
WITH path,
     [rel IN relationships(path) | rel.connection_type] AS connection_types
RETURN
  nodes(path)[0].id AS root_actor_id,
  nodes(path)[0].name AS root_actor_name,
  nodes(path)[-1].id AS influenced_actor_id,
  nodes(path)[-1].name AS influenced_actor_name,
  length(path) - 1 AS degrees_of_separation,
  connection_types AS connection_chain,
  [node IN nodes(path) | node.threat_level] AS threat_levels
ORDER BY degrees_of_separation ASC
"""

    @staticmethod
    def reroute_alternatives(disrupted_route_id: str) -> str:
        """
        Find alternative routes with same origin and destination.

        Identifies viable routing options when a primary route is disrupted.

        Args:
            disrupted_route_id: ID of the disrupted route

        Returns:
            Cypher query string
        """
        return f"""
MATCH (disrupted:Route {{id: $disrupted_route_id}})
MATCH (disrupted)-[:CONNECTS]->(origin),
      (disrupted)-[:CONNECTS]->(destination)
WHERE NOT EXISTS {{(disrupted)-[:DISRUPTS]-(disrupted_event:Event)}}
MATCH (alt:Route)-[:CONNECTS]->(origin_alt),
      (alt:Route)-[:CONNECTS]->(dest_alt)
WHERE alt <> disrupted
  AND (
    (origin_alt.id = origin.id AND dest_alt.id = destination.id)
    OR (origin_alt.id = destination.id AND dest_alt.id = origin.id)
  )
  AND alt.status = "operational"
RETURN
  alt.id AS route_id,
  alt.name AS route_name,
  alt.distance_km AS distance_km,
  alt.status AS status,
  disrupted.distance_km - alt.distance_km AS distance_delta_km
ORDER BY distance_delta_km ASC
"""

    @staticmethod
    def chokepoint_concentration(corridor_id: str) -> str:
        """
        Identify concentration of traffic through a corridor chokepoint.

        Counts vessels, flights, and infrastructure using a corridor
        to assess criticality and vulnerability.

        Args:
            corridor_id: ID of the corridor

        Returns:
            Cypher query string
        """
        return f"""
MATCH (corridor:Corridor {{id: $corridor_id}})
WITH corridor
OPTIONAL MATCH (v:Vessel)-[:TRAVELS_IN]->(corridor)
WITH corridor, COUNT(v) AS vessel_count, COLLECT(v.id) AS vessels
OPTIONAL MATCH (f:Flight)-[:TRAVELS_IN]->(corridor)
WITH corridor, vessel_count, vessels, COUNT(f) AS flight_count, COLLECT(f.id) AS flights
OPTIONAL MATCH (r:Route)-[:TRAVELS_IN]->(corridor)
WITH corridor, vessel_count, vessels, flight_count, flights, COUNT(r) AS route_count, COLLECT(r.id) AS routes
RETURN
  corridor.id AS corridor_id,
  corridor.name AS corridor_name,
  corridor.corridor_type AS corridor_type,
  corridor.risk_level AS current_risk_level,
  vessel_count,
  flight_count,
  route_count,
  vessel_count + flight_count + route_count AS total_entities,
  vessels,
  flights,
  routes
"""

    @staticmethod
    def region_cascade(region_id: str, depth: int = 3) -> str:
        """
        Trace cascade of regional impacts through adjacent regions.

        Follows ADJACENT_TO relationships to identify how events or risks
        propagate across geographical boundaries.

        Args:
            region_id: ID of the initial region
            depth: Maximum propagation depth

        Returns:
            Cypher query string
        """
        return f"""
MATCH (root:Region {{id: $region_id}})
CALL apoc.path.expandConfig(root, {{
  relationshipFilter: "ADJACENT_TO",
  maxLevel: {depth},
  uniqueness: "NODE_GLOBAL"
}}) YIELD path
WITH path,
     [rel IN relationships(path) | rel.border_type] AS border_types
RETURN
  nodes(path)[0].id AS origin_region_id,
  nodes(path)[0].name AS origin_region_name,
  nodes(path)[-1].id AS cascade_region_id,
  nodes(path)[-1].name AS cascade_region_name,
  length(path) - 1 AS cascade_depth,
  border_types,
  [node IN nodes(path) | {{id: node.id, name: node.name, risk: node.risk_baseline}}] AS region_chain
ORDER BY cascade_depth ASC
"""

    @staticmethod
    def scenario_impact_subgraph(scenario_id: str) -> str:
        """
        Extract complete impact subgraph for a scenario.

        Returns all nodes and relationships that a scenario simulates,
        plus their immediate neighbors for impact context.

        Args:
            scenario_id: ID of the scenario

        Returns:
            Cypher query string
        """
        return f"""
MATCH (scenario:Scenario {{id: $scenario_id}})
MATCH (scenario)-[:SIMULATES]->(target)
WITH scenario, target
OPTIONAL MATCH (target)-[r]-(neighbor)
WHERE neighbor <> scenario
WITH scenario, target, r, neighbor
RETURN
  scenario.id AS scenario_id,
  scenario.name AS scenario_name,
  scenario.description AS scenario_description,
  COLLECT(DISTINCT {{
    id: target.id,
    type: labels(target)[0],
    name: COALESCE(target.name, target.flight_number, target.icao, target.mmsi),
    properties: properties(target)
  }}) AS simulated_targets,
  COLLECT(DISTINCT {{
    id: neighbor.id,
    type: labels(neighbor)[0],
    name: COALESCE(neighbor.name, neighbor.flight_number, neighbor.icao, neighbor.mmsi),
    relationship: type(r)
  }}) AS impacted_neighbors
"""

    @staticmethod
    def events_near_point(lat: float, lon: float, radius_km: float, limit: int = 50) -> str:
        """
        Spatial query for events near a geographic point.

        Uses Haversine distance calculation to find all events
        within radius of a lat/lon coordinate.

        Args:
            lat: Latitude of center point
            lon: Longitude of center point
            radius_km: Search radius in kilometers
            limit: Maximum results to return

        Returns:
            Cypher query string
        """
        return f"""
MATCH (event:Event)
WITH event,
     (6371 * 2 * asin(sqrt(
       sin(radians((event.lat - $lat) / 2)) ^ 2 +
       cos(radians($lat)) * cos(radians(event.lat)) *
       sin(radians((event.lon - $lon) / 2)) ^ 2
     ))) AS distance_km
WHERE distance_km <= $radius_km
RETURN
  event.id AS event_id,
  event.event_type AS event_type,
  event.severity AS severity,
  event.lat AS lat,
  event.lon AS lon,
  event.description AS description,
  event.timestamp AS timestamp,
  event.confidence AS confidence,
  ROUND(distance_km, 2) AS distance_km
ORDER BY distance_km ASC
LIMIT {limit}
"""
