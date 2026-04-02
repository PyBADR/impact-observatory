"""
Decision Intelligence API — Structured Decision Output Contract
Every response answers: What happened? Impact? Affected? Risk? Action?

This module provides FastAPI endpoints for:
- Propagation analysis
- Scenario evaluation
- Monte Carlo simulations
- Decision generation and explainability
- Insurance impact assessment
- Composite risk scoring
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from enum import Enum

from app.api.auth import api_key_auth
from app.api.models import (
    DecisionOutputResponse,
    DecisionOutputContract,
    BilingualTextModel,
    ConfidenceBreakdown,
    WeightConfig,
    Explanation,
    InsuranceImpactModel,
    ExplanationResponse,
    RecommendationResponse,
)

router = APIRouter(prefix="/api/v1", tags=["decision-intelligence"])
logger = logging.getLogger(__name__)


# ── Request/Response Models ──

class ShockInput(BaseModel):
    """Input specification for a shock event."""
    nodeId: str = Field(..., description="Node ID to apply shock to")
    impact: float = Field(ge=-1.0, le=1.0, description="Shock impact magnitude")


class PropagationRequest(BaseModel):
    """Request for propagation analysis."""
    shocks: List[ShockInput]
    max_iterations: int = Field(default=6, ge=1, le=20)
    lang: str = Field(default="ar", pattern="^(ar|en)$")


class ScenarioRequest(BaseModel):
    """Request for scenario evaluation."""
    scenario_id: str = Field(..., description="Scenario identifier")
    shocks: List[ShockInput]
    severity: float = Field(default=0.7, ge=0.0, le=1.0, description="Shock severity 0-1")
    lang: str = Field(default="ar", pattern="^(ar|en)$")
    max_iterations: int = Field(default=6, ge=1, le=20)


class MonteCarloRequest(BaseModel):
    """Request for Monte Carlo simulation."""
    shocks: List[ShockInput]
    runs: int = Field(default=500, ge=10, le=10000, description="Number of simulation runs")
    severity: float = Field(default=0.7, ge=0.0, le=1.0)
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    lang: str = Field(default="ar", pattern="^(ar|en)$")


class CompositeScoreRequest(BaseModel):
    """Request for composite risk score computation."""
    shocks: List[ShockInput]
    scenario_id: str = Field(default="hormuz_closure", description="Scenario context")
    severity: float = Field(default=0.7, ge=0.0, le=1.0)


class InsuranceExposureRequest(BaseModel):
    """Request for portfolio exposure analysis."""
    policies: List[Dict[str, Any]] = Field(..., description="List of insurance policies")


# ── Endpoints ──

@router.post("/propagation/run")
async def run_propagation_endpoint(
    req: PropagationRequest,
    api_key: str = Depends(api_key_auth)
) -> Dict[str, Any]:
    """
    Run discrete dynamic propagation on GCC reality graph.
    
    Computes cascading impacts through the knowledge graph given initial shocks.
    Uses the mathematical model from propagation_engine.py with tolerance < 0.001.
    
    Args:
        req: PropagationRequest with shocks and parameters
        api_key: API key authentication
        
    Returns:
        Propagation result with node impacts, affected sectors, energy metrics
    """
    try:
        from app.intelligence.engines.propagation_engine import run_propagation, result_to_dict
        
        nodes, edges = _get_graph_data()
        shocks = [{"nodeId": s.nodeId, "impact": s.impact} for s in req.shocks]
        result = run_propagation(nodes, edges, shocks, req.max_iterations)
        
        logger.info(f"Propagation complete: {len(result.affected_nodes)} nodes affected, depth={result.propagation_depth}")
        return {"status": "success", "data": result_to_dict(result)}
        
    except ImportError as e:
        logger.error(f"Intelligence module import error: {str(e)}")
        raise HTTPException(status_code=503, detail="Intelligence engine unavailable")
    except Exception as e:
        logger.error(f"Propagation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Propagation failed: {str(e)}")


@router.post("/scenario/run")
async def run_scenario_endpoint(
    req: ScenarioRequest,
    api_key: str = Depends(api_key_auth)
) -> Dict[str, Any]:
    """
    Run complete scenario: propagation + engine + decision.
    
    Full pipeline from shock injection through decision generation.
    Answers: What happened? What is the impact? What is affected? 
    How big is the risk? What is the recommended action?
    
    Args:
        req: ScenarioRequest with scenario ID, shocks, severity
        api_key: API key authentication
        
    Returns:
        Complete scenario result with propagation, engine output, and decision
    """
    try:
        from app.intelligence.engines.propagation_engine import run_propagation, result_to_dict as prop_to_dict
        from app.intelligence.engines.scenario_engines import get_scenario_engine, result_to_dict as engine_to_dict
        from app.intelligence.engines.decision_engine import compute_decision, result_to_dict as decision_to_dict
        
        nodes, edges = _get_graph_data()
        shocks = [{"nodeId": s.nodeId, "impact": s.impact} for s in req.shocks]
        
        # Step 1: Propagation
        logger.info(f"Scenario {req.scenario_id}: Running propagation with {len(shocks)} shocks")
        prop_result = run_propagation(nodes, edges, shocks, req.max_iterations)
        
        # Step 2: Scenario engine
        engine = get_scenario_engine(req.scenario_id)
        engine_result = engine["compute"](prop_result.node_impacts, req.severity)
        
        # Step 3: Decision
        scientist_state = _build_scientist_state(prop_result, engine_result, req.severity)
        decision = compute_decision(prop_result, engine_result, scientist_state, req.scenario_id)
        
        # Step 4: Build structured output contract
        contract = _build_output_contract(req.scenario_id, prop_result, engine_result, decision)
        
        logger.info(f"Scenario {req.scenario_id} complete: risk_score={contract.risk_score:.1f}, system_stress={contract.system_stress}")
        
        return {
            "status": "success",
            "contract": contract.dict(),
            "propagation": prop_to_dict(prop_result),
            "engine": engine_to_dict(engine_result) if hasattr(engine_result, 'engine_id') else engine_result,
            "decision": decision_to_dict(decision),
        }
        
    except ImportError as e:
        logger.error(f"Intelligence module import error: {str(e)}")
        raise HTTPException(status_code=503, detail="Intelligence engine unavailable")
    except Exception as e:
        logger.error(f"Scenario execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Scenario failed: {str(e)}")


@router.post("/simulation/monte-carlo")
async def run_monte_carlo_endpoint(
    req: MonteCarloRequest,
    api_key: str = Depends(api_key_auth)
) -> Dict[str, Any]:
    """
    Run Monte Carlo simulation with seeded reproducibility.
    
    Executes multiple stochastic propagation runs to assess uncertainty
    in impact predictions. Useful for risk quantification and confidence intervals.
    
    Args:
        req: MonteCarloRequest with shocks, run count, optional seed
        api_key: API key authentication
        
    Returns:
        Distribution of outcomes across all runs
    """
    try:
        from app.intelligence.engines.monte_carlo import run_monte_carlo, result_to_dict, MonteCarloOptions
        
        nodes, edges = _get_graph_data()
        shocks = [{"nodeId": s.nodeId, "impact": s.impact} for s in req.shocks]
        options = MonteCarloOptions(runs=req.runs, seed=req.seed)
        
        logger.info(f"Monte Carlo: {req.runs} runs, seed={req.seed}, {len(shocks)} shocks")
        result = run_monte_carlo(nodes, edges, shocks, options)
        
        return {"status": "success", "data": result_to_dict(result)}
        
    except ImportError as e:
        logger.error(f"Monte Carlo module unavailable: {str(e)}")
        raise HTTPException(status_code=503, detail="Monte Carlo engine unavailable")
    except Exception as e:
        logger.error(f"Monte Carlo execution error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Monte Carlo failed: {str(e)}")


@router.post("/decision/generate")
async def generate_decision_endpoint(
    req: ScenarioRequest,
    api_key: str = Depends(api_key_auth)
) -> Dict[str, Any]:
    """
    Generate decision recommendations from scenario.
    
    Produces decision output contract with structured answers to:
    - What happened? (event)
    - What is the impact? (economic_impact_estimate, insurance_impact)
    - What is affected? (affected_airports, affected_ports, affected_routes)
    - How big is the risk? (risk_score, disruption_score)
    - What is the recommended action? (recommended_action)
    
    Args:
        req: ScenarioRequest with scenario and shocks
        api_key: API key authentication
        
    Returns:
        DecisionOutputContract in Master Prompt format
    """
    try:
        from app.intelligence.engines.propagation_engine import run_propagation
        from app.intelligence.engines.scenario_engines import get_scenario_engine
        from app.intelligence.engines.decision_engine import compute_decision, result_to_dict
        
        nodes, edges = _get_graph_data()
        shocks = [{"nodeId": s.nodeId, "impact": s.impact} for s in req.shocks]
        prop_result = run_propagation(nodes, edges, shocks, req.max_iterations)
        engine = get_scenario_engine(req.scenario_id)
        engine_result = engine["compute"](prop_result.node_impacts, req.severity)
        scientist_state = _build_scientist_state(prop_result, engine_result, req.severity)
        decision = compute_decision(prop_result, engine_result, scientist_state, req.scenario_id)
        
        logger.info(f"Decision generated for {req.scenario_id}: urgency_level={decision.urgency_level}")
        return {"status": "success", "data": result_to_dict(decision)}
        
    except Exception as e:
        logger.error(f"Decision generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Decision generation failed: {str(e)}")


@router.get("/scenario/templates")
async def list_scenario_templates(
    api_key: str = Depends(api_key_auth)
) -> Dict[str, Any]:
    """
    List all available scenario engine templates.
    
    Returns:
        Available scenarios with IDs, labels in EN/AR
    """
    try:
        from app.intelligence.engines.scenario_engines import SCENARIO_ENGINES
        
        templates = []
        for eid, engine in SCENARIO_ENGINES.items():
            if isinstance(engine, dict):
                templates.append({
                    "id": eid,
                    "label": engine.get("label", eid),
                    "labelAr": engine.get("label_ar", ""),
                    "chainLabel": engine.get("chain_label", ""),
                })
            else:
                templates.append({
                    "id": eid,
                    "label": getattr(engine, 'label', eid),
                    "labelAr": getattr(engine, 'label_ar', ''),
                    "chainLabel": getattr(engine, 'chain_label', ''),
                })
        
        logger.info(f"Listed {len(templates)} scenario templates")
        return {"status": "success", "templates": templates, "count": len(templates)}
        
    except Exception as e:
        logger.error(f"Template listing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to list templates")


@router.post("/scores/composite")
async def composite_score_endpoint(
    req: CompositeScoreRequest,
    api_key: str = Depends(api_key_auth)
) -> Dict[str, Any]:
    """
    Compute composite risk scores: exposure, disruption, confidence, base premium.
    
    Produces comprehensive risk assessment combining multiple dimensions.
    Formula: base_premium = exposure_score * disruption_score * temporal_persistence
    
    Args:
        req: CompositeScoreRequest with shocks and scenario
        api_key: API key authentication
        
    Returns:
        Composite scores with component breakdown
    """
    try:
        from app.intelligence.engines.propagation_engine import run_propagation
        from app.intelligence.engines.scenario_engines import get_scenario_engine
        from app.intelligence.math.exposure import compute_sector_exposure
        from app.intelligence.math.disruption import compute_disruption_index
        from app.intelligence.math.confidence import compute_model_confidence
        import numpy as np
        
        nodes, edges = _get_graph_data()
        shocks = [{"nodeId": s.nodeId, "impact": s.impact} for s in req.shocks]
        prop_result = run_propagation(nodes, edges, shocks, 6)
        
        # Sector impacts
        sector_impacts = {}
        for s in prop_result.affected_sectors:
            sector_impacts[s.sector] = s.avg_impact
        
        exposure = compute_sector_exposure(sector_impacts)
        affected_count = sum(1 for v in prop_result.node_impacts.values() if abs(v) > 0.01)
        disruption = compute_disruption_index(affected_count, len(nodes), req.severity, 30)
        confidence = compute_model_confidence(prop_result.confidence)
        
        # Base premium = exposure * disruption * temporal_persistence
        temporal = float(np.exp(-0.02 * 30))
        base_premium = exposure["total"] * disruption["score"] * temporal
        
        logger.info(f"Composite score: exposure={exposure['total']:.3f}, disruption={disruption['score']:.3f}, premium=${base_premium:.2f}M")
        
        return {
            "status": "success",
            "data": {
                "exposure_score": exposure,
                "disruption_score": disruption,
                "temporal_persistence": temporal,
                "base_premium": base_premium,
                "confidence": confidence,
                "explanation": {
                    "formula": "base_premium = exposure_score * disruption_score * temporal_persistence",
                    "components": {
                        "exposure": exposure["total"],
                        "disruption": disruption["score"],
                        "temporal": temporal
                    }
                }
            }
        }
        
    except ImportError as e:
        logger.error(f"Math module unavailable: {str(e)}")
        raise HTTPException(status_code=503, detail="Scoring engine unavailable")
    except Exception as e:
        logger.error(f"Score computation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Score computation failed: {str(e)}")


@router.post("/insurance/exposure")
async def insurance_exposure_endpoint(
    req: InsuranceExposureRequest,
    api_key: str = Depends(api_key_auth)
) -> Dict[str, Any]:
    """
    Compute portfolio exposure with GCC zone factors.
    
    Assesses total exposure of insurance portfolio to regional risks.
    
    Args:
        req: InsuranceExposureRequest with policies
        api_key: API key authentication
        
    Returns:
        Portfolio exposure metrics
    """
    try:
        from app.intelligence.insurance_intelligence.portfolio_exposure import compute_portfolio_exposure
        
        logger.info(f"Computing exposure for {len(req.policies)} policies")
        result = compute_portfolio_exposure(req.policies)
        
        return {"status": "success", "data": result}
        
    except ImportError as e:
        logger.error(f"Insurance module unavailable: {str(e)}")
        raise HTTPException(status_code=503, detail="Insurance intelligence unavailable")
    except Exception as e:
        logger.error(f"Exposure computation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Exposure computation failed: {str(e)}")


@router.post("/insurance/claims-surge")
async def insurance_claims_surge_endpoint(
    req: ScenarioRequest,
    api_key: str = Depends(api_key_auth)
) -> Dict[str, Any]:
    """
    Compute claims surge from scenario.
    
    Projects expected claims surge in event of scenario materialization.
    
    Args:
        req: ScenarioRequest with scenario and shocks
        api_key: API key authentication
        
    Returns:
        Claims surge projection
    """
    try:
        from app.intelligence.insurance_intelligence.claims_surge import compute_gcc_claims_surge
        from app.intelligence.engines.propagation_engine import run_propagation
        
        nodes, edges = _get_graph_data()
        shocks = [{"nodeId": s.nodeId, "impact": s.impact} for s in req.shocks]
        prop_result = run_propagation(nodes, edges, shocks, req.max_iterations)
        affected_sectors = [s.sector for s in prop_result.affected_sectors]
        
        logger.info(f"Computing claims surge for {len(affected_sectors)} sectors at severity={req.severity}")
        result = compute_gcc_claims_surge(req.severity, affected_sectors)
        
        return {"status": "success", "data": result}
        
    except ImportError as e:
        logger.error(f"Insurance module unavailable: {str(e)}")
        raise HTTPException(status_code=503, detail="Claims surge engine unavailable")
    except Exception as e:
        logger.error(f"Claims surge computation error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Claims surge failed: {str(e)}")


@router.post("/insurance/underwriting-watch")
async def underwriting_watch_endpoint(
    req: ScenarioRequest,
    api_key: str = Depends(api_key_auth)
) -> Dict[str, Any]:
    """
    Evaluate underwriting watch triggers.
    
    Assesses whether scenario triggers underwriting restrictions or monitoring.
    
    Args:
        req: ScenarioRequest with scenario evaluation parameters
        api_key: API key authentication
        
    Returns:
        Underwriting watch status and triggers
    """
    try:
        from app.intelligence.insurance_intelligence.underwriting_watch import evaluate_underwriting_watch
        from app.intelligence.engines.propagation_engine import run_propagation
        from app.intelligence.engines.gcc_constants import BASES
        
        nodes, edges = _get_graph_data()
        shocks = [{"nodeId": s.nodeId, "impact": s.impact} for s in req.shocks]
        prop_result = run_propagation(nodes, edges, shocks, req.max_iterations)
        
        total_insured = BASES["insurancePremium"] * 10  # approximate
        portfolio_exposure = prop_result.total_loss * 0.3
        claims_mult = 1 + req.severity * 1.5
        risk_score = min(1.0, prop_result.system_energy / 15)
        concentration = len(prop_result.affected_sectors) / 5
        
        logger.info(f"Underwriting watch: risk_score={risk_score:.3f}, concentration={concentration:.3f}")
        result = evaluate_underwriting_watch(portfolio_exposure, total_insured, claims_mult, risk_score, concentration)
        
        return {"status": "success", "data": result}
        
    except ImportError as e:
        logger.error(f"Underwriting module unavailable: {str(e)}")
        raise HTTPException(status_code=503, detail="Underwriting engine unavailable")
    except Exception as e:
        logger.error(f"Underwriting watch error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Underwriting watch failed: {str(e)}")


@router.post("/insurance/severity-projection")
async def severity_projection_endpoint(
    req: ScenarioRequest,
    api_key: str = Depends(api_key_auth)
) -> Dict[str, Any]:
    """
    Project severity over time horizon.
    
    Models how scenario impact evolves temporally.
    
    Args:
        req: ScenarioRequest with scenario parameters
        api_key: API key authentication
        
    Returns:
        Temporal severity projection
    """
    try:
        from app.intelligence.insurance_intelligence.severity_projection import compute_severity_projection
        from app.intelligence.engines.propagation_engine import run_propagation
        
        nodes, edges = _get_graph_data()
        shocks = [{"nodeId": s.nodeId, "impact": s.impact} for s in req.shocks]
        prop_result = run_propagation(nodes, edges, shocks, req.max_iterations)
        
        exposure = prop_result.total_loss / 2100  # normalize to GDP fraction
        intensity = req.severity
        concentration = len(prop_result.affected_sectors) / 5
        
        logger.info(f"Severity projection: exposure={exposure:.3f}, intensity={intensity:.3f}")
        result = compute_severity_projection(exposure, intensity, concentration)
        
        return {"status": "success", "data": result}
        
    except ImportError as e:
        logger.error(f"Severity module unavailable: {str(e)}")
        raise HTTPException(status_code=503, detail="Severity engine unavailable")
    except Exception as e:
        logger.error(f"Severity projection error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Severity projection failed: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "engine": "impact-observatory-decision-intelligence",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# ── Legacy endpoints (preserved from existing decision.py) ──

_decisions_db = {
    "DEC001": {
        "id": "DEC001",
        "scenario_id": "SCEN001",
        "decision_type": "supply_chain_mitigation",
        "decision": "Activate alternative suppliers in East Asia",
        "confidence": 0.87,
        "timestamp": datetime(2026, 3, 28, 14, 30),
        "reasoning": [
            "Primary supplier at 85% risk level",
            "Inventory buffer at 2.1 weeks",
            "Alternative suppliers available with 3-day lead time",
        ],
        "recommended_actions": [
            "Shift 30% volume to Thailand supplier",
            "Increase safety stock by 15%",
            "Establish backup logistics contract",
        ],
        "risk_reduction": 0.42,
        "implementation_timeline_days": 5,
    },
}

_explanations_db = {
    "DEC001": {
        "decision_id": "DEC001",
        "factors": [
            {"factor": "Supplier Risk", "weight": 0.35, "value": 0.85},
            {"factor": "Inventory Position", "weight": 0.25, "value": 0.42},
            {"factor": "Alternative Availability", "weight": 0.20, "value": 0.88},
            {"factor": "Cost Impact", "weight": 0.15, "value": 0.30},
            {"factor": "Lead Time", "weight": 0.05, "value": 0.95},
        ],
        "key_constraints": ["Budget allocation", "Customer commitments"],
        "model_confidence": 0.87,
    },
}

_recommendations_db = {
    "DEC001": [
        {
            "rank": 1,
            "title": "Diversify supplier base",
            "description": "Reduce single-supplier dependency from 60% to 40%",
            "priority": "high",
            "timeline_days": 30,
            "estimated_cost_usd": 500000,
        },
    ],
}


@router.post(
    "/decisions/output",
    response_model=DecisionOutputContract,
    tags=["Decisions"],
    summary="Generate decision output",
)
async def generate_decision(
    api_key: str = Depends(api_key_auth),
    scenario_id: str = Query(..., description="Scenario ID to generate decision for"),
    decision_context: str = Query(
        "supply_chain_risk", description="Context for decision generation"
    ),
) -> DecisionOutputContract:
    """
    Generate decision output for a given scenario (legacy endpoint).
    
    Creates decision recommendations based on scenario analysis.
    Returns DecisionOutputContract with all required fields.
    """
    try:
        decision_options = list(_decisions_db.values())
        selected_decision = decision_options[hash(scenario_id) % len(decision_options)]
        
        stress_levels = {
            "supply_chain_mitigation": "elevated",
            "insurance_adjustment": "high",
            "demand_adjustment": "critical",
        }
        system_stress = stress_levels.get(selected_decision["decision_type"], "nominal")
        
        timeline_to_horizon = {
            2: "immediate",
            5: "short-term",
            14: "medium-term",
            30: "long-term",
        }
        timeline = selected_decision["implementation_timeline_days"]
        scenario_horizon = "long-term"
        for days, horizon in sorted(timeline_to_horizon.items()):
            if timeline <= days:
                scenario_horizon = horizon
                break
        
        logger.info(f"Generated decision for {scenario_id}")
        
        return DecisionOutputContract(
            event=BilingualTextModel(
                en=selected_decision["decision"],
                ar=f"قرار: {selected_decision['decision']}"
            ),
            timestamp=selected_decision["timestamp"],
            risk_score=min(85 + (selected_decision["confidence"] * 10), 100),
            disruption_score=min(75 + (selected_decision["risk_reduction"] * 20), 100),
            confidence_score=selected_decision["confidence"],
            system_stress=system_stress,
            affected_airports=[],
            affected_ports=[],
            affected_corridors=[],
            affected_routes=[],
            economic_impact_estimate=2500000.0,
            insurance_impact=InsuranceImpactModel(
                exposure_score=72.5,
                claims_surge_potential=0.45,
                underwriting_class="restricted",
                expected_claims_uplift=1.2
            ),
            recommended_action=BilingualTextModel(
                en=selected_decision["decision"],
                ar=f"الإجراء الموصى به: {selected_decision['decision']}"
            ),
            scenario_horizon=scenario_horizon,
            explanation=Explanation(
                top_causal_factors=selected_decision["reasoning"][:5],
                propagation_path=[
                    {
                        "stage": i + 1,
                        "entity_type": "supply_chain_node",
                        "impact_level": 0.7 - (i * 0.15)
                    }
                    for i in range(3)
                ],
                confidence_breakdown=ConfidenceBreakdown(
                    simulation_confidence=0.88,
                    economic_confidence=0.82,
                    insurance_confidence=0.79,
                    recommendation_confidence=selected_decision["confidence"]
                ),
                weight_config_used=WeightConfig(
                    geopolitical_weight=0.35,
                    infrastructure_weight=0.25,
                    economic_weight=0.25,
                    insurance_weight=0.15
                )
            )
        )
    except Exception as e:
        logger.error(f"Decision generation error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate decision")


@router.get(
    "/decisions/latest",
    response_model=DecisionOutputResponse,
    tags=["Decisions"],
    summary="Get latest decision",
)
async def get_latest_decision(
    api_key: str = Depends(api_key_auth),
    scenario_id: Optional[str] = Query(None, description="Filter by scenario ID"),
) -> DecisionOutputResponse:
    """Get latest decision (legacy endpoint)."""
    try:
        decisions = list(_decisions_db.values())
        
        if scenario_id:
            decisions = [d for d in decisions if d["scenario_id"] == scenario_id]
        
        if not decisions:
            logger.warning(f"No decisions found for scenario {scenario_id}")
            raise HTTPException(status_code=404, detail="No decisions found")
        
        latest = max(decisions, key=lambda d: d["timestamp"])
        logger.info(f"Retrieved latest decision {latest['id']}")
        
        return DecisionOutputResponse(
            decision_id=latest["id"],
            scenario_id=latest["scenario_id"],
            decision_type=latest["decision_type"],
            decision=latest["decision"],
            confidence=latest["confidence"],
            timestamp=latest["timestamp"],
            reasoning=latest["reasoning"],
            recommended_actions=latest["recommended_actions"],
            risk_reduction_potential=latest["risk_reduction"],
            implementation_timeline_days=latest["implementation_timeline_days"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving latest decision: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to retrieve decision")


@router.post(
    "/decisions/explain",
    response_model=ExplanationResponse,
    tags=["Decisions"],
    summary="Explain decision reasoning",
)
async def explain_decision(
    api_key: str = Depends(api_key_auth),
    decision_id: str = Query(..., description="Decision ID to explain"),
) -> ExplanationResponse:
    """Provide detailed explanation of decision reasoning (legacy endpoint)."""
    try:
        if decision_id not in _explanations_db:
            logger.warning(f"Explanation not found for decision {decision_id}")
            raise HTTPException(status_code=404, detail="Decision explanation not found")
        
        explanation = _explanations_db[decision_id]
        decision = _decisions_db[decision_id]
        
        logger.info(f"Generated explanation for decision {decision_id}")
        
        return ExplanationResponse(
            decision_id=decision_id,
            summary=decision["decision"],
            factors=explanation["factors"],
            key_constraints=explanation["key_constraints"],
            model_confidence=explanation["model_confidence"],
            supporting_evidence=decision["reasoning"],
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining decision: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to explain decision")


@router.post(
    "/decisions/recommend",
    response_model=RecommendationResponse,
    tags=["Decisions"],
    summary="Get decision recommendations",
)
async def get_recommendations(
    api_key: str = Depends(api_key_auth),
    decision_id: str = Query(..., description="Decision ID to get recommendations for"),
    include_costs: bool = Query(True, description="Include cost estimates"),
) -> RecommendationResponse:
    """Get prioritized recommendations for implementing a decision (legacy endpoint)."""
    try:
        if decision_id not in _recommendations_db:
            logger.warning(f"Recommendations not found for decision {decision_id}")
            raise HTTPException(status_code=404, detail="Decision recommendations not found")
        
        decision = _decisions_db[decision_id]
        recs = _recommendations_db[decision_id]
        
        recommendations = []
        for rec in recs:
            rec_item = {
                "rank": rec["rank"],
                "title": rec["title"],
                "description": rec["description"],
                "priority": rec["priority"],
                "timeline_days": rec["timeline_days"],
            }
            if include_costs:
                rec_item["estimated_cost_usd"] = rec["estimated_cost_usd"]
            recommendations.append(rec_item)
        
        logger.info(f"Generated {len(recommendations)} recommendations for decision {decision_id}")
        
        return RecommendationResponse(
            decision_id=decision_id,
            decision_summary=decision["decision"],
            recommendations=recommendations,
            total_timeline_days=max(r["timeline_days"] for r in recommendations),
            total_estimated_cost_usd=(
                sum(r["estimated_cost_usd"] for r in recs) if include_costs else None
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


# ── Internal Helpers ──

_cached_graph = None


def _get_graph_data() -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Load graph nodes and edges.
    
    In production, loads from PostgreSQL. Fallback to in-memory test graph
    and optional JSON export from gcc-knowledge-graph package.
    """
    global _cached_graph
    if _cached_graph is not None:
        return _cached_graph
    
    import json
    import os
    
    # Try loading from gcc-knowledge-graph package JSON export
    graph_path = os.path.join(
        os.path.dirname(__file__),
        '..', '..', '..', 'packages', '@impact-observatory', 'gcc-knowledge-graph', 'data', 'gcc_graph.json'
    )
    
    if os.path.exists(graph_path):
        try:
            with open(graph_path) as f:
                data = json.load(f)
                _cached_graph = (data["nodes"], data["edges"])
                logger.info(f"Loaded graph from {graph_path}")
                return _cached_graph
        except Exception as e:
            logger.warning(f"Failed to load graph from {graph_path}: {e}")
    
    # Fallback: minimal test graph
    nodes = [
        {"id": "geo_hormuz", "label": "Strait of Hormuz", "labelAr": "مضيق هرمز", "layer": "geography", "sensitivity": 0.95, "damping_factor": 0.02, "weight": 0.95, "value": 1000},
        {"id": "eco_oil", "label": "Oil Revenue", "labelAr": "إيرادات النفط", "layer": "economy", "sensitivity": 0.85, "damping_factor": 0.05, "weight": 0.9, "value": 540},
        {"id": "eco_shipping", "label": "Shipping", "labelAr": "الشحن البحري", "layer": "economy", "sensitivity": 0.75, "damping_factor": 0.05, "weight": 0.8, "value": 12},
        {"id": "fin_insurers", "label": "Insurance Market", "labelAr": "سوق التأمين", "layer": "finance", "sensitivity": 0.7, "damping_factor": 0.05, "weight": 0.75, "value": 28},
        {"id": "eco_aviation", "label": "Aviation", "labelAr": "الطيران", "layer": "economy", "sensitivity": 0.65, "damping_factor": 0.05, "weight": 0.7, "value": 42},
        {"id": "eco_tourism", "label": "Tourism", "labelAr": "السياحة", "layer": "economy", "sensitivity": 0.6, "damping_factor": 0.08, "weight": 0.65, "value": 85},
        {"id": "eco_gdp", "label": "GCC GDP", "labelAr": "الناتج المحلي الخليجي", "layer": "economy", "sensitivity": 0.5, "damping_factor": 0.1, "weight": 0.85, "value": 2100},
    ]
    edges = [
        {"id": "e1", "source": "geo_hormuz", "target": "eco_oil", "weight": 0.85, "polarity": -1, "label": "Oil disruption", "labelAr": "تعطل النفط"},
        {"id": "e2", "source": "geo_hormuz", "target": "eco_shipping", "weight": 0.75, "polarity": -1, "label": "Shipping disruption", "labelAr": "تعطل الشحن"},
        {"id": "e3", "source": "eco_shipping", "target": "fin_insurers", "weight": 0.6, "polarity": 1, "label": "Insurance demand", "labelAr": "طلب التأمين"},
        {"id": "e4", "source": "geo_hormuz", "target": "eco_aviation", "weight": 0.5, "polarity": -1, "label": "Aviation impact", "labelAr": "تأثير الطيران"},
        {"id": "e5", "source": "eco_aviation", "target": "eco_tourism", "weight": 0.55, "polarity": 1, "label": "Tourism link", "labelAr": "ربط السياحة"},
        {"id": "e6", "source": "eco_oil", "target": "eco_gdp", "weight": 0.7, "polarity": 1, "label": "GDP contribution", "labelAr": "مساهمة الناتج"},
        {"id": "e7", "source": "eco_tourism", "target": "eco_gdp", "weight": 0.4, "polarity": 1, "label": "Tourism GDP", "labelAr": "سياحة الناتج"},
    ]
    
    _cached_graph = (nodes, edges)
    logger.info("Using fallback in-memory test graph")
    return _cached_graph


def _build_scientist_state(prop_result: Any, engine_result: Any, severity: float) -> Dict[str, Any]:
    """Build ScientistState from propagation + engine results."""
    total_exposure = (
        engine_result.total_exposure
        if hasattr(engine_result, "total_exposure")
        else engine_result.get("totalExposure", 0)
    )
    dominant = prop_result.affected_sectors[0] if prop_result.affected_sectors else None
    
    shock_class = (
        "critical"
        if severity > 0.7
        else "severe"
        if severity > 0.5
        else "moderate"
        if severity > 0.3
        else "low"
    )
    stage = (
        "saturated"
        if prop_result.propagation_depth >= 5
        else "cascading"
        if prop_result.propagation_depth > 2
        else "initial"
    )
    
    return {
        "energy": prop_result.system_energy,
        "confidence": prop_result.confidence,
        "uncertainty": 1 - prop_result.confidence,
        "regionalStress": min(1.0, prop_result.system_energy / 10),
        "shockClass": shock_class,
        "stage": stage,
        "propagationDepth": prop_result.propagation_depth,
        "totalExposure": total_exposure,
        "dominantSector": dominant,
    }


def _build_output_contract(
    scenario_id: str, prop_result: Any, engine_result: Any, decision: Any
) -> DecisionOutputContract:
    """Build the mandatory structured decision output contract."""
    affected_airports = [
        n
        for n, v in prop_result.node_impacts.items()
        if abs(v) > 0.01 and ("inf_" in n and ("airport" in n or "jed" in n or "dxb" in n or "ruh" in n))
    ]
    affected_ports = [
        n
        for n, v in prop_result.node_impacts.items()
        if abs(v) > 0.01 and ("port" in n or "jebel" in n or "dammam" in n)
    ]
    affected_routes = [
        n
        for n, v in prop_result.node_impacts.items()
        if abs(v) > 0.01 and ("shipping" in n or "aviation" in n or "hormuz" in n)
    ]
    
    total_exposure = (
        engine_result.total_exposure
        if hasattr(engine_result, "total_exposure")
        else engine_result.get("totalExposure", 0)
    )
    
    top_action = decision.recommended_actions[0] if decision.recommended_actions else None
    
    return DecisionOutputContract(
        event=BilingualTextModel(
            en=f"Scenario {scenario_id} triggered",
            ar=f"تم تشغيل السيناريو {scenario_id}"
        ),
        timestamp=datetime.utcnow(),
        risk_score=min(decision.decision_pressure_score * 100, 100),
        disruption_score=min(len(prop_result.affected_sectors) * 15, 100),
        confidence_score=prop_result.confidence,
        system_stress="critical" if decision.decision_pressure_score > 0.7 else "high" if decision.decision_pressure_score > 0.5 else "elevated",
        affected_airports=affected_airports,
        affected_ports=affected_ports,
        affected_corridors=[],
        affected_routes=affected_routes,
        economic_impact_estimate=total_exposure * 1e9,
        insurance_impact=InsuranceImpactModel(
            exposure_score=min(decision.decision_pressure_score * 100, 100),
            claims_surge_potential=min(decision.decision_pressure_score * 1.5, 1.0),
            underwriting_class="critical" if decision.decision_pressure_score > 0.7 else "restricted" if decision.decision_pressure_score > 0.4 else "standard",
            expected_claims_uplift=1 + (decision.decision_pressure_score * 2)
        ),
        recommended_action=BilingualTextModel(
            en=top_action.action if top_action else "Monitor situation",
            ar="مراقبة الحالة" if not top_action else f"إجراء: {top_action.action}"
        ),
        scenario_horizon="short-term" if decision.urgency_level == "critical" else "medium-term" if decision.urgency_level == "high" else "long-term",
        explanation=Explanation(
            top_causal_factors=[
                f"Scenario {scenario_id}",
                f"Severity level {decision.decision_pressure_score:.1%}",
                f"{len(prop_result.affected_sectors)} sectors affected",
                f"System energy {prop_result.system_energy:.2f}",
            ],
            propagation_path=[
                {
                    "stage": i + 1,
                    "entity_type": "supply_chain_node",
                    "impact_level": max(0, 0.8 - (i * 0.15))
                }
                for i in range(min(5, prop_result.propagation_depth))
            ],
            confidence_breakdown=ConfidenceBreakdown(
                simulation_confidence=prop_result.confidence,
                economic_confidence=min(prop_result.confidence + 0.05, 1.0),
                insurance_confidence=max(prop_result.confidence - 0.05, 0.0),
                recommendation_confidence=decision.decision_pressure_score
            ),
            weight_config_used=WeightConfig(
                geopolitical_weight=0.35,
                infrastructure_weight=0.25,
                economic_weight=0.25,
                insurance_weight=0.15
            )
        )
    )
