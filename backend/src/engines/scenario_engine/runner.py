"""Orchestrate the full scenario simulation pipeline.

Pipeline:
    1. Build adjacency matrix
    2. Capture baseline snapshot
    3. Inject scenario shocks
    4. Run math-core propagation (shockwave equation)
    5. Run physics-layer shockwave
    6. Merge propagation results
    7. Optionally compute insurance impact
    8. Compute deltas
    9. Generate explanation

All imports reference existing math_core / physics / insurance modules.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime

import numpy as np
from numpy.typing import NDArray

from src.engines.math_core.propagation import (
    build_adjacency_matrix,
    propagate_multi_step,
    compute_system_energy,
    PropagationResult,
)
from src.engines.math_core.disruption import compute_disruption_vector
from src.engines.math_core.confidence import compute_system_confidence
from src.engines.physics.shockwave import propagate_shockwave
from src.engines.insurance_intelligence.claims_surge import (
    compute_claims_surge,
    ClaimsSurgeResult,
)
from src.engines.scenario.engine import GraphState
from src.models.canonical import Scenario, ImpactAssessment, ScoreExplanation

from src.engines.scenario_engine.baseline import BaselineSnapshot, capture_baseline
from src.engines.scenario_engine.inject import inject_from_scenario, InjectionResult
from src.engines.scenario_engine.delta import (
    ScenarioDelta,
    compute_delta,
    compute_economic_impact,
    PostShockState,
)
from src.engines.scenario_engine.explanation import (
    ScenarioExplanation,
    explain_scenario,
)


@dataclass
class ScenarioRunConfig:
    """Configuration for a scenario run."""
    max_propagation_steps: int = 20
    convergence_threshold: float = 1e-4
    propagation_hops: int = 3
    include_insurance: bool = True
    include_physics: bool = True
    base_claims_usd_per_node: float = 10_000_000.0  # $10M default per node
    gdp_data: dict[str, float] | None = None  # node_id -> GDP in USD


@dataclass
class InsuranceImpact:
    """Aggregate insurance impact from scenario."""
    total_claims_uplift_pct: float
    total_estimated_delta_usd: float
    severe_count: int
    high_count: int
    node_results: list[ClaimsSurgeResult]


@dataclass
class ScenarioRunResult:
    """Complete result of a scenario simulation run."""
    scenario_id: str
    scenario_title: str
    baseline: BaselineSnapshot
    injection: InjectionResult
    propagation: PropagationResult
    post_shock_state: PostShockState
    delta: ScenarioDelta
    impacts: list[ImpactAssessment]
    insurance_impact: InsuranceImpact | None
    system_stress: float
    system_energy: float
    narrative: str
    recommendations: list[str]
    explanation: ScenarioExplanation
    execution_time_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


def _merge_risk_vectors(
    math_risk: NDArray[np.float64],
    physics_peak: NDArray[np.float64] | None,
    shock_risk: NDArray[np.float64],
) -> NDArray[np.float64]:
    """Merge math propagation, physics shockwave, and direct shock injection.

    Strategy: element-wise maximum across all three sources, clamped to [0, 1].
    """
    merged = np.maximum(math_risk, shock_risk)
    if physics_peak is not None:
        merged = np.maximum(merged, physics_peak)
    return np.clip(merged, 0.0, 1.0)


def _compute_impacts(
    node_ids: list[str],
    node_labels: dict[str, str],
    node_sectors: list[str],
    baseline_risk: NDArray[np.float64],
    post_risk: NDArray[np.float64],
    scenario_id: str,
) -> list[ImpactAssessment]:
    """Build per-node ImpactAssessment objects for nodes with material change."""
    impacts: list[ImpactAssessment] = []

    for i, nid in enumerate(node_ids):
        b = float(baseline_risk[i])
        p = float(post_risk[i])
        delta = p - b

        if abs(delta) < 0.01:
            continue

        label = node_labels.get(nid, nid)
        sector = node_sectors[i] if i < len(node_sectors) else "unknown"

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

        direction = "increased" if delta > 0 else "decreased"
        impacts.append(
            ImpactAssessment(
                scenario_id=scenario_id,
                target_entity_id=nid,
                target_entity_type=sector,
                baseline_score=b,
                post_scenario_score=p,
                delta=delta,
                operational_impact=f"{label}: risk {direction} by {abs(delta)*100:.1f}pp",
                factors=factors,
                provenance=None,  # type: ignore[arg-type]
            )
        )

    impacts.sort(key=lambda x: abs(x.delta), reverse=True)
    return impacts


def _compute_insurance_impact(
    node_ids: list[str],
    post_risk: NDArray[np.float64],
    post_disruption: NDArray[np.float64],
    exposure_vector: NDArray[np.float64],
    system_stress: float,
    base_claims_usd: float,
) -> InsuranceImpact:
    """Compute insurance claims surge for all nodes."""
    n = len(node_ids)
    results: list[ClaimsSurgeResult] = []

    for i, nid in enumerate(node_ids):
        r = compute_claims_surge(
            entity_id=nid,
            risk=float(post_risk[i]),
            disruption=float(post_disruption[i]),
            exposure=float(exposure_vector[i]),
            policy_sensitivity=0.5,  # moderate default
            base_claims_usd=base_claims_usd,
            system_stress=system_stress,
            uncertainty=0.2,  # moderate uncertainty
        )
        results.append(r)

    severe = sum(1 for r in results if r.classification == "SEVERE")
    high = sum(1 for r in results if r.classification == "HIGH")
    total_uplift = float(np.mean([r.claims_uplift_pct for r in results])) if results else 0.0
    total_delta = sum(r.estimated_claims_delta_usd for r in results)

    return InsuranceImpact(
        total_claims_uplift_pct=total_uplift,
        total_estimated_delta_usd=total_delta,
        severe_count=severe,
        high_count=high,
        node_results=results,
    )


def run_scenario(
    graph_state: GraphState,
    scenario: Scenario,
    config: ScenarioRunConfig | None = None,
) -> ScenarioRunResult:
    """Execute the full scenario simulation pipeline.

    Steps:
        1. Build adjacency matrix from graph_state edges
        2. Capture baseline snapshot
        3. Inject all scenario shocks with multi-hop propagation
        4. Run math-core shockwave propagation (R(t+1) = alpha*A*R(t) + beta*S + delta*E)
        5. Run physics-layer shockwave (optional)
        6. Merge all risk vectors (max across sources)
        7. Compute post-shock disruption
        8. Compute insurance impact (optional)
        9. Compute deltas (baseline vs post)
        10. Generate explanation and recommendations
    """
    t_start = time.perf_counter()
    cfg = config or ScenarioRunConfig()

    # 1. Adjacency
    adjacency = build_adjacency_matrix(graph_state.node_ids, graph_state.edges)
    node_index = {nid: i for i, nid in enumerate(graph_state.node_ids)}
    n = len(graph_state.node_ids)

    # 2. Baseline
    baseline = capture_baseline(graph_state)

    # 3. Inject shocks
    injection = inject_from_scenario(
        scenario=scenario,
        graph_state_node_ids=graph_state.node_ids,
        adjacency=adjacency,
        baseline=baseline,
        propagation_hops=cfg.propagation_hops,
    )

    # 4. Math-core propagation
    propagation = propagate_multi_step(
        adjacency=adjacency,
        initial_risk=baseline.risk_vector,
        shock=injection.combined_shock_vector,
        max_steps=cfg.max_propagation_steps,
        convergence_threshold=cfg.convergence_threshold,
    )

    # 5. Physics shockwave (optional)
    physics_peak: NDArray[np.float64] | None = None
    if cfg.include_physics:
        origin_indices = [
            node_index[s.target_entity_id]
            for s in scenario.shocks
            if s.target_entity_id in node_index
        ]
        if origin_indices:
            peak, _history = propagate_shockwave(
                adjacency,
                origin_indices,
                n_steps=propagation.steps or 10,
            )
            physics_peak = peak

    # 6. Merge
    merged_risk = _merge_risk_vectors(
        propagation.final_state,
        physics_peak,
        injection.modified_risk_vector,
    )

    # 7. Post-shock disruption
    post_disruption, _ = compute_disruption_vector(
        graph_state.node_ids,
        merged_risk,
    )

    # Post-shock confidence (degraded by shock intensity)
    confidence_decay = np.clip(1.0 - 0.3 * injection.combined_shock_vector, 0.3, 1.0)
    post_confidence = baseline.confidence_vector * confidence_decay

    # System metrics
    system_energy = compute_system_energy(merged_risk)
    system_stress = float(np.mean(merged_risk) + 0.5 * float(np.std(merged_risk)))
    sys_confidence = compute_system_confidence(merged_risk, post_confidence)

    # Build PostShockState
    post_state = PostShockState(
        risk_vector=merged_risk,
        disruption_vector=post_disruption,
        confidence_vector=post_confidence,
        pressure_vector=baseline.pressure_vector + 0.3 * injection.combined_shock_vector,
        system_stress=system_stress,
        system_energy=system_energy,
        system_confidence=sys_confidence,
    )

    # 8. Insurance (optional)
    insurance_impact: InsuranceImpact | None = None
    if cfg.include_insurance:
        insurance_impact = _compute_insurance_impact(
            graph_state.node_ids,
            merged_risk,
            post_disruption,
            baseline.exposure_vector,
            system_stress,
            cfg.base_claims_usd_per_node,
        )

    # 9. Delta
    delta = compute_delta(baseline, post_state)
    if cfg.gdp_data:
        economic = compute_economic_impact(delta, cfg.gdp_data, baseline.node_ids)
        delta.total_economic_impact_usd = economic

    # 10. Impacts list
    node_sectors = graph_state.node_sectors if graph_state.node_sectors else ["unknown"] * n
    impacts = _compute_impacts(
        graph_state.node_ids,
        graph_state.node_labels,
        node_sectors,
        baseline.risk_vector,
        merged_risk,
        scenario.id,
    )

    # 11. Explanation
    explanation = explain_scenario(scenario, delta, baseline, post_state, graph_state)

    t_end = time.perf_counter()

    return ScenarioRunResult(
        scenario_id=scenario.id,
        scenario_title=scenario.title,
        baseline=baseline,
        injection=injection,
        propagation=propagation,
        post_shock_state=post_state,
        delta=delta,
        impacts=impacts,
        insurance_impact=insurance_impact,
        system_stress=system_stress,
        system_energy=system_energy,
        narrative=explanation.narrative,
        recommendations=explanation.recommendations,
        explanation=explanation,
        execution_time_ms=(t_end - t_start) * 1000.0,
    )
