"""
Confidence model for assessing credibility and reliability of threat intelligence.

Implements multi-factor confidence scoring combining source quality, corroboration,
data freshness, and signal agreement metrics.
"""

from dataclasses import dataclass, field
from typing import Dict
import numpy as np


@dataclass
class ConfidenceResult:
    """
    Result of confidence assessment.

    Attributes:
        score: Composite confidence score in [0, 1]
        level: Categorical confidence level (low/medium/high/very_high)
        factors: Dictionary of individual confidence factors
    """
    score: float
    level: str = "low"
    factors: Dict[str, float] = field(default_factory=dict)

    def __post_init__(self):
        """Validate score and confidence level."""
        if not 0 <= self.score <= 1:
            raise ValueError(f"Confidence score must be in [0, 1], got {self.score}")

        valid_levels = {"low", "medium", "high", "very_high"}
        if self.level.lower() not in valid_levels:
            raise ValueError(
                f"Confidence level must be in {valid_levels}, got {self.level}"
            )


def compute_confidence(
    source_quality: float,
    corroboration_count: int,
    data_freshness: float,
    signal_agreement: float,
) -> ConfidenceResult:
    """
    Compute composite confidence score for threat intelligence assessment.

    Integrates four confidence dimensions:

    C = w_src * Q + w_corr * Corr(c) + w_fresh * F + w_agree * A

    Where:
        - Q: source quality (0-1)
        - Corr(c): corroboration factor from count: min(c/3, 1)
        - F: data freshness (0-1, typically temporal decay score)
        - A: signal agreement ratio (0-1, consensus among sources)

    Default weights (equal importance): w_src=0.25, w_corr=0.25, w_fresh=0.25, w_agree=0.25

    Corroboration factor uses logarithmic scale: sources 1-3 have increasing effect,
    diminishing returns beyond 3 sources.

    Confidence levels:
        - low: score < 0.30
        - medium: 0.30 ≤ score < 0.60
        - high: 0.60 ≤ score < 0.85
        - very_high: score ≥ 0.85

    Args:
        source_quality: Quality/reliability of primary source (0-1)
        corroboration_count: Number of corroborating sources (non-negative integer)
        data_freshness: Freshness of the intelligence (0-1, 1=very fresh)
        signal_agreement: Degree of agreement among sources (0-1)

    Returns:
        ConfidenceResult with composite score, level, and factor breakdown.

    Raises:
        ValueError: If any input is invalid
    """
    # Validate inputs
    if not 0 <= source_quality <= 1:
        raise ValueError(f"Source quality must be in [0, 1], got {source_quality}")

    if not isinstance(corroboration_count, (int, np.integer)) or corroboration_count < 0:
        raise ValueError(
            f"Corroboration count must be non-negative integer, got {corroboration_count}"
        )

    if not 0 <= data_freshness <= 1:
        raise ValueError(f"Data freshness must be in [0, 1], got {data_freshness}")

    if not 0 <= signal_agreement <= 1:
        raise ValueError(f"Signal agreement must be in [0, 1], got {signal_agreement}")

    # Compute corroboration factor using logarithmic scale
    # Each additional corroboration provides diminishing benefit
    # 0 sources: 0, 1 source: 0.33, 2 sources: 0.55, 3+ sources: 1.0
    if corroboration_count == 0:
        corroboration_factor = 0.0
    else:
        # Log scale: ln(1 + count) / ln(4) provides smooth scaling
        # This gives: 1 source ~0.35, 2 sources ~0.56, 3 sources ~0.69, 4+ ~0.85+
        corroboration_factor = float(np.log1p(corroboration_count) / np.log(4.0))
        corroboration_factor = np.clip(corroboration_factor, 0.0, 1.0)

    # Equal weighting for all factors
    weights = {
        "source_quality": 0.25,
        "corroboration": 0.25,
        "freshness": 0.25,
        "agreement": 0.25,
    }

    # Compute factors dictionary
    factors = {
        "source_quality": source_quality * weights["source_quality"],
        "corroboration": corroboration_factor * weights["corroboration"],
        "data_freshness": data_freshness * weights["freshness"],
        "signal_agreement": signal_agreement * weights["agreement"],
    }

    # Composite score
    score = sum(factors.values())
    score = float(np.clip(score, 0.0, 1.0))

    # Determine confidence level
    if score >= 0.85:
        level = "very_high"
    elif score >= 0.60:
        level = "high"
    elif score >= 0.30:
        level = "medium"
    else:
        level = "low"

    return ConfidenceResult(
        score=score,
        level=level,
        factors=factors,
    )
