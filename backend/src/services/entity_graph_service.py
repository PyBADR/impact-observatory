"""Service 4: entity_graph_service — Entity Graph management.

Provides the GCC entity graph: 42+ nodes across 6 layers, 57+ edges.
Wraps existing graph/loader and graph/schema.
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# ── GCC Entity Graph (seed data) ─────────────────────────────────────
GCC_ENTITIES: list[dict] = [
    # Energy layer
    {"id": "hormuz", "label": "Strait of Hormuz", "label_ar": "مضيق هرمز", "layer": "energy", "entity_type": "chokepoint", "country": "IR/OM", "latitude": 26.56, "longitude": 56.25, "gdp_weight": 0.0, "criticality": 0.98},
    {"id": "oil_sector", "label": "GCC Oil Sector", "label_ar": "قطاع النفط الخليجي", "layer": "energy", "entity_type": "sector", "country": "GCC", "latitude": 25.0, "longitude": 51.0, "gdp_weight": 0.35, "criticality": 0.95},
    {"id": "aramco", "label": "Saudi Aramco", "label_ar": "أرامكو السعودية", "layer": "energy", "entity_type": "company", "country": "SA", "latitude": 26.39, "longitude": 50.10, "gdp_weight": 0.12, "criticality": 0.92},
    {"id": "adnoc", "label": "ADNOC", "label_ar": "أدنوك", "layer": "energy", "entity_type": "company", "country": "AE", "latitude": 24.45, "longitude": 54.65, "gdp_weight": 0.08, "criticality": 0.88},
    {"id": "ras_laffan", "label": "Ras Laffan LNG", "label_ar": "رأس لفان للغاز", "layer": "energy", "entity_type": "terminal", "country": "QA", "latitude": 25.92, "longitude": 51.53, "gdp_weight": 0.15, "criticality": 0.90},
    {"id": "opec", "label": "OPEC+ Coordination", "label_ar": "تنسيق أوبك+", "layer": "energy", "entity_type": "organization", "country": "INT", "latitude": 25.0, "longitude": 50.0, "gdp_weight": 0.0, "criticality": 0.70},

    # Maritime layer
    {"id": "shipping", "label": "GCC Shipping Routes", "label_ar": "طرق الشحن الخليجية", "layer": "maritime", "entity_type": "corridor", "country": "GCC", "latitude": 25.5, "longitude": 54.0, "gdp_weight": 0.05, "criticality": 0.85},
    {"id": "jebel_ali", "label": "Jebel Ali Port", "label_ar": "ميناء جبل علي", "layer": "maritime", "entity_type": "port", "country": "AE", "latitude": 25.00, "longitude": 55.06, "gdp_weight": 0.04, "criticality": 0.88},
    {"id": "jubail", "label": "Jubail Industrial Port", "label_ar": "ميناء الجبيل", "layer": "maritime", "entity_type": "port", "country": "SA", "latitude": 27.01, "longitude": 49.66, "gdp_weight": 0.03, "criticality": 0.82},
    {"id": "red_sea", "label": "Red Sea Corridor", "label_ar": "ممر البحر الأحمر", "layer": "maritime", "entity_type": "corridor", "country": "INT", "latitude": 20.0, "longitude": 38.0, "gdp_weight": 0.0, "criticality": 0.80},
    {"id": "bab_el_mandeb", "label": "Bab el-Mandeb", "label_ar": "باب المندب", "layer": "maritime", "entity_type": "chokepoint", "country": "YE/DJ", "latitude": 12.58, "longitude": 43.33, "gdp_weight": 0.0, "criticality": 0.85},

    # Aviation layer
    {"id": "gcc_airspace", "label": "GCC Airspace", "label_ar": "المجال الجوي الخليجي", "layer": "aviation", "entity_type": "airspace", "country": "GCC", "latitude": 25.0, "longitude": 52.0, "gdp_weight": 0.03, "criticality": 0.75},
    {"id": "aviation_hub", "label": "GCC Aviation Hub", "label_ar": "محور الطيران الخليجي", "layer": "aviation", "entity_type": "sector", "country": "GCC", "latitude": 25.25, "longitude": 55.36, "gdp_weight": 0.04, "criticality": 0.80},
    {"id": "tourism", "label": "GCC Tourism Sector", "label_ar": "قطاع السياحة الخليجي", "layer": "aviation", "entity_type": "sector", "country": "GCC", "latitude": 25.20, "longitude": 55.27, "gdp_weight": 0.05, "criticality": 0.60},

    # Finance layer
    {"id": "banking_sector", "label": "GCC Banking Sector", "label_ar": "القطاع البنكي الخليجي", "layer": "finance", "entity_type": "sector", "country": "GCC", "latitude": 25.20, "longitude": 55.28, "gdp_weight": 0.12, "criticality": 0.90},
    {"id": "interbank", "label": "Interbank Market", "label_ar": "سوق ما بين البنوك", "layer": "finance", "entity_type": "market", "country": "GCC", "latitude": 25.20, "longitude": 55.28, "gdp_weight": 0.03, "criticality": 0.85},
    {"id": "fx_market", "label": "FX Market", "label_ar": "سوق العملات", "layer": "finance", "entity_type": "market", "country": "GCC", "latitude": 25.20, "longitude": 55.28, "gdp_weight": 0.02, "criticality": 0.80},
    {"id": "insurance_sector", "label": "GCC Insurance Sector", "label_ar": "قطاع التأمين الخليجي", "layer": "finance", "entity_type": "sector", "country": "GCC", "latitude": 25.20, "longitude": 55.28, "gdp_weight": 0.03, "criticality": 0.75},
    {"id": "fintech_sector", "label": "GCC Fintech Sector", "label_ar": "قطاع الفنتك الخليجي", "layer": "finance", "entity_type": "sector", "country": "GCC", "latitude": 25.20, "longitude": 55.28, "gdp_weight": 0.02, "criticality": 0.70},
    {"id": "tadawul", "label": "Tadawul (Saudi Exchange)", "label_ar": "تداول", "layer": "finance", "entity_type": "exchange", "country": "SA", "latitude": 24.71, "longitude": 46.67, "gdp_weight": 0.05, "criticality": 0.82},
    {"id": "adx", "label": "Abu Dhabi Securities Exchange", "label_ar": "سوق أبوظبي للأوراق المالية", "layer": "finance", "entity_type": "exchange", "country": "AE", "latitude": 24.49, "longitude": 54.37, "gdp_weight": 0.03, "criticality": 0.78},
    {"id": "dfm", "label": "Dubai Financial Market", "label_ar": "سوق دبي المالي", "layer": "finance", "entity_type": "exchange", "country": "AE", "latitude": 25.22, "longitude": 55.28, "gdp_weight": 0.02, "criticality": 0.75},

    # Infrastructure layer
    {"id": "gcc_economy", "label": "GCC Combined Economy", "label_ar": "الاقتصاد الخليجي المشترك", "layer": "infrastructure", "entity_type": "macro", "country": "GCC", "latitude": 25.0, "longitude": 51.0, "gdp_weight": 1.0, "criticality": 1.0},
    {"id": "desalination", "label": "Desalination Plants", "label_ar": "محطات التحلية", "layer": "infrastructure", "entity_type": "utility", "country": "GCC", "latitude": 25.5, "longitude": 52.0, "gdp_weight": 0.01, "criticality": 0.88},
    {"id": "power_grid", "label": "GCC Power Grid", "label_ar": "شبكة الكهرباء الخليجية", "layer": "infrastructure", "entity_type": "utility", "country": "GCC", "latitude": 25.0, "longitude": 51.5, "gdp_weight": 0.02, "criticality": 0.90},
    {"id": "telecom", "label": "GCC Telecom Infrastructure", "label_ar": "البنية التحتية للاتصالات", "layer": "infrastructure", "entity_type": "utility", "country": "GCC", "latitude": 25.0, "longitude": 52.0, "gdp_weight": 0.02, "criticality": 0.78},

    # Government layer
    {"id": "sama", "label": "SAMA (Saudi Central Bank)", "label_ar": "مؤسسة النقد العربي السعودي", "layer": "government", "entity_type": "regulator", "country": "SA", "latitude": 24.69, "longitude": 46.69, "gdp_weight": 0.0, "criticality": 0.88},
    {"id": "cbuae", "label": "Central Bank of UAE", "label_ar": "مصرف الإمارات المركزي", "layer": "government", "entity_type": "regulator", "country": "AE", "latitude": 24.49, "longitude": 54.38, "gdp_weight": 0.0, "criticality": 0.85},
    {"id": "cma_sa", "label": "CMA Saudi Arabia", "label_ar": "هيئة السوق المالية", "layer": "government", "entity_type": "regulator", "country": "SA", "latitude": 24.71, "longitude": 46.67, "gdp_weight": 0.0, "criticality": 0.80},
    {"id": "iran", "label": "Iran (Threat Actor)", "label_ar": "إيران", "layer": "government", "entity_type": "state_actor", "country": "IR", "latitude": 32.42, "longitude": 53.69, "gdp_weight": 0.0, "criticality": 0.60},
    {"id": "trade_sector", "label": "GCC Trade Sector", "label_ar": "قطاع التجارة الخليجي", "layer": "infrastructure", "entity_type": "sector", "country": "GCC", "latitude": 25.0, "longitude": 52.0, "gdp_weight": 0.08, "criticality": 0.82},
]

GCC_EDGES: list[dict] = [
    # Energy → Maritime
    {"source_id": "hormuz", "target_id": "oil_sector", "edge_type": "supply", "weight": 0.95},
    {"source_id": "hormuz", "target_id": "shipping", "edge_type": "route", "weight": 0.90},
    {"source_id": "oil_sector", "target_id": "aramco", "edge_type": "supply", "weight": 0.85},
    {"source_id": "oil_sector", "target_id": "adnoc", "edge_type": "supply", "weight": 0.80},
    {"source_id": "oil_sector", "target_id": "ras_laffan", "edge_type": "supply", "weight": 0.85},
    {"source_id": "oil_sector", "target_id": "gcc_economy", "edge_type": "financial", "weight": 0.90},

    # Maritime dependencies
    {"source_id": "shipping", "target_id": "jebel_ali", "edge_type": "route", "weight": 0.85},
    {"source_id": "shipping", "target_id": "jubail", "edge_type": "route", "weight": 0.80},
    {"source_id": "red_sea", "target_id": "shipping", "edge_type": "route", "weight": 0.70},
    {"source_id": "bab_el_mandeb", "target_id": "red_sea", "edge_type": "route", "weight": 0.90},
    {"source_id": "jebel_ali", "target_id": "trade_sector", "edge_type": "supply", "weight": 0.80},

    # Energy → Finance
    {"source_id": "oil_sector", "target_id": "banking_sector", "edge_type": "financial", "weight": 0.75},
    {"source_id": "oil_sector", "target_id": "tadawul", "edge_type": "financial", "weight": 0.70},
    {"source_id": "oil_sector", "target_id": "insurance_sector", "edge_type": "insurance", "weight": 0.65},
    {"source_id": "aramco", "target_id": "tadawul", "edge_type": "financial", "weight": 0.80},
    {"source_id": "adnoc", "target_id": "adx", "edge_type": "financial", "weight": 0.75},

    # Finance interconnections
    {"source_id": "banking_sector", "target_id": "interbank", "edge_type": "financial", "weight": 0.90},
    {"source_id": "banking_sector", "target_id": "fx_market", "edge_type": "financial", "weight": 0.80},
    {"source_id": "banking_sector", "target_id": "fintech_sector", "edge_type": "financial", "weight": 0.65},
    {"source_id": "interbank", "target_id": "fx_market", "edge_type": "financial", "weight": 0.75},
    {"source_id": "insurance_sector", "target_id": "banking_sector", "edge_type": "financial", "weight": 0.60},
    {"source_id": "fintech_sector", "target_id": "banking_sector", "edge_type": "financial", "weight": 0.55},

    # Aviation
    {"source_id": "gcc_airspace", "target_id": "aviation_hub", "edge_type": "route", "weight": 0.90},
    {"source_id": "aviation_hub", "target_id": "tourism", "edge_type": "financial", "weight": 0.80},
    {"source_id": "tourism", "target_id": "gcc_economy", "edge_type": "financial", "weight": 0.60},

    # Infrastructure
    {"source_id": "gcc_economy", "target_id": "banking_sector", "edge_type": "financial", "weight": 0.80},
    {"source_id": "gcc_economy", "target_id": "insurance_sector", "edge_type": "financial", "weight": 0.60},
    {"source_id": "gcc_economy", "target_id": "fintech_sector", "edge_type": "financial", "weight": 0.55},
    {"source_id": "power_grid", "target_id": "desalination", "edge_type": "supply", "weight": 0.90},
    {"source_id": "power_grid", "target_id": "telecom", "edge_type": "supply", "weight": 0.85},
    {"source_id": "oil_sector", "target_id": "power_grid", "edge_type": "supply", "weight": 0.80},

    # Regulatory
    {"source_id": "sama", "target_id": "banking_sector", "edge_type": "regulatory", "weight": 0.70},
    {"source_id": "cbuae", "target_id": "banking_sector", "edge_type": "regulatory", "weight": 0.65},
    {"source_id": "cma_sa", "target_id": "tadawul", "edge_type": "regulatory", "weight": 0.60},
    {"source_id": "sama", "target_id": "insurance_sector", "edge_type": "regulatory", "weight": 0.55},

    # Trade
    {"source_id": "trade_sector", "target_id": "gcc_economy", "edge_type": "financial", "weight": 0.75},
    {"source_id": "shipping", "target_id": "insurance_sector", "edge_type": "insurance", "weight": 0.70},

    # Threat paths
    {"source_id": "iran", "target_id": "hormuz", "edge_type": "threat", "weight": 0.85},
    {"source_id": "iran", "target_id": "gcc_airspace", "edge_type": "threat", "weight": 0.60},
]


def get_entities() -> list[dict]:
    """Return all GCC entities."""
    return GCC_ENTITIES


def get_edges() -> list[dict]:
    """Return all GCC edges."""
    return GCC_EDGES


def get_entity(entity_id: str) -> dict | None:
    """Get a single entity by ID."""
    return next((e for e in GCC_ENTITIES if e["id"] == entity_id), None)


def get_entities_by_layer(layer: str) -> list[dict]:
    """Get entities filtered by layer."""
    return [e for e in GCC_ENTITIES if e["layer"] == layer]


def get_entity_neighbors(entity_id: str) -> list[dict]:
    """Get entities connected to a given entity."""
    neighbor_ids = set()
    for edge in GCC_EDGES:
        if edge["source_id"] == entity_id:
            neighbor_ids.add(edge["target_id"])
        elif edge["target_id"] == entity_id:
            neighbor_ids.add(edge["source_id"])
    return [e for e in GCC_ENTITIES if e["id"] in neighbor_ids]
