"""Insurance regulatory thresholds — IFRS-17 aligned for GCC.

Used by insurance_service.py to classify stress and trigger underwriting actions.
"""

from __future__ import annotations

# Loss Ratio thresholds
LOSS_RATIO_NORMAL = 0.65
LOSS_RATIO_WARNING = 0.75
LOSS_RATIO_CRITICAL = 0.85
LOSS_RATIO_SUSPENDED = 0.95

# Combined Ratio thresholds
COMBINED_RATIO_PROFITABLE = 0.95
COMBINED_RATIO_WARNING = 1.00
COMBINED_RATIO_CRITICAL = 1.05
COMBINED_RATIO_CATASTROPHIC = 1.15

# Claims Surge multiplier thresholds
CLAIMS_SURGE_NORMAL = 1.2
CLAIMS_SURGE_WARNING = 1.5
CLAIMS_SURGE_CRITICAL = 2.0
CLAIMS_SURGE_CATASTROPHIC = 3.0

# Underwriting status thresholds
UNDERWRITING_STATUS_MAP = {
    "normal": {"loss_ratio_max": LOSS_RATIO_NORMAL, "combined_ratio_max": COMBINED_RATIO_PROFITABLE},
    "warning": {"loss_ratio_max": LOSS_RATIO_WARNING, "combined_ratio_max": COMBINED_RATIO_WARNING},
    "critical": {"loss_ratio_max": LOSS_RATIO_CRITICAL, "combined_ratio_max": COMBINED_RATIO_CRITICAL},
    "suspended": {"loss_ratio_max": float("inf"), "combined_ratio_max": float("inf")},
}

# IFRS-17 Risk Adjustment
IFRS17_RA_CONFIDENCE_LEVEL = 0.75  # 75th percentile typical for GCC insurers
IFRS17_RA_MAX_INCREASE_PCT = 10.0  # Max RA increase in percentage points

# Reinsurance triggers
REINSURANCE_TRIGGER_CLAIMS_SURGE = 2.0     # Trigger at 2x claims surge
REINSURANCE_TRIGGER_LOSS_RATIO = 0.85      # Trigger above 85% loss ratio
REINSURANCE_CASCADE_THRESHOLD = 3.0        # Full cascade at 3x surge

# Solvency margin
SOLVENCY_MARGIN_MINIMUM_PCT = 100.0        # Minimum solvency margin
SOLVENCY_MARGIN_WARNING_PCT = 150.0        # Warning threshold
SOLVENCY_MARGIN_TARGET_PCT = 200.0         # Target for GCC insurers

# Time-to-insolvency thresholds (hours)
INSOLVENCY_WARNING_HOURS = 720     # 30 days
INSOLVENCY_CRITICAL_HOURS = 168    # 7 days
INSOLVENCY_EMERGENCY_HOURS = 72    # 3 days
