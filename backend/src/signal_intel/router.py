"""Signal Intelligence Layer — Signal Router.

Routes mapped MacroSignalInput payloads into the downstream pipeline:
  1. Pack 1 intake (MacroSignalService.ingest_signal)
  2. Graph Brain ingestion (optional, if available)
  3. Macro runtime (optional, if auto-run enabled)

Routing is fail-safe:
  - If Pack 1 rejects a signal, it's logged and skipped
  - If Graph Brain is unavailable, Pack 1 intake still succeeds
  - If auto-run is disabled, signals stop at registry
  - All routing decisions are logged as IngestionRecords

No LLM inference. No autonomous loops. Human-triggered or poll-triggered only.
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from src.signal_intel.types import IngestionRecord, IngestionStatus

logger = logging.getLogger("signal_intel.router")


class RouteResult:
    """Result of routing a single signal through the pipeline."""

    def __init__(self) -> None:
        self.pack1_accepted: bool = False
        self.signal_id: Optional[UUID] = None
        self.registry_id: Optional[UUID] = None
        self.graph_ingested: bool = False
        self.graph_nodes: int = 0
        self.graph_edges: int = 0
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def success(self) -> bool:
        return self.pack1_accepted and not self.errors


class SignalRouter:
    """Routes signals into the Pack 1 → Graph Brain pipeline.

    Dependencies are injected, not imported directly.
    This keeps the router testable and decoupled from Pack 1 internals.
    """

    def __init__(
        self,
        signal_service=None,     # MacroSignalService instance
        graph_adapter=None,      # MacroGraphAdapter instance
        auto_graph_ingest: bool = True,
    ) -> None:
        self._signal_service = signal_service
        self._graph_adapter = graph_adapter
        self._auto_graph_ingest = auto_graph_ingest
        self._records: list[IngestionRecord] = []
        self._stats = {
            "routed": 0,
            "pack1_accepted": 0,
            "pack1_rejected": 0,
            "graph_ingested": 0,
            "graph_skipped": 0,
            "errors": 0,
        }

    @property
    def stats(self) -> dict:
        return {**self._stats, "total_records": len(self._records)}

    def route(
        self,
        signal_input,  # MacroSignalInput
        feed_id: str,
        item_id: str,
        content_hash: str,
    ) -> RouteResult:
        """Route a single signal through the pipeline.

        Steps:
          1. Submit to Pack 1 (MacroSignalService.ingest_signal)
          2. If accepted and graph enabled, ingest into Graph Brain
          3. Return RouteResult with full status

        Never throws. All errors captured in RouteResult.
        """
        result = RouteResult()
        self._stats["routed"] += 1

        # ── Step 1: Pack 1 Intake ───────────────────────────────────────────
        if self._signal_service is None:
            result.errors.append("signal_service not configured")
            self._stats["errors"] += 1
            self._log_record(item_id, feed_id, content_hash, IngestionStatus.FAILED,
                             error="signal_service_not_configured")
            return result

        try:
            entry, rejection, warnings = self._signal_service.ingest_signal(signal_input)
            result.warnings.extend(warnings)

            if rejection is not None:
                result.errors.append(f"Pack 1 rejected: {rejection.errors}")
                self._stats["pack1_rejected"] += 1
                self._log_record(item_id, feed_id, content_hash, IngestionStatus.REJECTED,
                                 error=str(rejection.errors))
                return result

            if entry is None:
                result.errors.append("Pack 1 returned no entry and no rejection")
                self._stats["errors"] += 1
                self._log_record(item_id, feed_id, content_hash, IngestionStatus.FAILED,
                                 error="pack1_returned_none")
                return result

            result.pack1_accepted = True
            result.signal_id = entry.signal.signal_id
            result.registry_id = entry.registry_id
            self._stats["pack1_accepted"] += 1

        except Exception as exc:
            result.errors.append(f"Pack 1 error: {type(exc).__name__}: {exc}")
            self._stats["errors"] += 1
            self._log_record(item_id, feed_id, content_hash, IngestionStatus.FAILED,
                             error=str(exc))
            return result

        # ── Step 2: Graph Brain Ingestion (optional) ────────────────────────
        if self._auto_graph_ingest and self._graph_adapter and result.pack1_accepted:
            try:
                if self._graph_adapter.is_available():
                    ingestion_summary = self._graph_adapter.ensure_ingested(entry.signal)
                    if ingestion_summary and ingestion_summary.get("ingested"):
                        result.graph_ingested = True
                        result.graph_nodes = ingestion_summary.get("nodes_created", 0)
                        result.graph_edges = ingestion_summary.get("edges_created", 0)
                        self._stats["graph_ingested"] += 1
                    else:
                        self._stats["graph_skipped"] += 1
                else:
                    self._stats["graph_skipped"] += 1
            except Exception as exc:
                # Graph failure is non-fatal
                result.warnings.append(f"Graph ingestion failed: {exc}")
                self._stats["graph_skipped"] += 1
                logger.warning("Graph ingestion failed for signal %s: %s",
                               result.signal_id, exc)

        # ── Audit Record ────────────────────────────────────────────────────
        self._log_record(
            item_id, feed_id, content_hash, IngestionStatus.ROUTED,
            signal_id=result.signal_id,
            registry_id=result.registry_id,
        )

        return result

    def _log_record(
        self,
        item_id: str,
        feed_id: str,
        content_hash: str,
        status: IngestionStatus,
        signal_id: UUID | None = None,
        registry_id: UUID | None = None,
        error: str | None = None,
    ) -> None:
        """Create an audit record."""
        self._records.append(IngestionRecord(
            item_id=item_id,
            feed_id=feed_id,
            content_hash=content_hash,
            status=status,
            signal_id=signal_id,
            registry_id=registry_id,
            error=error,
        ))

    def get_records(self, limit: int = 100) -> list[IngestionRecord]:
        """Return recent ingestion records."""
        return list(reversed(self._records[-limit:]))

    def clear_records(self) -> None:
        """Clear audit records. For testing only."""
        self._records.clear()
        self._stats = {
            "routed": 0, "pack1_accepted": 0, "pack1_rejected": 0,
            "graph_ingested": 0, "graph_skipped": 0, "errors": 0,
        }
