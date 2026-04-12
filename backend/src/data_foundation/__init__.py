"""
Impact Observatory | مرصد الأثر — P1 Data Foundation
====================================================

Production-grade data layer for GCC macro intelligence and decision support.
14 P1 datasets with strict Pydantic schemas, ingestion contracts, seed data,
and validation rules.

Architecture Layer: Data (Layer 1 of the 7-layer intelligence stack)
Owner: Data Engineering / Platform Team
Consumers: Feature Store, Knowledge Graph, Simulation Engine, Decision Brain

Package Layout:
  schemas/     — Pydantic models for every P1 dataset
  seed/        — JSON seed files with realistic GCC reference data
  ingestion/   — Ingestion contracts (source → raw → normalized)
  validation/  — Validation rules and quality gate logic
  metadata/    — Dataset and source registry metadata
"""

__version__ = "1.0.0"
