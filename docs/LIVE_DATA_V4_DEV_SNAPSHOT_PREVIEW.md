# Live Data v4 — Dev-only Connector Activation + Snapshot Preview

**Date:** 2026-04-15
**Branch:** `feature/live-data-v4-dev-snapshot-preview`
**Status:** Implemented — dev/test-only, fixture-based, zero scoring impact

---

## 1. What This Is

A **dev/test-only snapshot preview layer** that explicitly activates the RSS connector pilot with local fixture data. Gated by `ENABLE_DEV_SIGNAL_PREVIEW` feature flag (default: `false`).

### What this IS:
- Feature flag (`ENABLE_DEV_SIGNAL_PREVIEW`) — env-based, defaults false
- Preview service that activates RSS connector with local fixture
- Internal endpoint: `GET /internal/signal-snapshots/preview` (returns 404 when disabled)
- Dev-only UI panel in `/command-center` (hidden when flag is false)
- Full audit trail for every preview run

### What this is NOT:
- NOT enabled in production by default
- NOT making network calls (local fixture only)
- NOT affecting scenario scoring or numbers
- NOT "live intelligence" or "real-time"

---

## 2. Dev/Test-Only

The feature flag gates everything:

| Flag Value | Endpoint | UI Panel | Connector |
|------------|----------|----------|-----------|
| `false` (default, production) | Returns 404 | Hidden | Disabled |
| `true` (dev/test) | Returns snapshots | Visible | Activated with fixture |

**Production deployments must NOT set `ENABLE_DEV_SIGNAL_PREVIEW=true`.**

---

## 3. Fixture-Based

All data comes from `backend/tests/fixtures/sample_rss_feed.xml` — a static 5-item RSS feed with GCC energy/market signals. Zero HTTP requests are made.

---

## 4. Read-Only — No Scoring Impact

The preview service and connector do NOT:
- Import `simulation_engine` or `config`
- Modify `SCENARIO_CATALOG`
- Call `compute_trust_score()` or any scoring function
- Change any UI metric values

Test `test_catalog_unchanged_after_preview` enforces this.

---

## 5. No Production Live Feed

The only enabled source is the dev fixture connector. All 5 external signal sources (Reuters, Brent futures, EIA, GCC Central Banks, AIS) remain `enabled=False`.

---

## 6. How to Enable Locally

```bash
# Backend
cd backend
ENABLE_DEV_SIGNAL_PREVIEW=true .venv/bin/uvicorn src.main:app --reload

# Then visit:
# http://localhost:8000/internal/signal-snapshots/preview

# Frontend
cd frontend
NEXT_PUBLIC_ENABLE_DEV_SIGNAL_PREVIEW=true npm run dev

# Then visit:
# http://localhost:3000/command-center?demo=true
# → Look for "Signal Preview — Dev" panel below Data Trust Layer
```

---

## 7. Why v5 Is Required Before Signals Affect Numbers

| Requirement | Status |
|-------------|--------|
| Feature flag for signal scoring | Defined (`ENABLE_LIVE_SIGNAL_SCORING`) but NOT used |
| HTTP fetch with rate limiting | NOT implemented |
| Signal → scoring integration | NOT implemented |
| Provenance panel shows "Signal-enhanced" | NOT implemented |
| Stale signal auto-discard | NOT implemented |
| Error budget (3 failures → disable) | NOT implemented |

All of these are v5+ requirements. v4 only proves the preview pipeline works end-to-end with fixture data.

---

## 8. Files Created / Modified

| File | Change | Purpose |
|------|--------|---------|
| `backend/src/signal_ingestion/feature_flags.py` | **New** | Feature flags (env-based, defaults false) |
| `backend/src/signal_ingestion/preview_service.py` | **New** | Dev preview service (fixture → snapshots) |
| `backend/src/api/v1/signal_preview.py` | **New** | Internal endpoint (gated, returns 404 when disabled) |
| `backend/tests/test_dev_snapshot_preview.py` | **New** | 22 contract tests |
| `frontend/src/features/command-center/components/DevSignalPreview.tsx` | **New** | Dev-only UI panel (hidden by default) |
| `docs/LIVE_DATA_V4_DEV_SNAPSHOT_PREVIEW.md` | **New** | This documentation |
| `backend/src/main.py` | **Modified** | +2 lines (import + router registration) |
| `frontend/src/app/command-center/page.tsx` | **Modified** | +4 lines (import + render) |

---

## 9. Endpoint Behavior

### `GET /internal/signal-snapshots/preview`

**When disabled (default):**
```json
{
  "detail": {
    "message": "Signal preview is not enabled.",
    "hint": "Set ENABLE_DEV_SIGNAL_PREVIEW=true in your environment for dev/test.",
    "production_safe": true
  }
}
```
HTTP 404.

**When enabled:**
```json
{
  "enabled": true,
  "snapshots": [...],
  "snapshot_count": 5,
  "source_mode": "dev_fixture",
  "scoring_impact": "none",
  "notice": "Dev fixture preview — does not affect scenario scoring. Live feeds not connected."
}
```
HTTP 200.

---

## 10. UI Panel Behavior

The `DevSignalPreview` component:
- Checks `NEXT_PUBLIC_ENABLE_DEV_SIGNAL_PREVIEW === "true"` at build time
- Returns `null` (renders nothing) when flag is false
- Shows collapsible indigo-themed panel when true
- Displays: 3 fixture snapshots with title, summary, freshness, confidence
- Footer: "Dev fixture preview — does not affect scenario scoring"
