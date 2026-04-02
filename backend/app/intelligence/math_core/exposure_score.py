"""
Exposure scoring for GCC risk assessment using HHI (Herfindahl-Hirschman Index).

Implements HHI-based exposure analysis:
HHI = sum of (market_share_i)^2 for all entities
E_i(t) = concentration factor * (HHI / HHI_max)
"""

from dataclasses import dataclass
from typing import List, Dict
import numpy as np


@dataclass
class ExposureMetrics:
    """Container for exposure metrics."""

    concentration: float  # HHI concentration measure [0, 1]
    supplier_diversity: float  # Supplier/source diversity [0, 1]
    geographic_concentration: float  # Geographic concentration [0, 1]
    market_share: float  # Entity market share [0, 1]


def compute_herfindahl_index(
    market_shares: List[float],
) -> float:
    """
    Compute Herfindahl-Hirschman Index (HHI).

    HHI = sum of (share_i)^2 for all entities

    Args:
        market_shares: List of market shares for each entity [0, 1]

    Returns:
        HHI in [0, 1] where 1 = perfect monopoly, 0 = perfect competition
    """
    if not market_shares:
        return 0.0

    # Normalize shares to [0, 1] range
    total_share = sum(market_shares)
    if total_share <= 0:
        return 0.0

    normalized_shares = [s / total_share for s in market_shares]

    # Compute sum of squared shares
    hhi = sum(s ** 2 for s in normalized_shares)

    return float(np.clip(hhi, 0.0, 1.0))


def compute_herfindahl_normalized(
    market_shares: List[float],
) -> float:
    """
    Compute normalized HHI with unit range [0, 1].

    Normalized HHI = (HHI - HHI_min) / (HHI_max - HHI_min)

    Where HHI_min ≈ 1/n (perfect competition) and HHI_max = 1 (monopoly)

    Args:
        market_shares: List of market shares for each entity

    Returns:
        Normalized HHI in [0, 1]
    """
    if not market_shares or len(market_shares) <= 1:
        return 1.0

    hhi = compute_herfindahl_index(market_shares)
    n = len(market_shares)

    # HHI bounds
    hhi_min = 1.0 / n
    hhi_max = 1.0

    # Normalize to [0, 1]
    if hhi_max <= hhi_min:
        return 0.0

    normalized = (hhi - hhi_min) / (hhi_max - hhi_min)
    return float(np.clip(normalized, 0.0, 1.0))


def compute_exposure_score(
    metrics: ExposureMetrics,
    concentration_weight: float = 0.4,
) -> float:
    """
    Compute overall exposure score from HHI and diversification metrics.

    E_i(t) = concentration_weight * concentration
           + (1 - concentration_weight) * (1 - supplier_diversity)

    Args:
        metrics: ExposureMetrics object with concentration and diversity values
        concentration_weight: Weight for concentration factor (default 0.4)

    Returns:
        Exposure score in [0, 1] where 1 = high exposure, 0 = low exposure
    """
    concentration = np.clip(metrics.concentration, 0.0, 1.0)
    supplier_div = np.clip(metrics.supplier_diversity, 0.0, 1.0)

    # High exposure = high concentration + low diversity
    exposure = (
        concentration_weight * concentration
        + (1.0 - concentration_weight) * (1.0 - supplier_div)
    )

    return float(np.clip(exposure, 0.0, 1.0))


def compute_supplier_diversity(
    num_suppliers: int,
    baseline_suppliers: int = 5,
) -> float:
    """
    Compute supplier diversity metric.

    Diversity = min(num_suppliers / baseline_suppliers, 1.0)

    Args:
        num_suppliers: Number of unique suppliers/sources
        baseline_suppliers: Baseline for adequate diversification (default 5)

    Returns:
        Diversity score in [0, 1] where 1 = well diversified
    """
    if baseline_suppliers <= 0:
        return 0.0

    num_suppliers = max(0, num_suppliers)
    diversity = num_suppliers / baseline_suppliers

    return float(np.clip(diversity, 0.0, 1.0))


def compute_geographic_concentration(
    share_in_region: float,
    num_regions: int,
    baseline_regions: int = 10,
) -> float:
    """
    Compute geographic concentration.

    GeoConc = (share_in_region / max_share) * (1 - num_regions / baseline_regions)

    Args:
        share_in_region: Largest share concentrated in one region [0, 1]
        num_regions: Number of regions with presence
        baseline_regions: Baseline for good geographic diversification (default 10)

    Returns:
        Geographic concentration in [0, 1] where 1 = highly concentrated
    """
    share_in_region = np.clip(share_in_region, 0.0, 1.0)
    num_regions = max(1, num_regions)

    # Geographic spread factor: 1 - (distributed across regions)
    if baseline_regions <= 1:
        geographic_spread = 0.0
    else:
        geographic_spread = num_regions / baseline_regions
        geographic_spread = np.clip(geographic_spread, 0.0, 1.0)

    # Concentration = high share + low spread
    concentration = share_in_region * (1.0 - geographic_spread)

    return float(np.clip(concentration, 0.0, 1.0))


def compute_diversification_index(
    supplier_counts: Dict[str, int],
) -> float:
    """
    Compute diversification index using normalized entropy.

    Diversification = Shannon entropy / log(num_suppliers)

    Where Shannon entropy = -sum(p_i * log(p_i)) for share p_i

    Args:
        supplier_counts: Dictionary mapping supplier IDs to item counts

    Returns:
        Diversification in [0, 1] where 1 = perfectly diversified
    """
    if not supplier_counts or len(supplier_counts) <= 1:
        return 0.0

    total_items = sum(supplier_counts.values())
    if total_items <= 0:
        return 0.0

    # Compute probabilities
    probabilities = [count / total_items for count in supplier_counts.values()]

    # Compute Shannon entropy
    entropy = -sum(
        p * np.log(p) for p in probabilities if p > 0
    )

    # Normalize by maximum entropy (perfect diversification)
    max_entropy = np.log(len(supplier_counts))

    if max_entropy <= 0:
        return 0.0

    diversification = entropy / max_entropy
    return float(np.clip(diversification, 0.0, 1.0))


def compute_market_concentration_ratio(
    top_n_shares: List[float],
) -> float:
    """
    Compute concentration ratio of top N suppliers.

    CR_n = sum of top N market shares

    Args:
        top_n_shares: Sorted list of top N supplier market shares in descending order

    Returns:
        Concentration ratio in [0, 1] where 1 = top N control market
    """
    if not top_n_shares:
        return 0.0

    concentration = sum(top_n_shares)
    return float(np.clip(concentration, 0.0, 1.0))


def compute_exposure_from_concentration(
    hhi: float,
    supplier_count: int,
) -> float:
    """
    Compute exposure level based on HHI and supplier count.

    Exposure increases with HHI (concentration) and decreases with supplier count.

    Args:
        hhi: Herfindahl-Hirschman Index [0, 1]
        supplier_count: Number of suppliers

    Returns:
        Exposure in [0, 1]
    """
    hhi = np.clip(hhi, 0.0, 1.0)
    supplier_count = max(1, supplier_count)

    # Exposure = concentration * (1 - diversity factor)
    diversity_factor = min(1.0, np.log(supplier_count) / np.log(10))
    exposure = hhi * (1.0 - diversity_factor)

    return float(np.clip(exposure, 0.0, 1.0))


# Canonical alias for Master Prompt compliance
compute_exposure = compute_exposure_score
