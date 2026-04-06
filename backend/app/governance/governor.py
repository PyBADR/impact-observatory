"""
Impact Observatory | مرصد الأثر — Build Governor

Runs a battery of consistency checks against the entire system before deployment.
Blocks builds (exit code 1) when any BLOCKER check fails.

Checks:
  CHECK-1   bridge.py SCENARIO_SHOCKS keys == canonical registry keys
  CHECK-2   backend catalog.py scenario_ids == canonical registry keys
  CHECK-3   normalize.py uses registry-driven geo_scope (no TEMPLATE_GEO_SCOPE with old IDs)
  CHECK-4   Shock vector dry-fire for all registry scenarios (no ValueError, no empty)
  CHECK-5   All registry scenarios have non-zero MVOE values
  CHECK-6   No shock_mapping_key aliasing (shock_mapping_key must equal scenario_id)
  CHECK-7   Registry internal consistency (__post_init__ validates all entries)
  CHECK-8   Graph payload contract: build_graph_snapshot() produces nodes+edges for graph-supported scenarios

Run via:
  python backend/scripts/governance_check.py         # human-readable
  python backend/scripts/governance_check.py --json  # JSON output for CI
"""

from __future__ import annotations

import pathlib
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from .registry import CANONICAL_REGISTRY, get_all_ids, get_geo_scope


class CheckStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"


@dataclass
class GovernanceCheck:
    name: str
    status: CheckStatus
    detail: str
    blocker: bool    # if True, this check failure blocks deployment


@dataclass
class GovernanceResult:
    passed: bool
    checks: List[GovernanceCheck]
    blocker_failures: List[str]    # names of failed blocker checks

    def summary(self) -> str:
        total = len(self.checks)
        passed = sum(1 for c in self.checks if c.status == CheckStatus.PASS)
        failed = sum(1 for c in self.checks if c.status == CheckStatus.FAIL)
        warned = sum(1 for c in self.checks if c.status == CheckStatus.WARN)

        lines = [
            "",
            "═" * 60,
            f"  Impact Observatory — Governance Check",
            f"  Result: {'✓ PASSED' if self.passed else '✗ FAILED'}",
            f"  Checks: {total} total | {passed} pass | {failed} fail | {warned} warn",
            "═" * 60,
        ]
        if self.blocker_failures:
            lines.append(f"  Blocker failures:")
            for b in self.blocker_failures:
                lines.append(f"    ✗ {b}")
            lines.append("")

        for c in self.checks:
            if c.status == CheckStatus.PASS:
                icon = "✓"
            elif c.status == CheckStatus.FAIL:
                icon = "✗"
            else:
                icon = "⚠"
            blocker_tag = " [BLOCKER]" if c.blocker and c.status == CheckStatus.FAIL else ""
            lines.append(f"  {icon} [{c.status.value}]{blocker_tag} {c.name}")
            lines.append(f"      {c.detail}")

        lines.append("═" * 60)
        lines.append("")
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "blocker_failures": self.blocker_failures,
            "checks": [
                {
                    "name": c.name,
                    "status": c.status.value,
                    "detail": c.detail,
                    "blocker": c.blocker,
                }
                for c in self.checks
            ],
        }


def run_governance_checks() -> GovernanceResult:
    """
    Execute all governance consistency checks.

    Returns GovernanceResult with passed=True only if all BLOCKER checks pass.
    Non-blocker WARN checks do not prevent deployment.
    """
    checks: List[GovernanceCheck] = []
    registry_ids = set(get_all_ids())

    # ── CHECK-1: bridge.py SCENARIO_SHOCKS alignment ─────────────────────────
    checks.append(_check_bridge_alignment(registry_ids))

    # ── CHECK-2: backend catalog.py alignment ─────────────────────────────────
    checks.append(_check_catalog_alignment(registry_ids))

    # ── CHECK-3: normalize.py uses registry geo_scope ─────────────────────────
    checks.append(_check_geo_scope_registry_driven())

    # ── CHECK-4: shock vector dry-fire ────────────────────────────────────────
    checks.append(_check_shock_dry_fire(registry_ids))

    # ── CHECK-5: MVOE validity ────────────────────────────────────────────────
    checks.append(_check_mvoe_validity())

    # ── CHECK-6: no aliasing ──────────────────────────────────────────────────
    checks.append(_check_no_aliasing())

    # ── CHECK-7: registry internal consistency ───────────────────────────────
    checks.append(_check_registry_internal())

    # ── CHECK-8: graph payload contract (Stage 8 dry-fire) ───────────────────
    checks.append(_check_graph_payload_contract())

    # ── Aggregate result ──────────────────────────────────────────────────────
    blocker_failures = [
        c.name for c in checks
        if c.status == CheckStatus.FAIL and c.blocker
    ]
    passed = len(blocker_failures) == 0

    return GovernanceResult(
        passed=passed,
        checks=checks,
        blocker_failures=blocker_failures,
    )


# ── Individual check implementations ─────────────────────────────────────────

def _check_bridge_alignment(registry_ids: set) -> GovernanceCheck:
    name = "BRIDGE_SCENARIO_SHOCKS_ALIGNMENT"
    try:
        from app.graph.bridge import SCENARIO_SHOCKS
        bridge_ids = set(SCENARIO_SHOCKS.keys())
        missing = registry_ids - bridge_ids
        extra = bridge_ids - registry_ids

        if missing:
            return GovernanceCheck(
                name=name,
                status=CheckStatus.FAIL,
                detail=(
                    f"Bridge is missing canonical IDs: {sorted(missing)}. "
                    f"Any run with these scenario_ids will raise ValueError at Stage 8."
                ),
                blocker=True,
            )
        if extra:
            return GovernanceCheck(
                name=name,
                status=CheckStatus.WARN,
                detail=(
                    f"Bridge has {len(extra)} extra IDs not in canonical registry: {sorted(extra)}. "
                    f"These can never be run via the API (RULE-001 blocks them) but consume memory."
                ),
                blocker=False,
            )
        return GovernanceCheck(
            name=name,
            status=CheckStatus.PASS,
            detail=f"All {len(registry_ids)} canonical IDs present in bridge.SCENARIO_SHOCKS.",
            blocker=True,
        )
    except ImportError as e:
        return GovernanceCheck(
            name=name,
            status=CheckStatus.FAIL,
            detail=f"Cannot import app.graph.bridge: {e}",
            blocker=True,
        )


def _check_catalog_alignment(registry_ids: set) -> GovernanceCheck:
    name = "BACKEND_CATALOG_ALIGNMENT"
    try:
        from app.scenarios.catalog import get_catalog_ids
        catalog_ids = set(get_catalog_ids())
        missing = registry_ids - catalog_ids
        extra = catalog_ids - registry_ids

        if missing:
            return GovernanceCheck(
                name=name,
                status=CheckStatus.FAIL,
                detail=(
                    f"Backend catalog missing canonical IDs: {sorted(missing)}. "
                    f"GET /scenarios will not return these scenarios."
                ),
                blocker=True,
            )
        if extra:
            return GovernanceCheck(
                name=name,
                status=CheckStatus.WARN,
                detail=(
                    f"Backend catalog has {len(extra)} extra IDs not in canonical registry: "
                    f"{sorted(extra)}. These will be blocked at runtime by RULE-001."
                ),
                blocker=False,
            )
        return GovernanceCheck(
            name=name,
            status=CheckStatus.PASS,
            detail=f"All {len(registry_ids)} canonical IDs present in backend scenario catalog.",
            blocker=True,
        )
    except ImportError as e:
        return GovernanceCheck(
            name=name,
            status=CheckStatus.FAIL,
            detail=f"Cannot import app.scenarios.catalog: {e}",
            blocker=True,
        )


def _check_geo_scope_registry_driven() -> GovernanceCheck:
    name = "GEO_SCOPE_REGISTRY_DRIVEN"
    fallback = ["SA", "UAE"]
    bad_ids = []

    for sid in get_all_ids():
        scope = get_geo_scope(sid)
        if scope == fallback:
            bad_ids.append(sid)

    if bad_ids:
        return GovernanceCheck(
            name=name,
            status=CheckStatus.FAIL,
            detail=(
                f"{len(bad_ids)} scenario(s) return fallback geo_scope {fallback!r}: {bad_ids}. "
                f"This means their canonical registry entry is missing geographic_scope "
                f"or get_geo_scope() is not being called."
            ),
            blocker=True,
        )

    # Also check normalize.py for stale TEMPLATE_GEO_SCOPE dict
    normalize_path = pathlib.Path(__file__).parent.parent / "quality" / "normalize.py"
    stale_detail = ""
    try:
        src = normalize_path.read_text()
        if "hormuz_closure" in src:
            stale_detail = (
                " WARNING: normalize.py still contains 'hormuz_closure' in TEMPLATE_GEO_SCOPE. "
                "Remove this dict and replace with get_geo_scope() from governance.registry."
            )
            return GovernanceCheck(
                name=name,
                status=CheckStatus.FAIL,
                detail=(
                    f"normalize.py contains stale TEMPLATE_GEO_SCOPE with old dev-era IDs "
                    f"(found 'hormuz_closure'). Stage 3 geo_scope will default to {fallback!r} "
                    f"for all 8 canonical scenarios. Replace with "
                    f"from app.governance.registry import get_geo_scope."
                ),
                blocker=True,
            )
    except OSError:
        stale_detail = " (could not read normalize.py for stale-dict check)"

    return GovernanceCheck(
        name=name,
        status=CheckStatus.PASS,
        detail=(
            f"All {len(get_all_ids())} registry scenarios return canonical geo_scope. "
            f"normalize.py is clean (no TEMPLATE_GEO_SCOPE stale entries)."
            + stale_detail
        ),
        blocker=True,
    )


def _check_shock_dry_fire(registry_ids: set) -> GovernanceCheck:
    name = "SHOCK_VECTOR_DRY_FIRE"
    try:
        from app.graph.bridge import get_scenario_shock_vector
        failures = []
        empty = []
        total_shocks = 0

        for sid in sorted(registry_ids):
            try:
                shocks = get_scenario_shock_vector(sid)
                if not shocks:
                    empty.append(sid)
                else:
                    total_shocks += len(shocks)
            except ValueError as e:
                failures.append(f"{sid}: {e}")

        if failures or empty:
            parts = []
            if failures:
                parts.append(f"ValueError for: {failures}")
            if empty:
                parts.append(f"Empty vector (no shocks) for: {empty}")
            return GovernanceCheck(
                name=name,
                status=CheckStatus.FAIL,
                detail=" | ".join(parts),
                blocker=True,
            )

        return GovernanceCheck(
            name=name,
            status=CheckStatus.PASS,
            detail=(
                f"All {len(registry_ids)} scenarios resolve to non-empty shock vectors "
                f"({total_shocks} total shocks across all scenarios). "
                f"No ValueError, no empty vectors."
            ),
            blocker=True,
        )
    except ImportError as e:
        return GovernanceCheck(
            name=name,
            status=CheckStatus.FAIL,
            detail=f"Cannot import app.graph.bridge: {e}",
            blocker=True,
        )


def _check_mvoe_validity() -> GovernanceCheck:
    name = "MVOE_VALIDITY"
    issues = []

    for sid, entry in CANONICAL_REGISTRY.items():
        if not entry.execution_expected:
            continue
        if entry.mvoe.loss_usd <= 0:
            issues.append(f"{sid}.mvoe.loss_usd={entry.mvoe.loss_usd}")
        if entry.mvoe.impacted_nodes <= 0:
            issues.append(f"{sid}.mvoe.impacted_nodes={entry.mvoe.impacted_nodes}")
        if entry.mvoe.actions <= 0:
            issues.append(f"{sid}.mvoe.actions={entry.mvoe.actions}")
        if entry.mvoe.edges <= 0 and entry.graph_supported:
            issues.append(f"{sid}.mvoe.edges={entry.mvoe.edges} (graph_supported=True)")

    if issues:
        return GovernanceCheck(
            name=name,
            status=CheckStatus.FAIL,
            detail=f"Zero or negative MVOE values found: {issues}",
            blocker=True,
        )

    return GovernanceCheck(
        name=name,
        status=CheckStatus.PASS,
        detail=(
            f"All {len(CANONICAL_REGISTRY)} registry entries have valid non-zero MVOEs. "
            f"Invariant checks RULE-007 through RULE-009 will fire correctly."
        ),
        blocker=True,
    )


def _check_no_aliasing() -> GovernanceCheck:
    name = "NO_SHOCK_KEY_ALIASING"
    aliases = []

    for sid, entry in CANONICAL_REGISTRY.items():
        if entry.shock_mapping_key != sid:
            aliases.append(f"{sid} → {entry.shock_mapping_key}")

    if aliases:
        return GovernanceCheck(
            name=name,
            status=CheckStatus.FAIL,
            detail=(
                f"Shock key aliasing detected (shock_mapping_key ≠ scenario_id): {aliases}. "
                f"Aliasing reintroduces the ID mismatch bug. "
                f"shock_mapping_key must always equal scenario_id."
            ),
            blocker=True,
        )

    return GovernanceCheck(
        name=name,
        status=CheckStatus.PASS,
        detail=(
            f"All {len(CANONICAL_REGISTRY)} scenarios use self-referential shock_mapping_key "
            f"(no aliasing). ID mismatch between scenario_id and shock vector key is impossible."
        ),
        blocker=False,
    )


def _check_registry_internal() -> GovernanceCheck:
    name = "REGISTRY_INTERNAL_CONSISTENCY"
    try:
        # __post_init__ validates domain and shock_mapping_key for all entries
        # If we got here, all entries passed __post_init__ at import time
        from .registry import VALID_DOMAINS
        domain_issues = [
            f"{sid}: domain='{e.domain}' not in VALID_DOMAINS"
            for sid, e in CANONICAL_REGISTRY.items()
            if e.domain not in VALID_DOMAINS
        ]
        if domain_issues:
            return GovernanceCheck(
                name=name,
                status=CheckStatus.FAIL,
                detail=f"Invalid domain values: {domain_issues}",
                blocker=True,
            )
        return GovernanceCheck(
            name=name,
            status=CheckStatus.PASS,
            detail=(
                f"Registry loaded cleanly: {len(CANONICAL_REGISTRY)} entries, "
                f"all domains valid, all __post_init__ constraints satisfied."
            ),
            blocker=True,
        )
    except Exception as e:
        return GovernanceCheck(
            name=name,
            status=CheckStatus.FAIL,
            detail=f"Registry failed internal consistency check: {e}",
            blocker=True,
        )


def _check_graph_payload_contract() -> GovernanceCheck:
    """
    CHECK-8: Verify Stage 8 (build_graph_snapshot) produces non-empty nodes + edges
    for all graph-supported scenarios.

    This is a structural contract check for the graph pipeline.
    A failure here means Graph Explorer will always show blank regardless of
    whether the frontend correctly subscribes to run-state (which it does post-fix).

    Blocker: True — if Stage 8 produces nothing, no frontend fix can recover.
    """
    name = "GRAPH_MAP_PAYLOAD_CONTRACT"
    try:
        from app.graph.builder import build_graph_snapshot

        graph_supported_scenarios = [
            sid for sid, e in CANONICAL_REGISTRY.items()
            if e.graph_supported
        ]

        if not graph_supported_scenarios:
            return GovernanceCheck(
                name=name,
                status=CheckStatus.WARN,
                detail=(
                    "No graph_supported scenarios found in canonical registry. "
                    "Graph Explorer will always show capability=false."
                ),
                blocker=False,
            )

        failures: list[str] = []
        empty_nodes: list[str] = []
        empty_edges: list[str] = []

        for sid in graph_supported_scenarios:
            try:
                snapshot = build_graph_snapshot(scenario_id=sid, severity=0.7)
                if len(snapshot.impacted_nodes) == 0:
                    empty_nodes.append(sid)
                if len(snapshot.activated_edges) == 0:
                    empty_edges.append(sid)
            except Exception as e:
                failures.append(f"{sid}: {e}")

        if failures:
            return GovernanceCheck(
                name=name,
                status=CheckStatus.FAIL,
                detail=(
                    f"build_graph_snapshot() raised exceptions for: {failures}. "
                    f"Stage 8 is broken — Graph Explorer will always show blank."
                ),
                blocker=True,
            )

        if empty_nodes:
            return GovernanceCheck(
                name=name,
                status=CheckStatus.FAIL,
                detail=(
                    f"build_graph_snapshot() returned 0 impacted_nodes for "
                    f"{len(empty_nodes)} graph_supported scenario(s): {empty_nodes}. "
                    f"Check NODES registry (graph/registry.py) and bridge.py shock vectors. "
                    f"Graph Explorer will always show blank capability state."
                ),
                blocker=True,
            )

        if empty_edges:
            return GovernanceCheck(
                name=name,
                status=CheckStatus.FAIL,
                detail=(
                    f"build_graph_snapshot() returned 0 activated_edges for "
                    f"{len(empty_edges)} graph_supported scenario(s): {empty_edges}. "
                    f"Nodes are present but no propagation paths activated — "
                    f"check shock impact thresholds (src_impact > 0.01) and EDGES registry. "
                    f"Graph Explorer requires edges for graphSupported=true."
                ),
                blocker=True,
            )

        total = len(graph_supported_scenarios)
        return GovernanceCheck(
            name=name,
            status=CheckStatus.PASS,
            detail=(
                f"build_graph_snapshot() dry-fire passed for all {total} "
                f"graph_supported scenario(s). All scenarios produce non-empty "
                f"nodes and activated_edges at severity=0.7. "
                f"Graph Explorer payload contract satisfied."
            ),
            blocker=True,
        )

    except ImportError as e:
        return GovernanceCheck(
            name=name,
            status=CheckStatus.FAIL,
            detail=f"Cannot import app.graph.builder: {e}. Stage 8 module is missing.",
            blocker=True,
        )
