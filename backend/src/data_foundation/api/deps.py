"""Shared FastAPI dependencies for data_foundation routes."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession

from src.db.postgres import async_session_factory
from src.data_foundation.repositories import (
    EntityRepository,
    EventRepository,
    MacroRepository,
    RuleRepository,
    DecisionLogRepository,
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
from src.data_foundation.evaluation.repositories import (
    ExpectedOutcomeRepo,
    ActualOutcomeRepo,
    DecisionEvaluationRepo,
    AnalystFeedbackRepo,
    ReplayRunRepo,
    ReplayRunResultRepo,
    RulePerformanceRepo,
)
from src.data_foundation.enforcement.repositories import (
    EnforcementPolicyRepo,
    EnforcementDecisionRepo,
    ExecutionGateResultRepo,
    ApprovalRequestRepo,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


async def get_entity_repo(session: AsyncSession = None) -> AsyncGenerator[EntityRepository, None]:
    async with async_session_factory() as session:
        yield EntityRepository(session)


async def get_event_repo() -> AsyncGenerator[EventRepository, None]:
    async with async_session_factory() as session:
        yield EventRepository(session)


async def get_macro_repo() -> AsyncGenerator[MacroRepository, None]:
    async with async_session_factory() as session:
        yield MacroRepository(session)


async def get_rule_repo() -> AsyncGenerator[RuleRepository, None]:
    async with async_session_factory() as session:
        yield RuleRepository(session)


async def get_dlog_repo() -> AsyncGenerator[DecisionLogRepository, None]:
    async with async_session_factory() as session:
        yield DecisionLogRepository(session)


# ── Governance Layer ─────────────────────────────────────────────────────


async def get_governance_policy_repo() -> AsyncGenerator[GovernancePolicyRepo, None]:
    async with async_session_factory() as session:
        yield GovernancePolicyRepo(session)


async def get_lifecycle_event_repo() -> AsyncGenerator[RuleLifecycleEventRepo, None]:
    async with async_session_factory() as session:
        yield RuleLifecycleEventRepo(session)


async def get_truth_policy_repo() -> AsyncGenerator[TruthValidationPolicyRepo, None]:
    async with async_session_factory() as session:
        yield TruthValidationPolicyRepo(session)


async def get_truth_result_repo() -> AsyncGenerator[TruthValidationResultRepo, None]:
    async with async_session_factory() as session:
        yield TruthValidationResultRepo(session)


async def get_calibration_trigger_repo() -> AsyncGenerator[CalibrationTriggerRepo, None]:
    async with async_session_factory() as session:
        yield CalibrationTriggerRepo(session)


async def get_calibration_event_repo() -> AsyncGenerator[CalibrationEventRepo, None]:
    async with async_session_factory() as session:
        yield CalibrationEventRepo(session)


async def get_audit_entry_repo() -> AsyncGenerator[GovernanceAuditEntryRepo, None]:
    async with async_session_factory() as session:
        yield GovernanceAuditEntryRepo(session)


# ── Evaluation Layer ─────────────────────────────────────────────────────


async def get_expected_outcome_repo() -> AsyncGenerator[ExpectedOutcomeRepo, None]:
    async with async_session_factory() as session:
        yield ExpectedOutcomeRepo(session)


async def get_actual_outcome_repo() -> AsyncGenerator[ActualOutcomeRepo, None]:
    async with async_session_factory() as session:
        yield ActualOutcomeRepo(session)


async def get_evaluation_repo() -> AsyncGenerator[DecisionEvaluationRepo, None]:
    async with async_session_factory() as session:
        yield DecisionEvaluationRepo(session)


async def get_feedback_repo() -> AsyncGenerator[AnalystFeedbackRepo, None]:
    async with async_session_factory() as session:
        yield AnalystFeedbackRepo(session)


async def get_replay_run_repo() -> AsyncGenerator[ReplayRunRepo, None]:
    async with async_session_factory() as session:
        yield ReplayRunRepo(session)


async def get_replay_result_repo() -> AsyncGenerator[ReplayRunResultRepo, None]:
    async with async_session_factory() as session:
        yield ReplayRunResultRepo(session)


async def get_rule_performance_repo() -> AsyncGenerator[RulePerformanceRepo, None]:
    async with async_session_factory() as session:
        yield RulePerformanceRepo(session)


# ── Enforcement Layer ────────────────────────────────────────────────────


async def get_enforcement_policy_repo() -> AsyncGenerator[EnforcementPolicyRepo, None]:
    async with async_session_factory() as session:
        yield EnforcementPolicyRepo(session)


async def get_enforcement_decision_repo() -> AsyncGenerator[EnforcementDecisionRepo, None]:
    async with async_session_factory() as session:
        yield EnforcementDecisionRepo(session)


async def get_execution_gate_repo() -> AsyncGenerator[ExecutionGateResultRepo, None]:
    async with async_session_factory() as session:
        yield ExecutionGateResultRepo(session)


async def get_approval_request_repo() -> AsyncGenerator[ApprovalRequestRepo, None]:
    async with async_session_factory() as session:
        yield ApprovalRequestRepo(session)
