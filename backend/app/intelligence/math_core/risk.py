"""Risk scoring with GCC asset class weights."""
import numpy as np
from ..engines.gcc_constants import GCC_ASSET_WEIGHTS


def compute_risk_score(asset_class: str, factors: list[float]) -> float:
    """R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U"""
    weights = GCC_ASSET_WEIGHTS.get(asset_class, [1/6]*6)
    return float(np.dot(weights[:len(factors)], factors[:len(weights)]))


def compute_composite_risk(asset_risks: dict[str, float], sector_gdp: dict[str, float]) -> dict:
    total_exposure = sum(risk * sector_gdp.get(k, 0) for k, risk in asset_risks.items())
    avg_risk = np.mean(list(asset_risks.values())) if asset_risks else 0
    return {"total_exposure": total_exposure, "avg_risk": float(avg_risk), "asset_risks": asset_risks}
