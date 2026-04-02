"""Shockwave propagation: A(r,t) = A0 * e^(-alpha*r) * cos(omega*t - k*r)"""
import numpy as np
from ..engines.gcc_constants import PHYSICS


def compute_shockwave(amplitude_0: float, distance_km: float, time_hours: float, alpha: float = None, omega: float = 0.5, k: float = 0.1) -> dict:
    if alpha is None:
        alpha = PHYSICS["alpha"]
    r = distance_km / 100
    t = time_hours
    amplitude = amplitude_0 * np.exp(-alpha * r) * np.cos(omega * t - k * r)
    energy = amplitude_0**2 * np.exp(-2 * alpha * r)
    return {"amplitude": float(amplitude), "energy": float(energy), "decay_factor": float(np.exp(-alpha * r)), "phase": float(omega * t - k * r), "distance_km": distance_km, "time_hours": time_hours}


def compute_shockwave_field(origin: dict, targets: list[dict], amplitude_0: float, time_hours: float) -> list[dict]:
    results = []
    for target in targets:
        dist = haversine(origin["lat"], origin["lng"], target["lat"], target["lng"])
        wave = compute_shockwave(amplitude_0, dist, time_hours)
        results.append({"target_id": target.get("id", ""), "distance_km": dist, **wave})
    return results


def haversine(lat1, lng1, lat2, lng2):
    R = 6371
    dlat = np.radians(lat2 - lat1)
    dlng = np.radians(lng2 - lng1)
    a = np.sin(dlat / 2)**2 + np.cos(np.radians(lat1)) * np.cos(np.radians(lat2)) * np.sin(dlng / 2)**2
    return R * 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
