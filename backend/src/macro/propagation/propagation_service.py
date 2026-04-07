"""Macro Intelligence Layer — Propagation Orchestrator Service.

Orchestrates the full pipeline:
  NormalizedSignal → CausalMapping → PropagationResult

Also maintains an in-memory result store for Pack 2.
Swappable to persistent storage in Pack 3.

Design rules:
  - Service is the ONLY entry point for propagation
  - All results go through this service
  - No direct engine calls from routes
"""

from __future__ import annotations

import logging
from typing import Optional
from uuid import UUID

from src.macro.macro_enums import ImpactDomain
from src.macro.macro_schemas import NormalizedSignal
from src.macro.causal.causal_mapper import map_signal_to_causal
from src.macro.causal.causal_schemas import CausalMapping
from src.macro.propagation.propagation_engine import (
    MAX_PROPAGATION_DEPTH,
    MIN_SEVERITY_THRESHOLD,
    propagate,
)
from src.macro.propagation.propagation_schemas import (
    PropagationResult,
    PropagationSummary,
)

logger = logging.getLogger("macro.propagation_service")


class PropagationResultStore:
    """In-memory result store for Pack 2. Single-process safe."""

    def __init__(self) -> None:
        self._results: dict[UUID, PropagationResult] = {}
        self._by_signal_id: dict[UUID, UUID] = {}  # signal_id → result_id

    @property
    def size(self) -> int:
        return len(self._results)

    def clear(self) -> None:
        self._results.clear()
        self._by_signal_id.clear()


class PropagationService:
    """Orchestrates signal → causal → propagation pipeline."""

    def __init__(self, store: PropagationResultStore | None = None) -> None:
        self.store = store or PropagationResultStore()

    def propagate_signal(
        self,
        signal: NormalizedSignal,
        max_depth: int = MAX_PROPAGATION_DEPTH,
        min_severity: float = MIN_SEVERITY_THRESHOLD,
    ) -> PropagationResult:
        """Full pipeline: signal → causal mapping → propagation.

        Returns PropagationResult with paths, hits, and audit hash.
        """
        # Step 1: Causal mapping
        causal_mapping = map_signal_to_causal(signal, max_depth=max_depth)

        logger.info(
            "Causal mapping: signal=%s entry_domains=[%s] channels=%d reachable=%d",
            signal.signal_id,
            ", ".join(d.value for d in causal_mapping.entry_point.entry_domains),
            len(causal_mapping.activated_channels),
            causal_mapping.total_reachable_domains,
        )

        # Step 2: Propagation
        result = propagate(causal_mapping, max_depth=max_depth, min_severity=min_severity)

        # Step 3: Store result
        self.store._results[result.result_id] = result
        self.store._by_signal_id[signal.signal_id] = result.result_id

        logger.info(
            "Propagation complete: signal=%s domains_reached=%d max_depth=%d paths=%d hits=%d",
            signal.signal_id,
            result.total_domains_reached,
            result.max_depth,
            len(result.paths),
            len(result.hits),
        )

        return result

    def get_causal_mapping(
        self,
        signal: NormalizedSignal,
        max_depth: int = 4,
    ) -> CausalMapping:
        """Get causal mapping only (no propagation). For inspection."""
        return map_signal_to_causal(signal, max_depth=max_depth)

    # ── Queries ──────────────────────────────────────────────────────────

    def get_result(self, result_id: UUID) -> PropagationResult | None:
        return self.store._results.get(result_id)

    def get_result_by_signal(self, signal_id: UUID) -> PropagationResult | None:
        result_id = self.store._by_signal_id.get(signal_id)
        if result_id is None:
            return None
        return self.store._results.get(result_id)

    def list_results(
        self,
        offset: int = 0,
        limit: int = 50,
    ) -> tuple[list[PropagationSummary], int]:
        """Paginated summary listing."""
        results = sorted(
            self.store._results.values(),
            key=lambda r: r.propagated_at,
            reverse=True,
        )
        total = len(results)
        page = results[offset: offset + limit]
        summaries = [
            PropagationSummary(
                result_id=r.result_id,
                signal_id=r.signal_id,
                signal_title=r.signal_title,
                total_domains_reached=r.total_domains_reached,
                max_depth=r.max_depth,
                entry_domains=r.entry_domains,
                propagated_at=r.propagated_at,
            )
            for r in page
        ]
        return summaries, total

    def get_stats(self) -> dict:
        """Propagation layer statistics."""
        results = list(self.store._results.values())
        if not results:
            return {
                "total_results": 0,
                "avg_domains_reached": 0,
                "avg_max_depth": 0,
                "total_paths": 0,
                "total_hits": 0,
            }

        return {
            "total_results": len(results),
            "avg_domains_reached": round(
                sum(r.total_domains_reached for r in results) / len(results), 2
            ),
            "avg_max_depth": round(
                sum(r.max_depth for r in results) / len(results), 2
            ),
            "total_paths": sum(len(r.paths) for r in results),
            "total_hits": sum(len(r.hits) for r in results),
        }


# ── Module-level singleton ───────────────────────────────────────────────────

_default_store = PropagationResultStore()
_default_service = PropagationService(store=_default_store)


def get_propagation_service() -> PropagationService:
    """FastAPI dependency — returns the singleton service."""
    return _default_service
