"""
Impact Observatory | مرصد الأثر — Phase 3 Ownership Engine

Maps every decision action to its institutional owner, deadline, escalation path,
and GCC-specific authority hierarchy.

Design principles:
  - Each decision is owned by a specific institutional entity (from entity_graph.py)
  - Deadlines are calibrated to GCC regulatory/operational cadences
  - Escalation paths define who gets notified when deadlines are breached
  - All mappings are deterministic and auditable

The ownership engine answers:
  "WHO must act, by WHEN, and WHO escalates if they don't?"
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from app.domain.simulation.entity_graph import EntityType


class AuthorityLevel(str, Enum):
    """GCC institutional authority hierarchy."""
    OPERATIONAL = "operational"       # Day-to-day operators (branch, desk)
    TACTICAL = "tactical"            # Department heads, risk managers
    STRATEGIC = "strategic"          # C-suite, board committees
    SOVEREIGN = "sovereign"          # Central bank, ministry, sovereign fund


@dataclass(frozen=True, slots=True)
class OwnershipRecord:
    """Complete ownership mapping for a single decision action."""
    action: str                      # Decision action text
    sector: str                      # Sector this decision targets
    owner_entity_type: EntityType    # Institutional entity type that owns this
    owner_role: str                  # Specific role within the entity
    owner_role_ar: str               # Arabic role name
    authority_level: AuthorityLevel
    deadline_hours: float            # Hours from trigger to required action
    escalation_path: list[str]       # Ordered escalation chain
    regulatory_reference: str        # GCC regulation or framework reference
    failure_consequence: str         # What happens if deadline is breached


# ═══════════════════════════════════════════════════════════════════════════════
# Ownership Rules — sector-keyed decision-to-owner mapping
# ═══════════════════════════════════════════════════════════════════════════════

_OWNERSHIP_RULES: list[OwnershipRecord] = [
    # ── Oil & Gas decisions ──────────────────────────────────────────────
    OwnershipRecord(
        action="Activate strategic petroleum reserve drawdown protocol",
        sector="oil_gas",
        owner_entity_type=EntityType.ENERGY_PRODUCER,
        owner_role="VP Strategic Reserves",
        owner_role_ar="نائب رئيس الاحتياطيات الاستراتيجية",
        authority_level=AuthorityLevel.STRATEGIC,
        deadline_hours=6.0,
        escalation_path=["CEO Energy Co", "Minister of Energy", "Supreme Council"],
        regulatory_reference="GCC Emergency Energy Protocol Art. 12",
        failure_consequence="Uncontrolled supply shock propagates to downstream sectors within 12h",
    ),
    OwnershipRecord(
        action="Invoke force majeure on affected export contracts",
        sector="oil_gas",
        owner_entity_type=EntityType.ENERGY_PRODUCER,
        owner_role="General Counsel",
        owner_role_ar="المستشار القانوني العام",
        authority_level=AuthorityLevel.STRATEGIC,
        deadline_hours=12.0,
        escalation_path=["CEO Energy Co", "Minister of Energy"],
        regulatory_reference="OPEC+ Supply Agreement Clause 7.3",
        failure_consequence="Contractual penalties accrue; counterparty litigation exposure",
    ),

    # ── Banking decisions ────────────────────────────────────────────────
    OwnershipRecord(
        action="Activate emergency liquidity facility for exposed banks",
        sector="banking",
        owner_entity_type=EntityType.CENTRAL_BANK,
        owner_role="Director of Financial Stability",
        owner_role_ar="مدير الاستقرار المالي",
        authority_level=AuthorityLevel.STRATEGIC,
        deadline_hours=4.0,
        escalation_path=["Deputy Governor", "Governor", "Minister of Finance"],
        regulatory_reference="Basel III LCR / Central Bank Emergency Lending Framework",
        failure_consequence="Interbank market freeze cascades to deposit withdrawals within 24h",
    ),
    OwnershipRecord(
        action="Trigger interbank exposure limit reduction",
        sector="banking",
        owner_entity_type=EntityType.CENTRAL_BANK,
        owner_role="Head of Banking Supervision",
        owner_role_ar="رئيس الرقابة المصرفية",
        authority_level=AuthorityLevel.TACTICAL,
        deadline_hours=8.0,
        escalation_path=["Director of Financial Stability", "Deputy Governor"],
        regulatory_reference="CBUAE/SAMA Prudential Regulation",
        failure_consequence="Counterparty contagion amplifies across banking system",
    ),

    # ── Insurance decisions ──────────────────────────────────────────────
    OwnershipRecord(
        action="Activate reinsurance treaty cascade notification",
        sector="insurance",
        owner_entity_type=EntityType.REINSURANCE_LAYER,
        owner_role="Chief Underwriting Officer",
        owner_role_ar="الرئيس التنفيذي للاكتتاب",
        authority_level=AuthorityLevel.STRATEGIC,
        deadline_hours=12.0,
        escalation_path=["CEO Reinsurance Entity", "Insurance Regulatory Authority"],
        regulatory_reference="IFRS 17 / Local Insurance Authority Catastrophe Protocol",
        failure_consequence="Reinsurance capacity gap forces primary insurers to hold gross exposure",
    ),
    OwnershipRecord(
        action="Suspend new policy issuance in affected lines",
        sector="insurance",
        owner_entity_type=EntityType.REINSURANCE_LAYER,
        owner_role="Head of Treaty Management",
        owner_role_ar="رئيس إدارة الاتفاقيات",
        authority_level=AuthorityLevel.TACTICAL,
        deadline_hours=24.0,
        escalation_path=["CUO", "CEO", "Insurance Authority"],
        regulatory_reference="Local Insurance Authority Directive",
        failure_consequence="Underpriced risk accumulation during crisis period",
    ),

    # ── Real Estate decisions ────────────────────────────────────────────
    OwnershipRecord(
        action="Freeze new project approvals and reassess pipeline",
        sector="real_estate",
        owner_entity_type=EntityType.REAL_ESTATE_FINANCE,
        owner_role="Chief Risk Officer",
        owner_role_ar="الرئيس التنفيذي للمخاطر",
        authority_level=AuthorityLevel.STRATEGIC,
        deadline_hours=24.0,
        escalation_path=["CEO RE Finance", "Housing Ministry", "Central Bank"],
        regulatory_reference="Real Estate Regulatory Authority Guidelines",
        failure_consequence="Continued lending into distressed market amplifies NPL wave",
    ),
    OwnershipRecord(
        action="Activate mortgage refinance forbearance program",
        sector="real_estate",
        owner_entity_type=EntityType.REAL_ESTATE_FINANCE,
        owner_role="Head of Mortgage Operations",
        owner_role_ar="رئيس عمليات الرهن العقاري",
        authority_level=AuthorityLevel.TACTICAL,
        deadline_hours=48.0,
        escalation_path=["CRO RE Finance", "Central Bank Housing Committee"],
        regulatory_reference="Central Bank Mortgage Forbearance Framework",
        failure_consequence="Foreclosure cascade depresses asset values further",
    ),

    # ── Government / Fiscal decisions ────────────────────────────────────
    OwnershipRecord(
        action="Authorize sovereign wealth fund drawdown for fiscal buffer",
        sector="government",
        owner_entity_type=EntityType.SOVEREIGN_BUFFER,
        owner_role="Chief Investment Officer",
        owner_role_ar="الرئيس التنفيذي للاستثمار",
        authority_level=AuthorityLevel.SOVEREIGN,
        deadline_hours=12.0,
        escalation_path=["Board of Directors", "Minister of Finance", "Head of State"],
        regulatory_reference="Sovereign Fund Governance Charter",
        failure_consequence="Fiscal deficit breaches sustainability threshold; credit downgrade risk",
    ),
    OwnershipRecord(
        action="Implement emergency fiscal spending controls",
        sector="government",
        owner_entity_type=EntityType.SOVEREIGN_BUFFER,
        owner_role="Director of Fiscal Policy",
        owner_role_ar="مدير السياسة المالية",
        authority_level=AuthorityLevel.STRATEGIC,
        deadline_hours=24.0,
        escalation_path=["Minister of Finance", "Cabinet"],
        regulatory_reference="GCC Fiscal Responsibility Framework",
        failure_consequence="Uncontrolled spending depletes buffer faster than revenue recovery",
    ),

    # ── Fintech / Payment decisions ──────────────────────────────────────
    OwnershipRecord(
        action="Activate payment system contingency routing",
        sector="fintech",
        owner_entity_type=EntityType.PAYMENT_RAIL,
        owner_role="Head of Payment Operations",
        owner_role_ar="رئيس عمليات المدفوعات",
        authority_level=AuthorityLevel.TACTICAL,
        deadline_hours=2.0,
        escalation_path=["CTO Payment System", "Central Bank Payment Oversight"],
        regulatory_reference="CPMI-IOSCO PFMI / National Payment System Act",
        failure_consequence="Settlement failure cascades to merchant payment delays within 4h",
    ),
    OwnershipRecord(
        action="Invoke BUNA cross-border fallback settlement",
        sector="fintech",
        owner_entity_type=EntityType.PAYMENT_RAIL,
        owner_role="Director of Cross-Border Operations",
        owner_role_ar="مدير العمليات العابرة للحدود",
        authority_level=AuthorityLevel.STRATEGIC,
        deadline_hours=6.0,
        escalation_path=["CEO Payment Entity", "AMF BUNA Committee"],
        regulatory_reference="AMF BUNA Operating Rules",
        failure_consequence="Cross-border trade settlement halts; LC confirmations frozen",
    ),

    # ── Port / Logistics decisions ───────────────────────────────────────
    OwnershipRecord(
        action="Activate port diversion and alternative routing protocol",
        sector="oil_gas",
        owner_entity_type=EntityType.PORT_OPERATOR,
        owner_role="Director of Operations",
        owner_role_ar="مدير العمليات",
        authority_level=AuthorityLevel.TACTICAL,
        deadline_hours=4.0,
        escalation_path=["CEO Port Authority", "Minister of Transport", "Maritime Authority"],
        regulatory_reference="IMO/National Maritime Authority Emergency Protocol",
        failure_consequence="Port congestion cascades to supply chain delays; perishable cargo loss",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Lookup Engine
# ═══════════════════════════════════════════════════════════════════════════════

# Index by (sector, action) for O(1) lookup
_OWNERSHIP_INDEX: dict[tuple[str, str], OwnershipRecord] = {
    (r.sector, r.action): r for r in _OWNERSHIP_RULES
}

# Index by sector for batch retrieval
_SECTOR_INDEX: dict[str, list[OwnershipRecord]] = {}
for _r in _OWNERSHIP_RULES:
    _SECTOR_INDEX.setdefault(_r.sector, []).append(_r)


def get_ownership(sector: str, action: str) -> OwnershipRecord | None:
    """Look up ownership record for a specific decision action.

    Args:
        sector: Sector code (e.g. "banking")
        action: Exact action text from decision engine

    Returns:
        OwnershipRecord or None if no mapping exists.
    """
    return _OWNERSHIP_INDEX.get((sector, action))


def get_ownership_fuzzy(sector: str, action: str) -> OwnershipRecord | None:
    """Fuzzy match: find the best ownership record for an action.

    Falls back to substring matching if exact match fails.
    """
    # Exact match first
    exact = _OWNERSHIP_INDEX.get((sector, action))
    if exact:
        return exact

    # Substring match within sector
    sector_rules = _SECTOR_INDEX.get(sector, [])
    action_lower = action.lower()
    for rule in sector_rules:
        if rule.action.lower() in action_lower or action_lower in rule.action.lower():
            return rule

    # If no sector match, return first rule for the sector as default owner
    return sector_rules[0] if sector_rules else None


def get_sector_owners(sector: str) -> list[OwnershipRecord]:
    """Get all ownership records for a given sector.

    Returns:
        List of OwnershipRecord for the sector, empty if none.
    """
    return _SECTOR_INDEX.get(sector, [])


def resolve_country_owner(
    record: OwnershipRecord,
    country_code: str,
) -> dict:
    """Resolve a country-specific owner by combining the record with entity_graph.

    Returns a dict with fully qualified owner info including entity name.
    """
    from app.domain.simulation.entity_graph import build_entity_registry

    registry = build_entity_registry()
    entity_id = f"{country_code}:{record.owner_entity_type.value}"
    entity = registry.get(entity_id)

    return {
        "country_code": country_code,
        "entity_id": entity_id,
        "entity_name": entity.name if entity else "Unknown",
        "entity_name_ar": entity.name_ar if entity else "غير معروف",
        "role": record.owner_role,
        "role_ar": record.owner_role_ar,
        "authority_level": record.authority_level.value,
        "deadline_hours": record.deadline_hours,
        "escalation_path": record.escalation_path,
        "regulatory_reference": record.regulatory_reference,
        "failure_consequence": record.failure_consequence,
    }
