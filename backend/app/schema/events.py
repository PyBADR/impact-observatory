"""Event and incident models for the GCC Decision Intelligence Platform."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator

from .base import BaseEntity
from .enums import AlertStatus, EventType, SeverityLevel, SourceType
from .geo import GeoPoint


class SourceRecord(BaseEntity):
    """A raw record from a data source."""

    source_identifier: str = Field(description="Original identifier from the source")
    raw_data: dict[str, Any] = Field(description="Raw unprocessed data from source")
    normalized_data: Optional[dict[str, Any]] = Field(
        default=None, description="Normalized/extracted data"
    )
    processing_status: str = Field(
        default="pending", description="Status of data processing"
    )
    error_message: Optional[str] = Field(
        default=None, description="Error message if processing failed"
    )
    processed_at: Optional[datetime] = Field(
        default=None, description="Timestamp when record was processed"
    )

    @field_validator("source_type")
    @classmethod
    def validate_source_type(cls, v: SourceType | None) -> SourceType | None:
        """Ensure source_type is valid."""
        return v


class Signal(BaseEntity):
    """A signal or indicator from a data source."""

    name: str = Field(description="Name of the signal")
    description: Optional[str] = Field(default=None, description="Signal description")
    value: float | int | str | bool = Field(description="Signal value")
    unit: Optional[str] = Field(default=None, description="Unit of measurement")
    signal_type: str = Field(description="Type of signal (e.g., temperature, count, status)")
    detected_at: datetime = Field(description="When the signal was detected")
    location: Optional[GeoPoint] = Field(
        default=None, description="Location where signal was detected"
    )
    related_entity_id: Optional[str] = Field(
        default=None, description="ID of related entity"
    )
    related_entity_type: Optional[str] = Field(
        default=None, description="Type of related entity"
    )

    @field_validator("detected_at", mode="before")
    @classmethod
    def validate_detected_at(cls, v: datetime | None) -> datetime:
        """Ensure detected_at is set."""
        if v is None:
            return datetime.utcnow()
        return v


class Event(BaseEntity):
    """A recorded event in the system."""

    name: str = Field(description="Event name")
    description: str = Field(description="Detailed description of the event")
    description_ar: Optional[str] = Field(
        default=None, description="Arabic description of the event"
    )
    event_type: EventType = Field(description="Type of event")
    severity: float = Field(
        ge=0.0, le=1.0, description="Severity level (0-1)"
    )
    location: GeoPoint = Field(description="Geographic location of the event")
    start_time: datetime = Field(description="When the event started")
    end_time: Optional[datetime] = Field(
        default=None, description="When the event ended (if applicable)"
    )
    actors: list[str] = Field(
        default_factory=list, description="List of actor IDs involved"
    )
    affected_entities: dict[str, list[str]] = Field(
        default_factory=dict,
        description="Mapping of entity types to affected entity IDs",
    )
    sources: list[SourceRecord] = Field(
        default_factory=list, description="Source records for this event"
    )
    impact_summary: Optional[str] = Field(
        default=None, description="Summary of event impact"
    )
    external_references: list[str] = Field(
        default_factory=list, description="External URLs and references"
    )

    @field_validator("severity")
    @classmethod
    def validate_severity(cls, v: float) -> float:
        """Ensure severity is between 0 and 1."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("Severity must be between 0 and 1")
        return v

    @field_validator("end_time")
    @classmethod
    def validate_end_time(cls, v: datetime | None, info) -> datetime | None:
        """Ensure end_time is after start_time if provided."""
        if v is not None and "start_time" in info.data:
            if v < info.data["start_time"]:
                raise ValueError("End time must be after start time")
        return v


class Incident(Event):
    """A critical incident event."""

    incident_id: str = Field(description="Unique incident identifier")
    status: str = Field(
        default="active", description="Incident status (active, resolved, archived)"
    )
    priority: int = Field(
        default=3, ge=1, le=5, description="Priority level (1=highest, 5=lowest)"
    )
    assigned_team: Optional[str] = Field(
        default=None, description="ID of assigned response team"
    )
    response_actions: list[str] = Field(
        default_factory=list, description="List of response actions taken"
    )
    estimated_resolution_time: Optional[datetime] = Field(
        default=None, description="Estimated time for resolution"
    )
    root_cause: Optional[str] = Field(
        default=None, description="Identified root cause"
    )

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: int) -> int:
        """Ensure priority is valid."""
        if not 1 <= v <= 5:
            raise ValueError("Priority must be between 1 and 5")
        return v


class Alert(BaseEntity):
    """An alert notification in the system."""

    title: str = Field(description="Alert title")
    description: str = Field(description="Alert description")
    severity: SeverityLevel = Field(description="Severity level")
    status: AlertStatus = Field(default=AlertStatus.NEW, description="Current alert status")
    triggered_by_event_id: Optional[str] = Field(
        default=None, description="ID of triggering event"
    )
    triggered_by_signal_id: Optional[str] = Field(
        default=None, description="ID of triggering signal"
    )
    location: Optional[GeoPoint] = Field(
        default=None, description="Geographic location of the alert"
    )
    affected_entities: dict[str, list[str]] = Field(
        default_factory=dict, description="Mapping of entity types to affected entity IDs"
    )
    recipients: list[str] = Field(
        default_factory=list, description="List of user/team IDs to notify"
    )
    recommendations: list[str] = Field(
        default_factory=list, description="Recommended actions"
    )
    acknowledged_by: Optional[str] = Field(
        default=None, description="User ID who acknowledged the alert"
    )
    acknowledged_at: Optional[datetime] = Field(
        default=None, description="When the alert was acknowledged"
    )
    resolved_at: Optional[datetime] = Field(
        default=None, description="When the alert was resolved"
    )

    @field_validator("resolved_at")
    @classmethod
    def validate_resolved_at(cls, v: datetime | None, info) -> datetime | None:
        """Ensure resolved_at is after created_at if provided."""
        if v is not None and "created_at" in info.data:
            if v < info.data["created_at"]:
                raise ValueError("Resolved time must be after creation time")
        return v
