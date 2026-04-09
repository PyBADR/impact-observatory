"""Signal Intelligence Layer — Source Event Models.

Source-of-truth Pydantic contracts for external feed items.

A SourceEvent is a normalized representation of an inbound feed item
(RSS/Atom entry, JSON API event, webhook payload) before it is mapped
to a Pack 1 MacroSignalInput.

Design rules:
  - All optional fields default to None/empty — never raise on missing data
  - detected_at is always set (ingestion time if not provided by feed)
  - raw_payload preserves the original item for audit and re-processing
  - dedup_key is computed lazily from external_id or content hash
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, model_validator


class SourceType(str, Enum):
    """Classification of the external signal source."""
    RSS       = "rss"         # RSS/Atom feed
    JSON_API  = "json_api"    # REST or webhook JSON endpoint
    MANUAL    = "manual"      # manually authored event
    UNKNOWN   = "unknown"     # unclassified / fallback


class SourceConfidence(str, Enum):
    """Confidence in the source's reliability.

    Maps to MacroSignalInput.confidence when converted to Pack 1.
    """
    VERIFIED   = "verified"    # authoritative, known reliable source
    HIGH       = "high"        # credible single source
    MODERATE   = "moderate"    # credible but unconfirmed
    LOW        = "low"         # speculative / unverified source
    UNVERIFIED = "unverified"  # raw feed, no quality signal


# ── Source Event ──────────────────────────────────────────────────────────────

class SourceEvent(BaseModel):
    """Normalized external event, pre-Pack 1 mapping.

    Every inbound feed item is parsed into this model by its adapter.
    This is the single interface between feed adapters and the rest of
    the Signal Intelligence Layer.

    Required fields:
      source_type, source_name, source_ref, title

    Optional fields default to safe empty values. Never raise on missing data.
    """
    # ── Identity ──────────────────────────────────────────────────────────────
    event_id: UUID = Field(default_factory=uuid4)
    source_type: SourceType
    source_name: str = Field(
        ..., min_length=1,
        description="Human-readable source name (e.g. 'Reuters RSS', 'Bloomberg API')"
    )
    source_ref: str = Field(
        ..., min_length=1,
        description="Canonical source reference (URL, feed URL, or API endpoint)"
    )
    external_id: Optional[str] = Field(
        None, max_length=512,
        description=(
            "Caller-assigned or feed-provided external ID. "
            "Used as primary dedup key when present."
        )
    )

    # ── Content ───────────────────────────────────────────────────────────────
    title: str = Field(
        ..., min_length=1, max_length=1000,
        description="Event headline / title from the source feed"
    )
    description: Optional[str] = Field(
        None, max_length=10000,
        description="Extended description, summary, or body text"
    )
    url: Optional[str] = Field(
        None, max_length=2048,
        description="Direct URL to the source item (article, report, etc.)"
    )

    # ── Timing ────────────────────────────────────────────────────────────────
    published_at: Optional[datetime] = Field(
        None,
        description="When the item was published by the source (UTC). None if unavailable."
    )
    detected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When this item was detected / ingested (UTC). Always set."
    )

    # ── Hints (geographic, sector, category) ─────────────────────────────────
    # These are free-form strings from the feed, not ImpactDomain/GCCRegion enums.
    # The normalizer and Pack 1 mapper resolve them to typed values.
    region_hints: list[str] = Field(
        default_factory=list,
        description="Geographic region strings from the feed (e.g. ['Saudi Arabia', 'GCC'])"
    )
    country_hints: list[str] = Field(
        default_factory=list,
        description="Country name strings from the feed"
    )
    sector_hints: list[str] = Field(
        default_factory=list,
        description="Industry/sector strings from the feed (e.g. ['oil', 'banking'])"
    )
    category_hints: list[str] = Field(
        default_factory=list,
        description=(
            "Feed-provided category/tag labels "
            "(e.g. ['geopolitical', 'energy', 'conflict'])"
        )
    )

    # ── Quality ───────────────────────────────────────────────────────────────
    source_confidence: SourceConfidence = Field(
        default=SourceConfidence.UNVERIFIED,
        description="Reliability classification for this source"
    )

    # ── Raw Payload ───────────────────────────────────────────────────────────
    raw_payload: Optional[dict[str, Any]] = Field(
        None,
        description=(
            "Original unparsed feed item preserved as-is. "
            "Used for audit, re-processing, and downstream enrichment."
        )
    )

    # ── Deduplication key (computed) ──────────────────────────────────────────
    dedup_key: str = Field(
        default="",
        description=(
            "Stable deduplication key. "
            "Set to external_id if available, else to SHA-256 content hash. "
            "Computed by model_validator — do not set manually."
        )
    )

    @model_validator(mode="after")
    def _compute_dedup_key(self) -> "SourceEvent":
        """Compute dedup_key from external_id or content hash."""
        if not self.dedup_key:
            if self.external_id:
                self.dedup_key = f"ext:{self.external_id}"
            else:
                # Stable content hash: source_name + title + published_at + source_ref
                published_str = (
                    self.published_at.isoformat()
                    if self.published_at else ""
                )
                canonical = json.dumps({
                    "source_name": self.source_name,
                    "source_ref": self.source_ref,
                    "title": self.title,
                    "published_at": published_str,
                }, sort_keys=True)
                h = hashlib.sha256(canonical.encode()).hexdigest()
                self.dedup_key = f"hash:{h}"
        return self


class IngestionRecord(BaseModel):
    """Audit record for a single source event ingestion attempt.

    Created by the routing layer for every processed SourceEvent.
    """
    record_id: UUID = Field(default_factory=uuid4)
    event_id: UUID
    dedup_key: str
    was_duplicate: bool = False
    routing_mode: str = "ingest_only"
    signal_id: Optional[UUID] = None       # set if Pack 1 intake succeeded
    graph_ingested: bool = False            # set if graph ingestion succeeded
    runtime_executed: bool = False          # set if macro runtime executed
    errors: list[str] = Field(default_factory=list)
    recorded_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
