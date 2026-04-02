"""Scenario endpoints — template listing and simulation execution."""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from src.engines.scenario.engine import GraphState, ScenarioEngine
from src.engines.scenario.templates import (
    SCENARIO_TEMPLATES,
    get_template,
    list_templates,
)
from src.models.canonical import DisruptionType, Provenance, Scenario, ScenarioShock, SourceType
from src.services.state import get_state

router = APIRouter(prefix="/scenario", tags=["scenario"])


@router.get("/templates")
async def get_templates():
    """List all available scenario templates."""
    return {"templates": list_templates()}


@router.get("/templates/{scenario_id}")
async def get_template_detail(scenario_id: str):
    """Get full detail of a scenario template."""
    tpl = get_template(scenario_id)
    if not tpl:
        raise HTTPException(status_code=404, detail=f"Scenario template '{scenario_id}' not found")
    return tpl.model_dump()


class RunScenarioRequest(BaseModel):
    scenario_id: str | None = None
    severity_override: float | None = Field(None, ge=0, le=1)
    custom_shocks: list[dict] | None = None
    horizon_hours: float | None = None


@router.post("/run")
async def run_scenario(req: RunScenarioRequest):
    """Execute a scenario simulation and return full results.

    Either provide a scenario_id (from templates) or custom_shocks.
    """
    if req.scenario_id:
        scenario = get_template(req.scenario_id)
        if not scenario:
            raise HTTPException(status_code=404, detail=f"Template '{req.scenario_id}' not found")
    elif req.custom_shocks:
        scenario = Scenario(
            title="Custom Scenario",
            scenario_type="hypothetical",
            shocks=[
                ScenarioShock(
                    target_entity_id=s["target_entity_id"],
                    shock_type=DisruptionType(s.get("shock_type", "delay")),
                    severity_score=s.get("severity_score", 0.5),
                    description=s.get("description", ""),
                )
                for s in req.custom_shocks
            ],
            provenance=Provenance(source_type=SourceType.MANUAL, source_name="api"),
        )
    else:
        raise HTTPException(status_code=400, detail="Provide scenario_id or custom_shocks")

    if req.severity_override is not None:
        for shock in scenario.shocks:
            shock.severity_score *= req.severity_override

    if req.horizon_hours is not None:
        scenario.horizon_hours = req.horizon_hours

    # Build graph state from loaded data
    state = get_state()
    graph_state = GraphState(
        node_ids=state.node_ids,
        node_labels=state.node_labels,
        node_labels_ar=state.node_labels_ar,
        node_sectors=state.node_sectors,
        sector_weights=state.sector_weights,
        edges=state.edges,
    )

    engine = ScenarioEngine(graph_state=graph_state)
    result = engine.run(scenario)

    return {
        "scenario_id": scenario.id,
        "title": scenario.title,
        "title_ar": scenario.title_ar,
        "horizon_hours": scenario.horizon_hours,
        "system_stress": result.system_stress,
        "total_economic_loss_usd": result.total_economic_loss_usd,
        "top_impacted_entities": result.top_impacted_entities[:10],
        "narrative": result.narrative,
        "recommendations": result.recommendations,
        "impacts": [
            {
                "entity_id": imp.target_entity_id,
                "entity_type": imp.target_entity_type,
                "baseline": imp.baseline_score,
                "post_scenario": imp.post_scenario_score,
                "delta": imp.delta,
                "operational_impact": imp.operational_impact,
                "factors": [f.model_dump() for f in imp.factors],
            }
            for imp in result.impacts[:20]
        ],
    }
