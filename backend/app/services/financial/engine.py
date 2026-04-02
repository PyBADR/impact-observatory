"""Financial Impact Engine — Computes headline loss, peak day, time to failure

Core computation module for quantifying the financial impact of disruptive scenarios
in GCC member states. Implements deterministic pricing models based on sector exposure,
severity multipliers, and temporal dynamics.
"""

from app.intelligence.engines.gcc_constants import (
    BASES,
    HORMUZ_MULTIPLIERS,
)
from app.schemas.observatory import (
    ScenarioInput,
    FinancialImpact,
)


def compute_financial_impact(scenario: ScenarioInput) -> FinancialImpact:
    """
    Compute headline loss, peak impact day, and time to critical failure.
    
    For Hormuz-class disruptions, applies multiplicative loss based on:
    - Base GDP exposure (BASES["gccGDP"])
    - GDP multiplier shock (HORMUZ_MULTIPLIERS["gdpMultiplier"])
    - Scenario severity (0-1 scale)
    - Duration scaling (14-day baseline)
    
    Args:
        scenario: ScenarioInput with severity and duration_days
        
    Returns:
        FinancialImpact with headline_loss_usd, peak_day, time_to_failure_days,
        severity_code, and confidence
        
    Model:
        headline_loss = base_gdp * (1 - gdp_multiplier) * severity * (duration / 14)
        peak_day = min(duration, max(3, duration * 0.5))
        time_to_failure = max(1, 14 / severity)
    """
    # Base GDP loss (unmitigated shock)
    gdp_loss_coefficient = 1 - HORMUZ_MULTIPLIERS["gdpMultiplier"]  # 0.35
    
    # Headline loss: GDP exposure × shock × severity × duration scaling
    headline_loss_usd = (
        BASES["gccGDP"] * 
        gdp_loss_coefficient * 
        scenario.severity * 
        (scenario.duration_days / 14.0)
    )
    
    # Peak impact occurs at 50% of duration, minimum day 3
    peak_day = min(
        scenario.duration_days,
        max(3, int(scenario.duration_days * 0.5))
    )
    
    # Time to critical failure (days): inversely proportional to severity
    time_to_failure_days = max(1, int(14 / scenario.severity))
    
    # Severity classification based on headline loss (in billions USD)
    if headline_loss_usd < 50:       # < $50B
        severity_code = "LOW"
    elif headline_loss_usd < 200:    # < $200B
        severity_code = "MEDIUM"
    elif headline_loss_usd < 500:    # < $500B
        severity_code = "HIGH"
    else:                            # >= $500B
        severity_code = "CRITICAL"
    
    # Confidence: base 85% for deterministic model, adjusted by severity range
    # (high severity scenarios have wider confidence intervals)
    confidence = 0.85 * (1 - 0.15 * min(scenario.severity, 1.0))
    
    return FinancialImpact(
        headline_loss_usd=headline_loss_usd,
        peak_day=peak_day,
        time_to_failure_days=time_to_failure_days,
        severity_code=severity_code,
        confidence=confidence,
    )
