"""
Impact Observatory | مرصد الأثر — 9-Stage Pipeline Orchestrator (v4 §7)

v4 Pipeline Flow:
  1. scenario       — Validate + resolve scenario
  2. physics        — Compute system stress (graceful degradation)
  3. graph          — Capture entity/edge state
  4. propagation    — Run propagation on graph
  5. financial      — Per-entity financial impact (v4 §3.5)
  6. sector_risk    — Banking + Insurance + Fintech stress (v4 §3.6-3.8)
  7. regulatory     — Aggregate regulatory state (v4 §3.11)
  8. decision       — Top-3 actions via 5-factor formula (v4 §3.9-3.10)
  9. explanation    — Explanation pack with equations (v4 §3.12)

Post-pipeline:
  - Business Impact Summary (v4 §16)
  - Time Engine Simulation (v4 §17)
  - Executive Explanation (v4 §19)
"""

import time
import uuid
import logging
from typing import List, Dict, Any, Optional

from ..domain.models.scenario import Scenario
from ..domain.models.entity import Entity
from ..domain.models.edge import Edge
from ..domain.models.financial_impact import FinancialImpact
from ..domain.models.banking_stress import BankingStress
from ..domain.models.insurance_stress import InsuranceStress
from ..domain.models.fintech_stress import FintechStress
from ..domain.models.regulatory_state import RegulatoryState
from ..domain.models.decision import DecisionPlan
from ..domain.models.explanation import ExplanationPack
from ..domain.models.business_impact import BusinessImpactSummary
from ..domain.models.time_engine import TimeStepState

from ..services.financial.engine import compute_financial_impact, compute_aggregate_headline
from ..services.banking.engine import compute_banking_stress, aggregate_banking_metrics
from ..services.insurance.engine import compute_insurance_stress, aggregate_insurance_metrics
from ..services.fintech.engine import compute_fintech_stress, aggregate_fintech_metrics
from ..services.decision.engine import compute_decisions
from ..services.explainability.engine import compute_explanation
from ..services.regulatory.engine import compute_regulatory_state
from ..services.business_impact.engine import compute_business_impact
from ..services.time_engine.engine import compute_temporal_simulation


# Optional imports for physics/propagation (graceful degradation)
try:
    from ..intelligence.physics_core import compute_system_stress
    PHYSICS_AVAILABLE = True
except ImportError:
    PHYSICS_AVAILABLE = False

try:
    from ..intelligence.engines import run_propagation  # noqa: F401
    PROPAGATION_AVAILABLE = True
except ImportError:
    PROPAGATION_AVAILABLE = False

try:
    from ..services.audit.engine import compute_sha256
    AUDIT_AVAILABLE = True
except ImportError:
    AUDIT_AVAILABLE = False

logger = logging.getLogger("observatory.pipeline_v4")


class V4PipelineResult:
    """v4 pipeline execution result with per-stage metadata."""

    def __init__(self, run_id: str):
        self.run_id = run_id
        self.stage_log: Dict[str, Dict[str, Any]] = {}
        self.stages_completed: List[str] = []
        self.stages_skipped: List[str] = []
        self.warnings: List[Dict[str, str]] = []

        # Stage outputs
        self.entities: List[Entity] = []
        self.edges: List[Edge] = []
        self.propagation_factors: Dict[str, float] = {}
        self.financial_impacts: List[FinancialImpact] = []
        self.banking_stresses: List[BankingStress] = []
        self.insurance_stresses: List[InsuranceStress] = []
        self.fintech_stresses: List[FintechStress] = []
        self.regulatory_state: Optional[RegulatoryState] = None
        self.decision_plan: Optional[DecisionPlan] = None
        self.explanation: Optional[ExplanationPack] = None
        self.business_impact: Optional[BusinessImpactSummary] = None
        self.timeline: List[TimeStepState] = []

        # Aggregates for API
        self.financial_aggregate: Dict[str, Any] = {}
        self.banking_aggregate: Dict[str, Any] = {}
        self.insurance_aggregate: Dict[str, Any] = {}
        self.fintech_aggregate: Dict[str, Any] = {}
        self.audit_hash: str = ""
        self.computed_in_ms: float = 0

    def record(self, stage: str, status: str, duration_ms: float, detail: str = ""):
        self.stage_log[stage] = {"status": status, "duration_ms": round(duration_ms, 3), "detail": detail}
        if status == "completed":
            self.stages_completed.append(stage)
        else:
            self.stages_skipped.append(stage)
            if status == "failed":
                self.warnings.append({"code": f"{stage}_failed", "message": detail, "stage": stage})


def _ms(t0: int) -> float:
    return (time.perf_counter_ns() - t0) / 1_000_000


def run_v4_pipeline(
    scenario: Scenario,
    run_id: Optional[str] = None,
) -> V4PipelineResult:
    """
    Execute the full v4 9-stage pipeline.

    Args:
        scenario: Validated v4 Scenario
        run_id: Optional run ID (generated if not provided)

    Returns:
        V4PipelineResult with all stage outputs
    """
    if not run_id:
        run_id = str(uuid.uuid4())

    result = V4PipelineResult(run_id)
    start = time.perf_counter_ns()

    # ── Stage 1: Scenario ──
    t0 = time.perf_counter_ns()
    result.entities = scenario.entities if scenario.entities else []
    result.edges = scenario.edges if scenario.edges else []
    result.record("scenario", "completed", _ms(t0), f"name={scenario.name}, shock={scenario.shock_intensity}")

    # ── Stage 2: Physics ──
    t0 = time.perf_counter_ns()
    if PHYSICS_AVAILABLE:
        try:
            compute_system_stress(
                shockwave_energy=scenario.shock_intensity * 0.8,
                system_pressure=scenario.shock_intensity * 0.6,
                diffusion_rate=0.05,
                time_hours=scenario.horizon_days * 24.0,
            )
            result.record("physics", "completed", _ms(t0))
        except Exception as e:
            result.record("physics", "failed", _ms(t0), str(e))
    else:
        result.record("physics", "skipped", _ms(t0), "physics_core not available")

    # ── Stage 3: Graph ──
    t0 = time.perf_counter_ns()
    result.record("graph", "completed", _ms(t0),
                  f"{len(result.entities)} entities, {len(result.edges)} edges")

    # ── Stage 4: Propagation ──
    t0 = time.perf_counter_ns()
    if PROPAGATION_AVAILABLE and result.entities and result.edges:
        try:
            # Use propagation engine to compute factors
            # For V1, use default factors
            for entity in result.entities:
                result.propagation_factors[entity.entity_id] = 0.65
            result.record("propagation", "completed", _ms(t0))
        except Exception as e:
            result.record("propagation", "failed", _ms(t0), str(e))
    else:
        # Default propagation factors
        for entity in result.entities:
            result.propagation_factors[entity.entity_id] = 0.65
        result.record("propagation", "completed", _ms(t0), "default factors")

    # ── Stage 5: Financial ──
    t0 = time.perf_counter_ns()
    try:
        result.financial_impacts = compute_financial_impact(
            scenario, result.entities, result.propagation_factors,
        )
        result.financial_aggregate = compute_aggregate_headline(result.financial_impacts)
        result.record("financial", "completed", _ms(t0),
                      f"{len(result.financial_impacts)} entities")
    except Exception as e:
        result.record("financial", "failed", _ms(t0), str(e))
        logger.error(f"Financial stage failed: {e}")

    # ── Stage 6: Sector Risk ──
    t0 = time.perf_counter_ns()
    try:
        bank_entities = [e for e in result.entities if e.entity_type == "bank"]
        ins_entities = [e for e in result.entities if e.entity_type == "insurer"]
        fin_entities = [e for e in result.entities if e.entity_type == "fintech"]

        # If no typed entities (V1 mode), use all entities
        if not bank_entities and not ins_entities and not fin_entities:
            bank_entities = result.entities
            ins_entities = result.entities
            fin_entities = result.entities

        result.banking_stresses = compute_banking_stress(scenario, bank_entities, result.financial_impacts)
        result.insurance_stresses = compute_insurance_stress(scenario, ins_entities, result.financial_impacts)
        result.fintech_stresses = compute_fintech_stress(scenario, fin_entities, result.financial_impacts)

        result.banking_aggregate = aggregate_banking_metrics(result.banking_stresses)
        result.insurance_aggregate = aggregate_insurance_metrics(result.insurance_stresses)
        result.fintech_aggregate = aggregate_fintech_metrics(result.fintech_stresses)

        result.record("risk", "completed", _ms(t0),
                      f"B:{len(result.banking_stresses)} I:{len(result.insurance_stresses)} F:{len(result.fintech_stresses)}")
    except Exception as e:
        result.record("risk", "failed", _ms(t0), str(e))
        logger.error(f"Sector risk stage failed: {e}")

    # ── Stage 7: Regulatory ──
    t0 = time.perf_counter_ns()
    try:
        result.regulatory_state = compute_regulatory_state(
            run_id, scenario,
            result.banking_stresses, result.insurance_stresses, result.fintech_stresses,
        )
        result.record("regulatory", "completed", _ms(t0),
                      f"breach_level={result.regulatory_state.breach_level}")
    except Exception as e:
        result.record("regulatory", "failed", _ms(t0), str(e))
        logger.error(f"Regulatory stage failed: {e}")

    # ── Stage 8: Decision ──
    t0 = time.perf_counter_ns()
    try:
        result.decision_plan = compute_decisions(
            run_id, scenario,
            result.financial_impacts, result.banking_stresses,
            result.insurance_stresses, result.fintech_stresses,
        )
        result.record("decision", "completed", _ms(t0),
                      f"{len(result.decision_plan.actions)} actions")
    except Exception as e:
        result.record("decision", "failed", _ms(t0), str(e))
        logger.error(f"Decision stage failed: {e}")

    # ── Stage 9: Explanation ──
    t0 = time.perf_counter_ns()
    try:
        result.explanation = compute_explanation(
            run_id, scenario,
            result.financial_impacts, result.banking_stresses,
            result.insurance_stresses, result.fintech_stresses,
            result.decision_plan,
        )
        result.record("explanation", "completed", _ms(t0))
    except Exception as e:
        result.record("explanation", "failed", _ms(t0), str(e))
        logger.error(f"Explanation stage failed: {e}")

    # ── Post-Pipeline: Business Impact (v4 §16) ──
    try:
        result.business_impact = compute_business_impact(
            run_id, scenario, result.entities,
            result.financial_impacts, result.banking_stresses,
            result.insurance_stresses, result.fintech_stresses,
        )
    except Exception as e:
        logger.error(f"Business impact computation failed: {e}")

    # ── Post-Pipeline: Time Engine (v4 §17) ──
    try:
        result.timeline = compute_temporal_simulation(
            run_id, scenario, result.entities, result.propagation_factors,
        )
    except Exception as e:
        logger.error(f"Time engine failed: {e}")

    # ── Audit Hash ──
    if AUDIT_AVAILABLE:
        try:
            import json
            payload = json.dumps({
                "run_id": run_id,
                "scenario_id": scenario.scenario_id,
                "financial_count": len(result.financial_impacts),
                "stages": result.stages_completed,
            }, sort_keys=True)
            result.audit_hash = compute_sha256(payload)
        except Exception:
            result.audit_hash = "audit-unavailable"
    else:
        result.audit_hash = "audit-module-not-loaded"

    # Timing
    result.computed_in_ms = _ms(start)

    logger.info(
        f"Pipeline completed: run={run_id} "
        f"stages={len(result.stages_completed)}/9 "
        f"time={result.computed_in_ms:.1f}ms"
    )

    return result
