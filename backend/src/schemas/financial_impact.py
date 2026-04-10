"""Schema 5: FinancialImpact — computed financial loss per entity/sector."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import VersionedModel


class FinancialImpact(VersionedModel):
    """Financial loss computation for one entity or sector."""
    entity_id: str
    entity_label: str | None = None
    sector: str = Field(..., description="energy, maritime, aviation, banking, insurance, fintech, trade")
    loss_usd: float = Field(0.0, description="Estimated loss in USD")
    loss_pct_gdp: float = Field(0.0, description="Loss as percentage of GDP")
    peak_day: int = Field(0, description="Day of peak impact (1-indexed)")
    recovery_days: int = Field(0, description="Estimated days to recovery")
    confidence: float = Field(0.5, ge=0.0, le=1.0, description="Confidence in estimate")
    stress_level: float = Field(0.0, ge=0.0, le=1.0, description="Normalized stress 0–1")
    classification: str = Field("NOMINAL", pattern=r"^(NOMINAL|LOW|MODERATE|ELEVATED|CRITICAL)$")
