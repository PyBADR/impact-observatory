"""Schema 6: BankingStress — banking sector stress metrics."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import VersionedModel


class BankingStress(VersionedModel):
    """Banking sector stress assessment."""
    run_id: str
    total_exposure_usd: float = Field(0.0, description="Total banking sector exposure")
    liquidity_stress: float = Field(0.0, ge=0.0, le=1.0, description="Liquidity stress index")
    credit_stress: float = Field(0.0, ge=0.0, le=1.0, description="Credit risk stress index")
    fx_stress: float = Field(0.0, ge=0.0, le=1.0, description="FX/currency stress index")
    interbank_contagion: float = Field(0.0, ge=0.0, le=1.0, description="Interbank contagion risk")
    time_to_liquidity_breach_hours: float = Field(float("inf"), description="Hours until liquidity breach")
    capital_adequacy_impact_pct: float = Field(0.0, description="Impact on CAR in percentage points")
    aggregate_stress: float = Field(0.0, ge=0.0, le=1.0, description="Weighted aggregate stress")
    liquidity_stress_ratio: float = Field(0.0, description="CashOutflows / AvailableLiquidity")
    capital_stress_ratio: float = Field(0.0, description="Loss / Capital (Basel III)")
    time_to_liquidity_breach_estimated_hours: float = Field(float("inf"), description="Estimated hours until liquidity_stress_ratio > 1.0")
    classification: str = Field("NOMINAL")
    affected_institutions: list[dict] = Field(default_factory=list)
