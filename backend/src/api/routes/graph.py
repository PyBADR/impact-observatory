"""Graph query endpoints."""

from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/graph", tags=["graph"])


@router.get("/propagation-path")
async def propagation_path(
    start_node_id: str = Query(...),
    max_hops: int = Query(5, ge=1, le=10),
):
    """Find risk propagation paths from a node through the graph."""
    try:
        from src.engines.graph.loader import query_risk_propagation_path
        paths = await query_risk_propagation_path(start_node_id, max_hops)
        return {"start": start_node_id, "max_hops": max_hops, "paths": paths}
    except Exception:
        # Neo4j not connected — return from in-memory state
        from src.services.state import get_state
        state = get_state()
        # BFS through edges
        paths = _bfs_paths(start_node_id, state.edges, max_hops)
        return {"start": start_node_id, "max_hops": max_hops, "paths": paths}


@router.get("/chokepoints")
async def chokepoints():
    """Find high-concentration chokepoint nodes."""
    try:
        from src.engines.graph.loader import query_chokepoint_concentration
        results = await query_chokepoint_concentration()
        return {"chokepoints": results}
    except Exception:
        from src.services.state import get_state
        state = get_state()
        # Compute in-degree from edges
        in_degree: dict[str, int] = {}
        for e in state.edges:
            tgt = e.get("target", "")
            in_degree[tgt] = in_degree.get(tgt, 0) + 1
        ranked = sorted(in_degree.items(), key=lambda x: x[1], reverse=True)[:20]
        return {
            "chokepoints": [
                {"node_id": nid, "in_degree": deg, "name": state.node_labels.get(nid, nid)}
                for nid, deg in ranked
                if deg > 2
            ]
        }


@router.get("/nodes")
async def graph_nodes(
    sector: str | None = Query(None, description="Filter by layer: energy, maritime, aviation, finance, infrastructure, government"),
    limit: int = Query(200, ge=1, le=500),
):
    """Return GCC entity graph nodes and edges.

    Returns the static GCC knowledge graph (42+ entities, 57+ edges) from
    entity_graph_service. Optionally filtered by sector/layer.
    """
    from src.services.entity_graph_service import get_entities, get_edges

    entities = get_entities()
    edges = get_edges()

    # Apply sector filter
    if sector:
        entity_ids = {e["id"] for e in entities if e.get("layer") == sector}
        entities = [e for e in entities if e.get("layer") == sector]
        edges = [
            ed for ed in edges
            if ed.get("source_id") in entity_ids and ed.get("target_id") in entity_ids
        ]

    # Apply limit
    entities = entities[:limit]
    entity_ids = {e["id"] for e in entities}
    edges = [
        ed for ed in edges
        if ed.get("source_id") in entity_ids and ed.get("target_id") in entity_ids
    ]

    # Transform to frontend GraphNode / GraphEdge format
    nodes = [
        {
            "id": e["id"],
            "label": e["label"],
            "label_ar": e.get("label_ar", e["label"]),
            "type": e.get("entity_type", "node"),
            "layer": e.get("layer", "infrastructure"),
            "country": e.get("country", "GCC"),
            "latitude": e.get("latitude"),
            "longitude": e.get("longitude"),
            "gdp_weight": e.get("gdp_weight", 0),
            "criticality": e.get("criticality", 0.5),
            "risk_score": e.get("criticality", 0.5),  # use criticality as initial risk score
        }
        for e in entities
    ]

    graph_edges = [
        {
            "source": ed["source_id"],
            "target": ed["target_id"],
            "edge_type": ed.get("edge_type", "financial"),
            "weight": ed.get("weight", 0.5),
        }
        for ed in edges
    ]

    return {"nodes": nodes, "edges": graph_edges, "count": len(nodes)}


def _bfs_paths(start: str, edges: list[dict], max_hops: int) -> list[dict]:
    """Simple BFS for path finding without Neo4j."""
    adj: dict[str, list[str]] = {}
    for e in edges:
        src, tgt = e.get("source", ""), e.get("target", "")
        adj.setdefault(src, []).append(tgt)

    paths = []
    queue = [(start, [start])]
    visited = {start}

    while queue:
        node, path = queue.pop(0)
        if len(path) > max_hops + 1:
            break
        for neighbor in adj.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                new_path = path + [neighbor]
                paths.append({"node_ids": new_path, "hops": len(new_path) - 1})
                queue.append((neighbor, new_path))

    return paths[:50]
