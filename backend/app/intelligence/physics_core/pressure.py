"""System pressure / systemic risk indicator."""
import numpy as np


def compute_system_pressure(impacts: dict[str, float], weights: dict[str, float] = None) -> dict:
    values = np.array(list(impacts.values()))
    abs_values = np.abs(values)
    pressure = float(np.mean(abs_values) * np.max(abs_values)) if len(values) > 0 else 0
    distribution = {"mean": float(np.mean(abs_values)), "max": float(np.max(abs_values)) if len(values) > 0 else 0, "std": float(np.std(abs_values))} if len(values) > 0 else {}
    return {"pressure": min(1.0, pressure), "node_count": len(impacts), "distribution": distribution}
