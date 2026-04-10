"""
Authority Realism Engine — country-level GCC governance refinement.

Extends Stage 70's AuthorityEngine (which maps scenario_type → generic authority)
with country-level specificity:
  - Resolves the COUNTRY from scenario context (shock nodes, action owner)
  - Maps to actual named institutions per country
  - Adds regulatory bodies specific to the country
  - Builds complete escalation chains from operator → regulator → minister → council

Differences from Stage 70 AuthorityEngine:
  - Stage 70: scenario_type → generic "Central Bank / Monetary Authority"
  - Stage 80: scenario_type + country → "Central Bank of the UAE (CBUAE)"

6 GCC countries mapped:
  UAE, Saudi Arabia, Bahrain, Kuwait, Oman, Qatar

Consumed by: Stage 80 pipeline
Input: decisions + Stage 70 authority_assignments + scenario context
Output: list[AuthorityProfile]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.formatter_engine import FormattedExecutiveDecision
from src.decision_calibration.authority_engine import AuthorityAssignment

logger = logging.getLogger(__name__)

# ── Country → institution registry ────────────────────────────────────────

_COUNTRY_INSTITUTIONS: dict[str, dict[str, dict[str, str]]] = {
    "UAE": {
        "central_bank": {"en": "Central Bank of the UAE (CBUAE)", "ar": "المصرف المركزي لدولة الإمارات"},
        "energy_ministry": {"en": "Ministry of Energy and Infrastructure (MoEI)", "ar": "وزارة الطاقة والبنية التحتية"},
        "port_authority": {"en": "Abu Dhabi Ports / DP World", "ar": "موانئ أبوظبي / موانئ دبي العالمية"},
        "cyber_authority": {"en": "UAE Cybersecurity Council", "ar": "مجلس الأمن السيبراني الإماراتي"},
        "financial_regulator": {"en": "Securities and Commodities Authority (SCA)", "ar": "هيئة الأوراق المالية والسلع"},
        "insurance_regulator": {"en": "CBUAE Insurance Supervision Dept", "ar": "قسم الرقابة على التأمين - المصرف المركزي"},
        "supreme_council": {"en": "Federal Supreme Council", "ar": "المجلس الاتحادي الأعلى"},
        "fintech_regulator": {"en": "ADGM / DIFC Financial Services Authority", "ar": "سوق أبوظبي العالمي / سلطة دبي للخدمات المالية"},
    },
    "SAUDI": {
        "central_bank": {"en": "Saudi Central Bank (SAMA)", "ar": "البنك المركزي السعودي (ساما)"},
        "energy_ministry": {"en": "Ministry of Energy / Saudi Aramco", "ar": "وزارة الطاقة / أرامكو السعودية"},
        "port_authority": {"en": "Saudi Ports Authority (Mawani)", "ar": "الهيئة العامة للموانئ (موانئ)"},
        "cyber_authority": {"en": "National Cybersecurity Authority (NCA)", "ar": "الهيئة الوطنية للأمن السيبراني"},
        "financial_regulator": {"en": "Capital Market Authority (CMA)", "ar": "هيئة السوق المالية"},
        "insurance_regulator": {"en": "Insurance Authority (IA)", "ar": "هيئة التأمين"},
        "supreme_council": {"en": "Council of Ministers", "ar": "مجلس الوزراء"},
        "fintech_regulator": {"en": "SAMA Fintech Dept / CMA Sandbox", "ar": "إدارة التقنية المالية - ساما"},
    },
    "BAHRAIN": {
        "central_bank": {"en": "Central Bank of Bahrain (CBB)", "ar": "مصرف البحرين المركزي"},
        "energy_ministry": {"en": "National Oil & Gas Authority (NOGA)", "ar": "الهيئة الوطنية للنفط والغاز"},
        "port_authority": {"en": "Khalifa Bin Salman Port", "ar": "ميناء خليفة بن سلمان"},
        "cyber_authority": {"en": "National Cyber Security Centre (NCSC)", "ar": "المركز الوطني للأمن السيبراني"},
        "financial_regulator": {"en": "CBB Financial Regulation", "ar": "التنظيم المالي - مصرف البحرين المركزي"},
        "insurance_regulator": {"en": "CBB Insurance Supervision", "ar": "الرقابة على التأمين - مصرف البحرين المركزي"},
        "supreme_council": {"en": "Council of Ministers", "ar": "مجلس الوزراء"},
        "fintech_regulator": {"en": "CBB Fintech & Innovation Unit", "ar": "وحدة التقنية المالية والابتكار"},
    },
    "KUWAIT": {
        "central_bank": {"en": "Central Bank of Kuwait (CBK)", "ar": "بنك الكويت المركزي"},
        "energy_ministry": {"en": "Kuwait Petroleum Corporation (KPC)", "ar": "مؤسسة البترول الكويتية"},
        "port_authority": {"en": "Kuwait Ports Authority (KPA)", "ar": "المؤسسة العامة للموانئ الكويتية"},
        "cyber_authority": {"en": "National Cyber Security Center", "ar": "المركز الوطني للأمن السيبراني"},
        "financial_regulator": {"en": "Capital Markets Authority (CMA)", "ar": "هيئة أسواق المال"},
        "insurance_regulator": {"en": "Ministry of Commerce — Insurance Dept", "ar": "وزارة التجارة - إدارة التأمين"},
        "supreme_council": {"en": "Council of Ministers", "ar": "مجلس الوزراء"},
        "fintech_regulator": {"en": "CBK Fintech Office", "ar": "مكتب التقنية المالية - بنك الكويت المركزي"},
    },
    "OMAN": {
        "central_bank": {"en": "Central Bank of Oman (CBO)", "ar": "البنك المركزي العماني"},
        "energy_ministry": {"en": "Ministry of Energy and Minerals (MEM)", "ar": "وزارة الطاقة والمعادن"},
        "port_authority": {"en": "Asyad Group (Salalah/Sohar Ports)", "ar": "مجموعة أسياد (صلالة / صحار)"},
        "cyber_authority": {"en": "Information Technology Authority (ITA)", "ar": "هيئة تقنية المعلومات"},
        "financial_regulator": {"en": "Capital Market Authority (CMA)", "ar": "الهيئة العامة لسوق المال"},
        "insurance_regulator": {"en": "Capital Market Authority — Insurance", "ar": "الهيئة العامة لسوق المال - التأمين"},
        "supreme_council": {"en": "Council of Ministers", "ar": "مجلس الوزراء"},
        "fintech_regulator": {"en": "CBO Innovation Hub", "ar": "مركز الابتكار - البنك المركزي العماني"},
    },
    "QATAR": {
        "central_bank": {"en": "Qatar Central Bank (QCB)", "ar": "مصرف قطر المركزي"},
        "energy_ministry": {"en": "Ministry of Energy / QatarEnergy", "ar": "وزارة الطاقة / قطر للطاقة"},
        "port_authority": {"en": "Hamad Port / Mwani Qatar", "ar": "ميناء حمد / موانئ قطر"},
        "cyber_authority": {"en": "National Cyber Security Agency (NCSA)", "ar": "الوكالة الوطنية للأمن السيبراني"},
        "financial_regulator": {"en": "Qatar Financial Markets Authority (QFMA)", "ar": "هيئة قطر للأسواق المالية"},
        "insurance_regulator": {"en": "QCB Insurance Supervision", "ar": "الرقابة على التأمين - مصرف قطر المركزي"},
        "supreme_council": {"en": "Council of Ministers", "ar": "مجلس الوزراء"},
        "fintech_regulator": {"en": "QFC Fintech Authority", "ar": "هيئة مركز قطر للمال للتقنية المالية"},
    },
}

# ── Scenario → primary country ────────────────────────────────────────────

_SCENARIO_COUNTRY: dict[str, str] = {
    "hormuz_chokepoint_disruption":       "UAE",
    "hormuz_full_closure":                "UAE",
    "uae_banking_crisis":                 "UAE",
    "gcc_cyber_attack":                   "UAE",
    "saudi_oil_shock":                    "SAUDI",
    "saudi_vision_mega_project_halt":     "SAUDI",
    "qatar_lng_disruption":               "QATAR",
    "bahrain_sovereign_stress":           "BAHRAIN",
    "kuwait_fiscal_shock":                "KUWAIT",
    "oman_port_closure":                  "OMAN",
    "red_sea_trade_corridor_instability": "SAUDI",
    "energy_market_volatility_shock":     "SAUDI",
    "regional_liquidity_stress_event":    "UAE",
    "critical_port_throughput_disruption": "UAE",
    "financial_infrastructure_cyber_disruption": "UAE",
    "iran_regional_escalation":           "UAE",
    "difc_financial_contagion":           "UAE",
    "gcc_power_grid_failure":             "UAE",
    "gcc_insurance_reserve_shortfall":    "UAE",
    "gcc_fintech_payment_outage":         "UAE",
    "gcc_sovereign_debt_crisis":          "BAHRAIN",
}

# ── Sector → institution key mapping ─────────────────────────────────────

_SECTOR_INSTITUTION_KEY: dict[str, str] = {
    "banking":        "central_bank",
    "energy":         "energy_ministry",
    "maritime":       "port_authority",
    "logistics":      "port_authority",
    "fintech":        "fintech_regulator",
    "insurance":      "insurance_regulator",
    "infrastructure": "cyber_authority",
    "government":     "supreme_council",
}

# ── Scenario type → regulatory institution key ────────────────────────────

_TYPE_REGULATOR_KEY: dict[str, str] = {
    "MARITIME":    "port_authority",
    "ENERGY":      "energy_ministry",
    "LIQUIDITY":   "central_bank",
    "CYBER":       "cyber_authority",
    "REGULATORY":  "financial_regulator",
}


@dataclass(frozen=True, slots=True)
class AuthorityProfile:
    """Country-specific authority profile with full escalation chain."""
    decision_id: str
    action_id: str

    # Country context
    country: str
    country_ar: str

    # Primary owner (named institution)
    primary_owner_en: str
    primary_owner_ar: str

    # Secondary owner (sector-specific operator)
    secondary_owner_en: str
    secondary_owner_ar: str

    # Regulator (scenario-type specific)
    regulator_en: str
    regulator_ar: str

    # Escalation chain (operator → department head → minister → council)
    escalation_chain: list[dict[str, str]] = field(default_factory=list)

    # Cross-border entities
    cross_border_entities: list[dict[str, str]] = field(default_factory=list)

    # Notes
    authority_realism_notes: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "country": self.country,
            "country_ar": self.country_ar,
            "primary_owner_en": self.primary_owner_en,
            "primary_owner_ar": self.primary_owner_ar,
            "secondary_owner_en": self.secondary_owner_en,
            "secondary_owner_ar": self.secondary_owner_ar,
            "regulator_en": self.regulator_en,
            "regulator_ar": self.regulator_ar,
            "escalation_chain": self.escalation_chain,
            "cross_border_entities": self.cross_border_entities,
            "authority_realism_notes": self.authority_realism_notes,
        }


_COUNTRY_AR: dict[str, str] = {
    "UAE": "الإمارات",
    "SAUDI": "السعودية",
    "BAHRAIN": "البحرين",
    "KUWAIT": "الكويت",
    "OMAN": "عُمان",
    "QATAR": "قطر",
}


def refine_authority_realism(
    decisions: list[FormattedExecutiveDecision],
    authority_assignments: list[AuthorityAssignment],
    scenario_id: str,
    scenario_type: str,
) -> list[AuthorityProfile]:
    """
    Refine authority assignments with country-level institutional specificity.

    Args:
        decisions:              FormattedExecutiveDecision list from Stage 60.
        authority_assignments:  AuthorityAssignment list from Stage 70.
        scenario_id:            Current scenario ID.
        scenario_type:          Resolved scenario type (from ScenarioEnforcementEngine).

    Returns:
        list[AuthorityProfile] — country-specific authority with escalation chains.
    """
    country = _SCENARIO_COUNTRY.get(scenario_id, "UAE")
    country_ar = _COUNTRY_AR.get(country, "الإمارات")
    institutions = _COUNTRY_INSTITUTIONS.get(country, _COUNTRY_INSTITUTIONS["UAE"])

    auth_map = {a.action_id: a for a in authority_assignments}

    results: list[AuthorityProfile] = []

    for dec in decisions:
        auth = auth_map.get(dec.action_id)
        notes: list[dict[str, str]] = []

        # ── Primary owner from sector ────────────────────────────────────
        sector_key = _SECTOR_INSTITUTION_KEY.get(dec.sector, "central_bank")
        primary_inst = institutions.get(sector_key, institutions["central_bank"])

        # ── Secondary owner (always the operational authority from Stage 70)
        secondary_en = auth.operational_authority_en if auth else dec.decision_owner
        secondary_ar = auth.operational_authority_ar if auth else dec.decision_owner_ar

        # ── Regulator from scenario type ─────────────────────────────────
        reg_key = _TYPE_REGULATOR_KEY.get(scenario_type, "financial_regulator")
        regulator = institutions.get(reg_key, institutions["financial_regulator"])

        # ── Escalation chain ─────────────────────────────────────────────
        escalation = _build_escalation_chain(dec, institutions, country)

        # ── Cross-border entities ────────────────────────────────────────
        cross_border: list[dict[str, str]] = []
        if auth and auth.requires_cross_border_coordination:
            cross_border = _build_cross_border_entities(scenario_type)
            notes.append({
                "type": "CROSS_BORDER_REALISM",
                "message_en": f"Cross-border coordination includes {len(cross_border)} GCC entities",
                "message_ar": f"التنسيق العابر للحدود يشمل {len(cross_border)} جهات خليجية",
                "severity": "info",
            })

        results.append(AuthorityProfile(
            decision_id=dec.decision_id,
            action_id=dec.action_id,
            country=country,
            country_ar=country_ar,
            primary_owner_en=primary_inst["en"],
            primary_owner_ar=primary_inst["ar"],
            secondary_owner_en=secondary_en,
            secondary_owner_ar=secondary_ar,
            regulator_en=regulator["en"],
            regulator_ar=regulator["ar"],
            escalation_chain=escalation,
            cross_border_entities=cross_border,
            authority_realism_notes=notes,
        ))

    logger.info(
        "[AuthorityRealismEngine] Refined %d authority profiles for %s (%s)",
        len(results), country, scenario_type,
    )
    return results


def _build_escalation_chain(
    dec: FormattedExecutiveDecision,
    institutions: dict[str, dict[str, str]],
    country: str,
) -> list[dict[str, str]]:
    """Build 4-level escalation chain: operator → department → minister → council."""
    chain: list[dict[str, str]] = []

    # Level 1: Operational (sector-specific)
    sector_key = _SECTOR_INSTITUTION_KEY.get(dec.sector, "central_bank")
    inst = institutions.get(sector_key, institutions["central_bank"])
    chain.append({
        "level": "1",
        "role_en": "Operational Authority",
        "role_ar": "السلطة التشغيلية",
        "entity_en": inst["en"],
        "entity_ar": inst["ar"],
        "trigger": "immediate",
    })

    # Level 2: Regulatory (scenario-aligned)
    reg = institutions.get("financial_regulator", institutions["central_bank"])
    chain.append({
        "level": "2",
        "role_en": "Regulatory Authority",
        "role_ar": "السلطة التنظيمية",
        "entity_en": reg["en"],
        "entity_ar": reg["ar"],
        "trigger": "if_escalated_or_cross_sector",
    })

    # Level 3: Ministerial (always present for emergency)
    cb = institutions["central_bank"]
    chain.append({
        "level": "3",
        "role_en": "Ministerial / Governor Level",
        "role_ar": "مستوى وزاري / محافظ",
        "entity_en": cb["en"],
        "entity_ar": cb["ar"],
        "trigger": "emergency_or_high_severity",
    })

    # Level 4: Supreme council (last resort)
    council = institutions["supreme_council"]
    chain.append({
        "level": "4",
        "role_en": "Supreme Council / Cabinet",
        "role_ar": "المجلس الأعلى / مجلس الوزراء",
        "entity_en": council["en"],
        "entity_ar": council["ar"],
        "trigger": "sovereign_or_cross_border",
    })

    return chain


def _build_cross_border_entities(scenario_type: str) -> list[dict[str, str]]:
    """Build cross-border entity list for GCC coordination."""
    entities: list[dict[str, str]] = [
        {"entity_en": "GCC Secretariat General", "entity_ar": "الأمانة العامة لمجلس التعاون", "role": "coordination"},
    ]

    type_entities: dict[str, list[dict[str, str]]] = {
        "MARITIME": [
            {"entity_en": "International Maritime Organization (IMO)", "entity_ar": "المنظمة البحرية الدولية", "role": "standards"},
            {"entity_en": "Combined Maritime Forces (CMF)", "entity_ar": "القوات البحرية المشتركة", "role": "security"},
        ],
        "ENERGY": [
            {"entity_en": "OPEC Secretariat", "entity_ar": "أمانة أوبك", "role": "supply_coordination"},
            {"entity_en": "International Energy Agency (IEA)", "entity_ar": "وكالة الطاقة الدولية", "role": "monitoring"},
        ],
        "LIQUIDITY": [
            {"entity_en": "Bank for International Settlements (BIS)", "entity_ar": "بنك التسويات الدولية", "role": "standards"},
            {"entity_en": "International Monetary Fund (IMF)", "entity_ar": "صندوق النقد الدولي", "role": "support"},
        ],
        "CYBER": [
            {"entity_en": "FIRST (Forum of Incident Response)", "entity_ar": "منتدى الاستجابة للحوادث", "role": "incident_response"},
        ],
    }

    entities.extend(type_entities.get(scenario_type, []))
    return entities
