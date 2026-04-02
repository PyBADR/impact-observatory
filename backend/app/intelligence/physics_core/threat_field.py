"""Geospatial threat field for deck.gl visualization."""
from typing import List, Dict, Any


def compute_threat_field(events: List[Dict[str, Any]], grid_resolution: float = 0.5, decay_km: float = 100.0) -> Dict[str, Any]:
    """Generate threat intensity grid from conflict/incident events."""
    if not events:
        return {"type": "FeatureCollection", "features": []}
    features = []
    for event in events:
        lat, lng = event.get("lat", 0), event.get("lng", 0)
        severity = event.get("severity", 0.5)
        radius_deg = decay_km / 111.0
        features.append({
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [lng, lat]},
            "properties": {"severity": severity, "radius": radius_deg, "type": event.get("type", "unknown"), "decay_km": decay_km}
        })
    return {"type": "FeatureCollection", "features": features, "metadata": {"count": len(features), "grid_resolution": grid_resolution}}
