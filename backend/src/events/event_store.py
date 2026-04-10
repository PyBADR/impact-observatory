"""
Event Store — append-only, in-memory event log for decision lifecycle.

Thread-safe via threading.Lock. Supports:
  - Append events
  - Query by run_id, scenario_id, event_type
  - Replay events for a run (ordered by timestamp)
  - Compute ROI from confirmed outcome events

Designed for easy migration to PostgreSQL event table:
  Just replace _events list with DB insert/query.
"""
from __future__ import annotations

import logging
import threading
from typing import Any

from src.events.event_models import ScenarioEvent, EventType

logger = logging.getLogger(__name__)


class EventStore:
    """In-memory append-only event store with FIFO eviction and query capabilities."""

    def __init__(self, max_events: int = 10_000) -> None:
        self._events: list[ScenarioEvent] = []
        self._lock = threading.Lock()
        self._max_events = max_events
        self._evicted_count = 0

    # ── Write ───────────────────────────────────────────────────────────────

    def append(self, event: ScenarioEvent) -> ScenarioEvent:
        """Append an event with FIFO eviction if at capacity."""
        with self._lock:
            self._events.append(event)
            # FIFO eviction: remove oldest events when capacity exceeded
            if len(self._events) > self._max_events:
                evict_count = len(self._events) - self._max_events
                self._events = self._events[evict_count:]
                self._evicted_count += evict_count
                logger.info("Event store evicted %d oldest events (total evicted: %d)", evict_count, self._evicted_count)
        logger.debug(
            "Event appended: %s run=%s scenario=%s hash=%s",
            event.event_type, event.run_id, event.scenario_id, event.event_hash[:12],
        )
        return event

    def emit(
        self,
        event_type: EventType,
        run_id: str,
        scenario_id: str,
        payload: dict[str, Any] | None = None,
        actor: str = "system",
    ) -> ScenarioEvent:
        """Convenience: create + append in one call."""
        event = ScenarioEvent(
            event_type=event_type,
            run_id=run_id,
            scenario_id=scenario_id,
            payload=payload or {},
            actor=actor,
        )
        return self.append(event)

    # ── Read / Query ────────────────────────────────────────────────────────

    def get_by_run(self, run_id: str) -> list[ScenarioEvent]:
        """All events for a run, ordered by timestamp."""
        with self._lock:
            return [e for e in self._events if e.run_id == run_id]

    def get_by_scenario(self, scenario_id: str) -> list[ScenarioEvent]:
        """All events for a scenario across all runs."""
        with self._lock:
            return [e for e in self._events if e.scenario_id == scenario_id]

    def get_by_type(self, event_type: EventType) -> list[ScenarioEvent]:
        """All events of a specific type."""
        with self._lock:
            return [e for e in self._events if e.event_type == event_type]

    def get_by_run_and_type(
        self, run_id: str, event_type: EventType
    ) -> list[ScenarioEvent]:
        """Events for a specific run and type."""
        with self._lock:
            return [
                e for e in self._events
                if e.run_id == run_id and e.event_type == event_type
            ]

    def replay(self, run_id: str) -> list[dict[str, Any]]:
        """Replay all events for a run as dicts (for API response)."""
        events = self.get_by_run(run_id)
        return [e.to_dict() for e in events]

    @property
    def count(self) -> int:
        """Total events stored."""
        with self._lock:
            return len(self._events)

    # ── ROI Computation from Events (T7) ────────────────────────────────────

    def compute_roi_from_events(self, run_id: str) -> dict[str, Any]:
        """
        Compute ROI metrics from event stream for a given run.

        Looks at:
          - ACTION_RECOMMENDED events → expected loss avoided, cost
          - OUTCOME_CONFIRMED events → realized values
          - ROI_COMPUTED events → final computed ROI (if already exists)

        Returns:
            Dict with expected_value, realized_value, roi_ratio, event_count, etc.
        """
        recommended = self.get_by_run_and_type(run_id, "ACTION_RECOMMENDED")
        confirmed = self.get_by_run_and_type(run_id, "OUTCOME_CONFIRMED")

        # Sum expected values from recommended actions
        total_expected_loss_avoided = sum(
            float(e.payload.get("loss_avoided_usd", 0)) for e in recommended
        )
        total_cost = sum(
            float(e.payload.get("cost_usd", 0)) for e in recommended
        )

        # Sum realized values from confirmed outcomes
        total_realized = sum(
            float(e.payload.get("realized_value", 0)) for e in confirmed
        )

        # Compute ROI
        net_expected = total_expected_loss_avoided - total_cost
        roi_ratio = (
            total_realized / max(total_cost, 1.0)
            if total_cost > 0
            else 0.0
        )

        return {
            "run_id": run_id,
            "total_expected_loss_avoided": round(total_expected_loss_avoided, 2),
            "total_cost": round(total_cost, 2),
            "net_expected_value": round(net_expected, 2),
            "total_realized_value": round(total_realized, 2),
            "roi_ratio": round(roi_ratio, 4),
            "recommended_action_count": len(recommended),
            "confirmed_outcome_count": len(confirmed),
        }


# ── Module-level singleton ──────────────────────────────────────────────────
event_store = EventStore()
