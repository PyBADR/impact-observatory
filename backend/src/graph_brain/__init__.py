"""Graph Brain Shadow Layer — Phase 0 + Integration Pack A.

Knowledge Graph substrate for the Macro Intelligence system.
Sits between signal normalization (Pack 1) and causal/propagation (Pack 2).

Phase 0 (shadow layer):
  types      — Core domain types (GraphNode, GraphEdge, enums, paths, explanations)
  store      — In-memory graph store with adjacency structure
  ingestion  — NormalizedSignal → graph nodes/edges adapters
  query      — Graph query service (connected, upstream, downstream, path trace)
  explain    — Explainability engine (structured explanation paths)
  service    — Singleton service wrapping all graph operations

Integration Pack A (active runtime):
  bridge      — Type bridge: Graph Brain types → Pack 2-compatible enrichment data
  enrichment  — Feature-flagged enrichment layers for causal + propagation
  integration — Pipeline orchestrator: wires graph into causal→propagation flow
"""

__version__ = "0.2.0"
