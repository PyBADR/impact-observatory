"""In-memory application state for the GCC intelligence graph.

Loads GCC nodes and edges from seed data.
This serves as the runtime state until PostgreSQL/Neo4j are connected.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class AppState:
    node_ids: list[str] = field(default_factory=list)
    node_labels: dict[str, str] = field(default_factory=dict)
    node_labels_ar: dict[str, str] = field(default_factory=dict)
    node_sectors: list[str] = field(default_factory=list)
    sector_weights: dict[str, float] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)
    node_ids_full: list[dict[str, Any]] = field(default_factory=list)
    events: list[dict[str, Any]] = field(default_factory=list)
    flights: list[dict[str, Any]] = field(default_factory=list)
    vessels: list[dict[str, Any]] = field(default_factory=list)


_state: AppState | None = None


def init_state() -> AppState:
    """Initialize state from seed data."""
    global _state
    from src.services.seed_data import GCC_NODES, GCC_EDGES, SEED_EVENTS, SEED_FLIGHTS, SEED_VESSELS

    _state = AppState(
        node_ids=[n["id"] for n in GCC_NODES],
        node_ids_full=GCC_NODES,
        node_labels={n["id"]: n["label"] for n in GCC_NODES},
        node_labels_ar={n["id"]: n.get("label_ar", n["label"]) for n in GCC_NODES},
        node_sectors=[n["layer"] for n in GCC_NODES],
        sector_weights={
            "geography": 0.10,
            "infrastructure": 0.25,
            "economy": 0.30,
            "finance": 0.20,
            "society": 0.15,
        },
        edges=GCC_EDGES,
        events=SEED_EVENTS,
        flights=SEED_FLIGHTS,
        vessels=SEED_VESSELS,
    )
    return _state


def get_state() -> AppState:
    global _state
    if _state is None:
        return init_state()
    return _state
