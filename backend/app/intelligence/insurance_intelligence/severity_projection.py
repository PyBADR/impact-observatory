"""Severity Projection: S = f(exposure, intensity, concentration)
Projects severity evolution over time using exponential decay model.
"""
import numpy as np


def compute_severity_projection(
    exposure: float,
    intensity: float,
    concentration: float,
    time_horizon_days: int = 90,
) -> dict:
    """
    Project severity evolution with time-decay model.

    Args:
        exposure: Exposure value (0.0 to 1.0)
        intensity: Intensity multiplier (0.5 to 3.0)
        concentration: Concentration factor (0.0 to 1.0)
        time_horizon_days: Projection period

    Returns:
        Dictionary with:
        - current_severity: Base severity at t=0
        - projected_severity: Severity at time_horizon_days
        - time_horizon_days: Input horizon
        - projections: List of severity at key time points
        - peak_severity: Maximum severity
        - recovery_rate: Decay rate constant
    """
    # Base severity: product of factors, capped at 1.0
    base_severity = min(1.0, exposure * intensity * (1 + concentration))

    # Exponential decay model: e^(-0.02 * t)
    recovery_rate = 0.02
    time_decay = np.exp(-recovery_rate * time_horizon_days)
    projected = base_severity * time_decay

    # Generate projections at key milestones
    projections = []
    milestone_days = [1, 7, 14, 30, 60, 90]

    for day in milestone_days:
        if day <= time_horizon_days:
            decay = np.exp(-recovery_rate * day)
            severity_at_day = base_severity * decay
            projections.append({"day": day, "severity": float(severity_at_day)})

    return {
        "current_severity": float(base_severity),
        "projected_severity": float(projected),
        "time_horizon_days": time_horizon_days,
        "projections": projections,
        "peak_severity": float(base_severity),
        "recovery_rate": recovery_rate,
    }
