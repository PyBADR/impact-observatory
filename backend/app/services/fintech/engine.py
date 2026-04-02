"""
Impact Observatory | مرصد الأثر — Fintech Stress Engine (v4 §3.8)
Per-entity fintech stress with operational metrics and breach flags.
"""

from datetime import datetime, timezone
from typing import List

from ...domain.models.scenario import Scenario
from ...domain.models.entity import Entity
from ...domain.models.financial_impact import FinancialImpact
from ...domain.models.fintech_stress import FintechStress, FintechBreachFlags
from ...core.constants import (
    SERVICE_AVAILABILITY_MIN,
    SETTLEMENT_DELAY_MAX_MIN,
    OPERATIONAL_RISK_MAX,
)


def compute_fintech_stress(
    scenario: Scenario,
    fintech_entities: List[Entity],
    financial_impacts: List[FinancialImpact],
) -> List[FintechStress]:
    """
    v4 §3.8 — Compute per-entity fintech stress.

    Args:
        scenario: v4 Scenario with fraud_loss_rate
        fintech_entities: Entities with entity_type='fintech'
        financial_impacts: Per-entity financial impacts

    Returns:
        List of v4 FintechStress with breach_flags
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    results: List[FintechStress] = []

    for entity in fintech_entities:
        if entity.entity_type != "fintech":
            continue

        shock = scenario.shock_intensity

        # Transaction failure rate
        txn_failure_rate = min(0.25, 0.02 + 0.13 * shock)

        # Fraud loss
        fraud_loss = entity.exposure * scenario.fraud_loss_rate * shock

        # Service availability (degrades under stress)
        service_availability = max(0.50, entity.availability * (1 - 0.30 * shock))

        # Settlement delay (minutes)
        settlement_delay_min = 240 + int(4320 * shock)  # 4h baseline + up to 72h

        # Client churn rate
        client_churn_rate = min(0.15, 0.01 + 0.14 * shock)

        # Operational risk score (0-1)
        op_risk = min(1.0, 0.1 + 0.8 * shock)

        # Breach flags (v4 §3.8)
        breach_flags = FintechBreachFlags(
            availability_breach=service_availability < SERVICE_AVAILABILITY_MIN,
            settlement_breach=settlement_delay_min > SETTLEMENT_DELAY_MAX_MIN,
            operational_risk_breach=op_risk > OPERATIONAL_RISK_MAX,
        )

        results.append(FintechStress(
            entity_id=entity.entity_id,
            timestamp=now,
            transaction_failure_rate=round(txn_failure_rate, 4),
            fraud_loss=round(fraud_loss, 4),
            service_availability=round(service_availability, 4),
            settlement_delay_minutes=settlement_delay_min,
            client_churn_rate=round(client_churn_rate, 4),
            operational_risk_score=round(op_risk, 4),
            breach_flags=breach_flags,
        ))

    return results


def aggregate_fintech_metrics(stresses: List[FintechStress]) -> dict:
    """Aggregate fintech metrics across all entities."""
    if not stresses:
        return {
            "aggregate_txn_failure_rate": 0.02,
            "aggregate_settlement_delay_min": 240,
            "aggregate_service_availability": 0.995,
            "fraud_loss": 0,
            "breach_flags": FintechBreachFlags(
                availability_breach=False, settlement_breach=False,
                operational_risk_breach=False,
            ),
        }
    n = len(stresses)
    return {
        "aggregate_txn_failure_rate": round(sum(s.transaction_failure_rate for s in stresses) / n, 4),
        "aggregate_settlement_delay_min": round(sum(s.settlement_delay_minutes for s in stresses) / n),
        "aggregate_service_availability": round(sum(s.service_availability for s in stresses) / n, 4),
        "fraud_loss": round(sum(s.fraud_loss for s in stresses), 4),
        "breach_flags": FintechBreachFlags(
            availability_breach=any(s.breach_flags.availability_breach for s in stresses),
            settlement_breach=any(s.breach_flags.settlement_breach for s in stresses),
            operational_risk_breach=any(s.breach_flags.operational_risk_breach for s in stresses),
        ),
    }
