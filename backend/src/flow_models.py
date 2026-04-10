"""
Impact Observatory | مرصد الأثر
Flow Models — simulate five flow types across the GCC network.

All USD volumes are calibrated to GCC daily flow estimates (2024):
  Money     : $42B/day  (GCC interbank + cross-border)
  Logistics : $18B/day  (cargo value equivalent)
  Energy    : $580M/day (oil + gas export revenue)
  Payments  : $8B/day   (digital + SWIFT GCC domestic)
  Claims    : $120M/day (insurance claims processing)
"""
from __future__ import annotations

import math
from typing import Literal

from src.utils import clamp, classify_stress

# ---------------------------------------------------------------------------
# Baseline daily volumes (USD)
# ---------------------------------------------------------------------------

BASE_VOLUMES_USD: dict[str, float] = {
    "money":      42_000_000_000,
    "logistics":  18_000_000_000,
    "energy":        580_000_000,
    "payments":    8_000_000_000,
    "claims":        120_000_000,
}

# Sector sensitivity: how much a unit of severity disrupts each flow
_SENSITIVITY: dict[str, float] = {
    "money":     0.70,
    "logistics": 0.75,
    "energy":    0.85,
    "payments":  0.60,
    "claims":    0.50,
}

# Rerouting cost premium as fraction of disrupted volume
_REROUTING_PREMIUM: dict[str, float] = {
    "money":     0.002,
    "logistics": 0.045,
    "energy":    0.035,
    "payments":  0.010,
    "claims":    0.015,
}

# Channel capacity (multiple of base volume — represents max throughput)
_CHANNEL_CAPACITY_MULT: dict[str, float] = {
    "money":     1.50,
    "logistics": 1.25,
    "energy":    1.10,
    "payments":  1.80,
    "claims":    1.30,
}

# Recovery lag in days per flow type at severity=1.0
_RECOVERY_DAYS_FULL: dict[str, int] = {
    "money":     14,
    "logistics": 21,
    "energy":    45,
    "payments":   7,
    "claims":    30,
}

FlowType = Literal["money", "logistics", "energy", "payments", "claims"]


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _simulate_flow(
    flow_type: str,
    severity: float,
    sector_stress: float,
) -> dict:
    """
    Core simulation for a single flow type.

    disruption_factor = severity * sensitivity * (1 + sector_stress * 0.25)
    disrupted_volume  = base_volume * (1 - disruption_factor)
    congestion        = (base - disrupted) / base
    backlog_usd       = disrupted_volume * disruption_factor * recovery_days
    rerouting_cost    = disrupted_volume * rerouting_premium
    delay_days        = recovery_days_full * disruption_factor
    saturation_pct    = disrupted_volume / channel_capacity * 100
    """
    severity = clamp(severity, 0.0, 1.0)
    sector_stress = clamp(sector_stress, 0.0, 1.0)

    base_vol = BASE_VOLUMES_USD[flow_type]
    sensitivity = _SENSITIVITY[flow_type]

    disruption_factor = clamp(
        severity * sensitivity * (1.0 + sector_stress * 0.25),
        0.0, 0.98,
    )

    disrupted_vol = base_vol * (1.0 - disruption_factor)
    congestion = max(0.0, base_vol - disrupted_vol) / base_vol

    recovery_days_full = _RECOVERY_DAYS_FULL[flow_type]
    delay_days = round(recovery_days_full * disruption_factor, 1)

    backlog_usd = disrupted_vol * disruption_factor * max(1, delay_days / 7)
    rerouting_cost_usd = disrupted_vol * _REROUTING_PREMIUM[flow_type] * (1 + disruption_factor)

    channel_cap = base_vol * _CHANNEL_CAPACITY_MULT[flow_type]
    # When disrupted, remaining flow is pushed through alternate channels → saturation
    saturation_pct = clamp((disrupted_vol / channel_cap) * 100 * (1 + disruption_factor * 0.40), 0, 200)

    stress_score = clamp(disruption_factor * (1.0 + severity * 0.2), 0.0, 1.0)
    classification = classify_stress(stress_score)

    return {
        "flow_type": flow_type,
        "base_volume_usd": base_vol,
        "disrupted_volume_usd": round(disrupted_vol, 2),
        "disruption_factor": round(disruption_factor, 4),
        "congestion": round(congestion, 4),
        "delay_days": delay_days,
        "backlog_usd": round(backlog_usd, 2),
        "rerouting_cost_usd": round(rerouting_cost_usd, 2),
        "saturation_pct": round(saturation_pct, 2),
        "stress_score": round(stress_score, 4),
        "classification": classification,
        "volume_loss_usd": round(base_vol - disrupted_vol, 2),
    }


# ---------------------------------------------------------------------------
# Public flow simulation functions
# ---------------------------------------------------------------------------

def simulate_money_flow(severity: float, banking_stress: float) -> dict:
    """
    Simulate interbank and cross-border money flows across GCC.
    """
    return _simulate_flow("money", severity, banking_stress)


def simulate_logistics_flow(severity: float, trade_exposure: float) -> dict:
    """
    Simulate cargo and freight logistics flows (ports, roads, air freight).
    """
    return _simulate_flow("logistics", severity, trade_exposure)


def simulate_energy_flow(severity: float, energy_exposure: float) -> dict:
    """
    Simulate oil, gas, and LNG export flows from GCC producers.
    """
    return _simulate_flow("energy", severity, energy_exposure)


def simulate_payment_flow(severity: float, fintech_stress: float) -> dict:
    """
    Simulate digital payments, SWIFT messages, and real-time settlement.
    """
    return _simulate_flow("payments", severity, fintech_stress)


def simulate_claims_flow(severity: float, insurance_stress: float) -> dict:
    """
    Simulate insurance claims intake, processing, and reinsurance cessions.
    """
    return _simulate_flow("claims", severity, insurance_stress)


# ---------------------------------------------------------------------------
# Aggregate flow simulation
# ---------------------------------------------------------------------------

def simulate_all_flows(
    severity: float,
    sector_exposure: dict[str, float],
    stress_inputs: dict,
) -> dict:
    """
    Simulate all five GCC flow types and return aggregate metrics.

    stress_inputs keys expected:
      banking_stress, fintech_stress, insurance_stress

    Returns:
      {money, logistics, energy, payments, claims,
       aggregate_disruption_usd, most_disrupted_flow, flow_recovery_days}
    """
    banking_stress = clamp(stress_inputs.get("banking_stress", severity * 0.7), 0, 1)
    fintech_stress = clamp(stress_inputs.get("fintech_stress", severity * 0.5), 0, 1)
    insurance_stress = clamp(stress_inputs.get("insurance_stress", severity * 0.6), 0, 1)
    trade_exposure = clamp(sector_exposure.get("logistics", 0.2) + sector_exposure.get("maritime", 0.15), 0, 1)
    energy_exposure = clamp(sector_exposure.get("energy", 0.25), 0, 1)

    money = simulate_money_flow(severity, banking_stress)
    logistics = simulate_logistics_flow(severity, trade_exposure)
    energy = simulate_energy_flow(severity, energy_exposure)
    payments = simulate_payment_flow(severity, fintech_stress)
    claims = simulate_claims_flow(severity, insurance_stress)

    flows_by_name = {
        "money": money,
        "logistics": logistics,
        "energy": energy,
        "payments": payments,
        "claims": claims,
    }

    aggregate_disruption = sum(f["volume_loss_usd"] for f in flows_by_name.values())
    most_disrupted = max(flows_by_name, key=lambda k: flows_by_name[k]["disruption_factor"])
    max_recovery_days = max(
        int(math.ceil(f["delay_days"])) for f in flows_by_name.values()
    )

    return {
        "money": money,
        "logistics": logistics,
        "energy": energy,
        "payments": payments,
        "claims": claims,
        "aggregate_disruption_usd": round(aggregate_disruption, 2),
        "most_disrupted_flow": most_disrupted,
        "flow_recovery_days": max_recovery_days,
    }
