# Impact Observatory — Architecture Reference
## Model v2.1.0 | April 2026

---

## 10-Layer Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     IMPACT OBSERVATORY  |  مرصد الأثر                       │
│                   Decision Simulation Engine — v2.1.0                        │
└─────────────────────────────────────────────────────────────────────────────┘

LAYER 1 — CONFIGURATION & SETTINGS
┌─────────────────────────────────────────────────────────────────────────────┐
│  src/core/config.py       Pydantic Settings (env-file, secrets, DSN)        │
│  src/config.py            Convenience re-export                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
LAYER 2 — UTILITIES
┌─────────────────────────────────────────────────────────────────────────────┐
│  src/utils.py             format_loss_usd, classify_stress, clamp,          │
│                           weighted_average, generate_run_id, now_utc,       │
│                           severity_label (EN+AR), risk_label_ar              │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
LAYER 3 — SCHEMAS
┌─────────────────────────────────────────────────────────────────────────────┐
│  src/schemas.py           Pydantic v2 models:                                │
│                           SimulateRequest, SimulateResponse,                 │
│                           DecisionPlanResponse, ExplainabilityResponse,      │
│                           HealthResponse, ScenarioListItem, ErrorResponse    │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
LAYER 4 — RISK MODELS (pure math, no I/O)
┌─────────────────────────────────────────────────────────────────────────────┐
│  src/risk_models.py       compute_event_severity                             │
│                           compute_sector_exposure                            │
│                           compute_propagation                                │
│                           compute_liquidity_stress   (Basel III)             │
│                           compute_insurance_stress   (IFRS-17)               │
│                           compute_financial_losses                           │
│                           compute_confidence_score                           │
│                           compute_unified_risk_score                         │
│                           classify_risk, RISK_THRESHOLDS                     │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
LAYER 5 — PHYSICS INTELLIGENCE LAYER
┌─────────────────────────────────────────────────────────────────────────────┐
│  src/physics_intelligence_layer.py                                           │
│                           compute_node_utilization                           │
│                           check_flow_conservation    (1% tolerance)          │
│                           compute_bottleneck_scores                          │
│                           propagate_shock_wave       (α=0.08, β=0.65)       │
│                           compute_recovery_trajectory                        │
│                           compute_congestion                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
LAYER 6 — FLOW MODELS
┌─────────────────────────────────────────────────────────────────────────────┐
│  src/flow_models.py       simulate_money_flow    ($42B/day GCC baseline)    │
│                           simulate_logistics_flow ($18B/day)                 │
│                           simulate_energy_flow   ($580M/day)                 │
│                           simulate_payment_flow  ($8B/day)                   │
│                           simulate_claims_flow   ($120M/day)                 │
│                           simulate_all_flows                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
LAYER 7 — DECISION LAYER
┌─────────────────────────────────────────────────────────────────────────────┐
│  src/decision_layer.py    build_decision_actions   (top-5 ranked)           │
│                           build_five_questions     (EN+AR)                   │
│                           compute_escalation_triggers                        │
│                           compute_monitoring_priorities                      │
│                           Priority = 0.25*U + 0.30*L + 0.20*R + 0.15*F     │
│                                    + 0.10*T                                  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
LAYER 8 — EXPLAINABILITY ENGINE
┌─────────────────────────────────────────────────────────────────────────────┐
│  src/explainability.py    build_causal_chain       (20 steps, bilingual)    │
│                           build_narrative          (template-based, no LLM) │
│                           compute_sensitivity      (±10%, ±20% perturbation) │
│                           compute_uncertainty_bands                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
LAYER 9 — SIMULATION PIPELINE ORCHESTRATOR
┌─────────────────────────────────────────────────────────────────────────────┐
│  src/simulation_engine.py SimulationEngine.run()   (17 stages)             │
│                           GCC_NODES        (42 nodes, real lat/lng)         │
│                           GCC_ADJACENCY    (directed graph, ~120 edges)     │
│                           SCENARIO_CATALOG (15 scenarios)                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                      ↓
LAYER 10 — API ROUTES
┌─────────────────────────────────────────────────────────────────────────────┐
│  src/api/routes/          FastAPI routers:                                   │
│    health.py              GET  /api/v1/health                                │
│    scores.py              GET  /api/v1/scores                                │
│    decision.py            POST /api/v1/decision                              │
│    graph.py               GET  /api/v1/graph                                 │
│    events.py              GET  /api/v1/events                                │
│  src/api/v1/              Versioned API:                                     │
│    runs.py                POST /api/v1/simulate + GET /api/v1/runs/{id}     │
│    auth.py                POST /api/v1/auth/token                            │
│  src/main.py              FastAPI application factory                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Module Map

```
backend/
├── src/
│   ├── simulation_engine.py        Layer 9 — pipeline orchestrator + GCC data
│   ├── physics_intelligence_layer.py  Layer 5 — physics computations
│   ├── flow_models.py              Layer 6 — flow simulation
│   ├── risk_models.py              Layer 4 — risk math
│   ├── decision_layer.py           Layer 7 — decision support
│   ├── explainability.py           Layer 8 — explainability + narratives
│   ├── schemas.py                  Layer 3 — Pydantic v2 models
│   ├── utils.py                    Layer 2 — utilities
│   ├── config.py                   Layer 1 — config re-export
│   ├── core/
│   │   ├── config.py               Primary settings (pydantic-settings)
│   │   ├── rbac.py                 Role-based access control
│   │   └── project.py              Project metadata
│   ├── api/
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── scores.py
│   │   │   ├── decision.py
│   │   │   ├── graph.py
│   │   │   └── events.py
│   │   └── v1/
│   │       ├── runs.py             /simulate + /runs/{id}
│   │       └── auth.py             /auth/token
│   ├── engines/
│   │   ├── math/                   Legacy math engines
│   │   ├── physics/                Legacy physics engines (flow_field, etc.)
│   │   ├── math_core/              Advanced math (calibration, decay, scoring)
│   │   └── scenario/               Scenario engine
│   ├── services/
│   │   ├── decision_service.py
│   │   ├── explainability_service.py
│   │   ├── run_orchestrator.py
│   │   ├── run_store.py
│   │   ├── auth_service.py
│   │   ├── data_feeds.py
│   │   └── pdf_export.py
│   ├── models/
│   │   └── orm.py                  SQLAlchemy ORM models
│   └── schemas/
│       └── decision.py             Domain-specific decision schemas
├── README.md
├── METHODOLOGY.md
├── API_REFERENCE.md
├── ARCHITECTURE.md
└── requirements.txt
```

---

## Data Flow

```
POST /api/v1/simulate
        │
        ▼
SimulateRequest (Pydantic validation)
        │
        ▼
SimulationEngine.run(scenario_id, severity, horizon_hours)
        │
        ├── Stage 1:  Resolve scenario from SCENARIO_CATALOG
        ├── Stage 2:  compute_event_severity()
        ├── Stage 3:  compute_sector_exposure()
        ├── Stage 4:  compute_propagation()          ← numpy matrix ops
        ├── Stage 5:  compute_liquidity_stress()     ← Basel III
        ├── Stage 6:  compute_insurance_stress()     ← IFRS-17
        ├── Stage 7:  compute_financial_losses()     ← quadratic loss model
        ├── Stage 8:  compute_unified_risk_score()   ← 6-component GPNLTU
        ├── Stage 9:  compute_confidence_score()
        ├── Stage 10: compute_node_utilization()     ← 42 GCC nodes
        ├── Stage 11: compute_bottleneck_scores()
        ├── Stage 12: propagate_shock_wave()         ← PDE discretised
        ├── Stage 13: compute_congestion()
        ├── Stage 14: compute_recovery_trajectory()
        ├── Stage 15: simulate_all_flows()           ← 5 flow types
        ├── Stage 16: build_decision_actions()
        │             build_five_questions()
        │             compute_escalation_triggers()
        │             compute_monitoring_priorities()
        └── Stage 17: build_causal_chain()
                      build_narrative()              ← bilingual, template
                      compute_sensitivity()
                      compute_uncertainty_bands()
                      Assemble 16-field output dict
                              │
                              ▼
                      SimulateResponse (Pydantic)
                              │
                              ▼
                      HTTP 200 JSON response
```

---

## GCC Graph — 42 Nodes

### Node Sectors

| Sector | Count | Key Nodes |
|--------|-------|-----------|
| Maritime | 7 | hormuz, shipping_lanes, dubai_port, abu_dhabi_port, dammam_port, salalah_port, kuwait_port |
| Energy | 6 | qatar_lng, saudi_aramco, adnoc, kuwait_oil, gcc_pipeline, oman_oil |
| Banking | 7 | uae_banking, saudi_banking, riyadh_financial, bahrain_banking, kuwait_banking, qatar_banking, difc |
| Insurance | 2 | gcc_insurance, reinsurance_hub |
| Fintech | 4 | gcc_fintech, uae_payment_rail, saudi_payment_rail, swift_gcc |
| Logistics | 3 | dubai_logistics, riyadh_logistics, oman_trade |
| Infrastructure | 5 | gcc_power_grid, uae_telecom, saudi_telecom, gcc_water_desalin, uae_real_estate |
| Government | 8 | uae_cbuae, sama, qcb, cbk, cbo, gcc_fsb, gcc_labour_market, saudi_sovereign_fund |
| Healthcare | 2 | gcc_labour_market, gcc_healthcare |

### Criticality Ranking

| Node | Criticality |
|------|-------------|
| Strait of Hormuz | 1.00 |
| Saudi Aramco | 0.98 |
| Qatar LNG | 0.96 |
| CBUAE / SAMA | 0.95 |
| DIFC | 0.93 |
| GCC Financial Stability Board | 0.90 |
| SWIFT GCC | 0.90 |
| GCC Shipping Lanes | 0.92 |
| UAE Banking | 0.92 |
| Saudi Banking | 0.90 |

---

## Execution Guarantees

- Deterministic: identical inputs always produce identical outputs
- Bounded: all outputs are clamped to valid ranges
- Complete: every run produces all 16 mandatory fields
- Fast: median execution time < 200ms on modern hardware
- Thread-safe: SimulationEngine is stateless; safe to call concurrently
- Validated: all outputs pass Pydantic v2 schema validation

---

## Technology Stack

| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI 0.115+ |
| Data Validation | Pydantic v2 |
| Math Engine | NumPy 1.26+ |
| Database | PostgreSQL 17 (async via asyncpg) |
| Graph Store | Neo4j 5 |
| Cache | Redis 7 |
| Auth | python-jose (JWT) |
| PDF Export | fpdf2 |
| Python | 3.11+ |
