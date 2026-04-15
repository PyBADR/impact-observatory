"""
Impact Observatory | مرصد الأثر
Data Source Registry — typed catalog of every data source feeding scenario values.

Each source declares its type, refresh cadence, freshness status, and
confidence weight.  Static/config-based sources are explicitly labeled
so downstream consumers never mistake them for live feeds.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional


# ═══════════════════════════════════════════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════════════════════════════════════════

class DataSourceType(str, Enum):
    """Classification of data source origin."""
    STATIC = "static"            # Hardcoded in config.py / simulation_engine.py
    MANUAL = "manual"            # Analyst-entered, periodically updated
    RSS = "rss"                  # RSS/Atom news feed
    API = "api"                  # REST/GraphQL external API
    MARKET = "market"            # Market data feed (futures, FX, commodities)
    GOVERNMENT = "government"    # Government statistical agency
    INTERNAL = "internal"        # Internal observatory computation


class RefreshFrequency(str, Enum):
    """How often the source is expected to be refreshed."""
    STATIC = "static"      # Never changes unless code is redeployed
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"      # Updated by analyst action


class FreshnessStatus(str, Enum):
    """Current freshness assessment of the source data."""
    FRESH = "fresh"        # Data is within expected refresh window
    STALE = "stale"        # Data is past expected refresh window
    UNKNOWN = "unknown"    # Freshness cannot be determined


# ═══════════════════════════════════════════════════════════════════════════════
# DataSource model
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class DataSource:
    """A single data source feeding the simulation engine."""
    source_id: str
    name: str
    source_type: DataSourceType
    url: Optional[str]
    refresh_frequency: RefreshFrequency
    last_updated: str                       # ISO-8601 date string
    freshness_status: FreshnessStatus
    confidence_weight: float                # 0.0–1.0
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "source_id": self.source_id,
            "name": self.name,
            "source_type": self.source_type.value,
            "url": self.url,
            "refresh_frequency": self.refresh_frequency.value,
            "last_updated": self.last_updated,
            "freshness_status": self.freshness_status.value,
            "confidence_weight": self.confidence_weight,
            "notes": self.notes,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Registry — every source that feeds scenario outputs
# ═══════════════════════════════════════════════════════════════════════════════

DATA_SOURCE_REGISTRY: dict[str, DataSource] = {
    # ── Static / Config-Based Sources ────────────────────────────────────
    "src_config_weights": DataSource(
        source_id="src_config_weights",
        name="Simulation Formula Weights",
        source_type=DataSourceType.STATIC,
        url=None,
        refresh_frequency=RefreshFrequency.STATIC,
        last_updated="2026-04-10",
        freshness_status=FreshnessStatus.FRESH,
        confidence_weight=0.95,
        notes="All formula weights (ES, LSI, ISI, URS, Conf) defined in config.py. "
              "Calibrated against GCC historical data. Static until next model revision.",
    ),
    "src_scenario_catalog": DataSource(
        source_id="src_scenario_catalog",
        name="Scenario Catalog (base_loss, peak_day, recovery)",
        source_type=DataSourceType.STATIC,
        url=None,
        refresh_frequency=RefreshFrequency.STATIC,
        last_updated="2026-04-10",
        freshness_status=FreshnessStatus.FRESH,
        confidence_weight=0.85,
        notes="20 scenarios with base_loss_usd, peak_day_offset, recovery_base_days. "
              "Values are expert estimates, not market-derived. "
              "Defined in simulation_engine.py SCENARIO_CATALOG.",
    ),
    "src_gcc_node_registry": DataSource(
        source_id="src_gcc_node_registry",
        name="GCC Node Registry (42 infrastructure nodes)",
        source_type=DataSourceType.STATIC,
        url=None,
        refresh_frequency=RefreshFrequency.STATIC,
        last_updated="2026-04-10",
        freshness_status=FreshnessStatus.FRESH,
        confidence_weight=0.90,
        notes="42 nodes with capacity, criticality, redundancy, lat/lng. "
              "Represents GCC critical infrastructure topology. "
              "Defined in simulation_engine.py GCC_NODES.",
    ),
    "src_sector_coefficients": DataSource(
        source_id="src_sector_coefficients",
        name="Sector Alpha/Theta/Loss Allocation Coefficients",
        source_type=DataSourceType.STATIC,
        url=None,
        refresh_frequency=RefreshFrequency.STATIC,
        last_updated="2026-04-10",
        freshness_status=FreshnessStatus.FRESH,
        confidence_weight=0.90,
        notes="SECTOR_ALPHA (sensitivity), SECTOR_THETA (loss amplification), "
              "SECTOR_LOSS_ALLOCATION (fraction of base loss per sector). "
              "Defined in config.py.",
    ),
    "src_scenario_taxonomy": DataSource(
        source_id="src_scenario_taxonomy",
        name="Scenario Type Taxonomy (MARITIME/ENERGY/LIQUIDITY/CYBER/REGULATORY)",
        source_type=DataSourceType.STATIC,
        url=None,
        refresh_frequency=RefreshFrequency.STATIC,
        last_updated="2026-04-10",
        freshness_status=FreshnessStatus.FRESH,
        confidence_weight=0.95,
        notes="Maps 15 canonical scenarios to 5 types. "
              "Defined in config.py SCENARIO_TAXONOMY.",
    ),
    "src_risk_thresholds": DataSource(
        source_id="src_risk_thresholds",
        name="Risk Classification Thresholds (URS bands)",
        source_type=DataSourceType.STATIC,
        url=None,
        refresh_frequency=RefreshFrequency.STATIC,
        last_updated="2026-04-10",
        freshness_status=FreshnessStatus.FRESH,
        confidence_weight=0.95,
        notes="6 URS bands: NOMINAL/LOW/GUARDED/ELEVATED/HIGH/SEVERE. "
              "Defined in config.py RISK_THRESHOLDS.",
    ),
    "src_trust_sector_data": DataSource(
        source_id="src_trust_sector_data",
        name="Sector Data Completeness Baselines",
        source_type=DataSourceType.STATIC,
        url=None,
        refresh_frequency=RefreshFrequency.STATIC,
        last_updated="2026-04-10",
        freshness_status=FreshnessStatus.FRESH,
        confidence_weight=0.80,
        notes="TRUST_SECTOR_DATA_COMPLETENESS in config.py. "
              "Expert estimates of GCC data availability per sector. "
              "Energy: 0.88 (OPEC data), Healthcare: 0.55 (weakest).",
    ),
    "src_adjacency_graph": DataSource(
        source_id="src_adjacency_graph",
        name="GCC Infrastructure Adjacency Graph",
        source_type=DataSourceType.STATIC,
        url=None,
        refresh_frequency=RefreshFrequency.STATIC,
        last_updated="2026-04-10",
        freshness_status=FreshnessStatus.FRESH,
        confidence_weight=0.85,
        notes="GCC_ADJACENCY in simulation_engine.py. "
              "Directed graph of 42 nodes defining contagion pathways.",
    ),
    "src_frontend_briefings": DataSource(
        source_id="src_frontend_briefings",
        name="Scenario Briefing Narratives (frontend)",
        source_type=DataSourceType.STATIC,
        url=None,
        refresh_frequency=RefreshFrequency.STATIC,
        last_updated="2026-04-10",
        freshness_status=FreshnessStatus.FRESH,
        confidence_weight=0.75,
        notes="frontend/src/lib/scenarios.ts — analyst-written briefing narratives "
              "with severity, transmission chains, exposure registers. "
              "Static text, not computed.",
    ),

    # ── External Connectors (implemented but not live) ───────────────────
    "src_eia_energy": DataSource(
        source_id="src_eia_energy",
        name="U.S. Energy Information Administration (EIA)",
        source_type=DataSourceType.GOVERNMENT,
        url="https://api.eia.gov/v2/",
        refresh_frequency=RefreshFrequency.WEEKLY,
        last_updated="2026-04-01",
        freshness_status=FreshnessStatus.STALE,
        confidence_weight=0.70,
        notes="Connector implemented in data_foundation/connectors/eia.py. "
              "NOT connected to simulation pipeline. "
              "Would provide: crude oil prices, production volumes, inventory levels.",
    ),
    "src_cbk_banking": DataSource(
        source_id="src_cbk_banking",
        name="Central Bank of Kuwait (CBK) Economic Data",
        source_type=DataSourceType.GOVERNMENT,
        url="https://www.cbk.gov.kw/",
        refresh_frequency=RefreshFrequency.WEEKLY,
        last_updated="2026-03-15",
        freshness_status=FreshnessStatus.STALE,
        confidence_weight=0.65,
        notes="Connector implemented in data_foundation/connectors/cbk.py. "
              "NOT connected to simulation pipeline. "
              "Would provide: interest rates, money supply, banking sector indicators.",
    ),
    "src_imf_macro": DataSource(
        source_id="src_imf_macro",
        name="IMF Macroeconomic Indicators",
        source_type=DataSourceType.GOVERNMENT,
        url="https://www.imf.org/external/datamapper/api/v1",
        refresh_frequency=RefreshFrequency.WEEKLY,
        last_updated="2026-03-01",
        freshness_status=FreshnessStatus.STALE,
        confidence_weight=0.65,
        notes="Connector implemented in data_foundation/connectors/imf.py. "
              "NOT connected to simulation pipeline. "
              "Would provide: GDP, inflation, fiscal balance for GCC countries.",
    ),

    # ── Future Sources (not implemented) ─────────────────────────────────
    "src_opec_production": DataSource(
        source_id="src_opec_production",
        name="OPEC Monthly Oil Market Report",
        source_type=DataSourceType.GOVERNMENT,
        url="https://www.opec.org/opec_web/en/publications/338.htm",
        refresh_frequency=RefreshFrequency.MANUAL,
        last_updated="2026-01-01",
        freshness_status=FreshnessStatus.UNKNOWN,
        confidence_weight=0.0,
        notes="NOT implemented. Future source for energy scenario calibration.",
    ),
    "src_brent_futures": DataSource(
        source_id="src_brent_futures",
        name="Brent Crude Futures (ICE)",
        source_type=DataSourceType.MARKET,
        url=None,
        refresh_frequency=RefreshFrequency.DAILY,
        last_updated="2026-01-01",
        freshness_status=FreshnessStatus.UNKNOWN,
        confidence_weight=0.0,
        notes="NOT implemented. Would provide real-time energy price signals "
              "for energy_market_volatility_shock scenario.",
    ),
    "src_gcc_shipping_ais": DataSource(
        source_id="src_gcc_shipping_ais",
        name="AIS Maritime Traffic (GCC Waters)",
        source_type=DataSourceType.API,
        url=None,
        refresh_frequency=RefreshFrequency.DAILY,
        last_updated="2026-01-01",
        freshness_status=FreshnessStatus.UNKNOWN,
        confidence_weight=0.0,
        notes="NOT implemented. Connector skeleton exists in connectors/maritime_adapter.py. "
              "Would validate maritime scenario severity against live traffic.",
    ),
}


# ═══════════════════════════════════════════════════════════════════════════════
# Query helpers
# ═══════════════════════════════════════════════════════════════════════════════

def get_source(source_id: str) -> DataSource | None:
    """Look up a data source by ID. Returns None if not found."""
    return DATA_SOURCE_REGISTRY.get(source_id)


def get_sources_by_type(source_type: DataSourceType) -> list[DataSource]:
    """Return all sources of a given type."""
    return [s for s in DATA_SOURCE_REGISTRY.values() if s.source_type == source_type]


def get_stale_sources() -> list[DataSource]:
    """Return all sources with freshness_status == STALE."""
    return [
        s for s in DATA_SOURCE_REGISTRY.values()
        if s.freshness_status == FreshnessStatus.STALE
    ]


def get_connected_live_sources() -> list[DataSource]:
    """Return sources that are both non-static AND have confidence > 0.

    Currently returns empty — no live sources are connected to the pipeline.
    """
    return [
        s for s in DATA_SOURCE_REGISTRY.values()
        if s.source_type != DataSourceType.STATIC
        and s.confidence_weight > 0.0
        and s.freshness_status == FreshnessStatus.FRESH
    ]


def registry_summary() -> dict:
    """Return a summary of the registry state."""
    sources = list(DATA_SOURCE_REGISTRY.values())
    by_type: dict[str, int] = {}
    for s in sources:
        by_type[s.source_type.value] = by_type.get(s.source_type.value, 0) + 1

    live = get_connected_live_sources()
    stale = get_stale_sources()

    return {
        "total_sources": len(sources),
        "by_type": by_type,
        "live_connected_count": len(live),
        "stale_count": len(stale),
        "all_static_fallback": len(live) == 0,
        "static_sources": [
            s.source_id for s in sources
            if s.source_type == DataSourceType.STATIC
        ],
        "stale_sources": [s.source_id for s in stale],
    }
