"""Claims surge prediction.

S_i(t) = ψ1*R_i(t) + ψ2*D_i(t) + ψ3*Exposure_i + ψ4*PolicySensitivity_i

Claims uplift:
    ΔClaims_p(t) = BaseClaims_p * (1 + χ1*S_p(t) + χ2*Stress(t) + χ3*Uncertainty_p(t))

Where:
    ψ1 = 0.28 (risk weight)
    ψ2 = 0.30 (disruption weight)
    ψ3 = 0.25 (exposure weight)
    ψ4 = 0.17 (policy sensitivity weight)
    χ1 = 0.45 (surge coefficient)
    χ2 = 0.30 (stress coefficient)
    χ3 = 0.25 (uncertainty coefficient)
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.gcc_weights import (
    CLAIMS_SURGE,
    CLAIMS_UPLIFT,
    ClaimsSurgeWeights,
    ClaimsUpliftParams,
)


@dataclass
class ClaimsSurgeResult:
    """Claims surge assessment for one node/portfolio."""
    entity_id: str
    surge_score: float
    risk_contribution: float
    disruption_contribution: float
    exposure_contribution: float
    policy_sensitivity_contribution: float
    claims_uplift_pct: float
    estimated_claims_delta_usd: float
    classification: str  # SEVERE / HIGH / MODERATE / LOW


def compute_claims_surge(
    entity_id: str,
    risk: float,
    disruption: float,
    exposure: float,
    policy_sensitivity: float,
    base_claims_usd: float = 0.0,
    system_stress: float = 0.0,
    uncertainty: float = 0.0,
    surge_weights: ClaimsSurgeWeights | None = None,
    uplift_params: ClaimsUpliftParams | None = None,
) -> ClaimsSurgeResult:
    """Compute claims surge score and uplift.

    S = ψ1*R + ψ2*D + ψ3*E + ψ4*PS
    ΔClaims = Base * (1 + χ1*S + χ2*Stress + χ3*U)
    """
    sw = surge_weights or CLAIMS_SURGE
    up = uplift_params or CLAIMS_UPLIFT

    r_c = sw.risk * np.clip(risk, 0, 1)
    d_c = sw.disruption * np.clip(disruption, 0, 1)
    e_c = sw.exposure * np.clip(exposure, 0, 1)
    ps_c = sw.policy_sensitivity * np.clip(policy_sensitivity, 0, 1)

    surge = float(np.clip(r_c + d_c + e_c + ps_c, 0.0, 1.0))

    # Claims uplift
    uplift_factor = 1.0 + up.chi1 * surge + up.chi2 * system_stress + up.chi3 * uncertainty
    claims_delta = base_claims_usd * (uplift_factor - 1.0)
    uplift_pct = (uplift_factor - 1.0) * 100.0

    if surge >= 0.7:
        cls = "SEVERE"
    elif surge >= 0.5:
        cls = "HIGH"
    elif surge >= 0.3:
        cls = "MODERATE"
    else:
        cls = "LOW"

    return ClaimsSurgeResult(
        entity_id=entity_id,
        surge_score=surge,
        risk_contribution=float(r_c),
        disruption_contribution=float(d_c),
        exposure_contribution=float(e_c),
        policy_sensitivity_contribution=float(ps_c),
        claims_uplift_pct=uplift_pct,
        estimated_claims_delta_usd=claims_delta,
        classification=cls,
    )


def compute_claims_surge_batch(
    entity_ids: list[str],
    risk_vector: NDArray[np.float64],
    disruption_vector: NDArray[np.float64],
    exposure_vector: NDArray[np.float64],
    sensitivity_vector: NDArray[np.float64],
    base_claims: NDArray[np.float64],
    system_stress: float = 0.0,
    uncertainty_vector: NDArray[np.float64] | None = None,
) -> tuple[NDArray[np.float64], list[ClaimsSurgeResult]]:
    """Batch claims surge computation."""
    n = len(entity_ids)
    unc = uncertainty_vector if uncertainty_vector is not None else np.zeros(n)

    results = []
    for i, eid in enumerate(entity_ids):
        r = compute_claims_surge(
            eid, risk_vector[i], disruption_vector[i], exposure_vector[i],
            sensitivity_vector[i], base_claims[i], system_stress, unc[i],
        )
        results.append(r)

    scores = np.array([r.surge_score for r in results], dtype=np.float64)
    return scores, results
