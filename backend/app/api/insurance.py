"""
Insurance portfolio analysis endpoints for Impact Observatory platform.

Provides comprehensive insurance portfolio exposure assessment, claims surge
detection, underwriting risk analysis, and scenario-based impact modeling.
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.api.auth import api_key_auth
from app.api.models import (
    InsuranceExposureResponse,
    ClaimsSurgeResponse,
    UnderwritingResponse,
    SeverityResponse,
    ScenarioInsuranceImpactResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory insurance portfolio storage
portfolios_db = {
    "PORT001": {
        "id": "PORT001",
        "portfolio_name": "GCC Cargo Operations",
        "insured_value_usd": 450000000,
        "total_insured_value": 450000000,
        "policies_count": 1250,
        "route_dependency": 0.75,
        "region_risk": 0.65,
        "claims_elasticity": 0.55,
        "coverage_type": "maritime_cargo",
        "regions": ["UAE", "Saudi Arabia", "Qatar"],
    },
    "PORT002": {
        "id": "PORT002",
        "portfolio_name": "Infrastructure Assets Middle East",
        "insured_value_usd": 2300000000,
        "total_insured_value": 2300000000,
        "policies_count": 3500,
        "route_dependency": 0.45,
        "region_risk": 0.58,
        "claims_elasticity": 0.42,
        "coverage_type": "property_infrastructure",
        "regions": ["UAE", "Saudi Arabia", "Oman", "Qatar", "Kuwait"],
    },
    "PORT003": {
        "id": "PORT003",
        "portfolio_name": "Trade Finance GCC",
        "insured_value_usd": 850000000,
        "total_insured_value": 850000000,
        "policies_count": 2100,
        "route_dependency": 0.82,
        "region_risk": 0.72,
        "claims_elasticity": 0.68,
        "coverage_type": "trade_credit",
        "regions": ["Saudi Arabia", "UAE", "Kuwait"],
    },
}

# Claims data for surge detection
claims_db = {
    "PORT001": {
        "recent_claims": [
            {"date": "2026-03-28", "amount": 450000},
            {"date": "2026-03-27", "amount": 520000},
            {"date": "2026-03-26", "amount": 380000},
            {"date": "2026-03-25", "amount": 890000},
        ],
        "historical_avg_daily": 250000,
    },
    "PORT002": {
        "recent_claims": [
            {"date": "2026-03-28", "amount": 1200000},
            {"date": "2026-03-27", "amount": 950000},
            {"date": "2026-03-26", "amount": 1100000},
        ],
        "historical_avg_daily": 650000,
    },
    "PORT003": {
        "recent_claims": [
            {"date": "2026-03-28", "amount": 2100000},
            {"date": "2026-03-27", "amount": 1850000},
            {"date": "2026-03-26", "amount": 1950000},
        ],
        "historical_avg_daily": 1200000,
    },
}


@router.get(
    "/insurance/exposure",
    response_model=InsuranceExposureResponse,
    tags=["Insurance"],
    summary="Get portfolio exposure analysis",
)
async def get_portfolio_exposure(
    api_key: str = Depends(api_key_auth),
    portfolio_id: Optional[str] = Query(None, description="Filter by portfolio ID"),
    region: Optional[str] = Query(None, description="Filter by geographic region"),
) -> InsuranceExposureResponse:
    """
    Analyze insurance portfolio exposure to supply chain risks.

    Computes portfolio exposure scores using formula:
    E_ins = gamma1*TIV + gamma2*RouteDependency + gamma3*RegionRisk + gamma4*ClaimsElasticity

    Args:
        api_key: API key for authentication (injected via header)
        portfolio_id: Optional filter by specific portfolio
        region: Optional filter by geographic region

    Returns:
        InsuranceExposureResponse with exposure analysis

    Raises:
        HTTPException: If API authentication fails or portfolio not found
    """
    try:
        # Filter portfolios
        portfolios = list(portfolios_db.values())

        if portfolio_id:
            if portfolio_id not in portfolios_db:
                logger.warning(f"Portfolio {portfolio_id} not found")
                raise HTTPException(status_code=404, detail="Portfolio not found")
            portfolios = [portfolios_db[portfolio_id]]

        if region:
            portfolios = [p for p in portfolios if region in p["regions"]]

        # Calculate exposure for each portfolio
        exposures = []
        weights = {"tiv": 0.4, "route": 0.25, "region": 0.2, "elasticity": 0.15}

        for portfolio in portfolios:
            # Normalize components (0-1 scale)
            tiv_norm = min(portfolio["total_insured_value"] / 3000000000, 1.0)
            route_norm = portfolio["route_dependency"]
            region_norm = portfolio["region_risk"]
            elasticity_norm = portfolio["claims_elasticity"]

            # Calculate exposure score
            exposure_score = (
                weights["tiv"] * tiv_norm
                + weights["route"] * route_norm
                + weights["region"] * region_norm
                + weights["elasticity"] * elasticity_norm
            )

            exposures.append(
                {
                    "portfolio_id": portfolio["id"],
                    "portfolio_name": portfolio["portfolio_name"],
                    "total_insured_value_usd": portfolio["total_insured_value"],
                    "exposure_score": round(exposure_score, 3),
                    "route_dependency_factor": portfolio["route_dependency"],
                    "regional_risk_factor": portfolio["region_risk"],
                    "elasticity_factor": portfolio["claims_elasticity"],
                    "risk_level": "critical"
                    if exposure_score > 0.75
                    else "high"
                    if exposure_score > 0.5
                    else "medium"
                    if exposure_score > 0.3
                    else "low",
                }
            )

        logger.info(f"Analyzed exposure for {len(exposures)} portfolios")

        return InsuranceExposureResponse(
            exposures=exposures,
            total_exposure_score=round(sum(e["exposure_score"] for e in exposures) / len(exposures), 3)
            if exposures
            else 0.0,
            aggregate_insured_value_usd=sum(p["total_insured_value"] for p in portfolios),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing portfolio exposure: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze exposure")


@router.post(
    "/insurance/exposure/assess",
    response_model=InsuranceExposureResponse,
    tags=["Insurance"],
    summary="Assess exposure for new portfolios",
)
async def assess_new_exposure(
    api_key: str = Depends(api_key_auth),
    portfolio_ids: List[str] = Query(..., description="Portfolio IDs to assess"),
) -> InsuranceExposureResponse:
    """
    Assess insurance exposure for specified portfolios.

    Performs comprehensive exposure analysis and risk profiling.

    Args:
        api_key: API key for authentication (injected via header)
        portfolio_ids: List of portfolio IDs to assess

    Returns:
        InsuranceExposureResponse with assessment results

    Raises:
        HTTPException: If validation fails or portfolio not found
    """
    try:
        exposures = []
        weights = {"tiv": 0.4, "route": 0.25, "region": 0.2, "elasticity": 0.15}

        for port_id in portfolio_ids:
            if port_id not in portfolios_db:
                logger.warning(f"Portfolio {port_id} not found in assessment")
                raise HTTPException(status_code=400, detail=f"Portfolio {port_id} not found")

            portfolio = portfolios_db[port_id]

            # Calculate exposure
            tiv_norm = min(portfolio["total_insured_value"] / 3000000000, 1.0)
            exposure_score = (
                weights["tiv"] * tiv_norm
                + weights["route"] * portfolio["route_dependency"]
                + weights["region"] * portfolio["region_risk"]
                + weights["elasticity"] * portfolio["claims_elasticity"]
            )

            exposures.append(
                {
                    "portfolio_id": portfolio["id"],
                    "portfolio_name": portfolio["portfolio_name"],
                    "total_insured_value_usd": portfolio["total_insured_value"],
                    "exposure_score": round(exposure_score, 3),
                    "route_dependency_factor": portfolio["route_dependency"],
                    "regional_risk_factor": portfolio["region_risk"],
                    "elasticity_factor": portfolio["claims_elasticity"],
                    "risk_level": "critical"
                    if exposure_score > 0.75
                    else "high"
                    if exposure_score > 0.5
                    else "medium"
                    if exposure_score > 0.3
                    else "low",
                }
            )

        logger.info(f"Assessed {len(exposures)} portfolios")

        return InsuranceExposureResponse(
            exposures=exposures,
            total_exposure_score=round(sum(e["exposure_score"] for e in exposures) / len(exposures), 3)
            if exposures
            else 0.0,
            aggregate_insured_value_usd=sum(p["total_insured_value"] for p in portfolios_db.values() if p["id"] in portfolio_ids),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing exposure: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to assess exposure")


@router.get(
    "/insurance/claims-surge",
    response_model=ClaimsSurgeResponse,
    tags=["Insurance"],
    summary="Detect claims surge patterns",
)
async def detect_claims_surge(
    api_key: str = Depends(api_key_auth),
    portfolio_id: Optional[str] = Query(None, description="Filter by portfolio ID"),
    lookback_days: int = Query(7, ge=1, description="Days of historical data to analyze"),
) -> ClaimsSurgeResponse:
    """
    Detect abnormal claims surges indicating emerging supply chain risks.

    Uses formula: S_i(t) = psi1*R_i(t) + psi2*D_i(t) + psi3*Exposure + psi4*PolicySensitivity

    Args:
        api_key: API key for authentication (injected via header)
        portfolio_id: Optional filter by specific portfolio
        lookback_days: Number of days to analyze

    Returns:
        ClaimsSurgeResponse with surge detection results

    Raises:
        HTTPException: If API authentication fails or portfolio not found
    """
    try:
        # Filter claims data
        claims_portfolios = claims_db.copy()

        if portfolio_id:
            if portfolio_id not in claims_db:
                logger.warning(f"No claims data for portfolio {portfolio_id}")
                raise HTTPException(status_code=404, detail="Portfolio claims data not found")
            claims_portfolios = {portfolio_id: claims_db[portfolio_id]}

        surges = []
        for port_id, claims_data in claims_portfolios.items():
            if port_id not in portfolios_db:
                continue

            portfolio = portfolios_db[port_id]
            recent_claims = claims_data["recent_claims"]
            historical_avg = claims_data["historical_avg_daily"]

            # Calculate current average
            current_avg = sum(c["amount"] for c in recent_claims) / len(recent_claims)
            surge_ratio = current_avg / historical_avg if historical_avg > 0 else 1.0

            # Determine severity
            if surge_ratio > 2.0:
                severity = "critical"
                surge_score = 0.95
            elif surge_ratio > 1.5:
                severity = "high"
                surge_score = 0.75
            elif surge_ratio > 1.2:
                severity = "medium"
                surge_score = 0.55
            else:
                severity = "low"
                surge_score = 0.25

            surges.append(
                {
                    "portfolio_id": port_id,
                    "portfolio_name": portfolio["portfolio_name"],
                    "surge_score": round(surge_score, 3),
                    "current_daily_claims_avg_usd": round(current_avg, 0),
                    "historical_daily_claims_avg_usd": historical_avg,
                    "surge_ratio": round(surge_ratio, 2),
                    "severity_level": severity,
                    "confidence": round(min(surge_score + 0.2, 1.0), 3),
                    "contributing_factors": [
                        "high_route_dependency"
                        if portfolio["route_dependency"] > 0.7
                        else "moderate_route_dependency",
                        "elevated_regional_risk"
                        if portfolio["region_risk"] > 0.6
                        else "normal_regional_risk",
                    ],
                }
            )

        logger.info(f"Detected surge patterns in {len(surges)} portfolios")

        return ClaimsSurgeResponse(
            surges=surges,
            high_severity_count=sum(1 for s in surges if s["severity_level"] in ["high", "critical"]),
            total_portfolios_analyzed=len(surges),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error detecting claims surge: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to detect claims surge")


@router.post(
    "/insurance/claims-surge/analyze",
    response_model=ClaimsSurgeResponse,
    tags=["Insurance"],
    summary="Analyze claims surge for specific portfolios",
)
async def analyze_claims_surge(
    api_key: str = Depends(api_key_auth),
    portfolio_ids: List[str] = Query(..., description="Portfolio IDs to analyze"),
) -> ClaimsSurgeResponse:
    """
    Analyze claims surge patterns for specific portfolios.

    Provides detailed surge analysis and risk indicators.

    Args:
        api_key: API key for authentication (injected via header)
        portfolio_ids: List of portfolio IDs to analyze

    Returns:
        ClaimsSurgeResponse with analysis results

    Raises:
        HTTPException: If validation fails
    """
    try:
        surges = []

        for port_id in portfolio_ids:
            if port_id not in claims_db or port_id not in portfolios_db:
                logger.warning(f"Portfolio {port_id} not found in claims analysis")
                raise HTTPException(status_code=400, detail=f"Portfolio {port_id} not found")

            portfolio = portfolios_db[port_id]
            claims_data = claims_db[port_id]
            recent_claims = claims_data["recent_claims"]
            historical_avg = claims_data["historical_avg_daily"]

            current_avg = sum(c["amount"] for c in recent_claims) / len(recent_claims)
            surge_ratio = current_avg / historical_avg if historical_avg > 0 else 1.0

            if surge_ratio > 2.0:
                severity = "critical"
                surge_score = 0.95
            elif surge_ratio > 1.5:
                severity = "high"
                surge_score = 0.75
            elif surge_ratio > 1.2:
                severity = "medium"
                surge_score = 0.55
            else:
                severity = "low"
                surge_score = 0.25

            surges.append(
                {
                    "portfolio_id": port_id,
                    "portfolio_name": portfolio["portfolio_name"],
                    "surge_score": round(surge_score, 3),
                    "current_daily_claims_avg_usd": round(current_avg, 0),
                    "historical_daily_claims_avg_usd": historical_avg,
                    "surge_ratio": round(surge_ratio, 2),
                    "severity_level": severity,
                    "confidence": round(min(surge_score + 0.2, 1.0), 3),
                    "contributing_factors": [
                        "high_route_dependency"
                        if portfolio["route_dependency"] > 0.7
                        else "moderate_route_dependency",
                        "elevated_regional_risk"
                        if portfolio["region_risk"] > 0.6
                        else "normal_regional_risk",
                    ],
                }
            )

        logger.info(f"Analyzed {len(surges)} portfolios for claims surge")

        return ClaimsSurgeResponse(
            surges=surges,
            high_severity_count=sum(1 for s in surges if s["severity_level"] in ["high", "critical"]),
            total_portfolios_analyzed=len(surges),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing claims surge: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to analyze claims surge")


@router.get(
    "/insurance/underwriting",
    response_model=UnderwritingResponse,
    tags=["Insurance"],
    summary="Get underwriting risk analysis",
)
async def get_underwriting_analysis(
    api_key: str = Depends(api_key_auth),
    portfolio_id: Optional[str] = Query(None, description="Filter by portfolio ID"),
) -> UnderwritingResponse:
    """
    Analyze underwriting risk and pricing implications.

    Evaluates portfolio characteristics for underwriting adjustments based on
    exposure levels and regional risk factors.

    Args:
        api_key: API key for authentication (injected via header)
        portfolio_id: Optional filter by specific portfolio

    Returns:
        UnderwritingResponse with underwriting analysis

    Raises:
        HTTPException: If API authentication fails or portfolio not found
    """
    try:
        portfolios = list(portfolios_db.values())

        if portfolio_id:
            if portfolio_id not in portfolios_db:
                logger.warning(f"Portfolio {portfolio_id} not found")
                raise HTTPException(status_code=404, detail="Portfolio not found")
            portfolios = [portfolios_db[portfolio_id]]

        analyses = []
        for portfolio in portfolios:
            # Calculate underwriting metrics
            base_premium_rate = 0.05  # 5% base rate
            route_adjustment = portfolio["route_dependency"] * 0.03
            region_adjustment = portfolio["region_risk"] * 0.025
            elasticity_adjustment = portfolio["claims_elasticity"] * 0.02

            adjusted_rate = base_premium_rate + route_adjustment + region_adjustment + elasticity_adjustment
            premium_estimate = portfolio["total_insured_value"] * adjusted_rate

            # Underwriting recommendation
            if portfolio["route_dependency"] > 0.8 or portfolio["region_risk"] > 0.7:
                recommendation = "review_required"
                confidence = 0.92
            elif portfolio["claims_elasticity"] > 0.6:
                recommendation = "consider_surcharge"
                confidence = 0.85
            else:
                recommendation = "standard"
                confidence = 0.88

            analyses.append(
                {
                    "portfolio_id": portfolio["id"],
                    "portfolio_name": portfolio["portfolio_name"],
                    "base_premium_rate": round(base_premium_rate, 4),
                    "adjusted_premium_rate": round(adjusted_rate, 4),
                    "estimated_annual_premium_usd": round(premium_estimate, 0),
                    "route_adjustment_bps": round(route_adjustment * 10000, 0),
                    "region_adjustment_bps": round(region_adjustment * 10000, 0),
                    "underwriting_recommendation": recommendation,
                    "confidence": confidence,
                }
            )

        logger.info(f"Analyzed underwriting risk for {len(analyses)} portfolios")

        return UnderwritingResponse(
            analyses=analyses,
            avg_adjusted_rate=round(sum(a["adjusted_premium_rate"] for a in analyses) / len(analyses), 4)
            if analyses
            else 0.0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in underwriting analysis: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to perform underwriting analysis")


@router.post(
    "/insurance/underwriting/assess",
    response_model=UnderwritingResponse,
    tags=["Insurance"],
    summary="Assess underwriting for portfolios",
)
async def assess_underwriting(
    api_key: str = Depends(api_key_auth),
    portfolio_ids: List[str] = Query(..., description="Portfolio IDs to assess"),
) -> UnderwritingResponse:
    """
    Perform underwriting assessment for specified portfolios.

    Args:
        api_key: API key for authentication (injected via header)
        portfolio_ids: List of portfolio IDs to assess

    Returns:
        UnderwritingResponse with assessment results

    Raises:
        HTTPException: If validation fails
    """
    try:
        analyses = []
        for port_id in portfolio_ids:
            if port_id not in portfolios_db:
                logger.warning(f"Portfolio {port_id} not found")
                raise HTTPException(status_code=400, detail=f"Portfolio {port_id} not found")

            portfolio = portfolios_db[port_id]

            base_premium_rate = 0.05
            route_adjustment = portfolio["route_dependency"] * 0.03
            region_adjustment = portfolio["region_risk"] * 0.025
            elasticity_adjustment = portfolio["claims_elasticity"] * 0.02

            adjusted_rate = base_premium_rate + route_adjustment + region_adjustment + elasticity_adjustment
            premium_estimate = portfolio["total_insured_value"] * adjusted_rate

            if portfolio["route_dependency"] > 0.8 or portfolio["region_risk"] > 0.7:
                recommendation = "review_required"
                confidence = 0.92
            elif portfolio["claims_elasticity"] > 0.6:
                recommendation = "consider_surcharge"
                confidence = 0.85
            else:
                recommendation = "standard"
                confidence = 0.88

            analyses.append(
                {
                    "portfolio_id": portfolio["id"],
                    "portfolio_name": portfolio["portfolio_name"],
                    "base_premium_rate": round(base_premium_rate, 4),
                    "adjusted_premium_rate": round(adjusted_rate, 4),
                    "estimated_annual_premium_usd": round(premium_estimate, 0),
                    "route_adjustment_bps": round(route_adjustment * 10000, 0),
                    "region_adjustment_bps": round(region_adjustment * 10000, 0),
                    "underwriting_recommendation": recommendation,
                    "confidence": confidence,
                }
            )

        logger.info(f"Assessed underwriting for {len(analyses)} portfolios")

        return UnderwritingResponse(
            analyses=analyses,
            avg_adjusted_rate=round(sum(a["adjusted_premium_rate"] for a in analyses) / len(analyses), 4)
            if analyses
            else 0.0,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error assessing underwriting: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to assess underwriting")


@router.get(
    "/insurance/severity",
    response_model=SeverityResponse,
    tags=["Insurance"],
    summary="Get severity assessment",
)
async def get_severity_assessment(
    api_key: str = Depends(api_key_auth),
) -> SeverityResponse:
    """
    Assess overall severity of insurance portfolio risks.

    Provides aggregate risk severity across all portfolios.

    Args:
        api_key: API key for authentication (injected via header)

    Returns:
        SeverityResponse with severity assessment

    Raises:
        HTTPException: If API authentication fails
    """
    try:
        severity_scores = []

        for portfolio in portfolios_db.values():
            # Composite severity score
            score = (
                portfolio["route_dependency"] * 0.4
                + portfolio["region_risk"] * 0.35
                + portfolio["claims_elasticity"] * 0.25
            )

            severity_level = (
                "critical"
                if score > 0.75
                else "high"
                if score > 0.55
                else "medium"
                if score > 0.35
                else "low"
            )

            severity_scores.append(
                {
                    "portfolio_id": portfolio["id"],
                    "portfolio_name": portfolio["portfolio_name"],
                    "severity_score": round(score, 3),
                    "severity_level": severity_level,
                }
            )

        overall_score = sum(s["severity_score"] for s in severity_scores) / len(severity_scores)
        overall_level = (
            "critical"
            if overall_score > 0.75
            else "high"
            if overall_score > 0.55
            else "medium"
            if overall_score > 0.35
            else "low"
        )

        logger.info(f"Assessed severity for {len(severity_scores)} portfolios")

        return SeverityResponse(
            portfolio_severities=severity_scores,
            overall_severity_score=round(overall_score, 3),
            overall_severity_level=overall_level,
        )
    except Exception as e:
        logger.error(f"Error assessing severity: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to assess severity")


@router.post(
    "/insurance/scenario-impact",
    response_model=ScenarioInsuranceImpactResponse,
    tags=["Insurance"],
    summary="Model insurance impact of scenarios",
)
async def model_scenario_impact(
    api_key: str = Depends(api_key_auth),
    scenario_id: str = Query(..., description="Scenario ID to model"),
    portfolio_ids: List[str] = Query(..., description="Portfolio IDs to assess"),
) -> ScenarioInsuranceImpactResponse:
    """
    Model insurance portfolio impact of specified scenarios.

    Estimates claims impact, premium adjustments, and coverage implications
    for given scenario and portfolio combinations.

    Args:
        api_key: API key for authentication (injected via header)
        scenario_id: ID of the scenario to model
        portfolio_ids: List of portfolio IDs to assess

    Returns:
        ScenarioInsuranceImpactResponse with impact modeling

    Raises:
        HTTPException: If validation fails
    """
    try:
        impacts = []

        for port_id in portfolio_ids:
            if port_id not in portfolios_db:
                logger.warning(f"Portfolio {port_id} not found")
                raise HTTPException(status_code=400, detail=f"Portfolio {port_id} not found")

            portfolio = portfolios_db[port_id]

            # Scenario impact factors (simplified)
            exposure_impact = 1.2  # 20% increase in exposure
            severity_factor = 0.8  # 80% severity multiplier

            # Estimate losses
            estimated_loss_usd = portfolio["total_insured_value"] * exposure_impact * severity_factor * 0.15

            # Claims impact
            expected_claims_increase = estimated_loss_usd * 0.75

            # Premium adjustment
            premium_adjustment = estimated_loss_usd / portfolio["total_insured_value"]

            impacts.append(
                {
                    "portfolio_id": port_id,
                    "portfolio_name": portfolio["portfolio_name"],
                    "scenario_id": scenario_id,
                    "estimated_loss_usd": round(estimated_loss_usd, 0),
                    "expected_claims_increase_usd": round(expected_claims_increase, 0),
                    "estimated_premium_adjustment": round(premium_adjustment, 4),
                    "coverage_adequacy": "adequate"
                    if estimated_loss_usd < portfolio["total_insured_value"] * 0.3
                    else "marginal"
                    if estimated_loss_usd < portfolio["total_insured_value"] * 0.6
                    else "inadequate",
                }
            )

        total_impact = sum(imp["estimated_loss_usd"] for imp in impacts)

        logger.info(f"Modeled scenario {scenario_id} impact on {len(impacts)} portfolios")

        return ScenarioInsuranceImpactResponse(
            portfolio_impacts=impacts,
            total_estimated_impact_usd=round(total_impact, 0),
            scenario_id=scenario_id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error modeling scenario impact: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to model scenario impact")
