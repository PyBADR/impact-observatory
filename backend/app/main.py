import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from app.api.router import api_router
    from app.api.demo_routes import demo_router
except ImportError:
    from backend.app.api.router import api_router
    from backend.app.api.demo_routes import demo_router

app = FastAPI(
    title="Deevo GCC Shock Intelligence API",
    version="0.2.0",
    description="Structured simulation under uncertainty for GCC shock intelligence.",
)

# CORS: use ALLOWED_ORIGINS env var (comma-separated) or default to permissive for dev
_raw_origins = os.getenv("ALLOWED_ORIGINS", "*")
_origins = ["*"] if _raw_origins.strip() == "*" else [o.strip() for o in _raw_origins.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)
app.include_router(demo_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    return {"status": "ok", "version": "0.2.0", "engine": "deevo-sim-pilot"}
