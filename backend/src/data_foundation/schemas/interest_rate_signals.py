"""
Dataset E: Interest Rate Signals
==================================

Central bank policy rates, interbank rates, and yield curve data for GCC.
GCC rates are tightly coupled to Fed Funds Rate due to USD pegs (except KWD).

Source: Central banks (SAMA, CBUAE, CBK, QCB, CBB, CBO), Fed, Bloomberg
KG Mapping: (:InterestRateSignal)-[:ISSUED_BY]->(:CentralBank)
Consumers: Banking stress models, insurance investment yield projections
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

__all__ = ["InterestRateSignal"]


class InterestRateSignal(FoundationModel):
    """A single interest rate observation or policy rate change."""

    signal_id: str = Field(
        ...,
        description="Unique signal ID (e.g., 'KW-CBK-DISCOUNT-20250115').",
    )
    country: GCCCountry = Field(
        ...,
        description="GCC country.",
    )
    issuer_entity_id: str = Field(
        ...,
        description="FK to entity_registry — the central bank or authority.",
        examples=["KW-CBK", "SA-SAMA", "AE-CBUAE"],
    )
    rate_type: str = Field(
        ...,
        description="Type of interest rate.",
        examples=["POLICY_RATE", "DISCOUNT_RATE", "REPO_RATE", "REVERSE_REPO_RATE",
                   "INTERBANK_OVERNIGHT", "INTERBANK_1M", "INTERBANK_3M",
                   "GOVT_BOND_2Y", "GOVT_BOND_5Y", "GOVT_BOND_10Y"],
    )
    rate_value_bps: int = Field(
        ...,
        description="Rate in basis points (e.g., 425 = 4.25%).",
    )
    rate_value_pct: float = Field(
        ...,
        description="Rate as percentage (e.g., 4.25).",
    )
    effective_date: date = Field(
        ...,
        description="Date the rate becomes effective.",
    )
    previous_rate_bps: Optional[int] = Field(
        default=None,
        description="Previous rate in basis points.",
    )
    change_bps: Optional[int] = Field(
        default=None,
        description="Change from previous rate in basis points.",
    )
    reference_rate: Optional[str] = Field(
        default=None,
        description="Reference rate this tracks (e.g., 'FED_FUNDS_RATE').",
    )
    spread_to_reference_bps: Optional[int] = Field(
        default=None,
        description="Spread to reference rate in basis points.",
    )
    currency: Currency = Field(
        default=Currency.USD,
        description="Currency denomination.",
    )
    source_id: str = Field(
        ...,
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
    is_scheduled_decision: bool = Field(
        default=False,
        description="Whether this was from a scheduled policy meeting.",
    )
    next_decision_date: Optional[date] = Field(
        default=None,
        description="Next scheduled policy rate decision date.",
    )
