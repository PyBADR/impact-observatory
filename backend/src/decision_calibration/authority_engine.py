"""
Authority Matrix Engine — GCC-realistic institutional authority mapping.

Replaces generic owner strings with realistic GCC governance structure:
  - Central banks (CBUAE, SAMA, CBB, CBK, CBO, QCB)
  - Regulators (DFSA, CMA, NESA)
  - Operators (ADNOC, Saudi Aramco, QP, Mawani)
  - Ministries (MoF, MoE, MoI)

Authority assignment depends on:
  - scenario_type (MARITIME → port authorities, ENERGY → energy ministries)
  - sector (banking → central bank, energy → energy ministry)
  - decision_type (emergency → C-Suite/Minister, strategic → Board/Council)
  - country context (derived from action sector + scenario)

Rules:
  - Every decision must have exactly ONE primary authority
  - Every decision must have at least ONE escalation target
  - Emergency decisions → Minister/Governor level
  - Strategic decisions → Board/Council level
  - Operational decisions → Director/Department Head level

Consumed by: Stage 70 pipeline
Input: list[FormattedExecutiveDecision], scenario_type
Output: list[AuthorityAssignment]
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from src.decision_quality.formatter_engine import FormattedExecutiveDecision

logger = logging.getLogger(__name__)

# ── GCC Authority Registry ────────────────────────────────────────────────

# scenario_type → primary authority chain
_SCENARIO_AUTHORITIES: dict[str, dict[str, str]] = {
    "MARITIME": {
        "primary_en": "Federal Transport Authority / Port Authority",
        "primary_ar": "الهيئة الاتحادية للمواصلات / هيئة الموانئ",
        "escalation_en": "Ministry of Energy & Infrastructure",
        "escalation_ar": "وزارة الطاقة والبنية التحتية",
        "oversight_en": "Supreme Council for National Security",
        "oversight_ar": "المجلس الأعلى للأمن الوطني",
    },
    "ENERGY": {
        "primary_en": "Ministry of Energy / National Energy Company",
        "primary_ar": "وزارة الطاقة / شركة الطاقة الوطنية",
        "escalation_en": "Supreme Petroleum Council",
        "escalation_ar": "المجلس الأعلى للبترول",
        "oversight_en": "Council of Ministers",
        "oversight_ar": "مجلس الوزراء",
    },
    "LIQUIDITY": {
        "primary_en": "Central Bank / Monetary Authority",
        "primary_ar": "البنك المركزي / مؤسسة النقد",
        "escalation_en": "Financial Stability Committee",
        "escalation_ar": "لجنة الاستقرار المالي",
        "oversight_en": "Ministry of Finance",
        "oversight_ar": "وزارة المالية",
    },
    "CYBER": {
        "primary_en": "National Cybersecurity Authority",
        "primary_ar": "الهيئة الوطنية للأمن السيبراني",
        "escalation_en": "Ministry of Interior / Digital Authority",
        "escalation_ar": "وزارة الداخلية / الهيئة الرقمية",
        "oversight_en": "National Security Council",
        "oversight_ar": "مجلس الأمن الوطني",
    },
    "REGULATORY": {
        "primary_en": "Ministry of Foreign Affairs / Regulatory Authority",
        "primary_ar": "وزارة الخارجية / الهيئة التنظيمية",
        "escalation_en": "Council of Ministers",
        "escalation_ar": "مجلس الوزراء",
        "oversight_en": "Head of State Office",
        "oversight_ar": "ديوان رئيس الدولة",
    },
}

# sector → specific operational authority
_SECTOR_AUTHORITIES: dict[str, dict[str, str]] = {
    "maritime": {
        "operational_en": "Mawani / Abu Dhabi Ports / Salalah Port",
        "operational_ar": "موانئ / موانئ أبوظبي / ميناء صلالة",
    },
    "energy": {
        "operational_en": "ADNOC / Saudi Aramco / QatarEnergy",
        "operational_ar": "أدنوك / أرامكو السعودية / قطر للطاقة",
    },
    "banking": {
        "operational_en": "CBUAE / SAMA / Central Bank",
        "operational_ar": "المصرف المركزي / مؤسسة النقد",
    },
    "insurance": {
        "operational_en": "Insurance Authority / CCHI",
        "operational_ar": "هيئة التأمين / مجلس الضمان الصحي",
    },
    "logistics": {
        "operational_en": "Customs Authority / Free Zone Authority",
        "operational_ar": "هيئة الجمارك / هيئة المناطق الحرة",
    },
    "fintech": {
        "operational_en": "DFSA / ADGM / Central Bank Fintech Office",
        "operational_ar": "سلطة دبي للخدمات المالية / سوق أبوظبي العالمي",
    },
    "infrastructure": {
        "operational_en": "Telecommunications Regulatory Authority",
        "operational_ar": "هيئة تنظيم الاتصالات",
    },
    "government": {
        "operational_en": "Executive Office / Cabinet Secretariat",
        "operational_ar": "المكتب التنفيذي / الأمانة العامة لمجلس الوزراء",
    },
}

# decision_type → authority level
_AUTHORITY_LEVELS: dict[str, dict[str, str]] = {
    "emergency": {
        "level_en": "Minister / Governor / CEO",
        "level_ar": "وزير / محافظ / رئيس تنفيذي",
        "seniority": "C-Suite",
        "seniority_ar": "مستوى القيادة العليا",
    },
    "operational": {
        "level_en": "Director General / Department Head",
        "level_ar": "مدير عام / رئيس قسم",
        "seniority": "Department Head",
        "seniority_ar": "مستوى رئيس القسم",
    },
    "strategic": {
        "level_en": "Board of Directors / Council",
        "level_ar": "مجلس الإدارة / المجلس",
        "seniority": "Board",
        "seniority_ar": "مستوى مجلس الإدارة",
    },
}


@dataclass(frozen=True, slots=True)
class AuthorityAssignment:
    """Institutional authority assignment for a decision."""
    decision_id: str
    action_id: str

    # Primary authority (who executes)
    primary_authority_en: str
    primary_authority_ar: str

    # Operational authority (sector-specific operator)
    operational_authority_en: str
    operational_authority_ar: str

    # Escalation target (who to escalate to)
    escalation_target_en: str
    escalation_target_ar: str

    # Oversight body (regulatory/sovereign oversight)
    oversight_body_en: str
    oversight_body_ar: str

    # Authority level
    authority_level_en: str
    authority_level_ar: str
    seniority: str
    seniority_ar: str

    # Governance metadata
    requires_cross_border_coordination: bool
    coordination_bodies: list[dict[str, str]] = field(default_factory=list)
    authority_notes: list[dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "decision_id": self.decision_id,
            "action_id": self.action_id,
            "primary_authority_en": self.primary_authority_en,
            "primary_authority_ar": self.primary_authority_ar,
            "operational_authority_en": self.operational_authority_en,
            "operational_authority_ar": self.operational_authority_ar,
            "escalation_target_en": self.escalation_target_en,
            "escalation_target_ar": self.escalation_target_ar,
            "oversight_body_en": self.oversight_body_en,
            "oversight_body_ar": self.oversight_body_ar,
            "authority_level_en": self.authority_level_en,
            "authority_level_ar": self.authority_level_ar,
            "seniority": self.seniority,
            "seniority_ar": self.seniority_ar,
            "requires_cross_border_coordination": self.requires_cross_border_coordination,
            "coordination_bodies": self.coordination_bodies,
            "authority_notes": self.authority_notes,
        }


def assign_authorities(
    decisions: list[FormattedExecutiveDecision],
    scenario_type: str,
) -> list[AuthorityAssignment]:
    """
    Assign GCC-realistic institutional authorities to each decision.

    Args:
        decisions:      FormattedExecutiveDecision list from Stage 60.
        scenario_type:  Scenario type (MARITIME, ENERGY, LIQUIDITY, CYBER, REGULATORY).

    Returns:
        list[AuthorityAssignment] — one per decision.
    """
    scenario_auth = _SCENARIO_AUTHORITIES.get(scenario_type, _SCENARIO_AUTHORITIES["REGULATORY"])

    results: list[AuthorityAssignment] = []

    for dec in decisions:
        notes: list[dict[str, str]] = []

        # ── Resolve authority level from decision type ────────────────────
        level = _AUTHORITY_LEVELS.get(dec.decision_type, _AUTHORITY_LEVELS["operational"])

        # ── Resolve operational authority from sector ─────────────────────
        sector_auth = _SECTOR_AUTHORITIES.get(dec.sector, {
            "operational_en": f"{dec.sector.title()} Operations Authority",
            "operational_ar": f"هيئة عمليات {dec.sector}",
        })

        # ── Cross-border coordination detection ──────────────────────────
        cross_border = _requires_cross_border(dec, scenario_type)
        coordination: list[dict[str, str]] = []

        if cross_border:
            coordination = _get_coordination_bodies(scenario_type)
            notes.append({
                "type": "CROSS_BORDER",
                "message_en": "Decision requires cross-border GCC coordination",
                "message_ar": "القرار يتطلب تنسيقاً عابراً للحدود في دول الخليج",
                "severity": "info",
            })

        # ── Emergency escalation note ────────────────────────────────────
        if dec.decision_type == "emergency":
            notes.append({
                "type": "EMERGENCY_AUTHORITY",
                "message_en": f"Emergency authority activated — escalation to {scenario_auth['escalation_en']}",
                "message_ar": f"تم تفعيل صلاحية الطوارئ — التصعيد إلى {scenario_auth['escalation_ar']}",
                "severity": "warning",
            })

        results.append(AuthorityAssignment(
            decision_id=dec.decision_id,
            action_id=dec.action_id,
            primary_authority_en=scenario_auth["primary_en"],
            primary_authority_ar=scenario_auth["primary_ar"],
            operational_authority_en=sector_auth["operational_en"],
            operational_authority_ar=sector_auth["operational_ar"],
            escalation_target_en=scenario_auth["escalation_en"],
            escalation_target_ar=scenario_auth["escalation_ar"],
            oversight_body_en=scenario_auth["oversight_en"],
            oversight_body_ar=scenario_auth["oversight_ar"],
            authority_level_en=level["level_en"],
            authority_level_ar=level["level_ar"],
            seniority=level["seniority"],
            seniority_ar=level["seniority_ar"],
            requires_cross_border_coordination=cross_border,
            coordination_bodies=coordination,
            authority_notes=notes,
        ))

    logger.info(
        "[AuthorityEngine] Assigned authorities to %d decisions, %d cross-border",
        len(results), sum(1 for r in results if r.requires_cross_border_coordination),
    )
    return results


# ── Helpers ───────────────────────────────────────────────────────────────

def _requires_cross_border(dec: FormattedExecutiveDecision, scenario_type: str) -> bool:
    """Determine if decision requires cross-border coordination."""
    # Maritime and energy scenarios almost always cross borders
    if scenario_type in ("MARITIME", "ENERGY"):
        return True
    # Emergency decisions in any scenario type may need coordination
    if dec.decision_type == "emergency" and dec.urgency >= 0.80:
        return True
    # Liquidity crises with high impact
    if scenario_type == "LIQUIDITY" and dec.impact >= 0.70:
        return True
    return False


def _get_coordination_bodies(scenario_type: str) -> list[dict[str, str]]:
    """Get relevant cross-border coordination bodies."""
    bodies: list[dict[str, str]] = [
        {
            "body_en": "GCC Secretariat General",
            "body_ar": "الأمانة العامة لمجلس التعاون",
            "role_en": "Regional coordination",
            "role_ar": "التنسيق الإقليمي",
        },
    ]

    if scenario_type == "MARITIME":
        bodies.append({
            "body_en": "GCC Maritime Security Committee",
            "body_ar": "لجنة الأمن البحري لدول الخليج",
            "role_en": "Maritime security coordination",
            "role_ar": "تنسيق الأمن البحري",
        })
    elif scenario_type == "ENERGY":
        bodies.append({
            "body_en": "OPEC+ Coordination / GCC Energy Ministers Council",
            "body_ar": "تنسيق أوبك+ / مجلس وزراء الطاقة لدول الخليج",
            "role_en": "Energy supply coordination",
            "role_ar": "تنسيق إمدادات الطاقة",
        })
    elif scenario_type == "LIQUIDITY":
        bodies.append({
            "body_en": "GCC Central Banks Governors Committee",
            "body_ar": "لجنة محافظي البنوك المركزية لدول الخليج",
            "role_en": "Financial stability coordination",
            "role_ar": "تنسيق الاستقرار المالي",
        })
    elif scenario_type == "CYBER":
        bodies.append({
            "body_en": "GCC-CERT / Regional Cybersecurity Alliance",
            "body_ar": "فريق الاستجابة لطوارئ الحاسب الآلي / التحالف الإقليمي للأمن السيبراني",
            "role_en": "Cyber threat intelligence sharing",
            "role_ar": "مشاركة معلومات التهديدات السيبرانية",
        })

    return bodies
