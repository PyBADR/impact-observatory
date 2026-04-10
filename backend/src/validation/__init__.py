"""
Validation Contract Layer — enforces data integrity before API response.

Distinct from the sanity guard (which silently clamps values).
The validation layer DETECTS and FLAGS violations without mutating data,
so operators and auditors can see where the pipeline produced suspect values.

Applied BEFORE API response, BEFORE ROI computation, BEFORE persistence.
"""

from src.validation.contracts import validate_metrics, ValidationFlag

__all__ = ["validate_metrics", "ValidationFlag"]
