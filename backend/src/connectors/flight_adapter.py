"""Aviation / flight tracking data connector.

Adapts flight movement, delay, and cancellation data
into canonical Flight, Airport, and Event schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.connectors.base import BaseConnector
from src.models.canonical import (
    Alert,
    CanonicalBase,
    ConfidenceMeta,
    Event,
    Flight,
    GeoPoint,
    Provenance,
    SeverityLevel,
    SourceType,
)


class FlightAdapter(BaseConnector):
    """Adapter for flight tracking / aviation disruption data."""

    source_name = "flight_feed"
    source_type = "aviation"

    def __init__(self, data: list[dict[str, Any]] | None = None):
        self._data = data or []

    async def fetch_raw(self, **kwargs) -> list[dict[str, Any]]:
        return self._data

    def normalize(self, raw: dict[str, Any]) -> list[CanonicalBase]:
        entities: list[CanonicalBase] = []

        prov = Provenance(
            source_type=SourceType.AVIATION,
            source_name=self.source_name,
            source_id=str(raw.get("flight_id", raw.get("id", ""))),
            raw_payload=raw,
        )

        position = None
        if raw.get("latitude") and raw.get("longitude"):
            position = GeoPoint(
                lat=float(raw["latitude"]),
                lng=float(raw["longitude"]),
                alt_m=raw.get("altitude"),
            )

        flight = Flight(
            flight_number=raw.get("flight_number", raw.get("callsign", "UNKNOWN")),
            operator_id=raw.get("airline_icao"),
            origin_airport_id=raw.get("departure_airport", ""),
            destination_airport_id=raw.get("arrival_airport", ""),
            departure_time=_parse_ts(raw.get("departure_time")),
            arrival_time=_parse_ts(raw.get("arrival_time")),
            status=_map_status(raw.get("status", "scheduled")),
            aircraft_type=raw.get("aircraft_type", ""),
            current_position=position,
            provenance=prov,
            confidence=ConfidenceMeta(score=0.85, source_quality=0.9, data_freshness=1.0),
        )
        entities.append(flight)

        # Generate disruption events for cancelled/diverted flights
        status = raw.get("status", "").lower()
        if status in ("cancelled", "diverted"):
            severity = SeverityLevel.HIGH if status == "cancelled" else SeverityLevel.MEDIUM
            event = Event(
                title=f"Flight {flight.flight_number} {status}",
                event_type="aviation_disruption",
                severity=severity,
                severity_score=0.7 if status == "cancelled" else 0.5,
                location=position,
                affected_entity_ids=[flight.id],
                start_time=flight.departure_time,
                provenance=prov,
            )
            entities.append(event)

        return entities


def _parse_ts(ts: str | int | None) -> datetime | None:
    if ts is None:
        return None
    if isinstance(ts, int):
        return datetime.utcfromtimestamp(ts)
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(ts, fmt)
        except (ValueError, TypeError):
            continue
    return None


def _map_status(raw_status: str) -> str:
    mapping = {
        "en-route": "en_route",
        "in-air": "en_route",
        "landed": "arrived",
        "scheduled": "scheduled",
        "cancelled": "cancelled",
        "diverted": "diverted",
        "delayed": "scheduled",
    }
    return mapping.get(raw_status.lower(), raw_status.lower())
