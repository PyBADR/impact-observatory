"""Insurance Stress Engine — Computes claims surge, reinsurance trigger, solvency

Actuarial stress testing module for GCC insurance and takaful sector.
Quantifies underwriting losses, reinsurance activation, and insolvency risk
under catastrophic loss scenarios. Models combined ratio deterioration and
premium adequacy erosion.
"""

from app.intelligence.engines.gcc_constants import HORMUZ_MULTIPLIERS
from app.schemas.observatory import (
    ScenarioInput,
    FinancialImpact,
    InsuranceStress,
)


def compute_insurance_stress(
    scenario: ScenarioInput,
    financial_impact: FinancialImpact
) -> InsuranceStress:
    """
    Compute insurance sector stress indicators.
    
    Models:
    - Claims surge: Percentage increase in aggregate claim frequency/severity
    - Reinsurance trigger: Boolean flag if surge exceeds 30% threshold
    - Combined ratio: Loss + expense ratio (>1.0 = underwriting loss)
    - Solvency margin: Capital buffer as % above minimum requirement
    - Time to insolvency: Days until capital depletion (if unmitigated)
    - Premium adequacy: Premium income coverage ratio for claim liability
    
    Args:
        scenario: Event scenario with severity and duration
        financial_impact: Upstream financial impact module output
        
    Returns:
        InsuranceStress with claims and solvency metrics and stress_level assessment
        
    Model:
        claims_surge_pct = insSpike * 100 * severity - 100
        combined_ratio = 0.95 + (0.35 * severity)
        solvency_margin = max(5, 40 - (35 * severity))
        time_to_insolvency = max(1, 60 / (severity * 2))
        premium_adequacy = max(0.3, 1.0 - (0.7 * severity))
    """
    
    # Claims surge percentage above normal (baseline 0%)
    # Multiplier = 1.5 (50% baseline) at severity=1.0
    # Formula: (multiplier - 1) * 100 * severity
    claims_surge_pct = (
        (HORMUZ_MULTIPLIERS["insSpike"] - 1) * 100 * scenario.severity
    )
    
    # Reinsurance treaty activation trigger
    # Triggered if claims surge exceeds 30% threshold
    reinsurance_trigger = claims_surge_pct > 30
    
    # Combined ratio (loss + expense ratio)
    # Baseline: 95% (5% underwriting margin)
    # At severity=1.0: 95% + 35% = 130% (30% underwriting loss)
    combined_ratio = 0.95 + (0.35 * scenario.severity)
    
    # Solvency margin percentage above minimum requirement
    # Baseline: 40% surplus capital
    # At severity=1.0: 5% (near regulatory minimum)
    solvency_margin_pct = max(5, 40 - (35 * scenario.severity))
    
    # Time to insolvency (days until capital depletion)
    # Baseline: 60 days at minimal stress
    # Scales inversely with severity squared
    time_to_insolvency_days = max(1, int(60 / (scenario.severity * 2)))
    
    # Premium adequacy ratio (premium income relative to claim liability)
    # Baseline: 100% (premium covers expected claims)
    # At severity=1.0: 30% (70% coverage shortfall)
    premium_adequacy = max(0.3, 1.0 - (0.7 * scenario.severity))
    
    # Stress level based on combined ratio and solvency margin thresholds
    if solvency_margin_pct < 10 or combined_ratio > 1.50:
        stress_level = "CRITICAL"
    elif solvency_margin_pct < 20 or combined_ratio > 1.20:
        stress_level = "HIGH"
    elif solvency_margin_pct < 30 or combined_ratio > 1.05:
        stress_level = "MEDIUM"
    else:
        stress_level = "LOW"

    # Composite stress score (0-100) for dashboard gauges
    # Weighted blend: 40% solvency erosion + 35% combined ratio + 25% claims surge
    solvency_score = min(100.0, max(0.0, (40.0 - solvency_margin_pct) / 35.0 * 100.0))
    cr_score = min(100.0, max(0.0, (combined_ratio - 0.95) / 0.55 * 100.0))
    claims_score = min(100.0, max(0.0, claims_surge_pct / 50.0 * 100.0))
    stress_score = round(0.40 * solvency_score + 0.35 * cr_score + 0.25 * claims_score, 1)

    return InsuranceStress(
        claims_surge_pct=claims_surge_pct,
        reinsurance_trigger=reinsurance_trigger,
        combined_ratio=combined_ratio,
        solvency_margin_pct=solvency_margin_pct,
        time_to_insolvency_days=time_to_insolvency_days,
        premium_adequacy=premium_adequacy,
        stress_level=stress_level,
        stress_score=stress_score,
    )
