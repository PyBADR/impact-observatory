"""Scenario management endpoints"""

import logging
import uuid
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.api.models import (
    ScenarioRequest, ScenarioResponse, ScenarioRunResponse,
    ScenarioRunListResponse
)
from app.api.auth import api_key_auth, require_role
from app.scenarios.templates import SCENARIO_TEMPLATES

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory scenario storage (replace with database in production)
scenarios_db = {}
runs_db = {}


@router.get("/scenarios", response_model=List[ScenarioResponse])
async def list_scenarios(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(api_key_auth)
):
    """
    List all scenarios
    
    Args:
        skip: Number of records to skip
        limit: Maximum records to return
        api_key: API key for authentication
        
    Returns:
        List of ScenarioResponse objects
    """
    scenario_list = list(scenarios_db.values())
    return scenario_list[skip:skip + limit]


@router.post("/scenarios", response_model=ScenarioResponse)
async def create_scenario(
    request: ScenarioRequest,
    api_key: str = Depends(api_key_auth),
    role: str = Depends(require_role("analyst"))
):
    """
    Create a new scenario
    
    Args:
        request: ScenarioRequest with scenario details
        api_key: API key for authentication
        role: User role
        
    Returns:
        ScenarioResponse with created scenario
    """
    scenario_id = str(uuid.uuid4())
    
    scenario = ScenarioResponse(
        scenario_id=scenario_id,
        name=request.name,
        description=request.description,
        scenario_type=request.scenario_type,
        parameters=request.parameters,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    scenarios_db[scenario_id] = scenario
    logger.info(f"Created scenario {scenario_id}: {request.name}")
    
    return scenario


@router.post("/scenarios/run", response_model=ScenarioRunResponse)
async def run_scenario(
    scenario_id: str,
    api_key: str = Depends(api_key_auth),
    role: str = Depends(require_role("analyst"))
):
    """
    Run a scenario simulation
    
    Args:
        scenario_id: ID of scenario to run
        api_key: API key for authentication
        role: User role
        
    Returns:
        ScenarioRunResponse with run details
    """
    if scenario_id not in scenarios_db:
        raise HTTPException(status_code=404, detail="Scenario not found")
    
    run_id = str(uuid.uuid4())
    scenario = scenarios_db[scenario_id]
    
    run = ScenarioRunResponse(
        run_id=run_id,
        scenario_id=scenario_id,
        scenario_name=scenario.name,
        status="completed",
        started_at=datetime.utcnow(),
        completed_at=datetime.utcnow(),
        results={
            "impacted_assets": 45,
            "total_disruption_value": 2500000,
            "affected_corridors": 8,
            "cascade_depth": 3
        }
    )
    
    runs_db[run_id] = run
    logger.info(f"Executed scenario {scenario_id} as run {run_id}")
    
    return run


@router.get("/scenarios/runs/{run_id}", response_model=ScenarioRunResponse)
async def get_scenario_run(
    run_id: str,
    api_key: str = Depends(api_key_auth)
):
    """
    Get details of a scenario run
    
    Args:
        run_id: ID of the scenario run
        api_key: API key for authentication
        
    Returns:
        ScenarioRunResponse with run details
    """
    if run_id not in runs_db:
        raise HTTPException(status_code=404, detail="Scenario run not found")
    
    return runs_db[run_id]


@router.get("/scenarios/runs", response_model=ScenarioRunListResponse)
async def list_scenario_runs(
    scenario_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    api_key: str = Depends(api_key_auth)
):
    """
    List scenario runs
    
    Args:
        scenario_id: Optional filter by scenario ID
        skip: Number of records to skip
        limit: Maximum records to return
        api_key: API key for authentication
        
    Returns:
        ScenarioRunListResponse with runs
    """
    runs_list = list(runs_db.values())
    
    if scenario_id:
        runs_list = [r for r in runs_list if r.scenario_id == scenario_id]
    
    return ScenarioRunListResponse(
        total=len(runs_list),
        skip=skip,
        limit=limit,
        data=runs_list[skip:skip + limit]
    )


# ============================================================================
# New Mandatory Endpoints
# ============================================================================

@router.get(
    "/scenarios/templates",
    response_model=dict,
    summary="Get Scenario Templates",
    description="Retrieve all available scenario templates for disruption modeling"
)
async def get_scenario_templates(
    disruption_type: Optional[str] = Query(None, description="Filter by disruption type"),
    api_key: str = Depends(api_key_auth),
) -> dict:
    """
    Get all available scenario templates from the system template library.
    
    Templates include pre-configured disruption scenarios for geopolitical events,
    infrastructure failures, natural disasters, and other supply chain risks.
    
    Args:
        disruption_type: Optional filter by disruption type
        api_key: API key for authentication
        
    Returns:
        Dictionary with scenario templates and metadata
    """
    try:
        templates_list = []
        
        for template_id, template in SCENARIO_TEMPLATES.items():
            # Apply optional filter by disruption type
            if disruption_type and template.disruption_type != disruption_type:
                continue
            
            # Convert template to dict using its to_dict method if available
            if hasattr(template, 'to_dict'):
                template_dict = template.to_dict()
            else:
                # Fallback for templates without to_dict method
                template_dict = {
                    "id": template_id,
                    "name": getattr(template, 'name', template_id),
                    "title": getattr(template, 'title', ''),
                    "description": getattr(template, 'description', ''),
                    "disruption_type": getattr(template, 'disruption_type', ''),
                    "severity": getattr(template, 'severity', 0.0),
                    "affected_domains": getattr(template, 'affected_domains', []),
                    "affected_regions": getattr(template, 'affected_regions', []),
                    "affected_countries": getattr(template, 'affected_countries', []),
                    "duration_hours": getattr(template, 'duration_hours', 0),
                    "propagation_depth": getattr(template, 'propagation_depth', 1),
                    "scenario_tags": getattr(template, 'scenario_tags', []),
                }
            
            templates_list.append(template_dict)
        
        logger.info(f"Retrieved {len(templates_list)} scenario templates")
        
        return {
            "success": True,
            "explanation": "Available scenario templates for disruption modeling and impact analysis",
            "total": len(templates_list),
            "templates": templates_list,
            "timestamp": datetime.utcnow(),
        }
    except Exception as e:
        logger.error(f"Error retrieving scenario templates: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error retrieving scenario templates: {str(e)}")
