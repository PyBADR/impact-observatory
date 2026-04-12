"""
Enforcement Layer | طبقة التنفيذ
==================================

Decision enforcement, execution gating, approval workflow,
and confidence degradation for Impact Observatory.

Every decision candidate must resolve to an enforcement action
(ALLOW, BLOCK, ESCALATE, REQUIRE_APPROVAL, FALLBACK, SHADOW_ONLY,
DEGRADE_CONFIDENCE) before it may proceed to execution.

Modules:
  schemas.py                — 4 Pydantic domain models + enforcement constants
  orm_models.py             — 4 ORM table definitions
  converters.py             — Pydantic ↔ ORM converters
  repositories.py           — 4 typed async repositories
  enforcement_engine.py     — Deterministic policy evaluation engine
  execution_gate_service.py — Gate resolution (allow/block/escalate/fallback)
  enforcement_audit.py      — Audit chain integration for enforcement events
"""
