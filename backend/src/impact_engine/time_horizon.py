"""Time horizon computation — maps peak_day + recovery trajectory into TimeHorizon.

Uses recovery trajectory to interpolate 50% and 90% recovery milestones.
"""
from __future__ import annotations

from typing import Any

from src.config import (
    IE_ACUTE_THRESHOLD_DAYS,
    IE_SUSTAINED_THRESHOLD_DAYS,
    IE_RECOVERY_50_FACTOR,
    IE_RECOVERY_90_FACTOR,
)


def compute_time_horizon(
    peak_day: int,
    total_loss_usd: float,
    recovery_trajectory: list[dict[str, Any]],
    time_to_first_failure_hours: float,
    horizon_days: int,
) -> dict[str, Any]:
    """Compute time-based impact profile.

    Returns TimeHorizon-compatible dict.
    """
    # Find recovery milestones by scanning trajectory
    recovery_start_day = 0
    recovery_50_day = 0
    recovery_90_day = 0

    for point in recovery_trajectory:
        day = int(point.get("day", 0))
        frac = float(point.get("recovery_fraction", 0.0))

        if frac > 0.0 and recovery_start_day == 0:
            recovery_start_day = day

        if frac >= IE_RECOVERY_50_FACTOR and recovery_50_day == 0:
            recovery_50_day = day

        if frac >= IE_RECOVERY_90_FACTOR and recovery_90_day == 0:
            recovery_90_day = day

    # Estimate full recovery days
    if recovery_trajectory:
        last = recovery_trajectory[-1]
        last_frac = float(last.get("recovery_fraction", 0.0))
        last_day = int(last.get("day", horizon_days))
        if last_frac >= 0.95:
            full_recovery_days = last_day
        elif last_frac > 0.0:
            # Linear extrapolation
            full_recovery_days = min(
                int(last_day / max(last_frac, 0.01)),
                horizon_days * 3,
            )
        else:
            full_recovery_days = horizon_days * 2
    else:
        full_recovery_days = horizon_days

    # Classify horizon
    if full_recovery_days <= IE_ACUTE_THRESHOLD_DAYS:
        classification = "ACUTE"
    elif full_recovery_days <= IE_SUSTAINED_THRESHOLD_DAYS:
        classification = "SUSTAINED"
    else:
        classification = "CHRONIC"

    return {
        "peak_impact_day": peak_day,
        "peak_loss_usd": round(total_loss_usd, 2),
        "recovery_start_day": recovery_start_day,
        "recovery_50pct_day": recovery_50_day,
        "recovery_90pct_day": recovery_90_day,
        "full_recovery_days": full_recovery_days,
        "time_to_first_failure_hours": round(time_to_first_failure_hours, 1),
        "horizon_classification": classification,
    }
