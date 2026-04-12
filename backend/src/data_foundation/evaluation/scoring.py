"""
Evaluation Layer — Deterministic Scoring Algorithms
=====================================================

All scoring functions are pure: (expected, actual) → score.
No DB access, no side effects, no ML.

Every score has an explicit formula documented in the docstring.
All scores are reproducible given the same inputs.

Scoring method version: 1.0.0
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from src.data_foundation.schemas.enums import RiskLevel, SignalSeverity

from .schemas import (
    ExpectedOutcome,
    ActualOutcome,
    DecisionEvaluation,
    SCORING_METHOD_VERSION,
)

__all__ = [
    "compute_severity_alignment",
    "compute_entity_alignment",
    "compute_sector_alignment",
    "compute_timing_alignment",
    "compute_correctness_score",
    "compute_confidence_gap",
    "compute_explainability_completeness",
    "evaluate_decision",
]


# ═══════════════════════════════════════════════════════════════════════════════
# Ordinal maps for severity and risk level
# ═══════════════════════════════════════════════════════════════════════════════

_SEVERITY_ORDINAL: Dict[str, int] = {
    SignalSeverity.NOMINAL.value: 0,
    SignalSeverity.LOW.value: 1,
    SignalSeverity.GUARDED.value: 2,
    SignalSeverity.ELEVATED.value: 3,
    SignalSeverity.HIGH.value: 4,
    SignalSeverity.SEVERE.value: 5,
}

_SEVERITY_MAX = 5  # max ordinal distance

_RISK_ORDINAL: Dict[str, int] = {
    RiskLevel.NOMINAL.value: 0,
    RiskLevel.LOW.value: 1,
    RiskLevel.GUARDED.value: 2,
    RiskLevel.ELEVATED.value: 3,
    RiskLevel.HIGH.value: 4,
    RiskLevel.SEVERE.value: 5,
    RiskLevel.CRITICAL.value: 6,
}


# ═══════════════════════════════════════════════════════════════════════════════
# Individual scoring functions
# ═══════════════════════════════════════════════════════════════════════════════


def _enum_val(v) -> str:
    """Extract string value from enum or pass through."""
    return v.value if hasattr(v, "value") else str(v)


def compute_severity_alignment(
    expected_severity: str,
    actual_severity: Optional[str],
) -> float:
    """Ordinal distance between severity levels.

    Formula: 1.0 - abs(ord(expected) - ord(actual)) / MAX_ORDINAL
    Range: [0.0, 1.0]
    If actual is None (not yet observed), returns 0.0.
    """
    if actual_severity is None:
        return 0.0

    exp_ord = _SEVERITY_ORDINAL.get(_enum_val(expected_severity), 0)
    act_ord = _SEVERITY_ORDINAL.get(_enum_val(actual_severity), 0)

    distance = abs(exp_ord - act_ord)
    return max(0.0, 1.0 - distance / _SEVERITY_MAX)


def _jaccard(set_a: Set[str], set_b: Set[str]) -> float:
    """Jaccard similarity index.

    |A ∩ B| / |A ∪ B|
    If both empty → 1.0 (nothing expected, nothing happened — correct).
    If one empty and other non-empty → 0.0.
    """
    if not set_a and not set_b:
        return 1.0
    union = set_a | set_b
    if not union:
        return 1.0
    intersection = set_a & set_b
    return len(intersection) / len(union)


def compute_entity_alignment(
    expected_entities: List[str],
    actual_entities: List[str],
) -> float:
    """Jaccard similarity over entity ID sets.

    Formula: |expected ∩ actual| / |expected ∪ actual|
    Range: [0.0, 1.0]
    """
    return _jaccard(set(expected_entities), set(actual_entities))


def compute_sector_alignment(
    expected_sectors: List[str],
    actual_sectors: List[str],
) -> float:
    """Jaccard similarity over sector sets.

    Formula: |expected ∩ actual| / |expected ∪ actual|
    Range: [0.0, 1.0]
    """
    return _jaccard(set(expected_sectors), set(actual_sectors))


def compute_timing_alignment(
    expected_hours: Optional[float],
    actual_hours: Optional[float],
) -> float:
    """Timing alignment between expected and actual resolution hours.

    Formula: max(0, 1.0 - |expected - actual| / expected)
    Range: [0.0, 1.0]

    Edge cases:
      - If expected is None or 0 → timing was not predicted → 1.0 (neutral)
      - If actual is None → not yet resolved → 0.0
    """
    if expected_hours is None or expected_hours <= 0:
        return 1.0  # timing not predicted — cannot penalize
    if actual_hours is None:
        return 0.0  # not yet resolved

    deviation = abs(expected_hours - actual_hours) / expected_hours
    return max(0.0, 1.0 - deviation)


def compute_correctness_score(
    severity_alignment: float,
    entity_alignment: float,
    timing_alignment: float,
    sector_alignment: float,
) -> float:
    """Weighted composite correctness score.

    Formula:
      0.35 * severity_alignment
    + 0.30 * entity_alignment
    + 0.20 * timing_alignment
    + 0.15 * sector_alignment

    Weights rationale:
      - Severity (35%): Most important — did we get the severity right?
      - Entity (30%): Who was affected matters for targeted response
      - Timing (20%): How fast it unfolded matters for preparedness
      - Sector (15%): Sector-level alignment is coarser, lower weight

    Range: [0.0, 1.0]
    """
    return (
        0.35 * severity_alignment
        + 0.30 * entity_alignment
        + 0.20 * timing_alignment
        + 0.15 * sector_alignment
    )


def compute_confidence_gap(
    rule_confidence: float,
    correctness_score: float,
) -> float:
    """Gap between rule's declared confidence and actual correctness.

    Formula: rule_confidence - correctness_score
    Range: [-1.0, +1.0]

    Interpretation:
      Positive → rule was overconfident
      Negative → rule was underconfident (conservative — less dangerous)
      Zero → perfectly calibrated
    """
    return max(-1.0, min(1.0, rule_confidence - correctness_score))


def compute_explainability_completeness(expected: ExpectedOutcome) -> float:
    """Ratio of non-null predictive fields in ExpectedOutcome.

    Measures how much the system actually predicted vs left blank.
    Higher = more complete explanation was provided at decision time.

    Counted fields (10 total):
      expected_severity, expected_risk_level, expected_affected_entity_ids,
      expected_affected_sectors, expected_affected_countries,
      expected_financial_impact, expected_mitigation_effect,
      expected_resolution_hours, data_state_snapshot, spec_id

    Range: [0.0, 1.0]
    """
    fields = [
        expected.expected_severity is not None,
        expected.expected_risk_level is not None,
        len(expected.expected_affected_entity_ids) > 0,
        len(expected.expected_affected_sectors) > 0,
        len(expected.expected_affected_countries) > 0,
        expected.expected_financial_impact is not None,
        expected.expected_mitigation_effect is not None,
        expected.expected_resolution_hours is not None,
        len(expected.data_state_snapshot) > 0,
        expected.spec_id is not None,
    ]
    return sum(fields) / len(fields)


# ═══════════════════════════════════════════════════════════════════════════════
# Composite evaluation function
# ═══════════════════════════════════════════════════════════════════════════════


def evaluate_decision(
    expected: ExpectedOutcome,
    actual: ActualOutcome,
    rule_confidence: float = 0.5,
) -> DecisionEvaluation:
    """Compare expected vs actual outcomes and produce a DecisionEvaluation.

    This is a pure function: (expected, actual, confidence) → evaluation.
    No DB access, no side effects.

    Args:
        expected: The prediction made at decision time.
        actual: The observed outcome.
        rule_confidence: The rule's declared confidence_score [0-1].

    Returns:
        DecisionEvaluation with all 6 scoring dimensions computed.
    """
    severity_score = compute_severity_alignment(
        _enum_val(expected.expected_severity),
        _enum_val(actual.actual_severity) if actual.actual_severity else None,
    )

    entity_score = compute_entity_alignment(
        expected.expected_affected_entity_ids,
        actual.actual_affected_entity_ids,
    )

    sector_score = compute_sector_alignment(
        expected.expected_affected_sectors,
        actual.actual_affected_sectors,
    )

    timing_score = compute_timing_alignment(
        expected.expected_resolution_hours,
        actual.actual_resolution_hours,
    )

    correctness = compute_correctness_score(
        severity_score, entity_score, timing_score, sector_score,
    )

    gap = compute_confidence_gap(rule_confidence, correctness)
    explainability = compute_explainability_completeness(expected)

    evaluation = DecisionEvaluation(
        expected_outcome_id=expected.expected_outcome_id,
        actual_outcome_id=actual.actual_outcome_id,
        decision_log_id=expected.decision_log_id,
        rule_id=expected.rule_id,
        spec_id=expected.spec_id,
        correctness_score=round(correctness, 6),
        severity_alignment_score=round(severity_score, 6),
        entity_alignment_score=round(entity_score, 6),
        timing_alignment_score=round(timing_score, 6),
        sector_alignment_score=round(sector_score, 6),
        confidence_gap=round(gap, 6),
        explainability_completeness_score=round(explainability, 6),
    )
    evaluation.compute_hash()
    return evaluation
