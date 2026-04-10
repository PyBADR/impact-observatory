"""Metrics Provenance Pipeline — chains all 5 engines into a single
ProvenanceLayerResult that Stage 85 can attach to the run.

Execution order:
  1. MetricProvenanceEngine   → why this number
  2. FactorBreakdownEngine    → top drivers
  3. MetricRangeEngine        → uncertainty bands
  4. DecisionReasoningEngine  → why this decision
  5. DataBasisEngine          → data period + freshness
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

from src.metrics_provenance.provenance_engine import build_metric_provenance
from src.metrics_provenance.factor_engine import build_factor_breakdowns
from src.metrics_provenance.range_engine import build_metric_ranges
from src.metrics_provenance.reasoning_engine import build_decision_reasonings
from src.metrics_provenance.basis_engine import build_data_bases


@dataclass(frozen=True, slots=True)
class ProvenanceLayerResult:
    """Immutable output of the provenance pipeline."""

    metric_provenance: list[dict] = field(default_factory=list)
    factor_breakdowns: list[dict] = field(default_factory=list)
    metric_ranges: list[dict] = field(default_factory=list)
    decision_reasonings: list[dict] = field(default_factory=list)
    data_bases: list[dict] = field(default_factory=list)
    pipeline_meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "metric_provenance": self.metric_provenance,
            "factor_breakdowns": self.factor_breakdowns,
            "metric_ranges": self.metric_ranges,
            "decision_reasonings": self.decision_reasonings,
            "data_bases": self.data_bases,
            "pipeline_meta": self.pipeline_meta,
        }


def run_provenance_pipeline(run_result: dict) -> ProvenanceLayerResult:
    """Execute all 5 provenance engines on a completed run_result.

    Parameters
    ----------
    run_result : dict
        The full simulation run_result dict (must include headline,
        banking_stress, insurance_stress, decision_quality,
        decision_calibration, decision_trust, etc.)

    Returns
    -------
    ProvenanceLayerResult
        Frozen dataclass with all provenance outputs + pipeline metadata.
    """
    t0 = time.monotonic()
    errors: list[str] = []

    # ── Engine 1: Metric Provenance ─────────────────────────────────────
    try:
        provenance = build_metric_provenance(run_result)
    except Exception as exc:
        provenance = []
        errors.append(f"provenance_engine: {exc!r}")

    # ── Engine 2: Factor Breakdowns ─────────────────────────────────────
    try:
        factors = build_factor_breakdowns(run_result)
    except Exception as exc:
        factors = []
        errors.append(f"factor_engine: {exc!r}")

    # ── Engine 3: Metric Ranges ─────────────────────────────────────────
    try:
        ranges = build_metric_ranges(run_result)
    except Exception as exc:
        ranges = []
        errors.append(f"range_engine: {exc!r}")

    # ── Engine 4: Decision Reasonings ───────────────────────────────────
    try:
        reasonings = build_decision_reasonings(run_result)
    except Exception as exc:
        reasonings = []
        errors.append(f"reasoning_engine: {exc!r}")

    # ── Engine 5: Data Bases ────────────────────────────────────────────
    try:
        bases = build_data_bases(run_result)
    except Exception as exc:
        bases = []
        errors.append(f"basis_engine: {exc!r}")

    elapsed_ms = round((time.monotonic() - t0) * 1000, 2)

    # ── Pipeline integrity hash ─────────────────────────────────────────
    payload = {
        "metric_provenance_count": len(provenance),
        "factor_breakdowns_count": len(factors),
        "metric_ranges_count": len(ranges),
        "decision_reasonings_count": len(reasonings),
        "data_bases_count": len(bases),
    }
    integrity_hash = hashlib.sha256(
        json.dumps(payload, sort_keys=True).encode("utf-8")
    ).hexdigest()

    meta: dict[str, Any] = {
        "pipeline_version": "1.0.0",
        "engines_executed": 5 - len(errors),
        "engines_failed": len(errors),
        "errors": errors,
        "elapsed_ms": elapsed_ms,
        "integrity_hash": integrity_hash,
        "counts": payload,
    }

    return ProvenanceLayerResult(
        metric_provenance=provenance,
        factor_breakdowns=factors,
        metric_ranges=ranges,
        decision_reasonings=reasonings,
        data_bases=bases,
        pipeline_meta=meta,
    )
