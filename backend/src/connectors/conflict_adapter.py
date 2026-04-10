"""Conflict / geopolitical event data connector.

Adapts ACLED-style conflict data and generic incident feeds
into the canonical Event schema.
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
    Incident,
    Provenance,
    SeverityLevel,
    SourceType,
)


# Severity mapping from ACLED-style fatality counts
def _fatalities_to_severity(fatalities: int) -> tuple[SeverityLevel, float]:
    if fatalities == 0:
        return SeverityLevel.LOW, 0.2
    if fatalities <= 5:
        return SeverityLevel.MEDIUM, 0.5
    if fatalities <= 20:
        return SeverityLevel.HIGH, 0.75
    return SeverityLevel.CRITICAL, 0.95


class ConflictAdapter(BaseConnector):
    """Adapter for ACLED-style conflict event data."""

    source_name = "conflict_feed"
    source_type = "conflict"

    def __init__(self, data: list[dict[str, Any]] | None = None):
        self._data = data or []

    async def fetch_raw(self, **kwargs) -> list[dict[str, Any]]:
        """Return pre-loaded data. In production, this would call an API."""
        return self._data

    def normalize(self, raw: dict[str, Any]) -> list[CanonicalBase]:
        fatalities = int(raw.get("fatalities", 0))
        severity, severity_score = _fatalities_to_severity(fatalities)

        location = None
        if raw.get("latitude") and raw.get("longitude"):
            location = GeoPoint(lat=float(raw["latitude"]), lng=float(raw["longitude"]))

        prov = Provenance(
            source_type=SourceType.CONFLICT,
            source_name=self.source_name,
            source_id=str(raw.get("data_id", raw.get("id", ""))),
            raw_payload=raw,
        )

        event_type_map = {
            "Battles": "conflict",
            "Violence against civilians": "conflict",
            "Explosions/Remote violence": "conflict",
            "Riots": "security",
            "Protests": "political",
            "Strategic developments": "political",
        }

        event = Incident(
            title=raw.get("event_type", "Unknown Event"),
            description=raw.get("notes", ""),
            event_type=event_type_map.get(raw.get("event_type", ""), "conflict"),
            severity=severity,
            severity_score=severity_score,
            location=location,
            start_time=_parse_date(raw.get("event_date")),
            active=True,
            fatalities=fatalities,
            provenance=prov,
            confidence=ConfidenceMeta(
                score=0.7,
                source_quality=0.75,
                corroboration_count=int(raw.get("source_count", 1)),
                data_freshness=1.0,
            ),
            tags=[
                raw.get("event_type", ""),
                raw.get("sub_event_type", ""),
                raw.get("country", ""),
            ],
        )

        return [event]


def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d %B %Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None
