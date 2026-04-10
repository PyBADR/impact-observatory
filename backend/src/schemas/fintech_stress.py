"""Schema 8: FintechStress — fintech/payments sector stress metrics."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import VersionedModel


class FintechStress(VersionedModel):
    """Fintech sector stress assessment."""
    run_id: str
    payment_volume_impact_pct: float = Field(0.0, description="% drop in payment volumes")
    settlement_delay_hours: float = Field(0.0, description="Additional settlement delay")
    api_availability_pct: float = Field(100.0, description="API/gateway availability %")
    cross_border_disruption: float = Field(0.0, ge=0.0, le=1.0, description="Cross-border payment disruption index")
    digital_banking_stress: float = Field(0.0, ge=0.0, le=1.0, description="Digital banking channel stress")
    time_to_payment_failure_hours: float = Field(float("inf"), description="Hours until payment system failure")
    aggregate_stress: float = Field(0.0, ge=0.0, le=1.0)
    classification: str = Field("NOMINAL")
    affected_platforms: list[dict] = Field(default_factory=list)
