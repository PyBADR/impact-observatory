"""Banking Stress Engine — Computes liquidity gap, capital adequacy, interbank rates

Stress testing module for GCC banking system resilience. Quantifies liquidity pressure,
capital erosion, and systemic funding stress under disruptive scenarios.
Implements Basel III-aligned capital adequacy framework.
"""

from app.intelligence.engines.gcc_constants import BASES
from app.schemas.observatory import (
    ScenarioInput,
    FinancialImpact,
    BankingStress,
)


def compute_banking_stress(
    scenario: ScenarioInput,
    financial_impact: FinancialImpact
) -> BankingStress:
    """
    Compute banking sector stress indicators.
    
    Models:
    - Liquidity gap: Daily funding shortfall under stress withdrawal scenario
    - Capital adequacy ratio (CAR): Regulatory capital buffer erosion
    - Interbank rate spike: Unsecured funding cost premium (basis points)
    - Time to liquidity breach: Days until deposit/payment default risk
    - FX reserve drawdown: Central bank intervention capacity (% of reserves)
    
    Args:
        scenario: Event scenario with severity and duration
        financial_impact: Upstream financial impact module output
        
    Returns:
        BankingStress with stress indicators and overall stress_level assessment
        
    Model:
        liquidity_gap = banking_assets * 0.03 * severity * (duration / 14)
        capital_adequacy_ratio = max(0.08, 0.18 - (0.10 * severity))
        interbank_rate_spike = 50 + (250 * severity) basis points
        time_to_liquidity_breach = max(1, 30 / (severity * 2))
        fx_reserve_drawdown = min(25, reserves * 0.05 * severity / reserves * 100)
    """
    
    # Liquidity gap: 3% of banking assets under baseline stress
    # Scales with severity and duration
    liquidity_gap_usd = (
        BASES["bankingAssets"] * 
        0.03 * 
        scenario.severity * 
        (scenario.duration_days / 14.0)
    )
    
    # Capital adequacy ratio (CAR)
    # Baseline: 18% (well above Basel III 8% minimum)
    # Deteriorates by 10 percentage points per unit severity
    # Floor: 8% (regulatory minimum)
    capital_adequacy_ratio = max(
        0.08,
        0.18 - (0.10 * scenario.severity)
    )
    
    # Interbank rate spike (basis points above baseline LIBOR/SOFR)
    # Baseline: 50 bps
    # Maximum: 300 bps at full severity
    interbank_rate_spike = 0.5 + (2.5 * scenario.severity)  # percentage points
    
    # Time to liquidity breach (days until deposit covenant breach)
    # Inversely proportional to severity squared (exponential pressure)
    time_to_liquidity_breach_days = max(1, int(30 / (scenario.severity * 2)))
    
    # FX reserve drawdown (% of total central bank reserves)
    # Baseline: 0%, Maximum: 25% under extreme stress
    fx_reserve_drawdown_pct = min(
        25,
        BASES["cbReserves"] * 0.05 * scenario.severity / BASES["cbReserves"] * 100
    )
    
    # Stress level classification based on capital adequacy and liquidity metrics
    if capital_adequacy_ratio < 0.10:
        # Below 10% CAR = systemic capital deficiency
        stress_level = "CRITICAL"
    elif capital_adequacy_ratio < 0.12:
        # 10-12% CAR = severe stress, near-default risk
        stress_level = "HIGH"
    elif capital_adequacy_ratio < 0.15:
        stress_level = "MEDIUM"
    else:
        stress_level = "LOW"

    # Composite stress score (0-100) for dashboard gauges
    # Weighted blend: 50% CAR erosion + 30% liquidity pressure + 20% interbank stress
    car_score = min(100.0, max(0.0, (0.18 - capital_adequacy_ratio) / 0.10 * 100.0))
    liquidity_score = min(100.0, max(0.0, liquidity_gap_usd / (BASES["bankingAssets"] * 0.03) * 100.0))
    interbank_score = min(100.0, max(0.0, interbank_rate_spike / 3.0 * 100.0))
    stress_score = round(0.50 * car_score + 0.30 * liquidity_score + 0.20 * interbank_score, 1)

    return BankingStress(
        liquidity_gap_usd=liquidity_gap_usd,
        capital_adequacy_ratio=capital_adequacy_ratio,
        interbank_rate_spike=interbank_rate_spike,
        time_to_liquidity_breach_days=time_to_liquidity_breach_days,
        fx_reserve_drawdown_pct=fx_reserve_drawdown_pct,
        stress_level=stress_level,
        stress_score=stress_score,
    )
