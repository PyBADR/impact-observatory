"""Base model for all entities in the GCC Decision Intelligence Platform."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_validator

from .enums import ConfidenceLevel, SourceType


class BaseEntity(BaseModel):
    """Base model for all entities with common fields."""

    id: str = Field(default_factory=lambda: str(uuid4()), description="Unique identifier (UUID)")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when entity was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Timestamp when entity was last updated"
    )
    source_id: Optional[str] = Field(
        default=None, description="Identifier of the data source"
    )
    source_type: Optional[SourceType] = Field(
        default=None, description="Type of the data source"
    )
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)",
    )
    tags: list[str] = Field(
        default_factory=list, description="List of tags for categorization"
    )
    provenance: Optional[str] = Field(
        default=None, description="Provenance trail for data lineage"
    )

    model_config = {"use_enum_values": False}

    @field_validator("confidence")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Confidence must be between 0 and 1")
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(cls, v: list[str] | None) -> list[str]:
        """Ensure tags are non-empty strings."""
        if v is None:
            return []
        return [tag.strip() for tag in v if tag.strip()]

    @field_validator("updated_at", mode="before")
    @classmethod
    def validate_updated_at(cls, v: datetime | None) -> datetime:
        """Ensure updated_at is set to current time if not provided."""
        if v is None:
            return datetime.utcnow()
        return v


class SourceMetadata(BaseModel):
    """Metadata about a data source."""

    source_id: str = Field(description="Unique identifier for the source")
    source_type: SourceType = Field(description="Type of the source")
    confidence: ConfidenceLevel = Field(description="Confidence in the source")
    last_updated: datetime = Field(description="When the source was last updated")
    quality_score: float = Field(
        ge=0.0, le=1.0, description="Quality score of the source (0-1)"
    )
    url: Optional[str] = Field(default=None, description="Source URL if applicable")
    description: Optional[str] = Field(default=None, description="Description of the source")

    @field_validator("quality_score")
    @classmethod
    def validate_quality_score(cls, v: float) -> float:
        """Ensure quality score is valid."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Quality score must be between 0 and 1")
        return v
