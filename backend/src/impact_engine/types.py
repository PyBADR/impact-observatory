"""Typed view over SimulationEngine.run() output.

Does NOT add new fields — just types the existing dict for static analysis.
"""
from __future__ import annotations

from typing import Any, TypedDict


class PipelineOutput(TypedDict, total=False):
    """Typed wrapper around the raw engine.run() dict.

    All keys mirror SimulationEngine.run() output exactly.
    total=False because the engine dict may omit some keys in edge cases.
    """
    run_id: str
    scenario_id: str
    model_version: str
    severity: float
    horizon_hours: int
    time_horizon_days: int
    generated_at: str
    duration_ms: int

    event_severity: float
    peak_day: int
    confidence_score: float
    propagation_score: float
    unified_risk_score: Any  # float or dict depending on context
    risk_level: str
    congestion_score: float
    recovery_score: float

    financial_impact: dict[str, Any]
    sector_analysis: list[dict[str, Any]]
    propagation_chain: list[dict[str, Any]]
    physical_system_status: dict[str, Any]
    bottlenecks: list[dict[str, Any]]
    recovery_trajectory: list[dict[str, Any]]
    banking_stress: dict[str, Any]
    insurance_stress: dict[str, Any]
    fintech_stress: dict[str, Any]
    flow_analysis: dict[str, Any]
    explainability: dict[str, Any]
    decision_plan: dict[str, Any]
    headline: dict[str, Any]
