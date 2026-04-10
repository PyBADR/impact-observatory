# Impact Observatory | مرصد الأثر

**Decision Simulation Engine for GCC Financial Stability**

> مرصد الأثر — محرك محاكاة القرار للاستقرار المالي في منطقة الخليج العربي

[![Model Version](https://img.shields.io/badge/model-v2.1.0-blue)](METHODOLOGY.md)
[![Python](https://img.shields.io/badge/python-3.11%2B-green)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-teal)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/license-Proprietary-red)](#license)

---

## Overview

Impact Observatory is a deterministic, physics-informed financial stress simulation engine
purpose-built for GCC stakeholders: central banks, systemically important financial institutions,
insurance supervisors, sovereign wealth funds, and critical infrastructure operators.

Given a scenario (e.g. Strait of Hormuz disruption, UAE banking crisis, GCC cyber attack) and a
severity parameter, the engine computes — in under 500ms — a complete 16-field decision-ready
output including financial loss projections (USD), sector stress indices, risk classification,
propagation chains, recovery trajectories, and bilingual (EN/AR) executive narratives.

**Key design principles:**
- No LLM dependency for any mathematical computation
- All outputs are deterministic for identical inputs
- Every projection is denominated in USD
- Every run produces all 16 mandatory output fields
- Full Basel III / IFRS-17 awareness in stress computations
- 42 real GCC nodes with verified geographic coordinates
- 15 calibrated scenarios (8 canonical + 7 extended)

---

## Architecture Overview

The engine consists of 10 computational layers:

```
Layer  1  Configuration & Settings         src/core/config.py
Layer  2  Utilities & Formatters           src/utils.py
Layer  3  Schemas (Pydantic v2)            src/schemas.py
Layer  4  Risk Models (pure math)          src/risk_models.py
Layer  5  Physics Intelligence Layer       src/physics_intelligence_layer.py
Layer  6  Flow Models                      src/flow_models.py
Layer  7  Decision Layer                   src/decision_layer.py
Layer  8  Explainability Engine            src/explainability.py
Layer  9  Simulation Engine (pipeline)     src/simulation_engine.py
Layer 10  API Routes                       src/api/routes/
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for the full module map and data flow.

---

## Quick Start

### 1. Install dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your PostgreSQL, Neo4j, and Redis credentials
```

### 3. Start the API server

```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```

### 4. Run a simulation

```bash
curl -X POST http://localhost:8000/api/v1/simulate \
  -H "Content-Type: application/json" \
  -d '{
    "scenario_id": "hormuz_chokepoint_disruption",
    "severity": 0.75,
    "horizon_hours": 336
  }'
```

---

## Key Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/simulate` | Run a full simulation |
| `GET`  | `/api/v1/scenarios` | List all 15 available scenarios |
| `GET`  | `/api/v1/runs/{run_id}` | Retrieve a past run by ID |
| `GET`  | `/api/v1/health` | System health check |
| `GET`  | `/api/v1/graph` | GCC node graph topology |
| `POST` | `/api/v1/decision` | Standalone decision plan |

See [API_REFERENCE.md](API_REFERENCE.md) for full documentation.

---

## Available Scenarios

### Canonical (8)
| ID | Description | Base Loss (USD) |
|----|-------------|-----------------|
| `hormuz_chokepoint_disruption` | Strait of Hormuz Disruption | $3.2B |
| `uae_banking_crisis` | UAE Banking System Stress | $1.8B |
| `gcc_cyber_attack` | GCC Critical Infrastructure Cyber Attack | $950M |
| `saudi_oil_shock` | Saudi Arabia Oil Supply Shock | $2.8B |
| `qatar_lng_disruption` | Qatar LNG Supply Disruption | $1.4B |
| `bahrain_sovereign_stress` | Bahrain Sovereign & Banking Stress | $600M |
| `kuwait_fiscal_shock` | Kuwait Fiscal & Oil Revenue Shock | $750M |
| `oman_port_closure` | Oman Port & Trade Route Closure | $420M |

### Extended (7)
| ID | Description | Base Loss (USD) |
|----|-------------|-----------------|
| `gcc_power_grid_failure` | GCC Power Grid Cascade Failure | $1.1B |
| `difc_financial_contagion` | DIFC Financial Contagion Event | $2.2B |
| `gcc_insurance_reserve_shortfall` | GCC Insurance Reserve Shortfall | $380M |
| `gcc_fintech_payment_outage` | GCC Fintech Payment System Outage | $680M |
| `saudi_vision_mega_project_halt` | Saudi Vision 2030 Mega-Project Halt | $1.6B |
| `gcc_sovereign_debt_crisis` | GCC Multi-Sovereign Debt Stress | $4.5B |
| `hormuz_full_closure` | Full Hormuz Closure (Extreme) | $8.5B |

---

## Model Version

**v2.1.0** — April 2026

See [METHODOLOGY.md](METHODOLOGY.md) for all equations, weights, and calibration notes.

---

## Output Fields (16)

Every simulation run returns these fields:

1. `run_id` — UUID hex
2. `scenario_id`, `model_version`, `severity`, `horizon_hours`, `time_horizon_days`, `generated_at`, `duration_ms`
3. `event_severity` — amplified severity [0–1]
4. `peak_day` — day of maximum stress
5. `confidence_score` — model confidence [0–1]
6. `financial_impact` — total/direct/indirect/systemic losses + top 10 entities
7. `sector_analysis` — per-sector exposure and stress
8. `propagation_score` + `propagation_chain` — 20-step contagion trace
9. `unified_risk_score` + `risk_level` — NOMINAL/LOW/GUARDED/ELEVATED/HIGH/SEVERE
10. `physical_system_status` + `bottlenecks` + `congestion_score` + `recovery_score` + `recovery_trajectory`
11. `banking_stress` + `insurance_stress` + `fintech_stress`
12. `flow_analysis` — 5 flow types (money, logistics, energy, payments, claims)
13. `explainability` — causal chain, bilingual narrative, sensitivity, uncertainty bands
14. `decision_plan` — 5 ranked actions, escalation triggers, monitoring priorities, Five Questions
15. `headline` — KPI card summary (total loss, peak day, affected entities, severity code)

---

## License

Copyright 2026 Deevo. All rights reserved.
This software is proprietary and confidential. Redistribution or use without
written permission from Deevo is strictly prohibited.
