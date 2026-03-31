"""
Spatial decay and proximity modeling for geographic risk analysis.

Implements haversine distance calculation, spatial decay functions, and
2D influence field generation for distributed threat assessment.
"""

import numpy as np
from typing import Tuple


def haversine_km(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate great-circle distance between two coordinates using Haversine formula.

    The Haversine formula calculates distance on a sphere:

    a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
    c = 2 * atan2(√a, √(1−a))
    d = R * c

    Where R = 6371 km (Earth's mean radius).

    Args:
        lat1: Latitude of first point in degrees
        lon1: Longitude of first point in degrees
        lat2: Latitude of second point in degrees
        lon2: Longitude of second point in degrees

    Returns:
        Distance in kilometers
    """
    R = 6371.0  # Earth radius in kilometers

    # Convert degrees to radians
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = R * c

    return float(distance)


def spatial_decay(
    distance_km: float,
    lambda_param: float = 0.01,
) -> float:
    """
    Calculate spatial decay factor based on distance.

    Uses exponential decay model:
    D(d) = exp(-λ * d)

    Where:
        - d: distance in kilometers
        - λ: decay rate parameter (higher = faster decay)

    The parameter λ = 0.01 gives ~37% influence at ~100km, ~13% at ~200km.

    Args:
        distance_km: Distance in kilometers (non-negative)
        lambda_param: Decay rate parameter (default 0.01)

    Returns:
        Decay factor in (0, 1]
    """
    if distance_km < 0:
        raise ValueError(f"Distance must be non-negative, got {distance_km}")
    if lambda_param <= 0:
        raise ValueError(f"Lambda parameter must be positive, got {lambda_param}")

    decay = float(np.exp(-lambda_param * distance_km))
    return np.clip(decay, 0.0, 1.0)


def proximity_score(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
    lambda_param: float = 0.01,
) -> float:
    """
    Calculate proximity score combining haversine distance and spatial decay.

    Combines geographic distance with exponential decay to produce a
    proximity metric suitable for risk assessment:

    P(lat1, lon1, lat2, lon2) = exp(-λ * d_haversine)

    Where d_haversine is the great-circle distance in kilometers.

    Args:
        lat1: Latitude of origin point in degrees
        lon1: Longitude of origin point in degrees
        lat2: Latitude of target point in degrees
        lon2: Longitude of target point in degrees
        lambda_param: Decay rate parameter (default 0.01)

    Returns:
        Proximity score in [0, 1]
    """
    distance = haversine_km(lat1, lon1, lat2, lon2)
    score = spatial_decay(distance, lambda_param)
    return score


def influence_field(
    origin_lat: float,
    origin_lon: float,
    grid_lats: np.ndarray,
    grid_lons: np.ndarray,
    magnitude: float = 1.0,
    lambda_param: float = 0.01,
) -> np.ndarray:
    """
    Generate 2D influence field from a geographic origin point.

    Computes spatial decay influence at each grid point based on distance
    from origin. Useful for modeling threat spread, contamination, or
    disruption impact across geographic regions.

    The influence at each grid point (i,j) is:
    I(i,j) = magnitude * exp(-λ * d_haversine(origin, grid_point[i,j]))

    Args:
        origin_lat: Origin latitude in degrees
        origin_lon: Origin longitude in degrees
        grid_lats: 1D array of grid latitudes (will be broadcast to 2D)
        grid_lons: 1D array of grid longitudes (will be broadcast to 2D)
        magnitude: Maximum influence amplitude (default 1.0)
        lambda_param: Spatial decay rate (default 0.01)

    Returns:
        2D numpy array with influence values at each grid point

    Raises:
        ValueError: If grid dimensions don't match or magnitude is invalid
    """
    if len(grid_lats) != len(grid_lons):
        raise ValueError(
            f"Grid latitude ({len(grid_lats)}) and longitude ({len(grid_lons)}) "
            f"dimensions must match"
        )
    if magnitude < 0:
        raise ValueError(f"Magnitude must be non-negative, got {magnitude}")

    # Create 2D mesh grid
    lat_grid, lon_grid = np.meshgrid(grid_lats, grid_lons, indexing='ij')

    # Vectorized haversine calculation
    lat1_rad = np.radians(origin_lat)
    lon1_rad = np.radians(origin_lon)
    lat2_rad = np.radians(lat_grid)
    lon2_rad = np.radians(lon_grid)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distances = 6371.0 * c  # Earth radius in km

    # Compute influence field with spatial decay
    influence = magnitude * np.exp(-lambda_param * distances)
    influence = np.clip(influence, 0.0, 1.0)

    return influence
