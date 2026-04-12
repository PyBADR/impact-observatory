"""
Evaluation Layer | طبقة التقييم
================================

Outcome tracking, decision evaluation, replay, and rule performance
analysis for Impact Observatory.

Modules:
  schemas.py                  — 7 Pydantic domain models
  orm_models.py               — 7 ORM table definitions
  converters.py               — Pydantic ↔ ORM converters
  repositories.py             — 7 typed async repositories
  scoring.py                  — Deterministic scoring algorithms
  evaluation_service.py       — Expected → Actual → Evaluation pipeline
  replay_engine.py            — Historical event replay
  rule_performance_aggregator.py — Rule quality aggregation
"""
