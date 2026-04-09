"""Signal Intelligence Layer — Signal Mapper.

Maps RawFeedItem → MacroSignalInput (Pack 1 intake contract).

This is the critical bridge between the feed layer and the existing
Pack 1 pipeline. Every mapped signal must be a valid MacroSignalInput
that passes Pack 1 validation.

Mapping rules:
  1. Enrich item (classify, extract regions/domains, score severity)
  2. Title → title (required, min 5 chars)
  3. Description → description
  4. Feed source → SignalSource (content-aware override via signal_type)
  5. Severity hint → severity_score (enriched, clamped [0,1])
  6. Direction hint → SignalDirection
  7. Region hints → GCCRegion list (enriched, validated against enum)
  8. Domain hints → ImpactDomain list (enriched, validated against enum)
  9. Confidence → SignalConfidence (validated against enum)
  10. Tags → tags (from feed config + item categories)

No LLM inference. Pure rule-based mapping with enrichment.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalDirection,
    SignalSource,
    SignalType,
)
from src.macro.macro_schemas import MacroSignalInput
from src.signal_intel.dictionaries import (
    REGION_ALIASES,
    DOMAIN_ALIASES,
    SIGNAL_TYPE_TO_SOURCE,
)
from src.signal_intel.enrichment import enrich_feed_item
from src.signal_intel.types import FeedType, RawFeedItem

logger = logging.getLogger("signal_intel.mapper")


# ── Region Resolution ───────────────────────────────────────────────────────
# Now uses expanded REGION_ALIASES from dictionaries.py

def _resolve_regions(hints: list[str]) -> list[GCCRegion]:
    """Resolve region hints into validated GCCRegion list."""
    regions: set[GCCRegion] = set()
    for hint in hints:
        h = hint.strip().lower()
        if h in REGION_ALIASES:
            regions.add(REGION_ALIASES[h])
        else:
            # Try enum value match (e.g., "SA", "AE")
            for member in GCCRegion:
                if member.value.lower() == h:
                    regions.add(member)
                    break

    return list(regions) if regions else [GCCRegion.GCC_WIDE]


# ── Domain Resolution ───────────────────────────────────────────────────────
# Now uses expanded DOMAIN_ALIASES from dictionaries.py
# DOMAIN_ALIASES maps to string values; resolve to ImpactDomain enum here.

_DOMAIN_ENUM_MAP: dict[str, ImpactDomain] = {
    member.value: member for member in ImpactDomain
}


def _resolve_domains(hints: list[str]) -> list[ImpactDomain]:
    """Resolve domain hints into validated ImpactDomain list."""
    domains: set[ImpactDomain] = set()
    for hint in hints:
        h = hint.strip().lower()
        # First try expanded aliases → string → enum
        if h in DOMAIN_ALIASES:
            domain_value = DOMAIN_ALIASES[h]
            if domain_value in _DOMAIN_ENUM_MAP:
                domains.add(_DOMAIN_ENUM_MAP[domain_value])
        else:
            # Direct enum value match
            if h in _DOMAIN_ENUM_MAP:
                domains.add(_DOMAIN_ENUM_MAP[h])
    return list(domains)


# ── Source Mapping ──────────────────────────────────────────────────────────

_FEED_TYPE_TO_SOURCE: dict[FeedType, SignalSource] = {
    FeedType.RSS: SignalSource.GEOPOLITICAL,  # fallback, overridden by content
    FeedType.JSON_API: SignalSource.MARKET,
    FeedType.ECONOMIC: SignalSource.ECONOMIC,
}

_SIGNAL_TYPE_MAP: dict[str, SignalType] = {
    "geopolitical": SignalType.GEOPOLITICAL,
    "policy": SignalType.POLICY,
    "market": SignalType.MARKET,
    "commodity": SignalType.COMMODITY,
    "regulatory": SignalType.REGULATORY,
    "logistics": SignalType.LOGISTICS,
    "sentiment": SignalType.SENTIMENT,
    "systemic": SignalType.SYSTEMIC,
}

_DIRECTION_MAP: dict[str, SignalDirection] = {
    "positive": SignalDirection.POSITIVE,
    "negative": SignalDirection.NEGATIVE,
    "neutral": SignalDirection.NEUTRAL,
    "ambiguous": SignalDirection.AMBIGUOUS,
    "mixed": SignalDirection.MIXED,
    "uncertain": SignalDirection.UNCERTAIN,
}

_CONFIDENCE_MAP: dict[str, SignalConfidence] = {
    "verified": SignalConfidence.VERIFIED,
    "high": SignalConfidence.HIGH,
    "moderate": SignalConfidence.MODERATE,
    "low": SignalConfidence.LOW,
    "unverified": SignalConfidence.UNVERIFIED,
}


# ── Main Mapper ─────────────────────────────────────────────────────────────

def map_feed_item(item: RawFeedItem) -> MacroSignalInput | None:
    """Map a RawFeedItem to a MacroSignalInput.

    Now applies enrichment before mapping:
      1. enrich_feed_item() — classify, extract regions/domains, score severity
      2. _do_map() — resolve enums, build MacroSignalInput

    Returns None if the item cannot be mapped (e.g., title too short).
    Never throws — mapping failures return None.
    """
    try:
        # Apply enrichment before mapping
        enrich_feed_item(item)
        return _do_map(item)
    except Exception as exc:
        logger.warning(
            "Mapper failed for feed=%s item=%s: %s",
            item.feed_id, item.item_id, exc,
        )
        return None


def _do_map(item: RawFeedItem) -> MacroSignalInput | None:
    """Internal mapping logic."""
    # Title validation
    title = item.title.strip()
    if len(title) < 5:
        logger.debug("Skipping item with short title: %r", title)
        return None

    # Source — content-aware override via enriched signal_type
    # ECONOMIC feeds retain their source (data provenance) — override only RSS/JSON_API
    source = _FEED_TYPE_TO_SOURCE.get(item.feed_type, SignalSource.GEOPOLITICAL)
    if (
        item.feed_type != FeedType.ECONOMIC
        and item.signal_type_hint
        and item.signal_type_hint in SIGNAL_TYPE_TO_SOURCE
    ):
        new_source = SIGNAL_TYPE_TO_SOURCE[item.signal_type_hint]
        if new_source != source:
            logger.info(
                "mapper.source_override feed=%s type=%s old=%s new=%s",
                item.feed_id, item.signal_type_hint, source.value, new_source.value,
            )
            source = new_source

    # Severity (already enriched by compute_severity)
    severity_score = item.severity_hint if item.severity_hint is not None else 0.3

    # Direction
    direction = _DIRECTION_MAP.get(
        item.direction_hint or "", SignalDirection.NEGATIVE
    )

    # Confidence
    confidence = _CONFIDENCE_MAP.get(
        item.confidence, SignalConfidence.UNVERIFIED
    )

    # Regions (already enriched by extract_regions)
    regions = _resolve_regions(item.region_hints)

    # Impact domains (already enriched by extract_domains)
    domains = _resolve_domains(item.domain_hints)

    # Signal type (already enriched by classify_signal_type)
    signal_type = _SIGNAL_TYPE_MAP.get(item.signal_type_hint or "")

    # Event time
    event_time = item.published_at or datetime.now(timezone.utc)

    # Tags
    tags = list(set(
        item.payload.get("categories", [])
        + [item.feed_id, item.feed_type.value]
    ))

    # Source URI
    source_uri = item.url

    # External ID for dedup trace
    external_id = f"signal_intel:{item.feed_id}:{item.item_id}"

    # Country scope from region hints that didn't resolve to GCC
    country_scope: list[str] = []
    for hint in item.region_hints:
        h = hint.strip().lower()
        if h not in REGION_ALIASES and h not in {m.value.lower() for m in GCCRegion}:
            country_scope.append(hint.strip())

    # Sector scope from domain hints that didn't resolve
    sector_scope: list[str] = []
    for hint in item.domain_hints:
        h = hint.strip().lower()
        if h not in DOMAIN_ALIASES and h not in {m.value for m in ImpactDomain}:
            sector_scope.append(hint.strip())

    return MacroSignalInput(
        title=title[:300],
        description=(item.description or "")[:5000] or None,
        source=source,
        source_uri=source_uri,
        severity_score=severity_score,
        direction=direction,
        confidence=confidence,
        regions=regions,
        impact_domains=domains,
        event_time=event_time,
        ttl_hours=72,
        tags=tags[:20],
        external_id=external_id,
        signal_type=signal_type,
        country_scope=country_scope,
        sector_scope=sector_scope,
        raw_payload=item.payload if item.payload else None,
    )
