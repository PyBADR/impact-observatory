"""Signal Intelligence Layer — Core Types.

All types are pure Pydantic models. No business logic.
These form the internal contract between adapters, mapper, dedup, and router.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from enum import Enum

    class StrEnum(str, Enum):
        """Backport of StrEnum for Python < 3.11."""
        pass

from pydantic import BaseModel, Field, field_validator


# ── Feed Classification ─────────────────────────────────────────────────────

class FeedType(StrEnum):
    """Supported feed source types."""
    RSS = "rss"
    JSON_API = "json_api"
    ECONOMIC = "economic"


class FeedStatus(StrEnum):
    """Runtime status of a feed."""
    ACTIVE = "active"
    PAUSED = "paused"
    ERROR = "error"
    DISABLED = "disabled"


class IngestionStatus(StrEnum):
    """Status of a single feed item through the pipeline."""
    FETCHED = "fetched"
    MAPPED = "mapped"
    DEDUPLICATED = "deduplicated"
    BUFFERED = "buffered"
    ROUTED = "routed"
    REJECTED = "rejected"
    FAILED = "failed"


# ── Feed Configuration ──────────────────────────────────────────────────────

class FeedConfig(BaseModel):
    """Configuration for a single external feed.

    Immutable after creation. To update, create a new config.
    """
    feed_id: str = Field(
        ..., min_length=3, max_length=64,
        pattern=r"^[a-z0-9_-]+$",
        description="Unique feed identifier (lowercase, alphanumeric, hyphens/underscores)"
    )
    feed_type: FeedType
    name: str = Field(..., min_length=3, max_length=128)
    url: str = Field(..., min_length=10, max_length=2048)
    enabled: bool = True
    poll_interval_minutes: int = Field(default=15, ge=1, le=1440)

    # Source confidence baseline
    source_quality: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="Baseline quality score for this source [0,1]"
    )
    default_confidence: str = Field(
        default="moderate",
        description="Default confidence level: verified|high|moderate|low|unverified"
    )

    # Mapping hints
    default_regions: list[str] = Field(
        default_factory=list,
        description="Default GCC regions if feed items lack explicit region data"
    )
    default_domains: list[str] = Field(
        default_factory=list,
        description="Default impact domains for this feed"
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Tags applied to all signals from this feed"
    )

    # Optional auth (for JSON APIs)
    auth_header: Optional[str] = Field(
        None, description="Auth header name (e.g. 'X-Api-Key')"
    )
    auth_token_env: Optional[str] = Field(
        None, description="Env var name holding the auth token"
    )

    @field_validator("default_confidence")
    @classmethod
    def validate_confidence(cls, v: str) -> str:
        allowed = {"verified", "high", "moderate", "low", "unverified"}
        if v not in allowed:
            raise ValueError(f"confidence must be one of {allowed}")
        return v


# ── Raw Feed Item ───────────────────────────────────────────────────────────

class RawFeedItem(BaseModel):
    """A single item from an external feed, before mapping to MacroSignalInput.

    This is the adapter's output contract. Every adapter must produce these.
    """
    item_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Unique item ID (from source or generated)"
    )
    feed_id: str = Field(..., description="Which feed produced this item")
    feed_type: FeedType

    # Content fields
    title: str = Field(..., min_length=1, max_length=500)
    description: str = Field(default="", max_length=10000)
    url: Optional[str] = Field(None, max_length=2048)
    published_at: Optional[datetime] = None
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    # Structured data (adapter-specific)
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured payload from the source (varies by feed type)"
    )

    # Source metadata
    source_quality: float = Field(ge=0.0, le=1.0, default=0.5)
    confidence: str = Field(default="moderate")

    # Mapping hints (may be populated by adapter or left for mapper)
    region_hints: list[str] = Field(default_factory=list)
    domain_hints: list[str] = Field(default_factory=list)
    severity_hint: Optional[float] = Field(None, ge=0.0, le=1.0)
    direction_hint: Optional[str] = None
    signal_type_hint: Optional[str] = None

    # Dedup support
    content_hash: str = Field(
        default="",
        description="SHA-256 of canonical content for deduplication"
    )

    def compute_content_hash(self) -> str:
        """Deterministic content hash. Idempotent."""
        if self.content_hash:
            return self.content_hash
        canonical = json.dumps({
            "feed_id": self.feed_id,
            "title": self.title.strip().lower(),
            "published_at": self.published_at.isoformat() if self.published_at else "",
            "url": (self.url or "").strip(),
        }, sort_keys=True)
        self.content_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self.content_hash


# ── Feed Result ─────────────────────────────────────────────────────────────

class FeedResult(BaseModel):
    """Result of a single feed poll cycle."""
    feed_id: str
    feed_type: FeedType
    fetched_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    items_fetched: int = 0
    items_new: int = 0
    items_duplicate: int = 0
    items_rejected: int = 0
    items_routed: int = 0
    errors: list[str] = Field(default_factory=list)
    duration_ms: float = 0.0

    @property
    def success(self) -> bool:
        return len(self.errors) == 0


# ── Ingestion Record ────────────────────────────────────────────────────────

class IngestionRecord(BaseModel):
    """Audit record for a single signal through the ingestion pipeline."""
    record_id: UUID = Field(default_factory=uuid4)
    item_id: str
    feed_id: str
    content_hash: str
    status: IngestionStatus
    signal_id: Optional[UUID] = None  # Pack 1 signal ID if routed
    registry_id: Optional[UUID] = None  # Pack 1 registry ID if routed
    error: Optional[str] = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
