"""Schema 1: Scenario — defines an event trigger with severity/horizon."""

from __future__ import annotations

from pydantic import AliasChoices, Field
from datetime import datetime

from src.schemas.base import VersionedModel


class ScenarioCreate(VersionedModel):
    """Input to create a scenario run.

    Accepts both ``scenario_id`` (canonical) and ``template_id`` (v4 frontend alias).
    ``AliasChoices`` + the base model's ``populate_by_name=True`` ensures either field
    name is accepted in the request body.
    """
    scenario_id: str = Field(
        ...,
        validation_alias=AliasChoices("scenario_id", "template_id"),
        description="e.g. hormuz_chokepoint_disruption — also accepted as 'template_id'",
    )
    severity: float = Field(..., ge=0.0, le=1.0, description="0.0–1.0 severity scale")
    horizon_hours: int = Field(336, ge=1, le=8760, description="Projection horizon in hours (default 14 days)")
    label: str | None = Field(None, description="Human-readable label e.g. 'Strategic Maritime Chokepoint Disruption - 14D'")


class Scenario(VersionedModel):
    """Full scenario record."""
    id: str
    scenario_id: str
    severity: float
    horizon_hours: int
    label: str | None = None
    status: str = Field("pending", pattern=r"^(pending|running|completed|failed)$")
    created_at: datetime | None = None
    completed_at: datetime | None = None
