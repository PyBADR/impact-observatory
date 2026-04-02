"""Insurance Intelligence Package
Modules for portfolio exposure, claims surge, underwriting watch, and severity projections.
"""

from .portfolio_exposure import compute_portfolio_exposure, GCC_ZONE_FACTORS, CAT_LOADINGS
from .claims_surge import compute_claims_surge, compute_gcc_claims_surge
from .underwriting_watch import evaluate_underwriting_watch, WATCH_THRESHOLDS
from .severity_projection import compute_severity_projection

__all__ = [
    "compute_portfolio_exposure",
    "GCC_ZONE_FACTORS",
    "CAT_LOADINGS",
    "compute_claims_surge",
    "compute_gcc_claims_surge",
    "evaluate_underwriting_watch",
    "WATCH_THRESHOLDS",
    "compute_severity_projection",
]
