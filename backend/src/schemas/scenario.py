"""Schema 1: Scenario — defines an event trigger with severity/horizon."""

from __future__ import annotations

from pydantic import Field
from datetime import datetime

from src.schemas.base import VersionedModel


class ScenarioCreate(VersionedModel):
    """Input to create a scenario run."""
    template_id: str = Field(..., description="e.g. hormuz_disruption, yemen_escalation")
    severity: float = Field(..., ge=0.0, le=1.0, description="0.0–1.0 severity scale")
    horizon_hours: int = Field(336, ge=1, le=8760, description="Projection horizon in hours (default 14 days)")
    label: str | None = Field(None, description="Human-readable label e.g. 'Hormuz Closure - 14D - Severe'")


class Scenario(VersionedModel):
    """Full scenario record."""
    id: str
    template_id: str
    severity: float
    horizon_hours: int
    label: str | None = None
    status: str = Field("pending", pattern=r"^(pending|running|completed|failed)$")
    created_at: datetime | None = None
    completed_at: datetime | None = None
