"""Signal Intelligence Layer — Feed Registry.

Manages feed configurations and adapter instantiation.
Provides a declarative way to register feeds from config or API.

Included default feeds serve as templates — actual URLs must be
configured via environment or API.
"""

from __future__ import annotations

import logging
from typing import Any

from src.signal_intel.adapters.economic_adapter import EconomicAdapter
from src.signal_intel.adapters.json_api_adapter import JSONAPIAdapter
from src.signal_intel.adapters.rss_adapter import RSSFeedAdapter
from src.signal_intel.base_adapter import BaseFeedAdapter
from src.signal_intel.types import FeedConfig, FeedType

logger = logging.getLogger("signal_intel.feed_registry")


# ── Adapter Factory ─────────────────────────────────────────────────────────

_ADAPTER_MAP: dict[FeedType, type[BaseFeedAdapter]] = {
    FeedType.RSS: RSSFeedAdapter,
    FeedType.JSON_API: JSONAPIAdapter,
    FeedType.ECONOMIC: EconomicAdapter,
}


def create_adapter(config: FeedConfig, **kwargs: Any) -> BaseFeedAdapter:
    """Create an adapter instance from a FeedConfig.

    Args:
        config: Feed configuration.
        **kwargs: Additional adapter-specific arguments.

    Returns:
        Instantiated adapter.

    Raises:
        ValueError: If feed_type is not supported.
    """
    adapter_cls = _ADAPTER_MAP.get(config.feed_type)
    if adapter_cls is None:
        raise ValueError(f"Unsupported feed type: {config.feed_type}")
    return adapter_cls(config=config, **kwargs)


# ── Default Feed Templates ──────────────────────────────────────────────────
# These are TEMPLATES. Actual URLs should be configured via env/API.
# They demonstrate the expected configuration shape.

DEFAULT_FEED_TEMPLATES: list[dict[str, Any]] = [
    {
        "feed_id": "reuters-mideast-rss",
        "feed_type": "rss",
        "name": "Reuters Middle East",
        "url": "https://www.reuters.com/arc/outboundfeeds/rss/category/middle-east/",
        "enabled": False,  # disabled until explicitly enabled
        "poll_interval_minutes": 30,
        "source_quality": 0.85,
        "default_confidence": "high",
        "default_regions": ["GCC"],
        "default_domains": ["oil_gas", "sovereign_fiscal"],
        "tags": ["reuters", "news", "gcc"],
    },
    {
        "feed_id": "aljazeera-rss",
        "feed_type": "rss",
        "name": "Al Jazeera English",
        "url": "https://www.aljazeera.com/xml/rss/all.xml",
        "enabled": False,
        "poll_interval_minutes": 30,
        "source_quality": 0.70,
        "default_confidence": "moderate",
        "default_regions": ["GCC"],
        "default_domains": [],
        "tags": ["aljazeera", "news"],
    },
    {
        "feed_id": "oil-price-api",
        "feed_type": "economic",
        "name": "Oil Price Feed",
        "url": "https://api.example.com/v1/oil-prices",
        "enabled": False,
        "poll_interval_minutes": 60,
        "source_quality": 0.90,
        "default_confidence": "high",
        "default_regions": ["GCC"],
        "default_domains": ["oil_gas", "energy_grid", "sovereign_fiscal"],
        "tags": ["oil", "commodity", "price"],
        "auth_header": "X-Api-Key",
        "auth_token_env": "OIL_PRICE_API_KEY",
    },
    {
        "feed_id": "gcc-economic-indicators",
        "feed_type": "economic",
        "name": "GCC Economic Indicators",
        "url": "https://api.example.com/v1/gcc-indicators",
        "enabled": False,
        "poll_interval_minutes": 120,
        "source_quality": 0.80,
        "default_confidence": "moderate",
        "default_regions": ["GCC"],
        "default_domains": ["banking", "capital_markets", "sovereign_fiscal"],
        "tags": ["economic", "indicators", "gcc"],
    },
]


def load_default_templates() -> list[FeedConfig]:
    """Load default feed templates as FeedConfig instances."""
    configs = []
    for tmpl in DEFAULT_FEED_TEMPLATES:
        try:
            configs.append(FeedConfig(**tmpl))
        except Exception as exc:
            logger.warning("Invalid feed template %s: %s", tmpl.get("feed_id"), exc)
    return configs
