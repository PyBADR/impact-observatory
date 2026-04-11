"""Tests for the Outcome Tracking, Decision Evaluation & Replay Layer.

Covers:
  1. ORM model creation — all 7 table classes instantiate correctly
  2. Migration structure — 003 migration has correct up/down shape
  3. Repository CRUD — FakeAsyncSession stub for all 7 repos
  4. Deterministic scoring functions — severity, entity, timing, direction, correctness, explainability
  5. Replay execution — rule matching, scope checking, event flattening
  6. Expected vs Actual evaluation flow — end-to-end scoring
  7. Rule performance snapshot generation
  8. Pydantic schema validation — field constraints, enum validation
  9. API route smoke tests — FastAPI TestClient
"""

from __future__ import annotations

import importlib
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, List
from unittest.mock import MagicMock

import pytest


# ═════════════════════════════════════════════════════════════════════════════
# Helpers
# ═════════════════════════════════════════════════════════════════════════════

def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class FakeResult:
    """Mimics SQLAlchemy result proxy."""
    def __init__(self, values: list):
        self._values = values
        self._idx = 0

    def scalars(self):
        return self

    def all(self):
        return self._values

    def scalar_one_or_none(self):
        return self._values[0] if self._values else None

    def scalar_one(self):
        return self._values[0] if self._values else 0


class FakeAsyncSession:
    """Stub for AsyncSession that returns preset results."""
    def __init__(self):
        self._results: List[Any] = []
        self._added: List[Any] = []

    def push_result(self, values: list):
        self._results.append(FakeResult(values))

    def add(self, obj):
        self._added.append(obj)

    def add_all(self, objs):
        self._added.extend(objs)

    async def flush(self):
        pass

    async def execute(self, stmt):
        if self._results:
            return self._results.pop(0)
        return FakeResult([])

    async def merge(self, obj):
        return obj


# ═════════════════════════════════════════════════════════════════════════════
# 1. ORM MODEL CREATION
# ═════════════════════════════════════════════════════════════════════════════

class TestOrmModelCreation:
    """All 7 ORM models instantiate with correct fields."""

    def test_expected_outcome_orm(self):
        from src.data_foundation.models.outcome_tables import DecisionExpectedOutcomeORM
        orm = DecisionExpectedOutcomeORM(
            expected_outcome_id="EO-001",
            decision_log_id="DLOG-001",
            event_id="EVT-001",
            rule_id="RULE-001",
            expected_entities=["ent-1", "ent-2"],
            expected_severity="HIGH",
            expected_direction="DETERIORATE",
            expected_time_horizon_hours=48.0,
            expected_mitigation_effect=0.3,
            confidence_at_decision_time=0.75,
        )
        assert orm.expected_outcome_id == "EO-001"
        assert orm.expected_severity == "HIGH"
        assert orm.expected_direction == "DETERIORATE"
        assert orm.expected_entities == ["ent-1", "ent-2"]

    def test_actual_outcome_orm(self):
        from src.data_foundation.models.outcome_tables import DecisionActualOutcomeORM
        now = _utcnow()
        orm = DecisionActualOutcomeORM(
            actual_outcome_id="AO-001",
            expected_outcome_id="EO-001",
            observed_entities=["ent-1"],
            observed_severity="SEVERE",
            observed_direction="DETERIORATE",
            observed_time_to_materialization_hours=36.0,
            actual_effect_value=0.7,
            observation_source="market-data",
            observed_at=now,
        )
        assert orm.actual_outcome_id == "AO-001"
        assert orm.observed_severity == "SEVERE"

    def test_evaluation_orm(self):
        from src.data_foundation.models.outcome_tables import DecisionEvaluationORM
        orm = DecisionEvaluationORM(
            evaluation_id="EVAL-001",
            decision_log_id="DLOG-001",
            expected_outcome_id="EO-001",
            actual_outcome_id="AO-001",
            correctness_score=0.82,
            severity_alignment_score=0.8,
            entity_alignment_score=0.5,
            timing_alignment_score=1.0,
            confidence_gap=-0.07,
            explainability_completeness_score=0.65,
            evaluation_status="COMPLETED",
        )
        assert orm.correctness_score == 0.82
        assert orm.evaluation_status == "COMPLETED"

    def test_feedback_orm(self):
        from src.data_foundation.models.outcome_tables import AnalystFeedbackRecordORM
        orm = AnalystFeedbackRecordORM(
            feedback_id="FB-001",
            decision_log_id="DLOG-001",
            evaluation_id="EVAL-001",
            analyst_name="analyst-1",
            verdict="CORRECT",
            failure_mode=None,
        )
        assert orm.verdict == "CORRECT"
        assert orm.analyst_name == "analyst-1"

    def test_replay_run_orm(self):
        from src.data_foundation.models.outcome_tables import ReplayRunORM
        orm = ReplayRunORM(
            replay_run_id="REPLAY-001",
            source_event_id="EVT-001",
            replay_version=1,
            initiated_by="test-user",
            replay_status="COMPLETED",
        )
        assert orm.replay_run_id == "REPLAY-001"
        assert orm.replay_status == "COMPLETED"

    def test_replay_result_orm(self):
        from src.data_foundation.models.outcome_tables import ReplayRunResultORM
        orm = ReplayRunResultORM(
            replay_result_id="RR-001",
            replay_run_id="REPLAY-001",
            event_id="EVT-001",
            matched_rule_ids=["RULE-001", "RULE-002"],
            replayed_entities=["ent-1"],
            replayed_decisions=[{"rule_id": "RULE-001", "action": "ALERT"}],
            replayed_confidence_summary={"RULE-001": 0.8},
        )
        assert orm.matched_rule_ids == ["RULE-001", "RULE-002"]

    def test_rule_performance_snapshot_orm(self):
        from src.data_foundation.models.outcome_tables import RulePerformanceSnapshotORM
        orm = RulePerformanceSnapshotORM(
            snapshot_id="SNAP-001",
            rule_id="RULE-001",
            snapshot_date=_utcnow(),
            match_count=100,
            confirmed_correct_count=80,
            false_positive_count=10,
            false_negative_count=10,
            average_correctness_score=0.82,
            average_confidence_gap=-0.05,
        )
        assert orm.match_count == 100
        assert orm.average_correctness_score == 0.82


# ═════════════════════════════════════════════════════════════════════════════
# 2. MIGRATION STRUCTURE
# ═════════════════════════════════════════════════════════════════════════════

class TestMigrationStructure:
    """Migration 003 has correct shape."""

    def test_migration_imports(self):
        """Check migration file is valid Python with correct revision chain."""
        from pathlib import Path
        import ast
        path = Path(__file__).parent.parent / "alembic" / "versions" / "003_outcome_evaluation_replay_layer.py"
        content = path.read_text()
        # Parse as valid Python
        tree = ast.parse(content)
        # Extract revision assignments (annotated: `revision: str = "..."`)
        assignments = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                if node.target.id in ("revision", "down_revision"):
                    if isinstance(node.value, ast.Constant):
                        assignments[node.target.id] = node.value.value
        assert assignments["revision"] == "003_outcome_eval_replay"
        assert assignments["down_revision"] == "002_data_reality"

    def test_migration_has_all_tables(self):
        """Check that upgrade creates all 7 tables by inspecting source."""
        from pathlib import Path
        path = Path(__file__).parent.parent / "alembic" / "versions" / "003_outcome_evaluation_replay_layer.py"
        content = path.read_text()
        expected_tables = [
            "df_decision_expected_outcomes",
            "df_decision_actual_outcomes",
            "df_decision_evaluations",
            "df_analyst_feedback",
            "df_replay_runs",
            "df_replay_run_results",
            "df_rule_performance_snapshots",
        ]
        for table in expected_tables:
            assert table in content, f"Missing table: {table}"

    def test_downgrade_drops_all(self):
        from pathlib import Path
        path = Path(__file__).parent.parent / "alembic" / "versions" / "003_outcome_evaluation_replay_layer.py"
        content = path.read_text()
        # All 7 tables should appear in downgrade
        for table in [
            "df_decision_expected_outcomes",
            "df_decision_actual_outcomes",
            "df_decision_evaluations",
            "df_analyst_feedback",
            "df_replay_runs",
            "df_replay_run_results",
            "df_rule_performance_snapshots",
        ]:
            assert f'drop_table("{table}")' in content


# ═════════════════════════════════════════════════════════════════════════════
# 3. PYDANTIC SCHEMA VALIDATION
# ═════════════════════════════════════════════════════════════════════════════

class TestPydanticSchemas:
    """Schema field constraints and enum validation."""

    def test_expected_outcome_valid(self):
        from src.data_foundation.schemas.outcome_schemas import DecisionExpectedOutcome
        eo = DecisionExpectedOutcome(
            expected_outcome_id="EO-001",
            decision_log_id="DLOG-001",
            rule_id="RULE-001",
            expected_severity="HIGH",
            expected_direction="DETERIORATE",
            confidence_at_decision_time=0.8,
        )
        assert eo.expected_severity == "HIGH"

    def test_expected_outcome_invalid_severity(self):
        from src.data_foundation.schemas.outcome_schemas import DecisionExpectedOutcome
        with pytest.raises(Exception):
            DecisionExpectedOutcome(
                expected_outcome_id="EO-001",
                decision_log_id="DLOG-001",
                rule_id="RULE-001",
                expected_severity="INVALID",
                expected_direction="DETERIORATE",
            )

    def test_expected_outcome_invalid_direction(self):
        from src.data_foundation.schemas.outcome_schemas import DecisionExpectedOutcome
        with pytest.raises(Exception):
            DecisionExpectedOutcome(
                expected_outcome_id="EO-001",
                decision_log_id="DLOG-001",
                rule_id="RULE-001",
                expected_severity="HIGH",
                expected_direction="UNKNOWN",
            )

    def test_actual_outcome_valid(self):
        from src.data_foundation.schemas.outcome_schemas import DecisionActualOutcome
        ao = DecisionActualOutcome(
            actual_outcome_id="AO-001",
            expected_outcome_id="EO-001",
            observed_severity="SEVERE",
            observed_direction="IMPROVE",
            observed_at=_utcnow(),
        )
        assert ao.observed_direction == "IMPROVE"

    def test_actual_outcome_invalid_severity(self):
        from src.data_foundation.schemas.outcome_schemas import DecisionActualOutcome
        with pytest.raises(Exception):
            DecisionActualOutcome(
                actual_outcome_id="AO-001",
                expected_outcome_id="EO-001",
                observed_severity="MEGA_BAD",
                observed_direction="DETERIORATE",
                observed_at=_utcnow(),
            )

    def test_evaluation_valid(self):
        from src.data_foundation.schemas.outcome_schemas import DecisionEvaluation
        ev = DecisionEvaluation(
            evaluation_id="EVAL-001",
            decision_log_id="DLOG-001",
            expected_outcome_id="EO-001",
            actual_outcome_id="AO-001",
            correctness_score=0.85,
            severity_alignment_score=0.9,
            entity_alignment_score=0.7,
            timing_alignment_score=1.0,
            confidence_gap=-0.1,
            explainability_completeness_score=0.65,
            evaluation_status="COMPLETED",
            evaluated_at=_utcnow(),
        )
        assert ev.evaluation_status == "COMPLETED"

    def test_evaluation_invalid_status(self):
        from src.data_foundation.schemas.outcome_schemas import DecisionEvaluation
        with pytest.raises(Exception):
            DecisionEvaluation(
                evaluation_id="EVAL-001",
                decision_log_id="DLOG-001",
                expected_outcome_id="EO-001",
                actual_outcome_id="AO-001",
                correctness_score=0.85,
                severity_alignment_score=0.9,
                entity_alignment_score=0.7,
                timing_alignment_score=1.0,
                confidence_gap=-0.1,
                explainability_completeness_score=0.65,
                evaluation_status="INVALID_STATUS",
                evaluated_at=_utcnow(),
            )

    def test_feedback_valid_verdicts(self):
        from src.data_foundation.schemas.outcome_schemas import AnalystFeedbackRecord
        for verdict in ["CORRECT", "PARTIALLY_CORRECT", "INCORRECT", "INCONCLUSIVE"]:
            fb = AnalystFeedbackRecord(
                feedback_id="FB-001",
                decision_log_id="DLOG-001",
                analyst_name="analyst-1",
                verdict=verdict,
            )
            assert fb.verdict == verdict

    def test_feedback_invalid_verdict(self):
        from src.data_foundation.schemas.outcome_schemas import AnalystFeedbackRecord
        with pytest.raises(Exception):
            AnalystFeedbackRecord(
                feedback_id="FB-001",
                decision_log_id="DLOG-001",
                analyst_name="analyst-1",
                verdict="MAYBE",
            )

    def test_feedback_valid_failure_modes(self):
        from src.data_foundation.schemas.outcome_schemas import AnalystFeedbackRecord
        for mode in ["MISSED_SIGNAL", "WRONG_SEVERITY", "WRONG_ENTITY", "TIMING_OFF",
                      "RULE_GAP", "FALSE_POSITIVE", "OTHER"]:
            fb = AnalystFeedbackRecord(
                feedback_id="FB-001",
                decision_log_id="DLOG-001",
                analyst_name="analyst-1",
                verdict="INCORRECT",
                failure_mode=mode,
            )
            assert fb.failure_mode == mode

    def test_feedback_invalid_failure_mode(self):
        from src.data_foundation.schemas.outcome_schemas import AnalystFeedbackRecord
        with pytest.raises(Exception):
            AnalystFeedbackRecord(
                feedback_id="FB-001",
                decision_log_id="DLOG-001",
                analyst_name="analyst-1",
                verdict="INCORRECT",
                failure_mode="BAD_WEATHER",
            )

    def test_replay_run_valid_statuses(self):
        from src.data_foundation.schemas.outcome_schemas import ReplayRun
        for status in ["PENDING", "RUNNING", "COMPLETED", "FAILED"]:
            rr = ReplayRun(
                replay_run_id="REPLAY-001",
                source_event_id="EVT-001",
                initiated_by="test",
                started_at=_utcnow(),
                replay_status=status,
            )
            assert rr.replay_status == status

    def test_replay_run_invalid_status(self):
        from src.data_foundation.schemas.outcome_schemas import ReplayRun
        with pytest.raises(Exception):
            ReplayRun(
                replay_run_id="REPLAY-001",
                source_event_id="EVT-001",
                initiated_by="test",
                started_at=_utcnow(),
                replay_status="CANCELLED",
            )

    def test_performance_snapshot_valid(self):
        from src.data_foundation.schemas.outcome_schemas import RulePerformanceSnapshot
        snap = RulePerformanceSnapshot(
            snapshot_id="SNAP-001",
            rule_id="RULE-001",
            snapshot_date=_utcnow(),
            match_count=50,
            confirmed_correct_count=40,
            false_positive_count=5,
            false_negative_count=5,
            average_correctness_score=0.85,
            average_confidence_gap=-0.02,
        )
        assert snap.match_count == 50

    def test_request_schemas_validate(self):
        from src.data_foundation.schemas.outcome_schemas import (
            CreateExpectedOutcomeRequest,
            CreateActualOutcomeRequest,
            CreateFeedbackRequest,
            RunEvaluationRequest,
            RunReplayRequest,
            SnapshotRequest,
        )
        # Expected outcome request
        CreateExpectedOutcomeRequest(
            decision_log_id="DLOG-001",
            rule_id="RULE-001",
            expected_severity="HIGH",
            expected_direction="DETERIORATE",
        )
        # Actual outcome request
        CreateActualOutcomeRequest(
            expected_outcome_id="EO-001",
            observed_severity="HIGH",
            observed_direction="DETERIORATE",
            observed_at=_utcnow(),
        )
        # Feedback request
        CreateFeedbackRequest(
            decision_log_id="DLOG-001",
            analyst_name="analyst-1",
            verdict="CORRECT",
        )
        # Evaluation request
        RunEvaluationRequest(
            decision_log_id="DLOG-001",
            expected_outcome_id="EO-001",
            actual_outcome_id="AO-001",
        )
        # Replay request
        RunReplayRequest(
            source_event_id="EVT-001",
            initiated_by="test-user",
        )
        # Snapshot request
        SnapshotRequest(rule_id="RULE-001", snapshot_date=_utcnow())


# ═════════════════════════════════════════════════════════════════════════════
# 4. DETERMINISTIC SCORING FUNCTIONS
# ═════════════════════════════════════════════════════════════════════════════

class TestSeverityAlignment:
    """compute_severity_alignment — ordinal distance scoring."""

    def test_same_severity(self):
        from src.data_foundation.services.decision_evaluation_service import compute_severity_alignment
        assert compute_severity_alignment("HIGH", "HIGH") == 1.0

    def test_adjacent_severity(self):
        from src.data_foundation.services.decision_evaluation_service import compute_severity_alignment
        score = compute_severity_alignment("HIGH", "SEVERE")
        assert score == pytest.approx(0.8)

    def test_two_apart(self):
        from src.data_foundation.services.decision_evaluation_service import compute_severity_alignment
        score = compute_severity_alignment("HIGH", "ELEVATED")
        assert score == pytest.approx(0.8)

    def test_max_distance(self):
        from src.data_foundation.services.decision_evaluation_service import compute_severity_alignment
        score = compute_severity_alignment("NOMINAL", "SEVERE")
        assert score == pytest.approx(0.0)

    def test_symmetric(self):
        from src.data_foundation.services.decision_evaluation_service import compute_severity_alignment
        assert compute_severity_alignment("LOW", "HIGH") == compute_severity_alignment("HIGH", "LOW")

    def test_all_identical_scores_are_1(self):
        from src.data_foundation.services.decision_evaluation_service import compute_severity_alignment
        from src.data_foundation.schemas.outcome_schemas import VALID_SEVERITIES
        for sev in VALID_SEVERITIES:
            assert compute_severity_alignment(sev, sev) == 1.0


class TestEntityAlignment:
    """compute_entity_alignment — Jaccard similarity."""

    def test_identical_sets(self):
        from src.data_foundation.services.decision_evaluation_service import compute_entity_alignment
        assert compute_entity_alignment(["a", "b"], ["a", "b"]) == 1.0

    def test_disjoint_sets(self):
        from src.data_foundation.services.decision_evaluation_service import compute_entity_alignment
        assert compute_entity_alignment(["a", "b"], ["c", "d"]) == 0.0

    def test_partial_overlap(self):
        from src.data_foundation.services.decision_evaluation_service import compute_entity_alignment
        score = compute_entity_alignment(["a", "b", "c"], ["b", "c", "d"])
        # intersection = {b,c} = 2, union = {a,b,c,d} = 4 → 0.5
        assert score == pytest.approx(0.5)

    def test_empty_both(self):
        from src.data_foundation.services.decision_evaluation_service import compute_entity_alignment
        assert compute_entity_alignment([], []) == 1.0

    def test_one_empty(self):
        from src.data_foundation.services.decision_evaluation_service import compute_entity_alignment
        assert compute_entity_alignment(["a"], []) == 0.0
        assert compute_entity_alignment([], ["a"]) == 0.0

    def test_superset(self):
        from src.data_foundation.services.decision_evaluation_service import compute_entity_alignment
        score = compute_entity_alignment(["a", "b"], ["a", "b", "c"])
        # intersection = 2, union = 3 → 0.667
        assert score == pytest.approx(2 / 3, rel=1e-3)


class TestTimingAlignment:
    """compute_timing_alignment — ratio-based scoring."""

    def test_exact_match(self):
        from src.data_foundation.services.decision_evaluation_service import compute_timing_alignment
        assert compute_timing_alignment(48.0, 48.0) == 1.0

    def test_within_tolerance(self):
        from src.data_foundation.services.decision_evaluation_service import compute_timing_alignment
        # 2x ratio is boundary of full credit
        assert compute_timing_alignment(48.0, 96.0) == 1.0

    def test_beyond_max_tolerance(self):
        from src.data_foundation.services.decision_evaluation_service import compute_timing_alignment
        # 4x ratio = 0.0
        assert compute_timing_alignment(48.0, 192.0) == 0.0

    def test_partial_credit(self):
        from src.data_foundation.services.decision_evaluation_service import compute_timing_alignment
        # 3x → halfway between full and zero
        score = compute_timing_alignment(48.0, 144.0)
        assert 0.0 < score < 1.0

    def test_both_none(self):
        from src.data_foundation.services.decision_evaluation_service import compute_timing_alignment
        assert compute_timing_alignment(None, None) == 1.0

    def test_one_none(self):
        from src.data_foundation.services.decision_evaluation_service import compute_timing_alignment
        assert compute_timing_alignment(None, 48.0) == 0.5
        assert compute_timing_alignment(48.0, None) == 0.5

    def test_zero_expected(self):
        from src.data_foundation.services.decision_evaluation_service import compute_timing_alignment
        # If expected is 0, anything within 1 hour is full credit
        assert compute_timing_alignment(0.0, 0.5) == 1.0
        assert compute_timing_alignment(0.0, 5.0) == 0.0


class TestDirectionAlignment:
    """compute_direction_alignment — categorical match."""

    def test_same_direction(self):
        from src.data_foundation.services.decision_evaluation_service import compute_direction_alignment
        assert compute_direction_alignment("DETERIORATE", "DETERIORATE") == 1.0
        assert compute_direction_alignment("IMPROVE", "IMPROVE") == 1.0
        assert compute_direction_alignment("STABLE", "STABLE") == 1.0

    def test_opposite_direction(self):
        from src.data_foundation.services.decision_evaluation_service import compute_direction_alignment
        assert compute_direction_alignment("DETERIORATE", "IMPROVE") == 0.0
        assert compute_direction_alignment("IMPROVE", "DETERIORATE") == 0.0

    def test_stable_partial_credit(self):
        from src.data_foundation.services.decision_evaluation_service import compute_direction_alignment
        assert compute_direction_alignment("STABLE", "DETERIORATE") == 0.5
        assert compute_direction_alignment("IMPROVE", "STABLE") == 0.5


class TestCorrectnessScore:
    """compute_correctness — weighted combination."""

    def test_perfect_scores(self):
        from src.data_foundation.services.decision_evaluation_service import compute_correctness
        assert compute_correctness(1.0, 1.0, 1.0, 1.0) == 1.0

    def test_zero_scores(self):
        from src.data_foundation.services.decision_evaluation_service import compute_correctness
        assert compute_correctness(0.0, 0.0, 0.0, 0.0) == 0.0

    def test_weights_sum_to_one(self):
        from src.data_foundation.services.decision_evaluation_service import (
            WEIGHT_SEVERITY,
            WEIGHT_ENTITY,
            WEIGHT_TIMING,
            WEIGHT_DIRECTION,
        )
        assert WEIGHT_SEVERITY + WEIGHT_ENTITY + WEIGHT_TIMING + WEIGHT_DIRECTION == pytest.approx(1.0)

    def test_mixed_scores(self):
        from src.data_foundation.services.decision_evaluation_service import compute_correctness
        score = compute_correctness(0.8, 0.5, 1.0, 0.0)
        # 0.30*0.8 + 0.25*0.5 + 0.20*1.0 + 0.25*0.0 = 0.24+0.125+0.20+0.0 = 0.565
        assert score == pytest.approx(0.565)


class TestConfidenceGap:
    """compute_confidence_gap — simple difference."""

    def test_calibrated(self):
        from src.data_foundation.services.decision_evaluation_service import compute_confidence_gap
        assert compute_confidence_gap(0.8, 0.8) == 0.0

    def test_overconfident(self):
        from src.data_foundation.services.decision_evaluation_service import compute_confidence_gap
        gap = compute_confidence_gap(0.9, 0.5)
        assert gap == pytest.approx(0.4)

    def test_underconfident(self):
        from src.data_foundation.services.decision_evaluation_service import compute_confidence_gap
        gap = compute_confidence_gap(0.3, 0.8)
        assert gap == pytest.approx(-0.5)


class TestExplainabilityCompleteness:
    """compute_explainability_completeness — field presence scoring."""

    def test_none_log(self):
        from src.data_foundation.services.decision_evaluation_service import compute_explainability_completeness
        assert compute_explainability_completeness(None) == 0.0

    def test_empty_log(self):
        from src.data_foundation.services.decision_evaluation_service import compute_explainability_completeness
        assert compute_explainability_completeness({}) == 0.0

    def test_full_log(self):
        from src.data_foundation.services.decision_evaluation_service import compute_explainability_completeness
        log = {
            "rule_id": "RULE-001",
            "trigger_context": {"signal_ids": ["sig-1"]},
            "review_notes": "Looks correct",
            "entity_ids": ["ent-1"],
            "execution_result": {"status": "OK"},
        }
        assert compute_explainability_completeness(log) == pytest.approx(1.0)

    def test_partial_log(self):
        from src.data_foundation.services.decision_evaluation_service import compute_explainability_completeness
        log = {
            "rule_id": "RULE-001",
            "entity_ids": ["ent-1"],
        }
        score = compute_explainability_completeness(log)
        # matched_rules (0.25) + affected_entities (0.20) = 0.45
        assert score == pytest.approx(0.45)

    def test_explainability_weights_sum_to_one(self):
        from src.data_foundation.services.decision_evaluation_service import EXPLAINABILITY_FIELDS
        assert sum(EXPLAINABILITY_FIELDS.values()) == pytest.approx(1.0)


# ═════════════════════════════════════════════════════════════════════════════
# 5. FULL EVALUATION FLOW (evaluate_decision)
# ═════════════════════════════════════════════════════════════════════════════

class TestEvaluateDecision:
    """End-to-end evaluation using ORM-like objects."""

    def _make_expected(self, **kwargs):
        defaults = {
            "expected_outcome_id": "EO-001",
            "decision_log_id": "DLOG-001",
            "rule_id": "RULE-001",
            "expected_entities": ["ent-1", "ent-2"],
            "expected_severity": "HIGH",
            "expected_direction": "DETERIORATE",
            "expected_time_horizon_hours": 48.0,
            "expected_mitigation_effect": 0.3,
            "confidence_at_decision_time": 0.75,
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def _make_actual(self, **kwargs):
        defaults = {
            "actual_outcome_id": "AO-001",
            "expected_outcome_id": "EO-001",
            "observed_entities": ["ent-1", "ent-3"],
            "observed_severity": "HIGH",
            "observed_direction": "DETERIORATE",
            "observed_time_to_materialization_hours": 50.0,
            "actual_effect_value": 0.5,
            "observed_at": _utcnow(),
        }
        defaults.update(kwargs)
        return SimpleNamespace(**defaults)

    def test_perfect_prediction(self):
        from src.data_foundation.services.decision_evaluation_service import evaluate_decision
        expected = self._make_expected()
        actual = self._make_actual(
            observed_entities=["ent-1", "ent-2"],
            observed_severity="HIGH",
            observed_direction="DETERIORATE",
            observed_time_to_materialization_hours=48.0,
        )
        scores = evaluate_decision(expected, actual)
        assert scores.severity_alignment_score == 1.0
        assert scores.entity_alignment_score == 1.0
        assert scores.timing_alignment_score == 1.0
        assert scores.correctness_score == 1.0

    def test_partial_prediction(self):
        from src.data_foundation.services.decision_evaluation_service import evaluate_decision
        expected = self._make_expected()
        actual = self._make_actual()  # entity overlap: {ent-1}, severity same, timing close
        scores = evaluate_decision(expected, actual)
        assert 0.0 < scores.correctness_score < 1.0
        assert scores.severity_alignment_score == 1.0  # Same severity
        assert scores.entity_alignment_score < 1.0  # Partial overlap

    def test_wrong_direction_tanks_score(self):
        from src.data_foundation.services.decision_evaluation_service import evaluate_decision
        expected = self._make_expected(expected_direction="DETERIORATE")
        actual = self._make_actual(observed_direction="IMPROVE")
        scores = evaluate_decision(expected, actual)
        # Direction = 0.0, which is weighted at 0.25
        assert scores.correctness_score < 0.8

    def test_confidence_gap_computed(self):
        from src.data_foundation.services.decision_evaluation_service import evaluate_decision
        expected = self._make_expected(confidence_at_decision_time=0.9)
        actual = self._make_actual(
            observed_entities=["ent-1", "ent-2"],
            observed_severity="HIGH",
            observed_direction="DETERIORATE",
            observed_time_to_materialization_hours=48.0,
        )
        scores = evaluate_decision(expected, actual)
        # Perfect prediction → correctness = 1.0, confidence = 0.9 → gap = -0.1
        assert scores.confidence_gap == pytest.approx(-0.1, abs=0.01)


# ═════════════════════════════════════════════════════════════════════════════
# 6. REPLAY ENGINE — RULE MATCHING
# ═════════════════════════════════════════════════════════════════════════════

class TestReplayRuleMatching:
    """Rule matching functions used by the replay engine."""

    def test_evaluate_condition_gt(self):
        from src.data_foundation.services.replay_engine import _evaluate_condition
        assert _evaluate_condition({"field": "value", "operator": "gt", "threshold": 50}, {"value": 60}) is True
        assert _evaluate_condition({"field": "value", "operator": "gt", "threshold": 50}, {"value": 40}) is False

    def test_evaluate_condition_lt(self):
        from src.data_foundation.services.replay_engine import _evaluate_condition
        assert _evaluate_condition({"field": "value", "operator": "lt", "threshold": 50}, {"value": 40}) is True

    def test_evaluate_condition_eq(self):
        from src.data_foundation.services.replay_engine import _evaluate_condition
        assert _evaluate_condition({"field": "status", "operator": "eq", "threshold": "CLOSED"}, {"status": "CLOSED"}) is True

    def test_evaluate_condition_neq(self):
        from src.data_foundation.services.replay_engine import _evaluate_condition
        assert _evaluate_condition({"field": "status", "operator": "neq", "threshold": "OPERATIONAL"}, {"status": "CLOSED"}) is True

    def test_evaluate_condition_in(self):
        from src.data_foundation.services.replay_engine import _evaluate_condition
        assert _evaluate_condition(
            {"field": "country", "operator": "in", "threshold": ["KW", "SA", "AE"]},
            {"country": "KW"},
        ) is True

    def test_evaluate_condition_between(self):
        from src.data_foundation.services.replay_engine import _evaluate_condition
        assert _evaluate_condition(
            {"field": "value", "operator": "between", "threshold": [40, 60]},
            {"value": 50},
        ) is True
        assert _evaluate_condition(
            {"field": "value", "operator": "between", "threshold": [40, 60]},
            {"value": 70},
        ) is False

    def test_evaluate_condition_missing_field(self):
        from src.data_foundation.services.replay_engine import _evaluate_condition
        assert _evaluate_condition({"field": "missing", "operator": "gt", "threshold": 50}, {"value": 60}) is False

    def test_match_rule_and_logic(self):
        from src.data_foundation.services.replay_engine import match_rule_against_event
        rule = SimpleNamespace(
            conditions=[
                {"field": "severity_score", "operator": "gt", "threshold": 0.5},
                {"field": "category", "operator": "eq", "threshold": "ECONOMIC"},
            ],
            condition_logic="AND",
        )
        event = {"severity_score": 0.7, "category": "ECONOMIC"}
        assert match_rule_against_event(rule, event) is True

        event_fail = {"severity_score": 0.7, "category": "CYBER"}
        assert match_rule_against_event(rule, event_fail) is False

    def test_match_rule_or_logic(self):
        from src.data_foundation.services.replay_engine import match_rule_against_event
        rule = SimpleNamespace(
            conditions=[
                {"field": "severity_score", "operator": "gt", "threshold": 0.8},
                {"field": "category", "operator": "eq", "threshold": "ECONOMIC"},
            ],
            condition_logic="OR",
        )
        event = {"severity_score": 0.5, "category": "ECONOMIC"}
        assert match_rule_against_event(rule, event) is True

    def test_scope_check_country(self):
        from src.data_foundation.services.replay_engine import _check_scope
        rule = SimpleNamespace(
            applicable_countries=["KW", "SA"],
            applicable_sectors=None,
            applicable_scenarios=None,
        )
        event_match = {"countries_affected": ["KW", "AE"]}
        event_miss = {"countries_affected": ["AE", "QA"]}
        assert _check_scope(rule, event_match) is True
        assert _check_scope(rule, event_miss) is False

    def test_scope_check_no_constraints(self):
        from src.data_foundation.services.replay_engine import _check_scope
        rule = SimpleNamespace(
            applicable_countries=None,
            applicable_sectors=None,
            applicable_scenarios=None,
        )
        assert _check_scope(rule, {"countries_affected": ["KW"]}) is True

    def test_event_to_data(self):
        from src.data_foundation.services.replay_engine import _event_to_data
        event = SimpleNamespace(
            event_id="EVT-001",
            title="Test Event",
            category="ECONOMIC",
            severity="HIGH",
            severity_score=0.75,
            countries_affected=["KW"],
            sectors_affected=["banking"],
            entity_ids_affected=["ent-1"],
            scenario_ids=["saudi_oil_shock"],
            confidence_score=0.8,
            is_ongoing=False,
            raw_payload={"extra_field": 42},
        )
        data = _event_to_data(event)
        assert data["event_id"] == "EVT-001"
        assert data["severity_score"] == 0.75
        assert data["extra_field"] == 42
        assert data["countries_affected"] == ["KW"]


# ═════════════════════════════════════════════════════════════════════════════
# 7. REPOSITORY CRUD (via FakeAsyncSession)
# ═════════════════════════════════════════════════════════════════════════════

class TestRepositoryCrud:
    """Basic CRUD operations for all 7 repositories."""

    @pytest.mark.asyncio
    async def test_expected_outcome_repo_create(self):
        from src.data_foundation.repositories.expected_outcome_repo import ExpectedOutcomeRepository
        from src.data_foundation.models.outcome_tables import DecisionExpectedOutcomeORM
        session = FakeAsyncSession()
        repo = ExpectedOutcomeRepository(session)
        orm = DecisionExpectedOutcomeORM(
            expected_outcome_id="EO-001",
            decision_log_id="DLOG-001",
            rule_id="RULE-001",
            expected_severity="HIGH",
            expected_direction="DETERIORATE",
        )
        result = await repo.create(orm)
        assert result.expected_outcome_id == "EO-001"
        assert len(session._added) == 1

    @pytest.mark.asyncio
    async def test_actual_outcome_repo_create(self):
        from src.data_foundation.repositories.actual_outcome_repo import ActualOutcomeRepository
        from src.data_foundation.models.outcome_tables import DecisionActualOutcomeORM
        session = FakeAsyncSession()
        repo = ActualOutcomeRepository(session)
        orm = DecisionActualOutcomeORM(
            actual_outcome_id="AO-001",
            expected_outcome_id="EO-001",
            observed_severity="HIGH",
            observed_direction="DETERIORATE",
            observed_at=_utcnow(),
        )
        result = await repo.create(orm)
        assert result.actual_outcome_id == "AO-001"

    @pytest.mark.asyncio
    async def test_evaluation_repo_create(self):
        from src.data_foundation.repositories.evaluation_repo import EvaluationRepository
        from src.data_foundation.models.outcome_tables import DecisionEvaluationORM
        session = FakeAsyncSession()
        repo = EvaluationRepository(session)
        orm = DecisionEvaluationORM(
            evaluation_id="EVAL-001",
            decision_log_id="DLOG-001",
            expected_outcome_id="EO-001",
            actual_outcome_id="AO-001",
            correctness_score=0.8,
            severity_alignment_score=0.9,
            entity_alignment_score=0.7,
            timing_alignment_score=1.0,
            confidence_gap=-0.1,
            explainability_completeness_score=0.5,
        )
        result = await repo.create(orm)
        assert result.correctness_score == 0.8

    @pytest.mark.asyncio
    async def test_feedback_repo_create(self):
        from src.data_foundation.repositories.feedback_repo import FeedbackRepository
        from src.data_foundation.models.outcome_tables import AnalystFeedbackRecordORM
        session = FakeAsyncSession()
        repo = FeedbackRepository(session)
        orm = AnalystFeedbackRecordORM(
            feedback_id="FB-001",
            decision_log_id="DLOG-001",
            analyst_name="analyst-1",
            verdict="CORRECT",
        )
        result = await repo.create(orm)
        assert result.verdict == "CORRECT"

    @pytest.mark.asyncio
    async def test_replay_run_repo_create(self):
        from src.data_foundation.repositories.replay_run_repo import ReplayRunRepository
        from src.data_foundation.models.outcome_tables import ReplayRunORM
        session = FakeAsyncSession()
        repo = ReplayRunRepository(session)
        orm = ReplayRunORM(
            replay_run_id="REPLAY-001",
            source_event_id="EVT-001",
            initiated_by="test-user",
            replay_status="PENDING",
        )
        result = await repo.create(orm)
        assert result.replay_status == "PENDING"

    @pytest.mark.asyncio
    async def test_replay_result_repo_create(self):
        from src.data_foundation.repositories.replay_result_repo import ReplayResultRepository
        from src.data_foundation.models.outcome_tables import ReplayRunResultORM
        session = FakeAsyncSession()
        repo = ReplayResultRepository(session)
        orm = ReplayRunResultORM(
            replay_result_id="RR-001",
            replay_run_id="REPLAY-001",
            event_id="EVT-001",
            matched_rule_ids=["RULE-001"],
        )
        result = await repo.create(orm)
        assert result.matched_rule_ids == ["RULE-001"]

    @pytest.mark.asyncio
    async def test_rule_performance_repo_create(self):
        from src.data_foundation.repositories.rule_performance_repo import RulePerformanceRepository
        from src.data_foundation.models.outcome_tables import RulePerformanceSnapshotORM
        session = FakeAsyncSession()
        repo = RulePerformanceRepository(session)
        orm = RulePerformanceSnapshotORM(
            snapshot_id="SNAP-001",
            rule_id="RULE-001",
            snapshot_date=_utcnow(),
            match_count=50,
        )
        result = await repo.create(orm)
        assert result.match_count == 50

    @pytest.mark.asyncio
    async def test_expected_outcome_find_by_decision_log(self):
        from src.data_foundation.repositories.expected_outcome_repo import ExpectedOutcomeRepository
        from src.data_foundation.models.outcome_tables import DecisionExpectedOutcomeORM
        session = FakeAsyncSession()
        mock_result = DecisionExpectedOutcomeORM(
            expected_outcome_id="EO-002",
            decision_log_id="DLOG-002",
            rule_id="RULE-001",
            expected_severity="HIGH",
            expected_direction="DETERIORATE",
        )
        session.push_result([mock_result])
        repo = ExpectedOutcomeRepository(session)
        results = await repo.find_by_decision_log("DLOG-002")
        assert len(results) == 1
        assert results[0].expected_outcome_id == "EO-002"

    @pytest.mark.asyncio
    async def test_replay_run_get_latest_version(self):
        from src.data_foundation.repositories.replay_run_repo import ReplayRunRepository
        session = FakeAsyncSession()
        session.push_result([3])  # max version = 3
        repo = ReplayRunRepository(session)
        version = await repo.get_latest_version("EVT-001")
        assert version == 3

    @pytest.mark.asyncio
    async def test_replay_run_get_latest_version_no_runs(self):
        from src.data_foundation.repositories.replay_run_repo import ReplayRunRepository
        session = FakeAsyncSession()
        session.push_result([0])  # coalesce returns 0
        repo = ReplayRunRepository(session)
        version = await repo.get_latest_version("EVT-NEW")
        assert version == 0


# ═════════════════════════════════════════════════════════════════════════════
# 8. API ROUTE SMOKE TESTS
# ═════════════════════════════════════════════════════════════════════════════

class TestApiRoutes:
    """FastAPI route smoke tests using TestClient."""

    @pytest.fixture(autouse=True)
    def _setup_app(self):
        """Create a minimal FastAPI app with all 4 routers."""
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
        from src.data_foundation.api.outcomes import router as outcomes_router
        from src.data_foundation.api.evaluations import router as eval_router
        from src.data_foundation.api.feedback import router as feedback_router
        from src.data_foundation.api.replay import router as replay_router

        app = FastAPI()
        app.include_router(outcomes_router)
        app.include_router(eval_router)
        app.include_router(feedback_router)
        app.include_router(replay_router)
        self.client = TestClient(app)

    def test_create_expected_outcome(self):
        resp = self.client.post("/outcomes/expected", json={
            "decision_log_id": "DLOG-001",
            "rule_id": "RULE-001",
            "expected_severity": "HIGH",
            "expected_direction": "DETERIORATE",
            "confidence_at_decision_time": 0.8,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["expected_outcome_id"].startswith("EO-")
        assert data["expected_severity"] == "HIGH"

    def test_create_actual_outcome(self):
        resp = self.client.post("/outcomes/actual", json={
            "expected_outcome_id": "EO-test",
            "observed_severity": "SEVERE",
            "observed_direction": "DETERIORATE",
            "observed_at": _utcnow().isoformat(),
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["actual_outcome_id"].startswith("AO-")

    def test_run_evaluation(self):
        # First create expected and actual
        eo_resp = self.client.post("/outcomes/expected", json={
            "decision_log_id": "DLOG-EVAL",
            "rule_id": "RULE-001",
            "expected_severity": "HIGH",
            "expected_direction": "DETERIORATE",
            "expected_entities": ["ent-1"],
            "expected_time_horizon_hours": 48.0,
            "confidence_at_decision_time": 0.8,
        })
        eo_id = eo_resp.json()["expected_outcome_id"]

        ao_resp = self.client.post("/outcomes/actual", json={
            "expected_outcome_id": eo_id,
            "observed_severity": "HIGH",
            "observed_direction": "DETERIORATE",
            "observed_entities": ["ent-1"],
            "observed_time_to_materialization_hours": 50.0,
            "observed_at": _utcnow().isoformat(),
        })
        ao_id = ao_resp.json()["actual_outcome_id"]

        # Run evaluation
        eval_resp = self.client.post("/evaluations/run", json={
            "decision_log_id": "DLOG-EVAL",
            "expected_outcome_id": eo_id,
            "actual_outcome_id": ao_id,
        })
        assert eval_resp.status_code == 201
        data = eval_resp.json()
        assert data["evaluation_id"].startswith("EVAL-")
        assert data["evaluation_status"] == "COMPLETED"
        assert 0.0 <= data["correctness_score"] <= 1.0

    def test_get_evaluation(self):
        # Create one first
        eo_resp = self.client.post("/outcomes/expected", json={
            "decision_log_id": "DLOG-GET",
            "rule_id": "RULE-001",
            "expected_severity": "HIGH",
            "expected_direction": "DETERIORATE",
        })
        eo_id = eo_resp.json()["expected_outcome_id"]
        ao_resp = self.client.post("/outcomes/actual", json={
            "expected_outcome_id": eo_id,
            "observed_severity": "SEVERE",
            "observed_direction": "DETERIORATE",
            "observed_at": _utcnow().isoformat(),
        })
        ao_id = ao_resp.json()["actual_outcome_id"]
        eval_resp = self.client.post("/evaluations/run", json={
            "decision_log_id": "DLOG-GET",
            "expected_outcome_id": eo_id,
            "actual_outcome_id": ao_id,
        })
        eval_id = eval_resp.json()["evaluation_id"]

        # Now GET
        get_resp = self.client.get(f"/evaluations/{eval_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["evaluation_id"] == eval_id

    def test_get_evaluation_not_found(self):
        resp = self.client.get("/evaluations/EVAL-nonexistent")
        assert resp.status_code == 404

    def test_create_feedback(self):
        resp = self.client.post("/feedback", json={
            "decision_log_id": "DLOG-001",
            "analyst_name": "analyst-1",
            "verdict": "CORRECT",
            "feedback_notes": "Looks good.",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["feedback_id"].startswith("FB-")
        assert data["verdict"] == "CORRECT"

    def test_feedback_invalid_verdict(self):
        resp = self.client.post("/feedback", json={
            "decision_log_id": "DLOG-001",
            "analyst_name": "analyst-1",
            "verdict": "MAYBE",
        })
        assert resp.status_code == 422

    def test_run_replay(self):
        resp = self.client.post("/replay/run", json={
            "source_event_id": "EVT-001",
            "initiated_by": "test-user",
            "replay_reason": "Testing",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["replay_run"]["replay_run_id"].startswith("REPLAY-")
        assert data["replay_run"]["replay_status"] == "COMPLETED"
        assert len(data["results"]) == 1

    def test_get_replay(self):
        create_resp = self.client.post("/replay/run", json={
            "source_event_id": "EVT-002",
            "initiated_by": "test-user",
        })
        run_id = create_resp.json()["replay_run"]["replay_run_id"]

        get_resp = self.client.get(f"/replay/{run_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["replay_run"]["replay_run_id"] == run_id

    def test_get_replay_not_found(self):
        resp = self.client.get("/replay/REPLAY-nonexistent")
        assert resp.status_code == 404

    def test_evaluation_run_missing_expected(self):
        resp = self.client.post("/evaluations/run", json={
            "decision_log_id": "DLOG-001",
            "expected_outcome_id": "EO-nonexistent",
            "actual_outcome_id": "AO-nonexistent",
        })
        assert resp.status_code == 404


# ═════════════════════════════════════════════════════════════════════════════
# 9. PACKAGE IMPORTS
# ═════════════════════════════════════════════════════════════════════════════

class TestPackageImports:
    """All modules import without error."""

    def test_import_outcome_tables(self):
        import src.data_foundation.models.outcome_tables as m
        assert hasattr(m, "DecisionExpectedOutcomeORM")
        assert hasattr(m, "DecisionActualOutcomeORM")
        assert hasattr(m, "DecisionEvaluationORM")
        assert hasattr(m, "AnalystFeedbackRecordORM")
        assert hasattr(m, "ReplayRunORM")
        assert hasattr(m, "ReplayRunResultORM")
        assert hasattr(m, "RulePerformanceSnapshotORM")

    def test_import_outcome_schemas(self):
        import src.data_foundation.schemas.outcome_schemas as s
        assert hasattr(s, "DecisionExpectedOutcome")
        assert hasattr(s, "DecisionActualOutcome")
        assert hasattr(s, "DecisionEvaluation")
        assert hasattr(s, "AnalystFeedbackRecord")
        assert hasattr(s, "ReplayRun")
        assert hasattr(s, "ReplayRunResult")
        assert hasattr(s, "RulePerformanceSnapshot")
        assert hasattr(s, "EvaluationScores")
        assert hasattr(s, "ReplayReport")

    def test_import_repositories(self):
        from src.data_foundation.repositories.expected_outcome_repo import ExpectedOutcomeRepository
        from src.data_foundation.repositories.actual_outcome_repo import ActualOutcomeRepository
        from src.data_foundation.repositories.evaluation_repo import EvaluationRepository
        from src.data_foundation.repositories.feedback_repo import FeedbackRepository
        from src.data_foundation.repositories.replay_run_repo import ReplayRunRepository
        from src.data_foundation.repositories.replay_result_repo import ReplayResultRepository
        from src.data_foundation.repositories.rule_performance_repo import RulePerformanceRepository
        assert ExpectedOutcomeRepository.pk_field == "expected_outcome_id"
        assert ActualOutcomeRepository.pk_field == "actual_outcome_id"
        assert EvaluationRepository.pk_field == "evaluation_id"
        assert FeedbackRepository.pk_field == "feedback_id"
        assert ReplayRunRepository.pk_field == "replay_run_id"
        assert ReplayResultRepository.pk_field == "replay_result_id"
        assert RulePerformanceRepository.pk_field == "snapshot_id"

    def test_import_services(self):
        from src.data_foundation.services.outcome_tracking_service import OutcomeTrackingService
        from src.data_foundation.services.decision_evaluation_service import DecisionEvaluationService
        from src.data_foundation.services.replay_engine import ReplayEngine
        from src.data_foundation.services.rule_performance_service import RulePerformanceService
        assert callable(OutcomeTrackingService)
        assert callable(DecisionEvaluationService)
        assert callable(ReplayEngine)
        assert callable(RulePerformanceService)

    def test_import_api_routes(self):
        from src.data_foundation.api.outcomes import router as outcomes_router
        from src.data_foundation.api.evaluations import router as eval_router
        from src.data_foundation.api.feedback import router as feedback_router
        from src.data_foundation.api.replay import router as replay_router
        assert outcomes_router.prefix == "/outcomes"
        assert eval_router.prefix == "/evaluations"
        assert feedback_router.prefix == "/feedback"
        assert replay_router.prefix == "/replay"
