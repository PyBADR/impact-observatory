"""Graph Brain Shadow Layer — Phase 0.

Knowledge Graph substrate for the Macro Intelligence system.
Sits between signal normalization (Pack 1) and causal/propagation (Pack 2).

This is a SHADOW LAYER: built, tested, queryable, but not yet
the mandatory runtime source of truth. It augments — never replaces —
existing Pack 1 and Pack 2 contracts.

Modules:
  types      — Core domain types (GraphNode, GraphEdge, enums, paths, explanations)
  store      — In-memory graph store with adjacency structure
  ingestion  — NormalizedSignal → graph nodes/edges adapters
  query      — Graph query service (connected, upstream, downstream, path trace)
  explain    — Explainability engine (structured explanation paths)
"""

__version__ = "0.1.0"
