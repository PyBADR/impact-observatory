"""Maritime / vessel tracking data connector.

Adapts AIS-style ship movement data and port events
into canonical Vessel, Port, and Event schemas.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from src.connectors.base import BaseConnector
from src.models.canonical import (
    CanonicalBase,
    ConfidenceMeta,
    Event,
    GeoPoint,
    Provenance,
    SeverityLevel,
    SourceType,
    Vessel,
)


class MaritimeAdapter(BaseConnector):
    """Adapter for AIS-style maritime vessel data."""

    source_name = "maritime_feed"
    source_type = "maritime"

    def __init__(self, data: list[dict[str, Any]] | None = None):
        self._data = data or []

    async def fetch_raw(self, **kwargs) -> list[dict[str, Any]]:
        return self._data

    def normalize(self, raw: dict[str, Any]) -> list[CanonicalBase]:
        entities: list[CanonicalBase] = []

        prov = Provenance(
            source_type=SourceType.MARITIME,
            source_name=self.source_name,
            source_id=str(raw.get("mmsi", raw.get("id", ""))),
            raw_payload=raw,
        )

        position = None
        if raw.get("latitude") and raw.get("longitude"):
            position = GeoPoint(lat=float(raw["latitude"]), lng=float(raw["longitude"]))

        vessel_type_map = {
            0: "unknown",
            6: "passenger",
            7: "cargo",
            8: "tanker",
            9: "other",
        }
        raw_type = raw.get("ship_type", raw.get("vessel_type", 0))
        if isinstance(raw_type, int):
            vtype = vessel_type_map.get(raw_type // 10 if raw_type > 9 else raw_type, "other")
        else:
            vtype = str(raw_type).lower()

        vessel = Vessel(
            mmsi=str(raw.get("mmsi", "")),
            imo=str(raw.get("imo", "")),
            name=raw.get("name", raw.get("vessel_name", "Unknown Vessel")),
            vessel_type=vtype,
            current_position=position,
            destination_port_id=raw.get("destination", ""),
            speed_knots=float(raw.get("speed", raw.get("sog", 0.0))),
            heading=float(raw.get("heading", raw.get("cog", 0.0))),
            cargo_type=raw.get("cargo_type", ""),
            deadweight_tonnes=float(raw.get("dwt", 0.0)),
            provenance=prov,
            confidence=ConfidenceMeta(
                score=0.8,
                source_quality=0.85,
                data_freshness=1.0,
            ),
        )
        entities.append(vessel)

        # Detect anomalies: vessel stopped in chokepoint
        speed = vessel.speed_knots
        if speed < 0.5 and position:
            # Check if near known chokepoints (simplified)
            if 25.5 < position.lat < 27.0 and 55.5 < position.lng < 57.0:
                event = Event(
                    title=f"Vessel {vessel.name} stationary in Hormuz corridor",
                    event_type="maritime_anomaly",
                    severity=SeverityLevel.MEDIUM,
                    severity_score=0.5,
                    location=position,
                    affected_entity_ids=[vessel.id],
                    provenance=prov,
                )
                entities.append(event)

        return entities
