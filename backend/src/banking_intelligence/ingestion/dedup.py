"""
Banking Intelligence — Deduplication Registry
===============================================
In-memory dedup registry with per-type key tracking.

Dedup strategies by entity type:
  - Country:          ISO alpha-2 code (globally unique)
  - Authority:        SHA-256(authority_type + country + name_en.lower())
  - Bank:             SHA-256(swift_code) or SHA-256(license_number + country)
  - Fintech:          SHA-256(license_number + country) or SHA-256(name + country + category)
  - PaymentRail:      SHA-256(rail_type + country + system_name.lower())
  - ScenarioTrigger:  SHA-256(scenario_id + trigger_type + trigger_source)
  - DecisionPlaybook: SHA-256(playbook_type + scenario_id + version)
  - Edges:            SHA-256(from_id + to_id + edge_type)

All dedup keys are computed during Pydantic model validation
(model_validator in each schema class).
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class DedupEntry(BaseModel):
    """Single dedup registry entry."""
    dedup_key: str
    entity_type: str
    canonical_id: Optional[str] = None
    first_seen_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    last_seen_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    occurrence_count: int = 1


class DedupRegistry:
    """
    In-memory dedup registry.

    For production, this should be backed by Redis or a PostgreSQL
    table for cross-process dedup. The in-memory implementation
    is sufficient for single-process ingestion and testing.
    """

    def __init__(self):
        self._registry: dict[str, DedupEntry] = {}

    def _key(self, entity_type: str, dedup_key: str) -> str:
        return f"{entity_type}:{dedup_key}"

    def register(self, entity_type: str, dedup_key: str) -> bool:
        """
        Register a dedup key. Returns True if this is a NEW key
        (first occurrence), False if it already exists.
        """
        key = self._key(entity_type, dedup_key)
        if key in self._registry:
            entry = self._registry[key]
            entry.last_seen_at = datetime.now(timezone.utc)
            entry.occurrence_count += 1
            return False

        self._registry[key] = DedupEntry(
            dedup_key=dedup_key,
            entity_type=entity_type,
        )
        return True

    def exists(self, entity_type: str, dedup_key: str) -> bool:
        """Check if a dedup key already exists."""
        return self._key(entity_type, dedup_key) in self._registry

    def get(self, entity_type: str, dedup_key: str) -> Optional[DedupEntry]:
        """Get dedup entry if it exists."""
        return self._registry.get(self._key(entity_type, dedup_key))

    def count(self, entity_type: Optional[str] = None) -> int:
        """Count registered entries, optionally filtered by type."""
        if entity_type is None:
            return len(self._registry)
        return sum(
            1 for e in self._registry.values()
            if e.entity_type == entity_type
        )

    def clear(self, entity_type: Optional[str] = None) -> int:
        """Clear registry entries. Returns count of removed entries."""
        if entity_type is None:
            count = len(self._registry)
            self._registry.clear()
            return count

        keys_to_remove = [
            k for k, v in self._registry.items()
            if v.entity_type == entity_type
        ]
        for k in keys_to_remove:
            del self._registry[k]
        return len(keys_to_remove)

    def stats(self) -> dict[str, int]:
        """Return count per entity type."""
        from collections import Counter
        counts = Counter(e.entity_type for e in self._registry.values())
        return dict(counts)
