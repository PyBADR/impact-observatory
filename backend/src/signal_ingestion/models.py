"""
Impact Observatory | مرصد الأثر
Signal Ingestion Models — typed data models for signal sources and snapshots.

These models are read-only data containers. They do NOT interact with
the simulation engine or modify any scenario outputs.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════

class SignalSourceType(str, Enum):
    """Classification of signal source origin."""
    RSS = "rss"                # RSS/Atom news feed
    API = "api"                # REST/GraphQL external API
    MARKET = "market"          # Market data feed (futures, FX, commodities)
    GOVERNMENT = "government"  # Government statistical agency
    MANUAL = "manual"          # Analyst-entered signal


class SnapshotFreshness(str, Enum):
    """Freshness classification of an ingested signal snapshot."""
    FRESH = "fresh"            # Ingested within the expected refresh window
    RECENT = "recent"          # Slightly past refresh window but usable
    STALE = "stale"            # Past expected window, confidence degraded
    EXPIRED = "expired"        # Too old to use, should be discarded
    UNKNOWN = "unknown"        # Cannot determine (source unavailable)


# ═══════════════════════════════════════════════════════════════════════════════
# SignalSource — registry entry for a data feed
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SignalSource:
    """A registered external signal source.

    This is a registry entry, not a connection. The source may or may
    not be enabled. When enabled=False, the ingestion service skips it.
    """
    source_id: str
    name: str
    source_type: SignalSourceType
    url: Optional[str]
    refresh_frequency_minutes: int       # Expected refresh interval
    confidence_weight: float             # 0.0–1.0 base confidence
    enabled: bool                        # Whether ingestion should attempt this source
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "source_type": self.source_type.value,
            "url": self.url,
            "refresh_frequency_minutes": self.refresh_frequency_minutes,
            "confidence_weight": self.confidence_weight,
            "enabled": self.enabled,
            "notes": self.notes,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# SignalSnapshot — a single ingested signal record
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SignalSnapshot:
    """A single snapshot of an ingested external signal.

    Snapshots are immutable records. They capture a point-in-time
    observation from an external source. They are NEVER used to
    modify scenario calculations in v2.
    """
    snapshot_id: str
    source_id: str
    title: str
    summary: str
    url: Optional[str]
    published_at: str                    # ISO-8601 from source
    ingested_at: str                     # ISO-8601 when we captured it
    freshness_status: SnapshotFreshness
    confidence_score: float              # 0.0–1.0 computed confidence
    related_scenarios: list[str] = field(default_factory=list)
    related_countries: list[str] = field(default_factory=list)
    related_sectors: list[str] = field(default_factory=list)
    raw_metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "source_id": self.source_id,
            "title": self.title,
            "summary": self.summary,
            "url": self.url,
            "published_at": self.published_at,
            "ingested_at": self.ingested_at,
            "freshness_status": self.freshness_status.value,
            "confidence_score": round(self.confidence_score, 4),
            "related_scenarios": self.related_scenarios,
            "related_countries": self.related_countries,
            "related_sectors": self.related_sectors,
            "raw_metadata": self.raw_metadata,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Sample Sources — static registry for v2 (not connected)
# ═══════════════════════════════════════════════════════════════════════════════

SAMPLE_SIGNAL_SOURCES: dict[str, SignalSource] = {
    "sig_reuters_energy": SignalSource(
        source_id="sig_reuters_energy",
        name="Reuters Energy News (GCC)",
        source_type=SignalSourceType.RSS,
        url="https://www.reuters.com/business/energy/",
        refresh_frequency_minutes=60,
        confidence_weight=0.80,
        enabled=False,
        notes="RSS feed for GCC energy news. NOT connected in v2.",
    ),
    "sig_brent_futures": SignalSource(
        source_id="sig_brent_futures",
        name="Brent Crude Futures (ICE)",
        source_type=SignalSourceType.MARKET,
        url="https://www.ice.com/products/219/Brent-Crude-Futures",
        refresh_frequency_minutes=15,
        confidence_weight=0.90,
        enabled=False,
        notes="ICE Brent crude futures. NOT connected in v2. "
              "Would provide real-time price signals for energy scenarios.",
    ),
    "sig_eia_weekly": SignalSource(
        source_id="sig_eia_weekly",
        name="EIA Weekly Petroleum Status Report",
        source_type=SignalSourceType.GOVERNMENT,
        url="https://www.eia.gov/petroleum/supply/weekly/",
        refresh_frequency_minutes=10080,  # weekly
        confidence_weight=0.85,
        enabled=False,
        notes="U.S. EIA weekly report. NOT connected in v2. "
              "Would calibrate energy scenario base_loss_usd.",
    ),
    "sig_gcc_central_banks": SignalSource(
        source_id="sig_gcc_central_banks",
        name="GCC Central Bank Announcements",
        source_type=SignalSourceType.RSS,
        url=None,
        refresh_frequency_minutes=1440,  # daily
        confidence_weight=0.75,
        enabled=False,
        notes="Aggregated GCC central bank news. NOT connected in v2. "
              "Would feed banking/liquidity scenario severity.",
    ),
    "sig_maritime_ais": SignalSource(
        source_id="sig_maritime_ais",
        name="AIS Vessel Traffic — Strait of Hormuz",
        source_type=SignalSourceType.API,
        url=None,
        refresh_frequency_minutes=30,
        confidence_weight=0.70,
        enabled=False,
        notes="AIS maritime traffic data. NOT connected in v2. "
              "Would validate Hormuz scenario severity against live vessel counts.",
    ),
    "sig_sample_static": SignalSource(
        source_id="sig_sample_static",
        name="Sample Static Signals (Development)",
        source_type=SignalSourceType.MANUAL,
        url=None,
        refresh_frequency_minutes=0,
        confidence_weight=0.50,
        enabled=True,
        notes="Static sample signals for development and testing. "
              "The only enabled source in v2.",
    ),
}
