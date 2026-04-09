"""
Impact Observatory | مرصد الأثر
Executive Narrative Layer — transforms raw simulation outputs into
structured intelligence narratives for non-technical decision-makers.

Architecture: Adapter layer between SimulationEngine and API/UI.
No LLM dependency — all narratives are deterministic and template-based.

Pipeline: Signal → Propagation → Exposure → Decision → Outcome
"""

from src.narrative.engine import NarrativeEngine
from src.narrative.error_translator import translate_error

__all__ = ["NarrativeEngine", "translate_error"]
