"""Scenario orchestrator: baseline -> shock -> propagate -> quantify -> decide
Runs complete scenario analysis pipeline.
"""

from .baseline import compute_baseline
from .inject import inject_shocks
from .delta import compute_delta
from .explanation import generate_explanation


class PropagationResult:
    """Mock propagation result container."""

    def __init__(self):
        self.node_impacts = {}
        self.system_energy = 0.0
        self.confidence = 0.8
        self.propagation_depth = 0
        self.affected_sectors = []


class EngineResult:
    """Mock engine result container."""

    def __init__(self):
        self.total_exposure = 0.0


def run_scenario(
    nodes: list,
    edges: list,
    scenario_id: str,
    shocks: list,
    severity: float = 0.7,
    lang: str = "ar",
) -> dict:
    """
    Run complete scenario analysis pipeline.

    Args:
        nodes: List of graph nodes
        edges: List of graph edges
        scenario_id: Scenario identifier
        shocks: List of shock specifications
        severity: Scenario severity (0.0 to 1.0)
        lang: Output language (ar/en)

    Returns:
        Dictionary with complete scenario results including:
        - scenario_id, severity
        - baseline: Baseline state
        - propagation: Propagation results
        - engine_result: Engine computation results
        - delta: Impact deltas
        - explanation: Bilingual explanations
        - scientist_state: System state metrics
    """
    # Step 1: Compute baseline
    baseline = compute_baseline(nodes, edges)

    # Step 2: Inject shocks
    shocked = inject_shocks(baseline, shocks)

    # Step 3: Propagate shocks (mock)
    prop_result = PropagationResult()
    prop_result.system_energy = severity * 100
    prop_result.confidence = 0.8 + (severity * 0.1)
    prop_result.propagation_depth = max(1, int(severity * 5))
    prop_result.affected_sectors = []
    prop_result.node_impacts = {s.get("nodeId"): s.get("impact", 0) for s in shocks}

    # Step 4: Engine computation (mock)
    engine_result = EngineResult()
    total_shock_impact = sum(
        abs(s.get("impact", 0)) for s in shocks
    )
    engine_result.total_exposure = baseline.get("total_gdp", 3250) * severity * 0.1

    # Step 5: Build scientist state
    scientist_state = {
        "energy": prop_result.system_energy,
        "confidence": prop_result.confidence,
        "uncertainty": 1 - prop_result.confidence,
        "regionalStress": min(1.0, total_shock_impact),
        "shockClass": (
            "critical"
            if severity > 0.7
            else "severe"
            if severity > 0.5
            else "moderate"
        ),
        "stage": (
            "cascading"
            if prop_result.propagation_depth > 2
            else "initial"
        ),
        "propagationDepth": prop_result.propagation_depth,
        "totalExposure": engine_result.total_exposure,
        "dominantSector": (
            prop_result.affected_sectors[0] if prop_result.affected_sectors else None
        ),
    }

    # Step 6: Compute delta
    delta = compute_delta(baseline, prop_result, engine_result)

    # Step 7: Generate explanation
    explanation = generate_explanation(
        prop_result, engine_result, scientist_state, scenario_id, lang
    )

    return {
        "scenario_id": scenario_id,
        "severity": severity,
        "baseline": baseline,
        "propagation": {
            "node_impacts": prop_result.node_impacts,
            "system_energy": prop_result.system_energy,
            "confidence": prop_result.confidence,
            "propagation_depth": prop_result.propagation_depth,
        },
        "engine_result": {
            "total_exposure": engine_result.total_exposure,
        },
        "delta": delta,
        "explanation": explanation,
        "scientist_state": scientist_state,
    }
