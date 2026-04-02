"""Event endpoints."""

from fastapi import APIRouter, Query

from src.engines.math.scoring import composite_risk_score
from src.engines.physics.threat_field import ThreatField, compute_threat_at_point
from src.services.state import get_state

router = APIRouter(prefix="/events", tags=["events"])


@router.get("")
async def list_events(
    limit: int = Query(50, ge=1, le=500),
    severity_min: float = Query(0.0, ge=0.0, le=1.0),
):
    """List recent events, optionally filtered by minimum severity."""
    state = get_state()
    events = [
        e for e in state.events
        if e.get("severity_score", 0) >= severity_min
    ]
    return {
        "count": len(events[:limit]),
        "events": events[:limit],
    }


@router.get("/threat-field")
async def threat_field_at_point(
    lat: float = Query(..., ge=-90, le=90),
    lng: float = Query(..., ge=-180, le=180),
):
    """Compute threat field intensity at a geographic point."""
    state = get_state()
    events_with_loc = [
        e for e in state.events
        if e.get("lat") is not None and e.get("lng") is not None
    ]
    threat, contributors = compute_threat_at_point(lat, lng, events_with_loc)
    return {
        "lat": lat,
        "lng": lng,
        "threat_intensity": threat,
        "top_contributors": contributors[:5],
    }
