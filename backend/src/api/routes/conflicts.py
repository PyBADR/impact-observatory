"""Conflict and incident intelligence endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from src.engines.math_core.risk import (
    ThreatSource,
    compute_geopolitical_threat,
)
from src.engines.math_core.gcc_weights import EVENT_MULTIPLIERS
from src.services.state import get_state

router = APIRouter(prefix="/conflicts", tags=["conflicts"])


@router.get("")
async def list_conflicts(
    limit: int = Query(50, ge=1, le=500),
    severity_min: float = Query(0.0, ge=0.0, le=1.0),
    event_type: str | None = None,
):
    """List conflict events, optionally filtered."""
    state = get_state()
    events = state.events
    if event_type:
        events = [e for e in events if e.get("event_type") == event_type]
    events = [e for e in events if e.get("severity_score", 0) >= severity_min]
    return {"count": len(events[:limit]), "events": events[:limit]}


@router.get("/event-multipliers")
async def get_event_multipliers():
    """Return GCC event multiplier table for all event types."""
    return {
        "multipliers": EVENT_MULTIPLIERS,
        "description": "M_e values used in Phi_e(i,t) = M_e * Sev * Conf * exp(-λd*d) * exp(-λt*Δt)",
    }


class ThreatFieldRequest(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lng: float = Field(ge=-180, le=180)
    events: list[dict] = Field(default_factory=list)


@router.post("/threat-field")
async def compute_threat_field(req: ThreatFieldRequest):
    """Compute geopolitical threat field at a point using GCC equation."""
    state = get_state()
    event_sources = req.events or state.events

    threats = []
    for ev in event_sources:
        if ev.get("lat") and ev.get("lng"):
            threats.append(ThreatSource(
                event_type=ev.get("event_type", "diplomatic_tension"),
                severity=ev.get("severity_score", 0.5),
                confidence=ev.get("confidence", 0.7),
                lat=ev["lat"],
                lng=ev["lng"],
                hours_ago=ev.get("hours_ago", 1.0),
                is_kinetic=ev.get("event_type") in ("military", "security", "missile_strike"),
            ))

    threat_value, contributions = compute_geopolitical_threat(req.lat, req.lng, threats)
    return {
        "lat": req.lat,
        "lng": req.lng,
        "threat_intensity": threat_value,
        "n_sources": len(threats),
        "contributions": contributions[:10],
        "equation": "Phi_e(i,t) = M_e * Sev * Conf * exp(-λd*d) * exp(-λt*Δt)",
    }
