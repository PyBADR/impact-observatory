"""Schema 4: FlowState — physics engine output per entity per timestep."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import VersionedModel


class FlowState(VersionedModel):
    """Physics simulation state for one entity at one timestep."""
    entity_id: str
    timestep_hours: float
    pressure: float = Field(0.0, description="Stress pressure 0.0–1.0")
    flow_magnitude: float = Field(0.0, description="Flow magnitude through this node")
    threat_level: float = Field(0.0, description="Threat field intensity")
    shockwave_amplitude: float = Field(0.0, description="Shockwave amplitude at this node")
    friction: float = Field(0.0, description="Resistance/friction coefficient")
    system_stress: float = Field(0.0, description="Aggregate system stress 0.0–1.0")
    route_efficiency: float = Field(1.0, description="Route efficiency = 1.0 - friction")
    delay_hours: float = Field(0.0, description="Delay(t) = BaseDelay × CongestionFactor")
