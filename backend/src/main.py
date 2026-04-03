"""Impact Observatory | مرصد الأثر — FastAPI application entry point.

Decision Intelligence Platform for GCC Financial Markets.
Every output maps: Event → Math Models → Physics → Sector Stress → Decision

Architecture: 9-layer deterministic simulation engine
Model version: 2.1.0
"""

from contextlib import asynccontextmanager

from fastapi import APIRouter, Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from src.api.auth import require_api_key
from src.api.routes.conflicts import router as conflicts_router
from src.api.routes.decision import router as decision_router
from src.api.routes.events import router as events_router
from src.api.routes.flights import router as flights_router
from src.api.routes.graph import router as graph_router
from src.api.routes.health import router as health_router
from src.api.routes.incidents import router as incidents_router
from src.api.routes.insurance import router as insurance_router
from src.api.routes.scenarios import router as scenarios_router
from src.api.routes.scores import router as scores_router
from src.api.routes.vessels import router as vessels_router

# Impact Observatory v1 API
from src.api.v1.scenarios import router as v1_scenarios_router
from src.api.v1.runs import router as v1_runs_router
from src.api.v1.auth import router as v1_auth_router

from src.core.config import settings
from src.services.state import init_state


@asynccontextmanager
async def lifespan(app: FastAPI):
    import asyncio

    # ── Startup ──────────────────────────────────────────────────────────
    init_state()

    # Warm up simulation engine (imports + JIT-like first-call overhead)
    try:
        from src.simulation_engine import SimulationEngine, SCENARIO_CATALOG
        _warm = SimulationEngine()
        _warm.run("hormuz_chokepoint_disruption", severity=0.5, horizon_hours=24)
        print(f"✅ SimulationEngine v{SimulationEngine.MODEL_VERSION} ready "
              f"({len(SCENARIO_CATALOG)} scenarios)")
    except Exception as e:
        print(f"⚠️  SimulationEngine warmup skipped: {e}")

    # Real-time data feeds (non-blocking — falls back to seed data)
    try:
        from src.services.data_feeds import refresh_all_feeds
        from src.services.state import get_state
        asyncio.ensure_future(refresh_all_feeds(get_state()))
        print("📡 Data feeds initializing (ACLED/AIS/OpenSky)...")
    except Exception as e:
        print(f"⚠️  Data feeds skipped: {e}")

    # Optional databases (5 s timeout each — non-fatal)
    try:
        from src.db.neo4j import init_neo4j
        await asyncio.wait_for(init_neo4j(), timeout=5.0)
        print("✅ Neo4j connected")
    except Exception as e:
        print(f"⚠️  Neo4j skipped: {e}")

    try:
        from src.db.redis import init_redis
        await asyncio.wait_for(init_redis(), timeout=5.0)
        print("✅ Redis connected")
    except Exception as e:
        print(f"⚠️  Redis skipped: {e}")

    print("🚀 Impact Observatory | مرصد الأثر — ready")
    yield

    # ── Shutdown ─────────────────────────────────────────────────────────
    for closer, name in [
        ("src.db.neo4j", "close_neo4j"),
        ("src.db.redis", "close_redis"),
    ]:
        try:
            import importlib
            mod = importlib.import_module(closer)
            await getattr(mod, name)()
        except Exception:
            pass


# ── Application ───────────────────────────────────────────────────────────
app = FastAPI(
    title="Impact Observatory | مرصد الأثر",
    description=(
        "Decision Simulation Engine for GCC Financial Markets.\n\n"
        "Every output maps: Event → Math Models → Physics → Sector Stress → Decision.\n\n"
        "**Model version:** 2.1.0 | **Architecture:** 10-layer deterministic pipeline "
        "(17 runtime stages in SimulationEngine + 1 audit stage = 18 pipeline stages total)\n\n"
        "**Mandatory outputs:** scenario_id · model_version · event_severity · peak_day · "
        "confidence_score · financial_impact · sector_analysis · propagation_score · "
        "unified_risk_score · risk_level · physical_system_status · bottlenecks · "
        "congestion_score · recovery_score · explainability · decision_plan"
    ),
    version="2.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# ── CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Global exception handler ──────────────────────────────────────────────
@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(status_code=400, content={"detail": str(exc)})


# ── Health (no auth) ──────────────────────────────────────────────────────
app.include_router(health_router)


# ── Simulation engine direct endpoint (no auth — public) ─────────────────
@app.post("/simulate", tags=["simulation"], summary="Direct simulation — full 16-field output")
async def simulate_direct(body: dict):
    """Direct access to SimulationEngine.run() — bypasses legacy pipeline.

    Required: scenario_id (str), severity (float 0–1)
    Optional: horizon_hours (int, default 336)

    Returns all 16 mandatory output fields plus decision_plan.
    """
    from src.simulation_engine import SimulationEngine
    engine = SimulationEngine()
    scenario_id = body.get("scenario_id", "hormuz_chokepoint_disruption")
    severity = float(body.get("severity", 0.7))
    horizon_hours = int(body.get("horizon_hours", 336))
    result = engine.run(scenario_id=scenario_id, severity=severity, horizon_hours=horizon_hours)
    return result


# ── Version endpoint ──────────────────────────────────────────────────────
@app.get("/version", tags=["meta"])
async def get_version():
    """Return engine version, scenario count, and model equation."""
    from src.simulation_engine import SimulationEngine, SCENARIO_CATALOG
    return {
        "service": "Impact Observatory | مرصد الأثر",
        "model_version": SimulationEngine.MODEL_VERSION,
        "api_version": "2.1.0",
        "scenarios": len(SCENARIO_CATALOG),
        "scenario_ids": sorted(SCENARIO_CATALOG.keys()),
        "model_equation": "R_i(t) = w1*G + w2*P + w3*N + w4*L + w5*T + w6*U",
        "architecture_layers": 9,
        "risk_levels": ["NOMINAL", "LOW", "GUARDED", "ELEVATED", "HIGH", "SEVERE"],
    }


# ── All domain routers under /api/v1 with X-API-Key auth ─────────────────
api_v1 = APIRouter(prefix="/api/v1", dependencies=[Depends(require_api_key)])
api_v1.include_router(events_router)
api_v1.include_router(conflicts_router)
api_v1.include_router(incidents_router)
api_v1.include_router(flights_router)
api_v1.include_router(vessels_router)
api_v1.include_router(scores_router)
api_v1.include_router(scenarios_router)
api_v1.include_router(graph_router)
api_v1.include_router(insurance_router)
api_v1.include_router(decision_router)

# ── Impact Observatory v1 core endpoints ─────────────────────────────────
api_v1.include_router(v1_scenarios_router)
api_v1.include_router(v1_runs_router)

# ── Auth endpoints — no API key required ─────────────────────────────────
app.include_router(v1_auth_router, prefix="/api/v1")

app.include_router(api_v1)
