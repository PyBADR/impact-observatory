"""
Dataset G: FX Signals
=======================

Foreign exchange rates for GCC currencies. Most GCC currencies maintain
fixed or managed pegs to USD. KWD uses a basket peg.

Source: Central banks, Reuters, Bloomberg, XE
KG Mapping: (:FXSignal)-[:DENOMINATES]->(:Currency)
Consumers: Cross-border exposure modeling, insurance premium conversion
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
)

__all__ = ["FXSignal"]


class FXSignal(FoundationModel):
    """A single FX rate observation."""

    signal_id: str = Field(
        ...,
        description="Unique signal ID (e.g., 'USDSAR-20250115').",
    )
    base_currency: Currency = Field(
        ...,
        description="Base currency (numerator).",
    )
    quote_currency: Currency = Field(
        ...,
        description="Quote currency (denominator).",
    )
    country: Optional[GCCCountry] = Field(
        default=None,
        description="Primary GCC country for this pair.",
    )
    rate: float = Field(
        ...,
        gt=0.0,
        description="Exchange rate (base/quote).",
    )
    rate_type: str = Field(
        default="SPOT",
        description="Rate type.",
        examples=["SPOT", "FORWARD_1M", "FORWARD_3M", "FORWARD_6M", "FORWARD_12M",
                   "CENTRAL_BANK_OFFICIAL"],
    )
    observation_date: date = Field(
        ...,
        description="Date of observation.",
    )
    peg_rate: Optional[float] = Field(
        default=None,
        description="Official peg rate (null if floating).",
    )
    deviation_from_peg_bps: Optional[int] = Field(
        default=None,
        description="Deviation from peg in basis points. Alerts if > threshold.",
    )
    bid: Optional[float] = Field(default=None, description="Bid rate.")
    ask: Optional[float] = Field(default=None, description="Ask rate.")
    spread_bps: Optional[int] = Field(
        default=None,
        description="Bid-ask spread in basis points.",
    )
    daily_high: Optional[float] = Field(default=None)
    daily_low: Optional[float] = Field(default=None)
    previous_close: Optional[float] = Field(default=None)
    change_pct: Optional[float] = Field(
        default=None,
        description="Daily change percentage.",
    )
    source_id: str = Field(
        ...,
        description="FK to source_registry.",
    )
    confidence_score: float = Field(
        default=0.90,
        ge=0.0,
        le=1.0,
    )
    confidence_method: ConfidenceMethod = Field(
        default=ConfidenceMethod.SOURCE_DECLARED,
    )
