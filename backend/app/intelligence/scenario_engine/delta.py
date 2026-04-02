"""Compute delta between baseline and shocked state.
Calculates losses and impacts per sector.
"""

# Sector GDP bases (in billions USD)
SECTOR_GDP_BASE = {
    "infrastructure": 450,
    "economy": 1200,
    "finance": 800,
    "society": 600,
    "geography": 200,
}


def compute_delta(baseline: dict, propagation_result, engine_result) -> dict:
    """
    Compute deltas between baseline and shocked state.

    Args:
        baseline: Baseline state dictionary
        propagation_result: Result from propagation engine
        engine_result: Result from scenario engine

    Returns:
        Dictionary with:
        - sector_deltas: Impact and loss per sector
        - total_loss: Sum of sector losses
        - engine_exposure: Total exposure from engine
    """
    sector_deltas = {}
    total_loss = 0.0

    for sector, gdp in SECTOR_GDP_BASE.items():
        # Find affected sectors in propagation result
        affected = [
            s
            for s in (propagation_result.affected_sectors or [])
            if getattr(s, "sector", None) == sector
        ]

        if affected:
            impact = getattr(affected[0], "avg_impact", 0)
            loss = gdp * impact
            sector_deltas[sector] = {
                "baseline_gdp": gdp,
                "impact": impact,
                "loss": loss,
            }
            total_loss += loss

    # Extract total exposure from engine result
    if hasattr(engine_result, "total_exposure"):
        total_exposure = engine_result.total_exposure
    elif isinstance(engine_result, dict):
        total_exposure = engine_result.get("totalExposure", 0)
    else:
        total_exposure = 0

    return {
        "sector_deltas": sector_deltas,
        "total_loss": total_loss,
        "engine_exposure": total_exposure,
    }
