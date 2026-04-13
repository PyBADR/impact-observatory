# Impact Observatory — Backend Railway Deployment Guide

## Service Architecture

The backend is a FastAPI application running on Uvicorn inside a Python 3.12-slim container. It connects to PostgreSQL (required), and optionally to Neo4j and Redis. The simulation engine runs entirely in-memory — no GPU, no ML model files, no external inference service.

```
Railway Container (Dockerfile.backend)
  └── uvicorn src.main:app --port $PORT
       ├── PostgreSQL (required) ← Railway plugin or external
       ├── Neo4j (optional) ← 5s timeout, non-fatal
       └── Redis (optional) ← 5s timeout, non-fatal
```

---

## 1. Service Deployment Checklist

### Railway Project Setup

| Step | Action | Verify |
|---|---|---|
| 1 | Create Railway project | [ ] |
| 2 | Connect GitHub repo (PyBADR/impact-observatory) | [ ] |
| 3 | Railway auto-detects `railway.toml` at repo root | [ ] |
| 4 | Confirm builder is `DOCKERFILE`, path is `Dockerfile.backend` | [ ] |
| 5 | Add PostgreSQL plugin to the project | [ ] |
| 6 | Confirm `DATABASE_URL` is auto-injected into service env | [ ] |
| 7 | Set all required environment variables (see Section 2) | [ ] |
| 8 | Deploy | [ ] |
| 9 | Confirm health check passes at `/health` | [ ] |
| 10 | Confirm deploy logs show "Application startup complete" | [ ] |

### Dockerfile Behavior

The container builds in this order:

1. `python:3.12-slim` base image
2. Install `build-essential` and `curl` (needed for numpy C extension compilation)
3. `pip install -r requirements.txt` (cached layer — only rebuilds when requirements.txt changes)
4. Copy `backend/` source into `/app`
5. Set `PYTHONPATH=/app` so `from src.main import app` resolves
6. Start: `uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000}`

Railway injects `PORT` at runtime. The container respects it via shell-form CMD.

### railway.toml Settings

```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile.backend"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300          # 5 minutes — allows for slow startup
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 3
```

The 300-second health check timeout accounts for the multi-stage startup sequence (see Section 4).

---

## 2. Environment Variable Checklist

### Critical — Must Set Before First Deploy

| Variable | Default | Production Value | Notes |
|---|---|---|---|
| `DATABASE_URL` | _(none)_ | Auto-injected by Railway PostgreSQL plugin | Format: `postgresql://user:pass@host:port/db`. The app converts to `postgresql+asyncpg://` automatically. |
| `API_KEY` | `""` (empty = all access) | `openssl rand -hex 32` | **SECURITY CRITICAL.** If empty, all endpoints are publicly accessible without authentication. |
| `JWT_SECRET_KEY` | `io-dev-secret-change-in-prod-2026` | `openssl rand -hex 32` | Used for JWT token signing. Default is insecure. |
| `APP_ENV` | `development` | `production` | Switches logging and debug behavior. |

### Important — Set For Full Functionality

| Variable | Default | Notes |
|---|---|---|
| `CORS_ORIGINS` | `http://localhost:3000,https://deevo-sim.vercel.app` | Comma-separated. Add custom domains here. Vercel preview URLs are auto-allowed by regex. |
| `POSTGRES_PASSWORD` | `changeme` | Only needed if not using `DATABASE_URL`. Railway plugin injects `DATABASE_URL` directly. |
| `NEO4J_URI` | `bolt://localhost:7687` | Set if Neo4j is provisioned. Leave default if not — app continues without it. |
| `NEO4J_PASSWORD` | `changeme` | Only if Neo4j is enabled. |
| `REDIS_URL` | `redis://localhost:6379/0` | Set if Redis is provisioned. App works without caching if absent. |

### Optional — External Data Feeds

| Variable | Purpose |
|---|---|
| `ACLED_API_KEY` + `ACLED_API_EMAIL` | Conflict event data feed |
| `AISSTREAM_API_KEY` | Vessel tracking (AIS) |
| `OPENSKY_USERNAME` + `OPENSKY_PASSWORD` | Flight tracking data |
| `FEED_REFRESH_MINUTES` | Data feed refresh interval (default: 15) |

### Optional — Visualization Tokens

| Variable | Purpose |
|---|---|
| `CESIUM_ION_TOKEN` | 3D globe rendering (backend-side) |
| `NEXT_PUBLIC_MAPBOX_TOKEN` | Mapbox (not used by backend, but config accepts it) |

### Do Not Set

| Variable | Why |
|---|---|
| `PORT` | Railway injects this automatically. Do not override. |
| `PYTHONPATH` | Set in Dockerfile. Do not override. |
| `DEBUG` | Leave `false` in production. Enables verbose SQL logging. |

---

## 3. Migration Run Order

### First Deploy (fresh database)

The application auto-creates all tables on startup via `Base.metadata.create_all()` in the lifespan function. No manual migration step is required for the first deploy.

However, for audit trail and schema versioning, run Alembic explicitly:

```bash
# From backend/ directory, with DATABASE_URL set
alembic upgrade head
```

This executes the single migration file:

| Migration | Tables Created | Description |
|---|---|---|
| `001_p2_data_foundation_tables` | 12 tables | Entity registry, events, macro indicators, rules, decision logs, audit trail, governance, evaluation, enforcement |

### ORM Model Import Order (for reference)

The lifespan function imports 7 ORM model modules before `create_all()`:

```
1. src.models.orm                           ← Core simulation models
2. src.models.action_tracking               ← Decision action lifecycle
3. src.models.enterprise                    ← Enterprise entity models
4. src.data_foundation.models.tables        ← Data foundation tables (df_*)
5. src.data_foundation.evaluation.orm_models ← Evaluation tracking
6. src.data_foundation.governance.orm_models ← Governance audit
7. src.data_foundation.enforcement.orm_models ← Enforcement records
```

All 7 modules must be imported before `create_all()` runs, or their tables will not be created.

### Subsequent Deploys (schema changes)

If ORM models change, either:

1. **Auto-create (development):** `create_all()` adds new tables but does NOT modify existing tables or add new columns to existing tables.
2. **Alembic migration (production):** Generate and apply a migration:

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### Migration Checklist

- [ ] PostgreSQL is reachable from Railway container
- [ ] `DATABASE_URL` is set and valid
- [ ] `alembic upgrade head` runs without errors (or `create_all()` succeeds on startup)
- [ ] All 12 `df_*` tables exist after migration
- [ ] Entity registry table has `entity_id`, `entity_name`, `entity_type`, `country`, `sector` columns

---

## 4. Health Check Checklist

### Startup Sequence (in order)

The application goes through 7 stages before the `/health` endpoint becomes available:

| Stage | Action | Blocking? | Fatal? | Typical Time |
|---|---|---|---|---|
| 1 | `init_state()` — load GCC graph, nodes, edges, seed data | Yes | Yes | 2–5s |
| 2 | SimulationEngine warmup — first-call JIT overhead | No | No | 3–8s |
| 3 | Data feeds refresh — ACLED, AIS, OpenSky | No | No | 5–30s (async) |
| 4 | Neo4j connection | No | No | 0–5s (5s timeout) |
| 5 | Redis connection | No | No | 0–5s (5s timeout) |
| 6 | PostgreSQL `create_all()` — create/verify all tables | Yes | Yes | 2–10s |
| 7 | Banking Intelligence seed — load entity store | No | No | 1–3s |

**Total startup time:** 15–60 seconds under normal conditions. The 300-second Railway health check timeout provides margin for database connection retries and cold PostgreSQL starts.

### Health Endpoint Behavior

```
GET /health → 200 OK
{
  "status": "ok",
  "service": "Impact Observatory",
  "version": "1.0.0"
}
```

**Current limitation:** The `/health` endpoint only confirms the FastAPI process is running. It does NOT verify database connectivity. A healthy response does not guarantee PostgreSQL/Neo4j/Redis are reachable.

### Health Check Verification

| Check | How to Verify | Pass Criteria |
|---|---|---|
| Process alive | `GET /health` | Returns 200 with `"status": "ok"` |
| PostgreSQL connected | `POST /api/v1/runs` with valid payload | Returns 201 (not 500 connection error) |
| SimulationEngine ready | `POST /simulate` with test payload | Returns 200 with simulation result |
| Neo4j connected (if enabled) | Check deploy logs for "Neo4j connected" | No "Neo4j timeout" warning in logs |
| Redis connected (if enabled) | Check deploy logs for "Redis connected" | No "Redis timeout" warning in logs |
| Data feeds active | Check deploy logs for feed refresh | No "feed refresh failed" warnings |

### Health Check Failure Scenarios

| Symptom | Cause | Fix |
|---|---|---|
| Health check times out (no 200 within 300s) | `init_state()` or `create_all()` hanging | Check PostgreSQL connectivity. Check Railway logs for import errors. |
| Health returns 200 but API calls return 500 | PostgreSQL unreachable after startup | Check `DATABASE_URL`. Verify PostgreSQL plugin is running. |
| Restart loop (3 retries then stops) | Fatal error in startup sequence | Check logs for Python import errors, missing dependencies, or database connection failures. |
| Health returns 200 but slow responses (>5s) | Pool exhaustion (30 connection limit reached) | Scale up PostgreSQL max_connections or reduce pool_size. |

---

## 5. API Smoke Test Checklist

Run against the Railway deployment URL after health check passes.

### Public Endpoints (no API key required)

| # | Request | Expected | Check |
|---|---|---|---|
| 1 | `GET /health` | 200, `{"status": "ok"}` | [ ] |
| 2 | `GET /version` | 200, model metadata JSON | [ ] |
| 3 | `POST /simulate` with `{"scenario_id": "hormuz_chokepoint_disruption", "severity": 0.5, "horizon_hours": 72}` | 200, simulation result JSON | [ ] |

### Protected Endpoints (require `X-API-Key` header)

| # | Request | Expected | Check |
|---|---|---|---|
| 4 | `GET /api/v1/scenarios` without API key | 401 or 403 | [ ] |
| 5 | `GET /api/v1/scenarios` with valid `X-API-Key` | 200, scenario list | [ ] |
| 6 | `GET /api/v1/nodes` with valid `X-API-Key` | 200, 43 GCC nodes with lat/lng | [ ] |
| 7 | `POST /api/v1/runs` with `X-API-Key` and `{"scenario_id": "hormuz_chokepoint_disruption", "severity": 0.7, "horizon_hours": 72}` | 201, run result | [ ] |
| 8 | `GET /api/v1/runs/{run_id}` with the run_id from step 7 | 200, full run data | [ ] |
| 9 | `GET /api/v1/runs/{run_id}/financial` | 200, financial impact data | [ ] |
| 10 | `GET /api/v1/runs/{run_id}/banking` | 200, banking stress data | [ ] |
| 11 | `GET /api/v1/runs/{run_id}/insurance` | 200, insurance stress data | [ ] |
| 12 | `GET /api/v1/runs/{run_id}/decision` | 200, decision plan | [ ] |
| 13 | `GET /api/v1/runs/{run_id}/explanation` | 200, explanation pack | [ ] |

### Cross-Origin Verification

| # | Test | Expected | Check |
|---|---|---|---|
| 14 | `OPTIONS /api/v1/scenarios` with `Origin: https://deevo-sim.vercel.app` | 200 with `Access-Control-Allow-Origin` header | [ ] |
| 15 | `OPTIONS /api/v1/scenarios` with `Origin: https://random-branch-xyz.vercel.app` | 200 (regex allows all `*.vercel.app`) | [ ] |
| 16 | `OPTIONS /api/v1/scenarios` with `Origin: https://evil.com` | No `Access-Control-Allow-Origin` header | [ ] |

### Performance Baseline

| # | Request | Acceptable | Check |
|---|---|---|---|
| 17 | `POST /simulate` (Hormuz scenario, 72h) | < 50ms | [ ] |
| 18 | `GET /api/v1/nodes` | < 100ms | [ ] |
| 19 | `POST /api/v1/runs` (full pipeline) | < 500ms | [ ] |
| 20 | Check `X-Duration-Ms` response header on any request | Present and numeric | [ ] |

### curl Commands for Quick Verification

```bash
# Set these first
RAILWAY_URL="https://deevo-cortex-production.up.railway.app"
API_KEY="your-production-api-key"

# 1. Health
curl -s "$RAILWAY_URL/health" | python3 -m json.tool

# 2. Public simulation
curl -s -X POST "$RAILWAY_URL/simulate" \
  -H "Content-Type: application/json" \
  -d '{"scenario_id":"hormuz_chokepoint_disruption","severity":0.5,"horizon_hours":72}' \
  | python3 -m json.tool

# 3. Auth check — should fail without key
curl -s -o /dev/null -w "%{http_code}" "$RAILWAY_URL/api/v1/scenarios"

# 4. Auth check — should succeed with key
curl -s "$RAILWAY_URL/api/v1/scenarios" \
  -H "X-API-Key: $API_KEY" | python3 -m json.tool

# 5. Full run pipeline
RUN_RESPONSE=$(curl -s -X POST "$RAILWAY_URL/api/v1/runs" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{"scenario_id":"hormuz_chokepoint_disruption","severity":0.7,"horizon_hours":72}')
echo "$RUN_RESPONSE" | python3 -m json.tool

# 6. Extract run_id and fetch sub-resources
RUN_ID=$(echo "$RUN_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['run_id'])")
curl -s "$RAILWAY_URL/api/v1/runs/$RUN_ID/financial" -H "X-API-Key: $API_KEY" | python3 -m json.tool
curl -s "$RAILWAY_URL/api/v1/runs/$RUN_ID/decision" -H "X-API-Key: $API_KEY" | python3 -m json.tool
```

---

## 6. Failure Recovery Checklist

### Scenario A: Deploy Fails (container won't build)

| Step | Action |
|---|---|
| 1 | Check Railway build logs for Python import errors or pip install failures |
| 2 | Verify `requirements.txt` has no conflicting versions |
| 3 | Check if `build-essential` is present in Dockerfile (required for numpy) |
| 4 | Test locally: `docker build -f Dockerfile.backend -t io-backend .` |
| 5 | If dependency conflict: pin the conflicting package version in requirements.txt |

### Scenario B: Container Starts but Health Check Fails (restart loop)

| Step | Action |
|---|---|
| 1 | Check Railway deploy logs — look for the last log line before restart |
| 2 | If "ModuleNotFoundError": missing dependency in requirements.txt |
| 3 | If "connection refused" on PostgreSQL: verify `DATABASE_URL` is set and PostgreSQL plugin is running |
| 4 | If "asyncpg" connection error: check that `DATABASE_URL` uses `postgresql://` scheme (app converts automatically) |
| 5 | If stuck at "Creating tables": PostgreSQL is reachable but schema creation is hanging — check for lock conflicts |
| 6 | If no logs at all: container is OOM-killed — check Railway memory allocation (recommend 512MB minimum) |

### Scenario C: Health Check Passes but API Returns 500

| Step | Action |
|---|---|
| 1 | Check the specific endpoint failing — is it PostgreSQL-dependent? |
| 2 | If "PoolTimeout": connection pool exhausted — reduce concurrent load or increase `pool_size` |
| 3 | If "relation does not exist": tables were not created — run `alembic upgrade head` or restart service |
| 4 | If "Neo4j driver not initialized": Neo4j connection timed out on startup — check Neo4j service status |
| 5 | If "Redis connection refused": Redis unavailable — check Redis plugin status (non-fatal, but caching disabled) |

### Scenario D: Intermittent 500 Errors Under Load

| Step | Action |
|---|---|
| 1 | Check `X-Duration-Ms` header — if > 5000ms, requests are queuing on connection pool |
| 2 | Monitor PostgreSQL connection count — if at 30 (20 pool + 10 overflow), pool is exhausted |
| 3 | Scale horizontally: add a second Railway replica |
| 4 | Scale vertically: increase PostgreSQL `max_connections` on the plugin settings |
| 5 | If Redis is connected, check cache hit rate — low hit rate means the cache TTLs may be too short |

### Scenario E: Database Corruption or Data Loss

| Step | Action |
|---|---|
| 1 | Railway PostgreSQL plugin has automatic daily backups |
| 2 | Check Railway dashboard → PostgreSQL plugin → Backups tab |
| 3 | Restore from the most recent backup before the corruption event |
| 4 | After restore, restart the backend service to re-initialize connection pool |
| 5 | Run the smoke test checklist (Section 5) to verify restored state |

### Scenario F: Need to Rollback a Bad Deploy

| Step | Action |
|---|---|
| 1 | Railway dashboard → Deployments tab → click on the previous successful deployment |
| 2 | Click "Redeploy" on the known-good deployment |
| 3 | If the rollback commit has a different schema: run `alembic downgrade -1` before redeploying |
| 4 | Verify health check passes on the rolled-back deployment |
| 5 | Investigate the failed deployment in a separate branch before re-attempting |

### Scenario G: Secret Rotation

| Step | Action |
|---|---|
| 1 | Generate new values: `openssl rand -hex 32` for API_KEY and JWT_SECRET_KEY |
| 2 | Update Railway environment variables (Dashboard → Variables) |
| 3 | Railway auto-redeploys on env var change |
| 4 | **API_KEY rotation**: notify all API consumers to update their key immediately |
| 5 | **JWT_SECRET_KEY rotation**: all existing JWT tokens are invalidated — users must re-authenticate |
| 6 | **DATABASE_URL rotation**: update PostgreSQL password in both the plugin and the env var |

---

## Quick Reference: Production Environment

```
Service:     deevo-cortex-production
Platform:    Railway
Builder:     Dockerfile (Dockerfile.backend)
Runtime:     Python 3.12-slim + Uvicorn
Port:        $PORT (Railway-injected)
Health:      GET /health (300s timeout, 3 retries)
Database:    Railway PostgreSQL plugin (auto-injected DATABASE_URL)
API Docs:    https://deevo-cortex-production.up.railway.app/docs
Repository:  https://github.com/PyBADR/impact-observatory
```
