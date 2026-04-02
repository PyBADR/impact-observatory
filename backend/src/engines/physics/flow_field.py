"""Flow field: models movement patterns of flights and vessels as vector fields.

Each entity in motion contributes a velocity vector at its position.
Aggregated, this produces a flow density map — useful for identifying
congestion zones and dominant movement corridors.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class FlowVector:
    lat: float
    lng: float
    vx: float  # east-west component (positive = east)
    vy: float  # north-south component (positive = north)
    magnitude: float = 0.0

    def __post_init__(self) -> None:
        self.magnitude = float(np.sqrt(self.vx ** 2 + self.vy ** 2))


@dataclass
class FlowField:
    """Aggregate flow field from entity movements."""

    vectors: list[FlowVector] = field(default_factory=list)

    def add_vector(self, lat: float, lng: float, heading_deg: float, speed: float) -> None:
        """Add a flow vector from heading (degrees from north) and speed."""
        heading_rad = np.radians(heading_deg)
        vx = speed * np.sin(heading_rad)
        vy = speed * np.cos(heading_rad)
        self.vectors.append(FlowVector(lat=lat, lng=lng, vx=float(vx), vy=float(vy)))

    def density_at(self, lat: float, lng: float, radius_km: float = 50.0) -> float:
        """Flow density at a point: count of vectors within radius, weighted by magnitude."""
        from src.engines.math.decay import haversine_km

        total = 0.0
        for v in self.vectors:
            d = haversine_km(v.lat, v.lng, lat, lng)
            if d <= radius_km:
                weight = 1.0 - (d / radius_km)
                total += v.magnitude * weight
        return total

    def dominant_direction_at(
        self, lat: float, lng: float, radius_km: float = 50.0
    ) -> tuple[float, float]:
        """Average flow direction at a point. Returns (avg_vx, avg_vy)."""
        from src.engines.math.decay import haversine_km

        sum_vx, sum_vy, count = 0.0, 0.0, 0
        for v in self.vectors:
            d = haversine_km(v.lat, v.lng, lat, lng)
            if d <= radius_km:
                weight = 1.0 - (d / radius_km)
                sum_vx += v.vx * weight
                sum_vy += v.vy * weight
                count += 1
        if count == 0:
            return 0.0, 0.0
        return sum_vx / count, sum_vy / count

    def congestion_zones(self, threshold: float = 10.0) -> list[dict]:
        """Identify zones where flow density exceeds threshold.

        Simple grid-based scan over bounding box of all vectors.
        """
        if not self.vectors:
            return []

        lats = [v.lat for v in self.vectors]
        lngs = [v.lng for v in self.vectors]
        lat_range = (min(lats) - 0.5, max(lats) + 0.5)
        lng_range = (min(lngs) - 0.5, max(lngs) + 0.5)

        zones = []
        for lat in np.linspace(lat_range[0], lat_range[1], 20):
            for lng in np.linspace(lng_range[0], lng_range[1], 20):
                density = self.density_at(float(lat), float(lng))
                if density >= threshold:
                    zones.append({"lat": float(lat), "lng": float(lng), "density": density})

        return sorted(zones, key=lambda z: z["density"], reverse=True)
