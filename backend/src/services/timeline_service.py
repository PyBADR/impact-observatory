"""Service: Timeline Engine — deterministic multi-step temporal simulation."""

from __future__ import annotations
import math
from datetime import datetime, timezone, timedelta

def compute_timeline(run_result: dict) -> dict:
    """Compute timestep-by-timestep temporal simulation from run data."""
    run_id = run_result["run_id"]
    severity = run_result["scenario"]["severity"]
    horizon_hours = run_result["scenario"]["horizon_hours"]
    headline_loss = run_result.get("headline_loss_usd", 0)
    financial_impacts = run_result.get("financial_impacts", [])
    banking = run_result.get("banking_stress", {})
    insurance = run_result.get("insurance_stress", {})
    fintech = run_result.get("fintech_stress", {})

    # Time config
    granularity = 60  # minutes
    num_steps = min(24, horizon_hours)
    shock_decay = 0.03
    propagation_delay = 1
    recovery_rate = 0.01

    time_config = {
        "time_granularity_minutes": granularity,
        "time_horizon_steps": num_steps,
        "shock_decay_rate": shock_decay,
        "propagation_delay_steps": propagation_delay,
        "recovery_rate": recovery_rate,
        "max_temporal_iterations_per_step": 10,
    }

    start_time = datetime.now(timezone.utc)
    base_flow = headline_loss * 2  # Approximate system flow capacity
    banking_stress_val = banking.get("aggregate_stress", 0) if isinstance(banking, dict) else 0
    insurance_stress_val = insurance.get("aggregate_stress", 0) if isinstance(insurance, dict) else 0
    fintech_stress_val = fintech.get("aggregate_stress", 0) if isinstance(fintech, dict) else 0

    timesteps = []
    cumulative_loss = 0.0

    for step in range(num_steps):
        effective_shock = severity * ((1 - shock_decay) ** step)
        recovery = recovery_rate * step
        net_shock = max(0, effective_shock - recovery)

        step_loss = headline_loss * net_shock * (1.0 / num_steps)
        propagated = step_loss * 0.4 * min(1.0, step / max(1, num_steps * 0.3)) if step >= propagation_delay else 0
        cumulative_loss += step_loss + propagated

        flow = base_flow * (1.0 - net_shock * 0.5)
        breach_count = 0
        if banking_stress_val > 0.6 and step >= 2:
            breach_count += 1
        if insurance_stress_val > 0.5 and step >= 3:
            breach_count += 1
        if fintech_stress_val > 0.4 and step >= 1:
            breach_count += 1

        avg_stress = (banking_stress_val + insurance_stress_val + fintech_stress_val) / 3
        if avg_stress > 0.7 and step > num_steps * 0.5:
            sys_status = "critical"
        elif avg_stress > 0.5:
            sys_status = "degrading"
        elif cumulative_loss <= 0:
            sys_status = "stable"
        else:
            sys_status = "degrading" if net_shock > 0.3 else "stable"

        ts = (start_time + timedelta(minutes=granularity * step)).isoformat()
        timesteps.append({
            "run_id": run_id,
            "timestep_index": step,
            "timestamp": ts,
            "shock_intensity_effective": round(effective_shock, 4),
            "aggregate_loss": round(cumulative_loss, 2),
            "aggregate_flow": round(max(0, flow), 2),
            "regulatory_breach_count": breach_count,
            "system_status": sys_status,
        })

    return {
        "run_id": run_id,
        "status": "completed",
        "time_config": time_config,
        "timesteps": timesteps,
    }
