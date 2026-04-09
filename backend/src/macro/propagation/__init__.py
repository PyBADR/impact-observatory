"""Macro Intelligence Layer — Propagation Sublayer.

Builds explainable propagation paths from causal entry points
through the GCC domain graph.

Layer ownership:
  propagation_schemas.py  — PropagationNode, Edge, Hit, Path domain models
  propagation_engine.py   — deterministic graph traversal engine
  propagation_service.py  — orchestrates signal → causal → propagation pipeline
"""
