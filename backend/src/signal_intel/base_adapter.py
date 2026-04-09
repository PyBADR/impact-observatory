"""Signal Intelligence Layer — Abstract Feed Adapter.

Every external feed source must implement this interface.
Adapters are responsible for:
  1. Fetching raw data from the source
  2. Parsing it into RawFeedItem instances
  3. Setting source confidence and mapping hints

Adapters must NOT:
  - Run LLM inference
  - Mutate downstream state
  - Import Pack 1 or Graph Brain modules
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from typing import Any

from src.signal_intel.types import FeedConfig, FeedResult, FeedType, RawFeedItem

logger = logging.getLogger("signal_intel.adapter")


class BaseFeedAdapter(ABC):
    """Abstract base for all feed adapters.

    Subclasses must implement:
      - feed_type (property)
      - fetch_raw() — retrieve raw data from the external source
      - parse_items() — transform raw data into RawFeedItem list
    """

    def __init__(self, config: FeedConfig) -> None:
        self.config = config
        self._last_fetch: float | None = None

    @property
    @abstractmethod
    def feed_type(self) -> FeedType:
        """The feed type this adapter handles."""
        ...

    @abstractmethod
    async def fetch_raw(self) -> Any:
        """Fetch raw data from the external source.

        Returns source-specific raw data (XML string, JSON dict, etc.).
        Must handle its own HTTP errors gracefully.
        """
        ...

    @abstractmethod
    def parse_items(self, raw_data: Any) -> list[RawFeedItem]:
        """Parse raw source data into RawFeedItem instances.

        Must be deterministic: same raw_data → same output.
        Must set content_hash on each item.
        """
        ...

    async def poll(self) -> FeedResult:
        """Full poll cycle: fetch → parse → return result.

        This is the primary entry point called by the orchestrator.
        Never throws — all errors are captured in FeedResult.
        """
        result = FeedResult(
            feed_id=self.config.feed_id,
            feed_type=self.feed_type,
        )
        start = time.monotonic()

        try:
            raw_data = await self.fetch_raw()
            items = self.parse_items(raw_data)

            # Compute content hashes
            for item in items:
                item.compute_content_hash()

            result.items_fetched = len(items)
            self._last_fetch = time.time()

        except Exception as exc:
            result.errors.append(f"{type(exc).__name__}: {exc}")
            logger.error(
                "Feed %s poll failed: %s", self.config.feed_id, exc,
                exc_info=True,
            )
            items = []

        result.duration_ms = (time.monotonic() - start) * 1000

        # Attach items to result for downstream processing
        result._items = items  # type: ignore[attr-defined]
        return result

    def get_items_from_result(self, result: FeedResult) -> list[RawFeedItem]:
        """Extract parsed items from a FeedResult."""
        return getattr(result, "_items", [])
