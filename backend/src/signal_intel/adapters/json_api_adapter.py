"""Signal Intelligence Layer — JSON API Feed Adapter.

Ingests structured JSON payloads from news and event APIs.
Supports configurable field mapping via JSONPath-like dot notation.

Expected API response: JSON object with an array of items under a
configurable key (default: "articles" or "data" or root-level array).

Source quality: configurable per feed.
No LLM inference. Pure field extraction and mapping.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from src.signal_intel.base_adapter import BaseFeedAdapter
from src.signal_intel.types import FeedConfig, FeedType, RawFeedItem

logger = logging.getLogger("signal_intel.json_api")

_TIMEOUT = float(os.environ.get("SIGNAL_INTEL_HTTP_TIMEOUT", "30"))

# Default field mapping: JSON key → RawFeedItem field
DEFAULT_FIELD_MAP = {
    "title": ["title", "headline", "name"],
    "description": ["description", "summary", "content", "body", "text"],
    "url": ["url", "link", "source_url", "web_url"],
    "published_at": ["published_at", "publishedAt", "date", "pub_date", "timestamp", "created_at"],
    "item_id": ["id", "article_id", "event_id", "uuid"],
    "severity": ["severity", "severity_score", "impact_score", "risk_score"],
    "region": ["region", "country", "location", "geo"],
    "category": ["category", "type", "event_type", "domain", "sector"],
    "signal_type": ["signal_type", "signalType", "event_class", "signal_category"],
}


class JSONAPIAdapter(BaseFeedAdapter):
    """Adapter for structured JSON news/event APIs."""

    def __init__(
        self,
        config: FeedConfig,
        items_key: str | None = None,
        field_map: dict[str, list[str]] | None = None,
    ) -> None:
        super().__init__(config)
        self.items_key = items_key  # key in response JSON holding the array
        self.field_map = field_map or DEFAULT_FIELD_MAP

    @property
    def feed_type(self) -> FeedType:
        return FeedType.JSON_API

    async def fetch_raw(self) -> Any:
        """Fetch JSON from the API endpoint."""
        headers = {
            "User-Agent": "DeevoSignalIntel/1.0",
            "Accept": "application/json",
        }

        # Add auth header if configured
        if self.config.auth_header and self.config.auth_token_env:
            token = os.environ.get(self.config.auth_token_env, "")
            if token:
                headers[self.config.auth_header] = token

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(self.config.url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def parse_items(self, raw_data: Any) -> list[RawFeedItem]:
        """Parse JSON response into RawFeedItem list."""
        if raw_data is None:
            return []

        # Extract the items array
        items_list = self._extract_items_list(raw_data)
        if not items_list:
            return []

        results: list[RawFeedItem] = []
        for raw_item in items_list:
            if not isinstance(raw_item, dict):
                continue
            try:
                item = self._map_item(raw_item)
                if item:
                    results.append(item)
            except Exception as exc:
                logger.debug(
                    "Feed %s: skipping item due to %s: %s",
                    self.config.feed_id, type(exc).__name__, exc,
                )
                continue

        return results

    def _extract_items_list(self, data: Any) -> list[dict]:
        """Find the array of items in the JSON response."""
        # Direct array
        if isinstance(data, list):
            return data

        if not isinstance(data, dict):
            return []

        # Explicit items_key
        if self.items_key and self.items_key in data:
            val = data[self.items_key]
            return val if isinstance(val, list) else []

        # Auto-detect: try common keys
        for key in ("articles", "data", "items", "results", "events", "records"):
            if key in data and isinstance(data[key], list):
                return data[key]

        return []

    def _map_item(self, raw: dict[str, Any]) -> RawFeedItem | None:
        """Map a single JSON object to a RawFeedItem using field_map."""
        title = self._resolve_field(raw, "title")
        if not title:
            return None

        description = self._resolve_field(raw, "description") or ""
        url = self._resolve_field(raw, "url")
        item_id = self._resolve_field(raw, "item_id") or url or title
        pub_str = self._resolve_field(raw, "published_at")
        severity_raw = self._resolve_field(raw, "severity")
        region_raw = self._resolve_field(raw, "region")
        category_raw = self._resolve_field(raw, "category")

        published_at = _parse_datetime(pub_str) if pub_str else None

        # Severity hint
        severity_hint = None
        if severity_raw is not None:
            try:
                severity_hint = max(0.0, min(1.0, float(severity_raw)))
            except (ValueError, TypeError):
                pass

        # Region hints
        region_hints = list(self.config.default_regions)
        if region_raw:
            if isinstance(region_raw, list):
                region_hints.extend(str(r) for r in region_raw)
            else:
                region_hints.append(str(region_raw))

        # Domain hints from category
        domain_hints = list(self.config.default_domains)
        if category_raw:
            if isinstance(category_raw, list):
                domain_hints.extend(str(c) for c in category_raw)
            else:
                domain_hints.append(str(category_raw))

        # Signal type hint from API data
        signal_type_raw = self._resolve_field(raw, "signal_type")
        signal_type_hint = str(signal_type_raw).strip().lower() if signal_type_raw else None

        return RawFeedItem(
            item_id=str(item_id),
            feed_id=self.config.feed_id,
            feed_type=FeedType.JSON_API,
            title=str(title)[:500],
            description=str(description)[:10000],
            url=str(url) if url else None,
            published_at=published_at,
            payload=raw,
            source_quality=self.config.source_quality,
            confidence=self.config.default_confidence,
            region_hints=region_hints,
            domain_hints=domain_hints,
            severity_hint=severity_hint,
            signal_type_hint=signal_type_hint,
        )

    def _resolve_field(self, data: dict[str, Any], logical_field: str) -> Any:
        """Resolve a logical field name using the field map.

        Tries each candidate key in order, returns first non-None match.
        Supports one level of dot notation (e.g., 'source.name').
        """
        candidates = self.field_map.get(logical_field, [logical_field])
        for key in candidates:
            if "." in key:
                parts = key.split(".", 1)
                nested = data.get(parts[0])
                if isinstance(nested, dict):
                    val = nested.get(parts[1])
                    if val is not None:
                        return val
            else:
                val = data.get(key)
                if val is not None:
                    return val
        return None


# ── Helpers ─────────────────────────────────────────────────────────────────

def _parse_datetime(val: Any) -> datetime | None:
    """Parse a datetime from various formats."""
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)

    if isinstance(val, (int, float)):
        try:
            return datetime.fromtimestamp(val, tz=timezone.utc)
        except (ValueError, OSError):
            return None

    if not isinstance(val, str):
        return None

    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(val.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            continue
    return None
