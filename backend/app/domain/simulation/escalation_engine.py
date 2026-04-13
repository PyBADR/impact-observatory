"""
Impact Observatory | مرصد الأثر — Phase 3 Escalation Engine

Defines escalation thresholds and triggers that elevate decisions from
operational → tactical → strategic → sovereign authority levels.

Three escalation trigger categories:
  1. Entity Breach — an institutional entity's absorber capacity is exceeded
  2. Sector Cascade — sector stress exceeds SEVERE threshold across multiple countries
  3. Systemic Threshold — aggregate GCC-wide stress breaches systemic risk floor

Each trigger produces an EscalationAlert with:
  - trigger type and severity
  - affected entities/sectors/countries
  - recommended authority level
  - time-to-act deadline
  - narrative explanation
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Literal

from app.domain.simulation.entity_graph import EntityNode, EntityType
from app.domain.simulation.ownership_engine import AuthorityLevel


class EscalationTrigger(str, Enum):
    """Category of escalation trigger."""
    ENTITY_BREACH = "entity_breach"
    SECTOR_CASCADE = "sector_cascade"
    MULTI_COUNTRY_CASCADE = "multi_country_cascade"
    SYSTEMIC_THRESHOLD = "systemic_threshold"
    SOVEREIGN_BUFFER_DEPLETION = "sovereign_buffer_depletion"


class EscalationSeverity(str, Enum):
    """How urgent the escalation is."""
    WARNING = "warning"       # Approaching threshold
    CRITICAL = "critical"     # Threshold breached
    EMERGENCY = "emergency"   # Multiple thresholds breached simultaneously


@dataclass(frozen=True, slots=True)
class EscalationAlert:
    """A single escalation event requiring authority elevation."""
    trigger: EscalationTrigger
    severity: EscalationSeverity
    authority_required: AuthorityLevel
    headline: str
    headline_ar: str
    affected_entities: list[str]       # entity_ids
    affected_countries: list[str]      # country codes
    affected_sectors: list[str]        # sector codes
    time_to_act_hours: float
    narrative: str
    recommended_actions: list[str]


# ═══════════════════════════════════════════════════════════════════════════════
# Threshold Constants
# ═══════════════════════════════════════════════════════════════════════════════

SECTOR_SEVERE_THRESHOLD = 0.80     # Sector stress >= this is SEVERE
SECTOR_ELEVATED_THRESHOLD = 0.50   # >= ELEVATED
SYSTEMIC_AGGREGATE_THRESHOLD = 0.60  # GDP-weighted GCC average stress
SOVEREIGN_BUFFER_CRITICAL = 0.20   # Remaining capacity below this is critical
MULTI_COUNTRY_CASCADE_MIN = 3      # Minimum countries with ELEVATED+ stress


# ═══════════════════════════════════════════════════════════════════════════════
# Entity Breach Detection
# ═══════════════════════════════════════════════════════════════════════════════

def detect_entity_breaches(
    entities: dict[str, EntityNode],
) -> list[EscalationAlert]:
    """Detect entities whose stress exceeds their absorber capacity.

    An entity breach means the institutional buffer is exhausted —
    stress passes through to the sector-level nodes unmitigated.
    """
    alerts: list[EscalationAlert] = []

    for eid, entity in entities.items():
        if not entity.breached:
            continue

        # Sovereign buffer depletion is a special case
        if entity.entity_type == EntityType.SOVEREIGN_BUFFER:
            alerts.append(EscalationAlert(
                trigger=EscalationTrigger.SOVEREIGN_BUFFER_DEPLETION,
                severity=EscalationSeverity.EMERGENCY,
                authority_required=AuthorityLevel.SOVEREIGN,
                headline=f"{entity.name} buffer depleted — sovereign intervention required",
                headline_ar=f"نفاد احتياطي {entity.name_ar} — تدخل سيادي مطلوب",
                affected_entities=[eid],
                affected_countries=[entity.country_code],
                affected_sectors=["government", "banking"],
                time_to_act_hours=4.0,
                narrative=(
                    f"{entity.name} has exhausted its absorber capacity "
                    f"(capacity: {entity.absorber_capacity:.0%}, "
                    f"utilization: {entity.current_utilization:.0%}). "
                    f"Fiscal stress in {entity.country_code} will now propagate "
                    f"directly into banking and government sectors without buffer."
                ),
                recommended_actions=[
                    "Convene emergency sovereign wealth fund board meeting",
                    "Activate GCC mutual support mechanism",
                    "Engage IMF precautionary line communication",
                ],
            ))
            continue

        # Central bank breach
        if entity.entity_type == EntityType.CENTRAL_BANK:
            severity = EscalationSeverity.EMERGENCY
            authority = AuthorityLevel.SOVEREIGN
            time_hours = 2.0
            actions = [
                "Activate emergency lending facility at punitive rate",
                "Coordinate with GCC central banks for swap lines",
                "Prepare public communication on financial stability",
            ]
        # Reinsurance breach
        elif entity.entity_type == EntityType.REINSURANCE_LAYER:
            severity = EscalationSeverity.CRITICAL
            authority = AuthorityLevel.STRATEGIC
            time_hours = 12.0
            actions = [
                "Notify retrocession counterparties",
                "Activate catastrophe bond triggers",
                "Suspend new treaty commitments",
            ]
        # Payment rail breach
        elif entity.entity_type == EntityType.PAYMENT_RAIL:
            severity = EscalationSeverity.EMERGENCY
            authority = AuthorityLevel.STRATEGIC
            time_hours = 1.0
            actions = [
                "Switch to backup payment processing infrastructure",
                "Activate manual settlement procedures",
                "Notify all participating banks of degraded service",
            ]
        # Default for other entity types
        else:
            severity = EscalationSeverity.CRITICAL
            authority = AuthorityLevel.STRATEGIC
            time_hours = 8.0
            actions = [
                f"Activate {entity.entity_type.value} contingency protocol",
                "Notify regulatory authority",
            ]

        alerts.append(EscalationAlert(
            trigger=EscalationTrigger.ENTITY_BREACH,
            severity=severity,
            authority_required=authority,
            headline=f"{entity.name} absorber capacity breached",
            headline_ar=f"تجاوز قدرة الاستيعاب لـ {entity.name_ar}",
            affected_entities=[eid],
            affected_countries=[entity.country_code],
            affected_sectors=[],
            time_to_act_hours=time_hours,
            narrative=(
                f"{entity.name} ({entity.entity_type.value}) in {entity.country_code} "
                f"has breached its absorber capacity of {entity.absorber_capacity:.0%}. "
                f"Current stress: {entity.stress:.0%}. "
                f"Stress will now pass through to connected sector nodes."
            ),
            recommended_actions=actions,
        ))

    return alerts


# ═══════════════════════════════════════════════════════════════════════════════
# Sector Cascade Detection
# ═══════════════════════════════════════════════════════════════════════════════

def detect_sector_cascades(
    node_stresses: dict[tuple[str, str], float],
) -> list[EscalationAlert]:
    """Detect when a sector is SEVERE in multiple countries simultaneously.

    This indicates sector-wide systemic risk that requires coordinated
    GCC-level response rather than individual country action.
    """
    alerts: list[EscalationAlert] = []

    # Group stress by sector across countries
    sector_country_map: dict[str, dict[str, float]] = {}
    for (cc, sector), stress in node_stresses.items():
        sector_country_map.setdefault(sector, {})[cc] = stress

    for sector, country_stresses in sector_country_map.items():
        # Count countries at SEVERE level
        severe_countries = [
            cc for cc, stress in country_stresses.items()
            if stress >= SECTOR_SEVERE_THRESHOLD
        ]
        elevated_countries = [
            cc for cc, stress in country_stresses.items()
            if stress >= SECTOR_ELEVATED_THRESHOLD
        ]

        # Sector cascade: SEVERE in 2+ countries
        if len(severe_countries) >= 2:
            alerts.append(EscalationAlert(
                trigger=EscalationTrigger.SECTOR_CASCADE,
                severity=EscalationSeverity.EMERGENCY,
                authority_required=AuthorityLevel.SOVEREIGN,
                headline=f"{sector} sector at SEVERE across {len(severe_countries)} GCC states",
                headline_ar=f"قطاع {sector} في مستوى حاد عبر {len(severe_countries)} دول خليجية",
                affected_entities=[],
                affected_countries=severe_countries,
                affected_sectors=[sector],
                time_to_act_hours=6.0,
                narrative=(
                    f"The {sector} sector has reached SEVERE stress levels "
                    f"(≥{SECTOR_SEVERE_THRESHOLD:.0%}) in {len(severe_countries)} "
                    f"GCC states simultaneously: {', '.join(severe_countries)}. "
                    f"This constitutes a sector-wide cascade requiring coordinated response."
                ),
                recommended_actions=[
                    f"Convene GCC {sector} sector emergency coordination committee",
                    f"Activate cross-border {sector} mutual support protocols",
                    "Prepare joint public statement on sector stability measures",
                ],
            ))

        # Multi-country elevated: ELEVATED in 3+ countries (lower severity)
        elif len(elevated_countries) >= MULTI_COUNTRY_CASCADE_MIN:
            alerts.append(EscalationAlert(
                trigger=EscalationTrigger.MULTI_COUNTRY_CASCADE,
                severity=EscalationSeverity.CRITICAL,
                authority_required=AuthorityLevel.STRATEGIC,
                headline=f"{sector} sector elevated across {len(elevated_countries)} GCC states",
                headline_ar=f"قطاع {sector} مرتفع عبر {len(elevated_countries)} دول خليجية",
                affected_entities=[],
                affected_countries=elevated_countries,
                affected_sectors=[sector],
                time_to_act_hours=12.0,
                narrative=(
                    f"The {sector} sector is at ELEVATED stress (≥{SECTOR_ELEVATED_THRESHOLD:.0%}) "
                    f"in {len(elevated_countries)} GCC states: {', '.join(elevated_countries)}. "
                    f"Approaching cascade threshold — preemptive coordination recommended."
                ),
                recommended_actions=[
                    f"Alert GCC {sector} regulators to coordinate monitoring",
                    "Increase reporting frequency to daily stress snapshots",
                ],
            ))

    return alerts


# ═══════════════════════════════════════════════════════════════════════════════
# Systemic Threshold Detection
# ═══════════════════════════════════════════════════════════════════════════════

# Approximate GDP weights for GCC aggregate stress calculation
_GDP_WEIGHTS: dict[str, float] = {
    "SAU": 0.46,
    "UAE": 0.28,
    "QAT": 0.11,
    "KWT": 0.09,
    "OMN": 0.04,
    "BHR": 0.02,
}


def detect_systemic_threshold(
    node_stresses: dict[tuple[str, str], float],
) -> list[EscalationAlert]:
    """Detect when GDP-weighted average GCC stress exceeds systemic threshold.

    This is the highest-level trigger — indicates the entire GCC financial
    system is under systemic risk.
    """
    # Compute GDP-weighted average stress across all nodes
    total_weighted = 0.0
    total_weight = 0.0

    for (cc, sector), stress in node_stresses.items():
        gdp_w = _GDP_WEIGHTS.get(cc, 0.02)
        total_weighted += stress * gdp_w
        total_weight += gdp_w

    aggregate_stress = total_weighted / total_weight if total_weight > 0 else 0.0

    if aggregate_stress < SYSTEMIC_AGGREGATE_THRESHOLD:
        return []

    # Identify which countries contribute most
    country_avg: dict[str, float] = {}
    for (cc, sector), stress in node_stresses.items():
        country_avg.setdefault(cc, []).append(stress) if isinstance(
            country_avg.get(cc), list
        ) else None

    # Recompute properly
    country_avgs: dict[str, float] = {}
    country_totals: dict[str, list[float]] = {}
    for (cc, sector), stress in node_stresses.items():
        country_totals.setdefault(cc, []).append(stress)
    for cc, stresses in country_totals.items():
        country_avgs[cc] = sum(stresses) / len(stresses)

    top_contributors = sorted(country_avgs.items(), key=lambda x: -x[1])[:3]
    top_str = ", ".join(f"{cc} ({avg:.0%})" for cc, avg in top_contributors)

    return [EscalationAlert(
        trigger=EscalationTrigger.SYSTEMIC_THRESHOLD,
        severity=EscalationSeverity.EMERGENCY,
        authority_required=AuthorityLevel.SOVEREIGN,
        headline=f"GCC systemic risk threshold breached ({aggregate_stress:.0%})",
        headline_ar=f"تجاوز عتبة المخاطر النظامية الخليجية ({aggregate_stress:.0%})",
        affected_entities=[],
        affected_countries=list(_GDP_WEIGHTS.keys()),
        affected_sectors=[],
        time_to_act_hours=2.0,
        narrative=(
            f"GDP-weighted average stress across the GCC has reached "
            f"{aggregate_stress:.0%}, exceeding the systemic threshold of "
            f"{SYSTEMIC_AGGREGATE_THRESHOLD:.0%}. "
            f"Top contributors: {top_str}. "
            f"This level of aggregate stress historically precedes coordinated "
            f"market dislocations and requires immediate multi-sovereign response."
        ),
        recommended_actions=[
            "Convene GCC Financial Stability Board emergency session",
            "Activate GCC Central Bank Governors coordination hotline",
            "Prepare joint monetary policy statement",
            "Engage IMF rapid assessment team",
            "Activate cross-border deposit insurance coordination",
        ],
    )]


# ═══════════════════════════════════════════════════════════════════════════════
# Aggregate — collect all escalation alerts
# ═══════════════════════════════════════════════════════════════════════════════

def evaluate_escalations(
    entities: dict[str, EntityNode],
    node_stresses: dict[tuple[str, str], float],
) -> list[EscalationAlert]:
    """Run all escalation detectors and return sorted alerts.

    Returns alerts sorted by severity (EMERGENCY first) then time_to_act.
    """
    alerts: list[EscalationAlert] = []

    alerts.extend(detect_entity_breaches(entities))
    alerts.extend(detect_sector_cascades(node_stresses))
    alerts.extend(detect_systemic_threshold(node_stresses))

    # Sort: EMERGENCY > CRITICAL > WARNING, then shortest deadline first
    severity_order = {
        EscalationSeverity.EMERGENCY: 0,
        EscalationSeverity.CRITICAL: 1,
        EscalationSeverity.WARNING: 2,
    }
    alerts.sort(key=lambda a: (severity_order.get(a.severity, 9), a.time_to_act_hours))

    return alerts
