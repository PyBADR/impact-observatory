"""Vessel tracking and risk endpoints — full CRUD + filtering + proximity search.

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
router = APIRouter(prefix="/vessels", tags=["vessels"])

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

class VesselCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    mmsi: str = Field(..., min_length=9, max_length=16)
    imo: str | None = None
    vessel_type: str = Field("cargo", pattern=r"^(tanker|container|cargo|bulk|lng|lpg|ro_ro|passenger|military|other)$")
    flag_state: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    speed_knots: float | None = None
    heading: float | None = None
    destination_port_id: str | None = None
    risk_score: float | None = None
    metadata: dict | None = None


class VesselUpdate(BaseModel):
    name: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    speed_knots: float | None = None
    heading: float | None = None
    destination_port_id: str | None = None
    risk_score: float | None = None
    status: str | None = None
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


def _compute_vessel_risk(vessel: dict, state) -> dict:
    """Compute risk for a vessel based on position, route, and events."""
    risk = 0.0
    factors: list[dict] = []
    lat = vessel.get("latitude")
    lng = vessel.get("longitude")

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

    # Factor 2: Hormuz / chokepoint proximity (critical for maritime)
    maritime_chokepoints = {"hormuz", "shipping"}
    for nid in state.node_ids:
        if nid in maritime_chokepoints:
            node_data = next((n for n in state.node_ids_full if n["id"] == nid), None)
            if node_data and node_data.get("lat") and node_data.get("lng"):
                dist = _haversine_km(lat, lng, node_data["lat"], node_data["lng"])
                if dist < 200:
                    # Maritime chokepoint decay is 0.0035
                    contribution = 0.25 * math.exp(-0.0035 * dist)
                    risk += contribution
                    factors.append({
                        "type": "chokepoint_proximity",
                        "node_id": nid,
                        "distance_km": round(dist, 1),
                        "contribution": round(contribution, 4),
                    })

    # Factor 3: vessel type risk modifier
    type_modifiers = {
        "tanker": 0.10,
        "lng": 0.12,
        "lpg": 0.10,
        "military": 0.08,
        "container": 0.05,
    }
    vtype = vessel.get("vessel_type", "cargo")
    if vtype in type_modifiers:
        mod = type_modifiers[vtype]
        risk += mod
        factors.append({"type": "vessel_type_risk", "vessel_type": vtype, "contribution": mod})

    # Factor 4: low speed anomaly (possible loitering/AIS manipulation)
    speed = vessel.get("speed_knots")
    if speed is not None and 0 < speed < 3.0:
        risk += 0.08
        factors.append({"type": "low_speed_anomaly", "speed_knots": speed, "contribution": 0.08})

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
async def list_vessels(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    vessel_type: str | None = Query(None),
    destination: str | None = Query(None, description="Filter by destination port ID"),
    min_speed: float | None = Query(None, ge=0.0),
    max_speed: float | None = Query(None, ge=0.0),
    min_risk: float | None = Query(None, ge=0.0, le=1.0),
    flag_state: str | None = Query(None),
    sort_by: str = Query("id", pattern=r"^(id|name|vessel_type|speed_knots|risk_score)$"),
    db: AsyncSession | None = Depends(_get_db),
):
    """List tracked vessels with filtering and sorting."""
    if db is not None:
        try:
            from src.services.db_service import list_vessels_db
            return await list_vessels_db(
                db, limit=limit, offset=offset, vessel_type=vessel_type,
                destination=destination, flag_state=flag_state,
                min_speed=min_speed, max_speed=max_speed, min_risk=min_risk,
                sort_by=sort_by,
            )
        except Exception as e:
            logger.warning("DB query failed, falling back to in-memory: %s", e)

    state = get_state()
    vessels = list(state.vessels)

    if vessel_type:
        vessels = [v for v in vessels if v.get("vessel_type") == vessel_type]
    if destination:
        vessels = [v for v in vessels if v.get("destination_port_id") == destination]
    if flag_state:
        vessels = [v for v in vessels if (v.get("flag_state") or "").lower() == flag_state.lower()]
    if min_speed is not None:
        vessels = [v for v in vessels if (v.get("speed_knots") or 0.0) >= min_speed]
    if max_speed is not None:
        vessels = [v for v in vessels if (v.get("speed_knots") or 0.0) <= max_speed]
    if min_risk is not None:
        vessels = [v for v in vessels if (v.get("risk_score") or 0.0) >= min_risk]

    vessels.sort(key=lambda v: v.get(sort_by) or "")
    total = len(vessels)
    vessels = vessels[offset: offset + limit]
    return {"count": len(vessels), "total": total, "vessels": vessels}


@router.get("/nearby/search")
async def vessels_nearby(
    lat: float = Query(...),
    lng: float = Query(...),
    radius_km: float = Query(200, ge=1, le=2000),
):
    """Find vessels within a radius of a point."""
    state = get_state()
    nearby = []
    for v in state.vessels:
        vlat = v.get("latitude")
        vlng = v.get("longitude")
        if vlat is None or vlng is None:
            continue
        dist = _haversine_km(lat, lng, vlat, vlng)
        if dist <= radius_km:
            nearby.append({**v, "distance_km": round(dist, 1)})
    nearby.sort(key=lambda x: x["distance_km"])
    return {"count": len(nearby), "vessels": nearby}


@router.get("/{vessel_id}")
async def get_vessel(vessel_id: str, db: AsyncSession | None = Depends(_get_db)):
    """Get a single vessel by ID."""
    if db is not None:
        try:
            from src.services.db_service import get_vessel_db
            result = await get_vessel_db(db, vessel_id)
            if result:
                return result
        except Exception as e:
            logger.warning("DB query failed: %s", e)

    state = get_state()
    vessel = next((v for v in state.vessels if v["id"] == vessel_id), None)
    if not vessel:
        raise HTTPException(status_code=404, detail=f"Vessel {vessel_id} not found")
    return vessel


@router.post("", status_code=201)
async def create_vessel(body: VesselCreate, db: AsyncSession | None = Depends(_get_db)):
    """Create a new tracked vessel."""
    vessel_data = {
        "id": f"vsl-{uuid.uuid4().hex[:8]}",
        **body.model_dump(exclude_none=True),
    }

    if db is not None:
        try:
            from src.services.db_service import get_vessel_by_mmsi_db, create_vessel_db
            existing = await get_vessel_by_mmsi_db(db, body.mmsi)
            if existing:
                raise HTTPException(status_code=409, detail=f"Vessel with MMSI {body.mmsi} already exists")
            return await create_vessel_db(db, vessel_data)
        except HTTPException:
            raise
        except Exception as e:
            logger.warning("DB write failed, using in-memory: %s", e)

    state = get_state()
    if any(v.get("mmsi") == body.mmsi for v in state.vessels):
        raise HTTPException(status_code=409, detail=f"Vessel with MMSI {body.mmsi} already exists")
    state.vessels.append(vessel_data)
    return vessel_data


@router.put("/{vessel_id}")
async def update_vessel(vessel_id: str, body: VesselUpdate, db: AsyncSession | None = Depends(_get_db)):
    """Update an existing vessel."""
    updates = body.model_dump(exclude_none=True)

    if db is not None:
        try:
            from src.services.db_service import update_vessel_db
            result = await update_vessel_db(db, vessel_id, updates)
            if result:
                return result
        except Exception as e:
            logger.warning("DB update failed: %s", e)

    state = get_state()
    vessel = next((v for v in state.vessels if v["id"] == vessel_id), None)
    if not vessel:
        raise HTTPException(status_code=404, detail=f"Vessel {vessel_id} not found")
    vessel.update(updates)
    return vessel


@router.delete("/{vessel_id}", status_code=204)
async def delete_vessel(vessel_id: str, db: AsyncSession | None = Depends(_get_db)):
    """Remove a tracked vessel."""
    if db is not None:
        try:
            from src.services.db_service import delete_vessel_db
            deleted = await delete_vessel_db(db, vessel_id)
            if deleted:
                return
        except Exception as e:
            logger.warning("DB delete failed: %s", e)

    state = get_state()
    idx = next((i for i, v in enumerate(state.vessels) if v["id"] == vessel_id), None)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"Vessel {vessel_id} not found")
    state.vessels.pop(idx)


@router.get("/{vessel_id}/risk")
async def get_vessel_risk(vessel_id: str):
    """Compute real-time risk assessment for a vessel."""
    state = get_state()
    vessel = next((v for v in state.vessels if v["id"] == vessel_id), None)
    if not vessel:
        raise HTTPException(status_code=404, detail=f"Vessel {vessel_id} not found")
    return {
        "vessel_id": vessel_id,
        "vessel_name": vessel.get("name"),
        "mmsi": vessel.get("mmsi"),
        **_compute_vessel_risk(vessel, state),
    }


@router.post("/risk/batch")
async def batch_vessel_risk():
    """Compute risk scores for all tracked vessels."""
    state = get_state()
    results = []
    for v in state.vessels:
        risk = _compute_vessel_risk(v, state)
        results.append({
            "vessel_id": v["id"],
            "vessel_name": v.get("name"),
            "mmsi": v.get("mmsi"),
            **risk,
        })
    results.sort(key=lambda r: r["risk_score"], reverse=True)
    return {"count": len(results), "assessments": results}
