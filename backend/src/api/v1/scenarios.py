"""v1 Scenarios API — list templates."""

from __future__ import annotations

from fastapi import APIRouter

from src.services.scenario_service import list_templates

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("")
async def get_scenario_templates():
    """List all available scenario templates."""
    templates = list_templates()
    return {"count": len(templates), "templates": templates}
