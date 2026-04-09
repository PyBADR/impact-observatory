"""Signal Intelligence Layer — Domain Engine.

Comprehensive ImpactDomain detection from free-form text hints.

Extends the basic keyword lookup in normalizer.py with:
  - Full domain coverage across all 12 ImpactDomains
  - Per-keyword match weights (0.0–1.0) reflecting specificity
  - Multi-domain support (a single hint can activate multiple domains)
  - Aggregate weight accumulation per domain for ranking
  - Coverage score and primary domain identification

Design rules:
  - Deterministic: same hints → same DomainMapping
  - No external state, no ML, no fuzzy matching
  - All text lowercased before matching
  - Longer/more specific patterns scored higher
  - Never raises; returns empty DomainMapping on failure

Public API:
  resolve_domains(hints: list[str]) -> DomainMapping
"""

from __future__ import annotations

import logging
from typing import NamedTuple

from src.macro.macro_enums import ImpactDomain
from src.signals.types import DomainMapping, DomainMatch

logger = logging.getLogger("signals.domain_engine")


# ── Domain Entry ──────────────────────────────────────────────────────────────

class _DomainEntry(NamedTuple):
    """A single keyword → domain mapping with match weight."""
    keyword: str
    domain: ImpactDomain
    weight: float   # 0.0–1.0; reflects keyword specificity


# ── Comprehensive Domain Keyword Table ────────────────────────────────────────
# Weight guide:
#   1.0  = exact brand/org name (Saudi Aramco, QatarEnergy)
#   0.90 = very specific compound phrase (crude oil, fiscal deficit)
#   0.80 = specific single-domain term (petroleum, hydrocarbon)
#   0.70 = recognisable domain term (refinery, pipeline)
#   0.60 = broad but commonly domain-specific (bank, trade)
#   0.50 = very broad / shared across domains (market, power)

_DOMAIN_TABLE: list[_DomainEntry] = [

    # ── Oil & Gas ──────────────────────────────────────────────────────────────
    _DomainEntry("petroleum development oman", ImpactDomain.OIL_GAS, 1.0),
    _DomainEntry("saudi aramco",               ImpactDomain.OIL_GAS, 1.0),
    _DomainEntry("qatarenergy",                ImpactDomain.OIL_GAS, 1.0),
    _DomainEntry("qatar energy",               ImpactDomain.OIL_GAS, 1.0),
    _DomainEntry("liquefied natural gas",      ImpactDomain.OIL_GAS, 0.95),
    _DomainEntry("oil production",             ImpactDomain.OIL_GAS, 0.90),
    _DomainEntry("oil refinery",               ImpactDomain.OIL_GAS, 0.90),
    _DomainEntry("oil embargo",                ImpactDomain.OIL_GAS, 0.90),
    _DomainEntry("oil export",                 ImpactDomain.OIL_GAS, 0.90),
    _DomainEntry("oil output",                 ImpactDomain.OIL_GAS, 0.90),
    _DomainEntry("oil price",                  ImpactDomain.OIL_GAS, 0.90),
    _DomainEntry("natural gas",                ImpactDomain.OIL_GAS, 0.90),
    _DomainEntry("crude oil",                  ImpactDomain.OIL_GAS, 0.90),
    _DomainEntry("gas pipeline",               ImpactDomain.OIL_GAS, 0.85),
    _DomainEntry("oil field",                  ImpactDomain.OIL_GAS, 0.85),
    _DomainEntry("opec+",                      ImpactDomain.OIL_GAS, 0.90),
    _DomainEntry("adnoc",                      ImpactDomain.OIL_GAS, 0.90),
    _DomainEntry("aramco",                     ImpactDomain.OIL_GAS, 0.90),
    _DomainEntry("lng",                        ImpactDomain.OIL_GAS, 0.85),
    _DomainEntry("opec",                       ImpactDomain.OIL_GAS, 0.85),
    _DomainEntry("brent",                      ImpactDomain.OIL_GAS, 0.80),
    _DomainEntry("wti",                        ImpactDomain.OIL_GAS, 0.80),
    _DomainEntry("petroleum",                  ImpactDomain.OIL_GAS, 0.80),
    _DomainEntry("hydrocarbon",                ImpactDomain.OIL_GAS, 0.80),
    _DomainEntry("refinery",                   ImpactDomain.OIL_GAS, 0.75),
    _DomainEntry("upstream",                   ImpactDomain.OIL_GAS, 0.65),
    _DomainEntry("downstream",                 ImpactDomain.OIL_GAS, 0.65),
    _DomainEntry("pipeline",                   ImpactDomain.OIL_GAS, 0.60),
    _DomainEntry("crude",                      ImpactDomain.OIL_GAS, 0.70),
    _DomainEntry("energy",                     ImpactDomain.OIL_GAS, 0.55),
    _DomainEntry("oil",                        ImpactDomain.OIL_GAS, 0.65),
    _DomainEntry("gas",                        ImpactDomain.OIL_GAS, 0.65),

    # ── Banking ───────────────────────────────────────────────────────────────
    _DomainEntry("capital adequacy",           ImpactDomain.BANKING, 0.90),
    _DomainEntry("non-performing loan",        ImpactDomain.BANKING, 0.90),
    _DomainEntry("investment bank",            ImpactDomain.BANKING, 0.90),
    _DomainEntry("commercial bank",            ImpactDomain.BANKING, 0.90),
    _DomainEntry("central bank",               ImpactDomain.BANKING, 0.90),
    _DomainEntry("banking sector",             ImpactDomain.BANKING, 0.90),
    _DomainEntry("sharia banking",             ImpactDomain.BANKING, 0.85),
    _DomainEntry("islamic finance",            ImpactDomain.BANKING, 0.85),
    _DomainEntry("monetary policy",            ImpactDomain.BANKING, 0.85),
    _DomainEntry("interest rate",              ImpactDomain.BANKING, 0.85),
    _DomainEntry("credit rating",              ImpactDomain.BANKING, 0.85),
    _DomainEntry("bank credit",                ImpactDomain.BANKING, 0.85),
    _DomainEntry("interbank",                  ImpactDomain.BANKING, 0.85),
    _DomainEntry("npl",                        ImpactDomain.BANKING, 0.80),
    _DomainEntry("basel",                      ImpactDomain.BANKING, 0.80),
    _DomainEntry("liquidity",                  ImpactDomain.BANKING, 0.75),
    _DomainEntry("lending",                    ImpactDomain.BANKING, 0.75),
    _DomainEntry("banking",                    ImpactDomain.BANKING, 0.70),
    _DomainEntry("deposit",                    ImpactDomain.BANKING, 0.70),
    _DomainEntry("fintech",                    ImpactDomain.BANKING, 0.70),
    _DomainEntry("loan",                       ImpactDomain.BANKING, 0.65),
    _DomainEntry("credit",                     ImpactDomain.BANKING, 0.60),
    _DomainEntry("bank",                       ImpactDomain.BANKING, 0.60),

    # ── Insurance ─────────────────────────────────────────────────────────────
    _DomainEntry("insurance premium",          ImpactDomain.INSURANCE, 0.90),
    _DomainEntry("insurance sector",           ImpactDomain.INSURANCE, 0.90),
    _DomainEntry("insurance claim",            ImpactDomain.INSURANCE, 0.85),
    _DomainEntry("reinsurance",                ImpactDomain.INSURANCE, 0.90),
    _DomainEntry("underwriting",               ImpactDomain.INSURANCE, 0.85),
    _DomainEntry("takaful",                    ImpactDomain.INSURANCE, 0.90),
    _DomainEntry("actuarial",                  ImpactDomain.INSURANCE, 0.80),
    _DomainEntry("insurer",                    ImpactDomain.INSURANCE, 0.80),
    _DomainEntry("insurance",                  ImpactDomain.INSURANCE, 0.75),

    # ── Trade & Logistics ─────────────────────────────────────────────────────
    _DomainEntry("trade disruption",           ImpactDomain.TRADE_LOGISTICS, 0.90),
    _DomainEntry("trade route",                ImpactDomain.TRADE_LOGISTICS, 0.90),
    _DomainEntry("trade war",                  ImpactDomain.TRADE_LOGISTICS, 0.90),
    _DomainEntry("import tariff",              ImpactDomain.TRADE_LOGISTICS, 0.85),
    _DomainEntry("export ban",                 ImpactDomain.TRADE_LOGISTICS, 0.85),
    _DomainEntry("port congestion",            ImpactDomain.TRADE_LOGISTICS, 0.85),
    _DomainEntry("supply chain",               ImpactDomain.TRADE_LOGISTICS, 0.90),
    _DomainEntry("free trade",                 ImpactDomain.TRADE_LOGISTICS, 0.80),
    _DomainEntry("logistics",                  ImpactDomain.TRADE_LOGISTICS, 0.80),
    _DomainEntry("freight",                    ImpactDomain.TRADE_LOGISTICS, 0.75),
    _DomainEntry("customs",                    ImpactDomain.TRADE_LOGISTICS, 0.70),
    _DomainEntry("tariff",                     ImpactDomain.TRADE_LOGISTICS, 0.75),
    _DomainEntry("export",                     ImpactDomain.TRADE_LOGISTICS, 0.60),
    _DomainEntry("import",                     ImpactDomain.TRADE_LOGISTICS, 0.60),
    _DomainEntry("trade",                      ImpactDomain.TRADE_LOGISTICS, 0.55),

    # ── Sovereign / Fiscal ────────────────────────────────────────────────────
    _DomainEntry("sovereign credit",           ImpactDomain.SOVEREIGN_FISCAL, 0.95),
    _DomainEntry("sovereign rating",           ImpactDomain.SOVEREIGN_FISCAL, 0.95),
    _DomainEntry("sovereign debt",             ImpactDomain.SOVEREIGN_FISCAL, 0.95),
    _DomainEntry("government budget",          ImpactDomain.SOVEREIGN_FISCAL, 0.90),
    _DomainEntry("government revenue",         ImpactDomain.SOVEREIGN_FISCAL, 0.85),
    _DomainEntry("fiscal deficit",             ImpactDomain.SOVEREIGN_FISCAL, 0.90),
    _DomainEntry("fiscal surplus",             ImpactDomain.SOVEREIGN_FISCAL, 0.90),
    _DomainEntry("fiscal policy",              ImpactDomain.SOVEREIGN_FISCAL, 0.85),
    _DomainEntry("budget deficit",             ImpactDomain.SOVEREIGN_FISCAL, 0.85),
    _DomainEntry("public spending",            ImpactDomain.SOVEREIGN_FISCAL, 0.85),
    _DomainEntry("national debt",              ImpactDomain.SOVEREIGN_FISCAL, 0.85),
    _DomainEntry("treasury bond",              ImpactDomain.SOVEREIGN_FISCAL, 0.85),
    _DomainEntry("sovereign",                  ImpactDomain.SOVEREIGN_FISCAL, 0.70),
    _DomainEntry("fiscal",                     ImpactDomain.SOVEREIGN_FISCAL, 0.70),
    _DomainEntry("treasury",                   ImpactDomain.SOVEREIGN_FISCAL, 0.65),
    _DomainEntry("budget",                     ImpactDomain.SOVEREIGN_FISCAL, 0.60),

    # ── Real Estate ───────────────────────────────────────────────────────────
    _DomainEntry("real estate market",         ImpactDomain.REAL_ESTATE, 0.90),
    _DomainEntry("property market",            ImpactDomain.REAL_ESTATE, 0.90),
    _DomainEntry("housing market",             ImpactDomain.REAL_ESTATE, 0.90),
    _DomainEntry("commercial property",        ImpactDomain.REAL_ESTATE, 0.90),
    _DomainEntry("residential property",       ImpactDomain.REAL_ESTATE, 0.90),
    _DomainEntry("property development",       ImpactDomain.REAL_ESTATE, 0.85),
    _DomainEntry("property price",             ImpactDomain.REAL_ESTATE, 0.85),
    _DomainEntry("real estate",                ImpactDomain.REAL_ESTATE, 0.85),
    _DomainEntry("mortgage",                   ImpactDomain.REAL_ESTATE, 0.80),
    _DomainEntry("construction",               ImpactDomain.REAL_ESTATE, 0.70),
    _DomainEntry("property",                   ImpactDomain.REAL_ESTATE, 0.65),

    # ── Telecommunications ────────────────────────────────────────────────────
    _DomainEntry("telecommunications",         ImpactDomain.TELECOMMUNICATIONS, 0.90),
    _DomainEntry("telecom sector",             ImpactDomain.TELECOMMUNICATIONS, 0.90),
    _DomainEntry("submarine cable",            ImpactDomain.TELECOMMUNICATIONS, 0.90),
    _DomainEntry("undersea cable",             ImpactDomain.TELECOMMUNICATIONS, 0.90),
    _DomainEntry("network outage",             ImpactDomain.TELECOMMUNICATIONS, 0.85),
    _DomainEntry("internet outage",            ImpactDomain.TELECOMMUNICATIONS, 0.85),
    _DomainEntry("mobile network",             ImpactDomain.TELECOMMUNICATIONS, 0.85),
    _DomainEntry("broadband",                  ImpactDomain.TELECOMMUNICATIONS, 0.80),
    _DomainEntry("telecom",                    ImpactDomain.TELECOMMUNICATIONS, 0.80),
    _DomainEntry("5g",                         ImpactDomain.TELECOMMUNICATIONS, 0.80),
    _DomainEntry("internet",                   ImpactDomain.TELECOMMUNICATIONS, 0.60),

    # ── Aviation ─────────────────────────────────────────────────────────────
    _DomainEntry("airspace closure",           ImpactDomain.AVIATION, 0.90),
    _DomainEntry("aviation sector",            ImpactDomain.AVIATION, 0.90),
    _DomainEntry("flight ban",                 ImpactDomain.AVIATION, 0.90),
    _DomainEntry("air travel",                 ImpactDomain.AVIATION, 0.85),
    _DomainEntry("airspace",                   ImpactDomain.AVIATION, 0.80),
    _DomainEntry("aviation",                   ImpactDomain.AVIATION, 0.85),
    _DomainEntry("aircraft",                   ImpactDomain.AVIATION, 0.75),
    _DomainEntry("airline",                    ImpactDomain.AVIATION, 0.85),
    _DomainEntry("airport",                    ImpactDomain.AVIATION, 0.80),
    _DomainEntry("flight",                     ImpactDomain.AVIATION, 0.55),

    # ── Maritime ─────────────────────────────────────────────────────────────
    _DomainEntry("strait of hormuz",           ImpactDomain.MARITIME, 0.95),
    _DomainEntry("bab al-mandeb",              ImpactDomain.MARITIME, 0.95),
    _DomainEntry("suez canal",                 ImpactDomain.MARITIME, 0.95),
    _DomainEntry("shipping disruption",        ImpactDomain.MARITIME, 0.90),
    _DomainEntry("maritime security",          ImpactDomain.MARITIME, 0.90),
    _DomainEntry("shipping lane",              ImpactDomain.MARITIME, 0.90),
    _DomainEntry("sea blockade",               ImpactDomain.MARITIME, 0.90),
    _DomainEntry("oil tanker",                 ImpactDomain.MARITIME, 0.90),
    _DomainEntry("chokepoint",                 ImpactDomain.MARITIME, 0.85),
    _DomainEntry("maritime",                   ImpactDomain.MARITIME, 0.85),
    _DomainEntry("tanker",                     ImpactDomain.MARITIME, 0.80),
    _DomainEntry("vessel",                     ImpactDomain.MARITIME, 0.75),
    _DomainEntry("shipping",                   ImpactDomain.MARITIME, 0.70),
    _DomainEntry("port",                       ImpactDomain.MARITIME, 0.60),

    # ── Energy Grid ───────────────────────────────────────────────────────────
    _DomainEntry("electricity grid",           ImpactDomain.ENERGY_GRID, 0.95),
    _DomainEntry("electricity supply",         ImpactDomain.ENERGY_GRID, 0.90),
    _DomainEntry("grid stability",             ImpactDomain.ENERGY_GRID, 0.90),
    _DomainEntry("power grid",                 ImpactDomain.ENERGY_GRID, 0.95),
    _DomainEntry("power outage",               ImpactDomain.ENERGY_GRID, 0.90),
    _DomainEntry("renewable energy",           ImpactDomain.ENERGY_GRID, 0.80),
    _DomainEntry("nuclear power",              ImpactDomain.ENERGY_GRID, 0.80),
    _DomainEntry("solar energy",               ImpactDomain.ENERGY_GRID, 0.75),
    _DomainEntry("electricity",                ImpactDomain.ENERGY_GRID, 0.70),
    _DomainEntry("utility",                    ImpactDomain.ENERGY_GRID, 0.65),
    _DomainEntry("grid",                       ImpactDomain.ENERGY_GRID, 0.60),
    _DomainEntry("power",                      ImpactDomain.ENERGY_GRID, 0.50),

    # ── Cyber Infrastructure ──────────────────────────────────────────────────
    _DomainEntry("critical infrastructure",    ImpactDomain.CYBER_INFRASTRUCTURE, 0.90),
    _DomainEntry("cyber attack",               ImpactDomain.CYBER_INFRASTRUCTURE, 0.95),
    _DomainEntry("cyber incident",             ImpactDomain.CYBER_INFRASTRUCTURE, 0.90),
    _DomainEntry("cyberattack",                ImpactDomain.CYBER_INFRASTRUCTURE, 0.95),
    _DomainEntry("data breach",                ImpactDomain.CYBER_INFRASTRUCTURE, 0.90),
    _DomainEntry("cybersecurity",              ImpactDomain.CYBER_INFRASTRUCTURE, 0.90),
    _DomainEntry("ransomware",                 ImpactDomain.CYBER_INFRASTRUCTURE, 0.95),
    _DomainEntry("malware",                    ImpactDomain.CYBER_INFRASTRUCTURE, 0.85),
    _DomainEntry("ddos",                       ImpactDomain.CYBER_INFRASTRUCTURE, 0.85),
    _DomainEntry("cyber",                      ImpactDomain.CYBER_INFRASTRUCTURE, 0.80),
    _DomainEntry("hack",                       ImpactDomain.CYBER_INFRASTRUCTURE, 0.75),

    # ── Capital Markets ───────────────────────────────────────────────────────
    _DomainEntry("capital market",             ImpactDomain.CAPITAL_MARKETS, 0.90),
    _DomainEntry("equity market",              ImpactDomain.CAPITAL_MARKETS, 0.90),
    _DomainEntry("stock exchange",             ImpactDomain.CAPITAL_MARKETS, 0.90),
    _DomainEntry("stock market",               ImpactDomain.CAPITAL_MARKETS, 0.90),
    _DomainEntry("bond market",                ImpactDomain.CAPITAL_MARKETS, 0.90),
    _DomainEntry("market crash",               ImpactDomain.CAPITAL_MARKETS, 0.90),
    _DomainEntry("market volatility",          ImpactDomain.CAPITAL_MARKETS, 0.85),
    _DomainEntry("sukuk",                      ImpactDomain.CAPITAL_MARKETS, 0.85),
    _DomainEntry("ipo",                        ImpactDomain.CAPITAL_MARKETS, 0.80),
    _DomainEntry("equity",                     ImpactDomain.CAPITAL_MARKETS, 0.75),
    _DomainEntry("bond",                       ImpactDomain.CAPITAL_MARKETS, 0.70),
    _DomainEntry("stock",                      ImpactDomain.CAPITAL_MARKETS, 0.65),
    _DomainEntry("market",                     ImpactDomain.CAPITAL_MARKETS, 0.45),
]

# Pre-sorted by keyword length descending so longer (more specific) patterns
# are evaluated first — improves accuracy for overlapping terms.
_SORTED_TABLE = sorted(_DOMAIN_TABLE, key=lambda e: len(e.keyword), reverse=True)


# ── Engine ────────────────────────────────────────────────────────────────────

def resolve_domains(hints: list[str]) -> DomainMapping:
    """Resolve free-form hint strings to a DomainMapping.

    Scans all hints against the comprehensive domain table. Multiple hints
    and multiple matching keywords accumulate weight for each domain.

    Args:
        hints: Combined sector_hints + category_hints (+ optional title) from SourceEvent.

    Returns:
        DomainMapping — always valid, never raises.
    """
    try:
        return _resolve(hints)
    except Exception as e:
        logger.warning("domain_engine.resolve_domains failed: %s", e)
        return DomainMapping()


def _resolve(hints: list[str]) -> DomainMapping:
    domain_weights: dict[str, float] = {}   # domain_value → accumulated weight
    domain_matches: list[DomainMatch] = []

    for hint in hints:
        lower = hint.lower().strip()
        if not lower:
            continue
        for entry in _SORTED_TABLE:
            if entry.keyword in lower:
                domain_val = entry.domain.value
                # Accumulate — each additional hit adds half its weight, capped at 1.0
                prev = domain_weights.get(domain_val, 0.0)
                increment = entry.weight if prev == 0.0 else entry.weight * 0.40
                domain_weights[domain_val] = min(1.0, prev + increment)
                domain_matches.append(DomainMatch(
                    domain_value=domain_val,
                    matched_keyword=entry.keyword,
                    matched_text=hint,
                    match_weight=entry.weight,
                ))

    if not domain_weights:
        return DomainMapping(
            matched_domains=[],
            domain_weights={},
            domain_matches=[],
            primary_domain=None,
            confidence=0.0,
        )

    # Sort by accumulated weight descending
    matched_domains = sorted(domain_weights.keys(), key=lambda d: domain_weights[d], reverse=True)
    primary_domain = matched_domains[0]

    # Confidence: based on top domain weight and total hit count
    top_weight = domain_weights[primary_domain]
    hit_count  = len(domain_matches)
    if hit_count >= 5:
        confidence = min(1.0, top_weight * 1.10)
    elif hit_count >= 3:
        confidence = top_weight
    else:
        confidence = top_weight * 0.85

    return DomainMapping(
        matched_domains=matched_domains,
        domain_weights={k: round(v, 4) for k, v in domain_weights.items()},
        domain_matches=domain_matches,
        primary_domain=primary_domain,
        confidence=round(confidence, 4),
    )
