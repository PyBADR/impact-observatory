"""Signal Intelligence Layer — RSS/Atom Feed Adapter.

Ingests standard RSS 2.0 and Atom feeds. No browser automation,
no scraping. Parses XML with feedparser (stdlib-compatible).

Source quality: configurable per feed (default 0.5).
Confidence: moderate by default (single unverified source).
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any
from xml.etree import ElementTree

import httpx

from src.signal_intel.base_adapter import BaseFeedAdapter
from src.signal_intel.types import FeedConfig, FeedType, RawFeedItem

logger = logging.getLogger("signal_intel.rss")

# Atom namespace
ATOM_NS = "http://www.w3.org/2005/Atom"

# Request timeout
_TIMEOUT = float(os.environ.get("SIGNAL_INTEL_HTTP_TIMEOUT", "30"))


class RSSFeedAdapter(BaseFeedAdapter):
    """Adapter for RSS 2.0 and Atom feeds."""

    @property
    def feed_type(self) -> FeedType:
        return FeedType.RSS

    async def fetch_raw(self) -> str:
        """Fetch the feed XML as a string."""
        headers = {
            "User-Agent": "DeevoSignalIntel/1.0",
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml",
        }
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(self.config.url, headers=headers)
            resp.raise_for_status()
            return resp.text

    def parse_items(self, raw_data: Any) -> list[RawFeedItem]:
        """Parse RSS/Atom XML into RawFeedItem list."""
        if not isinstance(raw_data, str) or not raw_data.strip():
            return []

        try:
            root = ElementTree.fromstring(raw_data)
        except ElementTree.ParseError as exc:
            logger.warning("Feed %s XML parse error: %s", self.config.feed_id, exc)
            return []

        # Detect feed type
        if root.tag == "rss" or root.tag.endswith("}rss"):
            return self._parse_rss(root)
        elif root.tag == f"{{{ATOM_NS}}}feed" or root.tag == "feed":
            return self._parse_atom(root)
        else:
            # Try RSS channel structure
            channel = root.find("channel")
            if channel is not None:
                return self._parse_rss_channel(channel)
            logger.warning("Feed %s: unrecognized format (root=%s)", self.config.feed_id, root.tag)
            return []

    # ── RSS 2.0 ─────────────────────────────────────────────────────────────

    def _parse_rss(self, root: ElementTree.Element) -> list[RawFeedItem]:
        channel = root.find("channel")
        if channel is None:
            return []
        return self._parse_rss_channel(channel)

    def _parse_rss_channel(self, channel: ElementTree.Element) -> list[RawFeedItem]:
        items: list[RawFeedItem] = []
        for item_el in channel.findall("item"):
            title = _text(item_el, "title")
            if not title:
                continue

            link = _text(item_el, "link")
            description = _text(item_el, "description")
            pub_date = _text(item_el, "pubDate")
            guid = _text(item_el, "guid") or link or title

            published_at = _parse_rss_date(pub_date) if pub_date else None

            # Extract categories for payload and hint propagation
            categories = [
                c.text for c in item_el.findall("category")
                if c.text
            ]

            # Propagate categories into domain_hints for downstream resolution
            domain_hints = list(self.config.default_domains)
            for cat in categories:
                cat_clean = cat.strip()
                if cat_clean and cat_clean not in domain_hints:
                    domain_hints.append(cat_clean)

            items.append(RawFeedItem(
                item_id=guid,
                feed_id=self.config.feed_id,
                feed_type=FeedType.RSS,
                title=title[:500],
                description=(description or "")[:10000],
                url=link,
                published_at=published_at,
                payload={
                    "guid": guid,
                    "categories": categories,
                },
                source_quality=self.config.source_quality,
                confidence=self.config.default_confidence,
                region_hints=list(self.config.default_regions),
                domain_hints=domain_hints,
            ))

        return items

    # ── Atom ────────────────────────────────────────────────────────────────

    def _parse_atom(self, root: ElementTree.Element) -> list[RawFeedItem]:
        items: list[RawFeedItem] = []
        ns = ATOM_NS

        for entry in root.findall(f"{{{ns}}}entry") or root.findall("entry"):
            title = _atom_text(entry, "title", ns)
            if not title:
                continue

            link_el = entry.find(f"{{{ns}}}link") or entry.find("link")
            link = link_el.get("href", "") if link_el is not None else ""

            summary = _atom_text(entry, "summary", ns) or _atom_text(entry, "content", ns)
            entry_id = _atom_text(entry, "id", ns) or link or title
            updated = _atom_text(entry, "updated", ns) or _atom_text(entry, "published", ns)

            published_at = _parse_iso_date(updated) if updated else None

            items.append(RawFeedItem(
                item_id=entry_id,
                feed_id=self.config.feed_id,
                feed_type=FeedType.RSS,
                title=title[:500],
                description=(summary or "")[:10000],
                url=link or None,
                published_at=published_at,
                payload={"atom_id": entry_id},
                source_quality=self.config.source_quality,
                confidence=self.config.default_confidence,
                region_hints=list(self.config.default_regions),
                domain_hints=list(self.config.default_domains),
            ))

        return items


# ── XML Helpers ─────────────────────────────────────────────────────────────

def _text(parent: ElementTree.Element, tag: str) -> str:
    el = parent.find(tag)
    return (el.text or "").strip() if el is not None else ""


def _atom_text(parent: ElementTree.Element, tag: str, ns: str) -> str:
    el = parent.find(f"{{{ns}}}{tag}")
    if el is None:
        el = parent.find(tag)
    return (el.text or "").strip() if el is not None else ""


def _parse_rss_date(date_str: str) -> datetime | None:
    """Parse RFC 822 date (RSS pubDate format)."""
    try:
        return parsedate_to_datetime(date_str).astimezone(timezone.utc)
    except (ValueError, TypeError):
        return _parse_iso_date(date_str)


def _parse_iso_date(date_str: str) -> datetime | None:
    """Parse ISO 8601 date."""
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            continue
    return None
