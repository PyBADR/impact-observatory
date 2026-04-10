"""Schema 12: RegulatoryState — regulatory compliance state per run."""

from __future__ import annotations

from pydantic import Field

from src.schemas.base import VersionedModel


class RegulatoryState(VersionedModel):
    """Regulatory compliance state for a run."""
    run_id: str
    basel_iii_car_impact_pct: float = Field(0.0, description="Capital adequacy ratio impact")
    basel_iii_lcr_stress: float = Field(0.0, ge=0.0, le=1.0, description="Liquidity coverage ratio stress")
    basel_iii_nsfr_stress: float = Field(0.0, ge=0.0, le=1.0, description="Net stable funding ratio stress")
    ifrs17_risk_adjustment_pct: float = Field(0.0, description="IFRS-17 risk adjustment change")
    ifrs17_loss_component_usd: float = Field(0.0, description="IFRS-17 loss component")
    solvency_margin_impact_pct: float = Field(0.0, description="Insurance solvency margin impact")
    payment_system_compliance: str = Field("compliant", description="compliant|warning|breach")
    cross_border_regulatory_risk: float = Field(0.0, ge=0.0, le=1.0)
    aggregate_regulatory_risk: float = Field(0.0, ge=0.0, le=1.0)
    classification: str = Field("NOMINAL")
