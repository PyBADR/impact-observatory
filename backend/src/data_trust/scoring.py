"""
Impact Observatory | مرصد الأثر
Scoring Logic Layer — pure function that computes trust-weighted scenario scores.

This module provides a deterministic scoring function that combines:
  - Base static scenario values (from SCENARIO_CATALOG)
  - Optional signal inputs (future: live data feeds)
  - Source confidence weights
  - Freshness penalty
  - Sector multiplier (SECTOR_ALPHA)
  - Country exposure multiplier

The function is pure — no side effects, no I/O, no state mutation.
It is NOT connected to the UI or API pipeline unless explicitly gated
behind a feature flag.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from src.config import SECTOR_ALPHA, SECTOR_THETA
from src.data_trust.source_registry import (
    FreshnessStatus,
    get_source,
    get_connected_live_sources,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Result model
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class TrustScore:
    """Result of the trust-weighted scoring computation."""
    scenario_id: str
    raw_base_loss_usd: float
    adjusted_loss_usd: float
    source_confidence: float           # 0.0–1.0
    freshness_penalty: float           # 0.0–1.0  (0 = no penalty)
    sector_multiplier: float           # weighted avg SECTOR_ALPHA for affected sectors
    country_exposure_multiplier: float # 1.0 = neutral
    is_static_fallback: bool
    signal_inputs_used: list[str]      # IDs of any live signals applied (empty today)
    computation_trace: list[str]       # Step-by-step trace for explainability

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "raw_base_loss_usd": self.raw_base_loss_usd,
            "adjusted_loss_usd": self.adjusted_loss_usd,
            "source_confidence": round(self.source_confidence, 4),
            "freshness_penalty": round(self.freshness_penalty, 4),
            "sector_multiplier": round(self.sector_multiplier, 4),
            "country_exposure_multiplier": round(self.country_exposure_multiplier, 4),
            "is_static_fallback": self.is_static_fallback,
            "signal_inputs_used": self.signal_inputs_used,
            "computation_trace": self.computation_trace,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Country exposure multipliers — static expert estimates
# How exposed each GCC country is to systemic financial shocks
# ═══════════════════════════════════════════════════════════════════════════════

_COUNTRY_EXPOSURE: dict[str, float] = {
    "UAE":     1.15,   # High trade/finance exposure
    "SAUDI":   1.10,   # High oil revenue dependency
    "QATAR":   1.08,   # LNG export concentration
    "BAHRAIN": 1.20,   # Small economy, high leverage
    "KUWAIT":  1.05,   # Sovereign wealth buffer
    "OMAN":    1.12,   # Moderate diversification
}

# Map scenario IDs to primary country (mirrors authority_realism_engine)
_SCENARIO_COUNTRY: dict[str, str] = {
    "hormuz_chokepoint_disruption": "UAE",
    "hormuz_full_closure": "UAE",
    "uae_banking_crisis": "UAE",
    "gcc_cyber_attack": "UAE",
    "saudi_oil_shock": "SAUDI",
    "qatar_lng_disruption": "QATAR",
    "bahrain_sovereign_stress": "BAHRAIN",
    "kuwait_fiscal_shock": "KUWAIT",
    "oman_port_closure": "OMAN",
    "red_sea_trade_corridor_instability": "SAUDI",
    "energy_market_volatility_shock": "SAUDI",
    "regional_liquidity_stress_event": "UAE",
    "critical_port_throughput_disruption": "UAE",
    "financial_infrastructure_cyber_disruption": "UAE",
    "iran_regional_escalation": "UAE",
    "gcc_power_grid_failure": "UAE",
    "difc_financial_contagion": "UAE",
    "gcc_insurance_reserve_shortfall": "UAE",
    "gcc_fintech_payment_outage": "UAE",
    "saudi_vision_mega_project_halt": "SAUDI",
    "gcc_sovereign_debt_crisis": "UAE",
}


# ═══════════════════════════════════════════════════════════════════════════════
# Freshness penalty
# ═══════════════════════════════════════════════════════════════════════════════

def _compute_freshness_penalty(source_id: str) -> float:
    """Compute a 0–1 penalty based on source freshness.

    - FRESH  → 0.0 (no penalty)
    - STALE  → 0.15
    - UNKNOWN → 0.25
    - Source not found → 0.30
    """
    source = get_source(source_id)
    if source is None:
        return 0.30
    if source.freshness_status == FreshnessStatus.FRESH:
        return 0.0
    if source.freshness_status == FreshnessStatus.STALE:
        return 0.15
    return 0.25  # UNKNOWN


def _compute_sector_multiplier(sectors_affected: list[str]) -> float:
    """Weighted average of SECTOR_ALPHA for affected sectors.

    Returns 1.0 if no sectors specified.
    """
    if not sectors_affected:
        return 1.0
    alphas = [SECTOR_ALPHA.get(s, 0.05) for s in sectors_affected]
    return sum(alphas) / len(alphas)


# ═══════════════════════════════════════════════════════════════════════════════
# Core scoring function — pure, no side effects
# ═══════════════════════════════════════════════════════════════════════════════

def compute_trust_score(
    scenario_id: str,
    base_loss_usd: float,
    sectors_affected: list[str],
    *,
    signal_inputs: Optional[dict[str, float]] = None,
    source_id: str = "src_scenario_catalog",
) -> TrustScore:
    """Compute a trust-weighted scenario score.

    Parameters
    ----------
    scenario_id : str
        The scenario identifier.
    base_loss_usd : float
        Static base loss from SCENARIO_CATALOG.
    sectors_affected : list[str]
        List of sectors affected by the scenario.
    signal_inputs : dict[str, float] | None
        Optional live signal overrides. Keys are signal names,
        values are multipliers (1.0 = no change). Not used today.
    source_id : str
        The data source ID to check freshness against.

    Returns
    -------
    TrustScore
        Trust-weighted score with full computation trace.
    """
    trace: list[str] = []

    # Step 1: Source confidence
    source = get_source(source_id)
    source_confidence = source.confidence_weight if source else 0.50
    trace.append(f"source_confidence={source_confidence} (from {source_id})")

    # Step 2: Freshness penalty
    freshness_penalty = _compute_freshness_penalty(source_id)
    trace.append(f"freshness_penalty={freshness_penalty}")

    # Step 3: Sector multiplier
    sector_mult = _compute_sector_multiplier(sectors_affected)
    trace.append(f"sector_multiplier={sector_mult:.4f} (avg SECTOR_ALPHA for {sectors_affected})")

    # Step 4: Country exposure
    country = _SCENARIO_COUNTRY.get(scenario_id, "UAE")
    country_mult = _COUNTRY_EXPOSURE.get(country, 1.0)
    trace.append(f"country_exposure={country_mult} (country={country})")

    # Step 5: Signal inputs (future — currently unused)
    signal_factor = 1.0
    signals_used: list[str] = []
    if signal_inputs:
        for sig_name, sig_value in signal_inputs.items():
            signal_factor *= sig_value
            signals_used.append(sig_name)
        trace.append(f"signal_factor={signal_factor} (signals: {signals_used})")
    else:
        trace.append("signal_factor=1.0 (no live signals connected)")

    # Step 6: Check if any live sources are connected
    live_sources = get_connected_live_sources()
    is_static = len(live_sources) == 0
    trace.append(f"is_static_fallback={is_static} (live_sources={len(live_sources)})")

    # Step 7: Compute adjusted loss
    # adjusted = base * confidence * (1 - freshness_penalty) * country_mult * signal_factor
    confidence_factor = source_confidence * (1.0 - freshness_penalty)
    adjusted = base_loss_usd * confidence_factor * country_mult * signal_factor
    trace.append(
        f"adjusted_loss = {base_loss_usd} * {confidence_factor:.4f} "
        f"* {country_mult} * {signal_factor} = {adjusted:.0f}"
    )

    return TrustScore(
        scenario_id=scenario_id,
        raw_base_loss_usd=base_loss_usd,
        adjusted_loss_usd=round(adjusted, 2),
        source_confidence=source_confidence,
        freshness_penalty=freshness_penalty,
        sector_multiplier=sector_mult,
        country_exposure_multiplier=country_mult,
        is_static_fallback=is_static,
        signal_inputs_used=signals_used,
        computation_trace=trace,
    )
