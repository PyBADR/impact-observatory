"""
Impact Observatory | مرصد الأثر
Signal Ingestion Service — read-only signal snapshot processing.

This service:
  - Accepts raw signal inputs (static/sample in v2)
  - Normalizes them into typed SignalSnapshot records
  - Calculates freshness based on published_at vs ingestion time
  - Assigns confidence based on source weight and freshness
  - NEVER modifies scenario calculations or engine outputs

All functions are pure — no side effects, no I/O, no state mutation.
"""
from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Optional

from src.signal_ingestion.models import (
    SignalSource,
    SignalSnapshot,
    SnapshotFreshness,
    SAMPLE_SIGNAL_SOURCES,
)
from src.signal_ingestion.audit_log import (
    SignalAuditLog,
    SignalAuditAction,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Freshness calculation
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_freshness(
    published_at: str,
    ingested_at: str,
    refresh_frequency_minutes: int,
) -> SnapshotFreshness:
    """Classify freshness based on age relative to expected refresh.

    Parameters
    ----------
    published_at : str
        ISO-8601 timestamp from the source.
    ingested_at : str
        ISO-8601 timestamp when the snapshot was captured.
    refresh_frequency_minutes : int
        Expected refresh interval of the source in minutes.
        If 0, freshness is UNKNOWN (static/manual source).

    Returns
    -------
    SnapshotFreshness
        FRESH / RECENT / STALE / EXPIRED / UNKNOWN
    """
    if refresh_frequency_minutes <= 0:
        return SnapshotFreshness.UNKNOWN

    try:
        pub = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        ing = datetime.fromisoformat(ingested_at.replace("Z", "+00:00"))
    except (ValueError, AttributeError):
        return SnapshotFreshness.UNKNOWN

    age_minutes = (ing - pub).total_seconds() / 60.0

    if age_minutes < 0:
        # Published in the future — treat as fresh (clock skew)
        return SnapshotFreshness.FRESH

    ratio = age_minutes / refresh_frequency_minutes

    if ratio <= 1.0:
        return SnapshotFreshness.FRESH
    elif ratio <= 2.0:
        return SnapshotFreshness.RECENT
    elif ratio <= 5.0:
        return SnapshotFreshness.STALE
    else:
        return SnapshotFreshness.EXPIRED


# ═══════════════════════════════════════════════════════════════════════════════
# Confidence calculation
# ═══════════════════════════════════════════════════════════════════════════════

def calculate_confidence(
    source_confidence_weight: float,
    freshness: SnapshotFreshness,
) -> float:
    """Compute snapshot confidence from source weight and freshness.

    Parameters
    ----------
    source_confidence_weight : float
        Base confidence from the SignalSource (0.0–1.0).
    freshness : SnapshotFreshness
        Freshness classification of the snapshot.

    Returns
    -------
    float
        Computed confidence (0.0–1.0), penalized by staleness.
    """
    freshness_multiplier = {
        SnapshotFreshness.FRESH: 1.0,
        SnapshotFreshness.RECENT: 0.85,
        SnapshotFreshness.STALE: 0.60,
        SnapshotFreshness.EXPIRED: 0.30,
        SnapshotFreshness.UNKNOWN: 0.50,
    }
    mult = freshness_multiplier.get(freshness, 0.50)
    return round(min(1.0, max(0.0, source_confidence_weight * mult)), 4)


# ═══════════════════════════════════════════════════════════════════════════════
# Snapshot normalization
# ═══════════════════════════════════════════════════════════════════════════════

def _generate_snapshot_id(source_id: str, title: str, published_at: str) -> str:
    """Generate a deterministic snapshot ID from content."""
    raw = f"{source_id}|{title}|{published_at}"
    return f"snap_{hashlib.sha256(raw.encode()).hexdigest()[:16]}"


def normalize_snapshot(
    raw_input: dict[str, Any],
    source: SignalSource,
    ingested_at: Optional[str] = None,
) -> SignalSnapshot:
    """Normalize a raw signal input into a typed SignalSnapshot.

    Parameters
    ----------
    raw_input : dict
        Raw signal data with at least 'title' and 'published_at'.
    source : SignalSource
        The registered source this signal came from.
    ingested_at : str | None
        Override ingestion timestamp (ISO-8601). Defaults to now.

    Returns
    -------
    SignalSnapshot
        Normalized, immutable snapshot record.
    """
    now = ingested_at or datetime.now(timezone.utc).isoformat()
    title = str(raw_input.get("title", "Untitled Signal"))
    published = str(raw_input.get("published_at", now))

    freshness = calculate_freshness(
        published_at=published,
        ingested_at=now,
        refresh_frequency_minutes=source.refresh_frequency_minutes,
    )
    confidence = calculate_confidence(source.confidence_weight, freshness)

    return SignalSnapshot(
        snapshot_id=_generate_snapshot_id(source.source_id, title, published),
        source_id=source.source_id,
        title=title,
        summary=str(raw_input.get("summary", "")),
        url=raw_input.get("url"),
        published_at=published,
        ingested_at=now,
        freshness_status=freshness,
        confidence_score=confidence,
        related_scenarios=list(raw_input.get("related_scenarios", [])),
        related_countries=list(raw_input.get("related_countries", [])),
        related_sectors=list(raw_input.get("related_sectors", [])),
        raw_metadata={
            k: v for k, v in raw_input.items()
            if k not in {
                "title", "summary", "url", "published_at",
                "related_scenarios", "related_countries", "related_sectors",
            }
        },
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Batch ingestion
# ═══════════════════════════════════════════════════════════════════════════════

def ingest_signals(
    raw_inputs: list[dict[str, Any]],
    source_id: str,
    audit_log: Optional[SignalAuditLog] = None,
    ingested_at: Optional[str] = None,
) -> list[SignalSnapshot]:
    """Ingest a batch of raw signals from a source.

    Parameters
    ----------
    raw_inputs : list[dict]
        List of raw signal dicts.
    source_id : str
        The source_id to look up in SAMPLE_SIGNAL_SOURCES.
    audit_log : SignalAuditLog | None
        Optional audit log to record ingestion events.
    ingested_at : str | None
        Override ingestion timestamp for all snapshots.

    Returns
    -------
    list[SignalSnapshot]
        Normalized snapshots. Empty list if source not found or disabled.
    """
    source = SAMPLE_SIGNAL_SOURCES.get(source_id)

    if source is None:
        if audit_log:
            audit_log.record(
                action=SignalAuditAction.SOURCE_FAILED,
                source_id=source_id,
                detail=f"Source '{source_id}' not found in registry.",
            )
        return []

    if not source.enabled:
        if audit_log:
            audit_log.record(
                action=SignalAuditAction.FALLBACK_USED,
                source_id=source_id,
                detail=f"Source '{source.name}' is disabled. Returning empty.",
            )
        return []

    if audit_log:
        audit_log.record(
            action=SignalAuditAction.SOURCE_CHECKED,
            source_id=source_id,
            detail=f"Source '{source.name}' checked. {len(raw_inputs)} signals to ingest.",
        )

    snapshots: list[SignalSnapshot] = []
    for raw in raw_inputs:
        try:
            snap = normalize_snapshot(raw, source, ingested_at)
            snapshots.append(snap)
            if audit_log:
                audit_log.record(
                    action=SignalAuditAction.SNAPSHOT_CREATED,
                    source_id=source_id,
                    snapshot_id=snap.snapshot_id,
                    detail=f"Snapshot created: '{snap.title}' (confidence={snap.confidence_score})",
                )
        except Exception as exc:
            if audit_log:
                audit_log.record(
                    action=SignalAuditAction.SOURCE_FAILED,
                    source_id=source_id,
                    detail=f"Failed to normalize signal: {exc}",
                )

    return snapshots


# ═══════════════════════════════════════════════════════════════════════════════
# Sample signals — static data for development/testing
# ═══════════════════════════════════════════════════════════════════════════════

SAMPLE_RAW_SIGNALS: list[dict[str, Any]] = [
    {
        "title": "Brent crude rises 3% on Hormuz tension reports",
        "summary": "Oil prices climbed after reports of increased military "
                   "activity near the Strait of Hormuz. Analysts warn of "
                   "potential supply disruption to 20% of global oil transit.",
        "url": "https://example.com/energy/brent-hormuz-2026",
        "published_at": "2026-04-10T08:30:00Z",
        "related_scenarios": ["hormuz_chokepoint_disruption", "energy_market_volatility_shock"],
        "related_countries": ["UAE", "SAUDI", "QATAR"],
        "related_sectors": ["energy", "maritime"],
        "source_label": "Reuters Energy",
    },
    {
        "title": "CBUAE holds rates steady, flags regional liquidity tightening",
        "summary": "The Central Bank of the UAE maintained its benchmark rate "
                   "but warned of tightening liquidity across GCC interbank markets, "
                   "citing elevated geopolitical uncertainty.",
        "url": "https://example.com/finance/cbuae-rates-2026",
        "published_at": "2026-04-12T14:00:00Z",
        "related_scenarios": ["uae_banking_crisis", "regional_liquidity_stress_event"],
        "related_countries": ["UAE"],
        "related_sectors": ["banking", "fintech"],
        "source_label": "GCC Central Banks",
    },
    {
        "title": "Qatar LNG shipments rerouted via Cape of Good Hope",
        "summary": "Several Qatar LNG carriers diverted from the Red Sea route "
                   "to the Cape of Good Hope corridor, adding 12-15 days transit "
                   "time and $2-4M per voyage in additional costs.",
        "url": "https://example.com/shipping/qatar-lng-reroute",
        "published_at": "2026-04-08T11:15:00Z",
        "related_scenarios": ["qatar_lng_disruption", "red_sea_trade_corridor_instability"],
        "related_countries": ["QATAR"],
        "related_sectors": ["energy", "maritime", "logistics"],
        "source_label": "Maritime Intelligence",
    },
]
