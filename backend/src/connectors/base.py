"""Base connector interface for all data source adapters.

Every external source must normalize through a connector that maps
raw source records into the canonical schema before storage.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from src.models.canonical import CanonicalBase, Signal


class BaseConnector(ABC):
    """Abstract base for all ingestion connectors."""

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable name of this data source."""
        ...

    @property
    @abstractmethod
    def source_type(self) -> str:
        """SourceType enum value."""
        ...

    @abstractmethod
    async def fetch_raw(self, **kwargs) -> list[dict[str, Any]]:
        """Fetch raw records from the external source.

        Returns list of raw dicts before normalization.
        """
        ...

    @abstractmethod
    def normalize(self, raw_record: dict[str, Any]) -> list[CanonicalBase]:
        """Normalize a single raw record into one or more canonical entities.

        A single raw record may produce multiple canonical entities.
        For example, a conflict event produces an Event + Signals + potentially
        updated Region risk.
        """
        ...

    def to_signal(self, raw_record: dict[str, Any]) -> Signal:
        """Convert raw record to a Signal for audit/provenance."""
        from src.models.canonical import GeoPoint, Provenance, SourceType

        location = None
        if "latitude" in raw_record and "longitude" in raw_record:
            location = GeoPoint(lat=raw_record["latitude"], lng=raw_record["longitude"])

        return Signal(
            source_type=SourceType(self.source_type),
            signal_type="event",
            payload=raw_record,
            location=location,
            provenance=Provenance(
                source_type=SourceType(self.source_type),
                source_name=self.source_name,
                source_id=str(raw_record.get("id", "")),
            ),
        )

    async def ingest(self, **kwargs) -> list[CanonicalBase]:
        """Full pipeline: fetch → normalize → return canonical entities."""
        raw_records = await self.fetch_raw(**kwargs)
        results: list[CanonicalBase] = []
        for raw in raw_records:
            results.extend(self.normalize(raw))
        return results
