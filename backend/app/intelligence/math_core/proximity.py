"""
Proximity scoring for GCC risk assessment.

Implements GCC proximity bands:
P_i(t) = 1.00 if d <= 100 km
       = 0.80 if 100 < d <= 250
       = 0.55 if 250 < d <= 500
       = 0.30 if 500 < d <= 900
       = 0.10 if d > 900
"""

import numpy as np


def haversine_distance(
    lat1: float,
    lon1: float,
    lat2: float,
    lon2: float,
) -> float:
    """
    Calculate great-circle distance between two points in kilometers.

    Args:
        lat1: Latitude of point 1 (degrees)
        lon1: Longitude of point 1 (degrees)
        lat2: Latitude of point 2 (degrees)
        lon2: Longitude of point 2 (degrees)

    Returns:
        Distance in kilometers
    """
    R = 6371.0  # Earth radius in kilometers

    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)

    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    )
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    distance = R * c

    return float(distance)


def compute_proximity_score(
    entity_lat: float,
    entity_lon: float,
    event_lat: float,
    event_lon: float,
) -> float:
    """
    Compute proximity score P_i(t) based on GCC band structure.

    GCC proximity bands:
    P_i(t) = 1.00 if d <= 100 km
           = 0.80 if 100 < d <= 250
           = 0.55 if 250 < d <= 500
           = 0.30 if 500 < d <= 900
           = 0.10 if d > 900

    Args:
        entity_lat: Entity latitude (degrees)
        entity_lon: Entity longitude (degrees)
        event_lat: Event latitude (degrees)
        event_lon: Event longitude (degrees)

    Returns:
        Proximity score in {0.10, 0.30, 0.55, 0.80, 1.00}
    """
    distance_km = haversine_distance(entity_lat, entity_lon, event_lat, event_lon)

    if distance_km <= 100:
        return 1.00
    elif distance_km <= 250:
        return 0.80
    elif distance_km <= 500:
        return 0.55
    elif distance_km <= 900:
        return 0.30
    else:
        return 0.10


def compute_proximity_continuous(
    entity_lat: float,
    entity_lon: float,
    event_lat: float,
    event_lon: float,
    smoothing: bool = False,
) -> float:
    """
    Compute proximity score with optional smooth interpolation between bands.

    If smoothing=False, returns discrete band values.
    If smoothing=True, linearly interpolates within each band.

    Args:
        entity_lat: Entity latitude (degrees)
        entity_lon: Entity longitude (degrees)
        event_lat: Event latitude (degrees)
        event_lon: Event longitude (degrees)
        smoothing: If True, interpolate between band values

    Returns:
        Proximity score in [0.10, 1.00]
    """
    distance_km = haversine_distance(entity_lat, entity_lon, event_lat, event_lon)

    if not smoothing:
        return compute_proximity_score(entity_lat, entity_lon, event_lat, event_lon)

    # Smooth interpolation within bands
    if distance_km <= 100:
        # Band [0, 100] -> score [1.00, 1.00]
        return 1.00
    elif distance_km <= 250:
        # Band (100, 250] -> score [0.80, 1.00]
        t = (distance_km - 100) / 150
        return 1.00 - 0.20 * t
    elif distance_km <= 500:
        # Band (250, 500] -> score [0.55, 0.80]
        t = (distance_km - 250) / 250
        return 0.80 - 0.25 * t
    elif distance_km <= 900:
        # Band (500, 900] -> score [0.30, 0.55]
        t = (distance_km - 500) / 400
        return 0.55 - 0.25 * t
    else:
        # Band (900, inf) -> score [0.10, 0.30]
        return 0.10


# Canonical alias for Master Prompt compliance
compute_proximity = compute_proximity_score
