"""Decision Engine API — evaluate events against rules.

POST /foundation/decision-engine/evaluate-event

Accepts an event payload and returns:
  - matched rules
  - impact chain
  - affected entities
  - decision proposals
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from src.data_foundation.api.deps import get_session
from src.data_foundation.models.converters import (
    event_to_orm,
    event_from_orm,
    rule_from_orm,
    dlog_to_orm,
)
from src.data_foundation.repositories.entity_repo import EntityRepository
from src.data_foundation.repositories.event_repo import EventRepository
from src.data_foundation.repositories.rule_repo import RuleRepository
from src.data_foundation.repositories.dlog_repo import DecisionLogRepository
from src.data_foundation.schemas.event_signals import EventSignal
from src.data_foundation.schemas.decision_rules import DecisionRule
from src.data_foundation.schemas.decision_logs import DecisionLogEntry, TriggerContext
from src.data_foundation.decision.rule_engine import (
    DataState,
    evaluate_all_rules,
    RuleEvaluationResult,
)
from src.data_foundation.decision.impact_chain import (
    SignalDetection,
    TransmissionPath,
    ExposureAssessment,
    DecisionProposal,
    ImpactChain,
)
from src.data_foundation.schemas.enums import DecisionStatus

router = APIRouter(prefix="/foundation/decision-engine", tags=["Data Foundation — Decision Engine"])


# ── Request / Response models ────────────────────────────────────────────────

class EvaluateEventRequest(BaseModel):
    """POST body for event evaluation."""
    event: EventSignal = Field(..., description="The event signal to evaluate.")
    persist_event: bool = Field(
        default=True,
        description="Whether to persist the event to the database.",
    )
    persist_decisions: bool = Field(
        default=True,
        description="Whether to persist decision logs to the database.",
    )
    additional_state: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional data state values for rule evaluation.",
    )


class AffectedEntitySummary(BaseModel):
    entity_id: str
    entity_name: str
    entity_type: str
    country: str
    sector: str
    criticality_score: float


class MatchedRuleSummary(BaseModel):
    rule_id: str
    rule_name: str
    action: str
    escalation_level: str
    requires_human_approval: bool
    conditions_met: List[bool]
    reason: str


class DecisionProposalSummary(BaseModel):
    proposal_id: str
    rule_id: str
    action: str
    risk_level: str
    requires_approval: bool
    rationale: str
    affected_entity_ids: List[str]
    status: str


class EvaluateEventResponse(BaseModel):
    """Full response from event evaluation."""
    event_id: str
    event_persisted: bool
    severity: str
    severity_score: float

    matched_rules: List[MatchedRuleSummary]
    total_rules_evaluated: int
    total_rules_matched: int
    total_rules_blocked: int

    affected_entities: List[AffectedEntitySummary]

    decision_proposals: List[DecisionProposalSummary]
    decisions_persisted: bool

    impact_chain: Dict[str, Any]

    data_state_hash: str
    evaluated_at: str


# ── Core evaluation logic ────────────────────────────────────────────────────

def _build_data_state(event: EventSignal, extra: Dict[str, Any] | None = None) -> DataState:
    """Build a DataState from an event signal for rule evaluation."""
    values = {
        "event_signals.severity_score": event.severity_score,
        "event_signals.category": event.category.value if hasattr(event.category, "value") else event.category,
        "event_signals.is_ongoing": event.is_ongoing,
        "event_signals.corroborating_source_count": event.corroborating_source_count,
    }
    if extra:
        values.update(extra)
    return DataState(values=values)


def _build_signal(event: EventSignal) -> SignalDetection:
    return SignalDetection(
        signal_ref_id=event.event_id,
        signal_dataset="p1_event_signals",
        signal_type=event.category.value if hasattr(event.category, "value") else event.category,
        severity=event.severity,
        severity_score=event.severity_score,
        detected_at=event.detected_at,
        countries_affected=event.countries_affected,
        sectors_affected=event.sectors_affected,
        confidence_score=event.confidence_score,
    )


def _build_chain(
    event: EventSignal,
    signal: SignalDetection,
    proposals: List[DecisionProposal],
) -> ImpactChain:
    return ImpactChain(
        chain_id=f"CHAIN-{event.event_id}",
        signal=signal,
        transmissions=[],
        exposures=[],
        decisions=proposals,
        outcomes=[],
        created_at=datetime.now(timezone.utc),
        chain_status="ACTIVE",
    )


def _create_log_entry(
    rule: DecisionRule,
    event: EventSignal,
    prev_hash: str | None,
) -> DecisionLogEntry:
    """Create a DecisionLogEntry from a triggered rule."""
    log_id = f"DLOG-{event.event_id[:20]}-{rule.rule_id[:20]}-{uuid.uuid4().hex[:8]}"

    trigger_ctx = TriggerContext(
        signal_ids=[event.event_id],
        indicator_values={"severity_score": event.severity_score},
        scenario_id=event.scenario_ids[0] if event.scenario_ids else None,
        urs_score=event.severity_score,
        risk_level=rule.escalation_level,
    )

    # Compute audit hash
    hash_input = json.dumps({
        "log_id": log_id,
        "rule_id": rule.rule_id,
        "event_id": event.event_id,
        "action": rule.action.value if hasattr(rule.action, "value") else rule.action,
    }, sort_keys=True)
    audit_hash = hashlib.sha256(hash_input.encode()).hexdigest()

    return DecisionLogEntry(
        log_id=log_id,
        rule_id=rule.rule_id,
        rule_version=rule.version,
        triggered_at=datetime.now(timezone.utc),
        action=rule.action,
        status=DecisionStatus.PROPOSED if rule.requires_human_approval else DecisionStatus.APPROVED,
        trigger_context=trigger_ctx,
        country=event.countries_affected[0] if event.countries_affected else None,
        entity_ids=event.entity_ids_affected,
        requires_approval=rule.requires_human_approval,
        audit_hash=audit_hash,
        previous_log_hash=prev_hash,
    )


# ── Endpoint ─────────────────────────────────────────────────────────────────

@router.post("/evaluate-event", response_model=EvaluateEventResponse)
async def evaluate_event(
    request: EvaluateEventRequest,
    session: AsyncSession = Depends(get_session),
):
    """Evaluate an event against all active decision rules.

    Returns matched rules, affected entities, decision proposals,
    and a full impact chain for audit.
    """
    event = request.event

    # 1. Persist event if requested
    event_persisted = False
    if request.persist_event:
        try:
            event_repo = EventRepository(session)
            existing = await event_repo.get_by_pk(event.event_id)
            if not existing:
                orm = event_to_orm(event)
                await event_repo.create(orm)
                event_persisted = True
        except Exception:
            pass  # Non-fatal: evaluation proceeds even if persistence fails

    # 2. Load active rules from DB
    rule_repo = RuleRepository(session)
    rule_rows = await rule_repo.find_active()
    rules = [rule_from_orm(r) for r in rule_rows]

    # 3. Build data state and evaluate
    data_state = _build_data_state(event, request.additional_state)
    engine_output = evaluate_all_rules(rules, data_state)

    # 4. Look up affected entities
    entity_repo = EntityRepository(session)
    affected_summaries: List[AffectedEntitySummary] = []
    for eid in event.entity_ids_affected:
        row = await entity_repo.get_by_pk(eid)
        if row:
            affected_summaries.append(AffectedEntitySummary(
                entity_id=row.entity_id,
                entity_name=row.entity_name,
                entity_type=row.entity_type,
                country=row.country,
                sector=row.sector,
                criticality_score=row.criticality_score,
            ))

    # 5. Build matched rule summaries
    matched_summaries: List[MatchedRuleSummary] = []
    triggered_rules: List[DecisionRule] = []
    for eval_result in engine_output.triggered_rules:
        rule = next((r for r in rules if r.rule_id == eval_result.rule_id), None)
        if rule:
            triggered_rules.append(rule)
            matched_summaries.append(MatchedRuleSummary(
                rule_id=eval_result.rule_id,
                rule_name=rule.rule_name,
                action=eval_result.action.value if eval_result.action else "UNKNOWN",
                escalation_level=eval_result.risk_level.value if eval_result.risk_level else "UNKNOWN",
                requires_human_approval=rule.requires_human_approval,
                conditions_met=eval_result.conditions_met,
                reason=eval_result.reason,
            ))

    # 6. Create decision proposals and log entries
    signal = _build_signal(event)
    proposals: List[DecisionProposal] = []
    proposal_summaries: List[DecisionProposalSummary] = []
    decisions_persisted = False

    dlog_repo = DecisionLogRepository(session)
    prev_hash = await dlog_repo.get_latest_hash()

    for rule in triggered_rules:
        proposal_id = f"PROP-{event.event_id[:20]}-{rule.rule_id[:20]}"
        action_val = rule.action.value if hasattr(rule.action, "value") else rule.action
        esc_val = rule.escalation_level.value if hasattr(rule.escalation_level, "value") else rule.escalation_level

        proposal = DecisionProposal(
            proposal_id=proposal_id,
            exposure_ids=[],
            rule_id=rule.rule_id,
            rule_version=rule.version,
            action=rule.action,
            action_params=rule.action_params,
            risk_level=rule.escalation_level,
            requires_approval=rule.requires_human_approval,
            status=DecisionStatus.PROPOSED if rule.requires_human_approval else DecisionStatus.APPROVED,
            proposed_at=datetime.now(timezone.utc),
            rationale=f"Rule '{rule.rule_name}' triggered by event '{event.title}'. Action: {action_val}.",
            affected_entity_ids=event.entity_ids_affected,
            affected_countries=event.countries_affected,
        )
        proposals.append(proposal)

        status_val = "PROPOSED" if rule.requires_human_approval else "APPROVED"
        proposal_summaries.append(DecisionProposalSummary(
            proposal_id=proposal_id,
            rule_id=rule.rule_id,
            action=action_val,
            risk_level=esc_val,
            requires_approval=rule.requires_human_approval,
            rationale=proposal.rationale,
            affected_entity_ids=event.entity_ids_affected,
            status=status_val,
        ))

        # Persist decision log
        if request.persist_decisions:
            try:
                log_entry = _create_log_entry(rule, event, prev_hash)
                orm_log = dlog_to_orm(log_entry)
                await dlog_repo.create(orm_log)
                prev_hash = log_entry.audit_hash
                decisions_persisted = True
            except Exception:
                pass

    # 7. Build impact chain
    chain = _build_chain(event, signal, proposals)

    # 8. Commit all changes
    if event_persisted or decisions_persisted:
        await session.commit()

    return EvaluateEventResponse(
        event_id=event.event_id,
        event_persisted=event_persisted,
        severity=event.severity.value if hasattr(event.severity, "value") else event.severity,
        severity_score=event.severity_score,
        matched_rules=matched_summaries,
        total_rules_evaluated=engine_output.total_evaluated,
        total_rules_matched=engine_output.total_triggered,
        total_rules_blocked=engine_output.total_blocked,
        affected_entities=affected_summaries,
        decision_proposals=proposal_summaries,
        decisions_persisted=decisions_persisted,
        impact_chain=chain.model_dump(mode="json"),
        data_state_hash=engine_output.data_state_hash,
        evaluated_at=datetime.now(timezone.utc).isoformat(),
    )
