"""Signal Intelligence Layer — JSON API Adapter.

Parses generic JSON event payloads into SourceEvent objects.

Supports configurable field mapping to accommodate different API schemas.
When no mapping is provided, safe defaults are used (see DEFAULT_FIELD_MAPPING).

Design rules:
  - Never raises; returns None for unrecoverable items
  - All string extraction strips whitespace
  - Timestamps parsed from ISO 8601, Unix epoch (int/float), or common formats
  - Preserves full raw payload
  - Field mapping is additive — unmapped fields stay in raw_payload
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from src.signals.source_models import SourceConfidence, SourceEvent, SourceType

logger = logging.getLogger("signals.json_adapter")


# ── Field Mapping ─────────────────────────────────────────────────────────────

class FieldMapping:
    """Configurable mapping from JSON field names to SourceEvent fields.

    Each attribute names the key (or dot-separated path) in the JSON payload
    that maps to the corresponding SourceEvent field.

    Usage:
        mapping = FieldMapping(
            title="headline",
            description="body",
            external_id="event_id",
            published_at="timestamp",
            region_hints="regions",
            category_hints="labels",
        )
    """
    def __init__(
        self,
        title: str = "title",
        description: str = "description",
        external_id: str = "id",
        url: str = "url",
        published_at: str = "published_at",
        region_hints: str = "regions",
        country_hints: str = "countries",
        sector_hints: str = "sectors",
        category_hints: str = "categories",
    ) -> None:
        self.title = title
        self.description = description
        self.external_id = external_id
        self.url = url
        self.published_at = published_at
        self.region_hints = region_hints
        self.country_hints = country_hints
        self.sector_hints = sector_hints
        self.category_hints = category_hints


# Default field mapping — aligns with common REST API conventions
DEFAULT_FIELD_MAPPING = FieldMapping()

# ── Helpers ───────────────────────────────────────────────────────────────────

def _extract_nested(payload: dict[str, Any], key: str) -> Any:
    """Extract value from payload using dot-separated key path.

    e.g. "event.metadata.title" → payload["event"]["metadata"]["title"]
    Falls back to flat key lookup if path fails.
    """
    parts = key.split(".")
    current: Any = payload
    for part in parts:
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _str_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s if s else None


def _parse_datetime(value: Any) -> Optional[datetime]:
    """Parse various datetime representations to UTC datetime."""
    if value is None:
        return None

    # Already a datetime
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)

    # Unix epoch (seconds)
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value, tz=timezone.utc)
        except (OSError, OverflowError, ValueError):
            return None

    # String formats
    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None
        # Try ISO 8601 variants
        for fmt in (
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%dT%H:%M:%SZ",
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d",
        ):
            try:
                dt = datetime.strptime(value, fmt)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt.astimezone(timezone.utc)
            except ValueError:
                continue
        # Try numeric string
        try:
            ts = float(value)
            return datetime.fromtimestamp(ts, tz=timezone.utc)
        except (ValueError, OSError, OverflowError):
            pass

    return None


def _to_string_list(value: Any) -> list[str]:
    """Convert various value types to a deduplicated list of non-empty strings."""
    if value is None:
        return []
    if isinstance(value, str):
        s = value.strip()
        return [s] if s else []
    if isinstance(value, (list, tuple)):
        result: list[str] = []
        seen: set[str] = set()
        for item in value:
            s = _str_or_none(item)
            if s and s not in seen:
                seen.add(s)
                result.append(s)
        return result
    return []


# ── Adapter ───────────────────────────────────────────────────────────────────

class JSONAdapter:
    """Adapter that converts JSON event payloads to SourceEvent objects.

    Supports configurable field mapping for different API schemas.

    Usage:
        adapter = JSONAdapter(
            source_name="Bloomberg API",
            source_ref="https://api.bloomberg.com/gcc/alerts",
            source_confidence=SourceConfidence.HIGH,
            mapping=FieldMapping(title="headline", description="body"),
        )
        event = adapter.parse_item(json_payload)
    """

    def __init__(
        self,
        source_name: str,
        source_ref: str,
        source_confidence: SourceConfidence = SourceConfidence.UNVERIFIED,
        mapping: FieldMapping | None = None,
        region_hints: list[str] | None = None,
    ) -> None:
        """
        Args:
            source_name: Human-readable source name.
            source_ref: Canonical API endpoint or source identifier.
            source_confidence: Default confidence for items from this source.
            mapping: Field mapping config. Defaults to DEFAULT_FIELD_MAPPING.
            region_hints: Static region labels attached to every parsed item.
        """
        self.source_name = source_name.strip()
        self.source_ref = source_ref.strip()
        self.source_confidence = source_confidence
        self.mapping = mapping or DEFAULT_FIELD_MAPPING
        self.region_hints: list[str] = list(region_hints or [])

    def parse_item(self, payload: dict[str, Any]) -> Optional[SourceEvent]:
        """Parse one JSON payload dict into a SourceEvent.

        Returns None if the payload is unrecoverable (e.g. missing title).
        Never raises.
        """
        try:
            return self._parse(payload)
        except Exception as e:
            logger.warning("JSONAdapter.parse_item failed: %s", e)
            return None

    def _parse(self, payload: dict[str, Any]) -> Optional[SourceEvent]:
        m = self.mapping

        # ── Title (required) ──────────────────────────────────────────────────
        title = _str_or_none(_extract_nested(payload, m.title))
        if not title:
            # Try common fallback keys
            for key in ("headline", "name", "subject", "event_title"):
                title = _str_or_none(payload.get(key))
                if title:
                    break
        if not title:
            logger.debug("JSONAdapter: payload missing title, skipping")
            return None

        # ── External ID ───────────────────────────────────────────────────────
        external_id = _str_or_none(_extract_nested(payload, m.external_id))

        # ── Description ───────────────────────────────────────────────────────
        description = _str_or_none(_extract_nested(payload, m.description))
        if not description:
            for key in ("body", "content", "text", "summary", "details"):
                description = _str_or_none(payload.get(key))
                if description:
                    break

        # ── URL ───────────────────────────────────────────────────────────────
        url = _str_or_none(_extract_nested(payload, m.url))
        if not url:
            for key in ("link", "href", "article_url"):
                url = _str_or_none(payload.get(key))
                if url:
                    break

        # ── Timestamps ────────────────────────────────────────────────────────
        published_at = _parse_datetime(_extract_nested(payload, m.published_at))
        if published_at is None:
            for key in ("timestamp", "created_at", "event_time", "date", "time"):
                published_at = _parse_datetime(payload.get(key))
                if published_at is not None:
                    break

        # ── Hints ──────────────────────────────────────────────────────────────
        region_hints = list(self.region_hints)
        region_hints.extend(_to_string_list(_extract_nested(payload, m.region_hints)))

        country_hints = _to_string_list(_extract_nested(payload, m.country_hints))
        sector_hints  = _to_string_list(_extract_nested(payload, m.sector_hints))

        category_hints = _to_string_list(_extract_nested(payload, m.category_hints))
        if not category_hints:
            for key in ("tags", "labels", "keywords", "topic", "topics"):
                val = payload.get(key)
                if val:
                    category_hints = _to_string_list(val)
                    if category_hints:
                        break

        return SourceEvent(
            source_type=SourceType.JSON_API,
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
            raw_payload=dict(payload),
        )

    def parse_batch(self, payloads: list[dict[str, Any]]) -> list[SourceEvent]:
        """Parse a list of JSON payloads. Skips unparseable items."""
        events: list[SourceEvent] = []
        for payload in payloads:
            event = self.parse_item(payload)
            if event is not None:
                events.append(event)
        logger.info(
            "JSONAdapter[%s]: parsed %d/%d items",
            self.source_name, len(events), len(payloads),
        )
        return events
