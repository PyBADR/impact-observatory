# Impact Observatory | مرصد الأثر — Claude Code Setup

## Project Overview

9-layer deterministic GCC financial simulation engine. 43 nodes, 15 scenarios, 17-stage pipeline.

- **Frontend**: Next.js 15 + React 19 + TypeScript — deployed on Vercel
- **Backend**: FastAPI + Python 3.12 + Pydantic v2 — deployed on Railway
- **Repo**: https://github.com/PyBADR/impact-observatory

## Strict Rules

- Work ONLY inside this repository (`/deevo-sim/`). Never touch AI Fitness Mirror.
- Fix root causes, not symptoms. No hacky defensive patches.
- Backend contracts are the source of truth — TypeScript types must match Pydantic models.
- All formula weights live in `backend/src/config.py` — never hardcode in engine files.

---

## Preview Servers

| Service | Command | URL |
|---|---|---|
| **Frontend** | `npm run dev` (in `frontend/`) | http://localhost:3000 |
| **Backend** | `.venv/bin/uvicorn src.main:app --reload` (in `backend/`) | http://localhost:8000 |
| **API Docs** | _(backend must be running)_ | http://localhost:8000/docs |
| **Health** | _(backend must be running)_ | http://localhost:8000/health |

---

## Quick Start (Local Development)

```bash
# 1. Backend — first time only
cd backend
/opt/homebrew/bin/python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # edit .env if needed

# 2. Backend — every time
cd backend
.venv/bin/uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

# 3. Frontend — first time only
cd frontend
npm install

# 4. Frontend — every time
cd frontend
npm run dev
```

Both servers run simultaneously. Frontend at :3000 proxies API calls to backend at :8000.

---

## Architecture

```
simulation_engine.py        ← 17-stage pipeline (source of truth)
    ↓
services/run_orchestrator.py ← transforms & persists result
    ↓
api/v1/runs.py              ← HTTP routes + Pydantic validation gate
    ↓
simulation_schemas.py        ← RunResult schema (must match frontend types)
    ↓
frontend/src/types/observatory.ts ← TypeScript interfaces (aligned to Pydantic)
```

**Layer ownership (CODE_GRAPH.md):**
- `config.py` — all formula constants
- `risk_models.py` — all math formulas
- `physics_intelligence_layer.py` — all physics
- `main.py` / `api/` — never import math modules directly

---

## Key Files

| File | Purpose |
|---|---|
| `backend/src/simulation_engine.py` | Core 17-stage simulation (1100+ lines) |
| `backend/src/simulation_schemas.py` | Pydantic response models — source of type truth |
| `backend/src/config.py` | All formula weights + constants |
| `backend/src/services/run_orchestrator.py` | Pipeline + persistence |
| `backend/src/api/v1/runs.py` | Main API routes (71 total) |
| `backend/src/api/v1/nodes.py` | GET /api/v1/nodes — GCC node registry (42 nodes, lat/lng for globe) |
| `frontend/src/types/observatory.ts` | TypeScript interfaces |
| `frontend/src/lib/api.ts` | API client |
| `frontend/src/hooks/use-api.ts` | React data hooks |
| `backend/tests/test_pipeline_contracts.py` | 113 contract tests |
| `backend/tests/test_api_endpoints.py` | 27 API endpoint tests |

---

## Environment Variables

Copy `backend/.env.example` → `backend/.env` for local dev.
Copy `.env.example` → `.env` for root-level (docker compose).

Frontend reads from `frontend/.env.local` (already present).

**Required for production:**
- `API_KEY` — strong random key (`openssl rand -hex 32`)
- `JWT_SECRET_KEY` — override the dev default
- `POSTGRES_PASSWORD`, `NEO4J_PASSWORD` — strong passwords

**Optional (system works without them):**
- `ACLED_API_KEY`, `AISSTREAM_API_KEY`, `OPENSKY_USERNAME` — real-time data feeds
- `NEXT_PUBLIC_MAPBOX_TOKEN`, `NEXT_PUBLIC_CESIUM_TOKEN` — map visualization

---

## Running Tests

```bash
cd backend

# All tests
.venv/bin/python -m pytest tests/ -v --tb=short

# Contract tests only (fast, 113 tests)
.venv/bin/python -m pytest tests/test_pipeline_contracts.py -v

# API endpoint tests (requires no external services)
.venv/bin/python -m pytest tests/test_api_endpoints.py -v
```

TypeScript check:
```bash
cd frontend
npx tsc --noEmit
```

---

## Deployment

- **Frontend** → Vercel auto-deploys on push to `main`
  - URL: https://deevo-sim.vercel.app
  - Config: `vercel.json` + `frontend/.env.production`

- **Backend** → Railway auto-deploys on push to `main`
  - Config: `railway.toml` + `Dockerfile.backend`
  - Entry: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
  - Health: `GET /health`

---

## Scenario Catalog (15 scenarios)

| ID | Description |
|---|---|
| `hormuz_chokepoint_disruption` | Strait of Hormuz partial blockage |
| `hormuz_full_closure` | Complete Hormuz closure |
| `saudi_oil_shock` | Saudi Aramco production shock |
| `uae_banking_crisis` | UAE banking sector stress |
| `gcc_cyber_attack` | Regional cyber infrastructure attack |
| `qatar_lng_disruption` | Qatar LNG export disruption |
| `bahrain_sovereign_stress` | Bahrain fiscal/sovereign stress |
| `kuwait_fiscal_shock` | Kuwait oil revenue shock |
| `oman_port_closure` | Oman Salalah/Sohar port closure |
| `red_sea_trade_corridor_instability` | Red Sea shipping disruption |
| `energy_market_volatility_shock` | GCC energy price shock |
| `regional_liquidity_stress_event` | Cross-border liquidity stress |
| `critical_port_throughput_disruption` | Multi-port throughput failure |
| `financial_infrastructure_cyber_disruption` | Financial system cyber attack |
| `iran_regional_escalation` | Regional geopolitical escalation |

---

## Risk Levels (URS thresholds)

| Level | URS Range |
|---|---|
| NOMINAL | < 0.20 |
| LOW | 0.20 – 0.35 |
| GUARDED | 0.35 – 0.50 |
| ELEVATED | 0.50 – 0.65 |
| HIGH | 0.65 – 0.80 |
| SEVERE | ≥ 0.80 |
