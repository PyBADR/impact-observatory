"""
Threat field modeling using Gaussian spatial decay.

Physics metaphor: A threat source emits a scalar field (like temperature or
potential) that decays with distance. The decay follows a Gaussian (RBF) kernel,
where intensity = magnitude * exp(-lambda * distance^2).

This models how disruptions, conflicts, or risks spread spatially with reduced
impact as distance increases.
"""

from dataclasses import dataclass
from typing import List, Tuple
import numpy as np


@dataclass
class ThreatSource:
    """
    A point source of threat/risk with spatial decay.
    
    Attributes:
        lat: Latitude of threat origin
        lon: Longitude of threat origin
        magnitude: Threat intensity [0-1], dimensionless
        decay_lambda: Decay rate (inverse of characteristic distance squared)
                      Higher lambda = shorter range. Typical: 0.05-0.2
        event_id: Unique identifier for this threat event
    """
    lat: float
    lon: float
    magnitude: float
    decay_lambda: float
    event_id: str

    def __post_init__(self):
        """Validate magnitude is in [0, 1]."""
        if not (0 <= self.magnitude <= 1):
            raise ValueError(f"magnitude must be in [0, 1], got {self.magnitude}")
        if self.decay_lambda <= 0:
            raise ValueError(f"decay_lambda must be positive, got {self.decay_lambda}")


@dataclass
class ContourPoint:
    """A point on a threat contour."""
    lat: float
    lon: float
    value: float


class ThreatField:
    """
    Spatial threat field modeled as superposition of Gaussian point sources.
    
    Computational approach: Each source contributes threat as:
        threat_contribution = magnitude * exp(-lambda * distance^2)
    
    Total threat at any point is the sum of all source contributions, providing
    a smooth, differentiable threat landscape.
    """

    def __init__(self):
        """Initialize empty threat field."""
        self.sources: List[ThreatSource] = []

    def add_source(self, source: ThreatSource) -> None:
        """
        Add a threat source to the field.
        
        Args:
            source: ThreatSource with location, magnitude, and decay parameters
        """
        self.sources.append(source)

    def evaluate(self, lat: float, lon: float) -> float:
        """
        Evaluate total threat magnitude at a single point.
        
        Uses Gaussian RBF kernel: combines all source contributions.
        Each source contributes: magnitude * exp(-lambda * distance^2)
        where distance is Euclidean in lat-lon space.
        
        Args:
            lat: Query latitude
            lon: Query longitude
            
        Returns:
            Threat magnitude [0, inf), typically bounded by sum of magnitudes
        """
        if not self.sources:
            return 0.0

        threat = 0.0
        for source in self.sources:
            # Euclidean distance in lat-lon space
            dx = lat - source.lat
            dy = lon - source.lon
            distance_sq = dx * dx + dy * dy

            # Gaussian decay: exp(-lambda * d^2)
            contribution = source.magnitude * np.exp(-source.decay_lambda * distance_sq)
            threat += contribution

        return float(threat)

    def evaluate_grid(
        self, lat_range: Tuple[float, float], lon_range: Tuple[float, float],
        resolution: int
    ) -> np.ndarray:
        """
        Evaluate threat field on a regular 2D grid.
        
        Physics interpretation: Create a 2D "threat potential map" suitable
        for visualization or downstream analysis.
        
        Args:
            lat_range: (min_lat, max_lat)
            lon_range: (min_lon, max_lon)
            resolution: Number of points per dimension (grid is resolution x resolution)
            
        Returns:
            2D numpy array of shape (resolution, resolution) with threat values.
            Rows index latitude (top=max, bottom=min), columns index longitude (left=min, right=max).
        """
        lats = np.linspace(lat_range[0], lat_range[1], resolution)
        lons = np.linspace(lon_range[0], lon_range[1], resolution)

        if not self.sources:
            return np.zeros((resolution, resolution))

        # Create grid points
        lon_grid, lat_grid = np.meshgrid(lons, lats)
        threat_grid = np.zeros_like(lon_grid)

        # Vectorized computation for efficiency
        source_lats = np.array([s.lat for s in self.sources])
        source_lons = np.array([s.lon for s in self.sources])
        magnitudes = np.array([s.magnitude for s in self.sources])
        lambdas = np.array([s.decay_lambda for s in self.sources])

        for i, source in enumerate(self.sources):
            dx = lat_grid - source.lat
            dy = lon_grid - source.lon
            distance_sq = dx * dx + dy * dy
            threat_grid += source.magnitude * np.exp(-source.decay_lambda * distance_sq)

        return threat_grid

    def get_contours(self, threshold: float) -> List[Tuple[float, float, float]]:
        """
        Find all points in the field above a threat threshold.
        
        Uses a grid-based sampling approach: evaluates threat on a moderate
        resolution grid and returns points exceeding threshold.
        
        Args:
            threshold: Minimum threat value to include
            
        Returns:
            List of (lat, lon, threat_value) tuples for points above threshold.
            Empty list if no sources or no points exceed threshold.
        """
        if not self.sources:
            return []

        # Use a sampling grid to find high-threat regions
        resolution = 100
        
        # Estimate bounding box from sources with margin
        lats = [s.lat for s in self.sources]
        lons = [s.lon for s in self.sources]
        margin = 5.0  # degrees
        
        lat_range = (min(lats) - margin, max(lats) + margin)
        lon_range = (min(lons) - margin, max(lons) + margin)

        grid = self.evaluate_grid(lat_range, lon_range, resolution)

        lats_grid = np.linspace(lat_range[0], lat_range[1], resolution)
        lons_grid = np.linspace(lon_range[0], lon_range[1], resolution)

        lon_mesh, lat_mesh = np.meshgrid(lons_grid, lats_grid)

        # Find points above threshold
        mask = grid >= threshold
        contour_lats = lat_mesh[mask]
        contour_lons = lon_mesh[mask]
        contour_values = grid[mask]

        return list(zip(contour_lats, contour_lons, contour_values))
