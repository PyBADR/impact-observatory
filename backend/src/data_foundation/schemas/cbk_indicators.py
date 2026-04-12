"""
Dataset H: Kuwait CBK Indicators
==================================

Kuwait-specific central bank indicators from the Central Bank of Kuwait (CBK).
Includes monetary aggregates, banking system aggregates, credit growth,
and CBK-specific regulatory metrics.

This dataset exists as a dedicated P1 dataset because Kuwait is the primary
deployment market for Impact Observatory. Other GCC central bank data is
captured in macro_indicators and interest_rate_signals.

Source: CBK Statistical Bulletin, CBK Monthly Monetary Report
KG Mapping: (:CBKIndicator)-[:PUBLISHED_BY]->(:Entity{id:'KW-CBK'})
Consumers: Kuwait banking stress model, CBK regulatory dashboard
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import Field

from src.data_foundation.schemas.base import FoundationModel
from src.data_foundation.schemas.enums import ConfidenceMethod, Currency

__all__ = ["CBKIndicatorRecord"]


class CBKIndicatorRecord(FoundationModel):
    """A single CBK-published indicator observation."""

    indicator_id: str = Field(
        ...,
        description="Unique record ID (e.g., 'KW-CBK-M2-202501').",
    )
    indicator_code: str = Field(
        ...,
        description="CBK indicator code.",
        examples=[
            "M1_MONEY_SUPPLY", "M2_MONEY_SUPPLY", "TOTAL_BANK_DEPOSITS",
            "TOTAL_BANK_CREDIT", "PRIVATE_SECTOR_CREDIT", "GOVT_DEPOSITS",
            "INTERBANK_RATE_OVERNIGHT", "CBK_DISCOUNT_RATE",
            "NPL_RATIO", "CAPITAL_ADEQUACY_RATIO", "LIQUIDITY_RATIO",
            "TOTAL_BANK_ASSETS", "FOREIGN_ASSETS", "RESERVE_ASSETS",
            "CREDIT_GROWTH_YOY", "DEPOSIT_GROWTH_YOY",
        ],
    )
    indicator_name: str = Field(
        ...,
        description="Human-readable name.",
    )
    indicator_name_ar: Optional[str] = Field(
        default=None,
        description="Arabic indicator name.",
    )
    value: float = Field(
        ...,
        description="Observed value.",
    )
    unit: str = Field(
        ...,
        description="Unit of measurement.",
        examples=["million_kwd", "percent", "ratio", "basis_points", "billion_kwd"],
    )
    currency: Currency = Field(
        default=Currency.KWD,
    )
    period_start: date = Field(
        ...,
        description="Start of observation period.",
    )
    period_end: date = Field(
        ...,
        description="End of observation period.",
    )
    frequency: str = Field(
        default="monthly",
        description="Observation frequency.",
        examples=["daily", "weekly", "monthly", "quarterly"],
    )
    source_id: str = Field(
        default="cbk-statistical-bulletin",
        description="FK to source_registry.",
    )
    confidence_score: float = Field(
        default=0.95,
        ge=0.0,
        le=1.0,
    )
    confidence_method: ConfidenceMethod = Field(
        default=ConfidenceMethod.SOURCE_DECLARED,
    )
    is_provisional: bool = Field(
        default=False,
    )
    previous_value: Optional[float] = Field(
        default=None,
    )
    yoy_change_pct: Optional[float] = Field(
        default=None,
        description="Year-over-year change (%).",
    )
    mom_change_pct: Optional[float] = Field(
        default=None,
        description="Month-over-month change (%).",
    )
    regulatory_threshold: Optional[float] = Field(
        default=None,
        description="CBK regulatory minimum/maximum for this metric (if applicable).",
    )
    breach_status: Optional[str] = Field(
        default=None,
        description="Whether the value breaches the regulatory threshold.",
        examples=["WITHIN_LIMITS", "APPROACHING_LIMIT", "BREACHED"],
    )
