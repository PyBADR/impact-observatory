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
    except (RuntimeError, ImportError, ModuleNotFoundError):
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
    except (RuntimeError, ImportError, ModuleNotFoundError):
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
