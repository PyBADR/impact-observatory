"""System stress tensor combining shockwave + pressure + diffusion."""
import numpy as np


def compute_system_stress(shockwave_energy: float, system_pressure: float, diffusion_rate: float, time_hours: float) -> dict:
    stress = shockwave_energy * system_pressure * (1 + diffusion_rate * time_hours)
    normalized = min(1.0, stress)
    level = "critical" if normalized > 0.8 else "high" if normalized > 0.6 else "medium" if normalized > 0.3 else "low"
    return {"stress": normalized, "level": level, "components": {"shockwave": shockwave_energy, "pressure": system_pressure, "diffusion": diffusion_rate}, "time_hours": time_hours}
