"""
Dataset J: Banking Sector Profiles
=====================================

Financial profiles for GCC commercial and investment banks.
Captures key prudential ratios, asset quality, P&L metrics, and
systemic importance indicators.

Source: Bank annual/quarterly reports, central bank publications, Bloomberg
KG Mapping: (:BankProfile)-[:PROFILES]->(:Entity{type:'commercial_bank'})
Consumers: Banking stress model (LSI computation), systemic risk analysis
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

__all__ = ["BankingSectorProfile"]


class BankingSectorProfile(FoundationModel):
    """Financial profile of a GCC bank at a point in time."""

    profile_id: str = Field(
        ...,
        description="Unique profile ID (e.g., 'KW-NBK-2024Q4').",
    )
    entity_id: str = Field(
        ...,
        description="FK to entity_registry.",
        examples=["KW-NBK", "SA-ALRAJHI", "AE-FAB"],
    )
    entity_name: str = Field(
        ...,
        description="Bank name for readability.",
    )
    country: GCCCountry = Field(...)
    reporting_date: date = Field(
        ...,
        description="End of reporting period.",
    )
    reporting_period: str = Field(
        ...,
        description="Reporting period label.",
        examples=["2024Q4", "2024H2", "2024FY"],
    )
    currency: Currency = Field(
        default=Currency.KWD,
    )

    # --- Size metrics ---
    total_assets: Optional[float] = Field(default=None, description="Total assets (millions).")
    total_deposits: Optional[float] = Field(default=None, description="Total deposits (millions).")
    total_loans: Optional[float] = Field(default=None, description="Total loans/financing (millions).")
    total_equity: Optional[float] = Field(default=None, description="Total equity (millions).")

    # --- Profitability ---
    net_income: Optional[float] = Field(default=None, description="Net income (millions).")
    roe_pct: Optional[float] = Field(default=None, description="Return on equity (%).")
    roa_pct: Optional[float] = Field(default=None, description="Return on assets (%).")
    cost_to_income_pct: Optional[float] = Field(default=None, description="Cost-to-income ratio (%).")
    nim_pct: Optional[float] = Field(default=None, description="Net interest margin (%).")

    # --- Asset quality ---
    npl_ratio_pct: Optional[float] = Field(default=None, description="Non-performing loan ratio (%).")
    npl_coverage_pct: Optional[float] = Field(default=None, description="NPL coverage ratio (%).")
    loan_loss_provision: Optional[float] = Field(default=None, description="Loan loss provision (millions).")

    # --- Capital adequacy ---
    car_pct: Optional[float] = Field(default=None, description="Capital adequacy ratio (%). Basel III minimum: 10.5%.")
    cet1_pct: Optional[float] = Field(default=None, description="CET1 ratio (%).")
    tier1_pct: Optional[float] = Field(default=None, description="Tier 1 capital ratio (%).")
    leverage_ratio_pct: Optional[float] = Field(default=None, description="Leverage ratio (%).")

    # --- Liquidity ---
    lcr_pct: Optional[float] = Field(default=None, description="Liquidity coverage ratio (%). Basel III minimum: 100%.")
    nsfr_pct: Optional[float] = Field(default=None, description="Net stable funding ratio (%).")
    loan_to_deposit_pct: Optional[float] = Field(default=None, description="Loan-to-deposit ratio (%).")

    # --- Systemic importance ---
    is_dsib: bool = Field(default=False, description="Domestic systemically important bank.")
    dsib_buffer_pct: Optional[float] = Field(default=None, description="D-SIB capital surcharge (%).")

    # --- Metadata ---
    source_id: str = Field(..., description="FK to source_registry.")
    confidence_score: float = Field(default=0.85, ge=0.0, le=1.0)
    confidence_method: ConfidenceMethod = Field(default=ConfidenceMethod.SOURCE_DECLARED)
    is_audited: bool = Field(default=False, description="Whether figures are from audited financials.")
    auditor: Optional[str] = Field(default=None, examples=["KPMG", "PwC", "EY", "Deloitte"])
    tags: List[str] = Field(default_factory=list)
