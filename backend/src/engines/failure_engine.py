"""Failure & Fallback Framework — Phase 6, Stage 41.

Defines system behavior under failure conditions.
Every failure mode has an explicit fallback action.
No undefined behavior — every edge case is covered.

Failure modes are evaluated against pipeline outputs to determine
which (if any) apply, and what the safe fallback action is.
"""

from __future__ import annotations

from datetime import datetime, timezone

# ══════════════════════════════════════════════════════════════════════════════
# Failure mode definitions — static, auditable
# ══════════════════════════════════════════════════════════════════════════════

FAILURE_MODES: list[dict] = [
    {
        "id": "FM-001",
        "condition": "low_confidence",
        "description": "Model confidence below 0.60 — output unreliable",
        "fallback_action": "REQUIRE_MANUAL_APPROVAL",
        "severity": "HIGH",
    },
    {
        "id": "FM-002",
        "condition": "missing_data",
        "description": "Data completeness below 0.50 — insufficient signal",
        "fallback_action": "SWITCH_TO_ADVISORY",
        "severity": "HIGH",
    },
    {
        "id": "FM-003",
        "condition": "pipeline_timeout",
        "description": "Pipeline execution exceeded 30 seconds",
        "fallback_action": "USE_CACHED_RESULT",
        "severity": "MEDIUM",
    },
    {
        "id": "FM-004",
        "condition": "policy_conflict",
        "description": "Multiple policy rules in conflict — cannot auto-resolve",
        "fallback_action": "ESCALATE_TO_CRO",
        "severity": "HIGH",
    },
    {
        "id": "FM-005",
        "condition": "out_of_scope_scenario",
        "description": "Scenario is outside pilot scope boundaries",
        "fallback_action": "REJECT_AND_LOG",
        "severity": "LOW",
    },
    {
        "id": "FM-006",
        "condition": "shadow_divergence_extreme",
        "description": "System and human decisions diverge on >80% of actions",
        "fallback_action": "PAUSE_AND_REVIEW",
        "severity": "CRITICAL",
    },
    {
        "id": "FM-007",
        "condition": "value_negative",
        "description": "System decisions produce negative estimated value",
        "fallback_action": "SWITCH_TO_ADVISORY",
        "severity": "HIGH",
    },
    {
        "id": "FM-008",
        "condition": "no_actions_generated",
        "description": "Pipeline produced zero decision actions",
        "fallback_action": "REQUIRE_MANUAL_ASSESSMENT",
        "severity": "MEDIUM",
    },
]


def evaluate_failure_modes(
    *,
    confidence_score: float = 1.0,
    data_completeness: float = 1.0,
    duration_ms: int = 0,
    policy_evaluations: list[dict] | None = None,
    pilot_scope_result: dict | None = None,
    shadow_comparisons: list[dict] | None = None,
    portfolio_value: dict | None = None,
    actions: list[dict] | None = None,
) -> list[dict]:
    """Evaluate all failure modes against current pipeline state.

    Returns list of triggered failure modes with their fallback actions.
    Each entry includes: id, condition, triggered, fallback_action, detail.
    """
    triggered: list[dict] = []

    # FM-001: Low confidence
    if confidence_score < 0.60:
        triggered.append(_trigger("FM-001", f"Confidence {confidence_score:.2f} < 0.60"))

    # FM-002: Missing data
    if data_completeness < 0.50:
        triggered.append(_trigger("FM-002", f"Data completeness {data_completeness:.2f} < 0.50"))

    # FM-003: Pipeline timeout
    if duration_ms > 30_000:
        triggered.append(_trigger("FM-003", f"Duration {duration_ms}ms > 30,000ms"))

    # FM-004: Policy conflict
    if policy_evaluations:
        blocked = [p for p in policy_evaluations if not p.get("allowed", True)]
        conflicting = [
            p for p in blocked
            if len(p.get("required_approvals", [])) > 2
        ]
        if len(conflicting) > 1:
            triggered.append(_trigger("FM-004", f"{len(conflicting)} conflicting policy blocks"))

    # FM-005: Out of scope
    if pilot_scope_result and not pilot_scope_result.get("in_scope", True):
        triggered.append(_trigger("FM-005", pilot_scope_result.get("reason", "Out of scope")))

    # FM-006: Extreme shadow divergence
    if shadow_comparisons:
        n = len(shadow_comparisons)
        divergent = sum(1 for s in shadow_comparisons if s.get("divergence", False))
        if n > 0 and (divergent / n) > 0.80:
            triggered.append(_trigger("FM-006", f"{divergent}/{n} decisions diverged (>{80}%)"))

    # FM-007: Negative value
    if portfolio_value and portfolio_value.get("total_value_created", 0) < 0:
        val = portfolio_value["total_value_created"]
        triggered.append(_trigger("FM-007", f"Negative value created: ${val:,.0f}"))

    # FM-008: No actions
    if actions is not None and len(actions) == 0:
        triggered.append(_trigger("FM-008", "Zero actions generated"))

    return triggered


def get_all_failure_modes() -> list[dict]:
    """Return the complete failure mode catalog (for audit/documentation)."""
    return [
        {**fm, "evaluated_at": datetime.now(timezone.utc).isoformat()}
        for fm in FAILURE_MODES
    ]


def _trigger(fm_id: str, detail: str) -> dict:
    """Build a triggered failure mode record."""
    fm = next((f for f in FAILURE_MODES if f["id"] == fm_id), None)
    if not fm:
        return {
            "id": fm_id,
            "condition": "unknown",
            "triggered": True,
            "fallback_action": "ESCALATE_TO_CRO",
            "severity": "HIGH",
            "detail": detail,
            "evaluated_at": datetime.now(timezone.utc).isoformat(),
        }
    return {
        "id": fm["id"],
        "condition": fm["condition"],
        "description": fm["description"],
        "triggered": True,
        "fallback_action": fm["fallback_action"],
        "severity": fm["severity"],
        "detail": detail,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
    }
