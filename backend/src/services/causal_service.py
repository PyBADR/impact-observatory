"""causal_service — Causal Entry Layer service.

Thin service wrapper over the causal mapper (src.macro.causal.causal_mapper).

Responsibilities:
  - Accept a NormalizedSignal and return a CausalMapping
  - Compute CausalEntryPoint (severity × confidence_weight = entry_strength)
  - Discover activated channels from the GCC causal graph
  - Cache results in-memory for repeated lookups (by signal_id)

Follows the singleton + dependency-injection pattern used by
macro_signal_service.py and propagation_service.py.

This layer sits at src/services/ (project-level) and delegates
to src/macro/causal/ (domain-level) — it does NOT contain
causal logic itself.
"""

from __future__ import annotations

import logging
from uuid import UUID

from src.macro.macro_schemas import NormalizedSignal
from src.macro.causal.causal_mapper import (
    CONFIDENCE_WEIGHTS,
    compute_entry_strength,
    map_signal_to_causal,
    map_signal_to_causal_entry,
)
from src.macro.causal.causal_schemas import (
    CausalEntryPoint,
    CausalMapping,
)

logger = logging.getLogger("services.causal")


class CausalResultStore:
    """In-memory store for CausalMapping results.

    Keyed by signal_id for fast repeated lookup.
    Isolated here so it can be swapped to a persistent store
    in Pack 3 without touching CausalService.
    """

    def __init__(self) -> None:
        self._mappings: dict[UUID, CausalMapping] = {}

    @property
    def size(self) -> int:
        return len(self._mappings)

    def get(self, signal_id: UUID) -> CausalMapping | None:
        return self._mappings.get(signal_id)

    def put(self, signal_id: UUID, mapping: CausalMapping) -> None:
        self._mappings[signal_id] = mapping

    def clear(self) -> None:
        self._mappings.clear()


class CausalService:
    """Service layer for the Causal Entry Layer.

    Single entry point for signal → causal mapping operations.
    All causal logic is delegated to src/macro/causal/.
    """

    def __init__(self, store: CausalResultStore | None = None) -> None:
        self.store = store or CausalResultStore()

    # ── Primary pipeline ─────────────────────────────────────────────────

    def map_signal(
        self,
        signal: NormalizedSignal,
        max_depth: int = 4,
    ) -> CausalMapping:
        """Map a NormalizedSignal to a full CausalMapping.

        Returns cached result if available. Caches on first call.

        Pipeline:
          1. Build CausalEntryPoint (domains, entry_strength, reasoning)
          2. Discover activated channels (BFS up to max_depth)
          3. Compute total reachable domains
          4. Return CausalMapping (entry_point + channels + metadata)
        """
        # Return cached result for the same signal
        cached = self.store.get(signal.signal_id)
        if cached is not None:
            logger.debug("CausalService cache hit: signal=%s", signal.signal_id)
            return cached

        mapping = map_signal_to_causal(signal, max_depth=max_depth)
        self.store.put(signal.signal_id, mapping)

        logger.info(
            "Causal mapping: signal=%s entry_domains=[%s] channels=%d reachable=%d",
            signal.signal_id,
            ", ".join(d.value for d in mapping.entry_point.entry_domains),
            len(mapping.activated_channels),
            mapping.total_reachable_domains,
        )
        return mapping

    def get_entry_point(self, signal: NormalizedSignal) -> CausalEntryPoint:
        """Return only the CausalEntryPoint (no channel discovery).

        Lightweight path for callers that only need entry strength + domains.
        """
        return map_signal_to_causal_entry(signal)

    def get_entry_strength(self, signal: NormalizedSignal) -> float:
        """Return the computed entry strength for a signal.

        entry_strength = severity_score × confidence_weight
        Deterministic. No ML.
        """
        return compute_entry_strength(signal.severity_score, signal.confidence)

    # ── Queries ──────────────────────────────────────────────────────────

    def get_mapping(self, signal_id: UUID) -> CausalMapping | None:
        """Return cached mapping by signal_id, or None if not computed yet."""
        return self.store.get(signal_id)

    def get_stats(self) -> dict:
        """Causal service statistics."""
        mappings = list(self.store._mappings.values())
        if not mappings:
            return {
                "total_mappings": 0,
                "avg_channels": 0,
                "avg_reachable_domains": 0,
            }
        return {
            "total_mappings": len(mappings),
            "avg_channels": round(
                sum(len(m.activated_channels) for m in mappings) / len(mappings), 2
            ),
            "avg_reachable_domains": round(
                sum(m.total_reachable_domains for m in mappings) / len(mappings), 2
            ),
        }


# ── Module-level singleton + FastAPI dependency ───────────────────────────────

_default_store = CausalResultStore()
_default_service = CausalService(store=_default_store)


def get_causal_service() -> CausalService:
    """FastAPI dependency — returns the module-level singleton."""
    return _default_service
