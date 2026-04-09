"""Signal Intelligence Layer — Signal Router.

Routes normalized SourceEvents through the processing pipeline.

Routing modes:
  INGEST_ONLY     — normalize → dedup → Pack 1 intake only
  INGEST_AND_GRAPH — normalize → dedup → Pack 1 intake → Graph Brain ingestion
  FULL_RUNTIME    — normalize → dedup → Pack 1 intake → Graph Brain → Macro runtime

Design rules:
  - Each mode is a strict superset of the previous
  - If a downstream layer is unavailable, fallback gracefully without failure
  - Every routed event produces an IngestionRecord for audit
  - Router is stateless per-call; all state lives in the DedupStore
  - No exceptions propagate out of route() — errors are captured in IngestionRecord
"""

from __future__ import annotations

import logging
from enum import Enum
from typing import Optional
from uuid import UUID

from src.signals.source_models import IngestionRecord, SourceEvent
from src.signals.normalizer import normalize_source_event, to_signal_input
from src.signals.dedup import DedupStore

logger = logging.getLogger("signals.router")


class RoutingMode(str, Enum):
    """Processing depth for a routed SourceEvent."""
    INGEST_ONLY      = "ingest_only"       # Pack 1 intake only
    INGEST_AND_GRAPH = "ingest_and_graph"  # Pack 1 + Graph Brain ingestion
    FULL_RUNTIME     = "full_runtime"      # Pack 1 + Graph Brain + Macro runtime


class SignalRouter:
    """Routes SourceEvents through the signal processing pipeline.

    Usage:
        router = SignalRouter(dedup_store=DedupStore())
        record = router.route(event, mode=RoutingMode.FULL_RUNTIME)
        if record.signal_id:
            print(f"Ingested signal {record.signal_id}")
    """

    def __init__(
        self,
        dedup_store: Optional[DedupStore] = None,
    ) -> None:
        self._dedup = dedup_store or DedupStore()

    # ── Public Interface ───────────────────────────────────────────────────────

    def route(
        self,
        event: SourceEvent,
        mode: RoutingMode = RoutingMode.INGEST_ONLY,
    ) -> IngestionRecord:
        """Route a SourceEvent through the pipeline according to mode.

        Always returns an IngestionRecord. Never raises.
        """
        record = IngestionRecord(
            event_id=event.event_id,
            dedup_key=event.dedup_key,
            routing_mode=mode.value,
        )

        try:
            # ── Step 1: Normalize ──────────────────────────────────────────────
            normalized = normalize_source_event(event)

            # ── Step 2: Dedup check ────────────────────────────────────────────
            if self._dedup.check_and_mark(normalized):
                record.was_duplicate = True
                logger.debug(
                    "Router: duplicate skipped key=%s", normalized.dedup_key[:32]
                )
                return record

            # ── Step 3: Pack 1 intake ──────────────────────────────────────────
            signal_id = self._ingest_pack1(normalized, record)
            if signal_id is None:
                # Pack 1 intake failed — record has errors
                return record
            record.signal_id = signal_id

            if mode == RoutingMode.INGEST_ONLY:
                return record

            # ── Step 4: Graph Brain ingestion ──────────────────────────────────
            if mode in (RoutingMode.INGEST_AND_GRAPH, RoutingMode.FULL_RUNTIME):
                self._ingest_graph(signal_id, normalized, record)

            if mode == RoutingMode.INGEST_AND_GRAPH:
                return record

            # ── Step 5: Macro runtime ──────────────────────────────────────────
            if mode == RoutingMode.FULL_RUNTIME:
                self._run_macro_runtime(signal_id, record)

        except Exception as e:
            err = f"Router.route unexpected error: {e}"
            logger.error(err)
            record.errors.append(err)

        return record

    def route_batch(
        self,
        events: list[SourceEvent],
        mode: RoutingMode = RoutingMode.INGEST_ONLY,
    ) -> list[IngestionRecord]:
        """Route a batch of events. Returns one record per event."""
        records: list[IngestionRecord] = []
        for event in events:
            records.append(self.route(event, mode=mode))
        new_count = sum(1 for r in records if not r.was_duplicate and r.signal_id)
        dup_count  = sum(1 for r in records if r.was_duplicate)
        err_count  = sum(1 for r in records if r.errors)
        logger.info(
            "Router.route_batch: %d events → %d new, %d duplicates, %d errors",
            len(events), new_count, dup_count, err_count,
        )
        return records

    # ── Internal Steps ─────────────────────────────────────────────────────────

    def _ingest_pack1(
        self,
        event: SourceEvent,
        record: IngestionRecord,
    ) -> Optional[UUID]:
        """Map SourceEvent → MacroSignalInput and submit to Pack 1 service.

        Returns signal_id on success, None on failure.
        """
        try:
            signal_input = to_signal_input(event)

            # Import Pack 1 service lazily to avoid circular imports at module load
            from src.macro.macro_signal_service import get_signal_service
            service = get_signal_service()
            entry, rejection, _warnings = service.ingest_signal(signal_input)

            if entry is None:
                reason = rejection.errors if rejection else ["unknown rejection"]
                record.errors.append(f"Pack 1 ingest rejected: {reason}")
                return None

            logger.info(
                "Router: Pack 1 ingested signal %s from '%s'",
                entry.signal.signal_id, event.source_name,
            )
            return entry.signal.signal_id

        except Exception as e:
            err = f"Pack 1 ingest failed: {e}"
            logger.warning("Router: %s", err)
            record.errors.append(err)
            return None

    def _ingest_graph(
        self,
        signal_id: UUID,
        event: SourceEvent,
        record: IngestionRecord,
    ) -> None:
        """Ingest signal into Graph Brain. Fail-safe."""
        try:
            from src.graph_brain.enrichment import is_enrichment_active
            if not is_enrichment_active():
                logger.debug("Router: Graph Brain enrichment inactive, skipping graph ingest")
                return

            from src.graph_brain.service import get_graph_brain_service
            from src.macro.macro_signal_service import get_signal_service

            service = get_signal_service()
            entry = service.get_by_signal_id(signal_id)
            if entry is None:
                record.errors.append(f"Graph ingest: signal {signal_id} not found in registry")
                return

            graph_service = get_graph_brain_service()
            graph_service.ingest(entry.signal)
            record.graph_ingested = True
            logger.info("Router: Graph Brain ingested signal %s", signal_id)

        except ImportError:
            logger.debug("Router: Graph Brain not importable, skipping graph ingest")
        except Exception as e:
            err = f"Graph ingest failed: {e}"
            logger.warning("Router: %s", err)
            record.errors.append(err)

    def _run_macro_runtime(
        self,
        signal_id: UUID,
        record: IngestionRecord,
    ) -> None:
        """Run the full macro runtime pipeline (causal → propagation → impact → decision).

        Fail-safe: any error is captured in record.errors.
        """
        try:
            from src.macro.macro_signal_service import get_signal_service

            service = get_signal_service()
            entry = service.get_by_signal_id(signal_id)
            if entry is None:
                record.errors.append(f"Runtime: signal {signal_id} not found in registry")
                return

            from src.graph_brain.macro_runtime import run_macro_pipeline
            result = run_macro_pipeline(entry.signal)

            # Optionally run Pack 3 decision pipeline
            try:
                from src.services.macro_decision_service import get_macro_decision_service
                decision_service = get_macro_decision_service()
                decision_service.run(result.propagation_result)
            except Exception as e:
                logger.debug("Router: decision pipeline skipped: %s", e)

            record.runtime_executed = True
            logger.info(
                "Router: macro runtime completed for signal %s — "
                "domains=%d, priority=%s",
                signal_id,
                result.propagation_result.total_domains_reached,
                "n/a",  # decision priority not surfaced here for simplicity
            )

        except ImportError as e:
            logger.debug("Router: macro runtime not available: %s", e)
        except Exception as e:
            err = f"Macro runtime failed: {e}"
            logger.warning("Router: %s", err)
            record.errors.append(err)
