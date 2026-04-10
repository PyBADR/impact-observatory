"""
Metrics Provenance Layer — Explainability + Factor Decomposition.

5 engines:
  1. MetricProvenanceEngine   — why this number, what source/model
  2. FactorBreakdownEngine    — top drivers for each metric
  3. MetricRangeEngine        — uncertainty bands, not false-precision points
  4. DecisionReasoningEngine  — why this decision, why this rank
  5. DataBasisEngine          — data period, calibration basis, freshness
"""
from src.metrics_provenance.provenance_engine import build_metric_provenance
from src.metrics_provenance.factor_engine import build_factor_breakdowns
from src.metrics_provenance.range_engine import build_metric_ranges
from src.metrics_provenance.reasoning_engine import build_decision_reasonings
from src.metrics_provenance.basis_engine import build_data_bases
from src.metrics_provenance.pipeline import run_provenance_pipeline, ProvenanceLayerResult

__all__ = [
    "build_metric_provenance",
    "build_factor_breakdowns",
    "build_metric_ranges",
    "build_decision_reasonings",
    "build_data_bases",
    "run_provenance_pipeline",
    "ProvenanceLayerResult",
]
