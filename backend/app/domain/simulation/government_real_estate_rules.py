"""
Impact Observatory | مرصد الأثر — Phase 3 Government & Real Estate Transmission Rules

Full transmission logic for the two most structurally connected GCC sectors:
  1. Government — fiscal backbone, infrastructure spender, regulator
  2. Real Estate — largest non-oil GDP contributor, banking system nexus

Uses the country-sector matrix (GOV_OUTBOUND/INBOUND, RE_OUTBOUND/INBOUND)
with country-amplified coupling weights to produce typed, auditable
stress transmission edges.

Design:
  - Pure functions — no mutation, no side effects
  - Returns lists of TransmissionEdge (frozen dataclass)
  - Every edge carries a narrative channel for explainability
  - Country amplification baked in via get_amplified_coupling()
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.domain.simulation.country_sector_matrix import (
    COUNTRY_PROFILES,
    GOV_INBOUND,
    GOV_OUTBOUND,
    RE_INBOUND,
    RE_OUTBOUND,
    MatrixCell,
    get_amplified_coupling,
)


@dataclass(frozen=True, slots=True)
class TransmissionEdge:
    """A single stress transmission path between two country-sector nodes."""
    source_country: str
    source_sector: str
    target_country: str
    target_sector: str
    weight: float               # country-amplified coupling 0–1
    lag_hours: float             # delay before stress materializes
    channel: str                 # human-readable narrative
    direction: Literal["outbound", "inbound"]
    rule_origin: Literal["government", "real_estate"]


# ═══════════════════════════════════════════════════════════════════════════════
# Government Transmission Rules
# ═══════════════════════════════════════════════════════════════════════════════

def government_outbound_edges(country_code: str, gov_stress: float) -> list[TransmissionEdge]:
    """Generate outbound edges from government sector to other sectors.

    Only fires edges where government stress exceeds a minimum threshold (0.10).
    Weight is scaled by current gov_stress level — higher stress = stronger transmission.

    Args:
        country_code: ISO 3166-1 alpha-3 (e.g. "SAU")
        gov_stress: Current government sector stress level 0–1

    Returns:
        List of TransmissionEdge from government to affected sectors.
    """
    if gov_stress < 0.10 or country_code not in COUNTRY_PROFILES:
        return []

    edges: list[TransmissionEdge] = []
    for sector, cell in GOV_OUTBOUND.items():
        amplified = get_amplified_coupling(cell, country_code)
        # Scale by current stress — low gov stress transmits weakly
        effective_weight = amplified * min(gov_stress * 1.5, 1.0)

        if effective_weight < 0.02:
            continue

        edges.append(TransmissionEdge(
            source_country=country_code,
            source_sector="government",
            target_country=country_code,
            target_sector=sector,
            weight=round(effective_weight, 4),
            lag_hours=cell.lag_hours,
            channel=cell.channel,
            direction="outbound",
            rule_origin="government",
        ))

    return edges


def government_inbound_edges(country_code: str, sector_stresses: dict[str, float]) -> list[TransmissionEdge]:
    """Generate inbound edges from other sectors into government.

    Each source sector pushes stress into government proportional to its
    own stress level and the country-amplified coupling weight.

    Args:
        country_code: ISO 3166-1 alpha-3
        sector_stresses: {sector_code: stress_0_to_1} for all sectors in this country

    Returns:
        List of TransmissionEdge from sectors into government.
    """
    if country_code not in COUNTRY_PROFILES:
        return []

    edges: list[TransmissionEdge] = []
    for sector, cell in GOV_INBOUND.items():
        src_stress = sector_stresses.get(sector, 0.0)
        if src_stress < 0.05:
            continue

        amplified = get_amplified_coupling(cell, country_code)
        effective_weight = amplified * min(src_stress * 1.3, 1.0)

        if effective_weight < 0.02:
            continue

        edges.append(TransmissionEdge(
            source_country=country_code,
            source_sector=sector,
            target_country=country_code,
            target_sector="government",
            weight=round(effective_weight, 4),
            lag_hours=cell.lag_hours,
            channel=cell.channel,
            direction="inbound",
            rule_origin="government",
        ))

    return edges


# ═══════════════════════════════════════════════════════════════════════════════
# Real Estate Transmission Rules
# ═══════════════════════════════════════════════════════════════════════════════

def real_estate_outbound_edges(country_code: str, re_stress: float) -> list[TransmissionEdge]:
    """Generate outbound edges from real estate sector to other sectors.

    Real estate stress cascades primarily to banking (NPL wave) and
    government (state-backed project exposure). Fires above 0.10 threshold.

    Args:
        country_code: ISO 3166-1 alpha-3
        re_stress: Current real estate sector stress level 0–1

    Returns:
        List of TransmissionEdge from real_estate to affected sectors.
    """
    if re_stress < 0.10 or country_code not in COUNTRY_PROFILES:
        return []

    profile = COUNTRY_PROFILES[country_code]
    leverage = profile.get("developer_leverage_ratio", 0.5)

    edges: list[TransmissionEdge] = []
    for sector, cell in RE_OUTBOUND.items():
        amplified = get_amplified_coupling(cell, country_code)
        # High developer leverage amplifies outbound real estate stress
        leverage_factor = 1.0 + (leverage - 0.5) * 0.4
        effective_weight = amplified * min(re_stress * 1.4, 1.0) * leverage_factor

        effective_weight = min(effective_weight, 1.0)
        if effective_weight < 0.02:
            continue

        edges.append(TransmissionEdge(
            source_country=country_code,
            source_sector="real_estate",
            target_country=country_code,
            target_sector=sector,
            weight=round(effective_weight, 4),
            lag_hours=cell.lag_hours,
            channel=cell.channel,
            direction="outbound",
            rule_origin="real_estate",
        ))

    return edges


def real_estate_inbound_edges(country_code: str, sector_stresses: dict[str, float]) -> list[TransmissionEdge]:
    """Generate inbound edges from other sectors into real estate.

    Banking credit freeze and government infrastructure spending freeze
    are the primary vectors that push stress into real estate.

    Args:
        country_code: ISO 3166-1 alpha-3
        sector_stresses: {sector_code: stress_0_to_1}

    Returns:
        List of TransmissionEdge from sectors into real_estate.
    """
    if country_code not in COUNTRY_PROFILES:
        return []

    edges: list[TransmissionEdge] = []
    for sector, cell in RE_INBOUND.items():
        src_stress = sector_stresses.get(sector, 0.0)
        if src_stress < 0.05:
            continue

        amplified = get_amplified_coupling(cell, country_code)
        effective_weight = amplified * min(src_stress * 1.3, 1.0)

        if effective_weight < 0.02:
            continue

        edges.append(TransmissionEdge(
            source_country=country_code,
            source_sector=sector,
            target_country=country_code,
            target_sector="real_estate",
            weight=round(effective_weight, 4),
            lag_hours=cell.lag_hours,
            channel=cell.channel,
            direction="inbound",
            rule_origin="real_estate",
        ))

    return edges


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-Country Government Contagion
# ═══════════════════════════════════════════════════════════════════════════════

# GCC fiscal contagion corridors — when one country's government is stressed,
# neighbors feel it through shared bond markets, trade links, currency pegs.
_FISCAL_CORRIDORS: list[tuple[str, str, float, str]] = [
    ("SAU", "BHR", 0.45, "Saudi fiscal stress threatens Bahrain via GCC support dependency"),
    ("SAU", "OMN", 0.25, "Saudi capex slowdown reduces Omani construction contracts"),
    ("UAE", "OMN", 0.20, "UAE banking retrenchment reduces Omani credit lines"),
    ("UAE", "BHR", 0.30, "UAE investor pullback from Bahrain financial centre"),
    ("KWT", "BHR", 0.15, "Kuwait fund withdrawal from Bahrain sovereign instruments"),
    ("QAT", "OMN", 0.10, "Qatar LNG revenue decline reduces Omani port throughput"),
    ("SAU", "UAE", 0.20, "Saudi-UAE trade corridor fiscal spillover"),
    ("UAE", "SAU", 0.15, "UAE real estate cooling reduces Saudi developer JV appetite"),
]


def cross_country_government_edges(
    country_stresses: dict[str, float],
    threshold: float = 0.30,
) -> list[TransmissionEdge]:
    """Generate cross-border government contagion edges.

    Only fires when source country government stress exceeds threshold.
    These represent GCC-specific fiscal spillover channels.

    Args:
        country_stresses: {country_code: government_sector_stress}
        threshold: Minimum stress to trigger cross-border contagion

    Returns:
        List of TransmissionEdge for cross-country government transmission.
    """
    edges: list[TransmissionEdge] = []
    for src, tgt, base_weight, channel in _FISCAL_CORRIDORS:
        src_stress = country_stresses.get(src, 0.0)
        if src_stress < threshold:
            continue

        # Scale weight by how far above threshold
        stress_factor = (src_stress - threshold) / (1.0 - threshold)
        effective_weight = base_weight * stress_factor

        if effective_weight < 0.02:
            continue

        edges.append(TransmissionEdge(
            source_country=src,
            source_sector="government",
            target_country=tgt,
            target_sector="government",
            weight=round(effective_weight, 4),
            lag_hours=48.0,
            channel=channel,
            direction="outbound",
            rule_origin="government",
        ))

    return edges


# ═══════════════════════════════════════════════════════════════════════════════
# Cross-Country Real Estate Contagion
# ═══════════════════════════════════════════════════════════════════════════════

_RE_CORRIDORS: list[tuple[str, str, float, str]] = [
    ("UAE", "SAU", 0.30, "UAE real estate crash triggers Saudi developer margin calls"),
    ("UAE", "BHR", 0.25, "Dubai property downturn reduces Bahrain offshore investment"),
    ("SAU", "UAE", 0.20, "Saudi Vision 2030 slowdown reduces UAE contractor pipeline"),
    ("SAU", "BHR", 0.15, "Saudi construction freeze propagates to Bahrain subcontractors"),
    ("QAT", "UAE", 0.15, "Qatar development pause redirects capital from UAE markets"),
    ("KWT", "UAE", 0.10, "Kuwait investor withdrawal from UAE off-plan market"),
]


def cross_country_real_estate_edges(
    country_stresses: dict[str, float],
    threshold: float = 0.35,
) -> list[TransmissionEdge]:
    """Generate cross-border real estate contagion edges.

    Args:
        country_stresses: {country_code: real_estate_sector_stress}
        threshold: Minimum stress to trigger cross-border contagion

    Returns:
        List of TransmissionEdge for cross-country real estate transmission.
    """
    edges: list[TransmissionEdge] = []
    for src, tgt, base_weight, channel in _RE_CORRIDORS:
        src_stress = country_stresses.get(src, 0.0)
        if src_stress < threshold:
            continue

        stress_factor = (src_stress - threshold) / (1.0 - threshold)
        effective_weight = base_weight * stress_factor

        if effective_weight < 0.02:
            continue

        edges.append(TransmissionEdge(
            source_country=src,
            source_sector="real_estate",
            target_country=tgt,
            target_sector="real_estate",
            weight=round(effective_weight, 4),
            lag_hours=72.0,
            channel=channel,
            direction="outbound",
            rule_origin="real_estate",
        ))

    return edges


# ═══════════════════════════════════════════════════════════════════════════════
# Aggregate — collect all Phase 3 transmission edges for a given state
# ═══════════════════════════════════════════════════════════════════════════════

def collect_all_transmission_edges(
    node_stresses: dict[tuple[str, str], float],
) -> list[TransmissionEdge]:
    """Collect all government and real estate transmission edges.

    This is the main entry point for the graph_runner to pull Phase 3 edges
    into the propagation loop.

    Args:
        node_stresses: {(country_code, sector_code): stress_0_to_1}
            for all 36 country-sector nodes.

    Returns:
        Complete list of TransmissionEdge from government and real estate rules.
    """
    all_edges: list[TransmissionEdge] = []
    countries = {cc for cc, _ in node_stresses}

    for cc in countries:
        # Build per-country sector stress map
        sector_map: dict[str, float] = {}
        for (c, s), stress in node_stresses.items():
            if c == cc:
                sector_map[s] = stress

        gov_stress = sector_map.get("government", 0.0)
        re_stress = sector_map.get("real_estate", 0.0)

        # Government rules
        all_edges.extend(government_outbound_edges(cc, gov_stress))
        all_edges.extend(government_inbound_edges(cc, sector_map))

        # Real estate rules
        all_edges.extend(real_estate_outbound_edges(cc, re_stress))
        all_edges.extend(real_estate_inbound_edges(cc, sector_map))

    # Cross-country contagion
    gov_country_stresses = {
        cc: node_stresses.get((cc, "government"), 0.0)
        for cc in countries
    }
    re_country_stresses = {
        cc: node_stresses.get((cc, "real_estate"), 0.0)
        for cc in countries
    }
    all_edges.extend(cross_country_government_edges(gov_country_stresses))
    all_edges.extend(cross_country_real_estate_edges(re_country_stresses))

    return all_edges
