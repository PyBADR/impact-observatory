"""
Impact Observatory | مرصد الأثر — Phase 1 Graph Types
Typed graph primitives for the stress propagation network.

The graph is a directed weighted multigraph:
  Node = (country, sector) tuple — 6 countries x 6 sectors = 36 nodes
  Edge = transmission channel with weight (stress coupling strength)

No external libraries — pure Python + stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True, slots=True)
class NodeId:
    """Unique identifier for a graph node: (country_code, sector_code)."""
    country: str  # e.g. "SAU"
    sector: str   # e.g. "oil_gas"

    def __str__(self) -> str:
        return f"{self.country}:{self.sector}"


@dataclass(slots=True)
class Edge:
    """Directed weighted edge in the propagation graph."""
    source: NodeId
    target: NodeId
    weight: float         # coupling strength 0.0–1.0
    channel: str          # human-readable transmission label
    delay_hours: float = 0.0  # time delay before stress arrives


@dataclass(slots=True)
class NodeState:
    """Mutable stress state for a single node during propagation."""
    node_id: NodeId
    stress: float = 0.0          # current stress level 0.0–1.0
    initial_shock: float = 0.0   # exogenous shock injected at t=0
    peak_stress: float = 0.0     # maximum stress observed
    primary_driver: str = ""     # what caused the most stress
    secondary_risk: str = ""     # second-order risk channel
    transmission_channel: str = ""


@dataclass(slots=True)
class PropagationGraph:
    """In-memory directed graph for stress transmission.

    Nodes are lazily created on first edge insertion.
    Propagation uses iterative relaxation (Bellman-Ford-like)
    rather than matrix multiplication — avoids numpy dependency.
    """
    nodes: dict[NodeId, NodeState] = field(default_factory=dict)
    edges: list[Edge] = field(default_factory=list)
    _adjacency: dict[NodeId, list[Edge]] = field(default_factory=dict)

    def add_node(self, node_id: NodeId, initial_shock: float = 0.0) -> NodeState:
        """Add or update a node. Returns the NodeState."""
        if node_id not in self.nodes:
            self.nodes[node_id] = NodeState(
                node_id=node_id,
                stress=initial_shock,
                initial_shock=initial_shock,
                peak_stress=initial_shock,
            )
        else:
            state = self.nodes[node_id]
            state.initial_shock = max(state.initial_shock, initial_shock)
            state.stress = max(state.stress, initial_shock)
            state.peak_stress = max(state.peak_stress, initial_shock)
        return self.nodes[node_id]

    def add_edge(self, edge: Edge) -> None:
        """Register a directed edge. Creates source/target nodes if missing."""
        self.add_node(edge.source)
        self.add_node(edge.target)
        self.edges.append(edge)
        self._adjacency.setdefault(edge.source, []).append(edge)

    def neighbors(self, node_id: NodeId) -> list[Edge]:
        """Return outgoing edges from node_id."""
        return self._adjacency.get(node_id, [])

    def get_state(self, node_id: NodeId) -> Optional[NodeState]:
        return self.nodes.get(node_id)
