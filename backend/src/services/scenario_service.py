"""Service 1: scenario_service — Event Scenario (سيناريو الحدث).

Takes a scenario template + severity + horizon → produces shock vector
and initializes a run record.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone

from src.schemas.scenario import Scenario, ScenarioCreate

logger = logging.getLogger(__name__)

# In-memory run store (replaced by DB in production)
_runs: dict[str, dict] = {}


# ── Scenario Templates ──────────────────────────────────────────────
SCENARIO_TEMPLATES: dict[str, dict] = {
    "hormuz_chokepoint_disruption": {
        "id": "hormuz_chokepoint_disruption",
        "label_en": "Strategic Maritime Chokepoint Disruption (Hormuz)",
        "label_ar": "تعطّل نقطة اختناق بحرية استراتيجية (مضيق هرمز)",
        "shock_nodes": ["hormuz", "oil_sector", "shipping"],
        "sectors_affected": ["energy", "maritime", "banking", "insurance", "fintech"],
        "base_loss_usd": 3_200_000_000,
        "peak_day_offset": 3,
        "recovery_base_days": 21,
    },
    "red_sea_trade_corridor_instability": {
        "id": "red_sea_trade_corridor_instability",
        "label_en": "Red Sea Trade Corridor Instability",
        "label_ar": "اضطراب ممر التجارة في البحر الأحمر",
        "shock_nodes": ["red_sea", "shipping", "bab_el_mandeb"],
        "sectors_affected": ["maritime", "energy", "insurance"],
        "base_loss_usd": 1_800_000_000,
        "peak_day_offset": 5,
        "recovery_base_days": 14,
    },
    "cross_border_sanctions_escalation": {
        "id": "cross_border_sanctions_escalation",
        "label_en": "Cross-Border Sanctions Escalation",
        "label_ar": "تصاعد العقوبات العابرة للحدود",
        "shock_nodes": ["iran", "oil_sector", "hormuz"],
        "sectors_affected": ["energy", "banking", "trade"],
        "base_loss_usd": 2_400_000_000,
        "peak_day_offset": 7,
        "recovery_base_days": 30,
    },
    "financial_infrastructure_cyber_disruption": {
        "id": "financial_infrastructure_cyber_disruption",
        "label_en": "Financial Infrastructure Cyber Disruption",
        "label_ar": "تعطّل البنية المالية نتيجة هجوم سيبراني",
        "shock_nodes": ["aramco", "adnoc", "banking_sector"],
        "sectors_affected": ["energy", "fintech", "banking"],
        "base_loss_usd": 900_000_000,
        "peak_day_offset": 1,
        "recovery_base_days": 7,
    },
    "regional_airspace_constraint": {
        "id": "regional_airspace_constraint",
        "label_en": "Regional Airspace Constraint Scenario",
        "label_ar": "سيناريو قيود المجال الجوي الإقليمي",
        "shock_nodes": ["gcc_airspace", "aviation_hub", "tourism"],
        "sectors_affected": ["aviation", "tourism", "fintech"],
        "base_loss_usd": 1_100_000_000,
        "peak_day_offset": 2,
        "recovery_base_days": 10,
    },
    "critical_port_throughput_disruption": {
        "id": "critical_port_throughput_disruption",
        "label_en": "Critical Port Throughput Disruption",
        "label_ar": "تعطّل تدفق العمليات في ميناء حيوي",
        "shock_nodes": ["jebel_ali", "ras_laffan", "jubail"],
        "sectors_affected": ["maritime", "energy", "trade"],
        "base_loss_usd": 1_500_000_000,
        "peak_day_offset": 4,
        "recovery_base_days": 14,
    },
    "energy_market_volatility_shock": {
        "id": "energy_market_volatility_shock",
        "label_en": "Energy Market Volatility Shock",
        "label_ar": "صدمة تقلبات أسواق الطاقة",
        "shock_nodes": ["oil_sector", "opec", "gcc_economy"],
        "sectors_affected": ["energy", "banking", "government"],
        "base_loss_usd": 4_500_000_000,
        "peak_day_offset": 5,
        "recovery_base_days": 45,
    },
    "regional_liquidity_stress_event": {
        "id": "regional_liquidity_stress_event",
        "label_en": "Regional Liquidity Stress Event",
        "label_ar": "أزمة سيولة مصرفية إقليمية",
        "shock_nodes": ["banking_sector", "interbank", "fx_market"],
        "sectors_affected": ["banking", "fintech", "insurance"],
        "base_loss_usd": 2_100_000_000,
        "peak_day_offset": 2,
        "recovery_base_days": 21,
    },
}


def create_run(params: ScenarioCreate) -> dict:
    """Create a new scenario run and return its metadata."""
    template = SCENARIO_TEMPLATES.get(params.scenario_id)
    if template is None:
        raise ValueError(f"Unknown scenario: {params.scenario_id}")

    run_id = f"run-{uuid.uuid4().hex[:12]}"
    label = params.label or f"{template['label_en']} - {params.horizon_hours // 24}D - S{params.severity}"

    run = {
        "run_id": run_id,
        "scenario_id": params.scenario_id,
        "severity": params.severity,
        "horizon_hours": params.horizon_hours,
        "label": label,
        "label_ar": template["label_ar"],
        "status": "running",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "template": template,
    }
    _runs[run_id] = run
    logger.info("Created run %s for scenario %s severity=%.2f", run_id, params.scenario_id, params.severity)
    return run


def get_run(run_id: str) -> dict | None:
    """Get run metadata."""
    return _runs.get(run_id)


def complete_run(run_id: str, results: dict) -> None:
    """Mark a run as completed with results."""
    run = _runs.get(run_id)
    if run:
        run["status"] = "completed"
        run["completed_at"] = datetime.now(timezone.utc).isoformat()
        run["results"] = results


def list_templates() -> list[dict]:
    """Return all available scenario templates."""
    return [
        {
            "id": t["id"],
            "label_en": t["label_en"],
            "label_ar": t["label_ar"],
            "sectors_affected": t["sectors_affected"],
            "base_loss_usd": t["base_loss_usd"],
        }
        for t in SCENARIO_TEMPLATES.values()
    ]
