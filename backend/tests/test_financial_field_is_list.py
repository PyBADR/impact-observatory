"""
Regression test: `financial` field in run_orchestrator output must always be
a Python list so the frontend can call .reduce() / for..of without crashing.

Root cause fixed: run_orchestrator.py previously set
  "financial": result.get("financial_impact", {})
which returned a dict (the full financial_impact object).
ExecutiveDashboard.tsx and dashboard/page.tsx both iterate `financial` as an
array → minified JS crashed with "f.reduce is not a function".

Fix: "financial" now uses `financial_list` (the top_entities array already
extracted on line 100) with an isinstance(list) guard.
"""
from __future__ import annotations

import pytest

# ---------------------------------------------------------------------------
# Attempt live import; skip gracefully if deps are missing in CI/local
# ---------------------------------------------------------------------------
try:
    from src.schemas.scenario import ScenarioCreate  # type: ignore
    from src.services.run_orchestrator import execute_run  # type: ignore
    _DEPS_AVAILABLE = True
except Exception as _import_err:  # pragma: no cover
    _DEPS_AVAILABLE = False
    _import_err_msg = str(_import_err)


skip_if_no_deps = pytest.mark.skipif(
    not _DEPS_AVAILABLE,
    reason=f"Backend deps not available in this environment",
)


SCENARIOS = [
    ("hormuz_chokepoint_disruption",              0.85, 336),
    ("red_sea_trade_corridor_instability",         0.70, 336),
    ("financial_infrastructure_cyber_disruption",  0.60, 168),
    ("energy_market_volatility_shock",             0.80, 336),
    ("regional_liquidity_stress_event",            0.70, 336),
    ("critical_port_throughput_disruption",        0.60, 336),
]


@skip_if_no_deps
@pytest.mark.parametrize("scenario_id,severity,horizon", SCENARIOS)
def test_financial_is_list(scenario_id: str, severity: float, horizon: int):
    """financial must be a list so the frontend can call .reduce() on it."""
    params = ScenarioCreate(
        scenario_id=scenario_id,
        severity=severity,
        horizon_hours=horizon,
    )
    result = execute_run(params)

    financial = result.get("financial")
    assert isinstance(financial, list), (
        f"[{scenario_id}] financial must be list, got {type(financial).__name__}. "
        "This causes 'f.reduce is not a function' crash in ExecutiveDashboard.tsx"
    )


@skip_if_no_deps
@pytest.mark.parametrize("scenario_id,severity,horizon", SCENARIOS)
def test_financial_entities_have_sector_and_loss(scenario_id: str, severity: float, horizon: int):
    """Each entity in financial[] must have sector and loss_usd fields
    (used by ExecutiveDashboard to build sector_exposure via .reduce())."""
    params = ScenarioCreate(
        scenario_id=scenario_id,
        severity=severity,
        horizon_hours=horizon,
    )
    result = execute_run(params)
    financial = result.get("financial", [])

    # If list is empty that is acceptable (no propagation = no entities)
    for i, fi in enumerate(financial):
        assert isinstance(fi, dict), f"[{scenario_id}] financial[{i}] must be dict, got {type(fi).__name__}"
        assert "sector" in fi, f"[{scenario_id}] financial[{i}] missing 'sector' key"
        assert "loss_usd" in fi, f"[{scenario_id}] financial[{i}] missing 'loss_usd' key"


@skip_if_no_deps
@pytest.mark.parametrize("scenario_id,severity,horizon", SCENARIOS)
def test_financial_not_dict(scenario_id: str, severity: float, horizon: int):
    """Explicit regression: financial must NOT be a dict.
    The old bug was setting financial = result.get('financial_impact', {})
    which returned {'total_loss_usd': ..., 'top_entities': [...], ...}"""
    params = ScenarioCreate(
        scenario_id=scenario_id,
        severity=severity,
        horizon_hours=horizon,
    )
    result = execute_run(params)
    financial = result.get("financial")

    assert not isinstance(financial, dict), (
        f"[{scenario_id}] financial must not be a dict — "
        "dict cannot be .reduce()d in JavaScript. "
        "Use financial_list (top_entities array) instead."
    )
