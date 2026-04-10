"""Macro Intelligence Layer — Domain Models & Contracts.

These are the source-of-truth Pydantic models for Pack 1.
Every signal entering the system must conform to these contracts.

Domain types implemented:
  MacroSignalInput    — raw intake payload (what the caller sends)
  MacroSignal         — validated internal representation
  NormalizedSignal    — post-normalization, registry-ready object
  SignalRegistryEntry — persisted registry record with metadata
  SignalRejection     — structured rejection record for audit
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator, model_validator

from src.macro.macro_enums import (
    GCCRegion,
    ImpactDomain,
    SignalConfidence,
    SignalDirection,
    SignalSeverity,
    SignalSource,
    SignalStatus,
    SignalType,
)


# ── Raw Intake Payload ───────────────────────────────────────────────────────

class MacroSignalInput(BaseModel):
    """Contract for external signal submission. This is the API boundary.

    Callers must provide at minimum: title, source, severity_score, direction,
    and at least one affected region.
    """
    title: str = Field(
        ..., min_length=5, max_length=300,
        description="Human-readable signal title"
    )
    description: Optional[str] = Field(
        None, max_length=5000,
        description="Extended signal description"
    )
    source: SignalSource = Field(
        ..., description="Origin classification"
    )
    source_uri: Optional[str] = Field(
        None, max_length=2048,
        description="URI of the originating data feed or report"
    )
    severity_score: float = Field(
        ..., ge=0.0, le=1.0,
        description="Numeric severity [0.0, 1.0] — maps to SignalSeverity enum"
    )
    direction: SignalDirection = Field(
        ..., description="Directional impact on target domain"
    )
    confidence: SignalConfidence = Field(
        default=SignalConfidence.UNVERIFIED,
        description="Confidence level in signal accuracy"
    )
    regions: list[GCCRegion] = Field(
        ..., min_length=1,
        description="Affected GCC regions (at least one)"
    )
    impact_domains: list[ImpactDomain] = Field(
        default_factory=list,
        description="Target domains (optional at intake, inferred during normalization)"
    )
    event_time: Optional[datetime] = Field(
        None,
        description="When the event occurred (UTC). Defaults to intake time if absent."
    )
    ttl_hours: Optional[int] = Field(
        default=72, ge=1, le=8760,
        description="Signal time-to-live in hours (1h to 365d). Default 72h."
    )
    tags: list[str] = Field(
        default_factory=list, max_length=20,
        description="Free-form tags for categorization"
    )
    external_id: Optional[str] = Field(
        None, max_length=256,
        description="Caller-assigned external reference ID for deduplication"
    )

    # ── Pack 1 extended fields ────────────────────────────────────────────────

    signal_type: Optional[SignalType] = Field(
        None,
        description="Canonical signal type (geopolitical/policy/market/…). "
                    "Optional complement to source classification."
    )
    country_scope: list[str] = Field(
        default_factory=list,
        description="Specific countries affected (open string list, e.g. ['Kuwait', 'Iraq'])"
    )
    sector_scope: list[str] = Field(
        default_factory=list,
        description="Specific sectors affected (open string list, e.g. ['oil', 'banking'])"
    )
    raw_payload: Optional[dict[str, Any]] = Field(
        None,
        description="Unstructured originating data. Preserved as-is in normalized signal."
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v: list[str]) -> list[str]:
        """Lowercase, strip, deduplicate tags."""
        seen: set[str] = set()
        clean: list[str] = []
        for tag in v:
            t = tag.strip().lower()
            if t and t not in seen:
                seen.add(t)
                clean.append(t)
        return clean

    @field_validator("country_scope", "sector_scope")
    @classmethod
    def normalize_string_list(cls, v: list[str]) -> list[str]:
        """Strip whitespace, drop empty strings, deduplicate, sort for stable order."""
        seen: set[str] = set()
        clean: list[str] = []
        for item in v:
            s = " ".join(item.split())  # collapse internal whitespace
            if s and s not in seen:
                seen.add(s)
                clean.append(s)
        return sorted(clean)


# ── Internal Validated Signal ────────────────────────────────────────────────

class MacroSignal(BaseModel):
    """Internal representation after validation. Assigned an ID and timestamp."""
    signal_id: UUID = Field(default_factory=uuid4)
    title: str
    description: Optional[str] = None
    source: SignalSource
    source_uri: Optional[str] = None
    severity_score: float = Field(ge=0.0, le=1.0)
    severity_level: SignalSeverity
    direction: SignalDirection
    confidence: SignalConfidence
    regions: list[GCCRegion]
    impact_domains: list[ImpactDomain]
    event_time: datetime
    intake_time: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    ttl_hours: int = 72
    tags: list[str] = Field(default_factory=list)
    external_id: Optional[str] = None
    status: SignalStatus = SignalStatus.VALIDATED
    content_hash: str = Field(
        default="",
        description="SHA-256 hash of canonical signal content for dedup"
    )

    @model_validator(mode="after")
    def compute_content_hash(self) -> "MacroSignal":
        """Deterministic content hash for deduplication."""
        if not self.content_hash:
            canonical = json.dumps({
                "title": self.title,
                "source": self.source.value,
                "severity_score": round(self.severity_score, 4),
                "direction": self.direction.value,
                "regions": sorted(r.value for r in self.regions),
                "event_time": self.event_time.isoformat(),
            }, sort_keys=True)
            self.content_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self


# ── Normalized Signal (registry-ready) ───────────────────────────────────────

class NormalizedSignal(BaseModel):
    """Post-normalization signal. Ready for registry storage and downstream
    causal/propagation layers.

    Invariants:
      - severity_level matches severity_score thresholds
      - impact_domains is non-empty (inferred if not provided)
      - event_time is always UTC
      - expires_at is computed from intake_time + ttl_hours
      - content_hash is populated
    """
    signal_id: UUID
    title: str
    description: Optional[str] = None
    source: SignalSource
    source_uri: Optional[str] = None
    severity_score: float = Field(ge=0.0, le=1.0)
    severity_level: SignalSeverity
    direction: SignalDirection
    confidence: SignalConfidence
    regions: list[GCCRegion]
    impact_domains: list[ImpactDomain] = Field(min_length=1)
    event_time: datetime
    intake_time: datetime
    ttl_hours: int
    expires_at: datetime
    tags: list[str] = Field(default_factory=list)
    external_id: Optional[str] = None
    status: SignalStatus = SignalStatus.NORMALIZED
    content_hash: str
    normalization_version: str = "1.0.0"
    # Extended Pack 1 fields
    signal_type: Optional[SignalType] = None
    country_scope: list[str] = Field(default_factory=list)
    sector_scope: list[str] = Field(default_factory=list)
    raw_payload: Optional[dict[str, Any]] = None


# ── Registry Entry ───────────────────────────────────────────────────────────

class SignalRegistryEntry(BaseModel):
    """Persisted registry record. Wraps NormalizedSignal with registry metadata."""
    registry_id: UUID = Field(default_factory=uuid4)
    signal: NormalizedSignal
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    status: SignalStatus = SignalStatus.REGISTERED
    superseded_by: Optional[UUID] = None
    audit_hash: str = Field(
        default="",
        description="SHA-256 of the full registry entry for audit trail"
    )

    @model_validator(mode="after")
    def compute_audit_hash(self) -> "SignalRegistryEntry":
        if not self.audit_hash:
            canonical = json.dumps({
                "registry_id": str(self.registry_id),
                "signal_id": str(self.signal.signal_id),
                "content_hash": self.signal.content_hash,
                "registered_at": self.registered_at.isoformat(),
            }, sort_keys=True)
            self.audit_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self


# ── Rejection Record ─────────────────────────────────────────────────────────

class SignalRejection(BaseModel):
    """Structured rejection for audit. Every rejected signal gets one."""
    rejection_id: UUID = Field(default_factory=uuid4)
    input_payload: dict  # raw input as dict
    errors: list[str]
    rejected_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
    rejection_hash: str = ""

    @model_validator(mode="after")
    def compute_rejection_hash(self) -> "SignalRejection":
        if not self.rejection_hash:
            canonical = json.dumps({
                "rejection_id": str(self.rejection_id),
                "errors": sorted(self.errors),
                "rejected_at": self.rejected_at.isoformat(),
            }, sort_keys=True)
            self.rejection_hash = hashlib.sha256(canonical.encode()).hexdigest()
        return self


# ── API Response Wrappers ────────────────────────────────────────────────────

class SignalIntakeResponse(BaseModel):
    """Successful intake response."""
    signal_id: UUID
    registry_id: UUID
    status: SignalStatus
    severity_level: SignalSeverity
    content_hash: str
    message: str = "Signal accepted and registered"


class SignalRejectionResponse(BaseModel):
    """Rejection response."""
    rejection_id: UUID
    errors: list[str]
    message: str = "Signal rejected"


class SignalQueryResponse(BaseModel):
    """Single signal lookup response."""
    entry: SignalRegistryEntry


class SignalListResponse(BaseModel):
    """Paginated signal list response."""
    total: int
    offset: int
    limit: int
    entries: list[SignalRegistryEntry]
