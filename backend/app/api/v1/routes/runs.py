"""
Impact Observatory | مرصد الأثر — Unified Run endpoints

POST /runs          → 202 Accepted — runs canonical unified pipeline
GET  /runs/{id}     → Full UnifiedRunResult
GET  /runs/{id}/status → Poll run status

Canonical backend: simulation/runner.py (13 stages, 29 engine calls)
All section-fetch endpoints removed — unified payload replaces them.

PERSISTENCE MODEL
    Source of truth: SQLite via app.signals.store (run_records + run_result_records)
    In-memory cache: _runs / _run_results dicts (fast lookup, rebuilt from DB at startup)

    Write order (both POST /runs and hitl.approve):
        1. Write to in-memory cache
        2. Write to SQLite (fire-and-forget — failures logged, never raise)

    Read order (GET /runs/{id}, GET /runs/{id}/status):
        1. Check in-memory cache
        2. On cache miss: load from SQLite and warm cache

    Startup: load_runs_from_db() restores _runs from DB (result blobs loaded on demand).
"""

from fastapi import APIRouter, Header, Query
from fastapi.responses import JSONResponse, Response
from typing import Optional
from datetime import datetime, timezone
import uuid
import logging

from ....core.security import authenticate
from ....core.rbac import Permission, has_permission
from ....core.errors import (
    InsufficientRoleError, RunNotFoundError, RunNotReadyError,
)
from ....core.constants import MODEL_VERSION
from ..schemas.common import success_response

logger = logging.getLogger("observatory.runs")

router = APIRouter()

# In-memory run + result cache (SQLite is source of truth — see PERSISTENCE MODEL above)
_runs: dict[str, dict] = {}
_run_results: dict[str, dict] = {}


# ── DB helpers ─────────────────────────────────────────────────────────────────

def _coerce_run_meta(row: dict) -> dict:
    """Normalize a DB row dict into the in-memory run_meta format.

    Converts datetime objects → ISO-8601 strings ending in Z, and drops None values
    that the downstream code doesn't expect.
    """
    out: dict = {}
    for k, v in row.items():
        if isinstance(v, datetime):
            out[k] = v.isoformat().replace("+00:00", "Z") if v.tzinfo else v.isoformat() + "Z"
        else:
            out[k] = v
    return out


def _db_save_run(run_meta: dict) -> None:
    """Fire-and-forget: persist run_meta to SQLite.  Failures logged, never raised."""
    try:
        from app.signals import store as signal_store
        signal_store.save_run(run_meta)
    except Exception as exc:
        logger.error("runs._db_save_run FAILED run_id=%s: %s", run_meta.get("run_id"), exc)


def _db_save_result(run_id: str, result: dict) -> None:
    """Fire-and-forget: persist full run result to SQLite.  Failures logged, never raised."""
    try:
        from app.signals import store as signal_store
        signal_store.save_run_result(run_id, result)
    except Exception as exc:
        logger.error("runs._db_save_result FAILED run_id=%s: %s", run_id, exc)


def _db_load_run(run_id: str) -> dict | None:
    """Load run metadata from SQLite (cache miss fallback).  Returns None on failure."""
    try:
        from app.signals import store as signal_store
        row = signal_store.load_run_by_id(run_id)
        if row is None:
            return None
        return _coerce_run_meta(row)
    except Exception as exc:
        logger.error("runs._db_load_run FAILED run_id=%s: %s", run_id, exc)
        return None


def _db_load_result(run_id: str) -> dict | None:
    """Load run result from SQLite (cache miss fallback).  Returns None on failure."""
    try:
        from app.signals import store as signal_store
        return signal_store.load_result_by_id(run_id)
    except Exception as exc:
        logger.error("runs._db_load_result FAILED run_id=%s: %s", run_id, exc)
        return None


# ── POST /runs ─────────────────────────────────────────────────────────────────
@router.post("/runs", status_code=202)
async def create_run(
    request_body: dict = None,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Create run via canonical unified pipeline (simulation/runner.py, 13 stages).

    Accepts template_id (required), severity (0-1), horizon_hours, label.
    Returns 202 with run_meta. Full result stored in _run_results for GET /runs/{id}.
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.LAUNCH_RUN):
        err = InsufficientRoleError(auth.role.value)
        return JSONResponse(status_code=403, content=err.to_envelope())

    run_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    body = request_body or {}

    # template_id is the sole canonical identifier — no legacy alias.
    # Callers must send template_id; scenario_id is NOT accepted.
    # The empty-string check below (line ~151) will reject requests missing template_id.
    template_id = body.get("template_id", "")
    severity = min(1.0, max(0.0, float(body.get("severity", 0.7))))
    horizon_hours = max(1, min(8760, int(body.get("horizon_hours", 168))))
    label = body.get("label", "")

    run_meta = {
        "run_id": run_id,
        "scenario_id": template_id,
        "scenario_version": "1.0.0",
        "model_version": MODEL_VERSION,
        "dataset_version": "2026.04.02",
        "regulatory_version": "2.4.0",
        "severity": severity,
        "horizon_hours": horizon_hours,
        "label": label,
        "status": "running",
        "created_at": now,
    }
    _runs[run_id] = run_meta
    _db_save_run(run_meta)  # persist "running" state immediately

    if not template_id:
        run_meta["status"] = "failed"
        run_meta["error"] = "template_id is required"
        _db_save_run(run_meta)  # persist failed state
        return JSONResponse(status_code=202, content=success_response(run_meta))

    # Run canonical unified pipeline (13 stages, 29 engine calls)
    try:
        from ....simulation.runner import run_unified_pipeline
        result = run_unified_pipeline(
            template_id=template_id,
            severity=severity,
            horizon_hours=horizon_hours,
            label=label,
        )

        # Inject canonical run_id (BP-06: runner generates its own format)
        result["run_id"] = run_id

        # Cache + persist full unified result
        _run_results[run_id] = result
        _db_save_result(run_id, result)

        run_meta["status"] = result.get("status", "completed")
        run_meta["completed_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        run_meta["computed_in_ms"] = result.get("duration_ms", 0)
        run_meta["stages_completed"] = result.get("stages_completed", 0)
        run_meta["stages_total"] = 13

        logger.info(
            f"Run {run_id} completed: "
            f"{result.get('stages_completed', 0)}/13 stages, "
            f"{result.get('duration_ms', 0):.1f}ms"
        )
    except Exception as e:
        run_meta["status"] = "failed"
        run_meta["error"] = str(e)
        logger.error(f"Run {run_id} failed: {e}", exc_info=True)

    # Persist final run state (completed or failed)
    _db_save_run(run_meta)

    return JSONResponse(status_code=202, content=success_response(run_meta))


# ── GET /runs/{run_id}/status ──────────────────────────────────────────────────
@router.get("/runs/{run_id}/status")
async def get_run_status(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """v4 §4.3.2 — Poll run status."""
    authenticate(authorization, x_api_key)

    if run_id not in _runs:
        # DB fallback — run may have been created in a previous process lifecycle
        db_meta = _db_load_run(run_id)
        if db_meta is None:
            err = RunNotFoundError(run_id)
            return JSONResponse(status_code=404, content=err.to_envelope())
        _runs[run_id] = db_meta  # warm cache

    meta = _runs[run_id]
    payload = {
        "run_id": run_id,
        "status": meta["status"],
        "created_at": meta["created_at"],
        "completed_at": meta.get("completed_at"),
        "computed_in_ms": meta.get("computed_in_ms"),
        "stages_completed": meta.get("stages_completed", 0),
        "stages_total": meta.get("stages_total", 10),
    }

    # Enrich with result fields if available in cache
    if run_id in _run_results:
        payload["warnings"] = _run_results[run_id].get("warnings", [])
        payload["stage_log"] = _run_results[run_id].get("stage_log", {})
        payload["audit_hash"] = _run_results[run_id].get("trust", {}).get("audit_hash", "")

    return JSONResponse(content=success_response(payload))


# ── GET /runs/{run_id} ─────────────────────────────────────────────────────────
@router.get("/runs/{run_id}")
async def get_run_result(
    run_id: str,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Full UnifiedRunResult — single payload replaces all section-fetch endpoints."""
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.LAUNCH_RUN):
        err = InsufficientRoleError(auth.role.value)
        return JSONResponse(status_code=403, content=err.to_envelope())

    # Resolve run metadata (cache → DB)
    if run_id not in _runs:
        db_meta = _db_load_run(run_id)
        if db_meta is None:
            err = RunNotFoundError(run_id)
            return JSONResponse(status_code=404, content=err.to_envelope())
        _runs[run_id] = db_meta  # warm cache

    # Resolve run result (cache → DB)
    if run_id not in _run_results:
        db_result = _db_load_result(run_id)
        if db_result is not None:
            _run_results[run_id] = db_result  # warm cache
        else:
            status = _runs[run_id].get("status", "unknown")
            err = RunNotReadyError(run_id, status)
            return JSONResponse(status_code=err.http_status, content=err.to_envelope())

    return JSONResponse(content=success_response(_run_results[run_id]))


# ── GET /runs/{run_id}/export ──────────────────────────────────────────────────
@router.get("/runs/{run_id}/export")
async def export_run_pdf(
    run_id: str,
    lang: str = Query(default="en", pattern="^(en|ar)$"),
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None, alias="X-IO-API-Key"),
):
    """Export a completed run as a Unicode-safe PDF report (English or Arabic).

    Query params:
        lang: "en" (default) | "ar"

    Returns 200 application/pdf on success.
    Returns 404 if run not found, 425 if run not yet complete.
    """
    auth = authenticate(authorization, x_api_key)
    if not has_permission(auth.role, Permission.LAUNCH_RUN):
        err = InsufficientRoleError(auth.role.value)
        return JSONResponse(status_code=403, content=err.to_envelope())

    # Resolve run metadata
    if run_id not in _runs:
        db_meta = _db_load_run(run_id)
        if db_meta is None:
            err = RunNotFoundError(run_id)
            return JSONResponse(status_code=404, content=err.to_envelope())
        _runs[run_id] = db_meta

    # Resolve run result
    if run_id not in _run_results:
        db_result = _db_load_result(run_id)
        if db_result is not None:
            _run_results[run_id] = db_result
        else:
            status = _runs[run_id].get("status", "unknown")
            err = RunNotReadyError(run_id, status)
            return JSONResponse(status_code=err.http_status, content=err.to_envelope())

    from app.services.pdf_export import generate_pdf
    pdf_bytes = generate_pdf(_run_results[run_id], lang=lang)

    filename = f"impact-observatory-{run_id[:8]}-{lang}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Store accessors (used by hitl.py) ─────────────────────────────────────────

def get_run_store() -> dict:
    """Access the in-memory run cache."""
    return _runs


def get_result_store() -> dict:
    """Access the in-memory result cache."""
    return _run_results


# ── Startup recovery ───────────────────────────────────────────────────────────

def load_runs_from_db() -> None:
    """Restore the in-memory _runs cache from SQLite on startup.

    Result blobs are NOT loaded here — they are large and loaded on-demand
    when GET /runs/{id} is called.  Only run metadata is restored.

    Any rows that cannot be loaded are logged and skipped.
    """
    try:
        from app.signals import store as signal_store
        rows = signal_store.load_all_run_metadata()
    except Exception as exc:
        logger.error("load_runs_from_db: failed to load from DB: %s", exc)
        return

    loaded = 0
    for row in rows:
        run_id = row.get("run_id")
        if run_id and run_id not in _runs:
            try:
                _runs[run_id] = _coerce_run_meta(row)
                loaded += 1
            except Exception as exc:
                logger.error("load_runs_from_db: could not restore run_id=%s: %s", run_id, exc)

    logger.info("runs: startup recovery — loaded=%d run records from DB", loaded)
