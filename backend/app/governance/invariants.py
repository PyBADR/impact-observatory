"""
Impact Observatory | مرصد الأثر — Execution Invariants

Hard and soft validation rules applied to every run result.
A violation means the run either failed silently, produced wrong data,
or violated a structural contract.

Severity classification:
  HARD_FAIL            — execution cannot be considered valid; pipeline must not proceed
  SOFT_FAIL            — result is structurally present but below expected quality floor
  SILENT_FAILURE       — run reports success but all outputs are zero (worst class)
  UNSUPPORTED_CAPABILITY — capability was requested but not available in current deployment

Rules:
  RULE-001  No scenario may execute without a canonical registry entry
  RULE-002  No completed run may silently return zero total_loss_usd
  RULE-003  No completed run may silently return zero total_nodes_impacted
  RULE-004  No graph-supported scenario may complete with zero activated edges
  RULE-005  No executable scenario may bypass shock resolution (empty shock vector)
  RULE-006  Critical output fields (run_id, status, headline, scenario) must not be absent
  RULE-007  total_loss_usd must meet MVOE floor scaled by run_severity
  RULE-008  total_nodes_impacted must meet MVOE floor
  RULE-009  decision_inputs.actions must meet MVOE minimum count
  RULE-010  graph_payload.nodes must be non-empty when graph_supported=True
  RULE-011  map_payload.impacted_entities must be non-empty when map_supported=True
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional

from .registry import CANONICAL_REGISTRY, CanonicalScenario


# ── Severity taxonomy ─────────────────────────────────────────────────────────

class Severity(str, Enum):
    HARD_FAIL             = "HARD_FAIL"
    SOFT_FAIL             = "SOFT_FAIL"
    SILENT_FAILURE        = "SILENT_FAILURE"
    UNSUPPORTED_CAPABILITY = "UNSUPPORTED_CAPABILITY"


# ── Violation record ──────────────────────────────────────────────────────────

@dataclass
class InvariantViolation:
    rule_id: str           # e.g. "RULE-002"
    rule_name: str         # human-readable rule name
    severity: Severity
    field: str             # result field path that violated the rule
    expected: Any          # what was expected
    actual: Any            # what was found
    message: str           # full diagnostic message

    def to_dict(self) -> dict:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "severity": self.severity.value,
            "field": self.field,
            "expected": str(self.expected),
            "actual": str(self.actual),
            "message": self.message,
        }


# ── Invariant checker ─────────────────────────────────────────────────────────

def check_invariants(
    scenario_id: str,
    run_result: Dict[str, Any],
    run_severity: float = 0.7,
    shock_vector: Optional[List[dict]] = None,
) -> List[InvariantViolation]:
    """
    Apply all 9 invariant rules to a run result.

    Parameters
    ----------
    scenario_id : str
        The scenario_id that was run.
    run_result : dict
        The full UnifiedRunResult dict returned by run_unified_pipeline().
    run_severity : float
        The severity value used for this run (0.0–1.0). Used to scale MVOE thresholds.
    shock_vector : list[dict] | None
        If provided, used for RULE-005 shock vector presence check.
        If None, RULE-005 resolves the shock vector from bridge.py directly.

    Returns
    -------
    list[InvariantViolation]
        Empty list = all invariants satisfied.
        Non-empty = violations found, classified by severity.
    """
    violations: List[InvariantViolation] = []

    # ── RULE-001: canonical registry entry required ───────────────────────────
    entry: Optional[CanonicalScenario] = CANONICAL_REGISTRY.get(scenario_id)
    if entry is None:
        violations.append(InvariantViolation(
            rule_id="RULE-001",
            rule_name="CANONICAL_REGISTRY_ENTRY_REQUIRED",
            severity=Severity.HARD_FAIL,
            field="scenario_id",
            expected=f"one of {sorted(CANONICAL_REGISTRY.keys())}",
            actual=scenario_id,
            message=(
                f"scenario_id='{scenario_id}' has no canonical registry entry. "
                f"No run may execute without one. All scenario IDs must be registered in "
                f"backend/app/governance/registry.py before they can be executed."
            ),
        ))
        # Without a registry entry we have no MVOE or capability expectations —
        # all remaining rules require them, so return early.
        return violations

    # ── Extract run result fields once ───────────────────────────────────────
    status = run_result.get("status", "")
    headline = run_result.get("headline", {}) or {}
    total_loss = headline.get("total_loss_usd") or 0
    total_nodes = headline.get("total_nodes_impacted") or 0

    graph_payload = run_result.get("graph_payload", {}) or {}
    edges = graph_payload.get("edges") or []

    decision_inputs = run_result.get("decision_inputs", {}) or {}
    actions = decision_inputs.get("actions") or []

    is_completed = status == "completed"
    is_exec_expected = entry.execution_expected

    # ── RULE-002: zero loss on completed run ──────────────────────────────────
    if is_completed and is_exec_expected and total_loss == 0:
        violations.append(InvariantViolation(
            rule_id="RULE-002",
            rule_name="ZERO_LOSS_ON_COMPLETED_RUN",
            severity=Severity.SILENT_FAILURE,
            field="headline.total_loss_usd",
            expected="> 0 (execution_expected=True)",
            actual=0,
            message=(
                f"Run status='completed' but total_loss_usd=0. "
                f"Scenario '{scenario_id}' is execution_expected=True — "
                f"a zero-loss result on a completed run is a silent failure. "
                f"Root cause: shock vector empty, all node weights zero, or pipeline "
                f"skipped Stage 8."
            ),
        ))

    # ── RULE-003: zero nodes on completed run ────────────────────────────────
    if is_completed and is_exec_expected and total_nodes == 0:
        violations.append(InvariantViolation(
            rule_id="RULE-003",
            rule_name="ZERO_NODES_ON_COMPLETED_RUN",
            severity=Severity.SILENT_FAILURE,
            field="headline.total_nodes_impacted",
            expected=f">= {entry.mvoe.impacted_nodes} (MVOE at severity=1.0)",
            actual=0,
            message=(
                f"Run status='completed' but total_nodes_impacted=0. "
                f"Stage 8 graph build produced no impacted nodes. "
                f"This means apply_scenario_shocks() returned an empty map or "
                f"BFS propagation found no reachable nodes."
            ),
        ))

    # ── RULE-004: graph-supported scenario must have edges ────────────────────
    if entry.graph_supported and is_completed and len(edges) == 0:
        violations.append(InvariantViolation(
            rule_id="RULE-004",
            rule_name="GRAPH_SUPPORTED_BUT_NO_EDGES",
            severity=Severity.SILENT_FAILURE,
            field="graph_payload.edges",
            expected=f">= {entry.mvoe.edges} edges (MVOE at severity=1.0)",
            actual=0,
            message=(
                f"Scenario '{scenario_id}' declares graph_supported=True "
                f"but graph_payload.edges=[] on a completed run. "
                f"Graph Explorer will render an empty canvas. "
                f"The graph build (Stage 8) produced activated edges only when "
                f"source nodes have impact > 0.01 — check shock resolution."
            ),
        ))

    # ── RULE-005: shock vector must not be empty ──────────────────────────────
    if is_exec_expected:
        # If shock_vector not passed in, resolve from bridge directly
        resolved_sv = shock_vector
        if resolved_sv is None:
            try:
                from app.graph.bridge import get_scenario_shock_vector
                resolved_sv = get_scenario_shock_vector(scenario_id)
            except (ValueError, ImportError):
                resolved_sv = []

        if resolved_sv is not None and len(resolved_sv) == 0:
            violations.append(InvariantViolation(
                rule_id="RULE-005",
                rule_name="SHOCK_VECTOR_EMPTY",
                severity=Severity.HARD_FAIL,
                field="shock_vector",
                expected=f">= 1 shock entry for scenario '{scenario_id}'",
                actual=0,
                message=(
                    f"Shock vector for scenario_id='{scenario_id}' resolved to empty list. "
                    f"This guarantees zero nodes impacted and zero loss regardless of severity. "
                    f"Check bridge.py SCENARIO_SHOCKS — key must exactly match scenario_id."
                ),
            ))

    # ── RULE-006: critical output fields must not be absent ──────────────────
    required: Dict[str, Any] = {
        "run_id": run_result.get("run_id"),
        "status": run_result.get("status"),
        "headline": run_result.get("headline"),
        "scenario": run_result.get("scenario"),
    }
    for fname, fval in required.items():
        absent = fval is None or fval == "" or fval == {}
        if absent:
            violations.append(InvariantViolation(
                rule_id="RULE-006",
                rule_name="REQUIRED_FIELD_ABSENT",
                severity=Severity.SOFT_FAIL,
                field=fname,
                expected="non-null, non-empty value",
                actual=repr(fval),
                message=(
                    f"Required field '{fname}' is absent or empty in run result. "
                    f"The pipeline or adapter dropped this field. "
                    f"Frontend adapter will fail or produce null-safe fallbacks."
                ),
            ))

    # ── RULE-007: total_loss_usd must meet MVOE scaled by severity ────────────
    effective_min_loss = entry.mvoe.loss_usd * run_severity
    if (is_completed and is_exec_expected
            and total_loss > 0  # only fire if not already caught by RULE-002
            and total_loss < effective_min_loss):
        violations.append(InvariantViolation(
            rule_id="RULE-007",
            rule_name="LOSS_BELOW_MVOE",
            severity=Severity.SOFT_FAIL,
            field="headline.total_loss_usd",
            expected=f">= ${effective_min_loss:,.0f} (MVOE ${entry.mvoe.loss_usd:,.0f} × severity {run_severity})",
            actual=f"${total_loss:,.0f}",
            message=(
                f"total_loss_usd ${total_loss:,.0f} is below the minimum viable output "
                f"expectation of ${effective_min_loss:,.0f} "
                f"(registry MVOE ${entry.mvoe.loss_usd:,.0f} scaled by severity={run_severity}). "
                f"Check node weight calibration or shock magnitude in bridge.py."
            ),
        ))

    # ── RULE-008: total_nodes_impacted must meet MVOE ─────────────────────────
    # BFS propagation reaches roughly the same node count at any non-zero severity,
    # so this check is NOT scaled by severity — it uses the raw MVOE value.
    min_nodes = entry.mvoe.impacted_nodes
    if (is_completed and is_exec_expected
            and total_nodes > 0  # only fire if not already caught by RULE-003
            and total_nodes < min_nodes):
        violations.append(InvariantViolation(
            rule_id="RULE-008",
            rule_name="NODES_BELOW_MVOE",
            severity=Severity.SOFT_FAIL,
            field="headline.total_nodes_impacted",
            expected=f">= {min_nodes} (MVOE, severity-independent)",
            actual=total_nodes,
            message=(
                f"total_nodes_impacted={total_nodes} is below registry MVOE of {min_nodes}. "
                f"BFS propagation depth=3 should reach {min_nodes}+ nodes for this scenario "
                f"at any non-zero severity. Check registry, traversal depth, or node connectivity."
            ),
        ))

    # ── RULE-009: decision actions must meet MVOE ─────────────────────────────
    min_actions = entry.mvoe.actions
    if is_completed and is_exec_expected and len(actions) < min_actions:
        violations.append(InvariantViolation(
            rule_id="RULE-009",
            rule_name="NO_DECISION_ACTIONS",
            severity=Severity.SOFT_FAIL,
            field="decision_inputs.actions",
            expected=f">= {min_actions} action(s) (MVOE)",
            actual=len(actions),
            message=(
                f"Completed run produced {len(actions)} decision action(s), "
                f"below MVOE minimum of {min_actions}. "
                f"Stage 11 decision engine may have failed, returned empty, or "
                f"received an empty sector_rollup. Check _compute_decision_inputs()."
            ),
        ))

    # ── RULE-010: graph_payload.nodes absent when graph_supported ─────────────
    # Detects: Stage 8 builder returned 0 impacted nodes; or v2 backend deployment
    # (no graph pipeline); or graph/registry.py NODES list is empty.
    # Consequence: Graph Explorer will show blank capability state regardless of
    # whether the scenario itself completed successfully.
    graph_nodes = graph_payload.get("nodes") or []
    if entry.graph_supported and is_completed and len(graph_nodes) == 0:
        violations.append(InvariantViolation(
            rule_id="RULE-010",
            rule_name="GRAPH_PAYLOAD_NODES_ABSENT",
            severity=Severity.SOFT_FAIL,
            field="graph_payload.nodes",
            expected=">= 1 node (scenario is graph_supported=True)",
            actual=0,
            message=(
                f"Scenario '{scenario_id}' is graph_supported=True but graph_payload.nodes "
                f"is empty on a completed run. Graph Explorer will show a blank capability state. "
                f"Root cause: Stage 8 build_graph_snapshot() produced no impacted_nodes, "
                f"the deployed backend is v2 (no graph pipeline), or "
                f"GET /api/v1/graph/nodes is unreachable. "
                f"Frontend fallback (run-state hydration) will activate if graph_payload "
                f"is populated upstream. Check build_graph_snapshot() call in runner Stage 8."
            ),
        ))

    # ── RULE-011: map_payload.impacted_entities absent when map_supported ─────
    # Detects: map stage missing or failing silently; v2 backend (no map pipeline).
    # Consequence: Impact Map page will initialize with mapSupported=false and
    # show empty capability state. Frontend fallback subscribes to run-state but
    # cannot synthesize entities from absent data.
    map_payload_inner = run_result.get("map_payload", {}) or {}
    map_entities = map_payload_inner.get("impacted_entities") or []
    if entry.map_supported and is_completed and len(map_entities) == 0:
        violations.append(InvariantViolation(
            rule_id="RULE-011",
            rule_name="MAP_PAYLOAD_ENTITIES_ABSENT",
            severity=Severity.SOFT_FAIL,
            field="map_payload.impacted_entities",
            expected=">= 1 entity (scenario is map_supported=True)",
            actual=0,
            message=(
                f"Scenario '{scenario_id}' is map_supported=True but map_payload.impacted_entities "
                f"is empty on a completed run. Impact Map will show an empty capability state. "
                f"Root cause: map generation stage is not implemented in current deployment "
                f"(v2 backend), or the map stage failed silently. "
                f"Impact Map requires impacted_entities with lat/lng coordinates to render."
            ),
        ))

    return violations
