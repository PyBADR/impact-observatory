"""Vessel + flight flow field for deck.gl visualization."""
from typing import List, Dict, Any


def compute_flow_field(routes: List[Dict[str, Any]], field_type: str = "maritime") -> Dict[str, Any]:
    features = []
    for route in routes:
        origin = route.get("origin", {})
        dest = route.get("destination", {})
        features.append({
            "type": "Feature",
            "geometry": {"type": "LineString", "coordinates": [[origin.get("lng", 0), origin.get("lat", 0)], [dest.get("lng", 0), dest.get("lat", 0)]]},
            "properties": {"flow_type": field_type, "volume": route.get("volume", 1), "risk": route.get("risk", 0), "id": route.get("id", "")}
        })
    return {"type": "FeatureCollection", "features": features, "metadata": {"field_type": field_type, "route_count": len(features)}}
