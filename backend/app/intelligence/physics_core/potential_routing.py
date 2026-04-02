"""Dijkstra-based alternative route analysis."""
import heapq
from typing import Dict, List, Tuple, Any


def dijkstra(graph: Dict[str, List[Tuple[str, float]]], start: str, end: str) -> dict:
    dist = {start: 0.0}
    prev = {}
    pq = [(0.0, start)]
    while pq:
        d, u = heapq.heappop(pq)
        if u == end:
            break
        if d > dist.get(u, float('inf')):
            continue
        for v, w in graph.get(u, []):
            new_dist = d + w
            if new_dist < dist.get(v, float('inf')):
                dist[v] = new_dist
                prev[v] = u
                heapq.heappush(pq, (new_dist, v))
    path = []
    node = end
    while node in prev:
        path.append(node)
        node = prev[node]
    if path or start == end:
        path.append(start)
        path.reverse()
    return {"path": path, "cost": dist.get(end, float('inf')), "hops": len(path) - 1}


def find_alternative_routes(graph: dict, start: str, end: str, blocked: list[str] = None, k: int = 3) -> list[dict]:
    blocked = set(blocked or [])
    filtered = {n: [(v, w) for v, w in edges if v not in blocked] for n, edges in graph.items() if n not in blocked}
    primary = dijkstra(filtered, start, end)
    routes = [primary]
    for i in range(min(k - 1, len(primary["path"]) - 1)):
        modified = {n: list(edges) for n, edges in filtered.items()}
        if i < len(primary["path"]) - 1:
            u = primary["path"][i]
            v = primary["path"][i + 1]
            if u in modified:
                modified[u] = [(t, w) for t, w in modified[u] if t != v]
        alt = dijkstra(modified, start, end)
        if alt["path"] and alt not in routes:
            routes.append(alt)
    return routes
