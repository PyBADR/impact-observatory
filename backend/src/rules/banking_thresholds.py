"""Banking regulatory thresholds — Basel III aligned for GCC.

Used by banking_service.py to classify stress levels and trigger decisions.
"""

from __future__ import annotations

# Capital Adequacy Ratio (CAR) — Basel III minimums
CAR_MINIMUM_PCT = 8.0          # Basel III absolute minimum
CAR_BUFFER_PCT = 2.5           # Capital conservation buffer
CAR_COUNTERCYCLICAL_PCT = 0.0  # GCC typically 0%
CAR_DSIBS_PCT = 1.0            # D-SIBs additional buffer (GCC average)
CAR_TOTAL_REQUIREMENT_PCT = CAR_MINIMUM_PCT + CAR_BUFFER_PCT + CAR_COUNTERCYCLICAL_PCT + CAR_DSIBS_PCT  # 11.5%

# Liquidity Coverage Ratio (LCR) — Basel III
LCR_MINIMUM_PCT = 100.0        # Must hold 100% HQLA vs 30-day outflow

# Net Stable Funding Ratio (NSFR) — Basel III
NSFR_MINIMUM_PCT = 100.0

# GCC-specific thresholds (SAMA, CBUAE typical)
SAMA_CAR_MINIMUM_PCT = 12.0    # Saudi Arabia requires higher
CBUAE_CAR_MINIMUM_PCT = 13.0   # UAE requires higher

# Stress classification thresholds
LIQUIDITY_STRESS_THRESHOLDS = {
    "NOMINAL": (0.0, 0.15),
    "LOW": (0.15, 0.30),
    "MODERATE": (0.30, 0.50),
    "ELEVATED": (0.50, 0.70),
    "CRITICAL": (0.70, 1.0),
}

CREDIT_STRESS_THRESHOLDS = {
    "NOMINAL": (0.0, 0.10),
    "LOW": (0.10, 0.25),
    "MODERATE": (0.25, 0.45),
    "ELEVATED": (0.45, 0.65),
    "CRITICAL": (0.65, 1.0),
}

# Time-to-breach thresholds (hours)
LIQUIDITY_BREACH_WARNING_HOURS = 168    # 7 days
LIQUIDITY_BREACH_CRITICAL_HOURS = 72    # 3 days
LIQUIDITY_BREACH_EMERGENCY_HOURS = 24   # 1 day

# Interbank contagion thresholds
CONTAGION_WARNING = 0.30
CONTAGION_CRITICAL = 0.60
