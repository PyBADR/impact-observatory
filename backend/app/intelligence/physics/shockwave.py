"""
Shockwave propagation modeling.

Physics metaphor: A shock event (disruption, conflict, natural disaster)
propagates outward at a certain speed. Intensity decays with distance and
time using a wavefront model. Points further from the origin and reached
later experience reduced shock intensity.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Tuple
import numpy as np


@dataclass
class ShockEvent:
    """
    A shock event with spatiotemporal propagation.
    
    Attributes:
        origin_lat: Shock origin latitude
        origin_lon: Shock origin longitude
        magnitude: Initial shock intensity [0, 1]
        propagation_speed_kmh: Speed at which shockwave expands
        start_time: When the shock event begins
    """
    origin_lat: float
    origin_lon: float
    magnitude: float
    propagation_speed_kmh: float
    start_time: datetime

    def __post_init__(self):
        """Validate parameters."""
        if not (0 <= self.magnitude <= 1):
            raise ValueError(f"magnitude must be in [0, 1], got {self.magnitude}")
        if self.propagation_speed_kmh <= 0:
            raise ValueError(f"propagation_speed_kmh must be positive, got {self.propagation_speed_kmh}")


class ShockwaveEngine:
    """
    Collection of shocks modeling spatiotemporal disruption propagation.
    
    Computational model: A shockwave expands as a circular wavefront from the
    origin. Intensity follows:
        intensity = magnitude * exp(-lambda * distance) * H(distance - speed * dt)
    where:
        - lambda: decay rate (inverse of characteristic length scale)
        - H(x): Heaviside step function (0 if x < 0, else 1) - ensures causality
        - distance: Euclidean distance from origin
        - dt: time elapsed since start
    """

    def __init__(self, decay_lambda: float = 0.05):
        """
        Initialize shockwave engine.
        
        Args:
            decay_lambda: Spatial decay rate [default: 0.05 = 20 km characteristic length]
        """
        self.shocks: List[ShockEvent] = []
        self.decay_lambda = decay_lambda

    def add_shock(self, shock: ShockEvent) -> None:
        """
        Register a shock event.
        
        Args:
            shock: ShockEvent instance
        """
        self.shocks.append(shock)

    def evaluate_at(self, lat: float, lon: float, time: datetime) -> float:
        """
        Evaluate shock intensity at a point and time.
        
        Sums contributions from all registered shocks. Each shock contributes
        only after its wavefront reaches the point (Heaviside step function).
        
        Args:
            lat: Query latitude
            lon: Query longitude
            time: Query time
            
        Returns:
            Total shock intensity [0, inf), typically 0-1
        """
        if not self.shocks:
            return 0.0

        total_intensity = 0.0

        for shock in self.shocks:
            # Time elapsed since shock started
            time_delta = time - shock.start_time
            
            if time_delta.total_seconds() < 0:
                # Shock hasn't started yet
                continue

            dt_hours = time_delta.total_seconds() / 3600.0

            # Distance from shock origin (in km)
            dx_km = (lat - shock.origin_lat) * 111.0
            dy_km = (lon - shock.origin_lon) * 111.0 * np.cos(np.radians(lat))
            distance_km = np.sqrt(dx_km * dx_km + dy_km * dy_km)

            # Wavefront distance at current time
            wavefront_distance_km = shock.propagation_speed_kmh * dt_hours

            # Heaviside step: shock intensity is zero until wavefront arrives
            if distance_km > wavefront_distance_km:
                continue

            # Intensity: magnitude * exp(-lambda * distance)
            intensity = shock.magnitude * np.exp(-self.decay_lambda * distance_km)
            total_intensity += intensity

        return float(total_intensity)

    def propagate(
        self, targets: List[Tuple[float, float, str]], time: datetime
    ) -> Dict[str, float]:
        """
        Evaluate shock impact on multiple targets.
        
        Args:
            targets: List of (lat, lon, target_id) tuples
            time: Evaluation time
            
        Returns:
            Dictionary mapping target_id -> shock intensity at that target
        """
        impacts = {}
        for lat, lon, target_id in targets:
            impacts[target_id] = self.evaluate_at(lat, lon, time)

        return impacts
