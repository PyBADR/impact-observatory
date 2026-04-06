"""
Impact Observatory | مرصد الأثر — Failure Clustering

Algorithmic clustering of run failures by root cause.

Architecture decision: DETERMINISTIC FIRST, JACCARD SECOND, NO DEEP LEARNING.

Rationale:
  - Feature space: 9 binary invariant rule violations + 5 output flags
  - Total distinct failure signatures: 2^14 = 16,384 theoretical max
  - In practice, observed failure patterns are highly structured and map
    cleanly to known root causes (ID mismatch, empty shock vector, etc.)
  - Deterministic clustering handles all known failure classes with 100% precision
    and is fully auditable — no probability estimates, no training data required
  - Jaccard similarity clustering is added for incident aggregation across
    multiple run logs, not for individual run classification
  - Deep learning would add zero signal here: the feature space is too small,
    the labels are known, and the cost of misclassification is high

Cluster taxonomy (deterministic, ordered by severity):
  SCENARIO_ID_MISMATCH       RULE-001: unknown scenario_id at pipeline entry
  SHOCK_RESOLUTION_FAILURE   RULE-005: shock vector empty after bridge lookup
  SILENT_ZERO_COMPLETION     RULE-002 + RULE-003: completed but all zeros
  MISSING_GRAPH_CAPABILITY   RULE-004: graph_supported=True but edges=[]
  CONTRACT_MISMATCH          RULE-006: required fields absent in result
  MVOE_UNDERPERFORMANCE      RULE-007/008/009: below minimum thresholds
  GRAPH_PAYLOAD_MISSING      RULE-010: graph_payload.nodes empty (graph_supported=True)
  MAP_PAYLOAD_MISSING        RULE-011: map_payload.impacted_entities empty (map_supported=True)
  RENDERING_ONLY             No pipeline violations — symptom is UI/adapter only
  CLEAN                      No violations at all
  UNCLASSIFIED               Violations present but no cluster matched
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Set, Tuple


# ── Cluster labels ────────────────────────────────────────────────────────────

class FailureCluster(str, Enum):
    SCENARIO_ID_MISMATCH      = "SCENARIO_ID_MISMATCH"
    SHOCK_RESOLUTION_FAILURE  = "SHOCK_RESOLUTION_FAILURE"
    SILENT_ZERO_COMPLETION    = "SILENT_ZERO_COMPLETION"
    MISSING_GRAPH_CAPABILITY  = "MISSING_GRAPH_CAPABILITY"
    CONTRACT_MISMATCH         = "CONTRACT_MISMATCH"
    MVOE_UNDERPERFORMANCE     = "MVOE_UNDERPERFORMANCE"
    GRAPH_PAYLOAD_MISSING     = "GRAPH_PAYLOAD_MISSING"
    MAP_PAYLOAD_MISSING       = "MAP_PAYLOAD_MISSING"
    RENDERING_ONLY            = "RENDERING_ONLY"
    CLEAN                     = "CLEAN"
    UNCLASSIFIED              = "UNCLASSIFIED"


@dataclass
class ClusterResult:
    primary_cluster: FailureCluster
    secondary_clusters: List[FailureCluster]
    confidence: float          # 1.0 for deterministic; Jaccard-based for unsupervised
    matched_rules: List[str]   # rule_ids that triggered this cluster assignment
    method: str                # "deterministic" | "jaccard"


# ── Deterministic clustering ──────────────────────────────────────────────────

def deterministic_cluster(
    violation_rule_ids: Set[str],
    status: str,
    total_loss: float,
    total_nodes: int,
    total_actions: int,
    total_edges: int,
) -> ClusterResult:
    """
    Assign failure cluster(s) from a set of violated rule IDs and output metrics.

    Rules are evaluated in priority order — HARD_FAIL clusters first, then
    SILENT_FAILURE, then SOFT_FAIL, then clean states. First match is primary;
    remaining matches become secondary clusters.

    Confidence is always 1.0 (deterministic). There is no ambiguity: a run
    either violated RULE-001 or it didn't.
    """
    matched: List[Tuple[FailureCluster, List[str]]] = []

    # ── Priority 1: Identity failures (HARD_FAIL) ─────────────────────────────
    if "RULE-001" in violation_rule_ids:
        matched.append((FailureCluster.SCENARIO_ID_MISMATCH, ["RULE-001"]))

    if "RULE-005" in violation_rule_ids:
        matched.append((FailureCluster.SHOCK_RESOLUTION_FAILURE, ["RULE-005"]))

    # ── Priority 2: Silent zero completion ───────────────────────────────────
    silent_rules = {"RULE-002", "RULE-003"} & violation_rule_ids
    if status == "completed" and total_loss == 0 and total_nodes == 0:
        matched.append((FailureCluster.SILENT_ZERO_COMPLETION, sorted(silent_rules)))

    # ── Priority 3: Graph capability failure ─────────────────────────────────
    if "RULE-004" in violation_rule_ids:
        matched.append((FailureCluster.MISSING_GRAPH_CAPABILITY, ["RULE-004"]))

    # ── Priority 4: Contract / structural failure ─────────────────────────────
    if "RULE-006" in violation_rule_ids:
        matched.append((FailureCluster.CONTRACT_MISMATCH, ["RULE-006"]))

    # ── Priority 5: MVOE underperformance ────────────────────────────────────
    mvoe_rules = {"RULE-007", "RULE-008", "RULE-009"} & violation_rule_ids
    # Only fire if not already a full silent-zero (otherwise MVOE is redundant)
    if mvoe_rules and not silent_rules:
        matched.append((FailureCluster.MVOE_UNDERPERFORMANCE, sorted(mvoe_rules)))

    # ── Priority 6: Graph/map payload missing (cross-page sync failures) ──────
    # Fired when graph_supported=True but graph_payload.nodes is empty (RULE-010),
    # or map_supported=True but map_payload.impacted_entities is empty (RULE-011).
    # These indicate the backend pipeline built the sector result correctly but
    # did not produce graph or map payloads — causing blank pages in the frontend.
    if "RULE-010" in violation_rule_ids:
        matched.append((FailureCluster.GRAPH_PAYLOAD_MISSING, ["RULE-010"]))

    if "RULE-011" in violation_rule_ids:
        matched.append((FailureCluster.MAP_PAYLOAD_MISSING, ["RULE-011"]))

    # ── Priority 7: Clean states ──────────────────────────────────────────────
    if not violation_rule_ids:
        if status == "completed" and total_loss > 0 and total_nodes > 0:
            matched.append((FailureCluster.CLEAN, []))
        else:
            # No violations but output is empty — could be a not-yet-completed run
            matched.append((FailureCluster.RENDERING_ONLY, []))

    # ── Fallback ──────────────────────────────────────────────────────────────
    if not matched:
        matched.append((FailureCluster.UNCLASSIFIED, sorted(violation_rule_ids)))

    primary_cluster, primary_rules = matched[0]
    secondary = [c for c, _ in matched[1:]]

    return ClusterResult(
        primary_cluster=primary_cluster,
        secondary_clusters=secondary,
        confidence=1.0,
        matched_rules=primary_rules,
        method="deterministic",
    )


# ── Jaccard-based incident aggregation ────────────────────────────────────────
#
# Purpose: aggregate multiple run failures into recurring pattern groups.
# Use case: production log analysis after 50+ runs to discover systemic issues.
# Algorithm: greedy single-linkage agglomerative clustering on violation fingerprints.
# Complexity: O(n²) — appropriate; n is bounded by log volume.
# Dependencies: none (pure stdlib).

@dataclass
class IncidentSignature:
    """Minimal run incident record for Jaccard clustering."""
    run_id: str
    scenario_id: str
    violation_fingerprint: FrozenSet[str]   # frozenset of violated rule_ids
    # Optional output signature (zero/nonzero flags) for richer similarity
    output_flags: FrozenSet[str] = field(default_factory=frozenset)

    @classmethod
    def from_audit(cls, audit_dict: dict) -> "IncidentSignature":
        """Construct from a RunAudit.to_dict() output."""
        violations = audit_dict.get("invariant_violations", [])
        rule_ids = frozenset(v.get("rule_id", "") for v in violations)

        flags = set()
        if not audit_dict.get("loss_valid"):
            flags.add("flag_zero_loss")
        if not audit_dict.get("impact_valid"):
            flags.add("flag_zero_nodes")
        if not audit_dict.get("actions_valid"):
            flags.add("flag_no_actions")
        if not audit_dict.get("graph_valid"):
            flags.add("flag_no_edges")
        if not audit_dict.get("map_valid"):
            flags.add("flag_no_map")

        return cls(
            run_id=audit_dict.get("run_id", ""),
            scenario_id=audit_dict.get("scenario_id", ""),
            violation_fingerprint=rule_ids,
            output_flags=frozenset(flags),
        )


def jaccard_similarity(a: FrozenSet[str], b: FrozenSet[str]) -> float:
    """
    Jaccard similarity between two frozen sets.
    Returns 1.0 for two empty sets (both have no violations — identical state).
    """
    if not a and not b:
        return 1.0
    union = len(a | b)
    if union == 0:
        return 1.0
    return len(a & b) / union


def _combined_fingerprint(sig: IncidentSignature) -> FrozenSet[str]:
    """Merge violation and output fingerprints for similarity comparison."""
    return sig.violation_fingerprint | sig.output_flags


def cluster_incidents(
    incidents: List[IncidentSignature],
    similarity_threshold: float = 0.6,
) -> Dict[str, List[str]]:
    """
    Aggregate run incidents into pattern clusters using Jaccard similarity.

    This is lightweight unsupervised clustering — NOT deep learning.
    The algorithm is greedy single-linkage: each incident joins the first
    existing cluster where ANY member has Jaccard similarity >= threshold.

    When to use:
      - Analyzing 50+ production run failures to find recurring patterns
      - Identifying whether a new wave of failures matches a previously seen cluster
      - NOT needed for real-time per-run classification (use deterministic_cluster instead)

    Parameters
    ----------
    incidents : list[IncidentSignature]
        Run incidents to cluster. Must have at least 1 entry.
    similarity_threshold : float
        Jaccard similarity threshold for cluster membership. 0.6 = 3/5 features overlap.
        Lower values produce fewer, larger clusters. 0.8+ produces fine-grained clusters.

    Returns
    -------
    dict[str, list[str]]
        Maps cluster labels ("cluster_1", "cluster_2", ...) to lists of run_ids.
    """
    if not incidents:
        return {}

    # Greedy single-linkage: O(n²) — fine for n < 10,000
    clusters: Dict[str, List[IncidentSignature]] = {}
    cluster_counter = 0

    for incident in incidents:
        fp_i = _combined_fingerprint(incident)
        assigned = False

        for label, members in clusters.items():
            # Single-linkage: join if similar to ANY existing member
            if any(
                jaccard_similarity(fp_i, _combined_fingerprint(m)) >= similarity_threshold
                for m in members
            ):
                members.append(incident)
                assigned = True
                break

        if not assigned:
            cluster_counter += 1
            clusters[f"cluster_{cluster_counter}"] = [incident]

    return {
        label: [sig.run_id for sig in members]
        for label, members in clusters.items()
    }


def summarize_clusters(
    incidents: List[IncidentSignature],
    similarity_threshold: float = 0.6,
) -> List[dict]:
    """
    Cluster incidents and return a summary with representative violations per cluster.
    Useful for log analysis dashboards.
    """
    raw = cluster_incidents(incidents, similarity_threshold)
    incident_by_run_id = {sig.run_id: sig for sig in incidents}

    summaries = []
    for label, run_ids in raw.items():
        members = [incident_by_run_id[rid] for rid in run_ids if rid in incident_by_run_id]
        # Representative fingerprint: union of all violation fingerprints in cluster
        all_rules: FrozenSet[str] = frozenset().union(*(m.violation_fingerprint for m in members))
        all_scenarios = list({m.scenario_id for m in members})
        summaries.append({
            "cluster_label": label,
            "incident_count": len(run_ids),
            "run_ids": run_ids,
            "scenarios": all_scenarios,
            "common_violations": sorted(all_rules),
            "similarity_threshold": similarity_threshold,
            "method": "jaccard_single_linkage",
        })

    summaries.sort(key=lambda s: s["incident_count"], reverse=True)
    return summaries
