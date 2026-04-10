"""Unified normalizer — routes raw records through source-specific adapters.

The normalizer is the Layer 2 component of the lifecycle:
  INGEST → **NORMALIZE** → ENRICH → STORE → ...

It accepts raw records from any source, identifies the source type,
dispatches to the appropriate adapter, and returns canonical entities.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from src.models.canonical import (
    CanonicalBase,
    ConfidenceMeta,
    Event,
    Flight,
    GeoPoint,
    Incident,
    Provenance,
    SeverityLevel,
    SourceType,
    Vessel,
)


# ---------------------------------------------------------------------------
# Source detection
# ---------------------------------------------------------------------------

def _detect_source(raw: dict[str, Any]) -> str:
    """Heuristic source detection from raw record structure."""
    if "event_type" in raw and "fatalities" in raw:
        return "acled"
    if "category" in raw and "severity_level" in raw:
        return "global_incident_map"
    if "flight_number" in raw or "callsign" in raw:
        return "aviation"
    if "mmsi" in raw or "imo" in raw:
        return "maritime"
    if "iata" in raw or "icao" in raw:
        return "osm_infrastructure"
    return "unknown"


# ---------------------------------------------------------------------------
# ACLED conflict normalizer
# ---------------------------------------------------------------------------

def _normalize_acled(raw: dict[str, Any]) -> list[CanonicalBase]:
    """Normalize ACLED-style conflict event to canonical Incident."""
    fatalities = int(raw.get("fatalities", 0))
    if fatalities == 0:
        severity, score = SeverityLevel.LOW, 0.2
    elif fatalities <= 5:
        severity, score = SeverityLevel.MEDIUM, 0.5
    elif fatalities <= 20:
        severity, score = SeverityLevel.HIGH, 0.75
    else:
        severity, score = SeverityLevel.CRITICAL, 0.95

    location = None
    if raw.get("latitude") and raw.get("longitude"):
        location = GeoPoint(lat=float(raw["latitude"]), lng=float(raw["longitude"]))

    event_type_map = {
        "Battles": "conflict",
        "Violence against civilians": "conflict",
        "Explosions/Remote violence": "conflict",
        "Riots": "security",
        "Protests": "political",
        "Strategic developments": "political",
    }

    return [Incident(
        title=raw.get("event_type", "Unknown Event"),
        description=raw.get("notes", ""),
        event_type=event_type_map.get(raw.get("event_type", ""), "conflict"),
        severity=severity,
        severity_score=score,
        location=location,
        start_time=_parse_date(raw.get("event_date")),
        active=True,
        fatalities=fatalities,
        provenance=Provenance(
            source_type=SourceType.CONFLICT,
            source_name="acled",
            source_id=str(raw.get("data_id", "")),
            raw_payload=raw,
        ),
        confidence=ConfidenceMeta(
            score=0.7,
            source_quality=0.75,
            corroboration_count=int(raw.get("source_count", 1)),
            data_freshness=1.0,
        ),
        tags=[raw.get("event_type", ""), raw.get("country", "")],
    )]


# ---------------------------------------------------------------------------
# GlobalIncidentMap normalizer
# ---------------------------------------------------------------------------

def _normalize_global_incident(raw: dict[str, Any]) -> list[CanonicalBase]:
    """Normalize GlobalIncidentMap record to canonical Incident."""
    severity_map = {
        "critical": (SeverityLevel.CRITICAL, 0.9),
        "high": (SeverityLevel.HIGH, 0.7),
        "medium": (SeverityLevel.MEDIUM, 0.5),
        "low": (SeverityLevel.LOW, 0.25),
    }
    sev_str = raw.get("severity_level", "medium").lower()
    severity, score = severity_map.get(sev_str, (SeverityLevel.MEDIUM, 0.5))

    location = None
    if raw.get("lat") and raw.get("lng"):
        location = GeoPoint(lat=float(raw["lat"]), lng=float(raw["lng"]))

    return [Incident(
        title=raw.get("title", "Global Incident"),
        description=raw.get("description", ""),
        event_type=raw.get("category", "unknown"),
        severity=severity,
        severity_score=score,
        location=location,
        active=True,
        fatalities=raw.get("fatalities", 0),
        provenance=Provenance(
            source_type=SourceType.GLOBAL_INCIDENT,
            source_name="global_incident_map",
            source_id=str(raw.get("id", "")),
            raw_payload=raw,
        ),
        confidence=ConfidenceMeta(
            score=0.6,
            source_quality=0.65,
            corroboration_count=1,
            data_freshness=0.9,
        ),
        tags=[raw.get("category", "")],
    )]


# ---------------------------------------------------------------------------
# Aviation normalizer
# ---------------------------------------------------------------------------

def _normalize_aviation(raw: dict[str, Any]) -> list[CanonicalBase]:
    """Normalize aviation record to canonical Flight."""
    location = None
    if raw.get("latitude") and raw.get("longitude"):
        location = GeoPoint(lat=float(raw["latitude"]), lng=float(raw["longitude"]))

    return [Flight(
        flight_number=raw.get("flight_number", raw.get("callsign", "UNKN")),
        airline=raw.get("airline", ""),
        origin_airport=raw.get("origin", raw.get("origin_airport_id", "")),
        destination_airport=raw.get("destination", raw.get("destination_airport_id", "")),
        status=raw.get("status", "unknown"),
        location=location,
        altitude_ft=raw.get("altitude_ft"),
        speed_knots=raw.get("speed_knots"),
        heading=raw.get("heading"),
        provenance=Provenance(
            source_type=SourceType.AVIATION,
            source_name="aviation_feed",
            source_id=str(raw.get("id", raw.get("flight_number", ""))),
            raw_payload=raw,
        ),
        confidence=ConfidenceMeta(score=0.85, source_quality=0.9),
    )]


# ---------------------------------------------------------------------------
# Maritime normalizer
# ---------------------------------------------------------------------------

def _normalize_maritime(raw: dict[str, Any]) -> list[CanonicalBase]:
    """Normalize AIS/maritime record to canonical Vessel."""
    location = None
    if raw.get("latitude") and raw.get("longitude"):
        location = GeoPoint(lat=float(raw["latitude"]), lng=float(raw["longitude"]))

    return [Vessel(
        name=raw.get("name", raw.get("vessel_name", "Unknown")),
        mmsi=raw.get("mmsi", ""),
        imo=raw.get("imo"),
        vessel_type=raw.get("vessel_type", raw.get("type", "cargo")),
        flag_state=raw.get("flag_state", raw.get("flag", "")),
        location=location,
        speed_knots=raw.get("speed_knots", raw.get("speed")),
        heading=raw.get("heading"),
        destination_port=raw.get("destination_port_id", raw.get("destination", "")),
        provenance=Provenance(
            source_type=SourceType.MARITIME,
            source_name="ais_feed",
            source_id=str(raw.get("mmsi", raw.get("id", ""))),
            raw_payload=raw,
        ),
        confidence=ConfidenceMeta(score=0.8, source_quality=0.85),
    )]


# ---------------------------------------------------------------------------
# Main normalizer
# ---------------------------------------------------------------------------

_NORMALIZERS = {
    "acled": _normalize_acled,
    "global_incident_map": _normalize_global_incident,
    "aviation": _normalize_aviation,
    "maritime": _normalize_maritime,
}


def normalize_record(raw: dict[str, Any], source_hint: str | None = None) -> list[CanonicalBase]:
    """Normalize a single raw record into canonical entities.

    Args:
        raw: Raw record dict from any source.
        source_hint: Optional source type hint. If None, auto-detected.

    Returns:
        List of canonical entities (usually 1, but some sources produce multiple).
    """
    source = source_hint or _detect_source(raw)
    normalizer = _NORMALIZERS.get(source)
    if normalizer is None:
        return []
    return normalizer(raw)


def normalize_batch(
    records: list[dict[str, Any]],
    source_hint: str | None = None,
) -> list[CanonicalBase]:
    """Normalize a batch of raw records."""
    results: list[CanonicalBase] = []
    for raw in records:
        results.extend(normalize_record(raw, source_hint))
    return results


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_date(date_str: str | None) -> datetime | None:
    if not date_str:
        return None
    for fmt in ("%Y-%m-%d", "%d %B %Y", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    return None
