"""Enforcement Layer API routes.

Exposes enforcement policies, decisions, execution gates,
and approval requests. Includes enforcement evaluation endpoint.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.api.deps import get_session
from src.data_foundation.enforcement.converters import (
    enforcement_policy_to_orm,
    enforcement_policy_from_orm,
    enforcement_decision_to_orm,
    enforcement_decision_from_orm,
    execution_gate_to_orm,
    execution_gate_from_orm,
    approval_request_to_orm,
    approval_request_from_orm,
)
from src.data_foundation.enforcement.repositories import (
    EnforcementPolicyRepo,
    EnforcementDecisionRepo,
    ExecutionGateResultRepo,
    ApprovalRequestRepo,
)
from src.data_foundation.enforcement.schemas import (
    ApprovalRequest,
    EnforcementPolicy,
)
from src.data_foundation.enforcement.enforcement_engine import (
    EnforcementContext,
    evaluate_enforcement,
)
from src.data_foundation.enforcement.execution_gate_service import (
    resolve_gate,
    resolve_approval,
)
from src.data_foundation.enforcement.enforcement_audit import (
    audit_enforcement_policy_created,
    audit_enforcement_evaluated,
    audit_gate_resolved,
    audit_approval_requested,
    audit_approval_resolved,
)
from src.data_foundation.governance.converters import audit_entry_to_orm
from src.data_foundation.governance.repositories import GovernanceAuditEntryRepo

router = APIRouter(
    prefix="/foundation/enforcement",
    tags=["Data Foundation — Enforcement"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Request/Response models
# ═══════════════════════════════════════════════════════════════════════════════


class EvaluateEnforcementRequest(BaseModel):
    """POST body for enforcement evaluation."""

    decision_log_id: str = Field(...)
    rule_id: str = Field(...)
    spec_id: Optional[str] = Field(default=None)
    decision_action: Optional[str] = Field(default=None)
    decision_risk_level: Optional[str] = Field(default=None)
    decision_country: Optional[str] = Field(default=None)
    decision_sector: Optional[str] = Field(default=None)
    decision_confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    # Governance state (caller provides snapshot)
    rule_status: Optional[str] = Field(default=None)
    truth_valid: Optional[bool] = Field(default=None)
    unresolved_calibrations: int = Field(default=0, ge=0)
    latest_correctness_score: Optional[float] = Field(default=None)

    persist: bool = Field(
        default=True,
        description="Persist enforcement decision, gate, and audit entries.",
    )


class ResolveApprovalRequest(BaseModel):
    """POST body for resolving an approval request."""

    approved: bool = Field(...)
    approver: str = Field(...)
    reason: Optional[str] = Field(default=None)


# ═══════════════════════════════════════════════════════════════════════════════
# Policy CRUD
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/policies", response_model=list[dict])
async def list_enforcement_policies(
    enforcement_action: Optional[str] = Query(None),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = EnforcementPolicyRepo(session)
    if enforcement_action:
        rows = await repo.get_by_action(enforcement_action)
    else:
        rows = await repo.get_active_ordered()
    results = [enforcement_policy_from_orm(r) for r in rows]
    if is_active is not None:
        results = [r for r in results if r.is_active == is_active]
    return [r.model_dump(mode="json") for r in results[:limit]]


@router.get("/policies/{policy_id}")
async def get_enforcement_policy(
    policy_id: str, session: AsyncSession = Depends(get_session),
):
    repo = EnforcementPolicyRepo(session)
    row = await repo.get_by_pk(policy_id)
    if not row:
        raise HTTPException(404, f"Enforcement policy '{policy_id}' not found")
    return enforcement_policy_from_orm(row).model_dump(mode="json")


@router.post("/policies", status_code=201)
async def create_enforcement_policy(
    body: EnforcementPolicy, session: AsyncSession = Depends(get_session),
):
    repo = EnforcementPolicyRepo(session)
    existing = await repo.get_by_pk(body.policy_id)
    if existing:
        raise HTTPException(409, f"Policy '{body.policy_id}' already exists")
    body.compute_hash()
    orm = enforcement_policy_to_orm(body)
    await repo.create(orm)

    # Audit
    audit_repo = GovernanceAuditEntryRepo(session)
    latest = await audit_repo.get_latest()
    prev_hash = latest.provenance_hash if latest else None
    audit = audit_enforcement_policy_created(body, body.authored_by, prev_hash)
    await audit_repo.create(audit_entry_to_orm(audit))

    await session.commit()
    return enforcement_policy_from_orm(orm).model_dump(mode="json")


# ═══════════════════════════════════════════════════════════════════════════════
# Enforcement decisions (read-only)
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/decisions", response_model=list[dict])
async def list_enforcement_decisions(
    decision_log_id: Optional[str] = Query(None),
    enforcement_action: Optional[str] = Query(None),
    blocked_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = EnforcementDecisionRepo(session)
    if decision_log_id:
        rows = await repo.get_by_decision_log(decision_log_id)
    elif blocked_only:
        rows = await repo.get_blocked(limit=limit)
    elif enforcement_action:
        rows = await repo.get_by_action(enforcement_action, limit=limit)
    else:
        rows = await repo.list_all(limit=limit)
    return [enforcement_decision_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/decisions/{decision_id}")
async def get_enforcement_decision(
    decision_id: str, session: AsyncSession = Depends(get_session),
):
    repo = EnforcementDecisionRepo(session)
    row = await repo.get_by_pk(decision_id)
    if not row:
        raise HTTPException(404, f"Enforcement decision '{decision_id}' not found")
    return enforcement_decision_from_orm(row).model_dump(mode="json")


# ═══════════════════════════════════════════════════════════════════════════════
# Execution gates (read-only)
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/gates", response_model=list[dict])
async def list_gates(
    gate_outcome: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = ExecutionGateResultRepo(session)
    if gate_outcome:
        rows = await repo.get_by_outcome(gate_outcome, limit=limit)
    else:
        rows = await repo.list_all(limit=limit)
    return [execution_gate_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/gates/{gate_id}")
async def get_gate(
    gate_id: str, session: AsyncSession = Depends(get_session),
):
    repo = ExecutionGateResultRepo(session)
    row = await repo.get_by_pk(gate_id)
    if not row:
        raise HTTPException(404, f"Gate '{gate_id}' not found")
    return execution_gate_from_orm(row).model_dump(mode="json")


# ═══════════════════════════════════════════════════════════════════════════════
# Approval requests
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/approvals", response_model=list[dict])
async def list_approval_requests(
    status: Optional[str] = Query(None),
    required_approver_role: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    repo = ApprovalRequestRepo(session)
    if required_approver_role:
        rows = await repo.get_by_role(required_approver_role, status=status or "PENDING")
    elif status:
        rows = await repo.list_all(limit=500)
        rows = [r for r in rows if r.status == status]
    else:
        rows = await repo.get_pending()
    return [approval_request_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/approvals/{request_id}")
async def get_approval_request(
    request_id: str, session: AsyncSession = Depends(get_session),
):
    repo = ApprovalRequestRepo(session)
    row = await repo.get_by_pk(request_id)
    if not row:
        raise HTTPException(404, f"Approval request '{request_id}' not found")
    return approval_request_from_orm(row).model_dump(mode="json")


@router.post("/approvals/{request_id}/resolve")
async def resolve_approval_request(
    request_id: str,
    body: ResolveApprovalRequest,
    session: AsyncSession = Depends(get_session),
):
    """Resolve a pending approval request (approve or deny)."""
    repo = ApprovalRequestRepo(session)
    row = await repo.get_by_pk(request_id)
    if not row:
        raise HTTPException(404, f"Approval request '{request_id}' not found")
    existing = approval_request_from_orm(row)
    if existing.status != "PENDING":
        raise HTTPException(409, f"Approval request already resolved: {existing.status}")

    resolved = resolve_approval(existing, body.approved, body.approver, body.reason)

    # Update in DB
    await repo.update_fields(
        request_id,
        status=resolved.status,
        approved_by=resolved.approved_by,
        approval_reason=resolved.approval_reason,
        resolved_at=resolved.resolved_at,
        provenance_hash=resolved.provenance_hash,
    )

    # Audit
    audit_repo = GovernanceAuditEntryRepo(session)
    latest = await audit_repo.get_latest()
    prev_hash = latest.provenance_hash if latest else None
    audit = audit_approval_resolved(resolved, body.approver, prev_hash)
    await audit_repo.create(audit_entry_to_orm(audit))

    await session.commit()
    return resolved.model_dump(mode="json")


# ═══════════════════════════════════════════════════════════════════════════════
# Enforcement evaluation endpoint
# ═══════════════════════════════════════════════════════════════════════════════


@router.post("/evaluate")
async def evaluate_enforcement_endpoint(
    request: EvaluateEnforcementRequest,
    session: AsyncSession = Depends(get_session),
):
    """Evaluate enforcement policies against a decision candidate.

    Returns the enforcement decision, execution gate, and optional
    approval request.
    """
    # 1. Load active policies
    policy_repo = EnforcementPolicyRepo(session)
    policy_rows = await policy_repo.get_active_ordered()
    policies = [enforcement_policy_from_orm(r) for r in policy_rows]

    # 2. Build context
    context = EnforcementContext(
        decision_log_id=request.decision_log_id,
        rule_id=request.rule_id,
        spec_id=request.spec_id,
        decision_action=request.decision_action,
        decision_risk_level=request.decision_risk_level,
        decision_country=request.decision_country,
        decision_sector=request.decision_sector,
        decision_confidence=request.decision_confidence,
        rule_status=request.rule_status,
        truth_valid=request.truth_valid,
        unresolved_calibrations=request.unresolved_calibrations,
        latest_correctness_score=request.latest_correctness_score,
    )

    # 3. Evaluate enforcement
    enforcement_decision = evaluate_enforcement(policies, context)

    # 4. Resolve gate
    gate, approval = resolve_gate(enforcement_decision)

    # 5. Persist if requested
    if request.persist:
        dec_repo = EnforcementDecisionRepo(session)
        gate_repo = ExecutionGateResultRepo(session)
        audit_repo = GovernanceAuditEntryRepo(session)

        await dec_repo.create(enforcement_decision_to_orm(enforcement_decision))

        if approval:
            approval_repo = ApprovalRequestRepo(session)
            gate.approval_request_id = approval.request_id
            await approval_repo.create(approval_request_to_orm(approval))

        await gate_repo.create(execution_gate_to_orm(gate))

        # Audit chain
        latest = await audit_repo.get_latest()
        prev_hash = latest.provenance_hash if latest else None

        a1 = audit_enforcement_evaluated(enforcement_decision, "system", prev_hash)
        await audit_repo.create(audit_entry_to_orm(a1))

        a2 = audit_gate_resolved(gate, "system", a1.audit_hash)
        await audit_repo.create(audit_entry_to_orm(a2))

        if approval:
            a3 = audit_approval_requested(approval, "system", a2.audit_hash)
            await audit_repo.create(audit_entry_to_orm(a3))

        await session.commit()

    return {
        "enforcement_decision": enforcement_decision.model_dump(mode="json"),
        "execution_gate": gate.model_dump(mode="json"),
        "approval_request": approval.model_dump(mode="json") if approval else None,
    }
