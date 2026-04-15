"""
Impact Observatory | مرصد الأثر
Data Trust Audit Layer — v1.0.0

Provides source registry, scenario provenance, scoring logic,
and audit tooling for data transparency and fallback safety.

All scenario values remain static/config-based fallbacks.
This layer documents and scores them — it does NOT replace them.
"""
from __future__ import annotations

from src.data_trust.source_registry import (
    DataSource,
    DataSourceType,
    RefreshFrequency,
    FreshnessStatus,
    DATA_SOURCE_REGISTRY,
    get_source,
    get_sources_by_type,
    get_stale_sources,
)
from src.data_trust.scenario_provenance import (
    ScenarioProvenance,
    build_provenance_for_scenario,
    build_all_provenance,
)
from src.data_trust.scoring import (
    TrustScore,
    compute_trust_score,
)
from src.data_trust.audit_reviewer import (
    AuditFinding,
    AuditSeverity,
    run_data_trust_audit,
)

__all__ = [
    # Source Registry
    "DataSource",
    "DataSourceType",
    "RefreshFrequency",
    "FreshnessStatus",
    "DATA_SOURCE_REGISTRY",
    "get_source",
    "get_sources_by_type",
    "get_stale_sources",
    # Provenance
    "ScenarioProvenance",
    "build_provenance_for_scenario",
    "build_all_provenance",
    # Scoring
    "TrustScore",
    "compute_trust_score",
    # Audit
    "AuditFinding",
    "AuditSeverity",
    "run_data_trust_audit",
]
