"""
Event Models — typed event records for the decision lifecycle.

Six event types capture the full decision pipeline from scenario creation
through ROI computation. Each event is immutable, timestamped, and
carries a SHA-256 hash for audit integrity.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal


# ── Event Types ─────────────────────────────────────────────────────────────

EventType = Literal[
    "SCENARIO_STARTED",
    "ACTION_RECOMMENDED",
    "ACTION_APPROVED",
    "OUTCOME_PENDING",
    "OUTCOME_CONFIRMED",
    "ROI_COMPUTED",
]


@dataclass(frozen=True, slots=True)
class ScenarioEvent:
    """
    Immutable event record for the decision intelligence pipeline.

    Fields:
        event_type:   One of the 6 lifecycle event types.
        run_id:       Associated simulation run.
        scenario_id:  Scenario that triggered the event.
        payload:      Event-specific data (action details, outcome data, ROI, etc.).
        timestamp:    UTC ISO 8601 timestamp (auto-generated).
        event_hash:   SHA-256 of (event_type + run_id + scenario_id + payload + timestamp).
        actor:        Who/what triggered the event ("system", "operator", user ID).
    """

    event_type: EventType
    run_id: str
    scenario_id: str
    payload: dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default="")
    event_hash: str = field(default="")
    actor: str = field(default="system")

    def __post_init__(self) -> None:
        # Auto-generate timestamp and hash if not provided
        if not self.timestamp:
            object.__setattr__(
                self, "timestamp",
                datetime.now(timezone.utc).isoformat(),
            )
        if not self.event_hash:
            object.__setattr__(self, "event_hash", self._compute_hash())

    def _compute_hash(self) -> str:
        """SHA-256 of canonical event data for audit trail integrity."""
        canonical = json.dumps(
            {
                "event_type": self.event_type,
                "run_id": self.run_id,
                "scenario_id": self.scenario_id,
                "payload": self.payload,
                "timestamp": self.timestamp,
            },
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(canonical.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for API response / persistence."""
        return {
            "event_type": self.event_type,
            "run_id": self.run_id,
            "scenario_id": self.scenario_id,
            "payload": self.payload,
            "timestamp": self.timestamp,
            "event_hash": self.event_hash,
            "actor": self.actor,
        }
