"""Database service layer — provides ORM-backed CRUD for flights, vessels, events.

Falls back to in-memory state when PostgreSQL is not available (e.g., tests).
Uses async SQLAlchemy sessions when connected.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select, delete, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.orm import FlightRecord, VesselRecord, EventRecord

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════
# Flights
# ═══════════════════════════════════════════════════

async def list_flights_db(
    session: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    status: str | None = None,
    origin: str | None = None,
    destination: str | None = None,
    airline: str | None = None,
    min_risk: float | None = None,
    sort_by: str = "id",
) -> dict[str, Any]:
    """List flights from PostgreSQL with filtering."""
    q = select(FlightRecord)
    if status:
        q = q.where(FlightRecord.status == status)
    if origin:
        q = q.where(FlightRecord.origin_airport_id == origin)
    if destination:
        q = q.where(FlightRecord.destination_airport_id == destination)
    if airline:
        q = q.where(func.lower(FlightRecord.airline) == airline.lower())
    if min_risk is not None:
        q = q.where(FlightRecord.risk_score >= min_risk)

    # Sort
    sort_col = getattr(FlightRecord, sort_by, FlightRecord.id)
    q = q.order_by(sort_col)

    # Count
    count_q = select(func.count()).select_from(q.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    # Paginate
    q = q.offset(offset).limit(limit)
    result = await session.execute(q)
    flights = [_flight_to_dict(f) for f in result.scalars().all()]

    return {"count": len(flights), "total": total, "flights": flights}


async def get_flight_db(session: AsyncSession, flight_id: str) -> dict | None:
    """Get a single flight by ID."""
    result = await session.execute(select(FlightRecord).where(FlightRecord.id == flight_id))
    record = result.scalar_one_or_none()
    return _flight_to_dict(record) if record else None


async def create_flight_db(session: AsyncSession, data: dict) -> dict:
    """Create a new flight record."""
    record = FlightRecord(**{k: v for k, v in data.items() if hasattr(FlightRecord, k)})
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return _flight_to_dict(record)


async def update_flight_db(session: AsyncSession, flight_id: str, updates: dict) -> dict | None:
    """Update an existing flight."""
    result = await session.execute(select(FlightRecord).where(FlightRecord.id == flight_id))
    record = result.scalar_one_or_none()
    if not record:
        return None
    for key, val in updates.items():
        if hasattr(record, key) and val is not None:
            setattr(record, key, val)
    await session.commit()
    await session.refresh(record)
    return _flight_to_dict(record)


async def delete_flight_db(session: AsyncSession, flight_id: str) -> bool:
    """Delete a flight. Returns True if deleted."""
    result = await session.execute(delete(FlightRecord).where(FlightRecord.id == flight_id))
    await session.commit()
    return result.rowcount > 0


# ═══════════════════════════════════════════════════
# Vessels
# ═══════════════════════════════════════════════════

async def list_vessels_db(
    session: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    vessel_type: str | None = None,
    destination: str | None = None,
    flag_state: str | None = None,
    min_speed: float | None = None,
    max_speed: float | None = None,
    min_risk: float | None = None,
    sort_by: str = "id",
) -> dict[str, Any]:
    """List vessels from PostgreSQL with filtering."""
    q = select(VesselRecord)
    if vessel_type:
        q = q.where(VesselRecord.vessel_type == vessel_type)
    if destination:
        q = q.where(VesselRecord.destination_port_id == destination)
    if flag_state:
        q = q.where(func.lower(VesselRecord.flag_state) == flag_state.lower())
    if min_speed is not None:
        q = q.where(VesselRecord.speed_knots >= min_speed)
    if max_speed is not None:
        q = q.where(VesselRecord.speed_knots <= max_speed)
    if min_risk is not None:
        q = q.where(VesselRecord.risk_score >= min_risk)

    sort_col = getattr(VesselRecord, sort_by, VesselRecord.id)
    q = q.order_by(sort_col)

    count_q = select(func.count()).select_from(q.subquery())
    total = (await session.execute(count_q)).scalar() or 0

    q = q.offset(offset).limit(limit)
    result = await session.execute(q)
    vessels = [_vessel_to_dict(v) for v in result.scalars().all()]

    return {"count": len(vessels), "total": total, "vessels": vessels}


async def get_vessel_db(session: AsyncSession, vessel_id: str) -> dict | None:
    result = await session.execute(select(VesselRecord).where(VesselRecord.id == vessel_id))
    record = result.scalar_one_or_none()
    return _vessel_to_dict(record) if record else None


async def get_vessel_by_mmsi_db(session: AsyncSession, mmsi: str) -> dict | None:
    result = await session.execute(select(VesselRecord).where(VesselRecord.mmsi == mmsi))
    record = result.scalar_one_or_none()
    return _vessel_to_dict(record) if record else None


async def create_vessel_db(session: AsyncSession, data: dict) -> dict:
    record = VesselRecord(**{k: v for k, v in data.items() if hasattr(VesselRecord, k)})
    session.add(record)
    await session.commit()
    await session.refresh(record)
    return _vessel_to_dict(record)


async def update_vessel_db(session: AsyncSession, vessel_id: str, updates: dict) -> dict | None:
    result = await session.execute(select(VesselRecord).where(VesselRecord.id == vessel_id))
    record = result.scalar_one_or_none()
    if not record:
        return None
    for key, val in updates.items():
        if hasattr(record, key) and val is not None:
            setattr(record, key, val)
    await session.commit()
    await session.refresh(record)
    return _vessel_to_dict(record)


async def delete_vessel_db(session: AsyncSession, vessel_id: str) -> bool:
    result = await session.execute(delete(VesselRecord).where(VesselRecord.id == vessel_id))
    await session.commit()
    return result.rowcount > 0


# ═══════════════════════════════════════════════════
# Serializers
# ═══════════════════════════════════════════════════

def _flight_to_dict(record: FlightRecord) -> dict:
    return {
        "id": record.id,
        "flight_number": record.flight_number,
        "status": record.status,
        "origin_airport_id": record.origin_airport_id,
        "destination_airport_id": record.destination_airport_id,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "altitude_ft": record.altitude_ft,
        "speed_knots": record.speed_knots,
        "heading": record.heading,
        "airline": record.airline,
        "aircraft_type": record.aircraft_type,
        "risk_score": record.risk_score,
        "metadata": record.metadata_json,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }


def _vessel_to_dict(record: VesselRecord) -> dict:
    return {
        "id": record.id,
        "name": record.name,
        "mmsi": record.mmsi,
        "imo": record.imo,
        "vessel_type": record.vessel_type,
        "flag_state": record.flag_state,
        "latitude": record.latitude,
        "longitude": record.longitude,
        "speed_knots": record.speed_knots,
        "heading": record.heading,
        "destination_port_id": record.destination_port_id,
        "risk_score": record.risk_score,
        "metadata": record.metadata_json,
        "created_at": record.created_at.isoformat() if record.created_at else None,
        "updated_at": record.updated_at.isoformat() if record.updated_at else None,
    }
