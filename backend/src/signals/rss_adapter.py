"""Signal Intelligence Layer — RSS / Atom Adapter.

Parses RSS/Atom feed item dicts into SourceEvent objects.

Feed items are typically produced by `feedparser` or similar libraries
and have a dict-like interface. This adapter is tolerant of missing fields
and never raises on malformed input — it returns None for unrecoverable items.

Supported field sources (tried in order):
  title        : item['title'], item['summary'], item['description']
  description  : item['summary'], item['description'], item['content'][0]['value']
  external_id  : item['id'], item['guid'], item['link']
  published_at : item['published_parsed'], item['updated_parsed'], item['published']
  url          : item['link']
  categories   : item['tags'], item['category']
  authors      : item['author'], item['author_detail']['name']

Design rules:
  - Never raises; returns None if item is unrecoverable
  - All string extraction strips whitespace
  - Timestamps are always converted to UTC
  - Preserves full raw item as raw_payload
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from src.signals.source_models import SourceConfidence, SourceEvent, SourceType

logger = logging.getLogger("signals.rss_adapter")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _str_or_none(value: Any) -> Optional[str]:
    """Safely extract a non-empty string or return None."""
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _parse_time_struct(ts: Any) -> Optional[datetime]:
    """Convert time.struct_time (feedparser) or ISO string to UTC datetime."""
    if ts is None:
        return None
    # feedparser returns time.struct_time from *_parsed fields
    if isinstance(ts, time.struct_time):
        try:
            return datetime(*ts[:6], tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return None
    # ISO string fallback
    if isinstance(ts, str):
        ts = ts.strip()
        if not ts:
            return None
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S",
            "%a, %d %b %Y %H:%M:%S %z",
            "%a, %d %b %Y %H:%M:%S GMT",
        ):
            try:
                dt = datetime.strptime(ts, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                continue
    # Already a datetime
    if isinstance(ts, datetime):
        if ts.tzinfo is None:
            return ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc)
    return None


def _extract_categories(item: dict[str, Any]) -> list[str]:
    """Extract category/tag labels from a feed item."""
    cats: list[str] = []

    # feedparser: tags = [{'term': ..., 'scheme': ..., 'label': ...}]
    tags = item.get("tags") or []
    if isinstance(tags, list):
        for t in tags:
            if isinstance(t, dict):
                term = _str_or_none(t.get("label") or t.get("term"))
                if term:
                    cats.append(term)
            elif isinstance(t, str):
                s = _str_or_none(t)
                if s:
                    cats.append(s)

    # Plain string or list
    category = item.get("category")
    if isinstance(category, str):
        s = _str_or_none(category)
        if s:
            cats.append(s)
    elif isinstance(category, list):
        for c in category:
            s = _str_or_none(c)
            if s:
                cats.append(s)

    return cats


def _extract_content(item: dict[str, Any]) -> Optional[str]:
    """Extract best available content/body text from feed item."""
    # feedparser: content = [{'value': ..., 'type': ...}]
    content = item.get("content")
    if isinstance(content, list) and content:
        first = content[0]
        if isinstance(first, dict):
            return _str_or_none(first.get("value"))
    if isinstance(content, str):
        return _str_or_none(content)
    return None


# ── Adapter ───────────────────────────────────────────────────────────────────

class RSSAdapter:
    """Adapter that converts RSS/Atom feed item dicts to SourceEvent objects.

    Usage:
        adapter = RSSAdapter(
            source_name="Reuters GCC RSS",
            source_ref="https://feeds.reuters.com/reuters/businessNews",
            source_confidence=SourceConfidence.HIGH,
        )
        event = adapter.parse_item(feed_item)
        if event is not None:
            # process event
    """

    def __init__(
        self,
        source_name: str,
        source_ref: str,
        source_confidence: SourceConfidence = SourceConfidence.UNVERIFIED,
        region_hints: list[str] | None = None,
    ) -> None:
        """
        Args:
            source_name: Human-readable feed name.
            source_ref: Canonical feed URL or identifier.
            source_confidence: Default confidence for items from this feed.
            region_hints: Static region labels to attach to every parsed item.
        """
        self.source_name = source_name.strip()
        self.source_ref = source_ref.strip()
        self.source_confidence = source_confidence
        self.region_hints: list[str] = list(region_hints or [])

    def parse_item(self, item: dict[str, Any]) -> Optional[SourceEvent]:
        """Parse one feed item dict into a SourceEvent.

        Returns None if the item is unrecoverable (e.g. missing title).
        Never raises.
        """
        try:
            return self._parse(item)
        except Exception as e:
            logger.warning("RSSAdapter.parse_item failed: %s", e)
            return None

    def _parse(self, item: dict[str, Any]) -> Optional[SourceEvent]:
        # ── Title (required) ─────────────────────────────────────────────────
        title = (
            _str_or_none(item.get("title"))
            or _str_or_none(item.get("summary"))
            or _str_or_none(item.get("description"))
        )
        if not title:
            logger.debug("RSSAdapter: item has no title, skipping")
            return None

        # ── External ID ───────────────────────────────────────────────────────
        external_id = (
            _str_or_none(item.get("id"))
            or _str_or_none(item.get("guid"))
            or None  # don't use 'link' as external_id — it can change
        )

        # ── Description ───────────────────────────────────────────────────────
        description = (
            _str_or_none(item.get("summary"))
            or _str_or_none(item.get("description"))
            or _extract_content(item)
        )

        # ── URL ───────────────────────────────────────────────────────────────
        url = _str_or_none(item.get("link")) or _str_or_none(item.get("url"))

        # ── Timestamps ────────────────────────────────────────────────────────
        published_at = (
            _parse_time_struct(item.get("published_parsed"))
            or _parse_time_struct(item.get("updated_parsed"))
            or _parse_time_struct(item.get("published"))
            or _parse_time_struct(item.get("updated"))
        )

        # ── Categories ────────────────────────────────────────────────────────
        category_hints = _extract_categories(item)

        # ── Region/country/sector hints ───────────────────────────────────────
        # Merge adapter-level region hints with any per-item hints
        region_hints = list(self.region_hints)
        item_regions = item.get("region_hints") or []
        if isinstance(item_regions, list):
            region_hints.extend(str(r).strip() for r in item_regions if str(r).strip())

        country_hints: list[str] = []
        item_countries = item.get("country_hints") or []
        if isinstance(item_countries, list):
            country_hints.extend(str(c).strip() for c in item_countries if str(c).strip())

        sector_hints: list[str] = []
        item_sectors = item.get("sector_hints") or []
        if isinstance(item_sectors, list):
            sector_hints.extend(str(s).strip() for s in item_sectors if str(s).strip())

        return SourceEvent(
            source_type=SourceType.RSS,
            source_name=self.source_name,
            source_ref=self.source_ref,
            external_id=external_id,
            title=title,
            description=description,
            url=url,
            published_at=published_at,
            region_hints=region_hints,
            country_hints=country_hints,
            sector_hints=sector_hints,
            category_hints=category_hints,
            source_confidence=self.source_confidence,
            raw_payload=dict(item),
        )

    def parse_feed(self, items: list[dict[str, Any]]) -> list[SourceEvent]:
        """Parse a list of feed items. Skips unparseable items.

        Returns only successfully parsed events.
        """
        events: list[SourceEvent] = []
        for item in items:
            event = self.parse_item(item)
            if event is not None:
                events.append(event)
        logger.info(
            "RSSAdapter[%s]: parsed %d/%d items",
            self.source_name, len(events), len(items),
        )
        return events
