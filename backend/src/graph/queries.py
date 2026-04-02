"""Neo4j graph query library — impact paths, risk propagation, and analytics.

Provides parameterized Cypher queries for the GCC Decision Intelligence
graph model. All queries return structured dicts for API serialization.
"""

from __future__ import annotations

from typing import Any


# ---------------------------------------------------------------------------
# Impact path queries
# ---------------------------------------------------------------------------

IMPACT_PATH_QUERY = """
MATCH path = shortestPath((source {id: $source_id})-[*..10]-(target {id: $target_id}))
RETURN [n IN nodes(path) | {id: n.id, name: n.name, labels: labels(n)}] AS nodes,
       [r IN relationships(path) | {type: type(r), weight: r.weight}] AS relationships,
       length(path) AS hops
"""

MULTI_HOP_IMPACT_QUERY = """
MATCH (source {id: $source_id})
CALL apoc.path.subgraphNodes(source, {maxLevel: $max_hops}) YIELD node
WHERE node.id IS NOT NULL
RETURN node.id AS id, node.name AS name, labels(node) AS labels,
       node.severity_score AS severity
ORDER BY node.severity_score DESC
LIMIT $limit
"""

# ---------------------------------------------------------------------------
# Risk propagation queries
# ---------------------------------------------------------------------------

NEIGHBORS_WITH_RISK = """
MATCH (n {id: $node_id})-[r]-(neighbor)
WHERE neighbor.id IS NOT NULL
RETURN neighbor.id AS id, neighbor.name AS name, labels(neighbor) AS labels,
       type(r) AS relationship, r.weight AS weight,
       neighbor.severity_score AS severity
ORDER BY r.weight DESC
"""

PROPAGATION_PATH = """
MATCH path = (source {id: $source_id})-[*1..$max_depth]->(target)
WHERE target.id IS NOT NULL
WITH target, path,
     reduce(w = 1.0, r IN relationships(path) | w * coalesce(r.weight, 0.5)) AS path_weight
RETURN target.id AS id, target.name AS name, labels(target) AS labels,
       path_weight, length(path) AS depth
ORDER BY path_weight DESC
LIMIT $limit
"""

# ---------------------------------------------------------------------------
# Analytics queries
# ---------------------------------------------------------------------------

CHOKEPOINT_ANALYSIS = """
MATCH (n)
WHERE n.id IS NOT NULL
OPTIONAL MATCH (n)-[r]-()
WITH n, count(r) AS degree
ORDER BY degree DESC
LIMIT $limit
RETURN n.id AS id, n.name AS name, labels(n) AS labels, degree
"""

SECTOR_CONNECTIVITY = """
MATCH (a)-[r]-(b)
WHERE a.layer IS NOT NULL AND b.layer IS NOT NULL
RETURN a.layer AS source_sector, b.layer AS target_sector,
       count(r) AS connection_count,
       avg(r.weight) AS avg_weight
ORDER BY connection_count DESC
"""

RISK_HOTSPOTS = """
MATCH (e:Event)-[:ELEVATES_RISK_FOR]->(target)
WHERE e.severity_score >= $min_severity
RETURN target.id AS id, target.name AS name, labels(target) AS labels,
       count(e) AS event_count,
       avg(e.severity_score) AS avg_severity,
       max(e.severity_score) AS max_severity
ORDER BY avg_severity DESC
LIMIT $limit
"""

EVENT_IMPACT_CASCADE = """
MATCH (e:Event {id: $event_id})-[:ELEVATES_RISK_FOR|DISRUPTS|AFFECTS*1..3]->(affected)
WHERE affected.id IS NOT NULL
RETURN DISTINCT affected.id AS id, affected.name AS name,
       labels(affected) AS labels
"""


# ---------------------------------------------------------------------------
# Query executor
# ---------------------------------------------------------------------------

class GraphQueries:
    """Execute parameterized graph queries against Neo4j."""

    def __init__(self, session):
        self._session = session

    async def impact_path(
        self, source_id: str, target_id: str
    ) -> dict[str, Any] | None:
        result = await self._session.run(
            IMPACT_PATH_QUERY, source_id=source_id, target_id=target_id
        )
        record = await result.single()
        if not record:
            return None
        return {
            "nodes": record["nodes"],
            "relationships": record["relationships"],
            "hops": record["hops"],
        }

    async def neighbors(self, node_id: str) -> list[dict[str, Any]]:
        result = await self._session.run(NEIGHBORS_WITH_RISK, node_id=node_id)
        return [dict(record) async for record in result]

    async def propagation_path(
        self, source_id: str, max_depth: int = 5, limit: int = 20
    ) -> list[dict[str, Any]]:
        result = await self._session.run(
            PROPAGATION_PATH,
            source_id=source_id, max_depth=max_depth, limit=limit,
        )
        return [dict(record) async for record in result]

    async def chokepoints(self, limit: int = 10) -> list[dict[str, Any]]:
        result = await self._session.run(CHOKEPOINT_ANALYSIS, limit=limit)
        return [dict(record) async for record in result]

    async def sector_connectivity(self) -> list[dict[str, Any]]:
        result = await self._session.run(SECTOR_CONNECTIVITY)
        return [dict(record) async for record in result]

    async def risk_hotspots(
        self, min_severity: float = 0.5, limit: int = 10
    ) -> list[dict[str, Any]]:
        result = await self._session.run(
            RISK_HOTSPOTS, min_severity=min_severity, limit=limit
        )
        return [dict(record) async for record in result]

    async def event_cascade(self, event_id: str) -> list[dict[str, Any]]:
        result = await self._session.run(
            EVENT_IMPACT_CASCADE, event_id=event_id
        )
        return [dict(record) async for record in result]
