"""
Scenario Chain API

FastAPI router for bridging simulation engine output to banking_intelligence contracts.
Exposes three endpoints:
1. POST /banking/chain/from-simulation - accepts sim_result and bridges to full contract chain
2. GET /banking/chain/{run_id} - retrieves stored chain from database
3. POST /banking/chain/from-run/{run_id} - executes simulation and bridges end-to-end
"""

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, status
from pydantic import Field, BaseModel

from src.simulation_schemas import SimulateResponse
from src.banking_intelligence.services.scenario_bridge import (
    bridge_full_chain,
    bridge_to_decision_contract,
    bridge_to_counterfactual,
    bridge_to_propagation_contracts,
    bridge_to_outcome_review,
)
from src.banking_intelligence.schemas.decision_contract import DecisionContract
from src.banking_intelligence.schemas.counterfactual import CounterfactualContract
from src.banking_intelligence.schemas.propagation import PropagationContract
from src.banking_intelligence.schemas.outcome_review import OutcomeReviewContract


router = APIRouter(prefix="/banking/chain", tags=["banking-chain"])


# Request/Response models
class ScenarioChainRequest(BaseModel):
    """Request to bridge a simulation result to banking contracts."""
    run_id: str = Field(..., description="Unique simulation run identifier")
    scenario_id: str = Field(..., description="Scenario identifier")
    sim_result: SimulateResponse = Field(..., description="Simulation engine output")

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "run_20260410_001",
                "scenario_id": "hormuz_chokepoint_disruption",
                "sim_result": {
                    "baseline_urs": 0.42,
                    "unified_risk_score": 0.68,
                    "banking_stress": 0.55,
                    "fintech_stress": 0.48,
                },
            }
        }


class ScenarioChainResponse(BaseModel):
    """Response containing all bridged banking contracts."""
    decision_contract: DecisionContract = Field(..., description="Bridged decision contract")
    counterfactual_contract: CounterfactualContract = Field(
        ..., description="4-branch counterfactual analysis"
    )
    propagation_contracts: list[PropagationContract] = Field(
        ..., description="Propagation pathway contracts"
    )
    outcome_review_contract: OutcomeReviewContract = Field(
        ..., description="4-window outcome review contract"
    )
    metadata: dict[str, Any] = Field(..., description="Bridge operation metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "decision_contract": {...},
                "counterfactual_contract": {...},
                "propagation_contracts": [...],
                "outcome_review_contract": {...},
                "metadata": {
                    "bridged_timestamp": "2026-04-10T14:30:00Z",
                    "run_id": "run_20260410_001",
                    "scenario_id": "hormuz_chokepoint_disruption",
                    "baseline_urs": 0.42,
                    "final_urs": 0.68,
                },
            }
        }


class FromRunRequest(BaseModel):
    """Request to execute simulation and bridge end-to-end."""
    scenario_id: str = Field(
        ..., description="Scenario to simulate (e.g., hormuz_chokepoint_disruption)"
    )
    baseline_urs: float = Field(
        0.25, ge=0.0, le=1.0, description="Baseline unified risk score"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "scenario_id": "hormuz_chokepoint_disruption",
                "baseline_urs": 0.25,
            }
        }


class ChainStorageModel(BaseModel):
    """Internal model for persisting chain in database."""
    run_id: str
    scenario_id: str
    chain_timestamp: datetime
    decision_contract_id: str
    counterfactual_contract_id: str
    propagation_contract_ids: list[str]
    outcome_review_contract_id: str
    baseline_urs: float
    final_urs: float
    financial_impact_usd: float


# In-memory storage (replace with database in production)
_chain_storage: dict[str, dict[str, Any]] = {}


# Auth handled by parent api_v1 router (require_api_key dependency in main.py)


@router.post(
    "/from-simulation",
    response_model=ScenarioChainResponse,
    status_code=status.HTTP_200_OK,
)
async def bridge_from_simulation(
    request: ScenarioChainRequest,
) -> ScenarioChainResponse:
    """
    Bridge a simulation result to banking intelligence contracts.

    Accepts a complete SimulateResponse from the simulation engine and transforms
    it to DecisionContract, CounterfactualContract, PropagationContract list, and
    OutcomeReviewContract. Stores the full chain in the database.

    **Request body:**
    - run_id: unique simulation run identifier
    - scenario_id: scenario name (e.g., hormuz_chokepoint_disruption)
    - sim_result: complete SimulateResponse from simulation engine

    **Response:**
    - decision_contract: formal policy decision with reversibility/feasibility
    - counterfactual_contract: 4-branch (do_nothing, recommended, delayed, alternative)
    - propagation_contracts: list of entity-to-entity transfer pathways
    - outcome_review_contract: 4-window post-decision review schedule
    - metadata: bridge operation summary (timestamps, URS deltas, etc.)

    **Errors:**
    - 400 Bad Request: missing critical simulation fields
    - 401 Unauthorized: invalid or missing API key
    - 422 Unprocessable Entity: invalid request schema
    """
    try:
        # Bridge full chain
        chain_dict = bridge_full_chain(
            request.run_id,
            request.scenario_id,
            request.sim_result,
        )

        # Store in database
        _chain_storage[request.run_id] = {
            "timestamp": datetime.utcnow(),
            "scenario_id": request.scenario_id,
            "chain": chain_dict,
        }

        # Return response
        return ScenarioChainResponse(
            decision_contract=chain_dict["decision_contract"],
            counterfactual_contract=chain_dict["counterfactual_contract"],
            propagation_contracts=chain_dict["propagation_contracts"],
            outcome_review_contract=chain_dict["outcome_review_contract"],
            metadata=chain_dict["metadata"],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid simulation result: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to bridge scenario chain: {str(e)}",
        )


@router.get(
    "/{run_id}",
    response_model=ScenarioChainResponse,
    status_code=status.HTTP_200_OK,
)
async def retrieve_scenario_chain(
    run_id: str,
) -> ScenarioChainResponse:
    """
    Retrieve a previously stored scenario chain by run ID.

    Fetches the decision, counterfactual, propagation, and outcome review
    contracts created by /from-simulation or /from-run/{run_id}.

    **Path parameters:**
    - run_id: the simulation run identifier to retrieve

    **Response:**
    - Same as /from-simulation response (all four contract types + metadata)

    **Errors:**
    - 401 Unauthorized: invalid or missing API key
    - 404 Not Found: run_id does not exist in database
    """
    if run_id not in _chain_storage:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scenario chain not found for run_id: {run_id}",
        )

    stored = _chain_storage[run_id]
    chain_dict = stored["chain"]

    return ScenarioChainResponse(
        decision_contract=chain_dict["decision_contract"],
        counterfactual_contract=chain_dict["counterfactual_contract"],
        propagation_contracts=chain_dict["propagation_contracts"],
        outcome_review_contract=chain_dict["outcome_review_contract"],
        metadata=chain_dict["metadata"],
    )


@router.post(
    "/from-run/{run_id}",
    response_model=ScenarioChainResponse,
    status_code=status.HTTP_200_OK,
)
async def bridge_from_run(
    run_id: str,
    request: FromRunRequest,
) -> ScenarioChainResponse:
    """
    Execute a simulation and bridge to banking contracts end-to-end.

    Orchestrates the full pipeline:
    1. Run simulation via SimulationEngine.execute_run()
    2. Bridge result via bridge_full_chain()
    3. Store chain in database
    4. Return all contracts

    This endpoint is useful for one-shot scenario analysis without
    pre-staging simulation results.

    **Path parameters:**
    - run_id: identifier for this execution

    **Request body:**
    - scenario_id: scenario to simulate (e.g., hormuz_chokepoint_disruption)
    - baseline_urs: starting unified risk score (0.0-1.0, default 0.25)

    **Response:**
    - Same as /from-simulation (all four contract types + metadata)

    **Errors:**
    - 400 Bad Request: invalid scenario_id or baseline_urs
    - 401 Unauthorized: invalid or missing API key
    - 422 Unprocessable Entity: invalid request schema
    - 500 Internal Server Error: simulation execution failure
    """
    try:
        # Validate baseline_urs
        if not (0.0 <= request.baseline_urs <= 1.0):
            raise ValueError("baseline_urs must be between 0.0 and 1.0")

        # Execute simulation (lazy import to avoid heavy module-load at startup)
        from src.simulation_engine import SimulationEngine
        engine = SimulationEngine()
        raw_result = engine.run(
            scenario_id=request.scenario_id,
            severity=request.baseline_urs,
            horizon_hours=336,
        )
        sim_result = SimulateResponse(**raw_result)

        # Bridge to full chain
        chain_dict = bridge_full_chain(
            run_id,
            request.scenario_id,
            sim_result,
        )

        # Store chain
        _chain_storage[run_id] = {
            "timestamp": datetime.utcnow(),
            "scenario_id": request.scenario_id,
            "chain": chain_dict,
        }

        # Return response
        return ScenarioChainResponse(
            decision_contract=chain_dict["decision_contract"],
            counterfactual_contract=chain_dict["counterfactual_contract"],
            propagation_contracts=chain_dict["propagation_contracts"],
            outcome_review_contract=chain_dict["outcome_review_contract"],
            metadata=chain_dict["metadata"],
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid scenario request: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute and bridge scenario: {str(e)}",
        )
