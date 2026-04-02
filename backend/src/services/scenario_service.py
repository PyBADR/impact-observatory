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
    "hormuz_disruption": {
        "id": "hormuz_disruption",
        "label_en": "Hormuz Closure - Severe",
        "label_ar": "إغلاق مضيق هرمز - حاد",
        "shock_nodes": ["hormuz", "oil_sector", "shipping"],
        "sectors_affected": ["energy", "maritime", "banking", "insurance", "fintech"],
        "base_loss_usd": 3_200_000_000,  # $3.2B baseline for severe
        "peak_day_offset": 3,
        "recovery_base_days": 21,
    },
    "yemen_escalation": {
        "id": "yemen_escalation",
        "label_en": "Yemen Escalation",
        "label_ar": "تصعيد يمني",
        "shock_nodes": ["red_sea", "shipping", "bab_el_mandeb"],
        "sectors_affected": ["maritime", "energy", "insurance"],
        "base_loss_usd": 1_800_000_000,
        "peak_day_offset": 5,
        "recovery_base_days": 14,
    },
    "iran_sanctions": {
        "id": "iran_sanctions",
        "label_en": "Iran Sanctions Escalation",
        "label_ar": "تصعيد عقوبات إيران",
        "shock_nodes": ["iran", "oil_sector", "hormuz"],
        "sectors_affected": ["energy", "banking", "trade"],
        "base_loss_usd": 2_400_000_000,
        "peak_day_offset": 7,
        "recovery_base_days": 30,
    },
    "cyber_attack": {
        "id": "cyber_attack",
        "label_en": "Critical Infrastructure Cyber Attack",
        "label_ar": "هجوم سيبراني على البنية التحتية",
        "shock_nodes": ["aramco", "adnoc", "banking_sector"],
        "sectors_affected": ["energy", "fintech", "banking"],
        "base_loss_usd": 900_000_000,
        "peak_day_offset": 1,
        "recovery_base_days": 7,
    },
    "gulf_airspace": {
        "id": "gulf_airspace",
        "label_en": "Gulf Airspace Closure",
        "label_ar": "إغلاق المجال الجوي الخليجي",
        "shock_nodes": ["gcc_airspace", "aviation_hub", "tourism"],
        "sectors_affected": ["aviation", "tourism", "fintech"],
        "base_loss_usd": 1_100_000_000,
        "peak_day_offset": 2,
        "recovery_base_days": 10,
    },
    "port_disruption": {
        "id": "port_disruption",
        "label_en": "Major Port Disruption",
        "label_ar": "تعطل ميناء رئيسي",
        "shock_nodes": ["jebel_ali", "ras_laffan", "jubail"],
        "sectors_affected": ["maritime", "energy", "trade"],
        "base_loss_usd": 1_500_000_000,
        "peak_day_offset": 4,
        "recovery_base_days": 14,
    },
    "oil_price_shock": {
        "id": "oil_price_shock",
        "label_en": "Oil Price Shock",
        "label_ar": "صدمة أسعار النفط",
        "shock_nodes": ["oil_sector", "opec", "gcc_economy"],
        "sectors_affected": ["energy", "banking", "government"],
        "base_loss_usd": 4_500_000_000,
        "peak_day_offset": 5,
        "recovery_base_days": 45,
    },
    "banking_stress": {
        "id": "banking_stress",
        "label_en": "Regional Banking Stress",
        "label_ar": "ضغط بنكي إقليمي",
        "shock_nodes": ["banking_sector", "interbank", "fx_market"],
        "sectors_affected": ["banking", "fintech", "insurance"],
        "base_loss_usd": 2_100_000_000,
        "peak_day_offset": 2,
        "recovery_base_days": 21,
    },
}


def create_run(params: ScenarioCreate) -> dict:
    """Create a new scenario run and return its metadata."""
    template = SCENARIO_TEMPLATES.get(params.template_id)
    if template is None:
        raise ValueError(f"Unknown template: {params.template_id}")

    run_id = f"run-{uuid.uuid4().hex[:12]}"
    label = params.label or f"{template['label_en']} - {params.horizon_hours // 24}D - S{params.severity}"

    run = {
        "run_id": run_id,
        "template_id": params.template_id,
        "severity": params.severity,
        "horizon_hours": params.horizon_hours,
        "label": label,
        "label_ar": template["label_ar"],
        "status": "running",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "template": template,
    }
    _runs[run_id] = run
    logger.info("Created run %s for template %s severity=%.2f", run_id, params.template_id, params.severity)
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
