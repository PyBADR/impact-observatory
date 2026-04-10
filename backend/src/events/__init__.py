"""
Lightweight event sourcing for decision intelligence pipeline.

Events capture every state transition in the decision lifecycle:
  SCENARIO_STARTED → ACTION_RECOMMENDED → ACTION_APPROVED →
  OUTCOME_PENDING → OUTCOME_CONFIRMED → ROI_COMPUTED

Append-only, in-memory for v1 (can migrate to PostgreSQL event table later).
"""

from src.events.event_models import ScenarioEvent, EventType
from src.events.event_store import event_store, EventStore

__all__ = [
    "ScenarioEvent",
    "EventType",
    "event_store",
    "EventStore",
]
