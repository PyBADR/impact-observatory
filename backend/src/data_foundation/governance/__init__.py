"""
Governance Layer | طبقة الحوكمة
=================================

Decision governance, rule lifecycle management, truth validation,
calibration triggers, and unified audit trail for Impact Observatory.

Modules:
  schemas.py               — 8 Pydantic domain models
  orm_models.py            — 6 ORM table definitions
  converters.py            — Pydantic ↔ ORM converters
  repositories.py          — 6 typed async repositories
  rule_lifecycle.py        — State machine + transition guards
  truth_validation.py      — Source truth ranking + validation
  calibration_triggers.py  — Performance-based recalibration
  governance_audit.py      — Unified governance audit chain
"""
