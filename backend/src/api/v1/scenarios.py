"""v1 Scenarios API — list templates from SCENARIO_CATALOG (15 scenarios)."""

from __future__ import annotations

from fastapi import APIRouter

from src.simulation_engine import SCENARIO_CATALOG

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("")
async def get_scenario_templates():
    """List all available scenario templates (reads from SCENARIO_CATALOG)."""
    templates = [
        {
            "id": sc["id"],
            "name": sc.get("name", sc["id"]),
            "name_ar": sc.get("name_ar", ""),
            "shock_nodes": sc.get("shock_nodes", []),
            "base_loss_usd": sc.get("base_loss_usd", 0),
            "sectors_affected": sc.get("sectors_affected", []),
            "cross_sector": sc.get("cross_sector", False),
            "peak_day_offset": sc.get("peak_day_offset", 0),
            "recovery_base_days": sc.get("recovery_base_days", 0),
        }
        for sc in SCENARIO_CATALOG.values()
    ]
    return {"count": len(templates), "templates": templates}
