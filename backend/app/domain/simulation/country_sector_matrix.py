"""
Impact Observatory | مرصد الأثر — Phase 3 Country-Sector Matrix
GCC-specific cross-tab profiles: how each country's structure shapes
sector-level stress transmission.

This matrix answers: "Given stress in sector X in country A,
how much stress reaches sector Y in country B?"

The matrix is NOT a flat coupling table. Each cell encodes:
  - coupling: base transmission weight 0–1
  - channel: human-readable transmission narrative
  - lag_hours: how long before stress materializes
  - amplifier_key: which country-meta field amplifies the coupling

Sources:
  IMF FSAP reports, BIS locational banking stats, GCC central bank
  financial stability reviews, SAMA/CBUAE/CBK annual reports.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MatrixCell:
    """One cell in the country-sector transmission matrix."""
    coupling: float        # base weight 0–1
    channel: str           # human-readable label
    lag_hours: float       # delay before stress arrives
    amplifier_key: str     # country_meta key that scales coupling


# ═══════════════════════════════════════════════════════════════════════════════
# Country Profiles — structural characteristics that shape transmission
# ═══════════════════════════════════════════════════════════════════════════════

COUNTRY_PROFILES: dict[str, dict[str, float]] = {
    "KWT": {
        "fiscal_oil_dependency": 0.90,
        "sovereign_buffer_months": 36.0,
        "real_estate_gdp_share": 0.07,
        "gov_spending_multiplier": 1.25,
        "developer_leverage_ratio": 0.55,
        "state_ownership_share": 0.72,
        "infrastructure_pipeline_usd": 35.0e9,
    },
    "SAU": {
        "fiscal_oil_dependency": 0.62,
        "sovereign_buffer_months": 48.0,
        "real_estate_gdp_share": 0.08,
        "gov_spending_multiplier": 1.40,
        "developer_leverage_ratio": 0.48,
        "state_ownership_share": 0.65,
        "infrastructure_pipeline_usd": 180.0e9,  # Vision 2030
    },
    "UAE": {
        "fiscal_oil_dependency": 0.36,
        "sovereign_buffer_months": 24.0,
        "real_estate_gdp_share": 0.14,
        "gov_spending_multiplier": 1.15,
        "developer_leverage_ratio": 0.72,
        "state_ownership_share": 0.45,
        "infrastructure_pipeline_usd": 120.0e9,
    },
    "QAT": {
        "fiscal_oil_dependency": 0.70,
        "sovereign_buffer_months": 42.0,
        "real_estate_gdp_share": 0.09,
        "gov_spending_multiplier": 1.30,
        "developer_leverage_ratio": 0.50,
        "state_ownership_share": 0.68,
        "infrastructure_pipeline_usd": 55.0e9,
    },
    "BHR": {
        "fiscal_oil_dependency": 0.75,
        "sovereign_buffer_months": 4.0,
        "real_estate_gdp_share": 0.06,
        "gov_spending_multiplier": 1.10,
        "developer_leverage_ratio": 0.60,
        "state_ownership_share": 0.55,
        "infrastructure_pipeline_usd": 8.0e9,
    },
    "OMN": {
        "fiscal_oil_dependency": 0.68,
        "sovereign_buffer_months": 12.0,
        "real_estate_gdp_share": 0.05,
        "gov_spending_multiplier": 1.15,
        "developer_leverage_ratio": 0.52,
        "state_ownership_share": 0.58,
        "infrastructure_pipeline_usd": 25.0e9,
    },
}


# ═══════════════════════════════════════════════════════════════════════════════
# Government Sector — outbound transmission matrix
# How government stress radiates into other sectors
# ═══════════════════════════════════════════════════════════════════════════════

GOV_OUTBOUND: dict[str, MatrixCell] = {
    "banking": MatrixCell(
        coupling=0.55,
        channel="Sovereign deposit withdrawal + government bond repricing",
        lag_hours=12,
        amplifier_key="fiscal_oil_dependency",
    ),
    "insurance": MatrixCell(
        coupling=0.30,
        channel="Government insurance contract cancellation + mandate repricing",
        lag_hours=48,
        amplifier_key="state_ownership_share",
    ),
    "real_estate": MatrixCell(
        coupling=0.65,
        channel="Infrastructure spending freeze + permit moratorium",
        lag_hours=24,
        amplifier_key="infrastructure_pipeline_usd",  # scaled by pipeline size
    ),
    "fintech": MatrixCell(
        coupling=0.25,
        channel="Digital government services budget cut + regulatory uncertainty",
        lag_hours=72,
        amplifier_key="gov_spending_multiplier",
    ),
    "oil_gas": MatrixCell(
        coupling=0.35,
        channel="National oil company capex revision + royalty regime change",
        lag_hours=48,
        amplifier_key="state_ownership_share",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Government Sector — inbound transmission matrix
# How other sectors push stress into government
# ═══════════════════════════════════════════════════════════════════════════════

GOV_INBOUND: dict[str, MatrixCell] = {
    "oil_gas": MatrixCell(
        coupling=0.70,
        channel="Fiscal revenue collapse from energy price shock",
        lag_hours=6,
        amplifier_key="fiscal_oil_dependency",
    ),
    "banking": MatrixCell(
        coupling=0.40,
        channel="Banking sector bailout obligation + deposit guarantee activation",
        lag_hours=24,
        amplifier_key="state_ownership_share",
    ),
    "real_estate": MatrixCell(
        coupling=0.35,
        channel="Developer default contagion to state-backed projects",
        lag_hours=72,
        amplifier_key="infrastructure_pipeline_usd",
    ),
    "insurance": MatrixCell(
        coupling=0.20,
        channel="Government reinsurance obligation for catastrophe events",
        lag_hours=48,
        amplifier_key="state_ownership_share",
    ),
    "fintech": MatrixCell(
        coupling=0.10,
        channel="Digital payment system failure forces manual government disbursement",
        lag_hours=24,
        amplifier_key="gov_spending_multiplier",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Real Estate Sector — outbound transmission matrix
# ═══════════════════════════════════════════════════════════════════════════════

RE_OUTBOUND: dict[str, MatrixCell] = {
    "banking": MatrixCell(
        coupling=0.70,
        channel="Developer NPL cascade + mortgage default wave",
        lag_hours=24,
        amplifier_key="developer_leverage_ratio",
    ),
    "government": MatrixCell(
        coupling=0.40,
        channel="State-backed project cost overruns + land revenue decline",
        lag_hours=48,
        amplifier_key="infrastructure_pipeline_usd",
    ),
    "insurance": MatrixCell(
        coupling=0.35,
        channel="Construction insurance claims + surety bond defaults",
        lag_hours=36,
        amplifier_key="developer_leverage_ratio",
    ),
    "fintech": MatrixCell(
        coupling=0.15,
        channel="PropTech funding freeze + digital mortgage origination halt",
        lag_hours=48,
        amplifier_key="real_estate_gdp_share",
    ),
    "oil_gas": MatrixCell(
        coupling=0.10,
        channel="Reduced industrial zone construction for energy infrastructure",
        lag_hours=96,
        amplifier_key="real_estate_gdp_share",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Real Estate Sector — inbound transmission matrix
# ═══════════════════════════════════════════════════════════════════════════════

RE_INBOUND: dict[str, MatrixCell] = {
    "banking": MatrixCell(
        coupling=0.65,
        channel="Credit freeze halts project finance + construction lending",
        lag_hours=12,
        amplifier_key="developer_leverage_ratio",
    ),
    "government": MatrixCell(
        coupling=0.55,
        channel="Infrastructure spending freeze + permit moratorium",
        lag_hours=24,
        amplifier_key="infrastructure_pipeline_usd",
    ),
    "oil_gas": MatrixCell(
        coupling=0.30,
        channel="Construction material cost escalation from energy price spike",
        lag_hours=48,
        amplifier_key="real_estate_gdp_share",
    ),
    "insurance": MatrixCell(
        coupling=0.20,
        channel="Construction insurance repricing makes projects unviable",
        lag_hours=72,
        amplifier_key="developer_leverage_ratio",
    ),
    "fintech": MatrixCell(
        coupling=0.10,
        channel="Digital mortgage pipeline disruption",
        lag_hours=24,
        amplifier_key="real_estate_gdp_share",
    ),
}


def get_amplified_coupling(
    cell: MatrixCell,
    country_code: str,
    normalize_infra: float = 200.0e9,
) -> float:
    """Return the country-amplified coupling weight.

    For most keys, amplifier is a 0–1 ratio used directly.
    For infrastructure_pipeline_usd, normalize to a 0–1 scale.
    """
    profile = COUNTRY_PROFILES.get(country_code)
    if not profile:
        return cell.coupling

    raw = profile.get(cell.amplifier_key, 0.5)
    if cell.amplifier_key == "infrastructure_pipeline_usd":
        raw = min(raw / normalize_infra, 1.0)

    return min(cell.coupling * (1.0 + raw * 0.5), 1.0)
