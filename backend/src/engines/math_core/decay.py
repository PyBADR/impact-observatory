"""Spatial and temporal decay functions.

Spatial:  Influence(d) = exp(-lambda * d)
Temporal: Freshness(t) = exp(-gamma * delta_t)
"""

import numpy as np

from src.engines.math_core.config import DECAY


def spatial_decay(
    distance_km: float | np.ndarray,
    lam: float = DECAY.spatial_lambda,
) -> float | np.ndarray:
    """Distance-based attenuation of influence.

    Args:
        distance_km: Distance in kilometers (scalar or array).
        lam: Decay rate per km.

    Returns:
        Influence factor in [0, 1]. 1 at origin, approaches 0 at distance.
    """
    return np.exp(-lam * np.asarray(distance_km, dtype=np.float64))


def temporal_decay(
    delta_hours: float | np.ndarray,
    gamma: float = DECAY.temporal_gamma,
) -> float | np.ndarray:
    """Time-based freshness attenuation.

    Args:
        delta_hours: Hours since event (scalar or array).
        gamma: Decay rate per hour.

    Returns:
        Freshness factor in [0, 1]. 1 at t=0, approaches 0 over time.
    """
    return np.exp(-gamma * np.asarray(delta_hours, dtype=np.float64))


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two points in km."""
    r = 6371.0
    dlat = np.radians(lat2 - lat1)
    dlng = np.radians(lng2 - lng1)
    a = np.sin(dlat / 2) ** 2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlng / 2) ** 2
    return float(r * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a)))
