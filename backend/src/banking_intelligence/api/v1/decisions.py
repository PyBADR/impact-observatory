"""
Banking Intelligence — Decision Contract API
==============================================
Full lifecycle management for decision contracts,
counterfactual analyses, outcome reviews, and value audits.
"""
from __future__ import annotations

from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.banking_intelligence.schemas.decision_contract import (
    DecisionContract,
    DecisionStatus,
    VALID_TRANSITIONS,
)
from src.banking_intelligence.schemas.counterfactual import CounterfactualContract
from src.banking_intelligence.schemas.propagation import PropagationContract, PropagationChain
from src.banking_intelligence.schemas.outcome_review import (
    OutcomeReviewContract,
    DecisionValueAudit,
)


router = APIRouter(prefix="/banking/decisions", tags=["banking-decisions"])

# ── In-memory stores ───────────────────────────────────────────────────────
_decisions: dict[str, dict[str, Any]] = {}
_counterfactuals: dict[str, dict[str, Any]] = {}
_propagations: dict[str, dict[str, Any]] = {}
_outcome_reviews: dict[str, dict[str, Any]] = {}
_value_audits: dict[str, dict[str, Any]] = {}

# Optional graph writer (injected at startup)
_graph_writer = None


def set_graph_writer(writer):
    global _graph_writer
    _graph_writer = writer


# ═══════════════════════════════════════════════════════════════════════════
# Decision Contract CRUD
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/contracts", response_model=dict)
async def create_decision_contract(data: dict[str, Any]):
    """Create a new decision contract."""
    try:
        contract = DecisionContract.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    _decisions[contract.decision_id] = contract.model_dump(mode="json")

    if _graph_writer:
        try:
            await _graph_writer.write_decision_contract(contract)
        except Exception:
            pass  # Graph write is optional

    return {"decision_id": contract.decision_id, "status": contract.status.value}


@router.get("/contracts")
async def list_decision_contracts(
    scenario_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    sector: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=500),
):
    """List decision contracts with filtering."""
    results = list(_decisions.values())
    if scenario_id:
        results = [r for r in results if r.get("scenario_id") == scenario_id]
    if status:
        results = [r for r in results if r.get("status") == status]
    if sector:
        results = [r for r in results if r.get("sector") == sector]
    return {"total": len(results), "results": results[:limit]}


@router.get("/contracts/{decision_id}")
async def get_decision_contract(decision_id: str):
    """Get a single decision contract with full detail."""
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail=f"Decision not found: {decision_id}")
    return _decisions[decision_id]


class TransitionRequest(BaseModel):
    target_status: str
    changed_by: str
    reason: Optional[str] = None


@router.post("/contracts/{decision_id}/transition")
async def transition_decision(decision_id: str, req: TransitionRequest):
    """Execute a state transition on a decision contract."""
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail=f"Decision not found: {decision_id}")

    try:
        contract = DecisionContract.model_validate(_decisions[decision_id])
        target = DecisionStatus(req.target_status)
        contract.transition_to(target, req.changed_by, req.reason)
        _decisions[decision_id] = contract.model_dump(mode="json")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "decision_id": decision_id,
        "status": contract.status.value,
        "transition_count": len(contract.status_history),
    }


@router.get("/contracts/{decision_id}/chain")
async def get_decision_chain(decision_id: str):
    """Get decision with linked counterfactual, review, and audit."""
    if decision_id not in _decisions:
        raise HTTPException(status_code=404, detail=f"Decision not found: {decision_id}")

    decision = _decisions[decision_id]
    cf_id = decision.get("counterfactual_id")
    review_id = decision.get("outcome_review_id")
    audit_id = decision.get("value_audit_id")

    return {
        "decision": decision,
        "counterfactual": _counterfactuals.get(cf_id) if cf_id else None,
        "outcome_review": _outcome_reviews.get(review_id) if review_id else None,
        "value_audit": _value_audits.get(audit_id) if audit_id else None,
    }


# ═══════════════════════════════════════════════════════════════════════════
# Counterfactual Analysis
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/counterfactuals", response_model=dict)
async def create_counterfactual(data: dict[str, Any]):
    """Create a counterfactual analysis."""
    try:
        cf = CounterfactualContract.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    _counterfactuals[cf.counterfactual_id] = cf.model_dump(mode="json")

    # Link to decision
    if cf.decision_id in _decisions:
        _decisions[cf.decision_id]["counterfactual_id"] = cf.counterfactual_id

    if _graph_writer:
        try:
            await _graph_writer.write_counterfactual(cf)
        except Exception:
            pass

    return {
        "counterfactual_id": cf.counterfactual_id,
        "recommended_net_benefit_usd": cf.recommended_net_benefit_usd,
        "confidence_adjusted_benefit_usd": cf.confidence_adjusted_benefit_usd,
        "is_action_justified": cf.is_action_justified,
    }


@router.get("/counterfactuals/{cf_id}")
async def get_counterfactual(cf_id: str):
    if cf_id not in _counterfactuals:
        raise HTTPException(status_code=404, detail=f"Counterfactual not found: {cf_id}")
    return _counterfactuals[cf_id]


# ═══════════════════════════════════════════════════════════════════════════
# Propagation Contracts
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/propagations", response_model=dict)
async def create_propagation(data: dict[str, Any]):
    """Create a propagation intervention contract."""
    try:
        prop = PropagationContract.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    _propagations[prop.propagation_id] = prop.model_dump(mode="json")

    if _graph_writer:
        try:
            await _graph_writer.write_propagation(prop)
        except Exception:
            pass

    return {
        "propagation_id": prop.propagation_id,
        "from": prop.from_entity_id,
        "to": prop.to_entity_id,
        "breakable": prop.breakable_point,
        "max_blockable_severity": prop.max_blockable_severity,
    }


@router.get("/propagations")
async def list_propagations(
    scenario_id: Optional[str] = Query(None),
    breakable_only: bool = Query(False),
):
    results = list(_propagations.values())
    if scenario_id:
        results = [r for r in results if r.get("scenario_id") == scenario_id]
    if breakable_only:
        results = [r for r in results if r.get("breakable_point") is True]
    return {"total": len(results), "results": results}


@router.get("/propagations/{prop_id}")
async def get_propagation(prop_id: str):
    if prop_id not in _propagations:
        raise HTTPException(status_code=404, detail=f"Propagation not found: {prop_id}")
    return _propagations[prop_id]


# ═══════════════════════════════════════════════════════════════════════════
# Outcome Reviews
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/outcome-reviews", response_model=dict)
async def create_outcome_review(data: dict[str, Any]):
    """Create an outcome review."""
    try:
        review = OutcomeReviewContract.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    _outcome_reviews[review.review_id] = review.model_dump(mode="json")

    if review.decision_id in _decisions:
        _decisions[review.decision_id]["outcome_review_id"] = review.review_id

    if _graph_writer:
        try:
            await _graph_writer.write_outcome_review(review)
        except Exception:
            pass

    return {
        "review_id": review.review_id,
        "windows": len(review.windows),
        "completion_pct": review.completion_pct,
    }


@router.get("/outcome-reviews/{review_id}")
async def get_outcome_review(review_id: str):
    if review_id not in _outcome_reviews:
        raise HTTPException(status_code=404, detail=f"Review not found: {review_id}")
    return _outcome_reviews[review_id]


# ═══════════════════════════════════════════════════════════════════════════
# Value Audits
# ═══════════════════════════════════════════════════════════════════════════

@router.post("/value-audits", response_model=dict)
async def create_value_audit(data: dict[str, Any]):
    """Create a decision value audit."""
    try:
        audit = DecisionValueAudit.model_validate(data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    _value_audits[audit.audit_id] = audit.model_dump(mode="json")

    if audit.decision_id in _decisions:
        _decisions[audit.decision_id]["value_audit_id"] = audit.audit_id

    if _graph_writer:
        try:
            await _graph_writer.write_value_audit(audit)
        except Exception:
            pass

    return {
        "audit_id": audit.audit_id,
        "net_value_usd": audit.net_value_usd,
        "confidence_adjusted_value_usd": audit.confidence_adjusted_value_usd,
        "cfo_defensible": audit.cfo_defensible,
        "defensibility_gaps": audit.defensibility_gaps,
    }


@router.get("/value-audits/{audit_id}")
async def get_value_audit(audit_id: str):
    if audit_id not in _value_audits:
        raise HTTPException(status_code=404, detail=f"Audit not found: {audit_id}")
    return _value_audits[audit_id]
