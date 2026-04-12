"""
Dataset F: Oil & Energy Signals
=================================

Crude oil prices, OPEC+ production quotas, GCC production volumes,
LNG spot prices, and energy infrastructure status signals.

Source: OPEC, EIA, IEA, Platts, Argus, national oil companies
KG Mapping: (:EnergySignal)-[:AFFECTS]->(:Country|:Entity)
Consumers: Simulation engine (energy sector exposure), fiscal balance models
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import Field

from src.data_foundation.schemas.base import FoundationModel
from src.data_foundation.schemas.enums import (
    ConfidenceMethod,
    Currency,
    GCCCountry,
)

__all__ = ["OilEnergySignal"]


class OilEnergySignal(FoundationModel):
    """A single oil/energy market data point or production signal."""

    signal_id: str = Field(
        ...,
        description="Unique signal ID.",
        examples=["BRENT-SPOT-20250115", "SA-PROD-202501", "QA-LNG-SPOT-20250115"],
    )
    signal_type: str = Field(
        ...,
        description="Type of energy signal.",
        examples=["CRUDE_PRICE_SPOT", "CRUDE_PRICE_FUTURES", "PRODUCTION_VOLUME",
                   "OPEC_QUOTA", "LNG_SPOT_PRICE", "REFINERY_UTILIZATION",
                   "STRATEGIC_RESERVE_LEVEL", "EXPORT_VOLUME"],
    )
    benchmark: Optional[str] = Field(
        default=None,
        description="Price benchmark.",
        examples=["BRENT", "WTI", "OMAN_BLEND", "ARAB_LIGHT", "JKM_LNG"],
    )
    country: Optional[GCCCountry] = Field(
        default=None,
        description="GCC country (null for global benchmarks like Brent).",
    )
    entity_id: Optional[str] = Field(
        default=None,
        description="FK to entity_registry (e.g., specific refinery or field).",
    )
    value: float = Field(
        ...,
        description="Observed value.",
    )
    unit: str = Field(
        ...,
        description="Unit of measurement.",
        examples=["usd_per_barrel", "mbpd", "usd_per_mmbtu", "percent", "million_barrels"],
    )
    currency: Currency = Field(
        default=Currency.USD,
    )
    observation_date: date = Field(
        ...,
        description="Date of observation.",
    )
    previous_value: Optional[float] = Field(
        default=None,
        description="Previous observation for delta.",
    )
    change_pct: Optional[float] = Field(
        default=None,
        description="Percentage change from previous observation.",
    )
    fiscal_breakeven_price: Optional[float] = Field(
        default=None,
        description="Fiscal breakeven oil price for the country (USD/bbl).",
    )
    source_id: str = Field(
        ...,
        description="FK to source_registry.",
    )
    confidence_score: float = Field(
        default=0.85,
        ge=0.0,
        le=1.0,
    )
    confidence_method: ConfidenceMethod = Field(
        default=ConfidenceMethod.SOURCE_DECLARED,
    )
