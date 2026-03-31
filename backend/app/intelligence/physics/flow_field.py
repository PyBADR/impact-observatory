"""
Mobility flow field modeling.

Physics metaphor: Flows represent movement vectors (like fluid or particle flow)
between origins and destinations. Flow density at a point models how many flows
pass nearby, analogous to current density. Congestion measures cumulative density
relative to corridor capacity.
"""

from dataclasses import dataclass
from typing import List, Tuple, Dict
import numpy as np


@dataclass
class FlowVector:
    """
    A directed flow between two points.
    
    Attributes:
        origin_lat: Starting latitude
        origin_lon: Starting longitude
        dest_lat: Destination latitude
        dest_lon: Destination longitude
        magnitude: Flow intensity/volume [0, 1]
        flow_type: Category of flow ('air', 'sea', 'land', etc.)
    """
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float
    magnitude: float
    flow_type: str

    def __post_init__(self):
        """Validate magnitude."""
        if not (0 <= self.magnitude <= 1):
            raise ValueError(f"magnitude must be in [0, 1], got {self.magnitude}")


class FlowField:
    """
    Collection of flows modeling mobility corridors and congestion.
    
    Computational approach: Flow density at a point is estimated by summing
    contributions from flows nearby. A flow contributes density proportional to
    its magnitude, weighted by proximity (using Gaussian kernel).
    """

    def __init__(self):
        """Initialize empty flow field."""
        self.flows: List[FlowVector] = []

    def add_flow(self, flow: FlowVector) -> None:
        """
        Add a flow vector to the field.
        
        Args:
            flow: FlowVector describing origin, destination, and magnitude
        """
        self.flows.append(flow)

    def compute_density(self, lat: float, lon: float, radius_km: float = 100.0) -> float:
        """
        Estimate flow density at a point within a given radius.
        
        Physics model: Each flow contributes density inversely proportional to
        distance from the point. Uses an exponential kernel:
            contribution = magnitude * exp(-distance_km / radius_km)
        
        This models how a flow affects congestion in its vicinity.
        
        Args:
            lat: Query latitude
            lon: Query longitude
            radius_km: Characteristic range of flow influence (typical: 50-200 km)
            
        Returns:
            Normalized density estimate [0, inf), typically 0-1 in practice
        """
        if not self.flows:
            return 0.0

        density = 0.0
        for flow in self.flows:
            # Midpoint of flow path
            mid_lat = (flow.origin_lat + flow.dest_lat) / 2.0
            mid_lon = (flow.origin_lon + flow.dest_lon) / 2.0

            # Approximate distance using Euclidean metric, scaled to km
            # (1 degree ~ 111 km at equator; approximation)
            dx_km = (lat - mid_lat) * 111.0
            dy_km = (lon - mid_lon) * 111.0 * np.cos(np.radians(lat))
            distance_km = np.sqrt(dx_km * dx_km + dy_km * dy_km)

            # Exponential decay with distance
            contribution = flow.magnitude * np.exp(-distance_km / radius_km)
            density += contribution

        return float(density)

    def compute_congestion(
        self, corridor_id: str, flows: List[FlowVector],
        base_capacity: float = 1.0
    ) -> float:
        """
        Compute normalized congestion for a corridor.
        
        Physics model: Congestion = sum of flow magnitudes / capacity, clamped to [0, 1].
        Models how cumulative flow through a corridor approaches its capacity limit.
        
        Args:
            corridor_id: Identifier for the corridor (for logging/tracking)
            flows: List of FlowVector instances on this corridor
            base_capacity: Maximum flow capacity of corridor [default: 1.0]
            
        Returns:
            Congestion level [0, 1], where 1 means at/exceeds capacity
        """
        if not flows:
            return 0.0

        total_flow = sum(f.magnitude for f in flows)
        congestion = total_flow / base_capacity if base_capacity > 0 else 0.0

        # Clamp to [0, 1]
        return float(np.clip(congestion, 0.0, 1.0))

    def evaluate_grid(
        self, lat_range: Tuple[float, float], lon_range: Tuple[float, float],
        resolution: int = 50, radius_km: float = 100.0
    ) -> np.ndarray:
        """
        Evaluate flow density on a regular 2D grid.
        
        Args:
            lat_range: (min_lat, max_lat)
            lon_range: (min_lon, max_lon)
            resolution: Grid points per dimension
            radius_km: Flow influence radius for density computation
            
        Returns:
            2D numpy array of shape (resolution, resolution) with flow density.
        """
        lats = np.linspace(lat_range[0], lat_range[1], resolution)
        lons = np.linspace(lon_range[0], lon_range[1], resolution)

        lon_grid, lat_grid = np.meshgrid(lons, lats)
        density_grid = np.zeros_like(lon_grid)

        for i in range(resolution):
            for j in range(resolution):
                density_grid[i, j] = self.compute_density(
                    lat_grid[i, j], lon_grid[i, j], radius_km
                )

        return density_grid
