"""
Dataset I: Event Signals
==========================

Geopolitical, economic, regulatory, and operational events that may impact
GCC financial stability. Each event is classified, severity-scored, and
linked to affected entities and sectors.

Source: ACLED, GDELT, Reuters, analyst desk, government announcements
KG Mapping: (:Event)-[:IMPACTS]->(:Entity|:Sector|:Country)
Consumers: Simulation engine (shock injection), decision brain, alert system
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import Field

from src.data_foundation.schemas.base import FoundationModel, GeoCoordinate
from src.data_foundation.schemas.enums import (
    ConfidenceMethod,
    EventCategory,
    GCCCountry,
    Sector,
    SignalSeverity,
)

__all__ = ["EventSignal"]


class EventSignal(FoundationModel):
    """A classified event signal entering the intelligence pipeline."""

    event_id: str = Field(
        ...,
        description="Unique event identifier.",
        examples=["EVT-HORMUZ-20250115-001", "EVT-CBK-RATE-20250120-001"],
    )
    title: str = Field(
        ...,
        description="Short event headline.",
        examples=["Iran IRGC naval exercise near Strait of Hormuz"],
    )
    title_ar: Optional[str] = Field(
        default=None,
        description="Arabic headline.",
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed event description.",
    )
    category: EventCategory = Field(
        ...,
        description="Primary event classification.",
    )
    subcategory: Optional[str] = Field(
        default=None,
        description="More specific classification.",
        examples=["naval_exercise", "rate_decision", "sanctions_update", "port_closure"],
    )
    severity: SignalSeverity = Field(
        ...,
        description="Assessed severity level.",
    )
    severity_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Numeric severity [0.0–1.0] mapped to URS thresholds.",
    )
    event_time: datetime = Field(
        ...,
        description="When the event occurred or was announced (UTC).",
    )
    detected_at: datetime = Field(
        ...,
        description="When our system first detected this event (UTC).",
    )
    countries_affected: List[GCCCountry] = Field(
        default_factory=list,
        description="GCC countries directly affected.",
    )
    sectors_affected: List[Sector] = Field(
        default_factory=list,
        description="Sectors directly affected.",
    )
    entity_ids_affected: List[str] = Field(
        default_factory=list,
        description="Entity IDs directly affected (FK to entity_registry).",
    )
    scenario_ids: List[str] = Field(
        default_factory=list,
        description="Simulation scenarios this event may trigger.",
        examples=["hormuz_chokepoint_disruption", "kuwait_fiscal_shock"],
    )
    geo: Optional[GeoCoordinate] = Field(
        default=None,
        description="Event location coordinates.",
    )
    source_id: str = Field(
        ...,
        description="FK to source_registry.",
    )
    source_url: Optional[str] = Field(
        default=None,
        description="Original source URL.",
    )
    confidence_score: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
    )
    confidence_method: ConfidenceMethod = Field(
        default=ConfidenceMethod.DEFAULT,
    )
    corroborating_source_count: int = Field(
        default=1,
        ge=1,
        description="Number of independent sources confirming this event.",
    )
    is_ongoing: bool = Field(
        default=False,
        description="Whether this is an ongoing situation.",
    )
    parent_event_id: Optional[str] = Field(
        default=None,
        description="Parent event for event chains/escalation tracking.",
    )
    tags: List[str] = Field(
        default_factory=list,
    )
    raw_payload: Optional[Dict] = Field(
        default=None,
        description="Original source payload for audit and reprocessing.",
    )
