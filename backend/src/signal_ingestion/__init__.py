"""
Impact Observatory | مرصد الأثر
Signal Ingestion Layer — v2.0.0 (Read-Only Signal Snapshots)

Provides typed models, ingestion service, and audit logging for
external signal snapshots. This layer is READ-ONLY:
  - It does NOT modify scenario calculations.
  - It does NOT connect to live RSS/API feeds (yet).
  - It prepares the system for future v3 live integration.

All signal data is static/sample until live sources are enabled
behind a feature flag.
"""
from __future__ import annotations

from src.signal_ingestion.models import (
    SignalSource,
    SignalSourceType,
    SignalSnapshot,
    SnapshotFreshness,
)
from src.signal_ingestion.ingestion_service import (
    ingest_signals,
    normalize_snapshot,
    calculate_freshness,
    calculate_confidence,
)
from src.signal_ingestion.audit_log import (
    SignalAuditEntry,
    SignalAuditAction,
    SignalAuditLog,
)

__all__ = [
    # Models
    "SignalSource",
    "SignalSourceType",
    "SignalSnapshot",
    "SnapshotFreshness",
    # Ingestion
    "ingest_signals",
    "normalize_snapshot",
    "calculate_freshness",
    "calculate_confidence",
    # Audit
    "SignalAuditEntry",
    "SignalAuditAction",
    "SignalAuditLog",
]
