"""Real-time Data Feeds Service — Impact Observatory.

Connects to external data sources with graceful fallback to seed data:

  1. ACLED Conflict API   → /api/v1/events (geopolitical events)
  2. AISStream.io         → /api/v1/vessels (maritime tracking)
  3. OpenSky Network      → /api/v1/flights (aviation)

All feeds are optional — system operates on seed data if APIs unavailable.
Config via environment variables:
  ACLED_API_KEY, ACLED_EMAIL
  AISSTREAM_API_KEY
  OPENSKY_USERNAME, OPENSKY_PASSWORD

Data is fetched on startup and refreshed every FEED_REFRESH_MINUTES (default: 15).
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any

logger = logging.getLogger(__name__)

# Config from env
ACLED_API_KEY = os.getenv("ACLED_API_KEY", "")
ACLED_EMAIL = os.getenv("ACLED_EMAIL", "")
AISSTREAM_API_KEY = os.getenv("AISSTREAM_API_KEY", "")
OPENSKY_USERNAME = os.getenv("OPENSKY_USERNAME", "")
OPENSKY_PASSWORD = os.getenv("OPENSKY_PASSWORD", "")
FEED_REFRESH_MINUTES = int(os.getenv("FEED_REFRESH_MINUTES", "15"))

# GCC bounding box for filtering
GCC_BBOX = {
    "min_lat": 12.0, "max_lat": 32.0,
    "min_lng": 35.0, "max_lng": 63.0,
}

# Feed status tracking
_feed_status: dict[str, dict] = {
    "acled": {"status": "unconfigured", "last_fetch": None, "count": 0, "error": None},
    "aisstream": {"status": "unconfigured", "last_fetch": None, "count": 0, "error": None},
    "opensky": {"status": "unconfigured", "last_fetch": None, "count": 0, "error": None},
}


async def fetch_acled_events(limit: int = 100) -> list[dict]:
    """Fetch recent GCC conflict events from ACLED API.

    ACLED API: https://api.acleddata.com/acled/read
    Requires ACLED_API_KEY + ACLED_EMAIL env vars.

    Returns list of canonical event dicts.
    """
    if not ACLED_API_KEY or not ACLED_EMAIL:
        _feed_status["acled"]["status"] = "unconfigured"
        return []

    try:
        import aiohttp
        cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
        params = {
            "key": ACLED_API_KEY,
            "email": ACLED_EMAIL,
            "region": "Middle East",
            "event_date": cutoff,
            "event_date_where": "BETWEEN",
            "event_date_to": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
            "limit": limit,
            "format": "json",
            "fields": "event_id_cnty|event_date|event_type|sub_event_type|actor1|country|admin1|latitude|longitude|notes|fatalities|source|timestamp",
        }
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get("https://api.acleddata.com/acled/read", params=params) as resp:
                if resp.status != 200:
                    raise ValueError(f"ACLED returned {resp.status}")
                data = await resp.json()

        events = []
        for row in data.get("data", []):
            lat = float(row.get("latitude", 0) or 0)
            lng = float(row.get("longitude", 0) or 0)
            if not (GCC_BBOX["min_lat"] <= lat <= GCC_BBOX["max_lat"] and
                    GCC_BBOX["min_lng"] <= lng <= GCC_BBOX["max_lng"]):
                continue

            fatalities = int(row.get("fatalities", 0) or 0)
            severity = min(1.0, 0.2 + fatalities * 0.04 + (0.3 if "Explosion" in row.get("event_type", "") else 0))

            events.append({
                "id": f"acled_{row['event_id_cnty']}",
                "title": f"{row.get('event_type', 'Event')} — {row.get('admin1', row.get('country', ''))}",
                "event_type": _map_acled_type(row.get("event_type", "")),
                "severity_score": severity,
                "confidence": 0.85,
                "lat": lat,
                "lng": lng,
                "description": (row.get("notes", "") or "")[:500],
                "source_type": "acled",
                "source_name": row.get("source", "ACLED"),
                "is_kinetic": fatalities > 0 or "Explosion" in row.get("event_type", ""),
                "created_at": row.get("event_date", ""),
            })

        _feed_status["acled"].update({"status": "ok", "last_fetch": datetime.now(timezone.utc).isoformat(), "count": len(events), "error": None})
        logger.info("ACLED: fetched %d GCC events", len(events))
        return events

    except ImportError:
        _feed_status["acled"].update({"status": "no_aiohttp", "error": "aiohttp not installed"})
        return []
    except Exception as e:
        _feed_status["acled"].update({"status": "error", "error": str(e)[:200]})
        logger.warning("ACLED fetch failed: %s", e)
        return []


def _map_acled_type(acled_type: str) -> str:
    """Map ACLED event types to observatory types."""
    mapping = {
        "Battles": "armed_conflict",
        "Explosions/Remote violence": "airspace_strike",
        "Violence against civilians": "threat",
        "Protests": "protest_civil_unrest",
        "Riots": "protest_civil_unrest",
        "Strategic developments": "diplomatic_tension",
    }
    return mapping.get(acled_type, "threat")


async def fetch_aisstream_vessels(limit: int = 50) -> list[dict]:
    """Fetch GCC vessel positions from AISStream.io.

    AISStream WebSocket API: wss://stream.aisstream.io/v0/stream
    Requires AISSTREAM_API_KEY env var.

    Returns list of canonical vessel dicts.
    """
    if not AISSTREAM_API_KEY:
        _feed_status["aisstream"]["status"] = "unconfigured"
        return []

    vessels = []
    try:
        import aiohttp
        import json

        subscribe_msg = {
            "APIKey": AISSTREAM_API_KEY,
            "BoundingBoxes": [[
                [GCC_BBOX["min_lat"], GCC_BBOX["min_lng"]],
                [GCC_BBOX["max_lat"], GCC_BBOX["max_lng"]],
            ]],
            "FiltersShipMMSI": [],
            "FilterMessageTypes": ["PositionReport"],
        }

        seen_mmsi = set()
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(
                "wss://stream.aisstream.io/v0/stream",
                timeout=aiohttp.ClientTimeout(total=8),
            ) as ws:
                await ws.send_str(json.dumps(subscribe_msg))
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        try:
                            data = json.loads(msg.data)
                            pos = data.get("Message", {}).get("PositionReport", {})
                            meta = data.get("MetaData", {})
                            mmsi = str(meta.get("MMSI", ""))
                            if mmsi and mmsi not in seen_mmsi:
                                seen_mmsi.add(mmsi)
                                vessels.append({
                                    "id": f"ais_{mmsi}",
                                    "name": meta.get("ShipName", f"Vessel_{mmsi}").strip(),
                                    "mmsi": mmsi,
                                    "vessel_type": _map_ais_type(pos.get("SpecialManoeuvreIndicator", 0)),
                                    "latitude": pos.get("Latitude"),
                                    "longitude": pos.get("Longitude"),
                                    "speed_knots": pos.get("SpeedOverGround"),
                                    "heading": pos.get("TrueHeading"),
                                    "source_type": "aisstream",
                                })
                        except Exception:
                            pass
                    if len(vessels) >= limit:
                        break

        _feed_status["aisstream"].update({"status": "ok", "last_fetch": datetime.now(timezone.utc).isoformat(), "count": len(vessels), "error": None})
        logger.info("AISStream: fetched %d GCC vessels", len(vessels))
        return vessels

    except ImportError:
        _feed_status["aisstream"].update({"status": "no_aiohttp", "error": "aiohttp not installed"})
        return []
    except Exception as e:
        _feed_status["aisstream"].update({"status": "error", "error": str(e)[:200]})
        logger.warning("AISStream fetch failed: %s", e)
        return []


def _map_ais_type(indicator: int) -> str:
    if indicator == 1:
        return "tanker"
    if indicator == 2:
        return "cargo"
    return "cargo"


async def fetch_opensky_flights(limit: int = 50) -> list[dict]:
    """Fetch GCC flight positions from OpenSky Network REST API.

    API: https://opensky-network.org/api/states/all
    Optional: OPENSKY_USERNAME + OPENSKY_PASSWORD for higher rate limits.
    """
    try:
        import aiohttp
        params = {
            "lamin": GCC_BBOX["min_lat"],
            "lomin": GCC_BBOX["min_lng"],
            "lamax": GCC_BBOX["max_lat"],
            "lomax": GCC_BBOX["max_lng"],
        }
        auth = None
        if OPENSKY_USERNAME and OPENSKY_PASSWORD:
            auth = aiohttp.BasicAuth(OPENSKY_USERNAME, OPENSKY_PASSWORD)

        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
            async with session.get("https://opensky-network.org/api/states/all", params=params, auth=auth) as resp:
                if resp.status == 429:
                    _feed_status["opensky"].update({"status": "rate_limited"})
                    return []
                if resp.status != 200:
                    raise ValueError(f"OpenSky returned {resp.status}")
                data = await resp.json()

        flights = []
        for state in (data.get("states") or [])[:limit]:
            # OpenSky state vector: [icao24, callsign, origin_country, time_position, last_contact,
            #                         longitude, latitude, baro_altitude, on_ground, velocity, ...]
            if len(state) < 10 or state[8]:  # skip ground
                continue
            flights.append({
                "id": f"os_{state[0]}",
                "flight_number": (state[1] or "").strip() or state[0],
                "status": "airborne",
                "origin_airport_id": state[2] or "unknown",
                "destination_airport_id": "unknown",
                "latitude": state[6],
                "longitude": state[5],
                "altitude_ft": (state[7] or 0) * 3.28084 if state[7] else None,
                "speed_knots": (state[9] or 0) * 1.944,
                "source_type": "opensky",
            })

        _feed_status["opensky"].update({"status": "ok", "last_fetch": datetime.now(timezone.utc).isoformat(), "count": len(flights), "error": None})
        logger.info("OpenSky: fetched %d GCC flights", len(flights))
        return flights

    except ImportError:
        _feed_status["opensky"].update({"status": "no_aiohttp", "error": "aiohttp not installed"})
        return []
    except Exception as e:
        _feed_status["opensky"].update({"status": "error", "error": str(e)[:200]})
        logger.warning("OpenSky fetch failed: %s", e)
        return []


async def refresh_all_feeds(state) -> None:
    """Refresh all feeds and update state. Called on startup and periodically."""
    results = await asyncio.gather(
        fetch_acled_events(100),
        fetch_aisstream_vessels(50),
        fetch_opensky_flights(50),
        return_exceptions=True,
    )

    acled_events, ais_vessels, opensky_flights = results

    if isinstance(acled_events, list) and acled_events:
        state.events = acled_events + [e for e in state.events if not e.get("id", "").startswith("acled_")]
        logger.info("Feeds: injected %d ACLED events", len(acled_events))

    if isinstance(ais_vessels, list) and ais_vessels:
        state.vessels = ais_vessels + [v for v in state.vessels if not v.get("id", "").startswith("ais_")]
        logger.info("Feeds: injected %d AIS vessels", len(ais_vessels))

    if isinstance(opensky_flights, list) and opensky_flights:
        state.flights = opensky_flights + [f for f in state.flights if not f.get("id", "").startswith("os_")]
        logger.info("Feeds: injected %d OpenSky flights", len(opensky_flights))


def get_feed_status() -> dict:
    """Return current status of all feeds."""
    return {
        "feeds": _feed_status,
        "config": {
            "acled_configured": bool(ACLED_API_KEY and ACLED_EMAIL),
            "aisstream_configured": bool(AISSTREAM_API_KEY),
            "opensky_configured": bool(OPENSKY_USERNAME),
            "refresh_minutes": FEED_REFRESH_MINUTES,
        },
    }
