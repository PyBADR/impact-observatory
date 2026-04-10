"""Signal Intelligence Layer — Live feed ingestion pipeline.

Converts external feed items (RSS/Atom, JSON API) into Pack 1-compatible
MacroSignalInput payloads, with optional routing into Graph Brain and
Macro runtime.

Public API:
  from src.signals.source_models import SourceEvent, SourceType, SourceConfidence
  from src.signals.rss_adapter import RSSAdapter
  from src.signals.json_adapter import JSONAdapter, FieldMapping
  from src.signals.normalizer import normalize_source_event
  from src.signals.dedup import compute_dedup_key, is_duplicate
  from src.signals.router import SignalRouter, RoutingMode
"""
