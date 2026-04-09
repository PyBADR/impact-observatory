"""Signal Intelligence Layer — Production Input Loop.

Ingests real-world signals from external feeds and routes them into
the existing Pack 1 → Graph Brain → Macro Runtime pipeline.

Architecture:
  External Feeds → Feed Adapters → Signal Mapper → Dedup Engine
    → Signal Buffer (fail-safe) → Pack 1 Intake → Graph Ingestion
    → Macro Runtime → Impact → Decision

Design principles:
  1. Adapter-first: every source goes through a typed adapter
  2. Pack 1 compatibility: all output conforms to MacroSignalInput
  3. Deterministic: no LLM inference in ingestion, rules/mappings only
  4. Fail-safe: if routing disabled, signals buffer safely
  5. Traceable: full source metadata + confidence preserved
"""

__all__ = [
    "FeedOrchestrator",
    "SignalBuffer",
    "SignalRouter",
    "DedupEngine",
]
