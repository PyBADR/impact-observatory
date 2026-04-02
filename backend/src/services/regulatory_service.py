"""Service: Regulatory State — aggregate compliance status across GCC jurisdictions."""

from __future__ import annotations
from datetime import datetime, timezone

# GCC regulatory thresholds by jurisdiction
GCC_THRESHOLDS = {
    "SA": {"car_min": 0.12, "lcr_min": 1.0, "nsfr_min": 1.0, "solvency_min": 1.0, "regulator": "SAMA"},
    "AE": {"car_min": 0.13, "lcr_min": 1.0, "nsfr_min": 1.0, "solvency_min": 1.0, "regulator": "CBUAE"},
    "QA": {"car_min": 0.125, "lcr_min": 1.0, "nsfr_min": 1.0, "solvency_min": 1.0, "regulator": "QCB"},
    "KW": {"car_min": 0.13, "lcr_min": 1.0, "nsfr_min": 1.0, "solvency_min": 1.0, "regulator": "CBK"},
    "BH": {"car_min": 0.125, "lcr_min": 1.0, "nsfr_min": 1.0, "solvency_min": 1.0, "regulator": "CBB"},
    "OM": {"car_min": 0.12, "lcr_min": 1.0, "nsfr_min": 1.0, "solvency_min": 1.0, "regulator": "CBO"},
}

def compute_regulatory_state(run_id: str, banking: dict, insurance: dict, fintech: dict, jurisdiction: str = "AE") -> dict:
    """Compute aggregate regulatory state from sector stress data."""
    thresholds = GCC_THRESHOLDS.get(jurisdiction, GCC_THRESHOLDS["AE"])

    banking_stress = banking.get("aggregate_stress", 0) if isinstance(banking, dict) else 0
    insurance_stress = insurance.get("aggregate_stress", 0) if isinstance(insurance, dict) else 0
    fintech_stress = fintech.get("aggregate_stress", 0) if isinstance(fintech, dict) else 0

    # Derive regulatory ratios from stress levels
    aggregate_lcr = max(0.0, 1.0 - banking_stress * 0.6)
    aggregate_nsfr = max(0.0, 1.0 - banking_stress * 0.3)
    aggregate_solvency = max(0.0, 1.0 - insurance_stress * 0.4)
    aggregate_car = max(0.0, thresholds["car_min"] * (1.0 - banking_stress * 0.5))

    # Determine breach level
    breaches = []
    if aggregate_lcr < thresholds["lcr_min"]:
        breaches.append("lcr_breach")
    if aggregate_nsfr < thresholds["nsfr_min"]:
        breaches.append("nsfr_breach")
    if aggregate_solvency < thresholds["solvency_min"]:
        breaches.append("solvency_breach")
    if aggregate_car < thresholds["car_min"]:
        breaches.append("car_breach")

    if len(breaches) >= 3 or (aggregate_lcr < 0.5 and banking_stress > 0.8):
        breach_level = "critical"
    elif len(breaches) >= 2:
        breach_level = "major"
    elif len(breaches) >= 1:
        breach_level = "minor"
    else:
        breach_level = "none"

    mandatory_actions = []
    if breach_level == "critical":
        mandatory_actions = ["notify_regulator_within_24h", "freeze_high_risk_exposure_growth", "activate_contingency_funding_plan"]
    elif breach_level == "major":
        mandatory_actions = ["notify_regulator_within_24h", "prepare_recovery_plan"]
    elif breach_level == "minor":
        mandatory_actions = ["monitor_and_report"]

    return {
        "run_id": run_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "jurisdiction": jurisdiction,
        "regulatory_version": "2.4.0",
        "aggregate_lcr": round(aggregate_lcr, 4),
        "aggregate_nsfr": round(aggregate_nsfr, 4),
        "aggregate_solvency_ratio": round(aggregate_solvency, 4),
        "aggregate_capital_adequacy_ratio": round(aggregate_car, 4),
        "breach_level": breach_level,
        "mandatory_actions": mandatory_actions,
        "reporting_required": breach_level in ("major", "critical"),
    }
