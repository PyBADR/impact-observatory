"""v1 Nodes API — static GCC node registry for globe/map rendering.

GET /api/v1/nodes   — return all 42 GCC nodes with lat/lng for frontend map
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("")
async def get_gcc_nodes():
    """Return the GCC node registry for map/globe rendering.

    Nodes are static (infrastructure doesn't move); stale-time = Infinity on client.
    Each node includes: id, label, label_ar, sector, lat, lng, capacity, criticality.
    """
    from src.simulation_engine import GCC_NODES

    nodes = [
        {
            "id": node["id"],
            "label": node["label"],
            "label_ar": node.get("label_ar", ""),
            "sector": node["sector"],
            "lat": node["lat"],
            "lng": node["lng"],
            # Normalise capacity to a float 0–1 relative scale (not raw barrels/USD)
            "capacity": float(node.get("capacity", 1)),
            "criticality": float(node.get("criticality", 0.5)),
            "current_load": float(node.get("current_load", 0.5)),
            "redundancy": float(node.get("redundancy", 0.3)),
        }
        for node in GCC_NODES
    ]

    return {"nodes": nodes, "count": len(nodes)}
