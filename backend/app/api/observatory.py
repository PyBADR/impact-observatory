"""
Impact Observatory | مرصد الأثر — Unified Observatory API

Core Flow (10 stages):
  Scenario → Physics → Graph Snapshot → Propagation → Financial →
  Sector Risk → Regulatory → Decision → Explanation → Output

This module provides the single entry point for the complete Impact Observatory pipeline.
All financial sector stress modeling, decision analysis, and risk quantification flows
through this unified API. The pipeline orchestrator sequences all 10 stages and
integrates the preserved intelligence engines (propagation, physics, graph) with the
new sector-specific services (financial, banking, insurance, fintech, decision).
"""

from datetime import datetime
from typing import List

from fastapi import APIRouter, HTTPException

from ..schemas.observatory import (
    ScenarioInput,
    ObservatoryOutput,
    LABELS,
    FLOW_STAGES,
)
from ..orchestration.pipeline import run_observatory_pipeline


# Router configuration
router = APIRouter(prefix="/observatory", tags=["Observatory"])


# ============================================================================
# API ENDPOINTS
# ============================================================================

@router.post("/run", response_model=ObservatoryOutput)
async def run_observatory(scenario: ScenarioInput) -> ObservatoryOutput:
    """
    Execute the complete Impact Observatory pipeline (10 stages).

    Orchestrates:
      1. Scenario validation
      2. Physics (system stress via physics_core)
      3. Graph Snapshot (entity/edge capture)
      4. Propagation (discrete dynamic cascade)
      5. Financial impact quantification
      6. Sector risk (banking + insurance + fintech)
      7. Regulatory compliance (PDPL, IFRS 17, Basel III)
      8. Decision optimization (top 3 actions)
      9. Bilingual explainability
      10. Output assembly + SHA-256 audit hash

    Args:
        scenario: Input scenario describing the impact event

    Returns:
        ObservatoryOutput: Complete observatory analysis output

    Raises:
        HTTPException: If a mandatory computation engine fails
    """
    try:
        output, pipeline = run_observatory_pipeline(
            scenario=scenario,
            enable_physics=True,
            enable_propagation=True,
        )
        return output

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Observatory pipeline error: {str(e)}"
        )


@router.post("/run/detailed")
async def run_observatory_detailed(scenario: ScenarioInput) -> dict:
    """
    Execute the pipeline and return output WITH stage-level execution metadata.

    Same as /run but includes pipeline.stage_log showing per-stage status,
    timing, and degradation details. Useful for debugging and observability.
    """
    try:
        output, pipeline = run_observatory_pipeline(
            scenario=scenario,
            enable_physics=True,
            enable_propagation=True,
        )
        return {
            "output": output.model_dump(mode="json"),
            "pipeline": {
                "stages_executed": pipeline.stages_executed,
                "stages_skipped": pipeline.stages_skipped,
                "stage_log": pipeline.stage_log,
                "errors": pipeline.errors,
            },
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Observatory pipeline error: {str(e)}"
        )


@router.get("/labels")
async def get_labels() -> dict:
    """
    Retrieve bilingual field labels for UI rendering.

    Returns a dictionary of field identifiers mapped to English and Arabic
    labels for display in user interfaces supporting both languages.

    Returns:
        dict: Label mappings with "en" and "ar" keys
    """
    return LABELS


@router.get("/flow")
async def get_flow_stages() -> List[dict]:
    """
    Retrieve the Observable pipeline flow stages.

    Returns the sequence of processing stages from event scenario through
    decision actions, each with bilingual labels.

    Returns:
        List[dict]: Flow stages with id, English, and Arabic labels
    """
    return FLOW_STAGES


@router.get("/health")
async def health_check() -> dict:
    """
    Health check endpoint for the Observatory API.

    Returns:
        dict: Service status information
    """
    from ..orchestration.pipeline import PHYSICS_AVAILABLE, PROPAGATION_AVAILABLE

    return {
        "status": "operational",
        "service": "Impact Observatory | مرصد الأثر",
        "version": "1.1.0",
        "timestamp": datetime.utcnow().isoformat(),
        "capabilities": {
            "physics_core": PHYSICS_AVAILABLE,
            "propagation_engine": PROPAGATION_AVAILABLE,
            "financial_engine": True,
            "sector_risk_engines": True,
            "decision_engine": True,
            "explainability_engine": True,
            "audit_service": True,
        },
    }


# ============================================================================
# METADATA ENDPOINTS
# ============================================================================

@router.get("/metadata/schema")
async def get_schema_metadata() -> dict:
    """
    Retrieve schema and domain model metadata.

    Returns information about the ObservatoryOutput schema, field definitions,
    and validation rules.

    Returns:
        dict: Schema metadata including field descriptions and constraints
    """
    return {
        "observatory_output": {
            "description": "Complete Impact Observatory pipeline output (10 stages)",
            "stages": [
                "scenario", "physics", "graph_snapshot", "propagation", "financial",
                "sector_risk", "regulatory", "decision", "explanation", "output",
            ],
            "fields": {
                "scenario": {"type": "ScenarioInput", "stage": 1, "required": True},
                "entities": {"type": "List[Entity]", "stage": 3, "required": False},
                "edges": {"type": "List[Edge]", "stage": 3, "required": False},
                "flow_states": {"type": "List[FlowState]", "stage": 4, "required": False},
                "financial_impact": {"type": "FinancialImpact", "stage": 5, "required": True},
                "banking_stress": {"type": "BankingStress", "stage": 6, "required": True},
                "insurance_stress": {"type": "InsuranceStress", "stage": 6, "required": True},
                "fintech_stress": {"type": "FintechStress", "stage": 6, "required": True},
                "regulatory": {"type": "RegulatoryState", "stage": 7, "required": True},
                "decisions": {"type": "List[DecisionAction]", "stage": 8, "required": True},
                "decision_plan": {"type": "DecisionPlan", "stage": 8, "required": False},
                "explanation": {"type": "ExplanationPack", "stage": 9, "required": False},
                "timestamp": {"type": "datetime", "stage": 10, "required": True},
                "audit_hash": {"type": "str", "stage": 10, "required": True},
                "computed_in_ms": {"type": "float", "stage": 10, "required": True},
            }
        }
    }


@router.get("/metadata/flow")
async def get_flow_metadata() -> dict:
    """
    Retrieve detailed flow pipeline metadata.

    Returns:
        dict: Flow pipeline metadata and stage information
    """
    return {
        "pipeline": "Impact Observatory",
        "pipeline_ar": "مرصد الأثر",
        "flow": FLOW_STAGES,
        "description": "10-stage analytical flow from event scenario through physics, propagation, financial impact, sector risk, regulatory check, to recommended decisions",
        "description_ar": "تدفق تحليلي من 10 مراحل من سيناريو الحدث عبر الفيزياء والانتشار والأثر المالي ومخاطر القطاع والفحص التنظيمي إلى القرارات الموصى بها",
    }


@router.get("/metadata/sectors")
async def get_sector_metadata() -> dict:
    """
    Retrieve sector-specific metadata and model information.

    Returns:
        dict: Sector metadata including stress indicators and models
    """
    return {
        "sectors": {
            "banking": {
                "en": "Banking",
                "ar": "القطاع البنكي",
                "stress_indicators": [
                    "liquidity_gap_usd",
                    "capital_adequacy_ratio",
                    "interbank_rate_spike",
                    "time_to_liquidity_breach_days",
                    "fx_reserve_drawdown_pct"
                ]
            },
            "insurance": {
                "en": "Insurance",
                "ar": "التأمين",
                "stress_indicators": [
                    "claims_surge_pct",
                    "reinsurance_trigger",
                    "combined_ratio",
                    "solvency_margin_pct",
                    "time_to_insolvency_days"
                ]
            },
            "fintech": {
                "en": "Fintech",
                "ar": "الفنتك",
                "stress_indicators": [
                    "payment_failure_rate",
                    "settlement_delay_hours",
                    "gateway_downtime_pct",
                    "digital_banking_disruption"
                ]
            }
        }
    }


# ============================================================================
# VALIDATION ENDPOINTS
# ============================================================================

@router.post("/validate/scenario")
async def validate_scenario(scenario: ScenarioInput) -> dict:
    """
    Validate a scenario input without running the full pipeline.

    Args:
        scenario: Scenario to validate

    Returns:
        dict: Validation result with any errors or warnings
    """
    try:
        return {
            "valid": True,
            "message": "Scenario validation passed",
            "scenario_id": scenario.id,
            "scenario_name": scenario.name,
        }
    except Exception as e:
        return {
            "valid": False,
            "message": str(e),
        }
