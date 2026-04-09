"""Signal Intelligence Layer — Economic Signal Adapter.

Ingests lightweight economic indicators via structured JSON APIs:
  - Oil prices (Brent, WTI)
  - CPI / inflation data
  - Interest rate changes
  - Policy event signals

Each economic data point is mapped to a RawFeedItem with appropriate
severity scoring based on configurable thresholds.

No LLM inference. Pure threshold-based classification.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any

import httpx

from src.signal_intel.base_adapter import BaseFeedAdapter
from src.signal_intel.types import FeedConfig, FeedType, RawFeedItem

logger = logging.getLogger("signal_intel.economic")

_TIMEOUT = float(os.environ.get("SIGNAL_INTEL_HTTP_TIMEOUT", "30"))


# ── Severity thresholds for economic indicators ─────────────────────────────

# Percentage change thresholds → severity score
OIL_PRICE_THRESHOLDS = [
    (20.0, 0.95),   # ≥20% change → critical
    (10.0, 0.75),   # ≥10% → high
    (5.0, 0.50),    # ≥5% → elevated
    (2.0, 0.30),    # ≥2% → guarded
    (0.0, 0.15),    # any change → nominal
]

CPI_THRESHOLDS = [
    (5.0, 0.85),    # ≥5% CPI → severe
    (3.0, 0.60),    # ≥3% → elevated
    (2.0, 0.35),    # ≥2% → guarded
    (0.0, 0.15),    # any → nominal
]

RATE_THRESHOLDS = [
    (1.0, 0.80),    # ≥100bp change → high
    (0.5, 0.55),    # ≥50bp → elevated
    (0.25, 0.35),   # ≥25bp → guarded
    (0.0, 0.15),    # any → nominal
]


class EconomicIndicatorType:
    """Known economic indicator types with domain mappings."""
    OIL_PRICE = "oil_price"
    CPI = "cpi"
    INTEREST_RATE = "interest_rate"
    POLICY_EVENT = "policy_event"
    FX_RATE = "fx_rate"
    PMI = "pmi"

    DOMAIN_MAP: dict[str, list[str]] = {
        "oil_price": ["oil_gas", "energy_grid", "sovereign_fiscal"],
        "cpi": ["banking", "insurance", "capital_markets"],
        "interest_rate": ["banking", "real_estate", "capital_markets"],
        "policy_event": ["sovereign_fiscal", "insurance", "banking"],
        "fx_rate": ["trade_logistics", "capital_markets", "banking"],
        "pmi": ["trade_logistics", "oil_gas"],
    }

    SIGNAL_TYPE_MAP: dict[str, str] = {
        "oil_price": "commodity",
        "cpi": "market",
        "interest_rate": "policy",
        "policy_event": "policy",
        "fx_rate": "market",
        "pmi": "market",
    }


class EconomicAdapter(BaseFeedAdapter):
    """Adapter for structured economic data APIs.

    Expected JSON format (configurable):
    {
        "data": [
            {
                "indicator": "oil_price",
                "value": 85.4,
                "change_pct": -5.2,
                "date": "2026-04-07",
                "description": "Brent crude fell 5.2%",
                ...
            }
        ]
    }
    """

    def __init__(
        self,
        config: FeedConfig,
        items_key: str = "data",
        indicator_field: str = "indicator",
        value_field: str = "value",
        change_field: str = "change_pct",
    ) -> None:
        super().__init__(config)
        self.items_key = items_key
        self.indicator_field = indicator_field
        self.value_field = value_field
        self.change_field = change_field

    @property
    def feed_type(self) -> FeedType:
        return FeedType.ECONOMIC

    async def fetch_raw(self) -> Any:
        """Fetch economic data from API endpoint."""
        headers = {
            "User-Agent": "DeevoSignalIntel/1.0",
            "Accept": "application/json",
        }

        if self.config.auth_header and self.config.auth_token_env:
            token = os.environ.get(self.config.auth_token_env, "")
            if token:
                headers[self.config.auth_header] = token

        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(self.config.url, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def parse_items(self, raw_data: Any) -> list[RawFeedItem]:
        """Parse economic data into RawFeedItem list."""
        if raw_data is None:
            return []

        # Extract items array
        if isinstance(raw_data, list):
            items_list = raw_data
        elif isinstance(raw_data, dict):
            items_list = raw_data.get(self.items_key, [])
            if not isinstance(items_list, list):
                return []
        else:
            return []

        results: list[RawFeedItem] = []
        for raw in items_list:
            if not isinstance(raw, dict):
                continue
            try:
                item = self._map_economic_item(raw)
                if item:
                    results.append(item)
            except Exception as exc:
                logger.debug(
                    "Feed %s: skipping economic item: %s", self.config.feed_id, exc
                )
                continue

        return results

    def _map_economic_item(self, raw: dict[str, Any]) -> RawFeedItem | None:
        """Map a single economic data point to a RawFeedItem."""
        indicator = raw.get(self.indicator_field, "unknown")
        value = raw.get(self.value_field)
        change_pct = raw.get(self.change_field, 0.0)

        # Build title
        title = raw.get("title") or raw.get("description")
        if not title:
            title = f"{indicator}: value={value}, change={change_pct}%"
        title = str(title)[:500]

        if len(title) < 5:
            title = f"Economic signal: {title}"

        # Compute severity from change magnitude
        severity_hint = self._compute_severity(indicator, abs(float(change_pct or 0)))

        # Determine direction
        try:
            change_val = float(change_pct or 0)
        except (ValueError, TypeError):
            change_val = 0.0

        if change_val < -1.0:
            direction_hint = "negative"
        elif change_val > 1.0:
            direction_hint = "positive"
        else:
            direction_hint = "neutral"

        # Date parsing
        date_str = raw.get("date") or raw.get("timestamp") or raw.get("published_at")
        published_at = _parse_economic_date(date_str) if date_str else None

        # Domain hints from indicator type
        domain_hints = list(self.config.default_domains)
        indicator_domains = EconomicIndicatorType.DOMAIN_MAP.get(indicator, [])
        domain_hints.extend(indicator_domains)

        # Signal type hint
        signal_type_hint = EconomicIndicatorType.SIGNAL_TYPE_MAP.get(indicator)

        item_id = raw.get("id") or f"{self.config.feed_id}:{indicator}:{date_str or 'latest'}"

        return RawFeedItem(
            item_id=str(item_id),
            feed_id=self.config.feed_id,
            feed_type=FeedType.ECONOMIC,
            title=title,
            description=raw.get("description", ""),
            url=raw.get("url") or raw.get("source_url"),
            published_at=published_at,
            payload={
                "indicator": indicator,
                "value": value,
                "change_pct": change_pct,
                "unit": raw.get("unit", ""),
                "period": raw.get("period", ""),
                "raw": raw,
            },
            source_quality=self.config.source_quality,
            confidence=self.config.default_confidence,
            region_hints=list(self.config.default_regions) or ["GCC"],
            domain_hints=domain_hints,
            severity_hint=severity_hint,
            direction_hint=direction_hint,
            signal_type_hint=signal_type_hint,
        )

    def _compute_severity(self, indicator: str, abs_change: float) -> float:
        """Compute severity score from indicator type and change magnitude."""
        thresholds = {
            "oil_price": OIL_PRICE_THRESHOLDS,
            "cpi": CPI_THRESHOLDS,
            "interest_rate": RATE_THRESHOLDS,
            "fx_rate": RATE_THRESHOLDS,
            "pmi": CPI_THRESHOLDS,
        }

        indicator_thresholds = thresholds.get(indicator, CPI_THRESHOLDS)
        for threshold, severity in indicator_thresholds:
            if abs_change >= threshold:
                return severity

        return 0.15  # default nominal


def _parse_economic_date(val: Any) -> datetime | None:
    """Parse date from economic data."""
    if isinstance(val, datetime):
        return val if val.tzinfo else val.replace(tzinfo=timezone.utc)
    if not isinstance(val, str):
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            dt = datetime.strptime(val.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except (ValueError, TypeError):
            continue
    return None
