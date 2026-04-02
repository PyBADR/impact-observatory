"""
Expected Claims Uplift Analysis for GCC Insurance Intelligence.

Implements claims uplift projection using the GCC formula:

DeltaClaims_p(t) = BaseClaims_p * (1 + chi1 * S_p(t) + chi2 * Stress(t) + chi3 * Uncertainty_p(t))

Where:
    chi1 = 0.45 (Claims surge weight)
    chi2 = 0.30 (System stress weight)
    chi3 = 0.25 (Uncertainty weight)
"""

from dataclasses import dataclass
from typing import Dict

from .gcc_insurance_config import GCCInsuranceConfig, GCC_INSURANCE_CONFIG


@dataclass
class ClaimsUpliftResult:
    """Results from expected claims uplift computation."""

    base_claims: float  # Original/baseline claims amount
    projected_claims: float  # Projected claims after uplift
    uplift_amount: float  # Absolute uplift (projected - base)
    uplift_percentage: float  # Relative uplift ((projected - base) / base * 100)
    chi_weights: Dict[str, float]  # Weights used in calculation


def compute_expected_claims_uplift(
    base_claims: float,
    surge_score: float,
    system_stress: float,
    uncertainty: float,
    config: GCCInsuranceConfig = None,
) -> ClaimsUpliftResult:
    """
    Compute expected claims uplift from baseline using GCC formula.

    The expected claims uplift formula projects how baseline claims will increase
    due to system stress, claims surge potential, and uncertainty:

    DeltaClaims_p(t) = BaseClaims_p * (1 + chi1 * S_p(t) + chi2 * Stress(t) + chi3 * Uncertainty_p(t))

    This represents the expected multiplier effect on claims from disruptions
    and system-wide events.

    Args:
        base_claims: Baseline claims amount (must be non-negative)
        surge_score: Claims surge potential (0-1)
        system_stress: Overall system stress level (0-1)
        uncertainty: Model uncertainty factor (0-1)
        config: GCCInsuranceConfig with weights. Uses GCC defaults if None.

    Returns:
        ClaimsUpliftResult with base, projected, and uplift metrics.

    Raises:
        ValueError: If inputs are invalid.
    """
    # Validate inputs
    if base_claims < 0:
        raise ValueError(f"Base claims must be non-negative, got {base_claims}")

    inputs = {
        "surge_score": surge_score,
        "system_stress": system_stress,
        "uncertainty": uncertainty,
    }

    for name, value in inputs.items():
        if not 0 <= value <= 1:
            raise ValueError(f"{name} must be in [0, 1], got {value}")

    if config is None:
        config = GCC_INSURANCE_CONFIG

    config.validate()

    # Extract weights
    weights = config.claims_uplift_weights
    chi1 = weights["surge"]
    chi2 = weights["stress"]
    chi3 = weights["uncertainty"]

    # Compute uplift multiplier
    # DeltaClaims_p(t) = BaseClaims_p * (1 + chi1 * S_p(t) + chi2 * Stress(t) + chi3 * Uncertainty_p(t))
    uplift_multiplier = 1.0 + (
        chi1 * surge_score + chi2 * system_stress + chi3 * uncertainty
    )

    # Compute projected claims
    projected_claims = base_claims * uplift_multiplier

    # Compute uplift metrics
    uplift_amount = projected_claims - base_claims
    if base_claims > 0:
        uplift_percentage = (uplift_amount / base_claims) * 100.0
    else:
        uplift_percentage = 0.0

    return ClaimsUpliftResult(
        base_claims=float(base_claims),
        projected_claims=float(projected_claims),
        uplift_amount=float(uplift_amount),
        uplift_percentage=float(uplift_percentage),
        chi_weights={
            "surge": chi1,
            "stress": chi2,
            "uncertainty": chi3,
        },
    )


# Canonical alias for Master Prompt compliance
compute_claims_uplift = compute_expected_claims_uplift
