# Live Data v2 — Signal Snapshot Ingestion

**Date:** 2026-04-15
**Branch:** `feature/live-data-v2-signal-snapshot`
**Status:** Implemented — read-only, additive, zero scenario changes

---

## 1. What This Is

A **read-only signal snapshot ingestion layer** that can accept, normalize, and store external signal data as typed snapshots. It does NOT change any scenario outputs.

### What this IS:
- Typed models for signal sources and snapshots
- A normalization pipeline (raw dict → SignalSnapshot)
- Freshness and confidence calculations
- An immutable audit log for all ingestion events
- Sample static signals for development/testing
- TypeScript types for future frontend integration

### What this is NOT:
- NOT live RSS/API ingestion (all external sources are disabled)
- NOT connected to the simulation engine
- NOT modifying scenario numbers
- NOT "live intelligence" or "real-time data"
- NOT visible in the UI (type-only frontend changes)

---

## 2. This Does Not Change Scenario Numbers

The simulation engine reads from `SCENARIO_CATALOG` and `config.py`. This layer does not import, reference, or modify either. The test `test_scenario_catalog_unchanged_after_ingestion` explicitly verifies this invariant.

---

## 3. This Is Not Live Intelligence Yet

All signal sources in `SAMPLE_SIGNAL_SOURCES` have `enabled=False` except `sig_sample_static` (a manual/development source). No HTTP requests, RSS fetches, or API calls are made.

The sample signals in `SAMPLE_RAW_SIGNALS` are static text fixtures — analyst-written examples with hardcoded timestamps from April 2026.

---

## 4. How This Prepares for Future v3 Live Integration

The architecture is designed so that enabling a live source requires only:

1. Set `enabled=True` on a `SignalSource` entry
2. Implement a fetch function that returns `list[dict]` from the source
3. Pass the fetched dicts to `ingest_signals()`
4. Optionally connect the resulting snapshots to scoring via a **feature flag**

The scoring integration (step 4) is NOT built yet. It will be part of v3.

---

## 5. How Freshness Is Calculated

```
age_minutes = (ingested_at - published_at) / 60

ratio = age_minutes / source.refresh_frequency_minutes

ratio ≤ 1.0  → FRESH
ratio ≤ 2.0  → RECENT
ratio ≤ 5.0  → STALE
ratio > 5.0  → EXPIRED

refresh_frequency = 0 → UNKNOWN (static/manual source)
bad timestamp       → UNKNOWN
```

---

## 6. How Confidence Is Calculated

```
confidence = source.confidence_weight × freshness_multiplier

FRESH   → 1.00 (no penalty)
RECENT  → 0.85
STALE   → 0.60
EXPIRED → 0.30
UNKNOWN → 0.50

Result clamped to [0.0, 1.0]
```

---

## 7. How Signals May Later Connect to Scoring

**Not implemented in v2.** The future path (v3+):

```
[Feature Flag: ENABLE_LIVE_SIGNAL_SCORING = false]

IF flag is ON:
  1. Fetch live signals from enabled sources
  2. Normalize into SignalSnapshots
  3. For each snapshot with related_scenarios:
     - Look up the scenario in SCENARIO_CATALOG
     - Compute a signal_adjustment factor from snapshot confidence
     - Pass signal_adjustment to compute_trust_score() via signal_inputs
  4. Trust score shows adjusted_loss_usd reflecting live signals
  5. Provenance panel shows "Signal-enhanced" instead of "Static fallback"

IF flag is OFF (default, current):
  - No signals fetched
  - No scoring modification
  - Provenance shows "Static fallback"
  - Scenario numbers unchanged
```

---

## 8. Files Created

| File | Lines | Purpose |
|------|-------|---------|
| `backend/src/signal_ingestion/__init__.py` | ~45 | Package exports |
| `backend/src/signal_ingestion/models.py` | ~190 | SignalSource + SignalSnapshot + sample registry |
| `backend/src/signal_ingestion/ingestion_service.py` | ~220 | Normalization, freshness, confidence, batch ingestion |
| `backend/src/signal_ingestion/audit_log.py` | ~130 | Append-only audit log |
| `backend/tests/test_signal_ingestion.py` | ~330 | 43 contract tests |
| `frontend/src/types/signal-snapshot.ts` | ~90 | TypeScript types (type-only, no runtime) |
| `docs/LIVE_DATA_V2_SIGNAL_SNAPSHOT.md` | this file | Documentation |

**Files modified:** None. Zero existing files changed.

---

## 9. Signal Source Registry (v2)

| Source ID | Name | Type | Enabled | Notes |
|-----------|------|------|---------|-------|
| `sig_reuters_energy` | Reuters Energy News (GCC) | RSS | No | Would provide energy news signals |
| `sig_brent_futures` | Brent Crude Futures (ICE) | Market | No | Would provide price signals |
| `sig_eia_weekly` | EIA Weekly Petroleum Report | Government | No | Would calibrate energy scenarios |
| `sig_gcc_central_banks` | GCC Central Bank Announcements | RSS | No | Would feed banking scenarios |
| `sig_maritime_ais` | AIS Vessel Traffic — Hormuz | API | No | Would validate maritime severity |
| `sig_sample_static` | Sample Static Signals (Dev) | Manual | **Yes** | Static samples for testing only |

---

## 10. Decision Gate — What Must Be True Before v3

Before enabling any live signal source:

1. **Fetch function implemented** for the source (returns raw dicts)
2. **Error handling verified** — fetch failure returns empty, does not crash
3. **Rate limiting configured** — no more than 1 fetch per refresh_frequency
4. **Feature flag created** — `ENABLE_LIVE_SIGNAL_SCORING` defaults to `false`
5. **Scoring integration tested** — signal_inputs parameter validated
6. **Provenance panel updated** — shows "Signal-enhanced" when live
7. **Audit trail active** — every fetch/failure logged
8. **No "live intelligence" wording** until signals are actually connected
