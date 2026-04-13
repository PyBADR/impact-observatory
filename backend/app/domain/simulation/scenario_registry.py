"""
Impact Observatory | مرصد الأثر — Phase 2 Scenario Registry
Central registry mapping scenario slugs to their dataset modules.

Design:
  Each scenario is a ScenarioSpec dataclass containing:
    - Metadata (slug, name, description)
    - Default parameters
    - Callable factories for shock vectors and edges
    - Country/sector metadata references

  The registry is a plain dict[str, ScenarioSpec].
  Adding a new scenario = adding one entry + one dataset module.

Architecture layer: Configuration (Layer 1 — Data)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from app.domain.simulation.graph_types import Edge


# ═══════════════════════════════════════════════════════════════════════════════
# Scenario Specification
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True, slots=True)
class ScenarioSpec:
    """Immutable specification for a simulation scenario."""
    slug: str
    name: str
    name_ar: str
    description: str
    default_severity: float
    default_horizon_hours: int
    scenario_type: str                   # e.g. "energy_disruption", "liquidity_stress"

    # Dataset bindings — callables that produce typed data.
    # Decoupled from import-time so dataset modules load lazily.
    country_meta: dict[str, dict]
    sector_meta: dict[str, dict]
    build_shock_vector: Callable[..., dict[tuple[str, str], float]]
    build_edges: Callable[[dict[tuple[str, str], float]], list[Edge]]

    # Scenario-specific parameter names and defaults for the request schema
    extra_param_defaults: dict[str, Any] = field(default_factory=dict)

    # Explainability context
    shock_origin_label: str = ""         # e.g. "Strait of Hormuz transit disruption"
    primary_transmission: str = ""       # e.g. "Energy pricing → banking liquidity"


# ═══════════════════════════════════════════════════════════════════════════════
# Registry Construction
# ═══════════════════════════════════════════════════════════════════════════════

def _build_registry() -> dict[str, ScenarioSpec]:
    """Build the scenario registry. Called once at import time."""

    registry: dict[str, ScenarioSpec] = {}

    # ── Scenario 1: Hormuz Chokepoint Disruption (Phase 1) ───────────────
    from app.domain.simulation.hormuz_dataset import (
        COUNTRY_META as HORMUZ_COUNTRIES,
        SECTOR_META as HORMUZ_SECTORS,
        build_initial_shock_vector as hormuz_shock,
        build_edges as hormuz_edges,
    )
    registry["hormuz"] = ScenarioSpec(
        slug="hormuz",
        name="Energy & Trade Disruption — Strait of Hormuz",
        name_ar="اضطراب الطاقة والتجارة — مضيق هرمز",
        description=(
            "Partial or total blockage of the Strait of Hormuz disrupting "
            "oil/LNG transit, triggering energy price shock and cascading "
            "financial stress across GCC economies."
        ),
        default_severity=0.72,
        default_horizon_hours=168,
        scenario_type="energy_disruption",
        country_meta=HORMUZ_COUNTRIES,
        sector_meta=HORMUZ_SECTORS,
        build_shock_vector=hormuz_shock,
        build_edges=hormuz_edges,
        extra_param_defaults={"transit_reduction_pct": 0.60},
        shock_origin_label="Strait of Hormuz transit disruption",
        primary_transmission="Energy pricing → banking liquidity → fiscal revenue",
    )

    # ── Scenario 2: Regional Liquidity Stress Event ──────────────────────
    from app.domain.simulation.liquidity_dataset import (
        COUNTRY_META as LIQ_COUNTRIES,
        SECTOR_META as LIQ_SECTORS,
        build_initial_shock_vector as liq_shock,
        build_edges as liq_edges,
    )
    registry["liquidity_stress"] = ScenarioSpec(
        slug="liquidity_stress",
        name="Regional Liquidity Stress Event",
        name_ar="حدث ضغط السيولة الإقليمي",
        description=(
            "Cross-border liquidity squeeze triggered by simultaneous deposit "
            "flight, interbank market freeze, and sovereign CDS widening across "
            "GCC banking systems. Transmits via correspondent banking, trade "
            "finance, and FX swap channels."
        ),
        default_severity=0.65,
        default_horizon_hours=336,
        scenario_type="liquidity_stress",
        country_meta=LIQ_COUNTRIES,
        sector_meta=LIQ_SECTORS,
        build_shock_vector=liq_shock,
        build_edges=liq_edges,
        extra_param_defaults={"interbank_freeze_pct": 0.45},
        shock_origin_label="GCC interbank market freeze and deposit flight",
        primary_transmission="Banking liquidity → insurance solvency → fiscal pressure",
    )

    return registry


SCENARIO_REGISTRY: dict[str, ScenarioSpec] = _build_registry()


def get_scenario(slug: str) -> ScenarioSpec:
    """Retrieve a scenario spec by slug. Raises KeyError if not found."""
    if slug not in SCENARIO_REGISTRY:
        available = ", ".join(sorted(SCENARIO_REGISTRY.keys()))
        raise KeyError(
            f"Unknown scenario '{slug}'. Available: {available}"
        )
    return SCENARIO_REGISTRY[slug]


def list_scenarios() -> list[dict[str, str]]:
    """Return a summary list of all registered scenarios."""
    return [
        {
            "slug": spec.slug,
            "name": spec.name,
            "name_ar": spec.name_ar,
            "type": spec.scenario_type,
            "description": spec.description,
            "default_severity": str(spec.default_severity),
            "default_horizon_hours": str(spec.default_horizon_hours),
        }
        for spec in SCENARIO_REGISTRY.values()
    ]
