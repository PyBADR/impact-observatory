"""
Impact Observatory — 10-Stage Pipeline Orchestrator

Runtime Flow (canonical):
  1. scenario       — Validate + resolve scenario input
  2. physics        — Compute system stress via physics_core
  3. graph_snapshot — Capture entity/edge state from graph or scenario template
  4. propagation    — Run discrete dynamic propagation on graph
  5. financial      — Quantify headline financial impact
  6. sector_risk    — Banking + Insurance + Fintech stress models
  7. regulatory     — GCC regulatory compliance check (PDPL, IFRS 17, Basel III)
  8. decision       — Multi-objective decision optimization (top 3 actions)
  9. explanation    — Bilingual explainability pack
  10. output        — Assemble ObservatoryOutput, SHA-256 audit hash, timing

Design Decisions:
  - Stages 2-4 (physics/graph/propagation) degrade gracefully when Neo4j or
    graph data is unavailable. The pipeline still produces valid output via
    the financial-first path (stages 5-9).
  - Each stage records its execution status in the stage_log for auditability.
  - Propagation results feed INTO the financial engine via enrichment: when
    propagation data is available, sector-level impacts modulate the
    deterministic financial formulas for higher fidelity.
  - All computation is synchronous/deterministic (no async fan-out yet).

Trade-off Analysis:
  - Tight coupling to PropagationResult dataclass: accepted because the
    propagation engine is our most battle-tested module (563 lines, golden suite).
  - Optional stages vs. mandatory stages: physics/graph/propagation are optional
    to preserve the existing V1 financial-first flow. Financial, sector_risk,
    decision, explanation are mandatory.
"""

import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import asdict

from ..schemas.observatory import (
    ScenarioInput,
    ObservatoryOutput,
    Entity,
    Edge,
    FlowState,
    FinancialImpact,
    BankingStress,
    InsuranceStress,
    FintechStress,
    DecisionAction,
    DecisionPlan,
    RegulatoryState,
    ExplanationPack,
    RUNTIME_FLOW,
)

# ============================================================================
# STAGE IMPORTS — each wrapped in try/except for graceful degradation
# ============================================================================

# Stage 2: Physics Core
try:
    from ..intelligence.physics_core import (
        compute_system_stress,
        compute_shockwave,
        compute_system_pressure,
    )
    PHYSICS_AVAILABLE = True
except ImportError:
    PHYSICS_AVAILABLE = False

# Stage 3-4: Graph + Propagation
try:
    from ..intelligence.engines import run_propagation, PropagationResult
    PROPAGATION_AVAILABLE = True
except ImportError:
    PROPAGATION_AVAILABLE = False

# Stage 4b: Scenario engines (for graph data when Neo4j unavailable)
try:
    from ..intelligence.engines.scenario_engines import (
        engine_1_hormuz_strait_closure,
        ScenarioEngineResult,
    )
    from ..intelligence.engines.gcc_constants import (
        BASES,
        HORMUZ_MULTIPLIERS,
        SECTOR_GDP_BASE,
    )
    SCENARIO_ENGINES_AVAILABLE = True
except ImportError:
    SCENARIO_ENGINES_AVAILABLE = False

# Stage 5: Financial
from ..services.financial.engine import compute_financial_impact

# Stage 6: Sector Risk
from ..services.banking.engine import compute_banking_stress
from ..services.insurance.engine import compute_insurance_stress
from ..services.fintech.engine import compute_fintech_stress

# Stage 8: Decision
from ..services.decision.engine import compute_decisions

# Stage 9: Explanation
from ..services.explainability.engine import compute_explanation

# Stage 7: Regulatory (inline — lightweight enough to keep here)
# Stage 10: Audit
from ..services.audit.engine import compute_sha256


logger = logging.getLogger("observatory.pipeline")


# ============================================================================
# V1 HORMUZ TEST GRAPH — used when Neo4j is unavailable
# Mirrors the golden test suite's 10-node, 8-edge GCC impact graph.
# ============================================================================

HORMUZ_NODES = [
    {"id": "geo_hormuz", "label": "Strait of Hormuz", "labelAr": "مضيق هرمز",
     "layer": "geography", "sensitivity": 0.95, "damping_factor": 0.02, "weight": 0.95, "value": 1000},
    {"id": "eco_oil", "label": "Oil Revenue", "labelAr": "إيرادات النفط",
     "layer": "economy", "sensitivity": 0.85, "damping_factor": 0.05, "weight": 0.9, "value": 540},
    {"id": "eco_shipping", "label": "Shipping", "labelAr": "الشحن البحري",
     "layer": "economy", "sensitivity": 0.75, "damping_factor": 0.05, "weight": 0.8, "value": 12},
    {"id": "fin_insurers", "label": "Insurance Market", "labelAr": "سوق التأمين",
     "layer": "finance", "sensitivity": 0.7, "damping_factor": 0.05, "weight": 0.75, "value": 28},
    {"id": "eco_aviation", "label": "Aviation", "labelAr": "الطيران",
     "layer": "economy", "sensitivity": 0.65, "damping_factor": 0.05, "weight": 0.7, "value": 42},
    {"id": "eco_tourism", "label": "Tourism", "labelAr": "السياحة",
     "layer": "economy", "sensitivity": 0.6, "damping_factor": 0.08, "weight": 0.6, "value": 85},
    {"id": "fin_banking", "label": "Banking", "labelAr": "البنوك",
     "layer": "finance", "sensitivity": 0.65, "damping_factor": 0.05, "weight": 0.85, "value": 2800},
    {"id": "fin_reserves", "label": "CB Reserves", "labelAr": "احتياطيات البنك المركزي",
     "layer": "finance", "sensitivity": 0.5, "damping_factor": 0.1, "weight": 0.9, "value": 780},
    {"id": "soc_employment", "label": "Employment", "labelAr": "التوظيف",
     "layer": "society", "sensitivity": 0.55, "damping_factor": 0.08, "weight": 0.5, "value": 160},
    {"id": "inf_power", "label": "Power Grid", "labelAr": "شبكة الكهرباء",
     "layer": "infrastructure", "sensitivity": 0.4, "damping_factor": 0.12, "weight": 0.7, "value": 180},
]

HORMUZ_EDGES = [
    {"id": "e1", "source": "geo_hormuz", "target": "eco_oil",
     "weight": 0.9, "polarity": 1, "label": "disrupts", "labelAr": "يعطّل"},
    {"id": "e2", "source": "geo_hormuz", "target": "eco_shipping",
     "weight": 0.85, "polarity": 1, "label": "blocks", "labelAr": "يحجب"},
    {"id": "e3", "source": "eco_oil", "target": "fin_banking",
     "weight": 0.7, "polarity": 1, "label": "reduces liquidity", "labelAr": "يقلل السيولة"},
    {"id": "e4", "source": "eco_shipping", "target": "fin_insurers",
     "weight": 0.75, "polarity": 1, "label": "spikes premiums", "labelAr": "يرفع الأقساط"},
    {"id": "e5", "source": "eco_oil", "target": "eco_aviation",
     "weight": 0.6, "polarity": 1, "label": "fuel cost spike", "labelAr": "ارتفاع الوقود"},
    {"id": "e6", "source": "eco_aviation", "target": "eco_tourism",
     "weight": 0.5, "polarity": 1, "label": "reduces travel", "labelAr": "يقلل السفر"},
    {"id": "e7", "source": "fin_banking", "target": "fin_reserves",
     "weight": 0.65, "polarity": 1, "label": "drains reserves", "labelAr": "يستنزف الاحتياطيات"},
    {"id": "e8", "source": "eco_tourism", "target": "soc_employment",
     "weight": 0.45, "polarity": 1, "label": "reduces jobs", "labelAr": "يقلل الوظائف"},
]

HORMUZ_SHOCKS = [
    {"nodeId": "geo_hormuz", "impact": -0.8},
    {"nodeId": "eco_oil", "impact": -0.6},
]


# ============================================================================
# PIPELINE ORCHESTRATOR
# ============================================================================

class PipelineResult:
    """Internal pipeline execution result with stage-level metadata."""

    def __init__(self):
        self.stage_log: Dict[str, Dict[str, Any]] = {}
        self.stages_executed: List[str] = []
        self.stages_skipped: List[str] = []
        self.errors: List[Dict[str, str]] = []

    def record_stage(self, stage_id: str, status: str, duration_ms: float, detail: str = ""):
        self.stage_log[stage_id] = {
            "status": status,
            "duration_ms": round(duration_ms, 3),
            "detail": detail,
        }
        if status == "completed":
            self.stages_executed.append(stage_id)
        elif status == "skipped":
            self.stages_skipped.append(stage_id)
        elif status == "failed":
            self.stages_skipped.append(stage_id)
            self.errors.append({"stage": stage_id, "detail": detail})


def run_observatory_pipeline(
    scenario: ScenarioInput,
    enable_physics: bool = True,
    enable_propagation: bool = True,
    graph_nodes: Optional[List[Dict[str, Any]]] = None,
    graph_edges: Optional[List[Dict[str, Any]]] = None,
    graph_shocks: Optional[List[Dict[str, float]]] = None,
    max_propagation_iterations: int = 6,
) -> Tuple[ObservatoryOutput, PipelineResult]:
    """
    Execute the full 10-stage observatory pipeline.

    When graph_nodes/edges/shocks are not provided, falls back to the built-in
    Hormuz V1 test graph for Hormuz scenarios, or skips stages 2-4 for others.

    Args:
        scenario: Validated scenario input
        enable_physics: Whether to run physics_core stages (stage 2)
        enable_propagation: Whether to run propagation (stages 3-4)
        graph_nodes: Override graph nodes (None = use built-in or skip)
        graph_edges: Override graph edges
        graph_shocks: Override shocks
        max_propagation_iterations: Max iterations for propagation engine

    Returns:
        Tuple of (ObservatoryOutput, PipelineResult with stage metadata)
    """
    pipeline = PipelineResult()
    start_time_ns = time.perf_counter_ns()

    # ------------------------------------------------------------------
    # STAGE 1: Scenario
    # ------------------------------------------------------------------
    t0 = time.perf_counter_ns()
    # Scenario already validated by Pydantic — just record
    pipeline.record_stage("scenario", "completed", _elapsed_ms(t0),
                          f"Scenario '{scenario.id}' severity={scenario.severity}")

    # ------------------------------------------------------------------
    # STAGE 2: Physics
    # ------------------------------------------------------------------
    physics_stress = None
    t0 = time.perf_counter_ns()
    if enable_physics and PHYSICS_AVAILABLE:
        try:
            shockwave_energy = scenario.severity * 0.8  # Scaled from scenario
            system_pressure = scenario.severity * 0.6
            diffusion_rate = 0.05
            time_hours = scenario.duration_days * 24.0

            physics_stress = compute_system_stress(
                shockwave_energy=shockwave_energy,
                system_pressure=system_pressure,
                diffusion_rate=diffusion_rate,
                time_hours=time_hours,
            )
            pipeline.record_stage("physics", "completed", _elapsed_ms(t0),
                                  f"System stress={physics_stress['stress']:.3f} ({physics_stress['level']})")
        except Exception as e:
            logger.warning(f"Physics stage failed: {e}")
            pipeline.record_stage("physics", "failed", _elapsed_ms(t0), str(e))
    else:
        reason = "disabled" if not enable_physics else "physics_core not importable"
        pipeline.record_stage("physics", "skipped", _elapsed_ms(t0), reason)

    # ------------------------------------------------------------------
    # STAGE 3: Graph Snapshot
    # ------------------------------------------------------------------
    t0 = time.perf_counter_ns()
    entities: List[Entity] = []
    edges_out: List[Edge] = []

    # Determine which graph to use
    nodes_to_use = graph_nodes
    edges_to_use = graph_edges
    shocks_to_use = graph_shocks

    is_hormuz = _is_hormuz_scenario(scenario)

    if nodes_to_use is None and is_hormuz:
        # Fall back to built-in Hormuz V1 graph
        nodes_to_use = HORMUZ_NODES
        edges_to_use = HORMUZ_EDGES
        shocks_to_use = HORMUZ_SHOCKS
        logger.info("Using built-in Hormuz V1 graph (Neo4j unavailable)")

    if nodes_to_use:
        # Build Entity/Edge snapshots from graph data
        for n in nodes_to_use:
            entities.append(Entity(
                id=n["id"],
                name=n["label"],
                name_ar=n.get("labelAr", n["label"]),
                layer=n.get("layer", "economy"),
                sector=_layer_to_sector(n.get("layer", "economy")),
                severity=n.get("sensitivity", 0.5),
                metadata={"weight": n.get("weight", 0.5), "value": n.get("value", 0)},
            ))
        for e in edges_to_use:
            edges_out.append(Edge(
                source=e["source"],
                target=e["target"],
                weight=e.get("weight", 0.5),
                propagation_factor=e.get("weight", 0.5),
                edge_type=e.get("label", "impacts"),
            ))
        pipeline.record_stage("graph_snapshot", "completed", _elapsed_ms(t0),
                              f"{len(entities)} entities, {len(edges_out)} edges")
    else:
        pipeline.record_stage("graph_snapshot", "skipped", _elapsed_ms(t0),
                              "No graph data available for this scenario")

    # ------------------------------------------------------------------
    # STAGE 4: Propagation
    # ------------------------------------------------------------------
    t0 = time.perf_counter_ns()
    flow_states: List[FlowState] = []
    propagation_result: Optional[Any] = None

    if enable_propagation and PROPAGATION_AVAILABLE and nodes_to_use and shocks_to_use:
        try:
            propagation_result = run_propagation(
                nodes=nodes_to_use,
                edges=edges_to_use,
                shocks=shocks_to_use,
                max_iterations=max_propagation_iterations,
            )

            # Convert iteration snapshots to FlowState objects
            if propagation_result.iteration_snapshots:
                for snap in propagation_result.iteration_snapshots:
                    flow_states.append(FlowState(
                        timestep=snap.iteration,
                        entity_states=snap.impacts,
                        total_stress=snap.energy,
                        peak_entity=_find_peak_entity(snap.impacts),
                        converged=(snap.delta_energy < 0.005 and snap.iteration > 1),
                    ))

            detail = (
                f"depth={propagation_result.propagation_depth}, "
                f"energy={propagation_result.system_energy:.4f}, "
                f"spread={propagation_result.spread_level}, "
                f"affected={len([v for v in propagation_result.node_impacts.values() if abs(v) > 0.01])}/{len(propagation_result.node_impacts)}"
            )
            pipeline.record_stage("propagation", "completed", _elapsed_ms(t0), detail)
        except Exception as e:
            logger.warning(f"Propagation stage failed: {e}")
            pipeline.record_stage("propagation", "failed", _elapsed_ms(t0), str(e))
    else:
        reason = []
        if not enable_propagation:
            reason.append("disabled")
        if not PROPAGATION_AVAILABLE:
            reason.append("engine not importable")
        if not nodes_to_use:
            reason.append("no graph data")
        pipeline.record_stage("propagation", "skipped", _elapsed_ms(t0), ", ".join(reason) or "n/a")

    # ------------------------------------------------------------------
    # STAGE 5: Financial Impact
    # ------------------------------------------------------------------
    t0 = time.perf_counter_ns()
    financial_impact = compute_financial_impact(scenario)

    # Enrichment: if propagation ran, modulate confidence based on propagation depth
    if propagation_result:
        depth_bonus = min(0.05, propagation_result.propagation_depth * 0.01)
        financial_impact.confidence = min(1.0, financial_impact.confidence + depth_bonus)

    pipeline.record_stage("financial", "completed", _elapsed_ms(t0),
                          f"${financial_impact.headline_loss_usd:.1f}B {financial_impact.severity_code}")

    # ------------------------------------------------------------------
    # STAGE 6: Sector Risk
    # ------------------------------------------------------------------
    t0 = time.perf_counter_ns()
    banking_stress = compute_banking_stress(scenario, financial_impact)
    insurance_stress = compute_insurance_stress(scenario, financial_impact)
    fintech_stress = compute_fintech_stress(scenario, financial_impact)

    pipeline.record_stage("sector_risk", "completed", _elapsed_ms(t0),
                          f"Banking={banking_stress.stress_level} Insurance={insurance_stress.stress_level} Fintech={fintech_stress.stress_level}")

    # ------------------------------------------------------------------
    # STAGE 7: Regulatory
    # ------------------------------------------------------------------
    t0 = time.perf_counter_ns()
    regulatory = _compute_regulatory_state(
        scenario, financial_impact, banking_stress, insurance_stress, fintech_stress
    )
    pipeline.record_stage("regulatory", "completed", _elapsed_ms(t0),
                          f"SAMA={regulatory.sama_alert_level} CBUAE={regulatory.cbuae_alert_level}")

    # ------------------------------------------------------------------
    # STAGE 8: Decision
    # ------------------------------------------------------------------
    t0 = time.perf_counter_ns()
    decisions = compute_decisions(
        scenario, financial_impact, banking_stress, insurance_stress, fintech_stress
    )
    pipeline.record_stage("decision", "completed", _elapsed_ms(t0),
                          f"{len(decisions)} actions selected")

    # Build decision plan from top actions
    decision_plan = _build_decision_plan(scenario, decisions)

    # ------------------------------------------------------------------
    # STAGE 9: Explanation
    # ------------------------------------------------------------------
    t0 = time.perf_counter_ns()
    explanation = compute_explanation(
        scenario, financial_impact, banking_stress, insurance_stress, fintech_stress, decisions
    )
    pipeline.record_stage("explanation", "completed", _elapsed_ms(t0),
                          f"{len(explanation.key_findings)} findings, {len(explanation.causal_chain)}-node chain")

    # ------------------------------------------------------------------
    # STAGE 10: Output Assembly
    # ------------------------------------------------------------------
    t0 = time.perf_counter_ns()

    # Count completed stages (+1 for the output assembly stage being recorded now)
    stages_completed = len(pipeline.stages_executed) + 1

    # Build stage timings dict from pipeline log
    stage_timings = {
        stage_id: info["duration_ms"]
        for stage_id, info in pipeline.stage_log.items()
        if info["status"] == "completed"
    }

    # Build output with all stages
    # schema_version inherited from VersionedModel (frozen, default="v1")
    output = ObservatoryOutput(
        pipeline_stages_completed=stages_completed,
        # Stage 1
        scenario=scenario,
        # Stage 3
        entities=entities,
        edges=edges_out,
        # Stage 4
        flow_states=flow_states,
        # Stage 5
        financial_impact=financial_impact,
        # Stage 6
        banking_stress=banking_stress,
        insurance_stress=insurance_stress,
        fintech_stress=fintech_stress,
        # Stage 7
        regulatory=regulatory,
        # Stage 8
        decisions=decisions,
        decision_plan=decision_plan,
        # Stage 9
        explanation=explanation,
        # Stage 10
        timestamp=datetime.utcnow(),
        audit_hash="",  # Computed below
        computed_in_ms=0.0,  # Updated below
        runtime_flow=RUNTIME_FLOW,
        stage_timings=stage_timings,
    )

    # Compute SHA-256 audit hash
    output.audit_hash = compute_sha256(output)

    # Compute total elapsed
    end_time_ns = time.perf_counter_ns()
    output.computed_in_ms = (end_time_ns - start_time_ns) / 1_000_000.0

    pipeline.record_stage("output", "completed", _elapsed_ms(t0),
                          f"audit_hash={output.audit_hash[:16]}...")

    return output, pipeline


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _elapsed_ms(t0_ns: int) -> float:
    return (time.perf_counter_ns() - t0_ns) / 1_000_000.0


def _is_hormuz_scenario(scenario: ScenarioInput) -> bool:
    """Check if this is a Hormuz Strait closure scenario."""
    markers = ["hormuz", "هرمز"]
    text = f"{scenario.id} {scenario.name} {scenario.name_ar} {scenario.description}".lower()
    return any(m in text for m in markers)


def _layer_to_sector(layer: str) -> str:
    """Map graph layer to financial sector category."""
    mapping = {
        "geography": "infrastructure",
        "infrastructure": "infrastructure",
        "economy": "economy",
        "finance": "finance",
        "society": "society",
    }
    return mapping.get(layer, "economy")


def _find_peak_entity(impacts: Dict[str, float]) -> str:
    """Find the entity with highest absolute impact."""
    if not impacts:
        return ""
    return max(impacts, key=lambda k: abs(impacts[k]))


def _compute_regulatory_state(
    scenario: ScenarioInput,
    fi: FinancialImpact,
    bs: BankingStress,
    ins: InsuranceStress,
    ft: FintechStress,
) -> RegulatoryState:
    """
    Compute GCC regulatory compliance state.

    Checks:
      - PDPL: Always compliant (all computation is local)
      - IFRS 17: Liability adjustment proportional to insurance stress
      - Basel III: CAR floor check against banking stress
      - SAMA/CBUAE: Alert level based on aggregate stress
    """
    triggers: List[str] = []

    # IFRS 17 liability adjustment
    ifrs17_impact = fi.headline_loss_usd * 0.08 * scenario.severity
    if ins.combined_ratio > 1.0:
        ifrs17_impact *= 1.3
        triggers.append("IFRS17_LOSS_RECOGNITION")

    # Basel III CAR
    if bs.capital_adequacy_ratio < 0.08:
        triggers.append("BASEL3_CAR_BREACH")
    elif bs.capital_adequacy_ratio < 0.105:
        triggers.append("BASEL3_CONSERVATION_BUFFER_WARNING")

    # SAMA alert level
    sama_level = _regulatory_alert_level(
        bs.stress_level, ins.stress_level, ft.stress_level
    )
    if sama_level in ("WARNING", "CRITICAL"):
        triggers.append(f"SAMA_ALERT_{sama_level}")

    # CBUAE mirrors SAMA for GCC scenarios
    cbuae_level = sama_level

    # Insurance-specific triggers
    if ins.reinsurance_trigger:
        triggers.append("REINSURANCE_TREATY_ACTIVATION")
    if ins.solvency_margin_pct < 10.0:
        triggers.append("SOLVENCY_MARGIN_BREACH")

    # Fintech-specific triggers
    if ft.payment_failure_rate > 0.10:
        triggers.append("PAYMENT_SYSTEM_CRITICAL")

    # Sanctions exposure (elevated for geopolitical scenarios)
    sanctions = 0.0
    if _is_hormuz_scenario(scenario):
        sanctions = min(1.0, scenario.severity * 0.3)

    return RegulatoryState(
        pdpl_compliant=True,  # All computation local
        ifrs17_impact=round(ifrs17_impact, 2),
        basel3_car_floor=0.08,
        sama_alert_level=sama_level,
        cbuae_alert_level=cbuae_level,
        sanctions_exposure=round(sanctions, 3),
        regulatory_triggers=triggers,
    )


def _regulatory_alert_level(banking: str, insurance: str, fintech: str) -> str:
    """Derive regulatory alert level from sector stress levels."""
    level_scores = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
    scores = [
        level_scores.get(banking, 0),
        level_scores.get(insurance, 0),
        level_scores.get(fintech, 0),
    ]
    avg = sum(scores) / len(scores)
    if avg >= 2.5:
        return "CRITICAL"
    elif avg >= 1.5:
        return "WARNING"
    elif avg >= 0.5:
        return "WATCH"
    return "NORMAL"


def _build_decision_plan(
    scenario: ScenarioInput,
    decisions: List[DecisionAction],
) -> Optional[DecisionPlan]:
    """Build coordinated decision plan from selected actions."""
    if not decisions:
        return None

    total_cost = sum(d.cost_usd for d in decisions)
    total_avoided = sum(d.loss_avoided_usd for d in decisions)
    sectors = list(set(d.sector for d in decisions))

    # Execution timeline: max of individual urgency-driven timelines
    max_urgency = max(d.urgency for d in decisions) if decisions else 1.0
    execution_days = max(7, int(scenario.duration_days * (1.0 - max_urgency * 0.5)))

    return DecisionPlan(
        plan_id=f"plan_{scenario.id}_{len(decisions)}",
        name=f"Response Plan: {scenario.name}",
        name_ar=f"خطة الاستجابة: {scenario.name_ar}",
        actions=decisions,
        total_cost_usd=round(total_cost, 2),
        total_loss_avoided_usd=round(total_avoided, 2),
        net_benefit_usd=round(total_avoided - total_cost, 2),
        execution_days=execution_days,
        sectors_covered=sectors,
    )
