# Data Trust Audit Layer — v1.0.0

**Date:** 2026-04-15
**Branch:** `feature/data-trust-audit-layer-v1`
**Status:** Implemented — additive layer, zero UI changes, zero pipeline changes

---

## 1. Purpose

The Data Trust Audit Layer provides transparency about **where scenario numbers come from**, **how fresh they are**, and **whether any live data is connected**. It ensures that:

- No output is presented as "live intelligence" when it comes from static configuration.
- Every scenario value can be traced back to a declared data source.
- Confidence scores reflect actual data quality, not aspirational targets.
- Static fallback values are explicitly labeled as such.

---

## 2. Current State: Everything Is Static

**All scenario values are static/config-based.** There are no live data feeds connected to the simulation pipeline today.

| What | Where | Status |
|------|-------|--------|
| Formula weights (ES, LSI, ISI, URS, Conf) | `backend/src/config.py` | Static. Expert-calibrated. |
| Scenario parameters (base_loss, peak_day, recovery) | `backend/src/simulation_engine.py` SCENARIO_CATALOG | Static. 20 scenarios. |
| GCC node topology (42 nodes) | `backend/src/simulation_engine.py` GCC_NODES | Static. |
| Sector coefficients (alpha, theta, loss allocation) | `backend/src/config.py` | Static. |
| Scenario taxonomy (type mapping) | `backend/src/config.py` SCENARIO_TAXONOMY | Static. |
| Risk thresholds (URS bands) | `backend/src/config.py` RISK_THRESHOLDS | Static. |
| Trust sector data completeness | `backend/src/config.py` TRUST_SECTOR_DATA_COMPLETENESS | Static. Expert estimates. |
| Adjacency graph (contagion paths) | `backend/src/simulation_engine.py` GCC_ADJACENCY | Static. |
| Frontend briefing narratives | `frontend/src/lib/scenarios.ts` | Static. Analyst-written. |

### External Connectors (Implemented, NOT Connected)

| Connector | File | Data It Would Provide | Status |
|-----------|------|----------------------|--------|
| EIA (U.S. Energy Information Administration) | `backend/src/data_foundation/connectors/eia.py` | Crude oil prices, production volumes | Implemented, not wired |
| CBK (Central Bank of Kuwait) | `backend/src/data_foundation/connectors/cbk.py` | Interest rates, money supply | Implemented, not wired |
| IMF (International Monetary Fund) | `backend/src/data_foundation/connectors/imf.py` | GDP, inflation, fiscal balance | Implemented, not wired |
| Maritime AIS | `backend/src/connectors/maritime_adapter.py` | Vessel traffic, port utilization | Skeleton only |

**None of these connectors feed into the simulation engine.** They exist as infrastructure for future integration.

---

## 3. What Is Dynamic (Scenario-Driven, Not Live)

The simulation engine produces **different outputs for different scenarios** using a deterministic 17-stage pipeline. The numbers "move" because:

1. **Severity input** (0.01–1.0) is set per scenario run.
2. **Shock nodes** differ per scenario (e.g., Hormuz vs. Saudi Aramco).
3. **Propagation** spreads through the adjacency graph deterministically.
4. **Sector exposure** is computed from SECTOR_ALPHA × severity × connectivity.
5. **Financial loss** is computed from base_loss × sector_allocation × theta × impact_factor.
6. **Stress indices** (LSI, ISI) are formula-driven from exposure and severity.
7. **Risk classification** maps URS to NOMINAL/LOW/GUARDED/ELEVATED/HIGH/SEVERE.

**This is simulation, not live intelligence.** The same inputs always produce the same outputs.

---

## 4. What Is Future Live (Not Implemented)

These data sources would enable real-time scenario calibration if connected:

| Future Source | Type | What It Would Change |
|--------------|------|---------------------|
| Brent Crude Futures (ICE) | Market | Energy scenario base_loss calibration |
| OPEC Monthly Report | Government | Oil production scenario parameters |
| AIS Maritime Traffic | API | Maritime scenario severity validation |
| GCC Central Bank Reports | Government | Banking stress model inputs |
| CBUAE/SAMA Regulatory Data | Government | Trust sector data completeness |
| Reuters/Bloomberg Feeds | Market | Real-time severity adjustment |

**None of these are planned for v1.** This section exists to document the path forward.

---

## 5. How Numbers Move Today

```
User selects scenario (e.g., "Hormuz Chokepoint Disruption")
    │
    ├─ SCENARIO_CATALOG provides: base_loss=$3.2B, peak_day=3, recovery=21 days
    │   └─ Source: STATIC (expert estimate, last updated 2026-04-10)
    │
    ├─ Severity: 0.72 (from scenario briefing)
    │   └─ Source: STATIC (analyst-written)
    │
    ├─ Shock nodes: ["hormuz", "shipping_lanes"]
    │   └─ Source: STATIC (GCC_NODES topology)
    │
    ├─ Stage 1-17: SimulationEngine.run()
    │   ├─ Event severity: Es = w1*I + w2*D + w3*U + w4*G
    │   │   └─ Weights: STATIC (config.py ES_W1..W4)
    │   ├─ Sector exposure: alpha_j * Es * V_j * C_j
    │   │   └─ alpha_j: STATIC (config.py SECTOR_ALPHA)
    │   ├─ Propagation: X_(t+1) = beta*P*X_t + (1-beta)*X_t + S_t
    │   │   └─ beta: STATIC (config.py PROP_BETA=0.65)
    │   ├─ Financial loss: base_loss * allocation * theta * impact_factor
    │   │   └─ All multipliers: STATIC (config.py)
    │   └─ Risk level: URS mapped to threshold bands
    │       └─ Thresholds: STATIC (config.py RISK_THRESHOLDS)
    │
    └─ Output: SimulateResponse (16+ fields, all deterministic)
        └─ Source: INTERNAL (computed from static inputs)
```

**Every number in the output is traceable to config.py or SCENARIO_CATALOG.**

---

## 6. What Sources Are Needed (Future Roadmap)

To move from "scenario simulation" to "intelligence platform," these sources are needed:

### Priority 1 — Energy Calibration
- **Brent Crude Futures**: Daily. Would adjust base_loss_usd for energy scenarios.
- **OPEC Production Data**: Monthly. Would validate Saudi/Kuwait/Qatar scenario parameters.

### Priority 2 — Maritime Validation
- **AIS Vessel Traffic**: Daily. Would validate Hormuz/port scenario severity.
- **Port Throughput Data**: Weekly. Would calibrate port_closure scenario recovery times.

### Priority 3 — Financial Stress
- **GCC Interbank Rates**: Daily. Would adjust LSI model inputs.
- **CDS Spreads (GCC Sovereigns)**: Daily. Would calibrate sovereign stress scenarios.

### Priority 4 — Cyber/Infrastructure
- **CERT Advisories**: As-published. Would validate cyber scenario severity.
- **Grid Utilization Data**: Weekly. Would calibrate power grid scenario.

---

## 7. How to Validate Scenario Outputs

### Step 1: Check Provenance
```python
from src.data_trust import build_provenance_for_scenario
from src.simulation_engine import SCENARIO_CATALOG

entry = SCENARIO_CATALOG["hormuz_chokepoint_disruption"]
records = build_provenance_for_scenario("hormuz_chokepoint_disruption", entry)

for r in records:
    print(f"{r.value_name}: {r.current_value}")
    print(f"  Source: {r.source_id}")
    print(f"  Static fallback: {r.is_static_fallback}")
    print(f"  Confidence: {r.confidence_score}")
```

### Step 2: Check Trust Score
```python
from src.data_trust import compute_trust_score

score = compute_trust_score(
    scenario_id="hormuz_chokepoint_disruption",
    base_loss_usd=3_200_000_000,
    sectors_affected=["energy", "maritime", "banking"],
)

print(f"Raw base loss: ${score.raw_base_loss_usd:,.0f}")
print(f"Adjusted loss: ${score.adjusted_loss_usd:,.0f}")
print(f"Static fallback: {score.is_static_fallback}")
print(f"Source confidence: {score.source_confidence}")
print(f"Freshness penalty: {score.freshness_penalty}")
```

### Step 3: Run Audit
```python
from src.data_trust import run_data_trust_audit
from src.data_trust.audit_reviewer import format_audit_report

findings = run_data_trust_audit()
print(format_audit_report(findings))
```

### Step 4: Check Registry
```python
from src.data_trust.source_registry import registry_summary

summary = registry_summary()
print(f"Total sources: {summary['total_sources']}")
print(f"Live connected: {summary['live_connected_count']}")
print(f"All static fallback: {summary['all_static_fallback']}")
```

---

## 8. Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/src/data_trust/__init__.py` | ~55 | Package exports |
| `backend/src/data_trust/source_registry.py` | ~260 | Data Source Registry (15 sources) |
| `backend/src/data_trust/scenario_provenance.py` | ~170 | Scenario Data Provenance builder |
| `backend/src/data_trust/scoring.py` | ~200 | Trust-weighted scoring (pure function) |
| `backend/src/data_trust/audit_reviewer.py` | ~280 | AI Code Reviewer audit scanner |
| `backend/tests/test_data_trust_layer.py` | ~320 | 42 contract tests |
| `frontend/src/types/data-trust.ts` | ~110 | TypeScript types (mirrors Python models) |
| `docs/DATA_TRUST_LAYER.md` | this file | Documentation |

**Files NOT modified:** Zero existing files changed. This is a purely additive layer.

---

## 9. Safe Fallback Rule

```
IF live/source data is missing:
  → use static scenario value (from SCENARIO_CATALOG)
  → mark output as is_static_fallback = true
  → show freshness_status = "unknown"
  → NEVER pretend it is live
```

This rule is enforced by:
1. `source_registry.get_connected_live_sources()` returns `[]` (no live sources)
2. `scenario_provenance.build_provenance_for_scenario()` marks all records as `is_static_fallback=True`
3. `scoring.compute_trust_score()` sets `is_static_fallback=True` when no live sources exist
4. `audit_reviewer.run_data_trust_audit()` flags any "live" wording as CRITICAL severity

---

## 10. Decision Gate — What Must Be True Before Next Phase

Before connecting any live data source to the pipeline:

1. **Source must be registered** in `DATA_SOURCE_REGISTRY` with accurate metadata
2. **Provenance records** must be updated to reflect the live source
3. **Freshness monitoring** must be active (stale detection)
4. **Fallback path** must be tested — if live source fails, static value must be used
5. **Confidence calibration** must be validated against historical data
6. **Audit must pass** — no CRITICAL findings related to the new source
7. **Feature flag** must gate any UI exposure of live-sourced values
