# Live Data v5 — Advisory Signal Layer Implementation

**Date:** 2026-04-15
**Branch:** `feature/live-data-v5-advisory-signal-layer`
**Base:** `contract/unified-demo-operating-contract`
**Type:** Implementation — advisory-only signal interpretation layer
**Status:** Advisory mode only. No scoring. No metric changes.

---

## 1. What This Implements

This PR implements the **v5 advisory signal interpretation layer** as specified in `docs/LIVE_DATA_V5_ADVISORY_SIGNAL_BRIEF.md`. It adds:

- A `SignalAdvisory` typed model for advisory outputs
- An `advisory_service` that evaluates signals in advisory-only mode
- Extended audit log actions for advisory events
- A feature flag `ENABLE_SIGNAL_ADVISORY_V5` (default: false)
- An API endpoint `/internal/signal-advisory/evaluate`
- A frontend `AdvisorySignalPanel` component (hidden by default)
- TypeScript types mirroring the backend advisory model
- 24+ tests proving no scoring, no metric changes, no catalog mutation

---

## 2. Advisory Only — No Metric Changes

**Hard rules enforced in code:**

```python
# advisory_service.py — lines that enforce the contract:
metric_after=metric_before,   # HARD RULE: metric_after == metric_before
scoring_applied=False,         # HARD RULE: always False
adjustment_factor=0.0,         # Advisory mode — no adjustment
```

**What the advisory service does NOT do:**
- Does NOT import or call `compute_unified_risk_score`
- Does NOT import or call `compute_event_severity`
- Does NOT import or call `compute_financial_losses`
- Does NOT import or call any function from `risk_models.py`
- Does NOT write to `SCENARIO_CATALOG` (read-only lookup)
- Does NOT change `base_loss_usd`, `unified_risk_score`, or `confidence_score`
- Does NOT reorder scenario severity rankings
- Does NOT modify decision recommendations

---

## 3. No Scoring Implementation

The advisory service operates entirely in `ImpactMode.ADVISORY`. The governance gate is evaluated with `adjustment_factor=0.0`, meaning:

- The `MAX_ADJUSTMENT_FACTOR` (±15%) bound is never invoked
- The `GovernanceDecision.ALLOWED` path (which permits scoring) is not reachable in advisory mode
- Even if a signal passes all confidence/freshness gates, the output is advisory text only

The `ENABLE_SIGNAL_SCORING_V5` flag remains `false` and is not referenced by this implementation.

---

## 4. Feature Flag — Default False

| Flag | Default | Purpose |
|------|---------|---------|
| `ENABLE_SIGNAL_ADVISORY_V5` | `false` | Controls advisory panel visibility and API endpoint |

**Backend:** `backend/src/signal_ingestion/feature_flags.py`
```python
def is_signal_advisory_v5_enabled() -> bool:
    return _env_bool("ENABLE_SIGNAL_ADVISORY_V5", default=False)
```

**Frontend:** `process.env.NEXT_PUBLIC_ENABLE_SIGNAL_ADVISORY_V5 === "true"`

When false (default, production):
- API endpoint returns 404
- Advisory panel renders nothing (`return null`)
- No advisory interpretations generated
- Zero runtime overhead

---

## 5. Audit Before/After

Every advisory evaluation records an audit entry containing:

```
Advisory generated: scenario=hormuz_chokepoint_disruption,
  confidence=0.8000,
  freshness=fresh,
  metric_before=3200000000,
  metric_after=3200000000,
  scoring_applied=False,
  fallback_used=False,
  governance_decision=advisory_only
```

When the feature flag is disabled or the scenario is unknown, a `FALLBACK_USED` entry is recorded with the reason.

---

## 6. Fallback Behavior

| Condition | Behavior |
|-----------|----------|
| Feature flag disabled | Returns `None` — no advisory generated |
| Unknown scenario | Returns `None` — audit records reason |
| Source confidence < 0.60 | Fallback advisory — `fallback_used=True` |
| Snapshot confidence < 0.40 | Fallback advisory — `fallback_used=True` |
| Signal expired | Fallback advisory — `fallback_used=True` |
| Signal stale | Normal advisory (stale is advisory-eligible) |

Fallback advisories contain different text: "Signal was evaluated but did not meet confidence or freshness thresholds. Displayed as background context only — no metrics changed."

---

## 7. Why v6/v7 Are Required Before Scoring

The advisory layer deliberately stops short of scoring because:

1. **v6 — Transmission Graph Sandbox** is needed to validate entity relationships before signals can influence propagation paths. Without a validated graph, scoring would propagate inaccurate risk.

2. **v7 — Decision Engine Prototype** must be built and backtested in staging before recommendations can be generated. Untested recommendation logic could produce misleading action suggestions.

3. **v8 — Governance-Approved Scoring** requires:
   - 7+ days of stable advisory operation
   - Governance owner sign-off
   - `ENABLE_SIGNAL_SCORING_V5=true` (currently blocked)
   - All 8 governance gates passing per signal
   - `MAX_ADJUSTMENT_FACTOR` (±15%) enforcement

Scoring without these layers would bypass the governance architecture that protects production reliability.

---

## 8. Files Changed

### Backend (new)
| File | Purpose |
|------|---------|
| `backend/src/signal_ingestion/advisory_model.py` | `SignalAdvisory` typed model |
| `backend/src/signal_ingestion/advisory_service.py` | Read-only advisory evaluation service |
| `backend/src/api/v1/signal_advisory.py` | API endpoint (gated by feature flag) |
| `backend/tests/test_advisory_v5.py` | 24+ tests proving advisory-only behavior |

### Backend (modified)
| File | Change |
|------|--------|
| `backend/src/signal_ingestion/feature_flags.py` | Added `is_signal_advisory_v5_enabled()` |
| `backend/src/signal_ingestion/audit_log.py` | Added `ADVISORY_GENERATED`, `ADVISORY_FALLBACK` actions |
| `backend/src/signal_ingestion/__init__.py` | Exported new advisory modules |
| `backend/src/main.py` | Registered advisory API router |

### Frontend (new)
| File | Purpose |
|------|---------|
| `frontend/src/features/command-center/components/AdvisorySignalPanel.tsx` | Advisory context panel (hidden by default) |

### Frontend (modified)
| File | Change |
|------|--------|
| `frontend/src/types/signal-snapshot.ts` | Added `SignalAdvisory` interface |
| `frontend/src/app/command-center/page.tsx` | Imported and rendered `AdvisorySignalPanel` |

### Documentation
| File | Purpose |
|------|---------|
| `docs/LIVE_DATA_V5_ADVISORY_IMPLEMENTATION.md` | This document |

---

## 9. Test Coverage

| Test | Assertion |
|------|-----------|
| Feature flag defaults false | `is_signal_advisory_v5_enabled() is False` |
| Advisory disabled when flag off | `evaluate_advisory() returns None` |
| metric_after == metric_before (fresh) | Hard equality check |
| metric_after == metric_before (stale) | Hard equality check |
| metric_after == metric_before (expired) | Hard equality check |
| metric matches scenario base_loss | Validates against SCENARIO_CATALOG |
| scoring_applied == False (all freshness levels) | Loop over all SnapshotFreshness values |
| Low source confidence → fallback | `fallback_used is True` |
| Low snapshot confidence → fallback | `fallback_used is True` |
| Stale signal handling | Advisory generated, no scoring |
| Expired signal → fallback | `fallback_used is True` |
| SCENARIO_CATALOG unchanged | `deepcopy` before/after comparison |
| base_loss_usd unchanged for all scenarios | Per-scenario before/after check |
| No scoring functions imported | Source code text scan |
| Advisory model serialization | All 14 keys present |
| Batch advisory evaluation | Multiple snapshots, all advisory-only |
| Unknown scenario → None | Returns None, audit records |
| Audit records advisory events | Detail string contains key fields |

---

## 10. Production Impact

**None.** The feature flag defaults to `false`. In production:
- The API endpoint returns 404
- The advisory panel renders nothing
- No additional imports are executed at runtime (lazy evaluation)
- No scenario calculations are touched
- No UI metrics are changed
- The existing demo continues to work exactly as before
