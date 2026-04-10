"""Signal Intelligence Layer — Signal Ingestion Service.

Thin service wrapper over the Signal Intelligence pipeline:
  SourceEvent → normalize → dedup → Pack 1 intake → (Graph Brain) → (Macro runtime)

Responsibilities:
  - Provide a single entry point for external callers to submit events
  - Manage shared DedupStore and SignalRouter lifecycle
  - Expose per-adapter convenience methods
  - Cache IngestionRecords for observability

This service does NOT contain parsing logic — it delegates to:
  src.signals.rss_adapter.RSSAdapter
  src.signals.json_adapter.JSONAdapter
  src.signals.normalizer.normalize_source_event / to_signal_input
  src.signals.dedup.DedupStore
  src.signals.router.SignalRouter
"""

from __future__ import annotations

import logging
from typing import Any, Optional

from src.signals.source_models import IngestionRecord, SourceEvent
from src.signals.dedup import DedupStore
from src.signals.router import RoutingMode, SignalRouter
from src.signals.rss_adapter import RSSAdapter
from src.signals.json_adapter import FieldMapping, JSONAdapter
from src.signals.source_models import SourceConfidence

logger = logging.getLogger("services.signal_ingestion")


class SignalIngestionService:
    """Service wrapper for the Signal Intelligence pipeline.

    Usage:
        svc = SignalIngestionService()

        # Submit a pre-built SourceEvent
        record = svc.submit(event, mode=RoutingMode.FULL_RUNTIME)

        # Submit from RSS/Atom feed items
        records = svc.submit_rss_items(
            items=feed_items,
            source_name="Reuters GCC",
            source_ref="https://feeds.reuters.com/...",
        )

        # Submit from JSON API payloads
        records = svc.submit_json_items(
            payloads=api_payloads,
            source_name="Bloomberg API",
            source_ref="https://api.bloomberg.com/...",
        )
    """

    def __init__(
        self,
        dedup_ttl_seconds: int | None = None,
        default_mode: RoutingMode = RoutingMode.INGEST_ONLY,
    ) -> None:
        """
        Args:
            dedup_ttl_seconds: DedupStore TTL. None = session-scoped (no expiry).
            default_mode: Default routing mode for submit().
        """
        self._dedup = DedupStore(ttl_seconds=dedup_ttl_seconds)
        self._router = SignalRouter(dedup_store=self._dedup)
        self._default_mode = default_mode
        self._records: list[IngestionRecord] = []

    # ── Single Event Submission ────────────────────────────────────────────────

    def submit(
        self,
        event: SourceEvent,
        mode: RoutingMode | None = None,
    ) -> IngestionRecord:
        """Submit a single SourceEvent through the routing pipeline.

        Args:
            event: Pre-built SourceEvent (e.g. from an adapter).
            mode: Routing mode. Defaults to service default_mode.

        Returns:
            IngestionRecord with outcome details.
        """
        effective_mode = mode or self._default_mode
        record = self._router.route(event, mode=effective_mode)
        self._records.append(record)
        return record

    # ── RSS / Atom Feed Submission ─────────────────────────────────────────────

    def submit_rss_items(
        self,
        items: list[dict[str, Any]],
        source_name: str,
        source_ref: str,
        source_confidence: SourceConfidence = SourceConfidence.UNVERIFIED,
        region_hints: list[str] | None = None,
        mode: RoutingMode | None = None,
    ) -> list[IngestionRecord]:
        """Parse RSS/Atom feed items and submit through the pipeline.

        Args:
            items: List of feed item dicts (from feedparser or equivalent).
            source_name: Human-readable feed name.
            source_ref: Canonical feed URL.
            source_confidence: Confidence tier for this feed.
            region_hints: Static region labels for all items in this feed.
            mode: Routing mode.

        Returns:
            List of IngestionRecords (one per item; skips unparseable items).
        """
        adapter = RSSAdapter(
            source_name=source_name,
            source_ref=source_ref,
            source_confidence=source_confidence,
            region_hints=region_hints,
        )
        events = adapter.parse_feed(items)

        records: list[IngestionRecord] = []
        for event in events:
            records.append(self.submit(event, mode=mode))

        logger.info(
            "SignalIngestionService[RSS %s]: %d/%d items processed",
            source_name, len(records), len(items),
        )
        return records

    # ── JSON API Submission ────────────────────────────────────────────────────

    def submit_json_items(
        self,
        payloads: list[dict[str, Any]],
        source_name: str,
        source_ref: str,
        source_confidence: SourceConfidence = SourceConfidence.UNVERIFIED,
        field_mapping: Optional[FieldMapping] = None,
        region_hints: list[str] | None = None,
        mode: RoutingMode | None = None,
    ) -> list[IngestionRecord]:
        """Parse JSON API payloads and submit through the pipeline.

        Args:
            payloads: List of JSON payload dicts.
            source_name: Human-readable source name.
            source_ref: Canonical API endpoint or identifier.
            source_confidence: Confidence tier for this source.
            field_mapping: Optional custom field mapping.
            region_hints: Static region labels for all items from this source.
            mode: Routing mode.

        Returns:
            List of IngestionRecords (one per payload; skips unparseable items).
        """
        adapter = JSONAdapter(
            source_name=source_name,
            source_ref=source_ref,
            source_confidence=source_confidence,
            mapping=field_mapping,
            region_hints=region_hints,
        )
        events = adapter.parse_batch(payloads)

        records: list[IngestionRecord] = []
        for event in events:
            records.append(self.submit(event, mode=mode))

        logger.info(
            "SignalIngestionService[JSON %s]: %d/%d items processed",
            source_name, len(records), len(payloads),
        )
        return records

    # ── Observability ──────────────────────────────────────────────────────────

    @property
    def record_count(self) -> int:
        return len(self._records)

    @property
    def dedup_store_size(self) -> int:
        return self._dedup.size

    def list_records(self) -> list[IngestionRecord]:
        return list(self._records)

    def get_stats(self) -> dict:
        records = self._records
        total = len(records)
        duplicates = sum(1 for r in records if r.was_duplicate)
        ingested = sum(1 for r in records if r.signal_id is not None)
        graph_ingested = sum(1 for r in records if r.graph_ingested)
        runtime_executed = sum(1 for r in records if r.runtime_executed)
        errors = sum(1 for r in records if r.errors)
        return {
            "total_submitted": total,
            "duplicates_skipped": duplicates,
            "pack1_ingested": ingested,
            "graph_ingested": graph_ingested,
            "runtime_executed": runtime_executed,
            "with_errors": errors,
            "dedup_store_size": self._dedup.size,
        }

    def clear_records(self) -> None:
        """Clear record history. Primarily for tests."""
        self._records.clear()

    def clear_dedup(self) -> None:
        """Reset the dedup store. Primarily for tests."""
        self._dedup.clear()


# ── Singleton + DI ────────────────────────────────────────────────────────────

_service_instance: SignalIngestionService | None = None


def get_signal_ingestion_service() -> SignalIngestionService:
    """Return the module-level singleton SignalIngestionService.

    Resettable for tests by setting
    `src.services.signal_ingestion_service._service_instance = None`.
    """
    global _service_instance
    if _service_instance is None:
        _service_instance = SignalIngestionService()
    return _service_instance
