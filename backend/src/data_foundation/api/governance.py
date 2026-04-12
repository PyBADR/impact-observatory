"""Governance Layer API routes.

Exposes governance policies, rule lifecycle, truth validation,
calibration triggers/events, and unified audit chain.

Read-heavy, write-controlled — all mutations produce audit entries.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.api.deps import get_session
from src.data_foundation.governance.converters import (
    governance_policy_to_orm,
    governance_policy_from_orm,
    lifecycle_event_from_orm,
    truth_policy_to_orm,
    truth_policy_from_orm,
    truth_result_from_orm,
    calibration_trigger_to_orm,
    calibration_trigger_from_orm,
    calibration_event_from_orm,
    audit_entry_from_orm,
)
from src.data_foundation.governance.repositories import (
    GovernancePolicyRepo,
    RuleLifecycleEventRepo,
    TruthValidationPolicyRepo,
    TruthValidationResultRepo,
    CalibrationTriggerRepo,
    CalibrationEventRepo,
    GovernanceAuditEntryRepo,
)
from src.data_foundation.governance.schemas import (
    GovernancePolicy,
    TruthValidationPolicy,
    CalibrationTrigger,
)

router = APIRouter(
    prefix="/foundation/governance",
    tags=["Data Foundation — Governance"],
)


# ═══════════════════════════════════════════════════════════════════════════════
# Governance Policies
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/policies", response_model=list[dict])
async def list_policies(
    policy_type: Optional[str] = Query(None, description="Filter by policy type"),
    is_active: Optional[bool] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = GovernancePolicyRepo(session)
    if policy_type:
        rows = await repo.get_active_by_type(policy_type)
    else:
        rows = await repo.list_all(limit=limit)
    results = [governance_policy_from_orm(r) for r in rows]
    if is_active is not None:
        results = [r for r in results if r.is_active == is_active]
    return [r.model_dump(mode="json") for r in results]


@router.get("/policies/{policy_id}")
async def get_policy(policy_id: str, session: AsyncSession = Depends(get_session)):
    repo = GovernancePolicyRepo(session)
    row = await repo.get_by_pk(policy_id)
    if not row:
        raise HTTPException(404, f"Policy '{policy_id}' not found")
    return governance_policy_from_orm(row).model_dump(mode="json")


@router.post("/policies", status_code=201)
async def create_policy(body: GovernancePolicy, session: AsyncSession = Depends(get_session)):
    repo = GovernancePolicyRepo(session)
    existing = await repo.get_by_pk(body.policy_id)
    if existing:
        raise HTTPException(409, f"Policy '{body.policy_id}' already exists")
    body.compute_hash()
    orm = governance_policy_to_orm(body)
    await repo.create(orm)
    await session.commit()
    return governance_policy_from_orm(orm).model_dump(mode="json")


# ═══════════════════════════════════════════════════════════════════════════════
# Rule Lifecycle Events (read-only — created by lifecycle engine)
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/lifecycle-events", response_model=list[dict])
async def list_lifecycle_events(
    spec_id: Optional[str] = Query(None, description="Filter by rule spec ID"),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = RuleLifecycleEventRepo(session)
    if spec_id:
        rows = await repo.get_by_spec(spec_id, limit=limit)
    else:
        rows = await repo.list_all(limit=limit)
    return [lifecycle_event_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/lifecycle-events/{event_id}")
async def get_lifecycle_event(event_id: str, session: AsyncSession = Depends(get_session)):
    repo = RuleLifecycleEventRepo(session)
    row = await repo.get_by_pk(event_id)
    if not row:
        raise HTTPException(404, f"Lifecycle event '{event_id}' not found")
    return lifecycle_event_from_orm(row).model_dump(mode="json")


# ═══════════════════════════════════════════════════════════════════════════════
# Truth Validation Policies
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/truth-policies", response_model=list[dict])
async def list_truth_policies(
    target_dataset: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    repo = TruthValidationPolicyRepo(session)
    if target_dataset:
        row = await repo.get_active_for_dataset(target_dataset)
        rows = [row] if row else []
    else:
        rows = await repo.get_all_active()
    return [truth_policy_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/truth-policies/{policy_id}")
async def get_truth_policy(policy_id: str, session: AsyncSession = Depends(get_session)):
    repo = TruthValidationPolicyRepo(session)
    row = await repo.get_by_pk(policy_id)
    if not row:
        raise HTTPException(404, f"Truth policy '{policy_id}' not found")
    return truth_policy_from_orm(row).model_dump(mode="json")


@router.post("/truth-policies", status_code=201)
async def create_truth_policy(body: TruthValidationPolicy, session: AsyncSession = Depends(get_session)):
    repo = TruthValidationPolicyRepo(session)
    existing = await repo.get_by_pk(body.policy_id)
    if existing:
        raise HTTPException(409, f"Truth policy '{body.policy_id}' already exists")
    body.compute_hash()
    orm = truth_policy_to_orm(body)
    await repo.create(orm)
    await session.commit()
    return truth_policy_from_orm(orm).model_dump(mode="json")


# ═══════════════════════════════════════════════════════════════════════════════
# Truth Validation Results (read-only — produced by validation engine)
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/truth-results", response_model=list[dict])
async def list_truth_results(
    policy_id: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = TruthValidationResultRepo(session)
    if policy_id:
        rows = await repo.get_by_policy(policy_id, limit=limit)
    else:
        rows = await repo.list_all(limit=limit)
    return [truth_result_from_orm(r).model_dump(mode="json") for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# Calibration Triggers
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/calibration-triggers", response_model=list[dict])
async def list_calibration_triggers(
    trigger_type: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    repo = CalibrationTriggerRepo(session)
    if trigger_type:
        rows = await repo.get_by_type(trigger_type)
    else:
        rows = await repo.get_active()
    return [calibration_trigger_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/calibration-triggers/{trigger_id}")
async def get_calibration_trigger(trigger_id: str, session: AsyncSession = Depends(get_session)):
    repo = CalibrationTriggerRepo(session)
    row = await repo.get_by_pk(trigger_id)
    if not row:
        raise HTTPException(404, f"Calibration trigger '{trigger_id}' not found")
    return calibration_trigger_from_orm(row).model_dump(mode="json")


@router.post("/calibration-triggers", status_code=201)
async def create_calibration_trigger(body: CalibrationTrigger, session: AsyncSession = Depends(get_session)):
    repo = CalibrationTriggerRepo(session)
    existing = await repo.get_by_pk(body.trigger_id)
    if existing:
        raise HTTPException(409, f"Trigger '{body.trigger_id}' already exists")
    body.compute_hash()
    orm = calibration_trigger_to_orm(body)
    await repo.create(orm)
    await session.commit()
    return calibration_trigger_from_orm(orm).model_dump(mode="json")


# ═══════════════════════════════════════════════════════════════════════════════
# Calibration Events (read-only — produced by calibration engine)
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/calibration-events", response_model=list[dict])
async def list_calibration_events(
    rule_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None, description="Filter by status (TRIGGERED, RESOLVED, etc.)"),
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = CalibrationEventRepo(session)
    if rule_id:
        rows = await repo.get_by_rule(rule_id, limit=limit)
    elif status == "TRIGGERED":
        rows = await repo.get_unresolved()
    else:
        rows = await repo.list_all(limit=limit)
    return [calibration_event_from_orm(r).model_dump(mode="json") for r in rows]


# ═══════════════════════════════════════════════════════════════════════════════
# Governance Audit Trail
# ═══════════════════════════════════════════════════════════════════════════════


@router.get("/audit", response_model=list[dict])
async def list_audit_entries(
    subject_type: Optional[str] = Query(None),
    subject_id: Optional[str] = Query(None),
    event_type: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    repo = GovernanceAuditEntryRepo(session)
    if subject_type and subject_id:
        rows = await repo.get_by_subject(subject_type, subject_id, limit=limit)
    elif event_type:
        rows = await repo.get_by_event_type(event_type, limit=limit)
    elif actor:
        rows = await repo.get_by_actor(actor, limit=limit)
    else:
        rows = await repo.list_all(limit=limit)
    return [audit_entry_from_orm(r).model_dump(mode="json") for r in rows]


@router.get("/audit/{entry_id}")
async def get_audit_entry(entry_id: str, session: AsyncSession = Depends(get_session)):
    repo = GovernanceAuditEntryRepo(session)
    row = await repo.get_by_pk(entry_id)
    if not row:
        raise HTTPException(404, f"Audit entry '{entry_id}' not found")
    return audit_entry_from_orm(row).model_dump(mode="json")


@router.get("/audit/chain/{start_entry_id}", response_model=list[dict])
async def get_audit_chain(
    start_entry_id: str,
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    """Get the audit chain starting from a specific entry, ordered chronologically."""
    repo = GovernanceAuditEntryRepo(session)
    rows = await repo.get_chain(start_entry_id, limit=limit)
    if not rows:
        raise HTTPException(404, f"Audit entry '{start_entry_id}' not found or chain empty")
    entries = [audit_entry_from_orm(r) for r in rows]

    # Verify chain integrity inline
    from src.data_foundation.governance.governance_audit import verify_chain
    violations = verify_chain(entries)

    return {
        "chain": [e.model_dump(mode="json") for e in entries],
        "chain_valid": len(violations) == 0,
        "violations": violations,
        "total_entries": len(entries),
    }
