"""Claims Surge: Surge = base_claims * (1 + cat_factor)^severity
Computes surged claims with peak timing and reserve requirements.
"""
import numpy as np

# Default sector-to-catastrophe factor mapping
SECTOR_CAT_FACTORS = {
    "infrastructure": 1.5,
    "economy": 1.2,
    "finance": 1.0,
    "society": 0.8,
    "geography": 1.8,
}


def compute_claims_surge(
    base_claims: float, cat_factor: float, severity: float, duration_days: int = 30
) -> dict:
    """
    Compute claims surge multiplier and reserve requirements.

    Args:
        base_claims: Initial claims amount
        cat_factor: Catastrophe factor (0.5 to 3.0 typical)
        severity: Severity level (0.0 to 1.0)
        duration_days: Expected claim duration

    Returns:
        Dictionary with:
        - base_claims: Input base claims
        - surge_multiplier: (1 + cat_factor)^severity
        - surged_claims: Total claims after surge
        - daily_rate: Average daily claims rate
        - peak_day: Day of peak claims (at 30% of duration)
        - reserve_needed: 115% of surged claims
        - duration_days: Duration used
    """
    surge_multiplier = (1 + cat_factor) ** severity
    surged_claims = base_claims * surge_multiplier
    daily_rate = surged_claims / max(duration_days, 1)
    peak_day = int(duration_days * 0.3)
    reserve_needed = surged_claims * 1.15

    return {
        "base_claims": base_claims,
        "surge_multiplier": surge_multiplier,
        "surged_claims": surged_claims,
        "daily_rate": daily_rate,
        "peak_day": peak_day,
        "reserve_needed": reserve_needed,
        "duration_days": duration_days,
    }


def compute_gcc_claims_surge(
    scenario_severity: float, affected_sectors: list[str]
) -> dict:
    """
    Compute GCC-wide claims surge across multiple sectors.

    Args:
        scenario_severity: Scenario severity (0.0 to 1.0)
        affected_sectors: List of sector names

    Returns:
        Dictionary with:
        - total_surged_claims: Sum of all sector surges
        - sector_surges: Detailed surge for each sector
        - scenario_severity: Input severity
    """
    total_surge = 0.0
    sector_surges = {}

    for sector in affected_sectors:
        cat_factor = SECTOR_CAT_FACTORS.get(sector, 1.0)
        # Base premium estimate: 2.8B with 10% claims rate
        base = 28 * 0.1  # = 2.8 in billion units

        surge = compute_claims_surge(
            base_claims=base,
            cat_factor=cat_factor,
            severity=scenario_severity,
            duration_days=30,
        )
        sector_surges[sector] = surge
        total_surge += surge["surged_claims"]

    return {
        "total_surged_claims": total_surge,
        "sector_surges": sector_surges,
        "scenario_severity": scenario_severity,
    }
