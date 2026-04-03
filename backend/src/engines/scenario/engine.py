"""Scenario simulation engine.

Workflow:
1. Capture baseline snapshot (current risk state)
2. Inject shock(s) from scenario definition
3. Run propagation for scenario horizon
4. Compute delta impacts (post - baseline)
5. Generate explainable narrative and recommendations
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.propagation_matrix import (
    build_adjacency_matrix,
    compute_gdp_loss,
    compute_sector_impacts,
    compute_system_confidence,
    compute_system_energy,
    propagate_multi_step,
)
from src.engines.physics.shockwave import propagate_shockwave
from src.models.canonical import (
    ImpactAssessment,
    Scenario,
    ScenarioResult,
    ScenarioShock,
    ScoreExplanation,
)


@dataclass
class GraphState:
    """Represents the current state of the intelligence graph."""

    node_ids: list[str]
    node_labels: dict[str, str]
    node_labels_ar: dict[str, str]
    node_sectors: list[str]
    sector_weights: dict[str, float]
    edges: list[dict]
    baseline_risk: NDArray[np.float64] | None = None


@dataclass
class ScenarioEngine:
    """Run scenario simulations with baseline/shock/delta/recommendation outputs."""

    graph_state: GraphState
    adjacency: NDArray[np.float64] = field(init=False)
    node_index: dict[str, int] = field(init=False)

    def __post_init__(self) -> None:
        self.adjacency = build_adjacency_matrix(self.graph_state.node_ids, self.graph_state.edges)
        self.node_index = {nid: i for i, nid in enumerate(self.graph_state.node_ids)}

    def capture_baseline(self) -> NDArray[np.float64]:
        """Capture or compute baseline risk state."""
        if self.graph_state.baseline_risk is not None:
            return self.graph_state.baseline_risk.copy()
        # Default baseline: low uniform risk
        return np.full(len(self.graph_state.node_ids), 0.05, dtype=np.float64)

    def build_shock_vector(self, shocks: list[ScenarioShock]) -> NDArray[np.float64]:
        """Convert scenario shocks to a shock vector."""
        n = len(self.graph_state.node_ids)
        shock = np.zeros(n, dtype=np.float64)
        for s in shocks:
            idx = self.node_index.get(s.target_entity_id)
            if idx is not None:
                shock[idx] = s.severity_score
        return shock

    def run(self, scenario: Scenario) -> ScenarioResult:
        """Execute full scenario simulation."""
        baseline = self.capture_baseline()
        shock_vector = self.build_shock_vector(scenario.shocks)

        # Math propagation
        final_risk, steps, history = propagate_multi_step(
            self.adjacency, baseline, shock_vector
        )

        # Physics shockwave
        origin_indices = [
            self.node_index[s.target_entity_id]
            for s in scenario.shocks
            if s.target_entity_id in self.node_index
        ]
        peak_impact, wave_history = propagate_shockwave(
            self.adjacency, origin_indices, n_steps=steps
        )

        # Merge: take max of math propagation and physics shockwave
        merged_risk = np.maximum(final_risk, peak_impact)

        # Compute impacts
        impacts = self._compute_impacts(baseline, merged_risk, scenario)

        # System metrics
        sector_impacts = compute_sector_impacts(merged_risk, self.graph_state.node_sectors)
        gdp_loss = compute_gdp_loss(sector_impacts, self.graph_state.sector_weights)
        system_energy = compute_system_energy(merged_risk)
        system_confidence = compute_system_confidence(merged_risk)

        # Top impacted
        deltas = merged_risk - baseline
        top_indices = np.argsort(deltas)[::-1][:10]
        top_impacted = [self.graph_state.node_ids[i] for i in top_indices]

        # Narrative
        narrative = self._generate_narrative(scenario, impacts, sector_impacts, gdp_loss)
        recommendations = self._generate_recommendations(impacts, sector_impacts)

        return ScenarioResult(
            scenario_id=scenario.id,
            impacts=impacts,
            system_stress=float(system_energy),
            total_economic_loss_usd=gdp_loss * 1e9,  # scale to notional
            top_impacted_entities=top_impacted,
            narrative=narrative,
            recommendations=recommendations,
            provenance=scenario.provenance,
        )

    def _compute_impacts(
        self,
        baseline: NDArray[np.float64],
        post_scenario: NDArray[np.float64],
        scenario: Scenario,
    ) -> list[ImpactAssessment]:
        """Compute per-node impact assessments."""
        impacts = []
        for i, nid in enumerate(self.graph_state.node_ids):
            b = float(baseline[i])
            p = float(post_scenario[i])
            delta = p - b

            if abs(delta) < 0.01:
                continue

            factors = [
                ScoreExplanation(
                    factor="baseline_risk",
                    weight=1.0,
                    contribution=b,
                    detail=f"Pre-scenario risk: {b:.3f}",
                ),
                ScoreExplanation(
                    factor="post_scenario_risk",
                    weight=1.0,
                    contribution=p,
                    detail=f"Post-scenario risk: {p:.3f}",
                ),
                ScoreExplanation(
                    factor="delta",
                    weight=1.0,
                    contribution=delta,
                    detail=f"Change: {delta:+.3f}",
                ),
            ]

            label = self.graph_state.node_labels.get(nid, nid)
            sector = self.graph_state.node_sectors[i] if i < len(self.graph_state.node_sectors) else "unknown"

            impacts.append(
                ImpactAssessment(
                    scenario_id=scenario.id,
                    target_entity_id=nid,
                    target_entity_type=sector,
                    baseline_score=b,
                    post_scenario_score=p,
                    delta=delta,
                    operational_impact=f"{label}: risk increased by {delta*100:.1f}pp" if delta > 0 else f"{label}: risk decreased by {abs(delta)*100:.1f}pp",
                    factors=factors,
                    provenance=scenario.provenance,
                )
            )

        impacts.sort(key=lambda x: abs(x.delta), reverse=True)
        return impacts

    def _generate_narrative(
        self,
        scenario: Scenario,
        impacts: list[ImpactAssessment],
        sector_impacts: dict[str, float],
        gdp_loss: float,
    ) -> str:
        """Generate explainable narrative for the scenario result."""
        top_3 = impacts[:3]
        most_affected_sector = max(sector_impacts, key=sector_impacts.get) if sector_impacts else "N/A"

        lines = [
            f"Scenario: {scenario.title}",
            f"Horizon: {scenario.horizon_hours}h",
            f"Shocks applied to {len(scenario.shocks)} entities.",
            f"",
            f"Most affected sector: {most_affected_sector} ({sector_impacts.get(most_affected_sector, 0)*100:.1f}% avg impact)",
            f"Estimated GDP loss factor: {gdp_loss*100:.2f}%",
            f"",
            f"Top impacted entities:",
        ]
        for imp in top_3:
            lines.append(f"  - {imp.target_entity_id}: {imp.delta*100:+.1f}pp")

        return "\n".join(lines)

    def _generate_recommendations(
        self,
        impacts: list[ImpactAssessment],
        sector_impacts: dict[str, float],
    ) -> list[str]:
        """Generate actionable recommendations based on impacts."""
        recommendations = []

        # Critical impact threshold
        critical = [i for i in impacts if i.delta > 0.3]
        if critical:
            recommendations.append(
                f"CRITICAL: {len(critical)} entities face >30pp risk increase. "
                f"Immediate mitigation required for: {', '.join(i.target_entity_id for i in critical[:3])}"
            )

        # Sector-level recommendations
        high_sectors = {k: v for k, v in sector_impacts.items() if v > 0.5}
        for sector, impact in sorted(high_sectors.items(), key=lambda x: x[1], reverse=True):
            recommendations.append(
                f"Sector '{sector}' under {impact*100:.0f}% average stress. "
                f"Consider activating contingency plans."
            )

        if not recommendations:
            recommendations.append("No critical thresholds breached. Continue monitoring.")

        return recommendations
