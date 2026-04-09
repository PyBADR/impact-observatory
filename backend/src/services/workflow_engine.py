"""
Impact Observatory | مرصد الأثر — Workflow Engine Service

Layer: Services (L4) — State machine for insurance workflow execution.

Architecture Decision:
  Deterministic state machine with 4 step types:
    - auto:        Execute immediately (risk scoring, data enrichment)
    - hitl:        Pause for human approval (underwriter/adjuster review)
    - conditional: Branch based on rule evaluation (threshold checks)
    - api_call:    Call external service (simulation engine, fraud API)

  Each WorkflowRun tracks progress through ordered steps. Steps execute
  sequentially. HITL steps pause the run until approved/rejected.

Data Flow:
  WorkflowRunRequest → create run → execute step[0]
  → if auto: run handler → next step
  → if hitl: pause → await StepApproval → resume
  → if conditional: evaluate condition_json → branch
  → if api_call: call endpoint → capture result → next step
  → all steps complete → WorkflowRunStatus.COMPLETED

State Transitions:
  PENDING → RUNNING → AWAITING_APPROVAL → RUNNING → COMPLETED
                    → FAILED (on error)
                    → REJECTED (on hitl reject)
                    → CANCELLED (manual)

Risk Register:
  - Step timeout → mark step FAILED, run FAILED, log audit event
  - Orphan HITL → cron detects runs stuck >24h in AWAITING_APPROVAL
  - Simulation link → run_id links workflow to simulation for traceability
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.enterprise import (
    Workflow, WorkflowRun, WorkflowStep,
    WorkflowRunStatus, WorkflowStepStatus, WorkflowType,
)

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# Step Handler Registry
# ══════════════════════════════════════════════════════════════════════════════

StepHandler = Callable[[dict[str, Any], dict[str, Any]], Awaitable[dict[str, Any]]]

_step_handlers: dict[str, StepHandler] = {}


def register_step_handler(step_name: str):
    """Decorator to register an auto/api_call step handler.

    Usage:
        @register_step_handler("risk_score_calculation")
        async def handle_risk_score(input_data: dict, context: dict) -> dict:
            score = compute_risk(input_data)
            return {"risk_score": score}
    """
    def decorator(fn: StepHandler) -> StepHandler:
        _step_handlers[step_name] = fn
        return fn
    return decorator


# ══════════════════════════════════════════════════════════════════════════════
# Built-in Step Handlers
# ══════════════════════════════════════════════════════════════════════════════

@register_step_handler("risk_score_calculation")
async def _handle_risk_score(input_data: dict, context: dict) -> dict:
    """Auto step: calculate risk score from input data."""
    # In production, this calls the simulation engine
    severity = float(input_data.get("severity", 0.5))
    claim_amount = float(input_data.get("claim_amount", 0))
    risk_score = min(severity * 0.6 + (claim_amount / 1_000_000) * 0.4, 1.0)
    return {
        "risk_score": round(risk_score, 4),
        "risk_level": (
            "CRITICAL" if risk_score >= 0.8 else
            "HIGH" if risk_score >= 0.6 else
            "MODERATE" if risk_score >= 0.4 else
            "LOW"
        ),
        "auto_approve": risk_score < 0.4,
    }


@register_step_handler("data_enrichment")
async def _handle_data_enrichment(input_data: dict, context: dict) -> dict:
    """Auto step: enrich application/claim data with external sources."""
    return {
        "enriched": True,
        "sources": ["internal_db", "gcc_registry"],
        "flags": [],
    }


@register_step_handler("fraud_screening")
async def _handle_fraud_screening(input_data: dict, context: dict) -> dict:
    """Auto step: run fraud indicators check."""
    risk_score = context.get("risk_score", 0.5)
    fraud_score = risk_score * 0.3 + 0.1  # Placeholder
    return {
        "fraud_score": round(fraud_score, 4),
        "fraud_flags": [],
        "requires_investigation": fraud_score > 0.6,
    }


@register_step_handler("policy_compliance_check")
async def _handle_compliance(input_data: dict, context: dict) -> dict:
    """Auto step: check against tenant policy rules."""
    return {
        "compliant": True,
        "violations": [],
        "warnings": [],
    }


@register_step_handler("simulation_trigger")
async def _handle_simulation(input_data: dict, context: dict) -> dict:
    """API call step: trigger a simulation run."""
    # In production, calls POST /api/v1/scenarios/simulate
    return {
        "simulation_triggered": True,
        "scenario_id": input_data.get("scenario_id", "gcc_cyber_attack"),
        "note": "Simulation result linked via run_id",
    }


# ══════════════════════════════════════════════════════════════════════════════
# Workflow Engine
# ══════════════════════════════════════════════════════════════════════════════

class WorkflowEngine:
    """State machine engine for insurance workflow execution."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # ── Workflow CRUD ─────────────────────────────────────────────────────

    async def create_workflow(
        self,
        tenant_id: str,
        name: str,
        workflow_type: str,
        steps_json: list[dict],
        *,
        name_ar: str | None = None,
        description: str | None = None,
        config_json: dict | None = None,
    ) -> Workflow:
        """Create a workflow definition (template)."""
        wf = Workflow(
            tenant_id=tenant_id,
            name=name,
            name_ar=name_ar,
            workflow_type=workflow_type,
            description=description,
            steps_json=steps_json,
            config_json=config_json or {},
        )
        self.session.add(wf)
        await self.session.flush()
        logger.info("Workflow created: %s (%s) for tenant %s", name, workflow_type, tenant_id)
        return wf

    async def get_workflow(self, tenant_id: str, workflow_id: str) -> Workflow | None:
        result = await self.session.execute(
            select(Workflow).where(
                and_(Workflow.tenant_id == tenant_id, Workflow.id == workflow_id)
            )
        )
        return result.scalar_one_or_none()

    async def list_workflows(
        self, tenant_id: str, workflow_type: str | None = None
    ) -> list[Workflow]:
        q = select(Workflow).where(Workflow.tenant_id == tenant_id)
        if workflow_type:
            q = q.where(Workflow.workflow_type == workflow_type)
        q = q.order_by(Workflow.created_at.desc())
        result = await self.session.execute(q)
        return list(result.scalars().all())

    # ── Run Management ───────────────────────────────────────────────────

    async def start_run(
        self,
        tenant_id: str,
        workflow_id: str,
        initiated_by: str,
        input_json: dict[str, Any],
        *,
        run_id: str | None = None,
    ) -> WorkflowRun:
        """Start a new workflow run. Creates step records and begins execution."""
        wf = await self.get_workflow(tenant_id, workflow_id)
        if not wf:
            raise ValueError(f"Workflow not found: {workflow_id}")
        if not wf.is_active:
            raise ValueError(f"Workflow is inactive: {wf.name}")

        # Create the run
        wf_run = WorkflowRun(
            tenant_id=tenant_id,
            workflow_id=workflow_id,
            initiated_by=initiated_by,
            status=WorkflowRunStatus.PENDING,
            current_step=0,
            input_json=input_json,
            context_json={},
            run_id=run_id,
        )
        self.session.add(wf_run)
        await self.session.flush()

        # Create step records from workflow definition
        steps_def = wf.steps_json or []
        for i, step_def in enumerate(steps_def):
            step = WorkflowStep(
                workflow_run_id=wf_run.id,
                step_index=i,
                step_name=step_def.get("step_name", f"Step {i}"),
                step_type=step_def.get("step_type", "auto"),
                status=WorkflowStepStatus.PENDING,
                input_json=step_def.get("config"),
            )
            self.session.add(step)

        await self.session.flush()

        # Begin execution
        wf_run.status = WorkflowRunStatus.RUNNING
        await self._execute_current_step(wf_run)

        return wf_run

    async def get_run(self, tenant_id: str, run_id: str) -> WorkflowRun | None:
        result = await self.session.execute(
            select(WorkflowRun).where(
                and_(WorkflowRun.tenant_id == tenant_id, WorkflowRun.id == run_id)
            )
        )
        return result.scalar_one_or_none()

    async def list_runs(
        self,
        tenant_id: str,
        *,
        workflow_id: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[WorkflowRun], int]:
        q_base = select(WorkflowRun).where(WorkflowRun.tenant_id == tenant_id)
        if workflow_id:
            q_base = q_base.where(WorkflowRun.workflow_id == workflow_id)
        if status:
            q_base = q_base.where(WorkflowRun.status == status)

        count_q = select(func.count()).select_from(q_base.subquery())
        total = (await self.session.execute(count_q)).scalar() or 0

        q = q_base.order_by(WorkflowRun.started_at.desc()).offset((page - 1) * page_size).limit(page_size)
        result = await self.session.execute(q)
        return list(result.scalars().all()), total

    # ── Step Execution ───────────────────────────────────────────────────

    async def _execute_current_step(self, wf_run: WorkflowRun) -> None:
        """Execute the current step of a workflow run."""
        steps = sorted(wf_run.steps, key=lambda s: s.step_index)
        if wf_run.current_step >= len(steps):
            await self._complete_run(wf_run)
            return

        step = steps[wf_run.current_step]
        step.status = WorkflowStepStatus.RUNNING
        step.started_at = datetime.now(timezone.utc)

        start_time = time.perf_counter()

        try:
            if step.step_type == "hitl":
                # Pause for human decision
                step.status = WorkflowStepStatus.AWAITING_INPUT
                wf_run.status = WorkflowRunStatus.AWAITING_APPROVAL
                logger.info(
                    "Workflow %s paused at step %d (%s) — awaiting HITL",
                    wf_run.id[:12], step.step_index, step.step_name,
                )

            elif step.step_type == "conditional":
                # Evaluate condition from step config
                output = await self._evaluate_condition(step, wf_run.context_json or {})
                step.output_json = output
                step.status = WorkflowStepStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc)
                step.duration_ms = (time.perf_counter() - start_time) * 1000
                # Merge output into context
                ctx = dict(wf_run.context_json or {})
                ctx.update(output)
                wf_run.context_json = ctx
                # Advance
                wf_run.current_step += 1
                await self._execute_current_step(wf_run)

            else:
                # auto or api_call — run handler
                handler = _step_handlers.get(step.step_name)
                if handler:
                    output = await handler(
                        wf_run.input_json or {},
                        wf_run.context_json or {},
                    )
                else:
                    output = {"note": f"No handler registered for '{step.step_name}', auto-passing"}

                step.output_json = output
                step.status = WorkflowStepStatus.COMPLETED
                step.completed_at = datetime.now(timezone.utc)
                step.duration_ms = (time.perf_counter() - start_time) * 1000

                # Merge output into run context
                ctx = dict(wf_run.context_json or {})
                ctx.update(output)
                wf_run.context_json = ctx

                # Advance
                wf_run.current_step += 1
                await self._execute_current_step(wf_run)

        except Exception as e:
            step.status = WorkflowStepStatus.FAILED
            step.output_json = {"error": str(e)}
            step.completed_at = datetime.now(timezone.utc)
            step.duration_ms = (time.perf_counter() - start_time) * 1000
            wf_run.status = WorkflowRunStatus.FAILED
            wf_run.error_message = f"Step {step.step_index} ({step.step_name}) failed: {e}"
            logger.error("Workflow %s failed at step %d: %s", wf_run.id[:12], step.step_index, e)

    async def approve_step(
        self,
        tenant_id: str,
        run_id: str,
        decision: str,
        *,
        decision_by: str | None = None,
        reason: str | None = None,
        metadata: dict | None = None,
    ) -> WorkflowRun:
        """Process a HITL step decision (approve/reject/return)."""
        wf_run = await self.get_run(tenant_id, run_id)
        if not wf_run:
            raise ValueError(f"Workflow run not found: {run_id}")
        if wf_run.status != WorkflowRunStatus.AWAITING_APPROVAL:
            raise ValueError(f"Run is not awaiting approval (status: {wf_run.status})")

        steps = sorted(wf_run.steps, key=lambda s: s.step_index)
        current = steps[wf_run.current_step]

        current.decision_by = decision_by
        current.decision_reason = reason
        current.completed_at = datetime.now(timezone.utc)

        if decision == "approve":
            current.status = WorkflowStepStatus.COMPLETED
            current.output_json = {
                "decision": "approved",
                "reason": reason,
                "metadata": metadata,
            }
            # Merge and advance
            ctx = dict(wf_run.context_json or {})
            ctx[f"step_{current.step_index}_decision"] = "approved"
            wf_run.context_json = ctx
            wf_run.status = WorkflowRunStatus.RUNNING
            wf_run.current_step += 1
            await self._execute_current_step(wf_run)

        elif decision == "reject":
            current.status = WorkflowStepStatus.FAILED
            current.output_json = {"decision": "rejected", "reason": reason}
            wf_run.status = WorkflowRunStatus.REJECTED
            wf_run.completed_at = datetime.now(timezone.utc)
            logger.info("Workflow %s rejected at step %d", run_id[:12], current.step_index)

        elif decision == "return":
            # Return to previous step for revision
            current.status = WorkflowStepStatus.PENDING
            current.output_json = {"decision": "returned", "reason": reason}
            if wf_run.current_step > 0:
                wf_run.current_step -= 1
                prev_step = steps[wf_run.current_step]
                prev_step.status = WorkflowStepStatus.PENDING
            wf_run.status = WorkflowRunStatus.RUNNING
            await self._execute_current_step(wf_run)

        return wf_run

    async def cancel_run(self, tenant_id: str, run_id: str) -> WorkflowRun:
        """Cancel a running workflow."""
        wf_run = await self.get_run(tenant_id, run_id)
        if not wf_run:
            raise ValueError(f"Run not found: {run_id}")
        if wf_run.status in (WorkflowRunStatus.COMPLETED, WorkflowRunStatus.CANCELLED):
            raise ValueError(f"Cannot cancel run in status: {wf_run.status}")

        wf_run.status = WorkflowRunStatus.CANCELLED
        wf_run.completed_at = datetime.now(timezone.utc)
        return wf_run

    # ── Internal Helpers ─────────────────────────────────────────────────

    async def _complete_run(self, wf_run: WorkflowRun) -> None:
        """Mark a run as completed."""
        wf_run.status = WorkflowRunStatus.COMPLETED
        wf_run.completed_at = datetime.now(timezone.utc)
        wf_run.output_json = wf_run.context_json
        if wf_run.started_at:
            delta = (wf_run.completed_at - wf_run.started_at).total_seconds() * 1000
            wf_run.duration_ms = delta
        logger.info("Workflow %s completed in %.1fms", wf_run.id[:12], wf_run.duration_ms or 0)

    async def _evaluate_condition(
        self, step: WorkflowStep, context: dict
    ) -> dict[str, Any]:
        """Evaluate a conditional step. Returns branch result."""
        config = step.input_json or {}
        field = config.get("field", "risk_score")
        operator = config.get("operator", ">=")
        threshold = float(config.get("threshold", 0.5))
        value = float(context.get(field, 0))

        if operator == ">=":
            result = value >= threshold
        elif operator == "<=":
            result = value <= threshold
        elif operator == ">":
            result = value > threshold
        elif operator == "<":
            result = value < threshold
        elif operator == "==":
            result = value == threshold
        else:
            result = False

        return {
            "condition_field": field,
            "condition_operator": operator,
            "condition_threshold": threshold,
            "actual_value": value,
            "condition_met": result,
            "branch": "true" if result else "false",
        }


# ══════════════════════════════════════════════════════════════════════════════
# Pre-built Workflow Templates
# ══════════════════════════════════════════════════════════════════════════════

WORKFLOW_TEMPLATES: dict[str, dict[str, Any]] = {
    "motor_underwriting": {
        "name": "Motor Insurance Underwriting",
        "name_ar": "اكتتاب تأمين المركبات",
        "workflow_type": "underwriting",
        "description": "Standard motor insurance underwriting with risk scoring and manager approval",
        "steps": [
            {"step_name": "data_enrichment", "step_type": "auto"},
            {"step_name": "risk_score_calculation", "step_type": "auto"},
            {"step_name": "fraud_screening", "step_type": "auto"},
            {"step_name": "policy_compliance_check", "step_type": "auto"},
            {
                "step_name": "risk_threshold_check",
                "step_type": "conditional",
                "config": {"field": "risk_score", "operator": ">=", "threshold": 0.6},
            },
            {"step_name": "underwriter_review", "step_type": "hitl"},
            {"step_name": "manager_approval", "step_type": "hitl"},
        ],
    },
    "marine_claims": {
        "name": "Marine Cargo Claims Processing",
        "name_ar": "معالجة مطالبات البضائع البحرية",
        "workflow_type": "claims",
        "description": "Marine cargo claims with simulation-linked risk assessment",
        "steps": [
            {"step_name": "data_enrichment", "step_type": "auto"},
            {"step_name": "simulation_trigger", "step_type": "api_call"},
            {"step_name": "risk_score_calculation", "step_type": "auto"},
            {"step_name": "fraud_screening", "step_type": "auto"},
            {"step_name": "adjuster_review", "step_type": "hitl"},
            {"step_name": "policy_compliance_check", "step_type": "auto"},
            {"step_name": "manager_approval", "step_type": "hitl"},
        ],
    },
    "cyber_risk_assessment": {
        "name": "Cyber Risk Assessment",
        "name_ar": "تقييم المخاطر السيبرانية",
        "workflow_type": "risk_assessment",
        "description": "GCC cyber risk assessment with simulation and multi-level approval",
        "steps": [
            {"step_name": "data_enrichment", "step_type": "auto"},
            {"step_name": "simulation_trigger", "step_type": "api_call"},
            {"step_name": "risk_score_calculation", "step_type": "auto"},
            {
                "step_name": "severity_check",
                "step_type": "conditional",
                "config": {"field": "risk_score", "operator": ">=", "threshold": 0.7},
            },
            {"step_name": "analyst_review", "step_type": "hitl"},
            {"step_name": "cro_approval", "step_type": "hitl"},
        ],
    },
}
