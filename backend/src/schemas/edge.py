"""Schema 3: Edge — a dependency link between entities."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import VersionedModel


class Edge(VersionedModel):
    """A directed edge in the entity graph."""
    source_id: str
    target_id: str
    edge_type: str = Field(..., description="supply, financial, route, regulatory, insurance")
    weight: float = Field(1.0, ge=0.0, description="Propagation weight")
    delay_hours: float = Field(0.0, ge=0.0, description="Propagation delay in hours")
    metadata: dict | None = None
