"""Schema 7: InsuranceStress — insurance sector stress metrics (IFRS-17 aligned)."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import VersionedModel


class InsuranceStress(VersionedModel):
    """Insurance sector stress assessment."""
    run_id: str
    portfolio_exposure_usd: float = Field(0.0, description="Total portfolio exposure")
    claims_surge_multiplier: float = Field(1.0, description="Claims surge multiplier over baseline")
    severity_index: float = Field(0.0, ge=0.0, le=1.0, description="Severity projection index")
    loss_ratio: float = Field(0.0, description="Projected loss ratio")
    combined_ratio: float = Field(0.0, description="Projected combined ratio")
    underwriting_status: str = Field("normal", description="normal|warning|critical|suspended")
    time_to_insolvency_hours: float = Field(float("inf"), description="Hours until reserve depletion")
    reinsurance_trigger: bool = Field(False, description="Whether reinsurance cascade is triggered")
    ifrs17_risk_adjustment_pct: float = Field(0.0, description="IFRS-17 risk adjustment change")
    aggregate_stress: float = Field(0.0, ge=0.0, le=1.0)
    classification: str = Field("NOMINAL")
    affected_lines: list[dict] = Field(default_factory=list)
