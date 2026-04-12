"""
P1 Data Foundation — Base Model
================================

All P1 schemas inherit from FoundationModel, which extends the existing
VersionedModel with provenance, multi-tenant, and audit trail fields
required for production GCC intelligence data.

Design Principles:
  - schema_version for backward-compatible evolution
  - tenant_id for multi-tenant data isolation
  - created_at / updated_at for temporal tracking
  - provenance_hash (SHA-256) for audit trail integrity
  - country_code for GCC entity linkage
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

__all__ = ["FoundationModel", "AuditMixin", "GeoCoordinate"]


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _uuid() -> str:
    return str(uuid4())


class FoundationModel(BaseModel):
    """Base for all P1 Data Foundation schemas.

    Provides:
      - schema_version: API/schema versioning for migrations
      - tenant_id: Multi-tenant isolation key (nullable for global datasets)
      - created_at / updated_at: Temporal audit fields (UTC, timezone-aware)
      - provenance_hash: SHA-256 of the record's canonical JSON for tamper detection
    """

    schema_version: str = Field(
        default="1.0.0",
        description="SemVer schema version for migration tracking.",
    )
    tenant_id: Optional[str] = Field(
        default=None,
        description="Multi-tenant isolation key. Null for global reference data.",
    )
    created_at: datetime = Field(
        default_factory=_utcnow,
        description="Record creation timestamp (UTC).",
    )
    updated_at: datetime = Field(
        default_factory=_utcnow,
        description="Last modification timestamp (UTC).",
    )
    provenance_hash: Optional[str] = Field(
        default=None,
        description="SHA-256 hash of canonical record JSON for audit integrity.",
    )

    model_config = ConfigDict(
        from_attributes=True,
        extra="ignore",
        populate_by_name=True,
        json_schema_extra={"x-layer": "data-foundation-p1"},
    )

    def compute_provenance_hash(self) -> str:
        """Compute SHA-256 of the record excluding provenance_hash itself."""
        data = self.model_dump(exclude={"provenance_hash", "created_at", "updated_at"})
        canonical = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    @model_validator(mode="after")
    def _set_provenance(self) -> "FoundationModel":
        if self.provenance_hash is None:
            self.provenance_hash = self.compute_provenance_hash()
        return self


class AuditMixin(BaseModel):
    """Mixin for records that need explicit audit trail fields."""
    created_by: Optional[str] = Field(
        default=None,
        description="User or system that created this record.",
    )
    approved_by: Optional[str] = Field(
        default=None,
        description="User who approved this record (human-in-the-loop).",
    )
    audit_notes: Optional[str] = Field(
        default=None,
        description="Free-text audit annotation.",
    )


class GeoCoordinate(BaseModel):
    """Reusable geographic coordinate pair."""
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)

    model_config = ConfigDict(frozen=True)
