"""
Dataset D: Macro Indicators
=============================

GCC macroeconomic indicators: GDP, inflation, unemployment, fiscal balance,
current account, money supply, and composite indices.

Source: IMF, World Bank, GCC central banks, national statistics offices
KG Mapping: (:MacroIndicator)-[:MEASURES]->(:Country)
Consumers: Simulation engine (stage 2: macro context), decision calibration
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import Field

from src.data_foundation.schemas.base import FoundationModel
from src.data_foundation.schemas.enums import (
    ConfidenceMethod,
    Currency,
    GCCCountry,
    SourceReliability,
)

__all__ = ["MacroIndicatorRecord"]


class MacroIndicatorRecord(FoundationModel):
    """A single macroeconomic indicator observation for a GCC country."""

    indicator_id: str = Field(
        ...,
        description="Unique record ID (e.g., 'SA-GDP-2024Q4').",
    )
    country: GCCCountry = Field(
        ...,
        description="GCC country this indicator belongs to.",
    )
    indicator_code: str = Field(
        ...,
        description="Standardized indicator code.",
        examples=["GDP_REAL", "CPI_YOY", "UNEMPLOYMENT_RATE", "FISCAL_BALANCE_PCT_GDP",
                   "CURRENT_ACCOUNT_PCT_GDP", "M2_GROWTH_YOY", "PMI_COMPOSITE"],
    )
    indicator_name: str = Field(
        ...,
        description="Human-readable indicator name.",
        examples=["Real GDP Growth Rate (YoY %)", "Consumer Price Index (YoY %)"],
    )
    value: float = Field(
        ...,
        description="Observed value.",
    )
    unit: str = Field(
        ...,
        description="Unit of measurement.",
        examples=["percent", "basis_points", "billion_usd", "index_points"],
    )
    currency: Optional[Currency] = Field(
        default=None,
        description="Currency if the value is monetary.",
    )
    period_start: date = Field(
        ...,
        description="Start of the observation period.",
    )
    period_end: date = Field(
        ...,
        description="End of the observation period.",
    )
    frequency: str = Field(
        ...,
        description="Observation frequency.",
        examples=["monthly", "quarterly", "annual"],
    )
    source_id: str = Field(
        ...,
        description="FK to source_registry.",
    )
    source_reliability: SourceReliability = Field(
        default=SourceReliability.HIGH,
    )
    confidence_score: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence in this data point [0.0–1.0].",
    )
    confidence_method: ConfidenceMethod = Field(
        default=ConfidenceMethod.SOURCE_DECLARED,
    )
    is_provisional: bool = Field(
        default=False,
        description="Whether this is a preliminary/flash estimate.",
    )
    revision_number: int = Field(
        default=0,
        ge=0,
        description="Revision count (0 = first release).",
    )
    previous_value: Optional[float] = Field(
        default=None,
        description="Previous period value for delta computation.",
    )
    yoy_change_pct: Optional[float] = Field(
        default=None,
        description="Year-over-year change (%).",
    )
