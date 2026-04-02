"""Disruption score: D = severity * reach * duration"""


def compute_disruption_score(severity: float, reach: float, duration: float) -> float:
    return min(1.0, severity * reach * duration)


def compute_disruption_index(affected_nodes: int, total_nodes: int, avg_severity: float, duration_days: float) -> dict:
    reach = affected_nodes / max(total_nodes, 1)
    duration_norm = min(1.0, duration_days / 30)
    score = compute_disruption_score(avg_severity, reach, duration_norm)
    return {"score": score, "reach": reach, "severity": avg_severity, "duration_norm": duration_norm}
