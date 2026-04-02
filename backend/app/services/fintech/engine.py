"""Fintech Disruption Engine — Payment failures, settlement delays, gateway downtime

Digital financial services stress testing module. Quantifies operational resilience
and payment system disruption under infrastructure outages, cyber attacks, and
network congestion scenarios. Models T+0/T+1 settlement degradation.
"""

from app.schemas.observatory import (
    ScenarioInput,
    FinancialImpact,
    FintechStress,
)


def compute_fintech_stress(
    scenario: ScenarioInput,
    financial_impact: FinancialImpact
) -> FintechStress:
    """
    Compute fintech and digital banking stress indicators.
    
    Models:
    - Payment failure rate: Fraction of payment transactions failing
    - Settlement delay: Hours of deviation from T+0 baseline
    - Gateway downtime: Percentage of payment gateway unavailability
    - Digital banking disruption: Fraction of digital channel disruption
    - Time to payment failure: Days until critical payment system collapse
    
    Args:
        scenario: Event scenario with severity and duration
        financial_impact: Upstream financial impact module output
        
    Returns:
        FintechStress with payment and operational metrics and stress_level assessment
        
    Model:
        payment_failure_rate = min(0.15, 0.02 + (0.13 * severity))
        settlement_delay_hours = 4 + (72 * severity)
        gateway_downtime_pct = min(25, 2 + (23 * severity))
        digital_banking_disruption = min(0.8, 0.05 + (0.75 * severity))
        time_to_payment_failure = max(1, 21 / (severity * 1.5))
    """
    
    # Payment failure rate (fraction of transactions failing)
    # Baseline: 2% (normal system reliability)
    # At severity=1.0: 15% (maximum cap)
    payment_failure_rate = min(
        0.15,
        0.02 + (0.13 * scenario.severity)
    )
    
    # Settlement delay in hours above baseline T+0
    # Baseline: 4 hours (morning settlement window)
    # At severity=1.0: 76 hours (multi-day settlement)
    settlement_delay_hours = 4.0 + (72.0 * scenario.severity)
    
    # Gateway downtime percentage
    # Baseline: 2% (routine maintenance, failover)
    # At severity=1.0: 25% (major outage window)
    gateway_downtime_pct = min(
        25.0,
        2.0 + (23.0 * scenario.severity)
    )
    
    # Digital banking disruption fraction (0-1 scale)
    # Baseline: 5% (single channel degradation)
    # At severity=1.0: 80% (near-total digital channel disruption)
    digital_banking_disruption = min(
        0.8,
        0.05 + (0.75 * scenario.severity)
    )
    
    # Time to critical payment failure (days until systemic collapse)
    # Baseline: 14 days at minimal stress
    # Scales inversely with severity
    time_to_payment_failure_days = max(
        1,
        int(21 / (scenario.severity * 1.5))
    )
    
    # Stress level based on payment failure and gateway downtime thresholds
    if payment_failure_rate > 0.10 or gateway_downtime_pct > 15:
        # Critical: >10% payment failure or >15% gateway downtime
        stress_level = "CRITICAL"
    elif payment_failure_rate > 0.06 or gateway_downtime_pct > 10:
        # Severe: significant payment degradation
        stress_level = "HIGH"
    elif payment_failure_rate > 0.03 or gateway_downtime_pct > 5:
        stress_level = "MEDIUM"
    else:
        stress_level = "LOW"

    # Composite stress score (0-100) for dashboard gauges
    # Weighted blend: 40% payment failures + 35% gateway downtime + 25% digital disruption
    pfr_score = min(100.0, max(0.0, payment_failure_rate / 0.15 * 100.0))
    gateway_score = min(100.0, max(0.0, gateway_downtime_pct / 25.0 * 100.0))
    disruption_score = min(100.0, max(0.0, digital_banking_disruption / 0.8 * 100.0))
    stress_score = round(0.40 * pfr_score + 0.35 * gateway_score + 0.25 * disruption_score, 1)

    return FintechStress(
        payment_failure_rate=payment_failure_rate,
        settlement_delay_hours=settlement_delay_hours,
        gateway_downtime_pct=gateway_downtime_pct,
        digital_banking_disruption=digital_banking_disruption,
        time_to_payment_failure_days=time_to_payment_failure_days,
        stress_level=stress_level,
        stress_score=stress_score,
    )
