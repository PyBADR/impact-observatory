"""Generate human-readable explanations of scenario outcomes.

Produces GCC-specific narratives referencing actual node names, sectors,
and calibrated severity thresholds. Designed for executive dashboards
and decision-support briefings.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray

from src.engines.scenario.engine import GraphState
from src.engines.scenario_engine.baseline import BaselineSnapshot
from src.engines.scenario_engine.delta import ScenarioDelta, PostShockState, NodeDelta
from src.models.canonical import Scenario


@dataclass
class RiskFactor:
    """A single risk factor contributing to the scenario outcome."""
    factor_name: str
    severity: str  # CRITICAL / HIGH / MODERATE / LOW
    description: str
    affected_entities: list[str]
    mitigation_hint: str


@dataclass
class ScenarioExplanation:
    """Full human-readable explanation of a scenario simulation result."""
    narrative: str
    key_findings: list[str]
    recommendations: list[str]
    risk_factors: list[RiskFactor]
    confidence_assessment: str
    executive_summary: str
    sector_narratives: dict[str, str]


# Sector display names for GCC context
_SECTOR_DISPLAY: dict[str, str] = {
    "aviation": "Aviation & Airspace",
    "maritime": "Maritime & Shipping",
    "oil": "Oil & Energy",
    "oil_sector": "Oil & Energy",
    "finance": "Financial Markets",
    "fin_markets": "Financial Markets",
    "insurance": "Insurance & Reinsurance",
    "logistics": "Logistics & Supply Chain",
    "supply_chain": "Supply Chain",
    "tourism": "Tourism & Hospitality",
    "infrastructure": "Critical Infrastructure",
    "stability": "Regional Stability",
    "economy": "Economy",
    "society": "Society & Public Sentiment",
    "unknown": "Other Sectors",
}


def _sector_display(sector: str) -> str:
    return _SECTOR_DISPLAY.get(sector, sector.replace("_", " ").title())


def _severity_emoji_text(severity: str) -> str:
    """Text-based severity marker (no emoji)."""
    return f"[{severity}]"


def _build_narrative(
    scenario: Scenario,
    delta: ScenarioDelta,
    baseline: BaselineSnapshot,
    post_state: PostShockState,
    node_labels: dict[str, str],
) -> str:
    """Build the main narrative text."""
    lines: list[str] = []

    # Header
    lines.append(f"SCENARIO ASSESSMENT: {scenario.title}")
    lines.append(f"Type: {scenario.scenario_type.upper()} | Horizon: {scenario.horizon_hours}h")
    lines.append(f"Shocks applied: {len(scenario.shocks)} entities targeted")
    lines.append("")

    # System-level summary
    lines.append("SYSTEM IMPACT:")
    lines.append(f"  System stress: {baseline.system_stress:.3f} -> {post_state.system_stress:.3f} "
                 f"(delta: {delta.stress_delta:+.3f})")
    lines.append(f"  System energy: {baseline.system_energy:.3f} -> {post_state.system_energy:.3f} "
                 f"(delta: {delta.energy_delta:+.3f})")
    lines.append(f"  System confidence: {baseline.system_confidence:.3f} -> "
                 f"{post_state.system_confidence:.3f} (delta: {delta.confidence_system_delta:+.3f})")
    lines.append(f"  Nodes above CRITICAL threshold (>30pp): {delta.nodes_above_critical}")
    lines.append(f"  Nodes above HIGH threshold (>15pp): {delta.nodes_above_high}")
    lines.append("")

    # Top impacted nodes
    lines.append("TOP IMPACTED ENTITIES:")
    for nd in delta.top_impacted[:7]:
        label = node_labels.get(nd.node_id, nd.node_id)
        lines.append(f"  {_severity_emoji_text(nd.severity_class)} {label}: "
                     f"risk {nd.risk_delta:+.3f} ({nd.risk_delta*100:+.1f}pp)")
    lines.append("")

    # Sector summary
    if delta.sector_deltas:
        lines.append("SECTOR IMPACT SUMMARY:")
        sorted_sectors = sorted(
            delta.sector_deltas.values(),
            key=lambda sd: abs(sd.mean_risk_delta),
            reverse=True,
        )
        for sd in sorted_sectors[:5]:
            display = _sector_display(sd.sector)
            lines.append(f"  {_severity_emoji_text(sd.severity_class)} {display}: "
                         f"mean risk delta {sd.mean_risk_delta:+.3f}, "
                         f"max {sd.max_risk_delta:+.3f}, "
                         f"{sd.affected_node_count} nodes affected")
        lines.append("")

    # Economic
    if delta.total_economic_impact_usd > 0:
        usd = delta.total_economic_impact_usd
        if usd >= 1e9:
            lines.append(f"ESTIMATED ECONOMIC IMPACT: ${usd/1e9:.2f}B USD")
        elif usd >= 1e6:
            lines.append(f"ESTIMATED ECONOMIC IMPACT: ${usd/1e6:.1f}M USD")
        else:
            lines.append(f"ESTIMATED ECONOMIC IMPACT: ${usd:,.0f} USD")
        lines.append("")

    return "\n".join(lines)


def _build_key_findings(
    scenario: Scenario,
    delta: ScenarioDelta,
    node_labels: dict[str, str],
) -> list[str]:
    """Extract the key findings from the delta analysis."""
    findings: list[str] = []

    # Critical nodes
    critical_nodes = [nd for nd in delta.top_impacted if nd.severity_class == "CRITICAL"]
    if critical_nodes:
        names = [node_labels.get(nd.node_id, nd.node_id) for nd in critical_nodes[:5]]
        findings.append(
            f"{len(critical_nodes)} entities reach CRITICAL impact: {', '.join(names)}. "
            f"Maximum risk increase: {delta.max_risk_increase*100:.1f} percentage points."
        )

    # High-impact nodes
    high_nodes = [nd for nd in delta.top_impacted if nd.severity_class == "HIGH"]
    if high_nodes:
        findings.append(
            f"{len(high_nodes)} additional entities at HIGH impact level, "
            f"with mean risk increase of {delta.mean_risk_increase*100:.1f}pp."
        )

    # Confidence degradation
    if delta.confidence_system_delta < -0.1:
        findings.append(
            f"System confidence degraded by {abs(delta.confidence_system_delta)*100:.1f}pp, "
            f"indicating increased uncertainty in intelligence assessments."
        )

    # Stress
    if delta.stress_delta > 0.1:
        findings.append(
            f"System stress increased by {delta.stress_delta*100:.1f}pp, "
            f"suggesting cascading pressure buildup across the network."
        )

    # Sector-level
    critical_sectors = [
        sd for sd in delta.sector_deltas.values()
        if sd.severity_class in ("CRITICAL", "HIGH")
    ]
    if critical_sectors:
        names = [_sector_display(sd.sector) for sd in critical_sectors[:3]]
        findings.append(
            f"Sectors under significant stress: {', '.join(names)}."
        )

    # Scenario type note
    if scenario.scenario_type == "cascading":
        findings.append(
            "This cascading scenario shows multi-domain propagation effects, "
            "where initial shocks amplify through network dependencies."
        )

    if not findings:
        findings.append(
            "Scenario impact is contained. No entities breach critical thresholds."
        )

    return findings


def _build_recommendations(
    delta: ScenarioDelta,
    node_labels: dict[str, str],
    scenario_type: str,
) -> list[str]:
    """Generate actionable recommendations based on delta analysis."""
    recs: list[str] = []

    # Critical-tier recommendations
    critical = [nd for nd in delta.top_impacted if nd.severity_class == "CRITICAL"]
    if critical:
        names = [node_labels.get(nd.node_id, nd.node_id) for nd in critical[:3]]
        recs.append(
            f"IMMEDIATE ACTION: Activate contingency protocols for {', '.join(names)}. "
            f"Risk levels exceed 30pp increase threshold."
        )

    # High-tier
    high = [nd for nd in delta.top_impacted if nd.severity_class == "HIGH"]
    if high:
        names = [node_labels.get(nd.node_id, nd.node_id) for nd in high[:3]]
        recs.append(
            f"ELEVATED WATCH: Increase monitoring frequency for {', '.join(names)}. "
            f"Pre-position response resources."
        )

    # Sector-specific
    for sd in sorted(delta.sector_deltas.values(), key=lambda s: abs(s.mean_risk_delta), reverse=True):
        if sd.severity_class == "CRITICAL":
            display = _sector_display(sd.sector)
            recs.append(
                f"SECTOR ALERT: {display} sector shows system-wide stress. "
                f"Recommend cross-agency coordination and alternative routing activation."
            )
        elif sd.severity_class == "HIGH":
            display = _sector_display(sd.sector)
            recs.append(
                f"SECTOR WATCH: {display} — elevate to priority monitoring. "
                f"{sd.affected_node_count} nodes affected."
            )

    # Confidence degradation
    if delta.confidence_system_delta < -0.15:
        recs.append(
            "INTELLIGENCE GAP: System confidence has degraded significantly. "
            "Recommend additional source collection and cross-validation."
        )

    # Economic
    if delta.total_economic_impact_usd > 1e9:
        recs.append(
            f"ECONOMIC EXPOSURE: Estimated impact exceeds ${delta.total_economic_impact_usd/1e9:.1f}B. "
            f"Brief finance ministry and central bank on exposure."
        )

    # Scenario-type specific
    if scenario_type == "cascading" and delta.nodes_above_high > 5:
        recs.append(
            "CASCADE RISK: Multiple nodes in escalation chain. "
            "Consider preemptive isolation of highest-centrality nodes to contain spread."
        )

    if not recs:
        recs.append(
            "No critical thresholds breached. Continue standard monitoring posture."
        )

    return recs


def _build_risk_factors(
    delta: ScenarioDelta,
    scenario: Scenario,
    node_labels: dict[str, str],
) -> list[RiskFactor]:
    """Identify distinct risk factors from the scenario outcome."""
    factors: list[RiskFactor] = []

    # Direct shock targets
    shock_targets = [s.target_entity_id for s in scenario.shocks]
    shock_labels = [node_labels.get(t, t) for t in shock_targets]
    high_severity = [s for s in scenario.shocks if s.severity_score >= 0.8]

    if high_severity:
        factors.append(RiskFactor(
            factor_name="Direct High-Severity Shocks",
            severity="CRITICAL" if any(s.severity_score >= 0.9 for s in high_severity) else "HIGH",
            description=(
                f"{len(high_severity)} shocks with severity >= 0.8 applied directly "
                f"to network nodes."
            ),
            affected_entities=[node_labels.get(s.target_entity_id, s.target_entity_id)
                               for s in high_severity[:5]],
            mitigation_hint="Harden directly-targeted assets and activate backup systems.",
        ))

    # Network cascade
    cascade_nodes = [nd for nd in delta.top_impacted
                     if nd.node_id not in shock_targets and nd.severity_class in ("CRITICAL", "HIGH")]
    if cascade_nodes:
        factors.append(RiskFactor(
            factor_name="Network Cascade Propagation",
            severity="HIGH",
            description=(
                f"{len(cascade_nodes)} nodes impacted through network propagation "
                f"despite not being directly targeted."
            ),
            affected_entities=[node_labels.get(nd.node_id, nd.node_id)
                               for nd in cascade_nodes[:5]],
            mitigation_hint="Review network topology for single-point-of-failure dependencies.",
        ))

    # Confidence erosion
    if delta.confidence_system_delta < -0.1:
        factors.append(RiskFactor(
            factor_name="Intelligence Confidence Erosion",
            severity="MODERATE",
            description=(
                f"System confidence dropped by {abs(delta.confidence_system_delta)*100:.1f}pp, "
                f"reducing decision reliability."
            ),
            affected_entities=["System-wide"],
            mitigation_hint="Increase source diversity and cross-validation frequency.",
        ))

    # Pressure buildup
    pressure_nodes = [nd for nd in delta.top_impacted if nd.pressure_delta > 0.2]
    if pressure_nodes:
        factors.append(RiskFactor(
            factor_name="Pressure Buildup",
            severity="MODERATE",
            description=(
                f"{len(pressure_nodes)} nodes show significant pressure accumulation, "
                f"indicating potential for secondary failures."
            ),
            affected_entities=[node_labels.get(nd.node_id, nd.node_id)
                               for nd in pressure_nodes[:5]],
            mitigation_hint="Redistribute traffic/load away from pressured nodes.",
        ))

    return factors


def _build_confidence_assessment(
    delta: ScenarioDelta,
    baseline: BaselineSnapshot,
    post_state: PostShockState,
) -> str:
    """Assess confidence in the scenario simulation results."""
    conf = post_state.system_confidence

    if conf >= 0.8:
        level = "HIGH"
        note = (
            "Simulation results are supported by high-confidence intelligence. "
            "Input signals show strong corroboration."
        )
    elif conf >= 0.6:
        level = "MODERATE"
        note = (
            "Results carry moderate confidence. Some input signals lack full corroboration. "
            "Treat magnitude estimates as directionally correct with +/-15% uncertainty."
        )
    elif conf >= 0.4:
        level = "LOW"
        note = (
            "Confidence is below acceptable thresholds. Key inputs are poorly corroborated. "
            "Results should be treated as indicative only. Additional intelligence collection recommended."
        )
    else:
        level = "VERY LOW"
        note = (
            "Simulation confidence is critically low. Input data quality is insufficient "
            "for operational decision-making. Results are exploratory only."
        )

    degradation = ""
    if delta.confidence_system_delta < -0.05:
        degradation = (
            f" Confidence degraded by {abs(delta.confidence_system_delta)*100:.1f}pp "
            f"due to scenario shock effects on data quality."
        )

    return f"CONFIDENCE: {level}. {note}{degradation}"


def _build_sector_narratives(
    delta: ScenarioDelta,
    node_labels: dict[str, str],
) -> dict[str, str]:
    """Generate per-sector narrative descriptions."""
    narratives: dict[str, str] = {}

    for sector, sd in delta.sector_deltas.items():
        display = _sector_display(sector)

        if sd.severity_class == "CRITICAL":
            narratives[sector] = (
                f"{display} faces critical disruption with mean risk increase of "
                f"{sd.mean_risk_delta*100:.1f}pp across {sd.affected_node_count} nodes. "
                f"Peak node risk delta: {sd.max_risk_delta*100:.1f}pp. "
                f"Immediate sector-wide response required."
            )
        elif sd.severity_class == "HIGH":
            narratives[sector] = (
                f"{display} experiences elevated stress. Mean risk increased by "
                f"{sd.mean_risk_delta*100:.1f}pp with {sd.affected_node_count} nodes affected. "
                f"Enhanced monitoring and contingency activation recommended."
            )
        elif sd.severity_class == "MODERATE":
            narratives[sector] = (
                f"{display} shows moderate impact ({sd.mean_risk_delta*100:.1f}pp mean increase). "
                f"Current capacity should absorb the shock, but watchlist status recommended."
            )
        else:
            narratives[sector] = (
                f"{display} impact is minimal ({sd.mean_risk_delta*100:.1f}pp mean). "
                f"No action required; continue standard monitoring."
            )

    return narratives


def _build_executive_summary(
    scenario: Scenario,
    delta: ScenarioDelta,
    post_state: PostShockState,
) -> str:
    """One-paragraph executive summary."""
    severity = "critical" if delta.nodes_above_critical > 0 else (
        "significant" if delta.nodes_above_high > 0 else "contained"
    )

    top_node = delta.top_impacted[0] if delta.top_impacted else None
    top_name = top_node.node_id if top_node else "N/A"

    economic = ""
    if delta.total_economic_impact_usd > 0:
        if delta.total_economic_impact_usd >= 1e9:
            economic = f" Estimated economic exposure: ${delta.total_economic_impact_usd/1e9:.1f}B."
        else:
            economic = f" Estimated economic exposure: ${delta.total_economic_impact_usd/1e6:.0f}M."

    return (
        f"The '{scenario.title}' scenario produces {severity} impact across the GCC "
        f"intelligence network over a {scenario.horizon_hours}h horizon. "
        f"{delta.nodes_above_critical} nodes breach critical thresholds and "
        f"{delta.nodes_above_high} exceed high-impact levels. "
        f"The most impacted entity is {top_name} "
        f"(+{delta.max_risk_increase*100:.1f}pp risk). "
        f"System stress moved from {post_state.system_stress - delta.stress_delta:.3f} "
        f"to {post_state.system_stress:.3f}.{economic}"
    )


def explain_scenario(
    scenario: Scenario,
    delta: ScenarioDelta,
    baseline: BaselineSnapshot,
    post_state: PostShockState,
    graph_state: GraphState,
) -> ScenarioExplanation:
    """Generate a complete human-readable explanation of scenario outcomes.

    Args:
        scenario: The scenario definition that was simulated.
        delta: Computed delta between baseline and post-shock.
        baseline: Pre-shock baseline snapshot.
        post_state: Post-shock system state.
        graph_state: The intelligence graph (for node labels, sectors).

    Returns:
        ScenarioExplanation with narrative, findings, recommendations, and risk factors.
    """
    node_labels = graph_state.node_labels or {}

    narrative = _build_narrative(scenario, delta, baseline, post_state, node_labels)
    key_findings = _build_key_findings(scenario, delta, node_labels)
    recommendations = _build_recommendations(delta, node_labels, scenario.scenario_type)
    risk_factors = _build_risk_factors(delta, scenario, node_labels)
    confidence_assessment = _build_confidence_assessment(delta, baseline, post_state)
    sector_narratives = _build_sector_narratives(delta, node_labels)
    executive_summary = _build_executive_summary(scenario, delta, post_state)

    return ScenarioExplanation(
        narrative=narrative,
        key_findings=key_findings,
        recommendations=recommendations,
        risk_factors=risk_factors,
        confidence_assessment=confidence_assessment,
        executive_summary=executive_summary,
        sector_narratives=sector_narratives,
    )
