"""Flight tracking and risk endpoints — full CRUD + filtering + risk scoring.

Supports two backends:
    1. PostgreSQL (via ORM) — when DB is available, uses async sessions
    2. In-memory state — fallback for dev/test without DB
"""

from __future__ import annotations

import logging
import math
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.services.state import get_state

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/flights", tags=["flights"])

# DB session dependency — returns None if DB not available
async def _get_db() -> AsyncSession | None:
    try:
        from src.db.postgres import get_session
        async for session in get_session():
            return session
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Pydantic schemas
# ---------------------------------------------------------------------------

class FlightCreate(BaseModel):
    flight_number: str = Field(..., min_length=2, max_length=32)
    status: str = Field("scheduled", pattern=r"^(scheduled|en_route|landed|cancelled|diverted)$")
    origin_airport_id: str
    destination_airport_id: str
    latitude: float | None = None
    longitude: float | None = None
    altitude_ft: float | None = None
    speed_knots: float | None = None
    heading: float | None = None
    airline: str | None = None
    aircraft_type: str | None = None
    risk_score: float | None = None
    metadata: dict | None = None


class FlightUpdate(BaseModel):
    flight_number: str | None = None
    status: str | None = Field(None, pattern=r"^(scheduled|en_route|landed|cancelled|diverted)$")
    latitude: float | None = None
    longitude: float | None = None
    altitude_ft: float | None = None
    speed_knots: float | None = None
    heading: float | None = None
    risk_score: float | None = None
    metadata: dict | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Haversine distance in km."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    a = math.sin(dlat / 2) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlng / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _compute_flight_risk(flight: dict, state) -> dict:
    """Compute risk score for a flight based on proximity to conflict events and route nodes."""
    risk = 0.0
    factors: list[dict] = []

    lat = flight.get("latitude")
    lng = flight.get("longitude")

    if lat is None or lng is None:
        return {"risk_score": 0.0, "factors": [], "classification": "NOMINAL"}

    # Factor 1: proximity to conflict events
    for evt in state.events:
        elat = evt.get("lat")
        elng = evt.get("lng")
        if elat is None or elng is None:
            continue
        dist = _haversine_km(lat, lng, elat, elng)
        if dist < 500:
            severity = evt.get("severity_score", 0.5)
            contribution = severity * math.exp(-0.005 * dist)
            risk += contribution
            factors.append({
                "type": "event_proximity",
                "event_id": evt.get("id"),
                "distance_km": round(dist, 1),
                "contribution": round(contribution, 4),
            })

    # Factor 2: route passes through high-risk infrastructure nodes
    origin = flight.get("origin_airport_id", "")
    dest = flight.get("destination_airport_id", "")
    chokepoints = {"hormuz", "shipping", "airspace"}
    for nid in state.node_ids:
        if nid in chokepoints:
            node_data = next((n for n in state.node_ids_full if n["id"] == nid), None)
            if node_data and node_data.get("lat") and node_data.get("lng"):
                dist = _haversine_km(lat, lng, node_data["lat"], node_data["lng"])
                if dist < 300:
                    contribution = 0.15 * math.exp(-0.003 * dist)
                    risk += contribution
                    factors.append({
                        "type": "chokepoint_proximity",
                        "node_id": nid,
                        "distance_km": round(dist, 1),
                        "contribution": round(contribution, 4),
                    })

    # Factor 3: cancelled/diverted status adds uncertainty
    status = flight.get("status", "scheduled")
    if status == "diverted":
        risk += 0.15
        factors.append({"type": "status_risk", "status": status, "contribution": 0.15})
    elif status == "cancelled":
        risk += 0.05
        factors.append({"type": "status_risk", "status": status, "contribution": 0.05})

    risk = min(risk, 1.0)
    classification = (
        "CRITICAL" if risk > 0.7
        else "ELEVATED" if risk > 0.4
        else "MODERATE" if risk > 0.2
        else "LOW" if risk > 0.05
        else "NOMINAL"
    )
    return {
        "risk_score": round(risk, 4),
        "factors": factors,
        "classification": classification,
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("")
async def list_flights(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    status: str | None = Query(None),
    origin: str | None = Query(None, description="Filter by origin airport ID"),
    destination: str | None = Query(None, description="Filter by destination airport ID"),
    airline: str | None = Query(None),
    min_risk: float | None = Query(None, ge=0.0, le=1.0),
    sort_by: str = Query("id", pattern=r"^(id|flight_number|status|risk_score)$"),
    db: AsyncSession | None = Depends(_get_db),
):
    """List tracked flights with filtering and sorting."""
    # DB-backed path
    if db is not None:
        try:
            from src.services.db_service import list_flights_db
            return await list_flights_db(
                db, limit=limit, offset=offset, status=status,
                origin=origin, destination=destination, airline=airline,
                min_risk=min_risk, sort_by=sort_by,
            )
        except Exception as e:
            logger.warning("DB query failed, falling back to in-memory: %s", e)

    # In-memory fallback
    state = get_state()
    flights = list(state.flights)

    if status:
        flights = [f for f in flights if f.get("status") == status]
    if origin:
        flights = [f for f in flights if f.get("origin_airport_id") == origin]
    if destination:
        flights = [f for f in flights if f.get("destination_airport_id") == destination]
    if airline:
        flights = [f for f in flights if (f.get("airline") or "").lower() == airline.lower()]
    if min_risk is not None:
        flights = [f for f in flights if (f.get("risk_score") or 0.0) >= min_risk]

    flights.sort(key=lambda f: f.get(sort_by, ""))
    total = len(flights)
    flights = flights[offset: offset + limit]
    return {"count": len(flights), "total": total, "flights": flights}


@router.get("/{flight_id}")
async def get_flight(flight_id: str, db: AsyncSession | None = Depends(_get_db)):
    """Get a single flight by ID."""
    if db is not None:
        try:
            from src.services.db_service import get_flight_db
            result = await get_flight_db(db, flight_id)
            if result:
                return result
        except Exception as e:
            logger.warning("DB query failed: %s", e)

    state = get_state()
    flight = next((f for f in state.flights if f["id"] == flight_id), None)
    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")
    return flight


@router.post("", status_code=201)
async def create_flight(body: FlightCreate, db: AsyncSession | None = Depends(_get_db)):
    """Create a new tracked flight."""
    flight_data = {
        "id": f"flt-{uuid.uuid4().hex[:8]}",
        **body.model_dump(exclude_none=True),
    }

    if db is not None:
        try:
            from src.services.db_service import create_flight_db
            return await create_flight_db(db, flight_data)
        except Exception as e:
            logger.warning("DB write failed, using in-memory: %s", e)

    state = get_state()
    state.flights.append(flight_data)
    return flight_data


@router.put("/{flight_id}")
async def update_flight(flight_id: str, body: FlightUpdate, db: AsyncSession | None = Depends(_get_db)):
    """Update an existing flight."""
    updates = body.model_dump(exclude_none=True)

    if db is not None:
        try:
            from src.services.db_service import update_flight_db
            result = await update_flight_db(db, flight_id, updates)
            if result:
                return result
        except Exception as e:
            logger.warning("DB update failed: %s", e)

    state = get_state()
    flight = next((f for f in state.flights if f["id"] == flight_id), None)
    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")
    flight.update(updates)
    return flight


@router.delete("/{flight_id}", status_code=204)
async def delete_flight(flight_id: str, db: AsyncSession | None = Depends(_get_db)):
    """Remove a tracked flight."""
    if db is not None:
        try:
            from src.services.db_service import delete_flight_db
            deleted = await delete_flight_db(db, flight_id)
            if deleted:
                return
        except Exception as e:
            logger.warning("DB delete failed: %s", e)

    state = get_state()
    idx = next((i for i, f in enumerate(state.flights) if f["id"] == flight_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")
    state.flights.pop(idx)


@router.get("/{flight_id}/risk")
async def get_flight_risk(flight_id: str):
    """Compute real-time risk assessment for a flight."""
    state = get_state()
    flight = next((f for f in state.flights if f["id"] == flight_id), None)
    if not flight:
        raise HTTPException(status_code=404, detail=f"Flight {flight_id} not found")
    return {
        "flight_id": flight_id,
        "flight_number": flight.get("flight_number"),
        **_compute_flight_risk(flight, state),
    }


@router.post("/risk/batch")
async def batch_flight_risk():
    """Compute risk scores for all tracked flights."""
    state = get_state()
    results = []
    for f in state.flights:
        risk = _compute_flight_risk(f, state)
        results.append({
            "flight_id": f["id"],
            "flight_number": f.get("flight_number"),
            **risk,
        })
    results.sort(key=lambda r: r["risk_score"], reverse=True)
    return {"count": len(results), "assessments": results}


@router.get("/nearby/search")
async def flights_nearby(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(200, ge=1, le=2000),
):
    """Find flights within a radius of a point."""
    state = get_state()
    nearby = []
    for f in state.flights:
        flat = f.get("latitude")
        flng = f.get("longitude")
        if flat is None or flng is None:
            continue
        dist = _haversine_km(lat, lng, flat, flng)
        if dist <= radius_km:
            nearby.append({**f, "distance_km": round(dist, 1)})
    nearby.sort(key=lambda x: x["distance_km"])
    return {"count": len(nearby), "flights": nearby}
