"""
Impact Observatory | مرصد الأثر
Physics Intelligence Layer — node utilization, flow conservation, bottlenecks,
shock propagation, recovery trajectory, congestion.

All equations documented inline and in METHODOLOGY.md.
"""
from __future__ import annotations

import math
from typing import Any

import numpy as np

from src.utils import clamp, classify_stress
from src.config import (
    PHYS_ALPHA as ALPHA,
    PHYS_BETA as BETA,
    PHYS_FLOW_IMBALANCE_THRESHOLD,
    PHYS_CONGESTION_ONSET as CONGESTION_THRESHOLD,
    PHYS_RECOVERY_BASE_RATE,
)

# ---------------------------------------------------------------------------
# Constants (derived from config — do not hardcode here)
# ---------------------------------------------------------------------------

SATURATION_THRESHOLD = 0.85     # U_i above this → saturated

# Sector-specific recovery rates (fraction of damage recovered per day)
_RECOVERY_RATES: dict[str, float] = {
    "energy":         0.07,
    "maritime":       0.06,
    "banking":        0.12,
    "insurance":      0.10,
    "fintech":        0.14,
    "logistics":      0.08,
    "infrastructure": 0.05,
    "government":     0.15,
    "healthcare":     0.09,
}
_DEFAULT_RECOVERY_RATE = 0.08


class PhysicsViolationError(Exception):
    """Raised when a flow conservation violation exceeds tolerance."""


# ---------------------------------------------------------------------------
# 1. Node Utilization
# ---------------------------------------------------------------------------

def compute_node_utilization(nodes: list[dict], severity: float) -> list[dict]:
    """
    U_i = current_load_i / max_capacity_i

    Under a shock, current_load increases by:
      delta_load = severity * (1 - U_i_base) * criticality_i

    Returns list of:
      {node_id, label, utilization, saturation_status, capacity, load}
    """
    severity = clamp(severity, 0.0, 1.0)
    results: list[dict] = []

    for node in nodes:
        capacity = float(node.get("capacity", 1.0))
        base_load = float(node.get("current_load", 0.5)) * capacity
        criticality = clamp(float(node.get("criticality", 0.5)), 0.0, 1.0)

        base_util = clamp(base_load / capacity, 0.0, 1.0) if capacity > 0 else 0.0

        # Shock-driven load surge
        delta_load = severity * (1.0 - base_util) * criticality * capacity
        stressed_load = min(base_load + delta_load, capacity * 1.20)  # can overflow 20%
        utilization = clamp(stressed_load / capacity, 0.0, 1.20) if capacity > 0 else 0.0

        saturation_status = (
            "SATURATED" if utilization >= SATURATION_THRESHOLD
            else "NOMINAL"
        )

        results.append({
            "node_id": node.get("id", "unknown"),
            "label": node.get("label", node.get("id", "unknown")),
            "utilization": round(utilization, 4),
            "saturation_status": saturation_status,
            "capacity": capacity,
            "load": round(stressed_load, 2),
            "sector": node.get("sector", "infrastructure"),
            "criticality": criticality,
            "redundancy": float(node.get("redundancy", 0.3)),
        })

    return results


# ---------------------------------------------------------------------------
# 2. Flow Conservation
# ---------------------------------------------------------------------------

def check_flow_conservation(
    nodes: list[dict],
    flows: list[dict],
) -> dict:
    """
    Inflow_i - Outflow_i = delta_storage_i  (must balance within 1%)

    PhysicsViolationError is raised when abs(imbalance) > 1% for any node.

    Returns {balanced: bool, violations: list, net_accumulation: float}
    """
    TOLERANCE = PHYS_FLOW_IMBALANCE_THRESHOLD

    node_ids = {n.get("id") for n in nodes}
    inflow: dict[str, float] = {nid: 0.0 for nid in node_ids}
    outflow: dict[str, float] = {nid: 0.0 for nid in node_ids}

    for flow in flows:
        src = flow.get("source")
        dst = flow.get("target")
        vol = float(flow.get("volume", 0.0))
        if src in outflow:
            outflow[src] += vol
        if dst in inflow:
            inflow[dst] += vol

    violations = []
    total_net = 0.0

    for nid in node_ids:
        net = inflow[nid] - outflow[nid]
        total_net += net
        imbalance = abs(net) / max(inflow[nid] + outflow[nid], 1.0)
        if imbalance > TOLERANCE:
            violations.append({
                "node_id": nid,
                "inflow": round(inflow[nid], 2),
                "outflow": round(outflow[nid], 2),
                "imbalance_pct": round(imbalance * 100, 2),
            })

    balanced = len(violations) == 0 and abs(total_net) / max(abs(total_net) + 1, 1) < TOLERANCE

    if violations:
        raise PhysicsViolationError(
            f"Flow conservation violated in {len(violations)} node(s); "
            f"imbalances exceed {TOLERANCE * 100:.0f}% tolerance."
        )

    return {
        "balanced": balanced,
        "violations": violations,
        "net_accumulation": round(total_net, 2),
        "violation_count": len(violations),
    }


# ---------------------------------------------------------------------------
# 3. Bottleneck Score
# ---------------------------------------------------------------------------

def compute_bottleneck_scores(
    node_utilization: list[dict],
    adjacency: dict[str, list[str]],
) -> list[dict]:
    """
    B_i = U_i * criticality_i * (1 / (redundancy_i + 0.1))

    Connectivity bonus: log(1 + degree_i) / log(1 + max_degree)

    Returns list sorted by bottleneck_score descending.
    """
    if not node_utilization:
        return []

    degrees = {n: len(adjacency.get(n, [])) for n in adjacency}
    max_degree = max(degrees.values()) if degrees else 1

    results: list[dict] = []
    for node in node_utilization:
        nid = node["node_id"]
        util = node["utilization"]
        criticality = node.get("criticality", 0.5)
        redundancy = node.get("redundancy", 0.3)
        degree = degrees.get(nid, 1)

        connectivity_bonus = math.log1p(degree) / math.log1p(max_degree) if max_degree > 0 else 1.0

        bottleneck_score = clamp(
            util * criticality * (1.0 / (redundancy + 0.1)) * (0.7 + 0.3 * connectivity_bonus),
            0.0, 1.0,
        )

        results.append({
            "node_id": nid,
            "label": node.get("label", nid),
            "bottleneck_score": round(bottleneck_score, 4),
            "is_critical_bottleneck": bottleneck_score > 0.75,
            "utilization": node["utilization"],
            "criticality": criticality,
            "redundancy": redundancy,
            "degree": degree,
        })

    results.sort(key=lambda x: -x["bottleneck_score"])
    for i, r in enumerate(results):
        r["rank"] = i + 1

    return results


# ---------------------------------------------------------------------------
# 4. Shock Wave Propagation
# ---------------------------------------------------------------------------

def propagate_shock_wave(
    shock_nodes: list[str],
    severity: float,
    adjacency: dict[str, list[str]],
    n_steps: int,
) -> list[dict]:
    """
    Continuous shock propagation PDE (discretised):
      dP/dt = -alpha*P + beta * sum_j(A_ij * P_j)
      alpha = 0.08 (attenuation)
      beta  = 0.65 (amplification)

    Returns list of {step, node_id, shock_intensity, cumulative_damage, affected_nodes}.
    """
    severity = clamp(severity, 0.0, 1.0)
    all_nodes = list(adjacency.keys())
    if not all_nodes:
        return []

    node_index = {n: i for i, n in enumerate(all_nodes)}
    n = len(all_nodes)

    # Adjacency matrix
    A = np.zeros((n, n), dtype=np.float64)
    for node, neighbors in adjacency.items():
        i = node_index.get(node)
        if i is None:
            continue
        for nb in neighbors:
            j = node_index.get(nb)
            if j is not None:
                A[i, j] = 1.0

    # Row-normalise
    row_sums = A.sum(axis=1, keepdims=True)
    row_sums[row_sums == 0] = 1.0
    A_norm = A / row_sums

    # Initialise
    P = np.zeros(n, dtype=np.float64)
    for sn in shock_nodes:
        idx = node_index.get(sn)
        if idx is not None:
            P[idx] = severity

    cumulative_damage = P.copy()
    results: list[dict] = []

    for step in range(1, n_steps + 1):
        dP = -ALPHA * P + BETA * (A_norm @ P)
        P_new = np.clip(P + dP, 0.0, 1.0)

        affected = int(np.sum(P_new > 0.01))
        max_intensity = float(P_new.max())

        results.append({
            "step": step,
            "node_id": all_nodes[int(np.argmax(P_new))],
            "shock_intensity": round(max_intensity, 4),
            "cumulative_damage": round(float(cumulative_damage.max()), 4),
            "affected_nodes": affected,
            "mean_intensity": round(float(P_new[P_new > 0.01].mean()) if affected > 0 else 0.0, 4),
        })

        cumulative_damage = np.maximum(cumulative_damage, P_new)
        P = P_new

        if P.max() < 0.003:
            break

    return results


# ---------------------------------------------------------------------------
# 5. Recovery Trajectory
# ---------------------------------------------------------------------------

def compute_recovery_trajectory(
    severity: float,
    peak_day: int,
    horizon_days: int,
    sector: str,
) -> list[dict]:
    """
    Recovery model:
      R(t+1) = R(t) + r*(1 - Damage(t)) - ResidualStress(t)

    r = sector-specific recovery rate (0.05–0.15)
    Damage(0) = severity
    ResidualStress(t) = severity * e^(-0.12*t)

    Returns {day, recovery_fraction, damage_remaining}.
    """
    severity = clamp(severity, 0.0, 1.0)
    r = _RECOVERY_RATES.get(sector.lower(), _DEFAULT_RECOVERY_RATE)

    damage = severity
    recovery = 0.0
    trajectory: list[dict] = []

    for day in range(0, horizon_days + 1):
        residual_stress = severity * math.exp(-0.12 * max(0, day - peak_day))
        if day > peak_day:
            delta = r * (1.0 - damage) - max(0, residual_stress * 0.1)
            recovery = clamp(recovery + delta, 0.0, 1.0)
            damage = clamp(severity * (1.0 - recovery), 0.0, 1.0)

        trajectory.append({
            "day": day,
            "recovery_fraction": round(recovery, 4),
            "damage_remaining": round(damage, 4),
            "residual_stress": round(residual_stress, 4),
        })

        if recovery >= 0.99:
            break

    return trajectory


# ---------------------------------------------------------------------------
# 6. Congestion Score
# ---------------------------------------------------------------------------

def compute_congestion(node_utilization: list[dict]) -> dict:
    """
    CG_i = max(0, U_i - threshold) / (1 - threshold)   threshold = 0.75

    System congestion = capacity-weighted average of CG_i.

    Returns {system_congestion_score, congested_nodes, saturation_pct}.
    """
    if not node_utilization:
        return {
            "system_congestion_score": 0.0,
            "congested_nodes": [],
            "saturation_pct": 0.0,
        }

    congested_nodes = []
    total_weight = 0.0
    weighted_cong = 0.0
    n_saturated = 0

    for node in node_utilization:
        util = node["utilization"]
        capacity = float(node.get("capacity", 1.0))
        cg = max(0.0, (util - CONGESTION_THRESHOLD) / (1.0 - CONGESTION_THRESHOLD))

        if cg > 0:
            congested_nodes.append({
                "node_id": node["node_id"],
                "label": node.get("label", node["node_id"]),
                "congestion": round(cg, 4),
                "utilization": round(util, 4),
            })

        if util >= SATURATION_THRESHOLD:
            n_saturated += 1

        weighted_cong += cg * capacity
        total_weight += capacity

    system_cong = clamp(weighted_cong / total_weight, 0.0, 1.0) if total_weight > 0 else 0.0
    saturation_pct = round(n_saturated / len(node_utilization) * 100, 1)

    congested_nodes.sort(key=lambda x: -x["congestion"])

    return {
        "system_congestion_score": round(system_cong, 4),
        "congested_nodes": congested_nodes,
        "saturation_pct": saturation_pct,
        "n_congested": len(congested_nodes),
        "n_saturated": n_saturated,
    }
