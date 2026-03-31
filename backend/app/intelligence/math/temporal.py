"""
Temporal decay and freshness modeling for time-sensitive risk assessment.

Implements temporal decay functions and time-weighted aggregation for
managing how information quality changes with age.
"""

from datetime import datetime, timezone
from typing import List, Optional
import numpy as np


def temporal_decay(
    delta_seconds: float,
    gamma: float = 1e-5,
) -> float:
    """
    Calculate temporal decay factor based on elapsed time.

    Uses exponential decay model:
    T(Δt) = exp(-γ * Δt)

    Where:
        - Δt: time elapsed in seconds
        - γ: decay rate parameter (default 1e-5)

    The default γ = 1e-5 gives ~37% influence after ~100,000 seconds (~1.2 days),
    and ~13% after ~200,000 seconds (~2.3 days).

    Args:
        delta_seconds: Elapsed time in seconds (non-negative)
        gamma: Decay rate parameter (default 1e-5, must be positive)

    Returns:
        Temporal decay factor in (0, 1]

    Raises:
        ValueError: If delta_seconds is negative or gamma is non-positive
    """
    if delta_seconds < 0:
        raise ValueError(f"Time delta must be non-negative, got {delta_seconds}")
    if gamma <= 0:
        raise ValueError(f"Gamma parameter must be positive, got {gamma}")

    decay = float(np.exp(-gamma * delta_seconds))
    return np.clip(decay, 0.0, 1.0)


def freshness_score(
    event_time: datetime,
    reference_time: Optional[datetime] = None,
    gamma: float = 1e-5,
) -> float:
    """
    Calculate freshness score of information based on its age.

    Computes temporal decay from event time to reference time (default now):
    F(t) = exp(-γ * (t_ref - t_event))

    Timestamps are converted to UTC for consistent comparison.

    Args:
        event_time: Timestamp of the event/information
        reference_time: Reference time for comparison (default: current UTC time)
        gamma: Temporal decay rate (default 1e-5)

    Returns:
        Freshness score in [0, 1]

    Raises:
        ValueError: If event_time is in the future or gamma is invalid
    """
    if reference_time is None:
        reference_time = datetime.now(timezone.utc)

    # Ensure both times are timezone-aware for proper comparison
    if event_time.tzinfo is None:
        event_time = event_time.replace(tzinfo=timezone.utc)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    # Calculate elapsed seconds
    delta = reference_time - event_time
    delta_seconds = delta.total_seconds()

    if delta_seconds < 0:
        raise ValueError(
            f"Event time ({event_time}) cannot be in the future "
            f"relative to reference time ({reference_time})"
        )

    return temporal_decay(delta_seconds, gamma)


def time_weighted_aggregate(
    scores: List[float],
    timestamps: List[datetime],
    gamma: float = 1e-5,
) -> float:
    """
    Compute weighted aggregate of scores using temporal decay weights.

    Aggregates multiple scores with weights based on their freshness:

    A = Σ(S_i * F_i) / Σ(F_i)

    Where:
        - S_i: score i
        - F_i: freshness decay factor for timestamp i = exp(-γ * age_i)

    Recent scores are weighted more heavily. Uses current UTC time as reference.

    Args:
        scores: List of scalar values to aggregate (should be in [0, 1])
        timestamps: List of datetime objects corresponding to each score
        gamma: Temporal decay rate (default 1e-5)

    Returns:
        Weighted aggregate score in [0, 1]

    Raises:
        ValueError: If scores and timestamps have different lengths,
                   or if any timestamp is in the future
    """
    if len(scores) != len(timestamps):
        raise ValueError(
            f"Scores ({len(scores)}) and timestamps ({len(timestamps)}) "
            f"must have equal length"
        )

    if len(scores) == 0:
        raise ValueError("Cannot aggregate empty score list")

    if len(scores) == 1:
        return float(np.clip(scores[0], 0.0, 1.0))

    # Compute freshness weights for each timestamp
    reference_time = datetime.now(timezone.utc)
    weights = np.array([
        freshness_score(ts, reference_time, gamma)
        for ts in timestamps
    ])

    # Weighted average
    scores_array = np.array(scores)
    weighted_sum = np.sum(scores_array * weights)
    weight_sum = np.sum(weights)

    if weight_sum < 1e-10:  # Avoid division by near-zero
        # All weights decayed to near-zero, return average of scores
        return float(np.mean(scores_array))

    aggregate = weighted_sum / weight_sum
    return float(np.clip(aggregate, 0.0, 1.0))
