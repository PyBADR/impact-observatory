"""Macro Intelligence Layer — Pack 1: Contracts + Signal Intake Kernel.

Upstream intelligence that feeds the existing Decision → Outcome → Value chain.
Transforms external signals into structured, validated, registry-ready objects.

Layer ownership:
  macro_enums.py       — all shared enumerations
  macro_schemas.py     — Pydantic domain models (MacroSignal, NormalizedSignal)
  macro_validators.py  — field-level + cross-field validation rules
  macro_normalizer.py  — signal normalization pipeline
  macro_signal_service.py — signal registry + intake orchestration
"""

__version__ = "1.0.0"
