"""
Impact Observatory | مرصد الأثر
RSS Connector — pilot connector for RSS/XML signal feeds.

This connector:
  - Parses RSS 2.0 XML from a local fixture or string
  - Converts entries to normalized signal dicts
  - Does NOT make network calls (reads from file/string only)
  - Does NOT require secrets or API keys
  - Does NOT modify scenario outputs

In v3, this connector reads from a static fixture file.
Future versions may add HTTP fetch behind a feature flag.
"""
from __future__ import annotations

import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Optional

from src.signal_ingestion.models import SignalSource, SignalSourceType
from src.signal_ingestion.connectors.base import BaseConnector


# ═══════════════════════════════════════════════════════════════════════════════
# Scenario keyword mapping — maps RSS categories to scenario IDs
# ═══════════════════════════════════════════════════════════════════════════════

_CATEGORY_TO_SCENARIOS: dict[str, list[str]] = {
    "energy": ["energy_market_volatility_shock", "saudi_oil_shock"],
    "maritime": ["hormuz_chokepoint_disruption", "red_sea_trade_corridor_instability"],
    "banking": ["uae_banking_crisis", "regional_liquidity_stress_event"],
    "fintech": ["gcc_cyber_attack"],
    "insurance": ["bahrain_sovereign_stress"],
    "logistics": ["oman_port_closure", "critical_port_throughput_disruption"],
}

_CATEGORY_TO_COUNTRIES: dict[str, list[str]] = {
    "energy": ["SAUDI", "UAE", "KUWAIT"],
    "maritime": ["UAE", "OMAN", "QATAR"],
    "banking": ["UAE", "BAHRAIN"],
    "fintech": ["UAE"],
    "insurance": ["UAE", "BAHRAIN"],
    "logistics": ["UAE", "OMAN"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# Default fixture source
# ═══════════════════════════════════════════════════════════════════════════════

# The pilot RSS source — disabled by default
PILOT_RSS_SOURCE = SignalSource(
    source_id="sig_rss_pilot",
    name="RSS Connector Pilot (Fixture)",
    source_type=SignalSourceType.RSS,
    url=None,
    refresh_frequency_minutes=60,
    confidence_weight=0.75,
    enabled=False,
    notes="Pilot RSS connector reading from static XML fixture. "
          "No network calls. Disabled by default.",
)


# ═══════════════════════════════════════════════════════════════════════════════
# RSS Connector
# ═══════════════════════════════════════════════════════════════════════════════

class RSSConnector(BaseConnector):
    """RSS 2.0 connector that parses XML from a file or string.

    This connector NEVER makes HTTP requests. It reads from:
      - A local XML file path (fixture_path)
      - A raw XML string (xml_content)

    At least one must be provided.
    """

    def __init__(
        self,
        *,
        source: Optional[SignalSource] = None,
        fixture_path: Optional[Path] = None,
        xml_content: Optional[str] = None,
        enabled: bool = False,
    ) -> None:
        src = source or PILOT_RSS_SOURCE
        super().__init__(
            connector_id="rss_pilot",
            source=src,
            enabled=enabled,
        )
        self._fixture_path = fixture_path
        self._xml_content = xml_content

    def _get_xml(self) -> str:
        """Get XML content from string or file."""
        if self._xml_content is not None:
            return self._xml_content
        if self._fixture_path is not None and self._fixture_path.exists():
            return self._fixture_path.read_text(encoding="utf-8")
        raise FileNotFoundError(
            f"No XML content or fixture file available. "
            f"Path: {self._fixture_path}"
        )

    def _fetch_raw(self) -> list[dict[str, Any]]:
        """Parse RSS XML into raw item dicts."""
        xml_text = self._get_xml()
        root = ET.fromstring(xml_text)
        channel = root.find("channel")
        if channel is None:
            return []

        items: list[dict[str, Any]] = []
        for item in channel.findall("item"):
            entry: dict[str, Any] = {}
            title_el = item.find("title")
            entry["title"] = title_el.text if title_el is not None and title_el.text else ""

            link_el = item.find("link")
            entry["link"] = link_el.text if link_el is not None and link_el.text else None

            desc_el = item.find("description")
            entry["description"] = desc_el.text if desc_el is not None and desc_el.text else ""

            pubdate_el = item.find("pubDate")
            entry["pubDate"] = pubdate_el.text if pubdate_el is not None and pubdate_el.text else None

            categories = [
                cat.text.strip().lower()
                for cat in item.findall("category")
                if cat.text
            ]
            entry["categories"] = categories

            items.append(entry)

        return items

    def _parse_entry(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Convert one RSS item dict into the normalized signal format."""
        # Parse pubDate (RFC 2822) to ISO-8601
        published_at = None
        pub_str = raw.get("pubDate")
        if pub_str:
            try:
                dt = parsedate_to_datetime(pub_str)
                published_at = dt.astimezone(timezone.utc).isoformat()
            except (ValueError, TypeError):
                published_at = None

        if published_at is None:
            published_at = datetime.now(timezone.utc).isoformat()

        # Map categories to scenarios, countries, sectors
        categories = raw.get("categories", [])
        related_scenarios: list[str] = []
        related_countries: list[str] = []
        related_sectors: list[str] = list(categories)

        for cat in categories:
            related_scenarios.extend(_CATEGORY_TO_SCENARIOS.get(cat, []))
            related_countries.extend(_CATEGORY_TO_COUNTRIES.get(cat, []))

        # Deduplicate
        related_scenarios = list(dict.fromkeys(related_scenarios))
        related_countries = list(dict.fromkeys(related_countries))

        return {
            "title": raw.get("title", "Untitled"),
            "summary": raw.get("description", ""),
            "url": raw.get("link"),
            "published_at": published_at,
            "related_scenarios": related_scenarios,
            "related_countries": related_countries,
            "related_sectors": related_sectors,
            "rss_categories": categories,
        }

    def _health_ping(self) -> bool:
        """Check if the XML source is available and parseable.

        Raises on hard failures (missing file, unparseable XML) so
        the base class marks status as UNAVAILABLE.
        Returns False only for soft issues (e.g., missing <channel>).
        """
        xml_text = self._get_xml()           # Raises FileNotFoundError if missing
        root = ET.fromstring(xml_text)        # Raises ParseError if bad XML
        channel = root.find("channel")
        return channel is not None
