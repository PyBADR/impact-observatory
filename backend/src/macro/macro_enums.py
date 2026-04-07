"""Macro Intelligence Layer — Shared Enumerations.

Every enum is the single source of truth for its domain.
No string literals allowed in engine code — use these enums.
"""

from enum import Enum


class SignalSource(str, Enum):
    """Origin classification of an incoming macro signal."""
    GEOPOLITICAL = "geopolitical"
    ECONOMIC = "economic"
    MARKET = "market"
    REGULATORY = "regulatory"
    CLIMATE = "climate"
    CYBER = "cyber"
    INFRASTRUCTURE = "infrastructure"
    SOCIAL = "social"
    ENERGY = "energy"
    TRADE = "trade"


class SignalType(str, Enum):
    """Canonical signal type taxonomy for the Macro Intelligence Layer.

    Distinct from SignalSource (which classifies origin).
    SignalType classifies the nature of the signal for downstream routing.

    Values align with Pack 1 domain contract requirements:
      geopolitical — state-level political or conflict events
      policy       — government policy, fiscal, monetary decisions
      market       — price, volatility, liquidity movements
      commodity    — commodity supply/demand or price shocks
      regulatory   — regulatory or compliance changes
      logistics    — supply chain, shipping, port disruptions
      sentiment    — sentiment or perception shifts
      systemic     — multi-sector systemic risk signals
    """
    GEOPOLITICAL = "geopolitical"
    POLICY       = "policy"
    MARKET       = "market"
    COMMODITY    = "commodity"
    REGULATORY   = "regulatory"
    LOGISTICS    = "logistics"
    SENTIMENT    = "sentiment"
    SYSTEMIC     = "systemic"


class SignalSeverity(str, Enum):
    """Severity classification aligned with URS risk levels."""
    NOMINAL = "nominal"       # < 0.20
    LOW = "low"               # 0.20 – 0.35
    GUARDED = "guarded"       # 0.35 – 0.50
    ELEVATED = "elevated"     # 0.50 – 0.65
    HIGH = "high"             # 0.65 – 0.80
    SEVERE = "severe"         # >= 0.80


class SignalDirection(str, Enum):
    """Directional impact of the signal on the target domain.

    POSITIVE  — signal is expected to have a positive/beneficial effect
    NEGATIVE  — signal is expected to have a negative/harmful effect
    NEUTRAL   — no material directional impact expected
    AMBIGUOUS — conflicting or unclear directional signals
    MIXED     — both positive and negative impacts simultaneously (e.g. sector-specific split)
    UNCERTAIN — insufficient information to determine direction
    """
    POSITIVE  = "positive"
    NEGATIVE  = "negative"
    NEUTRAL   = "neutral"
    AMBIGUOUS = "ambiguous"
    MIXED     = "mixed"
    UNCERTAIN = "uncertain"


class SignalConfidence(str, Enum):
    """Confidence level in the signal's accuracy and relevance."""
    VERIFIED = "verified"       # corroborated by multiple sources
    HIGH = "high"               # single authoritative source
    MODERATE = "moderate"       # credible but unconfirmed
    LOW = "low"                 # speculative / single unverified source
    UNVERIFIED = "unverified"   # raw intake, no validation yet


class GCCRegion(str, Enum):
    """GCC member states — the system's geographic scope."""
    SAUDI_ARABIA = "SA"
    UAE = "AE"
    QATAR = "QA"
    KUWAIT = "KW"
    BAHRAIN = "BH"
    OMAN = "OM"
    GCC_WIDE = "GCC"


class SignalStatus(str, Enum):
    """Lifecycle status of a signal in the registry."""
    RECEIVED = "received"         # just ingested
    VALIDATED = "validated"       # passed validation
    NORMALIZED = "normalized"     # normalization complete
    REGISTERED = "registered"     # in registry, ready for downstream
    REJECTED = "rejected"         # failed validation — dead end
    SUPERSEDED = "superseded"     # replaced by newer signal
    EXPIRED = "expired"           # TTL exceeded


class ImpactDomain(str, Enum):
    """Downstream domains a signal may affect. Maps to decision graph nodes."""
    OIL_GAS = "oil_gas"
    BANKING = "banking"
    INSURANCE = "insurance"
    TRADE_LOGISTICS = "trade_logistics"
    SOVEREIGN_FISCAL = "sovereign_fiscal"
    REAL_ESTATE = "real_estate"
    TELECOMMUNICATIONS = "telecommunications"
    AVIATION = "aviation"
    MARITIME = "maritime"
    ENERGY_GRID = "energy_grid"
    CYBER_INFRASTRUCTURE = "cyber_infrastructure"
    CAPITAL_MARKETS = "capital_markets"
