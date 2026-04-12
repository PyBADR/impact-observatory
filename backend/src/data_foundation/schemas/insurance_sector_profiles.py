"""
Dataset K: Insurance Sector Profiles
=======================================

Financial profiles for GCC insurers and reinsurers.
Captures premium volumes, claims ratios, solvency, investment yield,
and IFRS 17 transition metrics.

Source: Regulator publications, insurer annual reports, AM Best, S&P
KG Mapping: (:InsuranceProfile)-[:PROFILES]->(:Entity{type:'insurer'})
Consumers: Insurance stress model (ISI computation), IFRS 17 compliance
"""

from __future__ import annotations

from datetime import date
from typing import List, Optional

from pydantic import Field

from src.data_foundation.schemas.base import FoundationModel
from src.data_foundation.schemas.enums import (
    ConfidenceMethod,
    Currency,
    GCCCountry,
)

__all__ = ["InsuranceSectorProfile"]


class InsuranceSectorProfile(FoundationModel):
    """Financial profile of a GCC insurer at a point in time."""

    profile_id: str = Field(
        ...,
        description="Unique profile ID (e.g., 'KW-GIG-2024FY').",
    )
    entity_id: str = Field(
        ...,
        description="FK to entity_registry.",
        examples=["KW-GIG", "SA-TAWUNIYA", "AE-ORIENT"],
    )
    entity_name: str = Field(...)
    country: GCCCountry = Field(...)
    insurance_type: str = Field(
        ...,
        description="Type of insurance business.",
        examples=["COMPOSITE", "GENERAL", "LIFE", "TAKAFUL", "REINSURANCE"],
    )
    reporting_date: date = Field(...)
    reporting_period: str = Field(
        ...,
        examples=["2024FY", "2024H1"],
    )
    currency: Currency = Field(default=Currency.KWD)

    # --- Premium metrics ---
    gwp: Optional[float] = Field(default=None, description="Gross written premiums (millions).")
    nwp: Optional[float] = Field(default=None, description="Net written premiums (millions).")
    nep: Optional[float] = Field(default=None, description="Net earned premiums (millions).")
    retention_ratio_pct: Optional[float] = Field(default=None, description="Retention ratio (%).")

    # --- Claims & underwriting ---
    net_claims_incurred: Optional[float] = Field(default=None, description="Net claims incurred (millions).")
    loss_ratio_pct: Optional[float] = Field(default=None, description="Loss ratio (%).")
    combined_ratio_pct: Optional[float] = Field(default=None, description="Combined ratio (%).")
    expense_ratio_pct: Optional[float] = Field(default=None, description="Expense ratio (%).")
    underwriting_result: Optional[float] = Field(default=None, description="Underwriting profit/loss (millions).")

    # --- Investment ---
    investment_income: Optional[float] = Field(default=None, description="Investment income (millions).")
    investment_yield_pct: Optional[float] = Field(default=None, description="Investment yield (%).")
    total_investments: Optional[float] = Field(default=None, description="Total investment portfolio (millions).")

    # --- Solvency ---
    total_assets: Optional[float] = Field(default=None, description="Total assets (millions).")
    total_equity: Optional[float] = Field(default=None, description="Total equity (millions).")
    solvency_ratio_pct: Optional[float] = Field(default=None, description="Solvency ratio (%).")
    minimum_capital_required: Optional[float] = Field(default=None, description="MCR (millions).")
    solvency_capital_required: Optional[float] = Field(default=None, description="SCR (millions).")

    # --- IFRS 17 ---
    ifrs17_adopted: bool = Field(default=False, description="Whether IFRS 17 is adopted.")
    csm_balance: Optional[float] = Field(
        default=None,
        description="Contractual Service Margin balance (millions). IFRS 17 specific.",
    )
    risk_adjustment: Optional[float] = Field(
        default=None,
        description="Risk adjustment for non-financial risk (millions). IFRS 17 specific.",
    )
    insurance_revenue: Optional[float] = Field(
        default=None,
        description="Insurance revenue under IFRS 17 (millions).",
    )

    # --- Rating ---
    am_best_rating: Optional[str] = Field(default=None, examples=["A", "A-", "B++"])
    sp_rating: Optional[str] = Field(default=None, examples=["A", "BBB+", "BB"])

    # --- Metadata ---
    source_id: str = Field(..., description="FK to source_registry.")
    confidence_score: float = Field(default=0.80, ge=0.0, le=1.0)
    confidence_method: ConfidenceMethod = Field(default=ConfidenceMethod.SOURCE_DECLARED)
    is_audited: bool = Field(default=False)
    tags: List[str] = Field(default_factory=list)
