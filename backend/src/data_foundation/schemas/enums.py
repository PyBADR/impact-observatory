"""
P1 Data Foundation — Shared Enumerations
=========================================

Single source of truth for all enum types used across the 14 P1 datasets.
Enum values use UPPER_SNAKE_CASE per project convention.
All enums inherit from (str, Enum) for JSON serialization.

Naming Convention:
  - GCC countries use ISO 3166-1 alpha-2 codes
  - Sectors align with Impact Observatory simulation_engine.py SECTOR_ALPHA keys
  - Severity levels align with URS thresholds from config.py
"""

from __future__ import annotations

from enum import Enum

__all__ = [
    "GCCCountry",
    "Sector",
    "EntityType",
    "DatasetPriority",
    "DatasetStatus",
    "IngestionFrequency",
    "SourceReliability",
    "SourceType",
    "SignalSeverity",
    "ConfidenceMethod",
    "Currency",
    "RiskLevel",
    "DecisionAction",
    "DecisionStatus",
    "EventCategory",
    "PortType",
    "TransportMode",
]


class GCCCountry(str, Enum):
    """GCC member states — ISO 3166-1 alpha-2."""
    SA = "SA"   # Saudi Arabia / المملكة العربية السعودية
    AE = "AE"   # United Arab Emirates / الإمارات العربية المتحدة
    KW = "KW"   # Kuwait / الكويت
    QA = "QA"   # Qatar / قطر
    BH = "BH"   # Bahrain / البحرين
    OM = "OM"   # Oman / عُمان


class Sector(str, Enum):
    """Sector classification — aligned with SECTOR_ALPHA in config.py."""
    ENERGY = "energy"
    MARITIME = "maritime"
    BANKING = "banking"
    INSURANCE = "insurance"
    FINTECH = "fintech"
    LOGISTICS = "logistics"
    INFRASTRUCTURE = "infrastructure"
    GOVERNMENT = "government"
    HEALTHCARE = "healthcare"
    REAL_ESTATE = "real_estate"
    TELECOM = "telecom"


class EntityType(str, Enum):
    """Classification of entities in the GCC economic graph."""
    COUNTRY = "country"
    REGULATOR = "regulator"
    CENTRAL_BANK = "central_bank"
    COMMERCIAL_BANK = "commercial_bank"
    INVESTMENT_BANK = "investment_bank"
    INSURER = "insurer"
    REINSURER = "reinsurer"
    INSURANCE_REGULATOR = "insurance_regulator"
    PORT = "port"
    AIRPORT = "airport"
    REFINERY = "refinery"
    OIL_FIELD = "oil_field"
    LNG_TERMINAL = "lng_terminal"
    PIPELINE = "pipeline"
    EXCHANGE = "exchange"
    SOVEREIGN_WEALTH_FUND = "sovereign_wealth_fund"
    MINISTRY = "ministry"
    FREE_ZONE = "free_zone"
    LOGISTICS_HUB = "logistics_hub"
    DATA_CENTER = "data_center"


class DatasetPriority(str, Enum):
    """Dataset build priority for phased delivery."""
    P1 = "P1"  # Phase 1 — core foundation
    P2 = "P2"  # Phase 2 — enrichment layer
    P3 = "P3"  # Phase 3 — advanced intelligence


class DatasetStatus(str, Enum):
    """Lifecycle status of a dataset definition."""
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    DEPRECATED = "DEPRECATED"
    ARCHIVED = "ARCHIVED"


class IngestionFrequency(str, Enum):
    """How often a dataset is refreshed from its source."""
    REAL_TIME = "REAL_TIME"       # Sub-second to seconds
    NEAR_REAL_TIME = "NEAR_RT"   # Minutes
    HOURLY = "HOURLY"
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    ON_DEMAND = "ON_DEMAND"      # Manual trigger
    STATIC = "STATIC"            # Seed data, rarely changes


class SourceReliability(str, Enum):
    """Reliability tier for data sources — drives confidence scoring."""
    AUTHORITATIVE = "AUTHORITATIVE"   # Government gazette, central bank, exchange filing
    HIGH = "HIGH"                     # Reuters, Bloomberg, ACLED
    MODERATE = "MODERATE"             # Industry reports, news wire
    LOW = "LOW"                       # Social media, unverified feeds
    EXPERIMENTAL = "EXPERIMENTAL"     # Internal models, prototype scrapers


class SourceType(str, Enum):
    """Classification of signal/data origin."""
    API = "API"
    WEBHOOK = "WEBHOOK"
    MANUAL = "MANUAL"
    SCRAPER = "SCRAPER"
    SENSOR = "SENSOR"
    SATELLITE = "SATELLITE"
    INTERNAL_MODEL = "INTERNAL_MODEL"
    FEED = "FEED"
    GOVERNMENT = "GOVERNMENT"
    RSS = "RSS"
    CSV_UPLOAD = "CSV_UPLOAD"
    DATABASE = "DATABASE"


class SignalSeverity(str, Enum):
    """Severity aligned with URS thresholds from config.py."""
    NOMINAL = "NOMINAL"       # URS < 0.20
    LOW = "LOW"               # URS 0.20–0.35
    GUARDED = "GUARDED"       # URS 0.35–0.50
    ELEVATED = "ELEVATED"     # URS 0.50–0.65
    HIGH = "HIGH"             # URS 0.65–0.80
    SEVERE = "SEVERE"         # URS ≥ 0.80


class ConfidenceMethod(str, Enum):
    """How the confidence score was determined."""
    SOURCE_DECLARED = "SOURCE_DECLARED"
    MODEL_COMPUTED = "MODEL_COMPUTED"
    RULE_BASED = "RULE_BASED"
    ANALYST_ASSIGNED = "ANALYST_ASSIGNED"
    MULTI_SOURCE_CORROBORATION = "MULTI_SOURCE_CORROBORATION"
    DEFAULT = "DEFAULT"


class Currency(str, Enum):
    """Currencies relevant to GCC macro intelligence."""
    SAR = "SAR"   # Saudi Riyal
    AED = "AED"   # UAE Dirham
    KWD = "KWD"   # Kuwaiti Dinar
    QAR = "QAR"   # Qatari Riyal
    BHD = "BHD"   # Bahraini Dinar
    OMR = "OMR"   # Omani Rial
    USD = "USD"   # US Dollar (peg reference)
    EUR = "EUR"   # Euro
    GBP = "GBP"   # British Pound
    CNY = "CNY"   # Chinese Yuan
    JPY = "JPY"   # Japanese Yen
    INR = "INR"   # Indian Rupee


class RiskLevel(str, Enum):
    """Risk classification for decision support."""
    NOMINAL = "NOMINAL"
    LOW = "LOW"
    GUARDED = "GUARDED"
    ELEVATED = "ELEVATED"
    HIGH = "HIGH"
    SEVERE = "SEVERE"
    CRITICAL = "CRITICAL"


class DecisionAction(str, Enum):
    """Action types for decision rules engine."""
    ALERT = "ALERT"
    ESCALATE = "ESCALATE"
    HEDGE = "HEDGE"
    REBALANCE = "REBALANCE"
    MONITOR = "MONITOR"
    PAUSE = "PAUSE"
    DIVEST = "DIVEST"
    INCREASE_RESERVES = "INCREASE_RESERVES"
    ACTIVATE_CONTINGENCY = "ACTIVATE_CONTINGENCY"
    NO_ACTION = "NO_ACTION"


class DecisionStatus(str, Enum):
    """Lifecycle of a decision log entry."""
    PROPOSED = "PROPOSED"
    APPROVED = "APPROVED"
    EXECUTED = "EXECUTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    SUPERSEDED = "SUPERSEDED"


class EventCategory(str, Enum):
    """Event classification for the event signals dataset."""
    GEOPOLITICAL = "GEOPOLITICAL"
    ECONOMIC = "ECONOMIC"
    REGULATORY = "REGULATORY"
    CYBER = "CYBER"
    CLIMATE = "CLIMATE"
    OPERATIONAL = "OPERATIONAL"
    MARKET = "MARKET"
    SANCTIONS = "SANCTIONS"
    CONFLICT = "CONFLICT"
    INFRASTRUCTURE = "INFRASTRUCTURE"


class PortType(str, Enum):
    """Classification of port/terminal nodes."""
    CONTAINER = "CONTAINER"
    BULK = "BULK"
    LNG = "LNG"
    OIL = "OIL"
    MULTI_PURPOSE = "MULTI_PURPOSE"
    DRY_DOCK = "DRY_DOCK"


class TransportMode(str, Enum):
    """Transport mode for logistics nodes."""
    MARITIME = "MARITIME"
    AIR = "AIR"
    ROAD = "ROAD"
    RAIL = "RAIL"
    PIPELINE = "PIPELINE"
    MULTIMODAL = "MULTIMODAL"
