"""
Impact Observatory | مرصد الأثر — Explainability Engine (v4 §3.12)
Generates ExplanationPack with equations, drivers, stage traces, and action explanations.
"""

from datetime import datetime, timezone
from typing import List, Optional

from ...domain.models.scenario import Scenario
from ...domain.models.financial_impact import FinancialImpact
from ...domain.models.banking_stress import BankingStress
from ...domain.models.insurance_stress import InsuranceStress
from ...domain.models.fintech_stress import FintechStress
from ...domain.models.decision import DecisionPlan
from ...domain.models.explanation import (
    ExplanationPack, Equations, ExplanationDriver,
    StageTrace, ActionExplanation,
)
from ...core.constants import PIPELINE_STAGES


def compute_explanation(
    run_id: str,
    scenario: Scenario,
    financial_impacts: List[FinancialImpact],
    banking_stresses: List[BankingStress],
    insurance_stresses: List[InsuranceStress],
    fintech_stresses: List[FintechStress],
    decision_plan: Optional[DecisionPlan] = None,
    stage_timings: dict[str, tuple[str, str, int]] | None = None,
) -> ExplanationPack:
    """
    v4 §3.12 — Generate explanation pack.

    ExplanationDriver fields: driver (str), magnitude (float), unit (str), affected_entities (list)
    StageTrace fields: stage (Literal), status (Literal), input_ref (str), output_ref (str), notes (str)
    ActionExplanation fields: rank (int), action_id (str), why_selected (str), supporting_metrics (dict)
    """
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    total_loss = sum(fi.loss for fi in financial_impacts)
    banking_breach_count = sum(1 for s in banking_stresses if s.breach_flags.lcr_breach or s.breach_flags.car_breach)
    insurance_breach_count = sum(1 for s in insurance_stresses if s.breach_flags.solvency_breach)
    fintech_breach_count = sum(1 for s in fintech_stresses if s.breach_flags.availability_breach)

    # Summary
    actions_count = len(decision_plan.actions) if decision_plan else 0
    summary = (
        f"{scenario.name} scenario (shock={scenario.shock_intensity}, horizon={scenario.horizon_days}d) "
        f"produces aggregate loss of ${total_loss:.1f}B across {len(financial_impacts)} entities. "
        f"Banking: {banking_breach_count} breaches. Insurance: {insurance_breach_count} breaches. "
        f"Fintech: {fintech_breach_count} breaches. "
        f"{actions_count} actions recommended."
    )

    # Equations (v4 frozen constants)
    equations = Equations()

    # Drivers — model: driver (str), magnitude (float), unit (str), affected_entities (list)
    drivers: List[ExplanationDriver] = []
    if banking_breach_count > 0:
        banking_loss = sum(fi.loss for fi in financial_impacts if fi.entity_id.startswith("bank"))
        drivers.append(ExplanationDriver(
            driver="Banking sector liquidity and capital breach under shock stress",
            magnitude=round(banking_loss, 2),
            unit="USD_B",
            affected_entities=[s.entity_id for s in banking_stresses if s.breach_flags.lcr_breach],
        ))
    if insurance_breach_count > 0:
        ins_loss = sum(fi.loss for fi in financial_impacts if fi.entity_id.startswith("ins"))
        drivers.append(ExplanationDriver(
            driver="Insurance solvency deterioration from claims spike",
            magnitude=round(ins_loss, 2),
            unit="USD_B",
            affected_entities=[s.entity_id for s in insurance_stresses if s.breach_flags.solvency_breach],
        ))
    if fintech_breach_count > 0:
        fin_loss = sum(fi.loss for fi in financial_impacts if fi.entity_id.startswith("fin"))
        drivers.append(ExplanationDriver(
            driver="Fintech service availability degradation and settlement delay",
            magnitude=round(fin_loss, 2),
            unit="USD_B",
            affected_entities=[s.entity_id for s in fintech_stresses if s.breach_flags.availability_breach],
        ))
    # Ensure at least one driver
    if not drivers:
        drivers.append(ExplanationDriver(
            driver="Aggregate shock propagation across financial system",
            magnitude=round(total_loss, 2),
            unit="USD_B",
            affected_entities=[fi.entity_id for fi in financial_impacts[:5]],
        ))

    # Stage traces — model: stage (Literal), status (Literal), input_ref (str), output_ref (str), notes (str)
    # 8 stages: physics, graph, propagation, financial, risk, regulatory, decision, explanation
    traced_stages = PIPELINE_STAGES[1:]  # physics through explanation
    stage_traces: List[StageTrace] = []
    for stage in traced_stages[:8]:
        timing = (stage_timings or {}).get(stage)
        if timing:
            st = "completed"
            notes = f"records={timing[2]}"
        else:
            st = "completed"
            notes = "timing not captured"

        stage_traces.append(StageTrace(
            stage=stage,
            status=st,
            input_ref=f"run:{run_id}/stage:{stage}/input",
            output_ref=f"run:{run_id}/stage:{stage}/output",
            notes=notes,
        ))

    # Action explanations — model: rank (int), action_id (str), why_selected (str), supporting_metrics (dict)
    action_explanations: List[ActionExplanation] = []
    if decision_plan:
        for action in decision_plan.actions:
            action_explanations.append(ActionExplanation(
                rank=action.rank,
                action_id=action.action_id,
                why_selected=(
                    f"Priority {action.priority_score:.2f}: urgency={action.urgency:.2f}, "
                    f"value={action.value:.2f}, feasibility={action.feasibility:.2f}. "
                    f"Expected loss reduction ${action.expected_loss_reduction:.1f}B "
                    f"within {action.execution_window_hours}h window. "
                    f"Override required: {action.requires_override}."
                ),
                supporting_metrics={
                    "urgency": action.urgency,
                    "value": action.value,
                    "reg_risk": action.reg_risk,
                    "feasibility": action.feasibility,
                    "time_effect": action.time_effect,
                    "priority_score": action.priority_score,
                },
            ))

    return ExplanationPack(
        run_id=run_id,
        generated_at=now,
        summary=summary,
        equations=equations,
        drivers=drivers,
        stage_traces=stage_traces,
        action_explanations=action_explanations,
        assumptions=[
            "Deterministic model with fixed GCC macro parameters",
            "Single shock event with exponential decay",
            "Homogeneous entity behavior within sector",
            "No inter-temporal feedback loops in V1",
        ],
        limitations=[
            "V1 uses aggregate sector-level entities, not individual institutions",
            "Monte Carlo uncertainty bands not computed in deterministic mode",
            "Cross-border contagion limited to GCC member states",
        ],
    )
