"""
Impact Observatory | مرصد الأثر
Base Connector — abstract interface for all signal connectors.

Every connector must implement:
  - fetch()        → raw entries from the source
  - normalize()    → convert raw entries to SignalSnapshot list
  - health_check() → verify the source is reachable/parseable

Connectors are READ-ONLY. They never modify scenario outputs.
"""
from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from src.signal_ingestion.models import SignalSnapshot, SignalSource
from src.signal_ingestion.audit_log import SignalAuditLog, SignalAuditAction


class ConnectorStatus(str, Enum):
    """Health status of a connector."""
    HEALTHY = "healthy"          # Source reachable, data parseable
    DEGRADED = "degraded"        # Source reachable but partial data
    UNAVAILABLE = "unavailable"  # Source not reachable or not parseable
    DISABLED = "disabled"        # Connector explicitly disabled
    UNCHECKED = "unchecked"      # Never checked


@dataclass
class ConnectorState:
    """Mutable runtime state of a connector instance."""
    status: ConnectorStatus = ConnectorStatus.UNCHECKED
    last_checked_at: Optional[str] = None
    last_success_at: Optional[str] = None
    failure_reason: Optional[str] = None
    total_fetches: int = 0
    total_snapshots: int = 0
    total_failures: int = 0


class BaseConnector(abc.ABC):
    """Abstract base for all signal connectors.

    Subclasses must implement:
      - _fetch_raw()    → list of raw dicts from the source
      - _parse_entry()  → convert one raw dict to a normalized dict
      - _health_ping()  → verify source availability (no side effects)
    """

    def __init__(
        self,
        connector_id: str,
        source: SignalSource,
        *,
        enabled: bool = False,
    ) -> None:
        self.connector_id = connector_id
        self.source = source
        self.enabled = enabled
        self._state = ConnectorState()

    @property
    def state(self) -> ConnectorState:
        return self._state

    # ── Abstract methods ──────────────────────────────────────────────

    @abc.abstractmethod
    def _fetch_raw(self) -> list[dict[str, Any]]:
        """Fetch raw entries from the source. May raise on failure."""
        ...

    @abc.abstractmethod
    def _parse_entry(self, raw: dict[str, Any]) -> dict[str, Any]:
        """Parse one raw entry into the normalized signal dict format.

        Must return a dict with at least 'title' and 'published_at'.
        """
        ...

    @abc.abstractmethod
    def _health_ping(self) -> bool:
        """Check if the source is available. Return True if healthy."""
        ...

    # ── Public API ────────────────────────────────────────────────────

    def health_check(self, audit_log: Optional[SignalAuditLog] = None) -> ConnectorStatus:
        """Run a health check on the source.

        Updates internal state and optionally logs to audit trail.
        """
        now = datetime.now(timezone.utc).isoformat()
        self._state.last_checked_at = now

        if not self.enabled:
            self._state.status = ConnectorStatus.DISABLED
            if audit_log:
                audit_log.record(
                    action=SignalAuditAction.FALLBACK_USED,
                    source_id=self.source.source_id,
                    detail=f"Connector '{self.connector_id}' is disabled.",
                )
            return ConnectorStatus.DISABLED

        try:
            ok = self._health_ping()
            if ok:
                self._state.status = ConnectorStatus.HEALTHY
                self._state.failure_reason = None
            else:
                self._state.status = ConnectorStatus.DEGRADED
                self._state.failure_reason = "Health ping returned False"
        except Exception as exc:
            self._state.status = ConnectorStatus.UNAVAILABLE
            self._state.failure_reason = str(exc)
            if audit_log:
                audit_log.record(
                    action=SignalAuditAction.SOURCE_FAILED,
                    source_id=self.source.source_id,
                    detail=f"Health check failed: {exc}",
                )

        return self._state.status

    def fetch(
        self,
        audit_log: Optional[SignalAuditLog] = None,
    ) -> list[dict[str, Any]]:
        """Fetch and parse raw entries from the source.

        Returns normalized dicts ready for snapshot creation.
        Returns empty list on failure (safe fallback).
        """
        now = datetime.now(timezone.utc).isoformat()
        self._state.last_checked_at = now
        self._state.total_fetches += 1

        if not self.enabled:
            self._state.status = ConnectorStatus.DISABLED
            if audit_log:
                audit_log.record(
                    action=SignalAuditAction.FALLBACK_USED,
                    source_id=self.source.source_id,
                    detail=f"Connector '{self.connector_id}' disabled. Returning empty.",
                )
            return []

        if audit_log:
            audit_log.record(
                action=SignalAuditAction.SOURCE_CHECKED,
                source_id=self.source.source_id,
                detail=f"Connector '{self.connector_id}' fetching from source.",
            )

        try:
            raw_entries = self._fetch_raw()
        except Exception as exc:
            self._state.status = ConnectorStatus.UNAVAILABLE
            self._state.failure_reason = str(exc)
            self._state.total_failures += 1
            if audit_log:
                audit_log.record(
                    action=SignalAuditAction.SOURCE_FAILED,
                    source_id=self.source.source_id,
                    detail=f"Fetch failed: {exc}",
                )
            return []

        parsed: list[dict[str, Any]] = []
        for raw in raw_entries:
            try:
                entry = self._parse_entry(raw)
                parsed.append(entry)
            except Exception as exc:
                self._state.total_failures += 1
                if audit_log:
                    audit_log.record(
                        action=SignalAuditAction.SOURCE_FAILED,
                        source_id=self.source.source_id,
                        detail=f"Parse error: {exc}",
                    )

        self._state.status = ConnectorStatus.HEALTHY
        self._state.last_success_at = now
        self._state.failure_reason = None
        return parsed

    def normalize(
        self,
        audit_log: Optional[SignalAuditLog] = None,
        ingested_at: Optional[str] = None,
    ) -> list[SignalSnapshot]:
        """Full pipeline: fetch → parse → normalize into SignalSnapshots.

        This is the main entry point for ingestion. Returns empty on failure.
        Uses the connector's own source directly — does NOT require the
        source to be in SAMPLE_SIGNAL_SOURCES registry.
        """
        from src.signal_ingestion.ingestion_service import normalize_snapshot

        parsed = self.fetch(audit_log=audit_log)
        if not parsed:
            return []

        now = ingested_at or datetime.now(timezone.utc).isoformat()

        if audit_log:
            audit_log.record(
                action=SignalAuditAction.SOURCE_CHECKED,
                source_id=self.source.source_id,
                detail=f"Normalizing {len(parsed)} entries from '{self.connector_id}'.",
            )

        snapshots: list[SignalSnapshot] = []
        for raw in parsed:
            try:
                snap = normalize_snapshot(raw, self.source, ingested_at=now)
                snapshots.append(snap)
                if audit_log:
                    audit_log.record(
                        action=SignalAuditAction.SNAPSHOT_CREATED,
                        source_id=self.source.source_id,
                        snapshot_id=snap.snapshot_id,
                        detail=f"Snapshot: '{snap.title}' (confidence={snap.confidence_score})",
                    )
            except Exception as exc:
                self._state.total_failures += 1
                if audit_log:
                    audit_log.record(
                        action=SignalAuditAction.SOURCE_FAILED,
                        source_id=self.source.source_id,
                        detail=f"Normalize error: {exc}",
                    )

        self._state.total_snapshots += len(snapshots)
        return snapshots

    def to_dict(self) -> dict:
        return {
            "connector_id": self.connector_id,
            "source_id": self.source.source_id,
            "name": self.source.name,
            "enabled": self.enabled,
            "status": self._state.status.value,
            "last_checked_at": self._state.last_checked_at,
            "last_success_at": self._state.last_success_at,
            "failure_reason": self._state.failure_reason,
            "total_fetches": self._state.total_fetches,
            "total_snapshots": self._state.total_snapshots,
            "total_failures": self._state.total_failures,
        }
