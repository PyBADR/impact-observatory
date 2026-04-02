"""Threat field: events radiate risk outward with distance attenuation.

Each event creates a scalar field around its origin:
    T(p) = Σ severity_i * exp(-lambda * d(p, origin_i))

The field is additive: overlapping threat zones compound.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from src.engines.math.decay import haversine_km, spatial_decay


@dataclass
class ThreatSource:
    lat: float
    lng: float
    severity: float  # [0, 1]
    decay_rate: float = 0.005  # per km


@dataclass
class ThreatField:
    """Aggregate threat field from multiple event sources."""

    sources: list[ThreatSource] = field(default_factory=list)

    def add_source(self, lat: float, lng: float, severity: float, decay_rate: float = 0.005) -> None:
        self.sources.append(ThreatSource(lat=lat, lng=lng, severity=severity, decay_rate=decay_rate))

    def evaluate(self, lat: float, lng: float) -> float:
        """Compute aggregate threat intensity at a point."""
        if not self.sources:
            return 0.0
        total = 0.0
        for src in self.sources:
            d = haversine_km(src.lat, src.lng, lat, lng)
            total += src.severity * float(spatial_decay(d, lam=src.decay_rate))
        return float(np.clip(total, 0.0, 1.0))

    def evaluate_grid(
        self, lat_range: tuple[float, float], lng_range: tuple[float, float], resolution: int = 50
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Evaluate threat field over a lat/lng grid.

        Returns:
            (lats, lngs, intensities) where intensities is (resolution, resolution).
        """
        lats = np.linspace(lat_range[0], lat_range[1], resolution)
        lngs = np.linspace(lng_range[0], lng_range[1], resolution)
        grid = np.zeros((resolution, resolution), dtype=np.float64)

        for i, lat in enumerate(lats):
            for j, lng in enumerate(lngs):
                grid[i, j] = self.evaluate(lat, lng)

        return lats, lngs, grid


def compute_threat_at_point(
    lat: float,
    lng: float,
    events: list[dict],
) -> tuple[float, list[dict]]:
    """Convenience: compute threat at a point from event dicts.

    Each event dict needs: lat, lng, severity_score.

    Returns:
        (threat_value, contributing_events_sorted_by_contribution)
    """
    contributions = []
    total = 0.0
    for ev in events:
        d = haversine_km(ev["lat"], ev["lng"], lat, lng)
        influence = ev.get("severity_score", 0.5) * float(spatial_decay(d))
        total += influence
        contributions.append({"event": ev, "distance_km": d, "influence": influence})

    contributions.sort(key=lambda x: x["influence"], reverse=True)
    return float(np.clip(total, 0.0, 1.0)), contributions
