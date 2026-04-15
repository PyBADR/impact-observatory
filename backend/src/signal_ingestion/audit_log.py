"""
Impact Observatory | مرصد الأثر
Signal Audit Log — immutable audit trail for signal ingestion events.

Records every source check, snapshot creation, failure, and fallback
event with timestamps. The log is append-only and never mutated.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Audit action types
# ═══════════════════════════════════════════════════════════════════════════════

class SignalAuditAction(str, Enum):
    """Types of auditable signal ingestion events."""
    SOURCE_CHECKED = "source_checked"       # Source was queried
    SNAPSHOT_CREATED = "snapshot_created"    # Snapshot successfully created
    SOURCE_FAILED = "source_failed"         # Source lookup or fetch failed
    FALLBACK_USED = "fallback_used"         # Source disabled/unavailable, using fallback


# ═══════════════════════════════════════════════════════════════════════════════
# Audit entry
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class SignalAuditEntry:
    """A single immutable audit log entry."""
    timestamp: str                          # ISO-8601
    action: SignalAuditAction
    source_id: str
    snapshot_id: Optional[str]
    detail: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action.value,
            "source_id": self.source_id,
            "snapshot_id": self.snapshot_id,
            "detail": self.detail,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Audit log — append-only container
# ═══════════════════════════════════════════════════════════════════════════════

class SignalAuditLog:
    """Append-only audit log for signal ingestion events.

    Thread-safe for single-threaded use (no concurrent writes expected
    in the simulation pipeline).
    """

    def __init__(self) -> None:
        self._entries: list[SignalAuditEntry] = []

    def record(
        self,
        action: SignalAuditAction,
        source_id: str,
        snapshot_id: Optional[str] = None,
        detail: str = "",
    ) -> SignalAuditEntry:
        """Append a new audit entry.

        Returns the created entry for inspection/testing.
        """
        entry = SignalAuditEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            action=action,
            source_id=source_id,
            snapshot_id=snapshot_id,
            detail=detail,
        )
        self._entries.append(entry)
        return entry

    @property
    def entries(self) -> list[SignalAuditEntry]:
        """Return all entries (newest last)."""
        return list(self._entries)

    @property
    def count(self) -> int:
        """Number of entries recorded."""
        return len(self._entries)

    def entries_by_action(self, action: SignalAuditAction) -> list[SignalAuditEntry]:
        """Filter entries by action type."""
        return [e for e in self._entries if e.action == action]

    def entries_by_source(self, source_id: str) -> list[SignalAuditEntry]:
        """Filter entries by source ID."""
        return [e for e in self._entries if e.source_id == source_id]

    def summary(self) -> dict:
        """Return a summary of the audit log."""
        by_action: dict[str, int] = {}
        for e in self._entries:
            by_action[e.action.value] = by_action.get(e.action.value, 0) + 1
        return {
            "total_entries": len(self._entries),
            "by_action": by_action,
            "sources_checked": len(set(
                e.source_id for e in self._entries
                if e.action == SignalAuditAction.SOURCE_CHECKED
            )),
            "snapshots_created": by_action.get("snapshot_created", 0),
            "failures": by_action.get("source_failed", 0),
            "fallbacks": by_action.get("fallback_used", 0),
        }

    def to_list(self) -> list[dict]:
        """Serialize all entries as dicts."""
        return [e.to_dict() for e in self._entries]
