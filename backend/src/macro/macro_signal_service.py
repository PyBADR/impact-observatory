"""Macro Intelligence Layer — Signal Registry Service.

Orchestrates the full intake pipeline:
  validate → normalize → check dedup → register → return

In-memory registry for Pack 1. Swappable to PostgreSQL/Redis in Pack 2.

Design rules:
  - Service is the ONLY write path to the registry
  - All reads go through service methods
  - No direct registry mutation from routes
  - Thread-safe via simple dict (single-process FastAPI)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalSeverity,
    SignalSource,
    SignalStatus,
)
from src.macro.macro_normalizer import normalize_signal
from src.macro.macro_schemas import (
    MacroSignalInput,
    NormalizedSignal,
    SignalRegistryEntry,
    SignalRejection,
)
from src.macro.macro_validators import validate_signal_input

logger = logging.getLogger("macro.signal_service")


class SignalRegistry:
    """In-memory signal registry. Single source of truth for Pack 1."""

    def __init__(self) -> None:
        self._entries: dict[UUID, SignalRegistryEntry] = {}
        self._by_content_hash: dict[str, UUID] = {}
        self._rejections: list[SignalRejection] = []

    @property
    def size(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        """Reset registry. For testing only."""
        self._entries.clear()
        self._by_content_hash.clear()
        self._rejections.clear()


class MacroSignalService:
    """Orchestrates signal intake, validation, normalization, and registration."""

    def __init__(self, registry: SignalRegistry | None = None) -> None:
        self.registry = registry or SignalRegistry()

    # ── Intake Pipeline ──────────────────────────────────────────────────

    def ingest_signal(
        self, input_data: MacroSignalInput
    ) -> tuple[SignalRegistryEntry | None, SignalRejection | None, list[str]]:
        """Full intake pipeline.

        Returns:
            (entry, rejection, warnings)
            - entry: SignalRegistryEntry if accepted, None if rejected
            - rejection: SignalRejection if rejected, None if accepted
            - warnings: non-blocking warnings (always returned)
        """
        # Step 1: Validate
        is_valid, errors, warnings = validate_signal_input(input_data)

        if not is_valid:
            rejection = SignalRejection(
                input_payload=input_data.model_dump(mode="json"),
                errors=errors,
            )
            self.registry._rejections.append(rejection)
            logger.warning(
                "Signal rejected: %s | errors=%s",
                input_data.title[:80],
                errors,
            )
            return None, rejection, warnings

        # Step 2: Normalize
        normalized = normalize_signal(input_data)

        # Step 3: Dedup check
        existing_id = self.registry._by_content_hash.get(normalized.content_hash)
        if existing_id is not None:
            existing = self.registry._entries.get(existing_id)
            if existing and existing.status != SignalStatus.EXPIRED:
                warnings.append(
                    f"dedup: signal duplicates existing registry entry "
                    f"{existing_id} (content_hash={normalized.content_hash[:16]}…)"
                )
                # Return existing entry, no new registration
                return existing, None, warnings

        # Step 4: Register
        entry = SignalRegistryEntry(signal=normalized)
        self.registry._entries[entry.registry_id] = entry
        self.registry._by_content_hash[normalized.content_hash] = entry.registry_id

        logger.info(
            "Signal registered: %s | id=%s | severity=%s | regions=%s",
            normalized.title[:80],
            entry.registry_id,
            normalized.severity_level.value,
            [r.value for r in normalized.regions],
        )

        return entry, None, warnings

    # ── Queries ──────────────────────────────────────────────────────────

    def get_by_registry_id(self, registry_id: UUID) -> SignalRegistryEntry | None:
        return self.registry._entries.get(registry_id)

    def get_by_signal_id(self, signal_id: UUID) -> SignalRegistryEntry | None:
        for entry in self.registry._entries.values():
            if entry.signal.signal_id == signal_id:
                return entry
        return None

    def list_signals(
        self,
        offset: int = 0,
        limit: int = 50,
        source: SignalSource | None = None,
        severity: SignalSeverity | None = None,
        region: GCCRegion | None = None,
        domain: ImpactDomain | None = None,
        status: SignalStatus | None = None,
    ) -> tuple[list[SignalRegistryEntry], int]:
        """Filtered, paginated signal listing.

        Returns (entries, total_matching_count).
        """
        results = list(self.registry._entries.values())

        # Apply filters
        if source is not None:
            results = [e for e in results if e.signal.source == source]
        if severity is not None:
            results = [e for e in results if e.signal.severity_level == severity]
        if region is not None:
            results = [e for e in results if region in e.signal.regions]
        if domain is not None:
            results = [e for e in results if domain in e.signal.impact_domains]
        if status is not None:
            results = [e for e in results if e.status == status]

        # Sort by registration time descending (newest first)
        results.sort(key=lambda e: e.registered_at, reverse=True)

        total = len(results)
        page = results[offset: offset + limit]
        return page, total

    def get_rejections(self, limit: int = 50) -> list[SignalRejection]:
        """Return recent rejections for audit."""
        return list(reversed(self.registry._rejections[-limit:]))

    def expire_stale_signals(self) -> int:
        """Mark expired signals. Returns count of newly expired entries."""
        now = datetime.now(timezone.utc)
        expired_count = 0
        for entry in self.registry._entries.values():
            if (
                entry.status == SignalStatus.REGISTERED
                and entry.signal.expires_at < now
            ):
                entry.status = SignalStatus.EXPIRED
                expired_count += 1
        return expired_count

    def get_stats(self) -> dict:
        """Registry statistics for health/observability."""
        entries = list(self.registry._entries.values())
        by_status: dict[str, int] = {}
        by_severity: dict[str, int] = {}
        by_source: dict[str, int] = {}

        for e in entries:
            by_status[e.status.value] = by_status.get(e.status.value, 0) + 1
            by_severity[e.signal.severity_level.value] = (
                by_severity.get(e.signal.severity_level.value, 0) + 1
            )
            by_source[e.signal.source.value] = (
                by_source.get(e.signal.source.value, 0) + 1
            )

        return {
            "total_entries": len(entries),
            "total_rejections": len(self.registry._rejections),
            "by_status": by_status,
            "by_severity": by_severity,
            "by_source": by_source,
        }


# ── Module-level singleton ───────────────────────────────────────────────────

_default_registry = SignalRegistry()
_default_service = MacroSignalService(registry=_default_registry)


def get_signal_service() -> MacroSignalService:
    """FastAPI dependency — returns the singleton service."""
    return _default_service
