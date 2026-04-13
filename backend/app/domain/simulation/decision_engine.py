"""
Impact Observatory | مرصد الأثر — Phase 1 Decision Engine
Generates actionable decisions from propagation results.

Each decision includes:
  - action: what to do
  - owner: who is responsible (institutional role, not person name)
  - timing: IMMEDIATE / 24H / 72H
  - value_avoided_usd: estimated loss averted
  - downside_risk: consequence of inaction

Decision generation is rule-based and deterministic.
No LLM inference — every recommendation traces to a threshold + sector rule.
"""
from __future__ import annotations

from app.domain.simulation.propagation_engine import PropagationResult
from app.domain.simulation.schemas import DecisionAction, Urgency


# ═══════════════════════════════════════════════════════════════════════════════
# Decision Rules — sector-level playbook
# ═══════════════════════════════════════════════════════════════════════════════

# Each rule: (sector, stress_threshold, action, owner, timing, value_pct, downside)
# value_pct = fraction of total loss avoidable if this action is taken
DECISION_RULES: list[tuple[str, float, str, str, Urgency, float, str]] = [
    # Oil & Gas — highest urgency
    (
        "oil_gas", 0.50,
        "Activate strategic petroleum reserve coordination across GCC states",
        "GCC Energy Ministers Council",
        Urgency.IMMEDIATE,
        0.12,
        "Oil price spiral exceeds $140/bbl; downstream refinery shutdowns within 72h",
    ),
    (
        "oil_gas", 0.30,
        "Initiate Fujairah/Yanbu bypass routing for committed cargo",
        "National Oil Company Operations",
        Urgency.WITHIN_24H,
        0.06,
        "Shipping delays compound to 18+ days; LNG spot premiums double",
    ),

    # Banking — liquidity cascade
    (
        "banking", 0.50,
        "Open emergency central bank liquidity window with expanded collateral",
        "GCC Central Bank Governors",
        Urgency.IMMEDIATE,
        0.15,
        "Interbank rate breach triggers margin calls across GCC; credit freeze within 48h",
    ),
    (
        "banking", 0.30,
        "Coordinate bilateral FX swap lines between GCC central banks",
        "Central Bank Treasury Division",
        Urgency.WITHIN_24H,
        0.08,
        "FX reserve drawdown accelerates; peg defense costs escalate",
    ),

    # Insurance — claims surge
    (
        "insurance", 0.45,
        "Invoke catastrophe reinsurance treaties and halt new marine underwriting",
        "Chief Risk Officer — Insurance Authority",
        Urgency.IMMEDIATE,
        0.05,
        "Claims-to-premium ratio breaches solvency buffer; regulatory intervention required",
    ),
    (
        "insurance", 0.25,
        "Increase loss reserves by 30% and coordinate with Lloyd's war-risk syndicate",
        "Chief Actuary — Takaful/Insurance Sector",
        Urgency.WITHIN_24H,
        0.03,
        "Underreserved claims erode capital adequacy; credit rating downgrade risk",
    ),

    # Government — fiscal stabilization
    (
        "government", 0.40,
        "Deploy fiscal stabilization package: accelerate sovereign wealth drawdown authorization",
        "Ministry of Finance — Fiscal Policy Unit",
        Urgency.IMMEDIATE,
        0.10,
        "Delayed fiscal response amplifies private-sector credit stress; social stability risk",
    ),
    (
        "government", 0.20,
        "Pre-authorize emergency budget reallocation for energy subsidies",
        "Budget Authority — Council of Ministers",
        Urgency.WITHIN_72H,
        0.04,
        "Consumer energy cost pass-through triggers inflation above 5%",
    ),

    # Real Estate — construction freeze
    (
        "real_estate", 0.40,
        "Freeze new mega-project approvals; restructure developer credit facilities",
        "Real Estate Regulatory Authority",
        Urgency.WITHIN_24H,
        0.03,
        "Developer defaults trigger NPL cascade in banking sector",
    ),

    # Fintech — payment continuity
    (
        "fintech", 0.35,
        "Activate payment system continuity protocols; reroute settlement via BUNA",
        "Payment Systems Director — Central Bank",
        Urgency.WITHIN_24H,
        0.02,
        "Cross-border payment delays disrupt trade settlement; remittance corridors freeze",
    ),
]


# ═══════════════════════════════════════════════════════════════════════════════
# Engine
# ═══════════════════════════════════════════════════════════════════════════════

def generate_decisions(result: PropagationResult) -> list[DecisionAction]:
    """Generate decision recommendations based on propagation output.

    Iterates sector impacts and fires every rule whose stress threshold is met.
    value_avoided_usd = value_pct * total_loss.
    """
    sector_stress: dict[str, float] = {}
    for si in result.sector_impacts:
        sector_stress[si.sector.value] = si.stress

    decisions: list[DecisionAction] = []
    for sector, threshold, action, owner, timing, value_pct, downside in DECISION_RULES:
        stress = sector_stress.get(sector, 0.0)
        if stress >= threshold:
            decisions.append(DecisionAction(
                action=action,
                owner=owner,
                timing=timing,
                value_avoided_usd=round(result.total_loss_usd * value_pct, 2),
                downside_risk=downside,
            ))

    # Sort: IMMEDIATE first, then 24H, then 72H; within tier by value descending
    timing_order = {Urgency.IMMEDIATE: 0, Urgency.WITHIN_24H: 1, Urgency.WITHIN_72H: 2}
    decisions.sort(key=lambda d: (timing_order.get(d.timing, 9), -d.value_avoided_usd))

    return decisions
