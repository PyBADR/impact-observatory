"""Incident intelligence endpoints — fused conflict + transport + infrastructure."""

from __future__ import annotations

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from src.services.state import get_state

router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("")
async def list_incidents(
    limit: int = Query(50, ge=1, le=500),
    severity_min: float = Query(0.0, ge=0.0, le=1.0),
    region: str | None = None,
):
    """List all incidents (fused from events, flight disruptions, vessel alerts)."""
    state = get_state()

    incidents: list[dict] = []

    # Events as incidents
    for ev in state.events:
        if ev.get("severity_score", 0) >= severity_min:
            if region and ev.get("region_id") != region:
                continue
            incidents.append({
                "id": ev.get("id"),
                "type": "conflict",
                "title": ev.get("title", "Unknown event"),
                "severity": ev.get("severity_score", 0),
                "lat": ev.get("lat"),
                "lng": ev.get("lng"),
                "region": ev.get("region_id"),
                "source_layer": "events",
            })

    # Cancelled/diverted flights as incidents
    for flt in state.flights:
        if flt.get("status") in ("cancelled", "diverted"):
            incidents.append({
                "id": flt.get("id"),
                "type": "transport_disruption",
                "title": f"Flight {flt.get('flight_number', '?')} {flt.get('status', '?')}",
                "severity": 0.5,
                "lat": flt.get("latitude"),
                "lng": flt.get("longitude"),
                "region": None,
                "source_layer": "flights",
            })

    # Slow/stopped vessels as incidents
    for vsl in state.vessels:
        speed = vsl.get("speed_knots", 0)
        if speed is not None and speed < 2.0:
            incidents.append({
                "id": vsl.get("id"),
                "type": "maritime_anomaly",
                "title": f"Vessel {vsl.get('name', '?')} near-stationary ({speed:.1f} kn)",
                "severity": 0.4,
                "lat": vsl.get("latitude"),
                "lng": vsl.get("longitude"),
                "region": None,
                "source_layer": "vessels",
            })

    incidents.sort(key=lambda x: x.get("severity", 0), reverse=True)
    return {"count": len(incidents[:limit]), "incidents": incidents[:limit]}


@router.get("/summary")
async def incident_summary():
    """High-level incident summary across all layers."""
    state = get_state()

    conflict_count = len(state.events)
    flight_disruptions = sum(
        1 for f in state.flights if f.get("status") in ("cancelled", "diverted")
    )
    maritime_anomalies = sum(
        1 for v in state.vessels if (v.get("speed_knots") or 0) < 2.0
    )
    max_severity = max(
        (e.get("severity_score", 0) for e in state.events), default=0
    )

    return {
        "total_incidents": conflict_count + flight_disruptions + maritime_anomalies,
        "conflict_events": conflict_count,
        "flight_disruptions": flight_disruptions,
        "maritime_anomalies": maritime_anomalies,
        "max_severity": max_severity,
        "layers_active": {
            "conflicts": conflict_count > 0,
            "flights": len(state.flights) > 0,
            "vessels": len(state.vessels) > 0,
        },
    }
