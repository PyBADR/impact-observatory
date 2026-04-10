"""
API endpoint integration tests.
Tests the full HTTP layer — not just the engine.

Notes on auth:
  - settings.api_key defaults to "" (empty string) = dev mode
  - In dev mode, require_api_key returns "CRO" with NO key required
  - So requests WITHOUT X-API-Key headers also succeed in dev mode
  - Tests document this behavior explicitly

Route: POST /api/v1/runs (includes require_api_key dependency via api_v1 router)
"""
import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi.testclient import TestClient
from src.main import app

client = TestClient(app)

# In dev mode (api_key = ""), any X-API-Key value is accepted.
# The header is optional in dev mode but included for prod-readiness.
VALID_HEADERS = {"X-API-Key": "observatory-dev-key"}


class TestHealthEndpoint:
    def test_health_returns_200(self):
        r = client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    def test_health_no_auth_required(self):
        """Health endpoint has no auth dependency — no header needed."""
        r = client.get("/health")
        assert r.status_code == 200


class TestRunEndpoint:
    def test_valid_run_returns_201(self):
        """POST /api/v1/runs returns 201 Created on success."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "hormuz_chokepoint_disruption", "severity": 0.7, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201
        data = r.json()
        assert "run_id" in data
        assert "unified_risk_score" in data
        assert isinstance(data["unified_risk_score"], (int, float))

    def test_valid_run_has_mandatory_fields(self):
        """All 16 mandatory output fields must be present."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "hormuz_chokepoint_disruption", "severity": 0.7, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201
        data = r.json()
        mandatory_fields = [
            "run_id", "scenario_id", "model_version", "event_severity", "peak_day",
            "confidence_score", "financial_impact", "sector_analysis", "propagation_score",
            "unified_risk_score", "risk_level", "physical_system_status", "bottlenecks",
            "congestion_score", "recovery_score", "explainability", "decision_plan",
        ]
        for field in mandatory_fields:
            assert field in data, f"Mandatory field '{field}' missing from response"

    def test_invalid_scenario_returns_400(self):
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "NONEXISTENT_XYZ", "severity": 0.7, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code in (400, 422)
        data = r.json()
        assert "detail" in data or "error" in data

    def test_financial_is_list_not_dict(self):
        """financial[] must be a list — frontend calls .reduce() on it."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "uae_banking_crisis", "severity": 0.6, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201
        data = r.json()
        assert isinstance(data.get("financial", []), list), \
            f"'financial' must be list, got {type(data.get('financial'))}"

    def test_sector_losses_is_list_of_dicts(self):
        """sector_losses must be a list of {sector, loss_usd, pct} dicts — not a flat dict."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "gcc_cyber_attack", "severity": 0.8, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201
        data = r.json()
        sl = data.get("financial_impact", {}).get("sector_losses", [])
        assert isinstance(sl, list), f"sector_losses must be list, got {type(sl)}"
        for item in sl:
            assert isinstance(item, dict), f"Each sector_loss must be dict, got {type(item)}"
            assert "sector" in item and "loss_usd" in item, \
                f"sector_loss missing required keys: {item}"

    def test_numeric_fields_are_numbers(self):
        """All top-level numeric fields must be int or float — never None."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "saudi_oil_shock", "severity": 0.5, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201
        data = r.json()
        numeric_fields = [
            "unified_risk_score", "event_severity", "confidence_score",
            "propagation_score", "congestion_score", "recovery_score",
        ]
        for f in numeric_fields:
            assert isinstance(data.get(f), (int, float)), \
                f"Field '{f}' must be numeric, got {type(data.get(f)).__name__} = {data.get(f)}"

    def test_physical_system_status_has_numeric_scores(self):
        """physical_system_status.congestion_score and recovery_score are called with .toFixed()."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "hormuz_chokepoint_disruption", "severity": 0.7, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201
        data = r.json()
        pss = data.get("physical_system_status", {})
        assert isinstance(pss.get("congestion_score"), (int, float)), \
            f"physical_system_status.congestion_score must be numeric"
        assert isinstance(pss.get("recovery_score"), (int, float)), \
            f"physical_system_status.recovery_score must be numeric"

    def test_insurance_time_to_insolvency_is_numeric(self):
        """time_to_insolvency_hours must be numeric — 9999 means no imminent risk."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "hormuz_chokepoint_disruption", "severity": 0.7, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201
        data = r.json()
        val = data.get("insurance_stress", {}).get("time_to_insolvency_hours")
        assert isinstance(val, (int, float)), \
            f"insurance_stress.time_to_insolvency_hours must be numeric (9999=no risk), got {type(val)}"

    def test_error_response_is_structured(self):
        """Error response must have 'error' or 'detail' key, not partial pipeline data."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "INVALID_SCENARIO_XYZ", "severity": 0.5, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code in (400, 422, 500)
        data = r.json()
        assert "unified_risk_score" not in data, \
            "Error response should not contain pipeline output fields"
        assert "detail" in data or "error" in data, \
            f"Error response must have 'detail' or 'error' key: {data}"

    def test_dev_mode_no_auth_key_still_works(self):
        """Dev mode: when api_key='', requests without header succeed (returns CRO role)."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "hormuz_chokepoint_disruption", "severity": 0.5, "horizon_hours": 24},
            # No X-API-Key header — should work in dev mode
        )
        # In dev mode (settings.api_key = ""), this returns 201
        # In prod mode (settings.api_key set), this returns 401
        if r.status_code == 201:
            pass  # dev mode — auth not enforced, expected
        else:
            assert r.status_code in (401, 403), \
                f"Without auth header: expected 201 (dev) or 401/403 (prod), got {r.status_code}"

    def test_headline_block_all_fields_present(self):
        """headline block must have all required fields."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "energy_market_volatility_shock", "severity": 0.6, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201
        data = r.json()
        headline = data.get("headline", {})
        required_headline_fields = [
            "total_loss_usd", "peak_day", "affected_entities",
            "critical_count", "elevated_count", "max_recovery_days", "average_stress",
        ]
        for f in required_headline_fields:
            assert f in headline, f"headline.{f} missing"
            assert isinstance(headline[f], (int, float)), \
                f"headline.{f} must be numeric, got {type(headline[f])}"

    def test_decisions_actions_is_list(self):
        """decisions.actions must be a list."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "hormuz_chokepoint_disruption", "severity": 0.7, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201
        data = r.json()
        decisions = data.get("decisions", {})
        assert isinstance(decisions.get("actions"), list), \
            f"decisions.actions must be list, got {type(decisions.get('actions'))}"

    def test_explainability_causal_chain_is_list(self):
        """explainability.causal_chain must be a list with exactly 20 steps."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "hormuz_chokepoint_disruption", "severity": 0.7, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201
        data = r.json()
        causal_chain = data.get("explainability", {}).get("causal_chain", [])
        assert isinstance(causal_chain, list), "explainability.causal_chain must be list"
        assert len(causal_chain) == 20, \
            f"causal_chain must have 20 steps, got {len(causal_chain)}"

    def test_banking_stress_aggregate_is_numeric(self):
        """banking_stress.aggregate_stress must be numeric."""
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": "uae_banking_crisis", "severity": 0.7, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201
        data = r.json()
        bs = data.get("banking_stress", {})
        assert isinstance(bs.get("aggregate_stress"), (int, float)), \
            f"banking_stress.aggregate_stress must be numeric"
        assert isinstance(bs.get("time_to_liquidity_breach_hours"), (int, float)), \
            f"banking_stress.time_to_liquidity_breach_hours must be numeric"

    @pytest.mark.parametrize("scenario_id", [
        "hormuz_chokepoint_disruption",
        "uae_banking_crisis",
        "red_sea_trade_corridor_instability",
        "energy_market_volatility_shock",
        "critical_port_throughput_disruption",
        "financial_infrastructure_cyber_disruption",
        "gcc_cyber_attack",
        "saudi_oil_shock",
        "regional_liquidity_stress_event",
    ])
    def test_all_scenarios_return_201(self, scenario_id):
        r = client.post(
            "/api/v1/runs",
            json={"scenario_id": scenario_id, "severity": 0.6, "horizon_hours": 24},
            headers=VALID_HEADERS,
        )
        assert r.status_code == 201, \
            f"Scenario '{scenario_id}' returned {r.status_code}: {r.text[:200]}"
        data = r.json()
        assert "run_id" in data, f"Scenario '{scenario_id}' response missing run_id"
        assert isinstance(data.get("unified_risk_score"), (int, float)), \
            f"Scenario '{scenario_id}' unified_risk_score is not numeric"


class TestListRunsEndpoint:
    def test_list_runs_returns_200(self):
        """GET /api/v1/runs should return a list."""
        r = client.get("/api/v1/runs", headers=VALID_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "runs" in data
        assert isinstance(data["runs"], list)

    def test_list_runs_has_pagination_fields(self):
        r = client.get("/api/v1/runs?limit=5&offset=0", headers=VALID_HEADERS)
        assert r.status_code == 200
        data = r.json()
        assert "limit" in data
        assert "offset" in data
        assert "count" in data
