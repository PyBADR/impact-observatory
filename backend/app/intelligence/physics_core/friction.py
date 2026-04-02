"""Friction model for route delay and cost."""


def compute_friction(base_cost: float, congestion: float, risk_factor: float, distance_km: float) -> dict:
    friction = (1 + congestion) * (1 + risk_factor) * (distance_km / 1000)
    adjusted_cost = base_cost * friction
    delay_hours = distance_km * congestion * 0.01
    return {"friction_coefficient": friction, "adjusted_cost": adjusted_cost, "delay_hours": delay_hours, "risk_premium": base_cost * risk_factor}
