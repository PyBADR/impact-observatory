"""Confidence intervals for IFRS 17 compliance."""
import numpy as np


def compute_confidence_interval(values: list[float], confidence: float = 0.95) -> dict:
    arr = np.array(values)
    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0
    z = 1.96 if confidence == 0.95 else 2.576
    margin = z * std / np.sqrt(len(arr)) if len(arr) > 0 else 0.0
    return {"mean": mean, "std": std, "lower": mean - margin, "upper": mean + margin, "confidence": confidence}


def compute_model_confidence(impact_variance: float) -> float:
    """C = 1 / (1 + variance)"""
    return float(np.clip(1.0 / (1.0 + impact_variance), 0, 1))
