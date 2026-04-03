"""
Impact Observatory | مرصد الأثر
Simulation Engine v2.1.0 — pipeline orchestrator.

Executes 17 computational stages in sequence and returns the full
16-field output dict. Every run is deterministic for identical inputs.
"""
from __future__ import annotations

import time
from typing import Any

import numpy as np

from src.risk_models import (
    compute_event_severity,
    compute_sector_exposure,
    compute_propagation,
    compute_liquidity_stress,
    compute_insurance_stress,
    compute_financial_losses,
    compute_confidence_score,
    compute_unified_risk_score,
    classify_risk,
)
from src.physics_intelligence_layer import (
    compute_node_utilization,
    compute_bottleneck_scores,
    propagate_shock_wave,
    compute_congestion,
    compute_recovery_trajectory,
    check_flow_conservation,
    PhysicsViolationError,
)
from src.flow_models import simulate_all_flows
from src.decision_layer import (
    build_decision_actions,
    build_five_questions,
    compute_escalation_triggers,
    compute_monitoring_priorities,
)
from src.explainability import (
    build_causal_chain,
    build_narrative,
    compute_sensitivity,
    compute_uncertainty_bands,
)
from src.utils import (
    clamp,
    generate_run_id,
    now_utc,
    format_loss_usd,
    classify_stress,
)

# ---------------------------------------------------------------------------
# GCC Node Registry — 42 nodes
# ---------------------------------------------------------------------------

GCC_NODES: list[dict] = [
    # ── Maritime / Chokepoints ────────────────────────────────────────────
    {"id": "hormuz",            "label": "Strait of Hormuz",           "label_ar": "مضيق هرمز",
     "sector": "maritime",      "capacity": 21_000_000,  "current_load": 0.82,
     "criticality": 1.00,       "redundancy": 0.05,      "lat": 26.59, "lng": 56.26},
    {"id": "shipping_lanes",    "label": "GCC Shipping Lanes",          "label_ar": "ممرات الشحن الخليجية",
     "sector": "maritime",      "capacity": 18_000_000,  "current_load": 0.76,
     "criticality": 0.92,       "redundancy": 0.15,      "lat": 25.00, "lng": 57.00},
    {"id": "dubai_port",        "label": "Jebel Ali Port (Dubai)",      "label_ar": "ميناء جبل علي",
     "sector": "maritime",      "capacity": 22_000_000,  "current_load": 0.73,
     "criticality": 0.90,       "redundancy": 0.20,      "lat": 24.98, "lng": 55.06},
    {"id": "abu_dhabi_port",    "label": "Khalifa Port (Abu Dhabi)",    "label_ar": "ميناء خليفة",
     "sector": "maritime",      "capacity": 8_500_000,   "current_load": 0.68,
     "criticality": 0.78,       "redundancy": 0.25,      "lat": 24.78, "lng": 54.64},
    {"id": "dammam_port",       "label": "King Abdul Aziz Port",        "label_ar": "ميناء الملك عبدالعزيز",
     "sector": "maritime",      "capacity": 6_000_000,   "current_load": 0.65,
     "criticality": 0.72,       "redundancy": 0.28,      "lat": 26.43, "lng": 50.10},
    {"id": "salalah_port",      "label": "Port of Salalah (Oman)",      "label_ar": "ميناء صلالة",
     "sector": "maritime",      "capacity": 4_500_000,   "current_load": 0.58,
     "criticality": 0.65,       "redundancy": 0.40,      "lat": 16.94, "lng": 54.00},
    {"id": "kuwait_port",       "label": "Shuwaikh / Shuaiba Port",     "label_ar": "ميناء الشويخ / الشعيبة",
     "sector": "maritime",      "capacity": 3_200_000,   "current_load": 0.60,
     "criticality": 0.62,       "redundancy": 0.35,      "lat": 29.37, "lng": 47.96},

    # ── Energy ────────────────────────────────────────────────────────────
    {"id": "qatar_lng",         "label": "Qatar LNG Facilities",        "label_ar": "منشآت LNG القطرية",
     "sector": "energy",        "capacity": 77_000_000,  "current_load": 0.88,
     "criticality": 0.96,       "redundancy": 0.12,      "lat": 25.28, "lng": 51.52},
    {"id": "saudi_aramco",      "label": "Saudi Aramco Operations",     "label_ar": "عمليات أرامكو السعودية",
     "sector": "energy",        "capacity": 12_000_000,  "current_load": 0.85,
     "criticality": 0.98,       "redundancy": 0.18,      "lat": 26.33, "lng": 50.15},
    {"id": "adnoc",             "label": "ADNOC Operations (UAE)",       "label_ar": "عمليات أدنوك",
     "sector": "energy",        "capacity": 4_000_000,   "current_load": 0.80,
     "criticality": 0.88,       "redundancy": 0.22,      "lat": 24.47, "lng": 54.37},
    {"id": "kuwait_oil",        "label": "Kuwait Petroleum Corp",        "label_ar": "مؤسسة البترول الكويتية",
     "sector": "energy",        "capacity": 2_700_000,   "current_load": 0.78,
     "criticality": 0.82,       "redundancy": 0.20,      "lat": 29.37, "lng": 47.97},
    {"id": "gcc_pipeline",      "label": "GCC Petrochemical Pipeline",   "label_ar": "خط أنابيب البتروكيماويات الخليجي",
     "sector": "energy",        "capacity": 5_000_000,   "current_load": 0.70,
     "criticality": 0.85,       "redundancy": 0.25,      "lat": 26.00, "lng": 50.55},
    {"id": "oman_oil",          "label": "Oman Oil & Gas Operations",    "label_ar": "عمليات النفط والغاز العُمانية",
     "sector": "energy",        "capacity": 1_050_000,   "current_load": 0.74,
     "criticality": 0.70,       "redundancy": 0.30,      "lat": 23.59, "lng": 58.40},

    # ── Banking ───────────────────────────────────────────────────────────
    {"id": "uae_banking",       "label": "UAE Banking Sector",           "label_ar": "القطاع المصرفي الإماراتي",
     "sector": "banking",       "capacity": 1_050_000_000_000, "current_load": 0.62,
     "criticality": 0.92,       "redundancy": 0.35,      "lat": 25.20, "lng": 55.27},
    {"id": "saudi_banking",     "label": "Saudi Banking Sector",         "label_ar": "القطاع المصرفي السعودي",
     "sector": "banking",       "capacity": 870_000_000_000,  "current_load": 0.65,
     "criticality": 0.90,       "redundancy": 0.38,      "lat": 24.69, "lng": 46.72},
    {"id": "riyadh_financial",  "label": "Riyadh Financial District",    "label_ar": "مركز الرياض المالي",
     "sector": "banking",       "capacity": 320_000_000_000,  "current_load": 0.68,
     "criticality": 0.88,       "redundancy": 0.32,      "lat": 24.69, "lng": 46.72},
    {"id": "bahrain_banking",   "label": "Bahrain Financial Harbour",    "label_ar": "مرسى البحرين المالي",
     "sector": "banking",       "capacity": 190_000_000_000,  "current_load": 0.70,
     "criticality": 0.80,       "redundancy": 0.30,      "lat": 26.21, "lng": 50.59},
    {"id": "kuwait_banking",    "label": "Kuwait Banking Sector",        "label_ar": "القطاع المصرفي الكويتي",
     "sector": "banking",       "capacity": 150_000_000_000,  "current_load": 0.64,
     "criticality": 0.75,       "redundancy": 0.35,      "lat": 29.37, "lng": 47.97},
    {"id": "qatar_banking",     "label": "Qatar Banking Sector",         "label_ar": "القطاع المصرفي القطري",
     "sector": "banking",       "capacity": 420_000_000_000,  "current_load": 0.67,
     "criticality": 0.82,       "redundancy": 0.33,      "lat": 25.29, "lng": 51.53},
    {"id": "difc",              "label": "DIFC (Dubai Int'l Finance Ctr)","label_ar": "مركز دبي المالي الدولي",
     "sector": "banking",       "capacity": 500_000_000_000,  "current_load": 0.72,
     "criticality": 0.93,       "redundancy": 0.30,      "lat": 25.21, "lng": 55.28},

    # ── Insurance ─────────────────────────────────────────────────────────
    {"id": "gcc_insurance",     "label": "GCC Insurance Market",         "label_ar": "سوق التأمين الخليجي",
     "sector": "insurance",     "capacity": 25_000_000_000,  "current_load": 0.58,
     "criticality": 0.78,       "redundancy": 0.40,      "lat": 25.20, "lng": 55.27},
    {"id": "reinsurance_hub",   "label": "GCC Reinsurance Hub",          "label_ar": "مركز إعادة التأمين الخليجي",
     "sector": "insurance",     "capacity": 8_000_000_000,   "current_load": 0.52,
     "criticality": 0.72,       "redundancy": 0.45,      "lat": 26.21, "lng": 50.59},

    # ── Fintech / Payments ────────────────────────────────────────────────
    {"id": "gcc_fintech",       "label": "GCC Fintech Ecosystem",        "label_ar": "منظومة التقنية المالية الخليجية",
     "sector": "fintech",       "capacity": 500_000_000_000, "current_load": 0.60,
     "criticality": 0.82,       "redundancy": 0.38,      "lat": 25.20, "lng": 55.27},
    {"id": "uae_payment_rail",  "label": "UAE Payment Rails (AANI)",     "label_ar": "شبكة المدفوعات الإماراتية",
     "sector": "fintech",       "capacity": 200_000_000_000, "current_load": 0.65,
     "criticality": 0.85,       "redundancy": 0.35,      "lat": 24.47, "lng": 54.37},
    {"id": "saudi_payment_rail","label": "Saudi Payment Network (mada)", "label_ar": "شبكة مدى السعودية",
     "sector": "fintech",       "capacity": 280_000_000_000, "current_load": 0.68,
     "criticality": 0.84,       "redundancy": 0.32,      "lat": 24.69, "lng": 46.72},
    {"id": "swift_gcc",         "label": "SWIFT GCC Node",               "label_ar": "عقدة SWIFT الخليجية",
     "sector": "fintech",       "capacity": 800_000_000_000, "current_load": 0.70,
     "criticality": 0.90,       "redundancy": 0.25,      "lat": 25.20, "lng": 55.27},

    # ── Logistics ─────────────────────────────────────────────────────────
    {"id": "dubai_logistics",   "label": "Dubai Logistics Corridor",     "label_ar": "ممر دبي اللوجستي",
     "sector": "logistics",     "capacity": 80_000_000,  "current_load": 0.72,
     "criticality": 0.82,       "redundancy": 0.30,      "lat": 25.07, "lng": 55.14},
    {"id": "riyadh_logistics",  "label": "Riyadh Dry Port & Logistics",  "label_ar": "ميناء الرياض الجاف",
     "sector": "logistics",     "capacity": 45_000_000,  "current_load": 0.65,
     "criticality": 0.72,       "redundancy": 0.35,      "lat": 24.63, "lng": 46.71},
    {"id": "oman_trade",        "label": "Oman Trade Infrastructure",    "label_ar": "البنية التجارية العُمانية",
     "sector": "logistics",     "capacity": 20_000_000,  "current_load": 0.60,
     "criticality": 0.65,       "redundancy": 0.40,      "lat": 23.61, "lng": 58.59},

    # ── Infrastructure ────────────────────────────────────────────────────
    {"id": "gcc_power_grid",    "label": "GCC Interconnected Power Grid","label_ar": "الشبكة الكهربائية الخليجية المترابطة",
     "sector": "infrastructure","capacity": 100_000,     "current_load": 0.77,
     "criticality": 0.88,       "redundancy": 0.28,      "lat": 26.00, "lng": 50.00},
    {"id": "uae_telecom",       "label": "UAE Telecom Infrastructure",   "label_ar": "بنية الاتصالات الإماراتية",
     "sector": "infrastructure","capacity": 50_000,      "current_load": 0.70,
     "criticality": 0.80,       "redundancy": 0.35,      "lat": 25.20, "lng": 55.27},
    {"id": "saudi_telecom",     "label": "Saudi Telecom Infrastructure", "label_ar": "بنية الاتصالات السعودية",
     "sector": "infrastructure","capacity": 75_000,      "current_load": 0.72,
     "criticality": 0.82,       "redundancy": 0.33,      "lat": 24.69, "lng": 46.72},
    {"id": "gcc_water_desalin", "label": "GCC Desalination Network",     "label_ar": "شبكة التحلية الخليجية",
     "sector": "infrastructure","capacity": 15_000,      "current_load": 0.80,
     "criticality": 0.87,       "redundancy": 0.22,      "lat": 26.00, "lng": 50.50},

    # ── Government / Regulatory ───────────────────────────────────────────
    {"id": "uae_cbuae",         "label": "Central Bank of UAE",          "label_ar": "المصرف المركزي الإماراتي",
     "sector": "government",    "capacity": 1,           "current_load": 0.50,
     "criticality": 0.95,       "redundancy": 0.50,      "lat": 24.47, "lng": 54.37},
    {"id": "sama",              "label": "Saudi Central Bank (SAMA)",    "label_ar": "مؤسسة النقد العربي السعودي",
     "sector": "government",    "capacity": 1,           "current_load": 0.50,
     "criticality": 0.95,       "redundancy": 0.50,      "lat": 24.69, "lng": 46.72},
    {"id": "qcb",               "label": "Qatar Central Bank",           "label_ar": "مصرف قطر المركزي",
     "sector": "government",    "capacity": 1,           "current_load": 0.50,
     "criticality": 0.88,       "redundancy": 0.50,      "lat": 25.29, "lng": 51.53},
    {"id": "cbk",               "label": "Central Bank of Kuwait",       "label_ar": "بنك الكويت المركزي",
     "sector": "government",    "capacity": 1,           "current_load": 0.50,
     "criticality": 0.85,       "redundancy": 0.50,      "lat": 29.37, "lng": 47.97},
    {"id": "cbo",               "label": "Central Bank of Oman",         "label_ar": "البنك المركزي العُماني",
     "sector": "government",    "capacity": 1,           "current_load": 0.50,
     "criticality": 0.82,       "redundancy": 0.50,      "lat": 23.59, "lng": 58.59},
    {"id": "gcc_fsb",           "label": "GCC Financial Stability Board","label_ar": "مجلس الاستقرار المالي الخليجي",
     "sector": "government",    "capacity": 1,           "current_load": 0.45,
     "criticality": 0.90,       "redundancy": 0.55,      "lat": 26.21, "lng": 50.59},

    # ── Society / Labour ──────────────────────────────────────────────────
    {"id": "gcc_labour_market", "label": "GCC Labour Market",            "label_ar": "سوق العمل الخليجي",
     "sector": "healthcare",    "capacity": 30_000_000,  "current_load": 0.55,
     "criticality": 0.60,       "redundancy": 0.45,      "lat": 25.50, "lng": 51.00},
    {"id": "gcc_healthcare",    "label": "GCC Healthcare Infrastructure","label_ar": "بنية الرعاية الصحية الخليجية",
     "sector": "healthcare",    "capacity": 200_000,     "current_load": 0.68,
     "criticality": 0.72,       "redundancy": 0.38,      "lat": 25.50, "lng": 51.00},
    {"id": "uae_real_estate",   "label": "UAE Real Estate Market",       "label_ar": "سوق العقارات الإماراتي",
     "sector": "infrastructure","capacity": 350_000_000_000,"current_load": 0.60,
     "criticality": 0.65,       "redundancy": 0.50,      "lat": 25.20, "lng": 55.27},
    {"id": "saudi_sovereign_fund","label":"Saudi PIF (Sovereign Wealth)","label_ar": "صندوق الاستثمارات العامة السعودي",
     "sector": "government",    "capacity": 700_000_000_000,"current_load": 0.55,
     "criticality": 0.85,       "redundancy": 0.55,      "lat": 24.69, "lng": 46.72},
]

# ---------------------------------------------------------------------------
# GCC Adjacency Graph
# ---------------------------------------------------------------------------

GCC_ADJACENCY: dict[str, list[str]] = {
    "hormuz": [
        "shipping_lanes", "qatar_lng", "dubai_port", "abu_dhabi_port",
        "dammam_port", "kuwait_port", "uae_banking", "saudi_aramco",
    ],
    "shipping_lanes": [
        "hormuz", "dubai_port", "salalah_port", "abu_dhabi_port",
        "dubai_logistics", "gcc_insurance",
    ],
    "dubai_port": [
        "shipping_lanes", "hormuz", "dubai_logistics", "uae_banking",
        "gcc_fintech", "uae_payment_rail", "gcc_insurance",
    ],
    "abu_dhabi_port": [
        "hormuz", "adnoc", "uae_banking", "uae_cbuae", "gcc_power_grid",
    ],
    "dammam_port": [
        "hormuz", "saudi_aramco", "riyadh_logistics", "saudi_banking",
        "same", "riyadh_financial",
    ],
    "salalah_port": [
        "shipping_lanes", "oman_oil", "oman_trade", "cbo",
    ],
    "kuwait_port": [
        "hormuz", "kuwait_oil", "kuwait_banking", "cbk",
    ],
    "qatar_lng": [
        "hormuz", "qatar_banking", "qcb", "gcc_insurance",
        "shipping_lanes", "gcc_power_grid",
    ],
    "saudi_aramco": [
        "dammam_port", "hormuz", "gcc_pipeline", "saudi_banking",
        "sama", "riyadh_financial", "gcc_power_grid",
    ],
    "adnoc": [
        "abu_dhabi_port", "uae_banking", "uae_cbuae", "gcc_pipeline",
        "gcc_power_grid",
    ],
    "kuwait_oil": [
        "kuwait_port", "kuwait_banking", "cbk", "gcc_pipeline",
    ],
    "gcc_pipeline": [
        "saudi_aramco", "adnoc", "kuwait_oil", "oman_oil",
        "gcc_power_grid",
    ],
    "oman_oil": [
        "salalah_port", "oman_trade", "cbo", "gcc_pipeline",
    ],
    "uae_banking": [
        "difc", "uae_cbuae", "dubai_port", "gcc_fintech",
        "swift_gcc", "gcc_insurance", "uae_payment_rail",
    ],
    "saudi_banking": [
        "sama", "riyadh_financial", "saudi_payment_rail",
        "gcc_insurance", "swift_gcc",
    ],
    "riyadh_financial": [
        "saudi_banking", "sama", "saudi_sovereign_fund",
        "swift_gcc", "saudi_telecom",
    ],
    "bahrain_banking": [
        "gcc_fsb", "reinsurance_hub", "swift_gcc", "gcc_insurance",
    ],
    "kuwait_banking": [
        "cbk", "swift_gcc", "gcc_insurance",
    ],
    "qatar_banking": [
        "qcb", "swift_gcc", "gcc_insurance", "qatar_lng",
    ],
    "difc": [
        "uae_banking", "gcc_fintech", "swift_gcc",
        "gcc_insurance", "reinsurance_hub",
    ],
    "gcc_insurance": [
        "reinsurance_hub", "uae_banking", "saudi_banking",
        "gcc_fintech", "dubai_port",
    ],
    "reinsurance_hub": [
        "gcc_insurance", "bahrain_banking", "difc",
    ],
    "gcc_fintech": [
        "uae_payment_rail", "saudi_payment_rail", "swift_gcc",
        "uae_banking", "saudi_banking",
    ],
    "uae_payment_rail": [
        "gcc_fintech", "uae_banking", "uae_cbuae", "swift_gcc",
    ],
    "saudi_payment_rail": [
        "gcc_fintech", "saudi_banking", "sama", "swift_gcc",
    ],
    "swift_gcc": [
        "uae_banking", "saudi_banking", "qatar_banking",
        "bahrain_banking", "kuwait_banking", "gcc_fintech",
    ],
    "dubai_logistics": [
        "dubai_port", "riyadh_logistics", "gcc_power_grid",
        "uae_telecom",
    ],
    "riyadh_logistics": [
        "dammam_port", "dubai_logistics", "saudi_telecom",
    ],
    "oman_trade": [
        "salalah_port", "oman_oil", "cbo",
    ],
    "gcc_power_grid": [
        "saudi_aramco", "adnoc", "qatar_lng", "gcc_water_desalin",
        "uae_telecom", "saudi_telecom",
    ],
    "uae_telecom": [
        "gcc_power_grid", "dubai_logistics", "uae_banking",
        "gcc_fintech",
    ],
    "saudi_telecom": [
        "gcc_power_grid", "riyadh_logistics", "saudi_banking",
        "riyadh_financial",
    ],
    "gcc_water_desalin": [
        "gcc_power_grid", "gcc_labour_market",
    ],
    "uae_cbuae": [
        "uae_banking", "uae_payment_rail", "gcc_fsb",
    ],
    "sama": [
        "saudi_banking", "saudi_payment_rail", "gcc_fsb",
        "riyadh_financial",
    ],
    "qcb": [
        "qatar_banking", "gcc_fsb",
    ],
    "cbk": [
        "kuwait_banking", "gcc_fsb",
    ],
    "cbo": [
        "oman_trade", "gcc_fsb",
    ],
    "gcc_fsb": [
        "uae_cbuae", "sama", "qcb", "cbk", "cbo",
        "bahrain_banking", "gcc_insurance",
    ],
    "gcc_labour_market": [
        "gcc_water_desalin", "gcc_healthcare", "uae_real_estate",
    ],
    "gcc_healthcare": [
        "gcc_labour_market", "gcc_power_grid",
    ],
    "uae_real_estate": [
        "uae_banking", "gcc_labour_market", "difc",
    ],
    "saudi_sovereign_fund": [
        "riyadh_financial", "sama", "gcc_fsb",
    ],
    # Fix forward reference in dammam_port
    "same": [],  # placeholder — cleaned below
}

# Remove placeholder key
GCC_ADJACENCY.pop("same", None)
# Fix the dammam_port entry that referenced "same" by mistake
GCC_ADJACENCY["dammam_port"] = [
    "hormuz", "saudi_aramco", "riyadh_logistics", "saudi_banking",
    "sama", "riyadh_financial",
]

# ---------------------------------------------------------------------------
# Scenario Catalog — 15 scenarios (8 canonical + 7 extended)
# ---------------------------------------------------------------------------

SCENARIO_CATALOG: dict[str, dict] = {
    # ── Canonical ────────────────────────────────────────────────────────
    "hormuz_chokepoint_disruption": {
        "id": "hormuz_chokepoint_disruption",
        "name": "Strait of Hormuz Disruption",
        "name_ar": "اضطراب مضيق هرمز",
        "shock_nodes": ["hormuz", "shipping_lanes"],
        "base_loss_usd": 3_200_000_000,
        "peak_day_offset": 3,
        "recovery_base_days": 21,
        "sectors_affected": ["energy", "maritime", "banking", "insurance", "fintech"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "uae_banking_crisis": {
        "id": "uae_banking_crisis",
        "name": "UAE Banking System Stress",
        "name_ar": "ضغط النظام المصرفي الإماراتي",
        "shock_nodes": ["uae_banking", "difc"],
        "base_loss_usd": 1_800_000_000,
        "peak_day_offset": 5,
        "recovery_base_days": 14,
        "sectors_affected": ["banking", "fintech", "insurance", "government"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "gcc_cyber_attack": {
        "id": "gcc_cyber_attack",
        "name": "GCC Critical Infrastructure Cyber Attack",
        "name_ar": "هجوم إلكتروني على البنية التحتية الحيوية الخليجية",
        "shock_nodes": ["swift_gcc", "uae_payment_rail", "saudi_payment_rail"],
        "base_loss_usd": 950_000_000,
        "peak_day_offset": 1,
        "recovery_base_days": 7,
        "sectors_affected": ["fintech", "banking", "infrastructure", "government"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "saudi_oil_shock": {
        "id": "saudi_oil_shock",
        "name": "Saudi Arabia Oil Supply Shock",
        "name_ar": "صدمة إمدادات النفط السعودية",
        "shock_nodes": ["saudi_aramco", "gcc_pipeline"],
        "base_loss_usd": 2_800_000_000,
        "peak_day_offset": 4,
        "recovery_base_days": 30,
        "sectors_affected": ["energy", "banking", "logistics", "maritime"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "qatar_lng_disruption": {
        "id": "qatar_lng_disruption",
        "name": "Qatar LNG Supply Disruption",
        "name_ar": "اضطراب إمدادات LNG القطرية",
        "shock_nodes": ["qatar_lng", "hormuz"],
        "base_loss_usd": 1_400_000_000,
        "peak_day_offset": 2,
        "recovery_base_days": 18,
        "sectors_affected": ["energy", "maritime", "banking"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "bahrain_sovereign_stress": {
        "id": "bahrain_sovereign_stress",
        "name": "Bahrain Sovereign & Banking Stress",
        "name_ar": "ضغط السيادة والقطاع المصرفي في البحرين",
        "shock_nodes": ["bahrain_banking", "reinsurance_hub"],
        "base_loss_usd": 600_000_000,
        "peak_day_offset": 7,
        "recovery_base_days": 21,
        "sectors_affected": ["banking", "insurance", "government"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "kuwait_fiscal_shock": {
        "id": "kuwait_fiscal_shock",
        "name": "Kuwait Fiscal & Oil Revenue Shock",
        "name_ar": "صدمة المالية العامة وإيرادات النفط الكويتية",
        "shock_nodes": ["kuwait_oil", "kuwait_banking"],
        "base_loss_usd": 750_000_000,
        "peak_day_offset": 6,
        "recovery_base_days": 24,
        "sectors_affected": ["energy", "banking", "government"],
        "cross_sector": False,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "oman_port_closure": {
        "id": "oman_port_closure",
        "name": "Oman Port & Trade Route Closure",
        "name_ar": "إغلاق الموانئ وطرق التجارة العُمانية",
        "shock_nodes": ["salalah_port", "oman_trade"],
        "base_loss_usd": 420_000_000,
        "peak_day_offset": 2,
        "recovery_base_days": 14,
        "sectors_affected": ["maritime", "logistics", "energy"],
        "cross_sector": False,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    # ── Extended ─────────────────────────────────────────────────────────
    "gcc_power_grid_failure": {
        "id": "gcc_power_grid_failure",
        "name": "GCC Power Grid Cascade Failure",
        "name_ar": "فشل متتالي في الشبكة الكهربائية الخليجية",
        "shock_nodes": ["gcc_power_grid", "gcc_water_desalin"],
        "base_loss_usd": 1_100_000_000,
        "peak_day_offset": 1,
        "recovery_base_days": 10,
        "sectors_affected": ["infrastructure", "energy", "banking", "healthcare"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "difc_financial_contagion": {
        "id": "difc_financial_contagion",
        "name": "DIFC Financial Contagion Event",
        "name_ar": "حدث عدوى مالية في مركز دبي المالي الدولي",
        "shock_nodes": ["difc", "uae_banking"],
        "base_loss_usd": 2_200_000_000,
        "peak_day_offset": 3,
        "recovery_base_days": 18,
        "sectors_affected": ["banking", "fintech", "insurance"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "gcc_insurance_reserve_shortfall": {
        "id": "gcc_insurance_reserve_shortfall",
        "name": "GCC Insurance Reserve Shortfall",
        "name_ar": "نقص احتياطيات التأمين الخليجي",
        "shock_nodes": ["gcc_insurance", "reinsurance_hub"],
        "base_loss_usd": 380_000_000,
        "peak_day_offset": 8,
        "recovery_base_days": 28,
        "sectors_affected": ["insurance", "banking", "fintech"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "gcc_fintech_payment_outage": {
        "id": "gcc_fintech_payment_outage",
        "name": "GCC Fintech Payment System Outage",
        "name_ar": "انقطاع نظام المدفوعات في التقنية المالية الخليجية",
        "shock_nodes": ["swift_gcc", "gcc_fintech"],
        "base_loss_usd": 680_000_000,
        "peak_day_offset": 1,
        "recovery_base_days": 5,
        "sectors_affected": ["fintech", "banking"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "saudi_vision_mega_project_halt": {
        "id": "saudi_vision_mega_project_halt",
        "name": "Saudi Vision 2030 Mega-Project Halt",
        "name_ar": "توقف المشاريع الكبرى لرؤية 2030 السعودية",
        "shock_nodes": ["riyadh_financial", "saudi_sovereign_fund"],
        "base_loss_usd": 1_600_000_000,
        "peak_day_offset": 10,
        "recovery_base_days": 45,
        "sectors_affected": ["banking", "infrastructure", "logistics", "government"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "gcc_sovereign_debt_crisis": {
        "id": "gcc_sovereign_debt_crisis",
        "name": "GCC Multi-Sovereign Debt Stress",
        "name_ar": "ضغط ديون سيادية متعددة في الخليج",
        "shock_nodes": ["gcc_fsb", "sama", "uae_cbuae"],
        "base_loss_usd": 4_500_000_000,
        "peak_day_offset": 14,
        "recovery_base_days": 90,
        "sectors_affected": ["government", "banking", "fintech", "insurance", "energy"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "hormuz_full_closure": {
        "id": "hormuz_full_closure",
        "name": "Full Hormuz Closure (Extreme Scenario)",
        "name_ar": "إغلاق كامل لمضيق هرمز (سيناريو متطرف)",
        "shock_nodes": ["hormuz", "shipping_lanes", "qatar_lng", "dammam_port"],
        "base_loss_usd": 8_500_000_000,
        "peak_day_offset": 5,
        "recovery_base_days": 60,
        "sectors_affected": ["energy", "maritime", "banking", "insurance", "logistics", "fintech"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    # ── Frontend-facing scenario IDs (mapped to engine equivalents) ──────
    "red_sea_trade_corridor_instability": {
        "id": "red_sea_trade_corridor_instability",
        "name": "Red Sea Trade Corridor Instability",
        "name_ar": "اضطراب ممر التجارة في البحر الأحمر",
        "label_en": "Red Sea Trade Corridor Instability",
        "label_ar": "اضطراب ممر التجارة في البحر الأحمر",
        "shock_nodes": ["shipping_lanes", "salalah_port", "oman_trade"],
        "base_loss_usd": 2_100_000_000,
        "peak_day_offset": 3,
        "recovery_base_days": 18,
        "sectors_affected": ["maritime", "logistics", "energy", "banking", "insurance"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "financial_infrastructure_cyber_disruption": {
        "id": "financial_infrastructure_cyber_disruption",
        "name": "Financial Infrastructure Cyber Disruption",
        "name_ar": "تعطّل البنية المالية نتيجة هجوم سيبراني",
        "label_en": "Financial Infrastructure Cyber Disruption",
        "label_ar": "تعطّل البنية المالية نتيجة هجوم سيبراني",
        "shock_nodes": ["swift_gcc", "uae_payment_rail", "gcc_fintech"],
        "base_loss_usd": 1_050_000_000,
        "peak_day_offset": 1,
        "recovery_base_days": 7,
        "sectors_affected": ["fintech", "banking", "infrastructure"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "energy_market_volatility_shock": {
        "id": "energy_market_volatility_shock",
        "name": "Energy Market Volatility Shock",
        "name_ar": "صدمة تقلبات أسواق الطاقة",
        "label_en": "Energy Market Volatility Shock",
        "label_ar": "صدمة تقلبات أسواق الطاقة",
        "shock_nodes": ["saudi_aramco", "qatar_lng", "adnoc", "gcc_pipeline"],
        "base_loss_usd": 3_400_000_000,
        "peak_day_offset": 4,
        "recovery_base_days": 28,
        "sectors_affected": ["energy", "banking", "maritime", "government"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "regional_liquidity_stress_event": {
        "id": "regional_liquidity_stress_event",
        "name": "Regional Liquidity Stress Event",
        "name_ar": "أزمة سيولة مصرفية إقليمية",
        "label_en": "Regional Liquidity Stress Event",
        "label_ar": "أزمة سيولة مصرفية إقليمية",
        "shock_nodes": ["uae_banking", "saudi_banking", "qatar_banking", "gcc_fsb"],
        "base_loss_usd": 2_600_000_000,
        "peak_day_offset": 6,
        "recovery_base_days": 21,
        "sectors_affected": ["banking", "fintech", "insurance", "government"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
    "critical_port_throughput_disruption": {
        "id": "critical_port_throughput_disruption",
        "name": "Critical Port Throughput Disruption",
        "name_ar": "تعطّل تدفق العمليات في ميناء حيوي",
        "label_en": "Critical Port Throughput Disruption",
        "label_ar": "تعطّل تدفق العمليات في ميناء حيوي",
        "shock_nodes": ["dubai_port", "abu_dhabi_port", "dammam_port"],
        "base_loss_usd": 1_750_000_000,
        "peak_day_offset": 2,
        "recovery_base_days": 14,
        "sectors_affected": ["maritime", "logistics", "banking", "energy"],
        "cross_sector": True,
        "node_sectors": {n["id"]: n["sector"] for n in GCC_NODES},
    },
}

# Create a node lookup map
_NODE_MAP: dict[str, dict] = {n["id"]: n for n in GCC_NODES}


# ---------------------------------------------------------------------------
# Simulation Engine
# ---------------------------------------------------------------------------

class SimulationEngine:
    """
    Full pipeline orchestrator for Impact Observatory v2.1.0.

    Call .run(scenario_id, severity, horizon_hours) to execute all 17 stages
    and receive the complete 16-field output dict.
    """

    MODEL_VERSION = "2.1.0"

    def run(
        self,
        scenario_id: str,
        severity: float,
        horizon_hours: int = 336,
    ) -> dict:
        """
        Execute the full 17-stage simulation pipeline.

        Args:
            scenario_id:    One of the keys in SCENARIO_CATALOG.
            severity:       Float [0.0, 1.0] — base severity of the event.
            horizon_hours:  Simulation horizon in hours (default 336 = 14 days).

        Returns:
            Complete 16-field output dict.

        Raises:
            ValueError: if scenario_id is not in catalog.
        """
        t_start = time.perf_counter()
        run_id = generate_run_id()
        generated_at = now_utc()
        severity = clamp(severity, 0.01, 1.0)

        # ── Stage 1: Resolve scenario ─────────────────────────────────────
        if scenario_id not in SCENARIO_CATALOG:
            available = list(SCENARIO_CATALOG.keys())
            raise ValueError(
                f"Unknown scenario '{scenario_id}'. "
                f"Available: {available}"
            )
        scenario = SCENARIO_CATALOG[scenario_id]
        shock_nodes: list[str] = scenario["shock_nodes"]
        base_loss_usd: float = scenario["base_loss_usd"]
        peak_day_offset: int = scenario["peak_day_offset"]
        recovery_days: int = scenario["recovery_base_days"]
        node_sectors: dict[str, str] = scenario["node_sectors"]
        cross_sector: bool = scenario["cross_sector"]
        horizon_days = max(1, horizon_hours // 24)
        peak_day = min(peak_day_offset, horizon_days)

        # ── Stage 2: Event severity ───────────────────────────────────────
        event_severity = compute_event_severity(
            base_severity=severity,
            n_shock_nodes=len(shock_nodes),
            cross_sector=cross_sector,
        )

        # ── Stage 3: Sector exposure ──────────────────────────────────────
        sector_exposure = compute_sector_exposure(
            shock_nodes=shock_nodes,
            severity=event_severity,
            node_sectors=node_sectors,
        )

        # ── Stage 4: Propagation ──────────────────────────────────────────
        propagation_raw = compute_propagation(
            shock_nodes=shock_nodes,
            severity=event_severity,
            adjacency=GCC_ADJACENCY,
            horizon_days=min(horizon_days, 14),
        )

        propagation_score = float(
            max((r["impact"] for r in propagation_raw), default=event_severity)
        )

        # ── Stage 5: Liquidity stress ─────────────────────────────────────
        liquidity_stress = compute_liquidity_stress(
            severity=event_severity,
            sector_exposure=sector_exposure,
        )

        # ── Stage 6: Insurance stress ─────────────────────────────────────
        insurance_stress = compute_insurance_stress(
            severity=event_severity,
            sector_exposure=sector_exposure,
        )

        # ── Stage 7: Financial losses ─────────────────────────────────────
        financial_impacts = compute_financial_losses(
            severity=event_severity,
            scenario_base_loss=base_loss_usd,
            propagation=propagation_raw,
            sector_exposure=sector_exposure,
        )

        total_loss_usd = sum(f["loss_usd"] for f in financial_impacts)
        direct_loss_usd = sum(f.get("direct_loss_usd", 0) for f in financial_impacts)
        indirect_loss_usd = sum(f.get("indirect_loss_usd", 0) for f in financial_impacts)
        systemic_loss_usd = sum(f.get("systemic_loss_usd", 0) for f in financial_impacts)
        systemic_multiplier = round(total_loss_usd / max(base_loss_usd, 1), 4)
        affected_entities = len(financial_impacts)
        critical_entities = sum(
            1 for f in financial_impacts
            if f.get("classification") in ("HIGH", "SEVERE")
        )

        # ── Stage 8: Unified risk score ───────────────────────────────────
        unified_risk = compute_unified_risk_score(
            severity=event_severity,
            propagation_score=propagation_score,
            liquidity_stress=liquidity_stress["aggregate_stress"],
            insurance_stress=insurance_stress["severity_index"],
            sector_exposure=sector_exposure,
            event_severity=event_severity,
        )
        risk_level = unified_risk["risk_level"]

        # ── Stage 9: Confidence score ─────────────────────────────────────
        confidence_score = compute_confidence_score(
            n_shock_nodes=len(shock_nodes),
            severity=event_severity,
            scenario_id=scenario_id,
        )

        # ── Stage 10: Node utilization ────────────────────────────────────
        node_util = compute_node_utilization(
            nodes=GCC_NODES,
            severity=event_severity,
        )

        # ── Stage 11: Bottlenecks ─────────────────────────────────────────
        bottlenecks = compute_bottleneck_scores(
            node_utilization=node_util,
            adjacency=GCC_ADJACENCY,
        )
        top_bottlenecks = bottlenecks[:5]

        # ── Stage 12: Shock wave propagation ─────────────────────────────
        shock_wave = propagate_shock_wave(
            shock_nodes=shock_nodes,
            severity=event_severity,
            adjacency=GCC_ADJACENCY,
            n_steps=min(horizon_days, 14),
        )

        # ── Stage 12b: Flow conservation check ───────────────────────────
        import logging as _logging
        _logger = _logging.getLogger(__name__)
        flow_balance_status = "BALANCED"
        # Build synthetic flows from adjacency for conservation check
        _synthetic_flows = []
        for src_node, neighbors in GCC_ADJACENCY.items():
            src_util = next((n["utilization"] for n in node_util if n["node_id"] == src_node), 0.5)
            for tgt in neighbors:
                _synthetic_flows.append({
                    "source": src_node,
                    "target": tgt,
                    "volume": src_util * event_severity,
                })
        try:
            check_flow_conservation(GCC_NODES, _synthetic_flows)
        except PhysicsViolationError as _pve:
            _logger.warning("PhysicsViolationError: %s", _pve)
            flow_balance_status = "VIOLATION_DETECTED"

        # ── Stage 13: Congestion ──────────────────────────────────────────
        congestion = compute_congestion(node_util)
        congestion_score = congestion["system_congestion_score"]
        saturated_nodes = congestion["n_saturated"]
        system_utilization = float(
            sum(n["utilization"] for n in node_util) / max(len(node_util), 1)
        )

        # ── Stage 14: Recovery trajectory ────────────────────────────────
        top_sector = max(sector_exposure, key=sector_exposure.get, default="energy")
        recovery_traj = compute_recovery_trajectory(
            severity=event_severity,
            peak_day=peak_day,
            horizon_days=min(horizon_days, recovery_days),
            sector=top_sector,
        )
        # Recovery score = fraction recovered at end of trajectory
        recovery_score = recovery_traj[-1]["recovery_fraction"] if recovery_traj else 0.0

        # ── Stage 15: Flow simulation ─────────────────────────────────────
        stress_inputs = {
            "banking_stress": liquidity_stress["aggregate_stress"],
            "fintech_stress": liquidity_stress["aggregate_stress"] * 0.75,
            "insurance_stress": insurance_stress["severity_index"],
        }
        flow_analysis = simulate_all_flows(
            severity=event_severity,
            sector_exposure=sector_exposure,
            stress_inputs=stress_inputs,
        )

        # ── Stage 16: Decision plan ───────────────────────────────────────
        sector_analysis = _build_sector_analysis(sector_exposure, liquidity_stress, insurance_stress)
        actions = build_decision_actions(
            risk_level=risk_level,
            sector_analysis=sector_analysis,
            liquidity_stress=liquidity_stress,
            insurance_stress=insurance_stress,
            unified_risk=unified_risk,
            total_loss_usd=total_loss_usd,
        )
        five_q = build_five_questions(
            scenario_id=scenario_id,
            shock_nodes=shock_nodes,
            severity=event_severity,
            risk_level=risk_level,
            total_loss_usd=total_loss_usd,
            affected_count=affected_entities,
            sector_analysis=sector_analysis,
            unified_risk=unified_risk,
            actions=actions,
        )
        escalation_triggers = compute_escalation_triggers(
            risk_level=risk_level,
            liquidity=liquidity_stress,
            insurance=insurance_stress,
        )
        monitoring_priorities = compute_monitoring_priorities(
            sector_analysis=sector_analysis,
            bottlenecks=top_bottlenecks,
        )

        # Time to first failure (hours): from liquidity model
        ttff_hours = liquidity_stress["time_to_breach_hours"]

        # ── Stage 17: Explainability ──────────────────────────────────────
        causal_chain = build_causal_chain(
            shock_nodes=shock_nodes,
            propagation=propagation_raw,
            financial_impacts=financial_impacts,
            severity=event_severity,
        )
        narrative = build_narrative(
            scenario_id=scenario_id,
            severity=event_severity,
            risk_level=risk_level,
            total_loss_usd=total_loss_usd,
            peak_day=peak_day,
            affected_count=affected_entities,
            top_sector=top_sector,
            confidence_score=confidence_score,
        )
        sensitivity = compute_sensitivity(
            base_severity=event_severity,
            base_loss=total_loss_usd,
            base_risk_score=unified_risk["score"],
        )
        uncertainty_bands = compute_uncertainty_bands(
            base_score=unified_risk["score"],
            confidence=confidence_score,
        )

        # ── Assemble output ───────────────────────────────────────────────
        duration_ms = int((time.perf_counter() - t_start) * 1000)

        average_stress = round(
            (liquidity_stress["aggregate_stress"] + insurance_stress["severity_index"]) / 2.0,
            4,
        )

        business_severity = classify_stress(event_severity)

        output = {
            # ── Metadata ──────────────────────────────────────────────────
            "run_id": run_id,
            "scenario_id": scenario_id,
            "model_version": self.MODEL_VERSION,
            "severity": round(severity, 4),
            "horizon_hours": horizon_hours,
            "time_horizon_days": horizon_days,
            "generated_at": generated_at,
            "duration_ms": duration_ms,

            # ── Core outputs ──────────────────────────────────────────────
            "event_severity": round(event_severity, 4),
            "peak_day": peak_day,
            "confidence_score": confidence_score,

            # ── Financial ─────────────────────────────────────────────────
            "financial_impact": {
                "total_loss_usd": round(total_loss_usd, 2),
                "total_loss_formatted": format_loss_usd(total_loss_usd),
                "direct_loss_usd": round(direct_loss_usd, 2),
                "indirect_loss_usd": round(indirect_loss_usd, 2),
                "systemic_loss_usd": round(systemic_loss_usd, 2),
                "systemic_multiplier": systemic_multiplier,
                "affected_entities": affected_entities,
                "critical_entities": critical_entities,
                "top_entities": financial_impacts[:10],
                # Checklist-required supplemental fields
                "gdp_impact_pct": round(total_loss_usd / 2_000_000_000_000 * 100, 6),  # ~$2T GCC GDP
                "sector_losses": {
                    fi["sector"]: round(fi["loss_usd"], 2)
                    for fi in financial_impacts
                },
                "confidence_interval": {
                    "lower": round(total_loss_usd * (1.0 - (1.0 - confidence_score) * 0.5), 2),
                    "upper": round(total_loss_usd * (1.0 + (1.0 - confidence_score) * 0.5), 2),
                    "confidence": confidence_score,
                },
            },

            # ── Sector ────────────────────────────────────────────────────
            "sector_analysis": sector_analysis,

            # ── Propagation ───────────────────────────────────────────────
            "propagation_score": round(propagation_score, 4),
            "propagation_chain": propagation_raw[:20],

            # ── Risk ──────────────────────────────────────────────────────
            "unified_risk_score": unified_risk["score"],
            "risk_level": risk_level,

            # ── Physics ───────────────────────────────────────────────────
            "physical_system_status": {
                "nodes_assessed": len(GCC_NODES),
                "saturated_nodes": saturated_nodes,
                "flow_balance_status": flow_balance_status,
                "system_utilization": round(system_utilization, 4),
                # Checklist-required supplemental fields (also exposed top-level)
                "congestion_score": round(congestion_score, 4),
                "recovery_score": round(recovery_score, 4),
                "bottlenecks": [b["node_id"] for b in top_bottlenecks if b.get("is_critical_bottleneck")],
                "node_states": {
                    n["node_id"]: n["saturation_status"]
                    for n in node_util[:10]  # top 10 most critical
                },
            },
            "bottlenecks": top_bottlenecks,
            "congestion_score": congestion_score,
            "recovery_score": round(recovery_score, 4),
            "recovery_trajectory": recovery_traj,

            # ── Sector stress ─────────────────────────────────────────────
            "banking_stress": {
                **liquidity_stress,
                "sector": "banking",
                # Map internal key names to frontend-expected names
                "time_to_liquidity_breach_hours": liquidity_stress.get("time_to_breach_hours", 9999.0),
                # credit_stress not in risk_models; derive from aggregate_stress
                "credit_stress": round(liquidity_stress["aggregate_stress"] * 0.85, 4),
                # aggregate_stress already present via **liquidity_stress
                # Additional fields expected by BankingStress type
                "total_exposure_usd": round(total_loss_usd * sector_exposure.get("banking", 0.30), 2),
                "fx_stress": round(liquidity_stress["aggregate_stress"] * 0.60, 4),
                "interbank_contagion": round(liquidity_stress["aggregate_stress"] * 0.70, 4),
                "capital_adequacy_impact_pct": round(
                    liquidity_stress["aggregate_stress"] * 3.5, 4
                ),
                "affected_institutions": [],
                "run_id": run_id,
            },
            "insurance_stress": {
                **insurance_stress,
                "sector": "insurance",
                # aggregate_stress alias (insurance_stress has severity_index; add alias)
                "aggregate_stress": round(insurance_stress["severity_index"], 4),
                # time_to_insolvency_hours: derive from reserve adequacy
                "time_to_insolvency_hours": round(
                    insurance_stress["reserve_adequacy"] * 720.0, 1  # months-equivalent in hours
                ) if insurance_stress["severity_index"] > 0.5 else 9999.0,
                "ifrs17_risk_adjustment_pct": round(
                    insurance_stress["severity_index"] * 12.0, 2
                ),
                "reinsurance_trigger": insurance_stress["severity_index"] > 0.65,
                "portfolio_exposure_usd": round(
                    total_loss_usd * sector_exposure.get("insurance", 0.15), 2
                ),
                "underwriting_status": classify_stress(insurance_stress["severity_index"]),
                "affected_lines": [],
                "run_id": run_id,
            },
            "fintech_stress": {
                "aggregate_stress": round(liquidity_stress["aggregate_stress"] * 0.75, 4),
                "digital_stress": round(liquidity_stress["liquidity_stress"] * 0.70, 4),
                "digital_banking_stress": round(liquidity_stress["liquidity_stress"] * 0.70, 4),
                # backward-compat alias for liquidity_stress (pre-v2.1.0 consumers)
                "liquidity_stress": round(liquidity_stress["liquidity_stress"] * 0.70, 4),
                # Derived from payments flow analysis
                "payment_disruption_score": round(
                    flow_analysis.get("payments", {}).get("disruption_factor", 0.0) *
                    liquidity_stress["aggregate_stress"],
                    4,
                ),
                "cross_border_disruption": round(
                    flow_analysis.get("money", {}).get("disruption_factor", 0.0) *
                    sector_exposure.get("fintech", 0.05),
                    4,
                ),
                "settlement_delay_hours": round(
                    flow_analysis.get("payments", {}).get("delay_days", 0.0) * 24, 1
                ),
                # Fields required by FintechStress type / frontend .toFixed() calls
                "payment_volume_impact_pct": round(
                    liquidity_stress["aggregate_stress"] * 0.75 * 100.0, 2
                ),
                "api_availability_pct": round(
                    max(0.0, 100.0 - liquidity_stress["aggregate_stress"] * 0.75 * 40.0), 2
                ),
                "time_to_payment_failure_hours": round(
                    liquidity_stress.get("time_to_breach_hours", 9999.0) * 0.60, 1
                ),
                "affected_platforms": [],
                "run_id": run_id,
                "sector": "fintech",
                "classification": classify_stress(liquidity_stress["aggregate_stress"] * 0.75),
            },
            "flow_analysis": flow_analysis,

            # ── Explainability ────────────────────────────────────────────
            "explainability": {
                "causal_chain": causal_chain,
                "narrative_en": narrative["narrative_en"],
                "narrative_ar": narrative["narrative_ar"],
                "sensitivity": sensitivity,
                "uncertainty_bands": uncertainty_bands,
                "confidence_score": confidence_score,
                "methodology": "deterministic_propagation",
                "source": "simulation_engine_v2.1.0",
                "model_equation": (
                    "Es=w1*I+w2*D+w3*U+w4*G | "
                    "Exp_j=alpha_j*Es*V_j*C_j | "
                    "X_(t+1)=beta*P*X_t+(1-beta)*X_t+S_t | "
                    "LSI=l1*W+l2*F+l3*M+l4*C | "
                    "ISI=m1*Cf+m2*LR+m3*Re+m4*Od | "
                    "NL_j=Exp_j*IF_jt*AB_j*theta_j | "
                    "Conf=r1*DQ+r2*MC+r3*HS+r4*ST | "
                    "URS=g1*Es+g2*PeakExp+g3*PeakStress+g4*PS*sqrt(sev)+g5*LN"
                ),
            },

            # ── Decision plan ─────────────────────────────────────────────
            "decision_plan": {
                "business_severity": business_severity,
                "time_to_first_failure_hours": ttff_hours,
                "actions": actions,
                "escalation_triggers": escalation_triggers,
                "monitoring_priorities": monitoring_priorities,
                "five_questions": five_q,
                # Checklist-required action partitions derived from actions list
                "immediate_actions": [a for a in actions if a.get("time_to_act_hours", 99) <= 6],
                "short_term_actions": [a for a in actions if 6 < a.get("time_to_act_hours", 99) <= 24],
                "long_term_actions": [a for a in actions if a.get("time_to_act_hours", 99) > 24],
                "priority_matrix": {
                    "IMMEDIATE": [a["action_id"] for a in actions if a.get("status") == "IMMEDIATE"],
                    "URGENT":    [a["action_id"] for a in actions if a.get("status") == "URGENT"],
                    "MONITOR":   [a["action_id"] for a in actions if a.get("status") == "MONITOR"],
                    "WATCH":     [a["action_id"] for a in actions if a.get("status") == "WATCH"],
                },
            },

            # ── Headline KPI ──────────────────────────────────────────────
            "headline": {
                "total_loss_usd": round(total_loss_usd, 2),
                "total_loss_formatted": format_loss_usd(total_loss_usd),
                "peak_day": peak_day,
                "affected_entities": affected_entities,
                "critical_count": critical_entities,
                "elevated_count": sum(
                    1 for f in financial_impacts
                    if f.get("classification") in ("ELEVATED", "MODERATE")
                ),
                "max_recovery_days": recovery_days,
                "severity_code": risk_level,
                "average_stress": average_stress,
            },
        }

        return output


# ---------------------------------------------------------------------------
# Internal helper
# ---------------------------------------------------------------------------

def _build_sector_analysis(
    sector_exposure: dict[str, float],
    liquidity_stress: dict,
    insurance_stress: dict,
) -> list[dict]:
    """Build per-sector analysis rows."""
    sector_stress_map = {
        "banking":   liquidity_stress["aggregate_stress"],
        "insurance": insurance_stress["severity_index"],
        "fintech":   liquidity_stress["aggregate_stress"] * 0.75,
    }

    rows = []
    for sector, exposure in sorted(sector_exposure.items(), key=lambda x: -x[1]):
        stress = sector_stress_map.get(sector, exposure * 0.85)
        classification = classify_stress(stress)
        rows.append({
            "sector": sector,
            "exposure": round(exposure, 4),
            "stress": round(stress, 4),
            "classification": classification,
            "risk_level": classification,
        })
    return rows
