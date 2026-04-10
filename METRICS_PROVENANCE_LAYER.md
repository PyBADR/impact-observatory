# Metrics Provenance Layer — Architecture Brief

**Stage 85 | Explainability + Factor Decomposition**
**Status:** Production-ready | **Tests:** 33 passed | **Suite total:** 352 passed, 5 skipped

---

## 1. Architecture Decision

The Metrics Provenance Layer (Stage 85) sits between the Decision Trust Layer (Stage 80) and the Validation Contract Layer. It exposes **why** the system computed each number, **what drove** it, **how uncertain** it is, **what data** backs it, and **why each decision** was recommended.

**Layer:** Governance → Explainability sub-layer
**Justification:** GCC institutional clients (CROs, regulators) cannot accept black-box numbers. Every metric must be traceable to its formula, factors, and data basis. This layer provides the last-mile product trust surface before launch.

---

## 2. Five Engines

| Engine | File | Purpose | Output count |
|--------|------|---------|--------------|
| MetricProvenanceEngine | `provenance_engine.py` | Why this number, what computed it | 10 metrics |
| FactorBreakdownEngine | `factor_engine.py` | Top drivers for each metric | 5+ breakdowns |
| MetricRangeEngine | `range_engine.py` | Uncertainty bands, not false-precision | 8 ranges |
| DecisionReasoningEngine | `reasoning_engine.py` | Why this decision, why this rank | per-decision |
| DataBasisEngine | `basis_engine.py` | Data period, calibration, freshness | 9 bases |

All engines are pure functions: `(run_result: dict) → list[dict]`. No side effects, no state, no external calls.

---

## 3. Data Flow

```
SimulationEngine.run()
  ↓ run_result dict (Stages 1-80)
run_provenance_pipeline(run_result)
  ├── build_metric_provenance()    → 10 provenance records
  ├── build_factor_breakdowns()    → 5+ breakdown records
  ├── build_metric_ranges()        → 8 range records
  ├── build_decision_reasonings()  → N reasoning records
  └── build_data_bases()           → 9 basis records
  ↓
ProvenanceLayerResult (frozen dataclass)
  ↓
response["provenance_layer"] = result.to_dict()
  ↓
5 API endpoints → Pydantic response models → Frontend TypeScript types
```

---

## 4. Schema / Contract

### MetricProvenance
- `metric_name` (str): Machine identifier
- `metric_name_ar` (str): Arabic display name
- `metric_value` (float): Computed value
- `unit` (str): USD, score [0-1], day, hours
- `formula` (str): Exact formula string
- `source_basis` (str): Where the data comes from
- `model_basis` (str): Which model produced it
- `contributing_factors` (list): Factor name, value, weight, description (EN/AR)
- `data_recency` (str): Freshness statement
- `confidence_notes` (str): Limitations and caveats

### MetricFactorBreakdown
- `factors` (list): Each with `contribution_value`, `contribution_pct`, `rationale_en/ar`
- `factors_sum` (float): Must equal sum of factor contributions
- `coverage_pct` (float): Sum/metric_value × 100 (validates coherence)

### MetricRange
- `min_value`, `expected_value`, `max_value`: Uncertainty band
- `confidence_band` (str): Human-readable band (e.g., "±18%")
- `reasoning_en/ar`: Why this width

### DecisionReasoning
- `why_this_decision_en/ar`: Trigger explanation
- `why_now_en/ar`: Time-to-act vs time-to-breach, urgency, regime
- `why_this_rank_en/ar`: Ranking score, crisis boost, feasibility penalty
- `trust_link_en`: Trust level, execution mode, override info
- `tradeoff_summary_en`: Cost, feasibility, conditional flags

### DataBasis
- `historical_basis_en/ar`: Analog event and period
- `scenario_basis_en/ar`: Scenario type, severity, well-known flag
- `calibration_basis_en/ar`: Source, period, model type, formula
- `freshness_flag`: CALIBRATED | SIMULATED | DERIVED | PARAMETRIC
- `freshness_weak` (bool): True if confidence in basis is low
- `analog_relevance` (float): 0.0–1.0

---

## 5. API Surface

| Endpoint | Method | Permission | Response Model |
|----------|--------|-----------|---------------|
| `/api/v1/runs/{run_id}/metrics-provenance` | GET | `run:read` | MetricsProvenanceResponse |
| `/api/v1/runs/{run_id}/factor-breakdown` | GET | `run:read` | FactorBreakdownResponse |
| `/api/v1/runs/{run_id}/metric-ranges` | GET | `run:read` | MetricRangesResponse |
| `/api/v1/runs/{run_id}/decision-reasoning` | GET | `run:explanation` | DecisionReasoningResponse |
| `/api/v1/runs/{run_id}/data-basis` | GET | `run:read` | DataBasisResponse |

All endpoints support on-the-fly computation for legacy runs (no `provenance_layer` in stored result). New runs pre-compute at Stage 85 in the orchestrator.

---

## 6. Uncertainty Model

Base uncertainty width:
```
base_width = 0.15 + 0.25 × |severity - 0.5| + 0.10 × (1 - confidence)
```

Per-metric multipliers:
- `total_loss_usd`: 1.2× (losses have wider tails), asymmetric upside 1.5×
- `unified_risk_score`: 0.8× (composite dampens noise)
- `propagation_score`: 0.6× (deterministic on fixed graph)
- `confidence_score`: ±8% (self-referential, narrow)
- `banking/insurance_stress`: 0.9× (sector models)
- `event_severity`: ±5% (deterministic from scenario params)
- `peak_day`: ±30% range, capped to horizon

**Trade-off:** Wider bands = more honest but less actionable. The asymmetric upside on losses (1.5×) reflects real GCC tail risk — systemic contagion amplifies losses nonlinearly.

---

## 7. Historical Analog Catalog

11 scenarios have explicit historical analogs:

| Scenario | Analog Event | Period | Relevance |
|----------|-------------|--------|-----------|
| hormuz_chokepoint | Tanker War / 2019 incidents | 1984-88 / Jun-Sep 2019 | 82% |
| saudi_oil_shock | Abqaiq-Khurais drone attack | Sep 2019 | 88% |
| uae_banking_crisis | Dubai World debt crisis | Nov 2009 – Mar 2010 | 78% |
| gcc_cyber_attack | Shamoon attack | Aug 2012 / Jan 2017 | 72% |
| qatar_lng_disruption | GCC diplomatic blockade | Jun 2017 – Jan 2021 | 75% |
| red_sea_instability | Houthi shipping attacks | Nov 2023 – present | 91% |

Scenarios without analogs get `freshness_flag: PARAMETRIC` and `freshness_weak: true`.

---

## 8. Factor Decomposition Coherence

Every breakdown satisfies:
```
Σ(factor.contribution_value) ≈ factors_sum
coverage_pct = (factors_sum / metric_value) × 100
```

Tested in `test_factors_sum_coherently` — tolerance < 0.01.

Total loss splits:
- By type: direct (60%) + indirect (28%) + systemic (12%) = 100%
- By sector: energy (30%) + maritime (20%) + banking (18%) + insurance (10%) + logistics (8%) + fintech (6%) + infrastructure (5%) + government (2%) + healthcare (1%) = 100%

URS factors: event_severity (g1=0.35) + exposure (g2=0.10) + stress (g3=0.15) + propagation (g4=0.30) + loss_severity (g5=0.10)

---

## 9. Implementation Sequence

| Step | File | Stage |
|------|------|-------|
| 1 | `backend/src/metrics_provenance/provenance_engine.py` | Engine 1 |
| 2 | `backend/src/metrics_provenance/factor_engine.py` | Engine 2 |
| 3 | `backend/src/metrics_provenance/range_engine.py` | Engine 3 |
| 4 | `backend/src/metrics_provenance/reasoning_engine.py` | Engine 4 |
| 5 | `backend/src/metrics_provenance/basis_engine.py` | Engine 5 |
| 6 | `backend/src/metrics_provenance/pipeline.py` | Pipeline chain |
| 7 | `backend/src/metrics_provenance/__init__.py` | Package exports |
| 8 | `backend/src/schemas/provenance_models.py` | Pydantic models |
| 9 | `backend/src/api/v1/provenance.py` | 5 API routes |
| 10 | `backend/src/services/run_orchestrator.py` | Stage 85 wiring |
| 11 | `backend/src/main.py` | Router registration |
| 12 | `frontend/src/types/provenance.ts` | TypeScript contracts |
| 13 | `frontend/src/lib/provenance-api.ts` | API client |
| 14 | `backend/tests/test_provenance_layer.py` | 33 contract tests |

---

## 10. Risk Register

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|-----------|
| Provenance engine error blocks run | LOW | HIGH | try/except in pipeline — all 5 engines fail independently, errors logged |
| Factor sums don't match metric | LOW | MEDIUM | Tested: `factors_sum_coherently` assertion with 0.01 tolerance |
| Historical analog stale | MEDIUM | LOW | `analog_relevance` score + `freshness_weak` flag surface this |
| Range too wide for executive action | MEDIUM | MEDIUM | Width formula is deterministic — adjustable via severity/confidence inputs |
| Arabic translations incomplete | MEDIUM | LOW | All engines produce `_ar` fields; basis engine uses bilingual templates |
| Legacy runs lack provenance_layer | HIGH | LOW | API computes on-the-fly via `_get_provenance_data()` fallback |

---

## 11. Observability Hooks

- `stage_timings["provenance_layer"]`: Execution time in ms (logged via `_log_stage`)
- `pipeline_meta.integrity_hash`: SHA-256 of output counts — verifies completeness
- `pipeline_meta.engines_executed / engines_failed`: Health signal
- `pipeline_meta.errors`: Detailed error messages per failed engine
- `pipeline_meta.elapsed_ms`: Total provenance computation time
- All 5 API endpoints inherit the global `observability_middleware` (X-Duration-Ms header)

---

## 12. Frontend Consumption Plan

### TypeScript Types
`frontend/src/types/provenance.ts` — 7 interfaces + 1 type alias:
- `ContributingFactor`, `MetricProvenance`, `MetricsProvenanceResponse`
- `FactorContribution`, `MetricFactorBreakdown`, `FactorBreakdownResponse`
- `MetricRange`, `MetricRangesResponse`
- `DecisionReasoning`, `DecisionReasoningResponse`
- `DataBasis`, `DataBasisResponse`
- `FreshnessFlag` type alias

### API Client
`frontend/src/lib/provenance-api.ts` — 5 typed fetch wrappers:
- `fetchMetricsProvenance(runId)` → metric-level provenance
- `fetchFactorBreakdown(runId)` → driver decomposition
- `fetchMetricRanges(runId)` → uncertainty bands
- `fetchDecisionReasoning(runId)` → decision explanations
- `fetchDataBasis(runId)` → data freshness assessment

### Recommended UI Components
1. **MetricProvenanceCard** — show formula, factors, source for any KPI
2. **FactorWaterfallChart** — stacked bar showing factor contributions
3. **UncertaintyBandOverlay** — min/expected/max on any metric chart
4. **DecisionReasoningPanel** — three-why card per decision
5. **DataFreshnessIndicator** — badge: CALIBRATED (green), SIMULATED (blue), PARAMETRIC (amber), DERIVED (gray)
6. **AnalogTimelineWidget** — historical analog with relevance score

---

## 13. Decision Gate

**What must be true before launch readiness review:**

- [x] All 5 engines produce valid output for all 15+ scenarios
- [x] Factor breakdowns sum coherently (tolerance < 0.01)
- [x] Range engine: min ≤ expected ≤ max for all metrics
- [x] Pipeline handles engine failures independently (no cascade)
- [x] Pydantic models validate against engine output (5/5 models)
- [x] 33 contract tests passing (7 test classes)
- [x] Full regression: 352 passed, 5 skipped, 0 failures
- [x] TypeScript contracts match Pydantic models (0 new TS errors)
- [x] API endpoints wired in main.py with RBAC enforcement
- [x] Stage 85 integrated in run_orchestrator.py
- [x] Legacy run fallback (on-the-fly computation) working
- [x] SHA-256 integrity hash on pipeline output
- [x] Arabic bilingual output on all text fields

**Next phase:** Frontend component implementation using the 6 recommended UI widgets above.
