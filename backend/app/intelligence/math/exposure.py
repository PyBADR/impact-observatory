"""
Asset exposure model for computing vulnerability and impact assessment.

Implements exposure scoring for individual assets and portfolio-level
aggregation with concentration risk metrics.
"""

from dataclasses import dataclass, field
from typing import List, Dict
import numpy as np


@dataclass
class ExposureInput:
    """
    Input data for individual asset exposure calculation.

    Attributes:
        entity_id: Unique identifier for the asset/entity
        value_at_risk: Monetary value exposed to risk
        dependency_weight: Relative importance of dependencies (0-1)
        criticality: Operational criticality score (0-1)
    """
    entity_id: str
    value_at_risk: float
    dependency_weight: float
    criticality: float


@dataclass
class ExposureResult:
    """
    Aggregated exposure analysis results.

    Attributes:
        total_exposure: Sum of all individual exposures
        top_contributors: List of (entity_id, exposure_value) for top assets
        concentration_risk: Herfindahl-Hirschman Index (HHI) of concentration
        asset_count: Number of assets in portfolio
        mean_exposure: Average exposure per asset
    """
    total_exposure: float
    top_contributors: List[tuple] = field(default_factory=list)
    concentration_risk: float = 0.0
    asset_count: int = 0
    mean_exposure: float = 0.0


def compute_exposure(
    value_at_risk: float,
    dependency_weight: float,
    operational_criticality: float,
) -> float:
    """
    Compute exposure for a single asset.

    Uses multiplicative model combining value, dependency, and criticality:

    E = VAR * (w_dep * D + w_crit * C)

    Where:
        - VAR: value at risk (in monetary units or normalized)
        - D: dependency weight (0-1)
        - C: operational criticality (0-1)
        - w_dep, w_crit: normalized weights summing to 1

    With default equal weighting: w_dep = 0.5, w_crit = 0.5

    Args:
        value_at_risk: Asset value exposed to risk (non-negative)
        dependency_weight: Relative dependency importance (0-1)
        operational_criticality: Criticality score (0-1)

    Returns:
        Exposure value (non-negative)

    Raises:
        ValueError: If any input is invalid (negative value, out-of-range weights)
    """
    if value_at_risk < 0:
        raise ValueError(f"Value at risk must be non-negative, got {value_at_risk}")

    if not 0 <= dependency_weight <= 1:
        raise ValueError(
            f"Dependency weight must be in [0, 1], got {dependency_weight}"
        )

    if not 0 <= operational_criticality <= 1:
        raise ValueError(
            f"Operational criticality must be in [0, 1], got {operational_criticality}"
        )

    # Weighted combination of dependency and criticality factors
    # Equal weighting by default
    factor = 0.5 * dependency_weight + 0.5 * operational_criticality

    # Exposure = value * combined factor
    exposure = value_at_risk * factor

    return float(np.clip(exposure, 0.0, None))


def aggregate_exposure(
    exposures: List[ExposureInput],
) -> ExposureResult:
    """
    Aggregate individual asset exposures and compute portfolio metrics.

    Computes total exposure, identifies top contributors, and calculates
    concentration risk using the Herfindahl-Hirschman Index (HHI):

    HHI = Σ(E_i / E_total)²

    HHI ranges from 1/n (perfect diversification) to 1 (complete concentration).
    Higher HHI indicates greater concentration risk.

    Args:
        exposures: List of ExposureInput objects for all assets

    Returns:
        ExposureResult with aggregated metrics and top contributors

    Raises:
        ValueError: If exposures list is empty or contains invalid data
    """
    if not exposures:
        raise ValueError("Cannot aggregate empty exposure list")

    # Compute individual exposures
    exposure_values = []
    entity_ids = []

    for exposure_input in exposures:
        entity_exposure = compute_exposure(
            value_at_risk=exposure_input.value_at_risk,
            dependency_weight=exposure_input.dependency_weight,
            operational_criticality=exposure_input.criticality,
        )
        exposure_values.append(entity_exposure)
        entity_ids.append(exposure_input.entity_id)

    exposure_values = np.array(exposure_values, dtype=np.float64)
    total_exposure = float(np.sum(exposure_values))

    # Handle zero total exposure case
    if total_exposure < 1e-10:
        return ExposureResult(
            total_exposure=0.0,
            top_contributors=[],
            concentration_risk=0.0,
            asset_count=len(exposures),
            mean_exposure=0.0,
        )

    # Compute concentration risk (HHI)
    market_shares = exposure_values / total_exposure
    hhi = float(np.sum(market_shares ** 2))

    # Identify top contributors (top 5 or all if fewer than 5)
    top_n = min(5, len(exposures))
    top_indices = np.argsort(exposure_values)[-top_n:][::-1]
    top_contributors = [
        (entity_ids[i], float(exposure_values[i]))
        for i in top_indices
        if exposure_values[i] > 0
    ]

    # Compute mean exposure
    mean_exposure = float(np.mean(exposure_values))

    return ExposureResult(
        total_exposure=total_exposure,
        top_contributors=top_contributors,
        concentration_risk=hhi,
        asset_count=len(exposures),
        mean_exposure=mean_exposure,
    )
