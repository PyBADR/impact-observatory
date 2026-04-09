"""Macro Intelligence Layer — Decision Engine (Pack 3).

Deterministic mapping from MacroImpact → DecisionOutput.

Algorithm:
  1. Map overall_severity_level → DecisionPriority (primary rule)
  2. For each DomainImpact, derive recommended action(s):
       - Entry domains get the primary action for the severity tier
       - Downstream domains get proportional actions based on their severity
       - High-exposure domains (weight >= 0.85) get an additional ESCALATE if
         severity >= HIGH
       - Domain-specific overrides apply (OIL_GAS, BANKING, SOVEREIGN_FISCAL)
  3. Deduplicate actions (same action_type + domain = keep highest urgency)
  4. Sort by urgency: immediate > within_24h > within_72h > routine
  5. Compose decision_reasoning (propagation + graph fragments)
  6. Set requires_escalation = priority in {ALERT, CRITICAL}

Design rules:
  - Pure function: same MacroImpact → same DecisionOutput
  - No external state, no ML, no LLM
  - Preserves full propagation + graph reasoning in decision_reasoning
  - All action descriptions are deterministic templates (no dynamic text from AI)
"""

from __future__ import annotations

from src.macro.macro_enums import (
    ImpactDomain,
    SignalSeverity,
)
from src.macro.impact.impact_models import DomainImpact, MacroImpact
from src.macro.decision.decision_models import (
    ActionType,
    DecisionAction,
    DecisionOutput,
    DecisionPriority,
)


# ── Priority Mapping ──────────────────────────────────────────────────────────

_SEVERITY_TO_PRIORITY: dict[SignalSeverity, DecisionPriority] = {
    SignalSeverity.NOMINAL:   DecisionPriority.ROUTINE,
    SignalSeverity.LOW:       DecisionPriority.WATCH,
    SignalSeverity.GUARDED:   DecisionPriority.WATCH,
    SignalSeverity.ELEVATED:  DecisionPriority.ADVISORY,
    SignalSeverity.HIGH:      DecisionPriority.ALERT,
    SignalSeverity.SEVERE:    DecisionPriority.CRITICAL,
}


def _map_severity_to_priority(level: SignalSeverity) -> DecisionPriority:
    return _SEVERITY_TO_PRIORITY.get(level, DecisionPriority.ROUTINE)


# ── Urgency Mapping ───────────────────────────────────────────────────────────

_URGENCY_ORDER = ["immediate", "within_24h", "within_72h", "routine"]

_PRIORITY_TO_URGENCY: dict[DecisionPriority, str] = {
    DecisionPriority.CRITICAL:  "immediate",
    DecisionPriority.ALERT:     "within_24h",
    DecisionPriority.ADVISORY:  "within_72h",
    DecisionPriority.WATCH:     "routine",
    DecisionPriority.ROUTINE:   "routine",
}


def _urgency_rank(urgency: str) -> int:
    """Lower rank = higher urgency. For sort ordering."""
    try:
        return _URGENCY_ORDER.index(urgency)
    except ValueError:
        return len(_URGENCY_ORDER)


# ── Action Templates ──────────────────────────────────────────────────────────
# Deterministic action descriptions keyed by (ActionType, ImpactDomain).
# Fallback to generic templates when domain-specific override not present.

_DOMAIN_ACTION_DESCRIPTIONS: dict[tuple[ActionType, ImpactDomain], str] = {
    # OIL_GAS actions
    (ActionType.MONITOR, ImpactDomain.OIL_GAS):
        "Monitor crude production metrics and export volumes for early stress indicators.",
    (ActionType.REVIEW, ImpactDomain.OIL_GAS):
        "Review oil export hedging positions and sovereign revenue projections.",
    (ActionType.HEDGE, ImpactDomain.OIL_GAS):
        "Hedge crude price exposure; engage buffer stock mechanisms.",
    (ActionType.ESCALATE, ImpactDomain.OIL_GAS):
        "Escalate to Ministry of Energy and sovereign wealth fund leadership.",
    (ActionType.ACTIVATE_CONTINGENCY, ImpactDomain.OIL_GAS):
        "Activate national strategic petroleum reserve and export diversion protocols.",

    # BANKING actions
    (ActionType.MONITOR, ImpactDomain.BANKING):
        "Monitor interbank liquidity rates and NPL ratios.",
    (ActionType.REVIEW, ImpactDomain.BANKING):
        "Review credit book exposure to affected sectors; check liquidity coverage ratio.",
    (ActionType.HEDGE, ImpactDomain.BANKING):
        "Reduce concentrated sector exposure; increase liquid asset buffers.",
    (ActionType.ESCALATE, ImpactDomain.BANKING):
        "Escalate to central bank supervisory unit and ALCO.",
    (ActionType.ACTIVATE_CONTINGENCY, ImpactDomain.BANKING):
        "Activate emergency liquidity facility; notify central bank of systemic risk.",

    # SOVEREIGN_FISCAL actions
    (ActionType.MONITOR, ImpactDomain.SOVEREIGN_FISCAL):
        "Monitor government revenue receipts and deficit projections.",
    (ActionType.REVIEW, ImpactDomain.SOVEREIGN_FISCAL):
        "Review fiscal buffers and discretionary spending commitments.",
    (ActionType.HEDGE, ImpactDomain.SOVEREIGN_FISCAL):
        "Activate sovereign wealth fund drawdown protocol; review debt issuance timing.",
    (ActionType.ESCALATE, ImpactDomain.SOVEREIGN_FISCAL):
        "Escalate to Ministry of Finance and central bank governor.",
    (ActionType.ACTIVATE_CONTINGENCY, ImpactDomain.SOVEREIGN_FISCAL):
        "Activate fiscal emergency protocols; notify IMF Article IV liaison.",

    # TRADE_LOGISTICS actions
    (ActionType.MONITOR, ImpactDomain.TRADE_LOGISTICS):
        "Monitor port throughput, shipping rates, and transit times.",
    (ActionType.REVIEW, ImpactDomain.TRADE_LOGISTICS):
        "Review supply chain dependencies and alternate routing capacity.",
    (ActionType.HEDGE, ImpactDomain.TRADE_LOGISTICS):
        "Pre-position strategic inventory; activate alternate supplier agreements.",
    (ActionType.ESCALATE, ImpactDomain.TRADE_LOGISTICS):
        "Escalate to transport ministry and customs authority.",
    (ActionType.ACTIVATE_CONTINGENCY, ImpactDomain.TRADE_LOGISTICS):
        "Activate trade corridor emergency protocols and strategic reserve drawdown.",

    # CAPITAL_MARKETS actions
    (ActionType.MONITOR, ImpactDomain.CAPITAL_MARKETS):
        "Monitor equity indices, FX rates, and credit spreads.",
    (ActionType.REVIEW, ImpactDomain.CAPITAL_MARKETS):
        "Review portfolio VaR and mark-to-market exposures.",
    (ActionType.HEDGE, ImpactDomain.CAPITAL_MARKETS):
        "Reduce equity exposure; increase safe-haven allocation.",
    (ActionType.ALERT_STAKEHOLDERS, ImpactDomain.CAPITAL_MARKETS):
        "Issue market alert to institutional investors and exchange operators.",
    (ActionType.ESCALATE, ImpactDomain.CAPITAL_MARKETS):
        "Escalate to securities regulator and exchange circuit-breaker committee.",

    # ENERGY_GRID actions
    (ActionType.MONITOR, ImpactDomain.ENERGY_GRID):
        "Monitor grid load, reserve margins, and generation capacity.",
    (ActionType.REVIEW, ImpactDomain.ENERGY_GRID):
        "Review demand response protocols and cross-border interconnect status.",
    (ActionType.HEDGE, ImpactDomain.ENERGY_GRID):
        "Pre-position fuel reserves; activate demand curtailment standby.",
    (ActionType.ACTIVATE_CONTINGENCY, ImpactDomain.ENERGY_GRID):
        "Activate national grid emergency load-shedding and backup generation protocols.",

    # MARITIME actions
    (ActionType.MONITOR, ImpactDomain.MARITIME):
        "Monitor vessel traffic, port congestion, and chokepoint status.",
    (ActionType.REVIEW, ImpactDomain.MARITIME):
        "Review maritime insurance coverage and alternate routing options.",
    (ActionType.HEDGE, ImpactDomain.MARITIME):
        "Pre-position alternative shipping routes; engage maritime insurer.",
    (ActionType.ESCALATE, ImpactDomain.MARITIME):
        "Escalate to coast guard and maritime authority.",

    # INSURANCE actions
    (ActionType.MONITOR, ImpactDomain.INSURANCE):
        "Monitor claims pipeline and reinsurance treaty triggers.",
    (ActionType.REVIEW, ImpactDomain.INSURANCE):
        "Review catastrophe reserve adequacy and reinsurance recoveries.",
    (ActionType.HEDGE, ImpactDomain.INSURANCE):
        "Retrocede peak risk exposure; review policy exclusion clauses.",

    # REAL_ESTATE actions
    (ActionType.MONITOR, ImpactDomain.REAL_ESTATE):
        "Monitor property transaction volumes and mortgage NPL ratios.",
    (ActionType.REVIEW, ImpactDomain.REAL_ESTATE):
        "Review collateral valuations and development pipeline exposure.",
    (ActionType.HEDGE, ImpactDomain.REAL_ESTATE):
        "Pause non-committed development approvals; increase provisioning.",

    # TELECOMMUNICATIONS actions
    (ActionType.MONITOR, ImpactDomain.TELECOMMUNICATIONS):
        "Monitor network uptime, latency, and critical infrastructure dependencies.",
    (ActionType.REVIEW, ImpactDomain.TELECOMMUNICATIONS):
        "Review business continuity plans and redundancy provisions.",

    # AVIATION actions
    (ActionType.MONITOR, ImpactDomain.AVIATION):
        "Monitor airspace restrictions, carrier capacity, and airport throughput.",
    (ActionType.REVIEW, ImpactDomain.AVIATION):
        "Review fuel hedge positions and route contingency plans.",
    (ActionType.PAUSE_OPERATIONS, ImpactDomain.AVIATION):
        "Implement precautionary operational pause on affected routes.",

    # CYBER_INFRASTRUCTURE actions
    (ActionType.MONITOR, ImpactDomain.CYBER_INFRASTRUCTURE):
        "Monitor threat intelligence feeds and critical system anomaly detection.",
    (ActionType.REVIEW, ImpactDomain.CYBER_INFRASTRUCTURE):
        "Review incident response readiness and patch status for critical systems.",
    (ActionType.ALERT_STAKEHOLDERS, ImpactDomain.CYBER_INFRASTRUCTURE):
        "Issue cyber threat advisory to CERT and critical infrastructure operators.",
    (ActionType.ACTIVATE_CONTINGENCY, ImpactDomain.CYBER_INFRASTRUCTURE):
        "Activate national cyber incident response protocol.",
}

_GENERIC_DESCRIPTIONS: dict[ActionType, str] = {
    ActionType.NO_ACTION:            "No action required at this time.",
    ActionType.MONITOR:              "Monitor domain-level indicators for early stress signals.",
    ActionType.REVIEW:               "Conduct active review of positions and exposure in this domain.",
    ActionType.HEDGE:                "Hedge or reduce exposure in this domain.",
    ActionType.ALERT_STAKEHOLDERS:   "Issue formal alert to relevant stakeholders.",
    ActionType.PAUSE_OPERATIONS:     "Pause non-critical operations in this domain.",
    ActionType.ESCALATE:             "Escalate to senior decision makers for immediate review.",
    ActionType.ACTIVATE_CONTINGENCY: "Activate contingency and recovery protocols.",
}


def _get_action_description(action_type: ActionType, domain: ImpactDomain) -> str:
    return _DOMAIN_ACTION_DESCRIPTIONS.get(
        (action_type, domain),
        _GENERIC_DESCRIPTIONS.get(action_type, "Action required."),
    )


# ── Domain Action Rules ───────────────────────────────────────────────────────

# Primary action per severity level (applies to all domains at that severity)
_SEVERITY_PRIMARY_ACTION: dict[SignalSeverity, ActionType] = {
    SignalSeverity.NOMINAL:   ActionType.NO_ACTION,
    SignalSeverity.LOW:       ActionType.MONITOR,
    SignalSeverity.GUARDED:   ActionType.MONITOR,
    SignalSeverity.ELEVATED:  ActionType.REVIEW,
    SignalSeverity.HIGH:      ActionType.HEDGE,
    SignalSeverity.SEVERE:    ActionType.ACTIVATE_CONTINGENCY,
}

# Secondary action for domains with exposure_weight >= 0.85 at elevated severity
_HIGH_EXPOSURE_ESCALATION_THRESHOLD = 0.85
_HIGH_EXPOSURE_ESCALATION_SEVERITY = SignalSeverity.HIGH

# Domain-specific override: always ESCALATE at HIGH+ severity
_ALWAYS_ESCALATE_DOMAINS: set[ImpactDomain] = {
    ImpactDomain.BANKING,
    ImpactDomain.SOVEREIGN_FISCAL,
    ImpactDomain.OIL_GAS,
}

# Severity values in ascending order for comparison
_SEVERITY_RANK: dict[SignalSeverity, int] = {
    SignalSeverity.NOMINAL:  0,
    SignalSeverity.LOW:      1,
    SignalSeverity.GUARDED:  2,
    SignalSeverity.ELEVATED: 3,
    SignalSeverity.HIGH:     4,
    SignalSeverity.SEVERE:   5,
}


def _severity_gte(a: SignalSeverity, b: SignalSeverity) -> bool:
    return _SEVERITY_RANK.get(a, 0) >= _SEVERITY_RANK.get(b, 0)


# ── Action Builder ────────────────────────────────────────────────────────────

def _make_action(
    action_type: ActionType,
    domain: ImpactDomain,
    urgency: str,
    severity_score: float,
    exposure_weight: float,
    depth: int,
) -> DecisionAction:
    description = _get_action_description(action_type, domain)
    rationale = (
        f"{domain.value} requires {action_type.value.replace('_', ' ')} "
        f"(severity={severity_score:.4f}, exposure_weight={exposure_weight:.2f}, "
        f"depth={depth})."
    )
    return DecisionAction(
        action_id=f"{action_type.value}:{domain.value}",
        domain=domain,
        action_type=action_type,
        description=description,
        urgency=urgency,
        rationale=rationale,
    )


def _derive_actions_for_domain(
    di: DomainImpact,
    overall_priority: DecisionPriority,
) -> list[DecisionAction]:
    """Derive recommended actions for a single DomainImpact.

    Rules applied in order:
      1. Primary action from di.severity_level
      2. ESCALATE if domain is in _ALWAYS_ESCALATE_DOMAINS and severity >= HIGH
      3. ESCALATE if exposure_weight >= threshold and severity >= HIGH
      4. ALERT_STAKEHOLDERS for CAPITAL_MARKETS at ELEVATED+
    """
    actions: list[DecisionAction] = []
    urgency = _PRIORITY_TO_URGENCY.get(overall_priority, "routine")

    # ── Rule 1: Primary action from domain's own severity ─────────────────────
    primary_action_type = _SEVERITY_PRIMARY_ACTION.get(
        di.severity_level, ActionType.MONITOR
    )
    if primary_action_type != ActionType.NO_ACTION:
        actions.append(_make_action(
            primary_action_type, di.domain, urgency,
            di.severity_score, di.exposure_weight, di.depth,
        ))

    # Skip supplementary rules if NOMINAL
    if di.severity_level == SignalSeverity.NOMINAL:
        return actions

    # ── Rule 2: Always escalate key systemic domains at HIGH+ ─────────────────
    if (
        di.domain in _ALWAYS_ESCALATE_DOMAINS
        and _severity_gte(di.severity_level, _HIGH_EXPOSURE_ESCALATION_SEVERITY)
        and ActionType.ESCALATE != primary_action_type
    ):
        actions.append(_make_action(
            ActionType.ESCALATE, di.domain, urgency,
            di.severity_score, di.exposure_weight, di.depth,
        ))

    # ── Rule 3: High-exposure domains escalate at HIGH+ ───────────────────────
    elif (
        di.exposure_weight >= _HIGH_EXPOSURE_ESCALATION_THRESHOLD
        and _severity_gte(di.severity_level, _HIGH_EXPOSURE_ESCALATION_SEVERITY)
        and ActionType.ESCALATE != primary_action_type
        and di.domain not in _ALWAYS_ESCALATE_DOMAINS  # already handled above
    ):
        actions.append(_make_action(
            ActionType.ESCALATE, di.domain, urgency,
            di.severity_score, di.exposure_weight, di.depth,
        ))

    # ── Rule 4: Capital markets alert at ELEVATED+ ────────────────────────────
    if (
        di.domain == ImpactDomain.CAPITAL_MARKETS
        and _severity_gte(di.severity_level, SignalSeverity.ELEVATED)
        and ActionType.ALERT_STAKEHOLDERS != primary_action_type
    ):
        actions.append(_make_action(
            ActionType.ALERT_STAKEHOLDERS, di.domain, urgency,
            di.severity_score, di.exposure_weight, di.depth,
        ))

    return actions


# ── Reasoning Composer ────────────────────────────────────────────────────────

def _compose_decision_reasoning(
    impact: MacroImpact,
    priority: DecisionPriority,
    actions: list[DecisionAction],
) -> str:
    """Compose full decision reasoning from impact data.

    Includes:
      1. Decision summary line
      2. Action rationale per action
      3. Domain propagation reasoning (preserves [Graph Brain] fragments)
    """
    lines = [
        f"Decision: {priority.value.upper()} — "
        f"{impact.overall_severity_level.value.upper()} severity "
        f"across {impact.total_domains_reached} domain(s) "
        f"(exposure_score={impact.total_exposure_score:.4f}, "
        f"confidence={impact.confidence.value}).",
        "",
        "Recommended actions:",
    ]
    for a in actions:
        lines.append(f"  [{a.action_type.value}] {a.domain.value}: {a.rationale}")

    lines.append("")
    lines.append("--- Impact reasoning (propagation + graph) ---")
    lines.append(impact.impact_reasoning)

    return "\n".join(lines)


def _compose_impact_summary(impact: MacroImpact, priority: DecisionPriority) -> str:
    """One-sentence summary for dashboard display."""
    top_domain = (
        impact.domain_impacts[0].domain.value
        if impact.domain_impacts else "no domains"
    )
    return (
        f"{priority.value.upper()} priority: "
        f"{impact.overall_severity_level.value} severity signal "
        f"reaching {impact.total_domains_reached} domain(s); "
        f"most affected: {top_domain}."
    )


# ── Core Engine ───────────────────────────────────────────────────────────────

def map_impact_to_decision(impact: MacroImpact) -> DecisionOutput:
    """Map a MacroImpact to a deterministic DecisionOutput.

    This is the primary entry point for the Decision Brain.

    Algorithm:
      1. Derive overall priority from impact.overall_severity_level
      2. For each DomainImpact, derive recommended actions
      3. Deduplicate: keep one action per (action_type, domain)
         — first occurrence wins (already ordered by impact severity)
      4. Sort: by urgency rank asc, then by domain severity desc
      5. Compose reasoning (preserves propagation + graph fragments)
      6. Set requires_escalation if priority in {ALERT, CRITICAL}

    Args:
        impact: A MacroImpact from compute_impact().

    Returns:
        DecisionOutput — always valid, never raises. Zero-impact inputs
        return a ROUTINE decision with no actions.
    """
    # ── Step 1: Overall priority ──────────────────────────────────────────────
    priority = _map_severity_to_priority(impact.overall_severity_level)

    # ── Step 2: Derive actions per domain ────────────────────────────────────
    # domain_impacts is already sorted severity desc from impact_engine
    all_actions: list[DecisionAction] = []
    for di in impact.domain_impacts:
        all_actions.extend(_derive_actions_for_domain(di, priority))

    # ── Step 3: Deduplicate (action_id = action_type:domain) ─────────────────
    seen_ids: set[str] = set()
    deduped: list[DecisionAction] = []
    for a in all_actions:
        if a.action_id not in seen_ids:
            seen_ids.add(a.action_id)
            deduped.append(a)

    # ── Step 4: Sort (highest urgency first, then domain severity desc) ───────
    # Build domain severity map for secondary sort key
    domain_severity: dict[ImpactDomain, float] = {
        di.domain: di.severity_score for di in impact.domain_impacts
    }
    deduped.sort(key=lambda a: (
        _urgency_rank(a.urgency),                               # primary: urgency asc
        -domain_severity.get(a.domain, 0.0),                   # secondary: severity desc
    ))

    # ── Step 5: Handle NOMINAL (no actions) ──────────────────────────────────
    # For NOMINAL severity, emit a single NO_ACTION for the first entry domain
    if priority == DecisionPriority.ROUTINE and not deduped and impact.entry_domains:
        first_entry = impact.entry_domains[0]
        deduped.append(DecisionAction(
            action_id=f"no_action:{first_entry.value}",
            domain=first_entry,
            action_type=ActionType.NO_ACTION,
            description=_GENERIC_DESCRIPTIONS[ActionType.NO_ACTION],
            urgency="routine",
            rationale=(
                f"Overall severity is NOMINAL ({impact.overall_severity:.4f}); "
                "no material response required at this time."
            ),
        ))

    # ── Step 6: Requires escalation ──────────────────────────────────────────
    requires_escalation = priority in {DecisionPriority.ALERT, DecisionPriority.CRITICAL}

    # ── Step 7: Compose reasoning ─────────────────────────────────────────────
    decision_reasoning = _compose_decision_reasoning(impact, priority, deduped)
    impact_summary = _compose_impact_summary(impact, priority)

    return DecisionOutput(
        signal_id=impact.signal_id,
        signal_title=impact.signal_title,
        priority=priority,
        requires_escalation=requires_escalation,
        recommended_actions=deduped,
        affected_domains=list(impact.affected_domains),
        overall_severity=impact.overall_severity,
        overall_severity_level=impact.overall_severity_level,
        confidence=impact.confidence,
        total_domains_reached=impact.total_domains_reached,
        impact_summary=impact_summary,
        decision_reasoning=decision_reasoning,
    )
