"""Macro Intelligence Layer — GCC Causal Channel Graph.

Static definition of all known causal transmission channels
between GCC impact domains.

This is the SINGLE SOURCE OF TRUTH for causal relationships.
No channel definitions exist outside this file.

Design:
  - Channels are pre-defined, not discovered at runtime.
  - Each channel has a base weight (transmission strength), decay, and lag.
  - Weights are calibrated for GCC market structure.
  - Bidirectional channels are explicitly marked.
  - Region-specific channels narrow the propagation scope.
  - relationship_type classifies the transmission mechanism.
  - lag_hours estimates propagation delay.

Calibration rationale:
  - Oil/Gas dominates GCC fiscal + banking → high weights (0.8–0.9)
  - Banking → capital markets is tight coupling → 0.85
  - Insurance ↔ real estate is moderate → 0.55
  - Cyber → everything is medium (0.45–0.60) — systemic but indirect
  - Maritime → trade logistics is near-direct → 0.90
"""

from src.macro.macro_enums import GCCRegion, ImpactDomain
from src.macro.causal.causal_schemas import CausalChannel, RelationshipType

RT = RelationshipType  # alias for readability


def _ch(
    from_d: ImpactDomain,
    to_d: ImpactDomain,
    label: str,
    weight: float,
    rel: RelationshipType,
    decay: float = 0.15,
    lag: int = 0,
    regions: list[GCCRegion] | None = None,
    bidirectional: bool = False,
) -> CausalChannel:
    """Channel factory. Generates stable channel_id from domain pair."""
    return CausalChannel(
        channel_id=f"{from_d.value}__{to_d.value}",
        from_domain=from_d,
        to_domain=to_d,
        relationship_type=rel,
        transmission_label=label,
        base_weight=weight,
        decay_per_hop=decay,
        lag_hours=lag,
        regions=regions or [GCCRegion.GCC_WIDE],
        bidirectional=bidirectional,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GCC CAUSAL CHANNEL REGISTRY
# ═══════════════════════════════════════════════════════════════════════════════

GCC_CAUSAL_CHANNELS: list[CausalChannel] = [
    # ── Oil & Gas → downstream ────────────────────────────────────────────
    _ch(ImpactDomain.OIL_GAS, ImpactDomain.SOVEREIGN_FISCAL,
        "Oil revenue shock → government fiscal capacity",
        0.90, RT.FISCAL_LINKAGE, 0.10, lag=24),
    _ch(ImpactDomain.OIL_GAS, ImpactDomain.BANKING,
        "Oil sector stress → bank asset quality / NPLs",
        0.80, RT.DIRECT_EXPOSURE, 0.12, lag=48),
    _ch(ImpactDomain.OIL_GAS, ImpactDomain.CAPITAL_MARKETS,
        "Oil price volatility → equity/bond market repricing",
        0.75, RT.MARKET_CONTAGION, 0.15, lag=4),
    _ch(ImpactDomain.OIL_GAS, ImpactDomain.ENERGY_GRID,
        "Oil/gas supply disruption → power generation stress",
        0.70, RT.SUPPLY_CHAIN, 0.10, lag=12),
    _ch(ImpactDomain.OIL_GAS, ImpactDomain.TRADE_LOGISTICS,
        "Oil export disruption → port throughput / shipping demand",
        0.65, RT.SUPPLY_CHAIN, 0.15, lag=24),

    # ── Banking → downstream ─────────────────────────────────────────────
    _ch(ImpactDomain.BANKING, ImpactDomain.CAPITAL_MARKETS,
        "Banking stress → equity sell-off / credit spread widening",
        0.85, RT.MARKET_CONTAGION, 0.12, lag=2),
    _ch(ImpactDomain.BANKING, ImpactDomain.REAL_ESTATE,
        "Credit tightening → property market contraction",
        0.70, RT.DIRECT_EXPOSURE, 0.15, lag=72),
    _ch(ImpactDomain.BANKING, ImpactDomain.INSURANCE,
        "Bank counterparty risk → insurance claims / credit insurance",
        0.55, RT.RISK_TRANSFER, 0.18, lag=48),

    # ── Sovereign Fiscal → downstream ────────────────────────────────────
    _ch(ImpactDomain.SOVEREIGN_FISCAL, ImpactDomain.BANKING,
        "Sovereign stress → bank sovereign exposure / guarantees",
        0.75, RT.FISCAL_LINKAGE, 0.12, lag=24),
    _ch(ImpactDomain.SOVEREIGN_FISCAL, ImpactDomain.CAPITAL_MARKETS,
        "Fiscal deterioration → sovereign bond repricing",
        0.80, RT.MARKET_CONTAGION, 0.10, lag=6),
    _ch(ImpactDomain.SOVEREIGN_FISCAL, ImpactDomain.REAL_ESTATE,
        "Government spending cuts → construction / real estate demand",
        0.50, RT.FISCAL_LINKAGE, 0.20, lag=168),

    # ── Maritime → downstream ────────────────────────────────────────────
    _ch(ImpactDomain.MARITIME, ImpactDomain.TRADE_LOGISTICS,
        "Port/shipping disruption → supply chain bottleneck",
        0.90, RT.SUPPLY_CHAIN, 0.08, lag=6),
    _ch(ImpactDomain.MARITIME, ImpactDomain.OIL_GAS,
        "Chokepoint blockage → oil export disruption",
        0.85, RT.SUPPLY_CHAIN, 0.10, lag=12),
    _ch(ImpactDomain.MARITIME, ImpactDomain.INSURANCE,
        "Maritime incident → marine/cargo insurance claims",
        0.65, RT.RISK_TRANSFER, 0.15, lag=24),

    # ── Trade Logistics → downstream ─────────────────────────────────────
    _ch(ImpactDomain.TRADE_LOGISTICS, ImpactDomain.REAL_ESTATE,
        "Supply chain disruption → construction material shortage",
        0.45, RT.SUPPLY_CHAIN, 0.20, lag=168),
    _ch(ImpactDomain.TRADE_LOGISTICS, ImpactDomain.CAPITAL_MARKETS,
        "Trade disruption → listed logistics/retail repricing",
        0.50, RT.MARKET_CONTAGION, 0.18, lag=12),

    # ── Energy Grid → downstream ─────────────────────────────────────────
    _ch(ImpactDomain.ENERGY_GRID, ImpactDomain.TELECOMMUNICATIONS,
        "Power outage → telecom infrastructure degradation",
        0.60, RT.INFRASTRUCTURE_DEP, 0.15, lag=2),
    _ch(ImpactDomain.ENERGY_GRID, ImpactDomain.BANKING,
        "Prolonged outage → ATM/digital banking disruption",
        0.40, RT.INFRASTRUCTURE_DEP, 0.20, lag=6),

    # ── Cyber Infrastructure → downstream ────────────────────────────────
    _ch(ImpactDomain.CYBER_INFRASTRUCTURE, ImpactDomain.BANKING,
        "Cyber attack → financial system disruption",
        0.60, RT.INFRASTRUCTURE_DEP, 0.15, lag=1),
    _ch(ImpactDomain.CYBER_INFRASTRUCTURE, ImpactDomain.TELECOMMUNICATIONS,
        "Cyber attack → telecom outage / data breach",
        0.55, RT.INFRASTRUCTURE_DEP, 0.15, lag=1),
    _ch(ImpactDomain.CYBER_INFRASTRUCTURE, ImpactDomain.CAPITAL_MARKETS,
        "Cyber attack → exchange halt / clearing disruption",
        0.50, RT.INFRASTRUCTURE_DEP, 0.18, lag=2),
    _ch(ImpactDomain.CYBER_INFRASTRUCTURE, ImpactDomain.ENERGY_GRID,
        "Cyber attack → SCADA/ICS compromise → grid instability",
        0.55, RT.INFRASTRUCTURE_DEP, 0.12, lag=4),

    # ── Capital Markets → downstream ─────────────────────────────────────
    _ch(ImpactDomain.CAPITAL_MARKETS, ImpactDomain.BANKING,
        "Market crash → bank trading losses / margin calls",
        0.65, RT.MARKET_CONTAGION, 0.15, lag=2),
    _ch(ImpactDomain.CAPITAL_MARKETS, ImpactDomain.INSURANCE,
        "Market volatility → investment portfolio losses",
        0.50, RT.RISK_TRANSFER, 0.18, lag=24),

    # ── Insurance → downstream ───────────────────────────────────────────
    _ch(ImpactDomain.INSURANCE, ImpactDomain.REAL_ESTATE,
        "Insurance market hardening → property development cost increase",
        0.45, RT.RISK_TRANSFER, 0.20, lag=168),

    # ── Real Estate → downstream ─────────────────────────────────────────
    _ch(ImpactDomain.REAL_ESTATE, ImpactDomain.BANKING,
        "Property value decline → mortgage NPL increase",
        0.70, RT.DIRECT_EXPOSURE, 0.15, lag=72),

    # ── Telecommunications → downstream ──────────────────────────────────
    _ch(ImpactDomain.TELECOMMUNICATIONS, ImpactDomain.BANKING,
        "Telecom outage → digital banking disruption",
        0.35, RT.INFRASTRUCTURE_DEP, 0.20, lag=2),

    # ── Aviation → downstream ────────────────────────────────────────────
    _ch(ImpactDomain.AVIATION, ImpactDomain.INSURANCE,
        "Aviation disruption → aviation insurance claims surge",
        0.55, RT.RISK_TRANSFER, 0.18, lag=24),
    _ch(ImpactDomain.AVIATION, ImpactDomain.TRADE_LOGISTICS,
        "Air cargo disruption → high-value goods supply chain stress",
        0.50, RT.SUPPLY_CHAIN, 0.18, lag=12),

    # ── Region-specific channels ─────────────────────────────────────────
    _ch(ImpactDomain.OIL_GAS, ImpactDomain.SOVEREIGN_FISCAL,
        "Bahrain oil dependency → acute fiscal vulnerability",
        0.95, RT.FISCAL_LINKAGE, 0.08, lag=12,
        regions=[GCCRegion.BAHRAIN]),
    _ch(ImpactDomain.MARITIME, ImpactDomain.TRADE_LOGISTICS,
        "Hormuz chokepoint → UAE/Oman port disruption",
        0.95, RT.SUPPLY_CHAIN, 0.05, lag=4,
        regions=[GCCRegion.UAE, GCCRegion.OMAN]),
]


# ── Lookup Indices ───────────────────────────────────────────────────────────

def _build_adjacency() -> dict[ImpactDomain, list[CausalChannel]]:
    """Build adjacency list: domain → outgoing channels."""
    adj: dict[ImpactDomain, list[CausalChannel]] = {}
    for ch in GCC_CAUSAL_CHANNELS:
        adj.setdefault(ch.from_domain, []).append(ch)
        if ch.bidirectional:
            adj.setdefault(ch.to_domain, []).append(ch)
    return adj


ADJACENCY: dict[ImpactDomain, list[CausalChannel]] = _build_adjacency()


def get_outgoing_channels(
    domain: ImpactDomain,
    region: GCCRegion | None = None,
) -> list[CausalChannel]:
    """Get all outgoing causal channels from a domain.

    If region is specified, only returns channels active in that region.
    GCC_WIDE channels are always included.
    """
    channels = ADJACENCY.get(domain, [])
    if region is None:
        return channels
    return [
        ch for ch in channels
        if GCCRegion.GCC_WIDE in ch.regions or region in ch.regions
    ]


def get_all_domains() -> set[ImpactDomain]:
    """Return all domains that participate in at least one channel."""
    domains: set[ImpactDomain] = set()
    for ch in GCC_CAUSAL_CHANNELS:
        domains.add(ch.from_domain)
        domains.add(ch.to_domain)
    return domains
