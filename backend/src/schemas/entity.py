"""Schema 2: Entity — a node in the GCC economic graph."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import VersionedModel


class Entity(VersionedModel):
    """A node in the entity graph (port, bank, refinery, exchange, etc.)."""
    id: str
    label: str
    label_ar: str | None = None
    layer: str = Field(..., description="energy, maritime, aviation, finance, infrastructure, government")
    entity_type: str = Field(..., description="port, bank, refinery, exchange, airport, ministry, etc.")
    country: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    gdp_weight: float = Field(0.0, ge=0.0, le=1.0, description="Fractional GDP contribution")
    criticality: float = Field(0.5, ge=0.0, le=1.0, description="Infrastructure criticality score")
    metadata: dict | None = None
