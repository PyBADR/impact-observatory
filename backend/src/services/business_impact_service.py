"""Service: Business Impact Layer — computes executive impact summary, loss trajectory, time-to-failure, and regulatory breach events."""

from __future__ import annotations
import math
from datetime import datetime, timezone, timedelta

from src.policies.executive_policy import classify_executive_status_v2
from src.policies.scenario_policy import resolve_scenario_type

def compute_business_impact(run_result: dict) -> dict:
    """Compute full business impact from a completed run."""
    run_id = run_result["run_id"]
    severity = run_result["scenario"]["severity"]
    horizon_hours = run_result["scenario"]["horizon_hours"]
    financial_impacts = run_result.get("financial_impacts", [])
    banking = run_result.get("banking_stress", {})
    insurance = run_result.get("insurance_stress", {})
    fintech = run_result.get("fintech_stress", {})

    # Compute headline metrics
    headline_loss = run_result.get("headline_loss_usd", 0)
    total_system_exposure = sum(f.get("loss_usd", 0) for f in financial_impacts) if financial_impacts else headline_loss

    # Loss trajectory (simulate 24 timesteps over the horizon)
    time_granularity_minutes = 60
    num_steps = min(24, horizon_hours)
    shock_decay_rate = 0.03
    start_time = datetime.now(timezone.utc)

    loss_trajectory = []
    cumulative = 0.0
    prev_cumulative = 0.0
    prev_velocity = 0.0
    peak_loss = 0.0
    peak_step = 0

    for step in range(num_steps):
        t = step
        effective_shock = severity * ((1 - shock_decay_rate) ** t)
        direct = headline_loss * effective_shock * (1.0 / num_steps)
        propagated = direct * 0.4 * min(1.0, t / max(1, num_steps * 0.3))
        cumulative += direct + propagated
        velocity = cumulative - prev_cumulative
        acceleration = velocity - prev_velocity

        if cumulative > peak_loss:
            peak_loss = cumulative
            peak_step = step

        status = "stable"
        if velocity > 0 and acceleration > 0:
            status = "critical" if cumulative > headline_loss * 0.7 else "deteriorating"
        elif velocity <= 0:
            status = "stable"

        ts = (start_time + timedelta(minutes=time_granularity_minutes * step)).isoformat()
        loss_trajectory.append({
            "run_id": run_id,
            "scope_level": "system",
            "scope_ref": "system",
            "timestep_index": step,
            "timestamp": ts,
            "direct_loss": round(direct, 2),
            "propagated_loss": round(propagated, 2),
            "cumulative_loss": round(cumulative, 2),
            "revenue_at_risk": round(cumulative * 0.15, 2),
            "loss_velocity": round(velocity, 2),
            "loss_acceleration": round(acceleration, 2),
            "status": status,
        })
        prev_velocity = velocity
        prev_cumulative = cumulative

    # Time to failure calculations
    time_to_failures = []

    # Banking liquidity failure
    banking_stress_val = banking.get("aggregate_stress", 0) if isinstance(banking, dict) else 0
    if banking_stress_val > 0.5:
        ttf_hours = max(1.0, (1.0 - banking_stress_val) * horizon_hours)
        time_to_failures.append({
            "run_id": run_id,
            "scope_level": "sector",
            "scope_ref": "bank",
            "failure_type": "liquidity_failure",
            "failure_threshold_value": 1.0,
            "current_value_at_t0": banking.get("liquidity_coverage_ratio", banking.get("liquidity_stress", 0.8)),
            "predicted_failure_timestep": int(ttf_hours / (time_granularity_minutes / 60)),
            "predicted_failure_timestamp": (start_time + timedelta(hours=ttf_hours)).isoformat(),
            "time_to_failure_hours": round(ttf_hours, 1),
            "confidence_score": 0.85,
            "failure_reached_within_horizon": ttf_hours < horizon_hours,
        })

    # Insurance solvency failure
    insurance_stress_val = insurance.get("aggregate_stress", 0) if isinstance(insurance, dict) else 0
    if insurance_stress_val > 0.4:
        ttf_hours = max(2.0, (1.0 - insurance_stress_val) * horizon_hours * 1.5)
        time_to_failures.append({
            "run_id": run_id,
            "scope_level": "sector",
            "scope_ref": "insurer",
            "failure_type": "solvency_failure",
            "failure_threshold_value": 1.0,
            "current_value_at_t0": insurance.get("solvency_ratio", 0.9),
            "predicted_failure_timestep": int(ttf_hours / (time_granularity_minutes / 60)),
            "predicted_failure_timestamp": (start_time + timedelta(hours=ttf_hours)).isoformat(),
            "time_to_failure_hours": round(ttf_hours, 1),
            "confidence_score": 0.78,
            "failure_reached_within_horizon": ttf_hours < horizon_hours,
        })

    # Fintech availability failure
    fintech_stress_val = fintech.get("aggregate_stress", 0) if isinstance(fintech, dict) else 0
    if fintech_stress_val > 0.3:
        ttf_hours = max(0.5, (1.0 - fintech_stress_val) * horizon_hours * 0.5)
        time_to_failures.append({
            "run_id": run_id,
            "scope_level": "sector",
            "scope_ref": "fintech",
            "failure_type": "availability_failure",
            "failure_threshold_value": 0.995,
            "current_value_at_t0": fintech.get("api_availability_pct", 99.0) / 100.0,
            "predicted_failure_timestep": int(ttf_hours / (time_granularity_minutes / 60)),
            "predicted_failure_timestamp": (start_time + timedelta(hours=ttf_hours)).isoformat(),
            "time_to_failure_hours": round(ttf_hours, 1),
            "confidence_score": 0.72,
            "failure_reached_within_horizon": ttf_hours < horizon_hours,
        })

    # Regulatory breach events
    breach_events = []
    breach_count_critical = 0
    breach_count_reportable = 0

    if banking_stress_val > 0.6:
        breach_events.append({
            "run_id": run_id, "timestep_index": 2,
            "timestamp": (start_time + timedelta(hours=2)).isoformat(),
            "scope_level": "sector", "scope_ref": "bank",
            "metric_name": "lcr", "metric_value": round(1.0 - banking_stress_val, 3),
            "threshold_value": 1.0, "breach_direction": "below_minimum",
            "breach_level": "critical" if banking_stress_val > 0.8 else "major",
            "first_breach": True, "reportable": True,
        })
        if banking_stress_val > 0.8:
            breach_count_critical += 1
        breach_count_reportable += 1

    if insurance_stress_val > 0.5:
        breach_events.append({
            "run_id": run_id, "timestep_index": 3,
            "timestamp": (start_time + timedelta(hours=3)).isoformat(),
            "scope_level": "sector", "scope_ref": "insurer",
            "metric_name": "solvency_ratio", "metric_value": round(1.0 - insurance_stress_val * 0.3, 3),
            "threshold_value": 1.0, "breach_direction": "below_minimum",
            "breach_level": "major", "first_breach": True, "reportable": True,
        })
        breach_count_reportable += 1

    # First failure timing
    first_failure_hours = None
    first_failure_type = None
    first_failure_ref = None
    for ttf in time_to_failures:
        if ttf["failure_reached_within_horizon"]:
            h = ttf["time_to_failure_hours"]
            if first_failure_hours is None or h < first_failure_hours:
                first_failure_hours = h
                first_failure_type = ttf["failure_type"]
                first_failure_ref = ttf["scope_ref"]

    # Business severity mapping (keep biz_severity for backward compat)
    loss_pct = peak_loss / max(1, headline_loss * num_steps) if headline_loss > 0 else 0
    if first_failure_hours and first_failure_hours < horizon_hours * 0.25:
        biz_severity = "severe"
    elif first_failure_hours and first_failure_hours < horizon_hours * 0.75:
        biz_severity = "high"
    elif first_failure_hours:
        biz_severity = "medium"
    elif breach_count_critical > 0:
        biz_severity = "severe"
    else:
        biz_severity = "low"

    # Dynamic executive classification (replaces static if/elif chain)
    _base_loss = run_result.get("scenario", {}).get("base_loss_usd", max(headline_loss, 1.0))
    _prop_speed = min(1.0, (
        banking.get("aggregate_stress", 0.0)
        + insurance.get("severity_index", 0.0)
        + fintech.get("aggregate_stress", 0.0)
    ) / 3.0 * 1.5)
    _scenario_id = run_result.get("scenario", {}).get("scenario_id", "")
    exec_status = classify_executive_status_v2(
        severity=severity,
        time_to_first_breach_hours=first_failure_hours,
        loss_ratio=peak_loss / max(_base_loss, 1.0),
        propagation_speed=_prop_speed,
        scenario_type=resolve_scenario_type(_scenario_id),
    )

    peak_ts = (start_time + timedelta(minutes=time_granularity_minutes * peak_step)).isoformat()

    summary = {
        "run_id": run_id,
        "currency": "USD",
        "peak_cumulative_loss": round(peak_loss, 2),
        "peak_loss_timestep": peak_step,
        "peak_loss_timestamp": peak_ts,
        "system_time_to_first_failure_hours": first_failure_hours,
        "first_failure_type": first_failure_type,
        "first_failure_scope_ref": first_failure_ref,
        "critical_breach_count": breach_count_critical,
        "reportable_breach_count": breach_count_reportable,
        "business_severity": biz_severity,
        "executive_status": exec_status,
    }

    return {
        "summary": summary,
        "loss_trajectory": loss_trajectory,
        "time_to_failures": time_to_failures,
        "regulatory_breach_events": breach_events,
    }
