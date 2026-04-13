"""
Impact Observatory | مرصد الأثر — Phase 3 Entity Graph
Institutional entities that sit ABOVE the country-sector grid.

The Phase 1+2 graph has 36 nodes (6 countries × 6 sectors).
Phase 3 adds 7 *entity types*, each instantiated per-country where applicable,
forming an institutional overlay that modifies stress propagation.

Entity types:
  1. central_bank       — monetary authority, lender of last resort
  2. energy_producer    — national oil/gas company (ADNOC, Aramco, KPC, etc.)
  3. port_operator      — critical logistics node (DP World, Sohar, Hamad, etc.)
  4. reinsurance_layer  — catastrophe reinsurance and retrocession
  5. payment_rail       — RTGS / BUNA / cross-border settlement
  6. sovereign_buffer   — sovereign wealth fund / fiscal reserve
  7. real_estate_finance — state-backed developer + mortgage entity

Each entity:
  - Has a stress absorber capacity (how much it can cushion)
  - Connects to specific country-sector nodes via typed links
  - Can trigger escalation when its capacity is breached
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class EntityType(str, Enum):
    CENTRAL_BANK = "central_bank"
    ENERGY_PRODUCER = "energy_producer"
    PORT_OPERATOR = "port_operator"
    REINSURANCE_LAYER = "reinsurance_layer"
    PAYMENT_RAIL = "payment_rail"
    SOVEREIGN_BUFFER = "sovereign_buffer"
    REAL_ESTATE_FINANCE = "real_estate_finance"


@dataclass(slots=True)
class EntityNode:
    """An institutional entity in the GCC financial system."""
    entity_id: str                   # unique, e.g. "SAU:central_bank"
    entity_type: EntityType
    country_code: str
    name: str
    name_ar: str
    absorber_capacity: float         # 0–1: how much stress it can cushion
    current_utilization: float = 0.0 # how much of capacity is already used
    stress: float = 0.0             # entity-level stress after propagation
    breached: bool = False          # True if stress > absorber_capacity

    @property
    def remaining_capacity(self) -> float:
        return max(self.absorber_capacity - self.current_utilization, 0.0)


@dataclass(frozen=True, slots=True)
class EntityLink:
    """Typed connection from an entity to a country-sector node."""
    entity_id: str
    country_code: str
    sector_code: str
    link_type: str        # "absorbs", "amplifies", "triggers"
    weight: float         # strength of the link
    channel: str          # narrative label


# ═══════════════════════════════════════════════════════════════════════════════
# Entity Registry — all GCC institutional entities
# ═══════════════════════════════════════════════════════════════════════════════

def build_entity_registry() -> dict[str, EntityNode]:
    """Build the full institutional entity registry for all GCC states."""
    entities: dict[str, EntityNode] = {}

    # Per-country entity specifications
    SPECS: dict[str, list[tuple[EntityType, str, str, float]]] = {
        "KWT": [
            (EntityType.CENTRAL_BANK,      "Central Bank of Kuwait",          "بنك الكويت المركزي",          0.75),
            (EntityType.ENERGY_PRODUCER,    "Kuwait Petroleum Corporation",    "مؤسسة البترول الكويتية",      0.80),
            (EntityType.PORT_OPERATOR,      "Kuwait Ports Authority",          "هيئة الموانئ الكويتية",        0.50),
            (EntityType.REINSURANCE_LAYER,  "Kuwait Reinsurance Pool",         "مجمع إعادة التأمين الكويتي",   0.55),
            (EntityType.PAYMENT_RAIL,       "KNET Payment System",             "شبكة الكويت للدفع",           0.65),
            (EntityType.SOVEREIGN_BUFFER,   "Kuwait Investment Authority",     "الهيئة العامة للاستثمار",      0.90),
            (EntityType.REAL_ESTATE_FINANCE,"Kuwait Credit Bank",              "بنك الائتمان الكويتي",         0.45),
        ],
        "SAU": [
            (EntityType.CENTRAL_BANK,      "Saudi Central Bank (SAMA)",        "البنك المركزي السعودي",        0.85),
            (EntityType.ENERGY_PRODUCER,    "Saudi Aramco",                     "أرامكو السعودية",              0.90),
            (EntityType.PORT_OPERATOR,      "Saudi Ports Authority",            "الهيئة العامة للموانئ",         0.60),
            (EntityType.REINSURANCE_LAYER,  "Saudi Reinsurance Company",        "الشركة السعودية لإعادة التأمين", 0.55),
            (EntityType.PAYMENT_RAIL,       "Saudi Payments (mada/SARIE)",      "المدفوعات السعودية",            0.75),
            (EntityType.SOVEREIGN_BUFFER,   "Public Investment Fund",           "صندوق الاستثمارات العامة",      0.92),
            (EntityType.REAL_ESTATE_FINANCE,"Saudi Real Estate Refinance Co",   "شركة إعادة التمويل العقاري",    0.60),
        ],
        "UAE": [
            (EntityType.CENTRAL_BANK,      "Central Bank of the UAE",          "مصرف الإمارات المركزي",        0.80),
            (EntityType.ENERGY_PRODUCER,    "ADNOC",                            "أدنوك",                        0.85),
            (EntityType.PORT_OPERATOR,      "DP World / Abu Dhabi Ports",       "موانئ دبي العالمية",            0.70),
            (EntityType.REINSURANCE_LAYER,  "Dubai International Financial Centre Reinsurance", "مركز دبي المالي لإعادة التأمين", 0.65),
            (EntityType.PAYMENT_RAIL,       "UAE SWITCH / UAEFTS",              "نظام التحويلات الإماراتي",      0.72),
            (EntityType.SOVEREIGN_BUFFER,   "Abu Dhabi Investment Authority",   "جهاز أبوظبي للاستثمار",        0.88),
            (EntityType.REAL_ESTATE_FINANCE,"Arada / Emaar Development Finance","التمويل العقاري الإماراتي",     0.50),
        ],
        "QAT": [
            (EntityType.CENTRAL_BANK,      "Qatar Central Bank",               "مصرف قطر المركزي",             0.78),
            (EntityType.ENERGY_PRODUCER,    "QatarEnergy",                      "قطر للطاقة",                   0.88),
            (EntityType.PORT_OPERATOR,      "Hamad Port / QTerminals",          "ميناء حمد",                    0.60),
            (EntityType.REINSURANCE_LAYER,  "Qatar Reinsurance (Q Re)",         "قطر لإعادة التأمين",           0.58),
            (EntityType.PAYMENT_RAIL,       "Qatar National Payment System",    "نظام المدفوعات الوطني",        0.68),
            (EntityType.SOVEREIGN_BUFFER,   "Qatar Investment Authority",       "جهاز قطر للاستثمار",           0.90),
            (EntityType.REAL_ESTATE_FINANCE,"Barwa Real Estate Finance",        "بروة للتمويل العقاري",         0.48),
        ],
        "BHR": [
            (EntityType.CENTRAL_BANK,      "Central Bank of Bahrain",          "مصرف البحرين المركزي",         0.60),
            (EntityType.ENERGY_PRODUCER,    "BAPCO Energies",                   "بابكو للطاقة",                 0.55),
            (EntityType.PORT_OPERATOR,      "Khalifa Bin Salman Port",          "ميناء خليفة بن سلمان",         0.45),
            (EntityType.REINSURANCE_LAYER,  "Bahrain Reinsurance Pool",         "مجمع البحرين لإعادة التأمين",   0.40),
            (EntityType.PAYMENT_RAIL,       "BENEFIT Payment System",           "شركة بنفت",                    0.58),
            (EntityType.SOVEREIGN_BUFFER,   "Mumtalakat Holding",               "شركة ممتلكات القابضة",         0.45),
            (EntityType.REAL_ESTATE_FINANCE,"Bahrain Housing Ministry Fund",    "صندوق وزارة الإسكان",          0.35),
        ],
        "OMN": [
            (EntityType.CENTRAL_BANK,      "Central Bank of Oman",             "البنك المركزي العُماني",       0.62),
            (EntityType.ENERGY_PRODUCER,    "OQ Group (Oman Oil)",              "مجموعة أوكيو",                 0.70),
            (EntityType.PORT_OPERATOR,      "Sohar/Salalah Port Complex",       "مجمع موانئ صحار/صلالة",        0.55),
            (EntityType.REINSURANCE_LAYER,  "Oman Reinsurance Company",         "شركة عُمان لإعادة التأمين",    0.42),
            (EntityType.PAYMENT_RAIL,       "Oman Clearing Company",            "الشركة العُمانية للمقاصة",     0.55),
            (EntityType.SOVEREIGN_BUFFER,   "Oman Investment Authority",        "جهاز الاستثمار العُماني",      0.58),
            (EntityType.REAL_ESTATE_FINANCE,"Oman Housing Bank",                "بنك الإسكان العُماني",         0.38),
        ],
    }

    for cc, specs in SPECS.items():
        for etype, name, name_ar, capacity in specs:
            eid = f"{cc}:{etype.value}"
            entities[eid] = EntityNode(
                entity_id=eid,
                entity_type=etype,
                country_code=cc,
                name=name,
                name_ar=name_ar,
                absorber_capacity=capacity,
            )

    return entities


# ═══════════════════════════════════════════════════════════════════════════════
# Entity Links — how entities connect to the country-sector grid
# ═══════════════════════════════════════════════════════════════════════════════

def build_entity_links() -> list[EntityLink]:
    """Build typed links from entities to country-sector nodes."""
    links: list[EntityLink] = []

    LINK_TEMPLATES: list[tuple[EntityType, str, str, float, str]] = [
        # entity_type, sector, link_type, weight, channel
        (EntityType.CENTRAL_BANK,      "banking",      "absorbs",   0.60, "Emergency liquidity provision cushions banking stress"),
        (EntityType.CENTRAL_BANK,      "fintech",      "absorbs",   0.30, "Payment system backstop reduces fintech settlement risk"),
        (EntityType.CENTRAL_BANK,      "government",   "absorbs",   0.25, "Sovereign bond market support stabilizes fiscal funding"),
        (EntityType.ENERGY_PRODUCER,    "oil_gas",      "amplifies", 0.70, "National oil company revenue = fiscal revenue backbone"),
        (EntityType.ENERGY_PRODUCER,    "government",   "amplifies", 0.50, "Energy revenue shortfall directly reduces fiscal capacity"),
        (EntityType.PORT_OPERATOR,      "oil_gas",      "amplifies", 0.45, "Port disruption blocks energy export logistics"),
        (EntityType.PORT_OPERATOR,      "real_estate",  "amplifies", 0.25, "Construction material import delays"),
        (EntityType.REINSURANCE_LAYER,  "insurance",    "absorbs",   0.55, "Reinsurance treaty absorbs catastrophe claims"),
        (EntityType.REINSURANCE_LAYER,  "real_estate",  "absorbs",   0.20, "Construction surety bonds backstop developer defaults"),
        (EntityType.PAYMENT_RAIL,       "banking",      "amplifies", 0.35, "Settlement failure amplifies interbank stress"),
        (EntityType.PAYMENT_RAIL,       "fintech",      "amplifies", 0.50, "Payment rail disruption cascades through digital channels"),
        (EntityType.SOVEREIGN_BUFFER,   "government",   "absorbs",   0.80, "Sovereign wealth drawdown cushions fiscal shock"),
        (EntityType.SOVEREIGN_BUFFER,   "banking",      "absorbs",   0.35, "Sovereign fund capital injection stabilizes banking"),
        (EntityType.SOVEREIGN_BUFFER,   "real_estate",  "absorbs",   0.25, "State-backed development fund supports key projects"),
        (EntityType.REAL_ESTATE_FINANCE,"real_estate",  "absorbs",   0.50, "Mortgage refinance facility prevents foreclosure cascade"),
        (EntityType.REAL_ESTATE_FINANCE,"banking",      "amplifies", 0.40, "Real estate finance entity default cascades to banks"),
    ]

    for cc in COUNTRY_PROFILES:
        for etype, sector, link_type, weight, channel in LINK_TEMPLATES:
            eid = f"{cc}:{etype.value}"
            links.append(EntityLink(
                entity_id=eid,
                country_code=cc,
                sector_code=sector,
                link_type=link_type,
                weight=weight,
                channel=channel,
            ))

    return links


# Reuse COUNTRY_PROFILES from this module
from app.domain.simulation.country_sector_matrix import COUNTRY_PROFILES
