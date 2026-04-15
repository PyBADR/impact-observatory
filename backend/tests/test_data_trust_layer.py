"""
Impact Observatory | مرصد الأثر
Test Suite: Data Trust Audit Layer v1

Tests:
  1. Source Registry — typed catalog, queries, no live sources
  2. Scenario Provenance — records for all catalog entries
  3. Scoring Logic — pure trust-weighted computation
  4. Audit Reviewer — finding generation, severity ordering
  5. Safe Fallback — every output marked as static_fallback
  6. Serialization — all models JSON-serializable
"""
import json
import pytest
from pathlib import Path

from src.data_trust.source_registry import (
    DataSource,
    DataSourceType,
    RefreshFrequency,
    FreshnessStatus,
    DATA_SOURCE_REGISTRY,
    get_source,
    get_sources_by_type,
    get_stale_sources,
    get_connected_live_sources,
    registry_summary,
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
    format_audit_report,
)
from src.simulation_engine import SCENARIO_CATALOG


# ═══════════════════════════════════════════════════════════════════════════════
# 1. Source Registry Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSourceRegistry:
    def test_registry_not_empty(self):
        assert len(DATA_SOURCE_REGISTRY) >= 10

    def test_every_source_has_required_fields(self):
        for sid, src in DATA_SOURCE_REGISTRY.items():
            assert isinstance(src, DataSource)
            assert src.source_id == sid
            assert len(src.name) > 0
            assert isinstance(src.source_type, DataSourceType)
            assert isinstance(src.refresh_frequency, RefreshFrequency)
            assert isinstance(src.freshness_status, FreshnessStatus)
            assert 0.0 <= src.confidence_weight <= 1.0
            assert len(src.last_updated) >= 10  # ISO date

    def test_get_source_found(self):
        src = get_source("src_config_weights")
        assert src is not None
        assert src.source_type == DataSourceType.STATIC

    def test_get_source_not_found(self):
        assert get_source("nonexistent_source") is None

    def test_get_sources_by_type_static(self):
        static = get_sources_by_type(DataSourceType.STATIC)
        assert len(static) >= 5
        for s in static:
            assert s.source_type == DataSourceType.STATIC

    def test_get_sources_by_type_government(self):
        gov = get_sources_by_type(DataSourceType.GOVERNMENT)
        assert len(gov) >= 3
        for s in gov:
            assert s.source_type == DataSourceType.GOVERNMENT

    def test_no_live_sources_connected(self):
        """Critical: no live sources are connected to the pipeline today."""
        live = get_connected_live_sources()
        assert len(live) == 0, (
            f"Expected 0 live sources but found {len(live)}: "
            f"{[s.source_id for s in live]}"
        )

    def test_stale_sources_detected(self):
        stale = get_stale_sources()
        assert len(stale) >= 1
        for s in stale:
            assert s.freshness_status == FreshnessStatus.STALE

    def test_registry_summary(self):
        summary = registry_summary()
        assert summary["total_sources"] == len(DATA_SOURCE_REGISTRY)
        assert summary["all_static_fallback"] is True
        assert summary["live_connected_count"] == 0
        assert isinstance(summary["by_type"], dict)

    def test_source_to_dict_serializable(self):
        for src in DATA_SOURCE_REGISTRY.values():
            d = src.to_dict()
            json.dumps(d)  # Must not raise


# ═══════════════════════════════════════════════════════════════════════════════
# 2. Scenario Provenance Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestScenarioProvenance:
    def test_build_provenance_returns_records(self):
        entry = SCENARIO_CATALOG["hormuz_chokepoint_disruption"]
        records = build_provenance_for_scenario(
            "hormuz_chokepoint_disruption", entry,
        )
        assert len(records) >= 6  # base_loss, peak_day, recovery, shock_nodes, sectors, type

    def test_provenance_has_required_fields(self):
        entry = SCENARIO_CATALOG["hormuz_chokepoint_disruption"]
        records = build_provenance_for_scenario(
            "hormuz_chokepoint_disruption", entry,
        )
        for rec in records:
            assert isinstance(rec, ScenarioProvenance)
            assert rec.scenario_id == "hormuz_chokepoint_disruption"
            assert len(rec.value_name) > 0
            assert len(rec.source_id) > 0
            assert len(rec.calculation_method) > 0
            assert len(rec.last_updated) >= 10
            assert 0.0 <= rec.confidence_score <= 1.0

    def test_all_provenance_marked_static_fallback(self):
        """Critical: every provenance record must be is_static_fallback=True."""
        entry = SCENARIO_CATALOG["hormuz_chokepoint_disruption"]
        records = build_provenance_for_scenario(
            "hormuz_chokepoint_disruption", entry,
        )
        for rec in records:
            assert rec.is_static_fallback is True, (
                f"Provenance {rec.value_name} should be static fallback "
                f"but is_static_fallback={rec.is_static_fallback}"
            )

    def test_base_loss_provenance_value_matches_catalog(self):
        entry = SCENARIO_CATALOG["hormuz_chokepoint_disruption"]
        records = build_provenance_for_scenario(
            "hormuz_chokepoint_disruption", entry,
        )
        base_loss_rec = next(
            r for r in records if r.value_name == "base_loss_usd"
        )
        assert base_loss_rec.current_value == entry["base_loss_usd"]

    def test_build_all_provenance_covers_catalog(self):
        all_prov = build_all_provenance(SCENARIO_CATALOG)
        assert len(all_prov) == len(SCENARIO_CATALOG)
        for sid in SCENARIO_CATALOG:
            assert sid in all_prov
            assert len(all_prov[sid]) >= 6

    def test_provenance_to_dict_serializable(self):
        entry = SCENARIO_CATALOG["hormuz_chokepoint_disruption"]
        records = build_provenance_for_scenario(
            "hormuz_chokepoint_disruption", entry,
        )
        for rec in records:
            d = rec.to_dict()
            json.dumps(d)  # Must not raise

    def test_sector_alpha_provenance_included(self):
        entry = SCENARIO_CATALOG["hormuz_chokepoint_disruption"]
        records = build_provenance_for_scenario(
            "hormuz_chokepoint_disruption", entry,
        )
        names = [r.value_name for r in records]
        # Hormuz affects energy, maritime, banking, insurance, fintech
        assert "sector_alpha_energy" in names
        assert "sector_alpha_maritime" in names


# ═══════════════════════════════════════════════════════════════════════════════
# 3. Scoring Logic Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestScoringLogic:
    def test_compute_trust_score_returns_result(self):
        score = compute_trust_score(
            scenario_id="hormuz_chokepoint_disruption",
            base_loss_usd=3_200_000_000,
            sectors_affected=["energy", "maritime", "banking"],
        )
        assert isinstance(score, TrustScore)

    def test_score_is_static_fallback(self):
        """Critical: all scores must be static fallback today."""
        score = compute_trust_score(
            scenario_id="hormuz_chokepoint_disruption",
            base_loss_usd=3_200_000_000,
            sectors_affected=["energy", "maritime"],
        )
        assert score.is_static_fallback is True

    def test_raw_base_loss_preserved(self):
        score = compute_trust_score(
            scenario_id="hormuz_chokepoint_disruption",
            base_loss_usd=3_200_000_000,
            sectors_affected=["energy"],
        )
        assert score.raw_base_loss_usd == 3_200_000_000

    def test_adjusted_loss_is_positive(self):
        score = compute_trust_score(
            scenario_id="hormuz_chokepoint_disruption",
            base_loss_usd=3_200_000_000,
            sectors_affected=["energy", "maritime"],
        )
        assert score.adjusted_loss_usd > 0

    def test_source_confidence_bounded(self):
        score = compute_trust_score(
            scenario_id="hormuz_chokepoint_disruption",
            base_loss_usd=3_200_000_000,
            sectors_affected=["energy"],
        )
        assert 0.0 <= score.source_confidence <= 1.0

    def test_freshness_penalty_bounded(self):
        score = compute_trust_score(
            scenario_id="hormuz_chokepoint_disruption",
            base_loss_usd=3_200_000_000,
            sectors_affected=["energy"],
        )
        assert 0.0 <= score.freshness_penalty <= 1.0

    def test_country_exposure_multiplier_realistic(self):
        score = compute_trust_score(
            scenario_id="hormuz_chokepoint_disruption",
            base_loss_usd=3_200_000_000,
            sectors_affected=["energy"],
        )
        assert 1.0 <= score.country_exposure_multiplier <= 1.3

    def test_computation_trace_present(self):
        score = compute_trust_score(
            scenario_id="hormuz_chokepoint_disruption",
            base_loss_usd=3_200_000_000,
            sectors_affected=["energy"],
        )
        assert len(score.computation_trace) >= 5

    def test_no_signal_inputs_used(self):
        score = compute_trust_score(
            scenario_id="hormuz_chokepoint_disruption",
            base_loss_usd=3_200_000_000,
            sectors_affected=["energy"],
        )
        assert len(score.signal_inputs_used) == 0

    def test_pure_function_deterministic(self):
        """Same inputs must produce same outputs."""
        args = dict(
            scenario_id="uae_banking_crisis",
            base_loss_usd=1_800_000_000,
            sectors_affected=["banking", "fintech"],
        )
        a = compute_trust_score(**args)
        b = compute_trust_score(**args)
        assert a.adjusted_loss_usd == b.adjusted_loss_usd
        assert a.source_confidence == b.source_confidence

    def test_different_scenarios_different_country_mult(self):
        uae = compute_trust_score(
            "hormuz_chokepoint_disruption", 1_000_000_000, ["energy"],
        )
        bahrain = compute_trust_score(
            "bahrain_sovereign_stress", 1_000_000_000, ["banking"],
        )
        assert uae.country_exposure_multiplier != bahrain.country_exposure_multiplier

    def test_score_to_dict_serializable(self):
        score = compute_trust_score(
            "hormuz_chokepoint_disruption", 3_200_000_000, ["energy"],
        )
        d = score.to_dict()
        json.dumps(d)  # Must not raise

    def test_all_catalog_scenarios_scoreable(self):
        """Every scenario in SCENARIO_CATALOG can be scored."""
        for sid, entry in SCENARIO_CATALOG.items():
            score = compute_trust_score(
                scenario_id=sid,
                base_loss_usd=entry["base_loss_usd"],
                sectors_affected=entry.get("sectors_affected", []),
            )
            assert score.adjusted_loss_usd > 0
            assert score.is_static_fallback is True


# ═══════════════════════════════════════════════════════════════════════════════
# 4. Audit Reviewer Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestAuditReviewer:
    @pytest.fixture
    def project_root(self):
        return Path(__file__).resolve().parent.parent.parent

    def test_audit_returns_findings(self, project_root):
        findings = run_data_trust_audit(project_root)
        assert isinstance(findings, list)
        assert len(findings) >= 10  # Should find many things

    def test_findings_have_required_fields(self, project_root):
        findings = run_data_trust_audit(project_root)
        for f in findings:
            assert isinstance(f, AuditFinding)
            assert len(f.category) > 0
            assert isinstance(f.severity, AuditSeverity)
            assert len(f.file_path) > 0
            assert len(f.description) > 0
            assert len(f.recommendation) > 0

    def test_findings_sorted_by_severity(self, project_root):
        findings = run_data_trust_audit(project_root)
        severity_vals = [f.severity for f in findings]
        order = {AuditSeverity.CRITICAL: 0, AuditSeverity.WARNING: 1, AuditSeverity.INFO: 2}
        numeric = [order[s] for s in severity_vals]
        assert numeric == sorted(numeric)

    def test_hardcoded_values_detected(self, project_root):
        findings = run_data_trust_audit(project_root)
        cats = [f.category for f in findings]
        assert "hardcoded_value" in cats

    def test_value_control_files_identified(self, project_root):
        findings = run_data_trust_audit(project_root)
        control_findings = [f for f in findings if f.category == "value_control_file"]
        assert len(control_findings) >= 5

    def test_missing_timestamps_flagged(self, project_root):
        findings = run_data_trust_audit(project_root)
        ts_findings = [f for f in findings if f.category == "missing_timestamp"]
        assert len(ts_findings) >= 1

    def test_format_report_is_markdown(self, project_root):
        findings = run_data_trust_audit(project_root)
        report = format_audit_report(findings)
        assert report.startswith("# Data Trust Audit Report")
        assert "Total findings" in report

    def test_findings_to_dict_serializable(self, project_root):
        findings = run_data_trust_audit(project_root)
        for f in findings:
            d = f.to_dict()
            json.dumps(d)  # Must not raise


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Safe Fallback Rule Tests
# ═══════════════════════════════════════════════════════════════════════════════

class TestSafeFallbackRule:
    def test_registry_confirms_all_static(self):
        summary = registry_summary()
        assert summary["all_static_fallback"] is True

    def test_provenance_all_static(self):
        """Every provenance record across all scenarios is static."""
        all_prov = build_all_provenance(SCENARIO_CATALOG)
        for sid, records in all_prov.items():
            for rec in records:
                assert rec.is_static_fallback is True, (
                    f"{sid}/{rec.value_name} is not static fallback"
                )

    def test_scoring_all_static(self):
        """Every trust score across all scenarios is static."""
        for sid, entry in SCENARIO_CATALOG.items():
            score = compute_trust_score(
                sid, entry["base_loss_usd"], entry.get("sectors_affected", []),
            )
            assert score.is_static_fallback is True, (
                f"{sid} score is not static fallback"
            )

    def test_no_live_data_leaks(self):
        """No source claims to be fresh AND non-static."""
        for src in DATA_SOURCE_REGISTRY.values():
            if src.source_type != DataSourceType.STATIC:
                # Non-static sources must NOT be fresh (they're not connected)
                if src.confidence_weight > 0:
                    assert src.freshness_status != FreshnessStatus.FRESH, (
                        f"Source {src.source_id} claims FRESH but is "
                        f"type={src.source_type.value} — potential false live claim"
                    )


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Cross-Scenario Coverage
# ═══════════════════════════════════════════════════════════════════════════════

class TestCrossScenarioCoverage:
    def test_all_20_scenarios_have_provenance(self):
        all_prov = build_all_provenance(SCENARIO_CATALOG)
        assert len(all_prov) == len(SCENARIO_CATALOG)

    def test_all_provenance_records_non_empty(self):
        all_prov = build_all_provenance(SCENARIO_CATALOG)
        for sid, records in all_prov.items():
            assert len(records) >= 6, f"Scenario {sid} has too few provenance records"

    def test_full_pipeline_json_serializable(self):
        """The complete output of all components is JSON-safe."""
        # Registry
        summary = registry_summary()
        json.dumps(summary)

        # Provenance
        all_prov = build_all_provenance(SCENARIO_CATALOG)
        for sid, records in all_prov.items():
            json.dumps([r.to_dict() for r in records])

        # Scoring
        for sid, entry in SCENARIO_CATALOG.items():
            score = compute_trust_score(
                sid, entry["base_loss_usd"], entry.get("sectors_affected", []),
            )
            json.dumps(score.to_dict())
