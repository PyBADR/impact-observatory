"""
Impact Observatory | مرصد الأثر
Scenario Data Provenance — typed provenance records for every scenario output value.

Each provenance record traces a scenario output value back to its source,
calculation method, and freshness.  When no live data is connected,
every record is marked ``is_static_fallback=True``.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.config import (
    SECTOR_ALPHA,
    SECTOR_THETA,
    SECTOR_LOSS_ALLOCATION,
    SCENARIO_TAXONOMY,
    RISK_THRESHOLDS,
)
from src.data_trust.source_registry import (
    FreshnessStatus,
    get_connected_live_sources,
)


# ═══════════════════════════════════════════════════════════════════════════════
# Provenance record
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class ScenarioProvenance:
    """Provenance record for a single scenario output value."""
    scenario_id: str
    value_name: str
    current_value: Any
    source_id: str
    calculation_method: str
    is_static_fallback: bool
    last_updated: str            # ISO-8601
    confidence_score: float      # 0.0–1.0

    def to_dict(self) -> dict:
        return {
            "scenario_id": self.scenario_id,
            "value_name": self.value_name,
            "current_value": self.current_value,
            "source_id": self.source_id,
            "calculation_method": self.calculation_method,
            "is_static_fallback": self.is_static_fallback,
            "last_updated": self.last_updated,
            "confidence_score": self.confidence_score,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Builder — generate provenance for a single scenario
# ═══════════════════════════════════════════════════════════════════════════════

def build_provenance_for_scenario(
    scenario_id: str,
    catalog_entry: dict[str, Any],
) -> list[ScenarioProvenance]:
    """Build provenance records for every key output of a scenario.

    Currently all values are static fallbacks because no live sources
    are connected to the simulation pipeline.
    """
    has_live = len(get_connected_live_sources()) > 0
    records: list[ScenarioProvenance] = []

    # -- base_loss_usd
    records.append(ScenarioProvenance(
        scenario_id=scenario_id,
        value_name="base_loss_usd",
        current_value=catalog_entry.get("base_loss_usd"),
        source_id="src_scenario_catalog",
        calculation_method="Expert estimate. Static value in SCENARIO_CATALOG.",
        is_static_fallback=not has_live,
        last_updated="2026-04-10",
        confidence_score=0.85 if not has_live else 0.90,
    ))

    # -- peak_day_offset
    records.append(ScenarioProvenance(
        scenario_id=scenario_id,
        value_name="peak_day_offset",
        current_value=catalog_entry.get("peak_day_offset"),
        source_id="src_scenario_catalog",
        calculation_method="Expert estimate. Static value in SCENARIO_CATALOG.",
        is_static_fallback=not has_live,
        last_updated="2026-04-10",
        confidence_score=0.80,
    ))

    # -- recovery_base_days
    records.append(ScenarioProvenance(
        scenario_id=scenario_id,
        value_name="recovery_base_days",
        current_value=catalog_entry.get("recovery_base_days"),
        source_id="src_scenario_catalog",
        calculation_method="Expert estimate. Static value in SCENARIO_CATALOG.",
        is_static_fallback=not has_live,
        last_updated="2026-04-10",
        confidence_score=0.75,
    ))

    # -- shock_nodes
    records.append(ScenarioProvenance(
        scenario_id=scenario_id,
        value_name="shock_nodes",
        current_value=catalog_entry.get("shock_nodes"),
        source_id="src_gcc_node_registry",
        calculation_method="Static node selection from GCC_NODES topology.",
        is_static_fallback=True,
        last_updated="2026-04-10",
        confidence_score=0.90,
    ))

    # -- sectors_affected
    records.append(ScenarioProvenance(
        scenario_id=scenario_id,
        value_name="sectors_affected",
        current_value=catalog_entry.get("sectors_affected"),
        source_id="src_scenario_catalog",
        calculation_method="Static sector list in SCENARIO_CATALOG.",
        is_static_fallback=True,
        last_updated="2026-04-10",
        confidence_score=0.90,
    ))

    # -- scenario_type (from taxonomy)
    scenario_type = SCENARIO_TAXONOMY.get(scenario_id, "UNKNOWN")
    records.append(ScenarioProvenance(
        scenario_id=scenario_id,
        value_name="scenario_type",
        current_value=scenario_type,
        source_id="src_scenario_taxonomy",
        calculation_method="Direct lookup in SCENARIO_TAXONOMY (config.py).",
        is_static_fallback=True,
        last_updated="2026-04-10",
        confidence_score=1.0 if scenario_type != "UNKNOWN" else 0.20,
    ))

    # -- sector_alpha coefficients used
    affected = catalog_entry.get("sectors_affected", [])
    for sector in affected:
        alpha = SECTOR_ALPHA.get(sector, 0.0)
        records.append(ScenarioProvenance(
            scenario_id=scenario_id,
            value_name=f"sector_alpha_{sector}",
            current_value=alpha,
            source_id="src_sector_coefficients",
            calculation_method=f"SECTOR_ALPHA['{sector}'] from config.py.",
            is_static_fallback=True,
            last_updated="2026-04-10",
            confidence_score=0.90,
        ))

    # -- sector_theta (loss amplification)
    for sector in affected:
        theta = SECTOR_THETA.get(sector, 1.0)
        records.append(ScenarioProvenance(
            scenario_id=scenario_id,
            value_name=f"sector_theta_{sector}",
            current_value=theta,
            source_id="src_sector_coefficients",
            calculation_method=f"SECTOR_THETA['{sector}'] from config.py.",
            is_static_fallback=True,
            last_updated="2026-04-10",
            confidence_score=0.90,
        ))

    return records


# ═══════════════════════════════════════════════════════════════════════════════
# Batch builder
# ═══════════════════════════════════════════════════════════════════════════════

def build_all_provenance(
    scenario_catalog: dict[str, dict[str, Any]],
) -> dict[str, list[ScenarioProvenance]]:
    """Build provenance for every scenario in the catalog.

    Returns a dict keyed by scenario_id.
    """
    result: dict[str, list[ScenarioProvenance]] = {}
    for sid, entry in scenario_catalog.items():
        result[sid] = build_provenance_for_scenario(sid, entry)
    return result
