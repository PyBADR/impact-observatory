"""
Insurance Intelligence Layer for GCC Impact Observatory platform.

This module provides comprehensive insurance risk assessment, claims projection,
portfolio management, and severity analysis for GCC-based insurance portfolios.
Implements weighted aggregation models, regional risk adjustment, and bilingual
reporting (English/Arabic) with production-grade configuration management.

Core Components:
- GCC Insurance Configuration: Centralized weights, thresholds, and regional multipliers
- Portfolio Exposure Analysis: TIV-based policy-level risk aggregation
- Claims Surge Potential: Real-time claims volatility assessment
- Claims Uplift Projection: Stress-adjusted loss ratio forecasting
- Underwriting Watch: Classification-based risk monitoring and actions
- Severity Projection: Historical calibration with trend analysis
- Insurance Engine: Multi-dimensional orchestration and scenario analysis

Regional Multipliers (GCC):
  Kuwait (KW): 1.05, Saudi Arabia (SA): 1.15, UAE (AE): 1.20,
  Qatar (QA): 1.10, Bahrain (BH): 1.00, Oman (OM): 0.95

Weights and Thresholds:
  Portfolio Exposure: gamma1=0.30, gamma2=0.25, gamma3=0.25, gamma4=0.20
  Claims Surge: psi1=0.28, psi2=0.30, psi3=0.25, psi4=0.17
  Claims Uplift: chi1=0.40, chi2=0.35, chi3=0.25
  Underwriting: 0.40 region risk, 0.25 logistics, 0.20 surge, 0.15 uncertainty
  Thresholds: STANDARD 0-25, MONITORED 25-50, RESTRICTED 50-70, REFERRAL 70+
"""

# Configuration
from .gcc_insurance_config import (
    GCCInsuranceConfig,
    GCC_INSURANCE_CONFIG,
)

# Portfolio Exposure
from .portfolio_exposure import (
    PolicyExposure,
    PortfolioExposureResult,
    compute_portfolio_exposure,
)

# Claims Surge
from .claims_surge import (
    SeverityLevel,
    ClaimsSurgeResult,
    compute_claims_surge_potential,
)

# Claims Uplift
from .claims_uplift import (
    ClaimsUpliftResult,
    compute_expected_claims_uplift,
)

# Underwriting Watch
from .underwriting_watch import (
    UnderwritingClassification,
    UnderwritingResult,
    compute_underwriting_restriction,
)

# Severity Projection
from .severity_projection import (
    TrendDirection,
    SeverityProjection,
    project_severity,
)

# Insurance Engine
from .insurance_engine import (
    AssessmentLevel,
    PolicyAssessment,
    PortfolioAssessment,
    ScenarioImpact,
    InsuranceIntelligenceEngine,
)

__all__ = [
    # Configuration
    "GCCInsuranceConfig",
    "GCC_INSURANCE_CONFIG",
    
    # Portfolio Exposure
    "PolicyExposure",
    "PortfolioExposureResult",
    "compute_portfolio_exposure",
    
    # Claims Surge
    "SeverityLevel",
    "ClaimsSurgeResult",
    "compute_claims_surge_potential",
    
    # Claims Uplift
    "ClaimsUpliftResult",
    "compute_expected_claims_uplift",
    
    # Underwriting Watch
    "UnderwritingClassification",
    "UnderwritingResult",
    "compute_underwriting_restriction",
    
    # Severity Projection
    "TrendDirection",
    "SeverityProjection",
    "project_severity",
    
    # Insurance Engine
    "AssessmentLevel",
    "PolicyAssessment",
    "PortfolioAssessment",
    "ScenarioImpact",
    "InsuranceIntelligenceEngine",
]

__version__ = "1.0.0"
__author__ = "GCC Impact Observatory"
