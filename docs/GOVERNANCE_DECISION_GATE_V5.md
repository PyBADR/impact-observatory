# Governance Decision Gate — Live Data v5

**Date:** 2026-04-15
**Branch:** `feature/governance-decision-gate-v5`
**Status:** Policy document — blocks v5 signal scoring until all rules are satisfied
**Enforcement:** `backend/src/signal_ingestion/governance.py` (policy constants + validators)

---

## Purpose

This document defines the **mandatory governance rules** that must be satisfied before any external signal is allowed to influence scenario metrics (URS, loss estimates, severity, confidence). Until every rule in this gate passes, the system operates in OFF or ADVISORY mode — signals are displayed but never modify numbers.

**No signal may affect scenario calculations unless this gate approves it.**

---

## A. Minimum Confidence Rule

### Thresholds

| Metric | Minimum | Action Below Threshold |
|--------|---------|----------------------|
| Source confidence weight | ≥ 0.60 | Signal ignored — fallback to static |
| Snapshot confidence score | ≥ 0.40 | Signal downgraded to advisory-only |
| Combined confidence | ≥ 0.50 | Signal cannot enter scoring pipeline |

### How Confidence Is Calculated

```
snapshot_confidence = source.confidence_weight × freshness_multiplier

freshness_multiplier:
  FRESH   → 1.00
  RECENT  → 0.85
  STALE   → 0.60
  EXPIRED → 0.30
  UNKNOWN → 0.50

combined_confidence = snapshot_confidence
  (future: may incorporate corroboration_count, cross-source agreement)
```

### Below-Threshold Behavior

- `snapshot_confidence < 0.40` → Signal is **advisory-only**: displayed in UI with "Low confidence" badge, never enters scoring
- `source.confidence_weight < 0.60` → Source is **untrusted**: all snapshots from this source are advisory-only regardless of freshness
- `combined_confidence < 0.50` → Signal is **blocked from scoring**: audit records `decision: BLOCKED_LOW_CONFIDENCE`

---

## B. Freshness Threshold

### Acceptable Windows by Source Type

| Source Type | Fresh Window | Recent Window | Stale Threshold | Expired Threshold |
|-------------|-------------|---------------|-----------------|-------------------|
| RSS | ≤ 60 min | ≤ 120 min | ≤ 300 min | > 300 min |
| API | ≤ 30 min | ≤ 60 min | ≤ 150 min | > 150 min |
| Market | ≤ 15 min | ≤ 30 min | ≤ 75 min | > 75 min |
| Government | ≤ 7 days | ≤ 14 days | ≤ 35 days | > 35 days |
| Manual | N/A | N/A | N/A | Always UNKNOWN |

### Stale Source Behavior

When a source's latest snapshot is STALE:
1. Mark source status as `DEGRADED`
2. Apply freshness penalty (confidence × 0.60)
3. Signal enters advisory-only mode — displayed but does not score
4. Audit records `decision: ADVISORY_STALE_SOURCE`

### Expired Signal Behavior

When a snapshot is EXPIRED:
1. Signal is **discarded from scoring pipeline**
2. Displayed in UI with "Expired" badge and strikethrough confidence
3. Audit records `decision: DISCARDED_EXPIRED`
4. System falls back to static scenario value

---

## C. Fallback Rule

### Fallback Priority Chain

```
1. SCORING signal available + confidence ≥ 0.50 + fresh/recent
   → Use signal-adjusted value

2. ADVISORY signal available + confidence ≥ 0.40
   → Use static fallback value
   → Display signal as advisory context

3. Last known snapshot available + age < 2× refresh window
   → Use static fallback value
   → Show "Last known: [timestamp]" context

4. No signal available OR all signals expired/blocked
   → Use static fallback value
   → Mark as "Static fallback — no signal data"
   → is_static_fallback = True
```

### Fallback Is Always Safe

The static scenario value (from `SCENARIO_CATALOG`) is **always** the fallback. A signal can only **adjust** the value within bounded limits — it cannot replace it entirely.

### Signal Adjustment Bounds

When scoring mode is enabled (future v5):
```
max_adjustment_factor = ±0.15 (15%)
adjusted_value = static_value × (1.0 + signal_adjustment)
signal_adjustment ∈ [-0.15, +0.15]
```

A signal can never move a scenario value by more than ±15% from its static baseline.

---

## D. Approval Rule

### Approval Chain for Signal Impact

| Impact Mode | Approval Required |
|-------------|------------------|
| OFF → ADVISORY | System rule (automatic if source is registered + enabled) |
| ADVISORY → SCORING | Feature flag (`ENABLE_SIGNAL_SCORING_V5=true`) + governance owner sign-off |
| SCORING individual source | Per-source enable flag (`ENABLE_SOURCE_<id>=true`) |
| Emergency disable | Any: kill switch, governance owner, or system auto-disable (3 consecutive failures) |

### Governance Owner

The governance owner is defined as the deployment operator or system administrator who controls environment variables. In production, this requires:
1. Setting the feature flag in the deployment config
2. Documenting the decision in the deployment log
3. Monitoring the first 24 hours of signal impact

### System Auto-Approval

A signal may enter advisory mode automatically if:
- Source is registered in `SAMPLE_SIGNAL_SOURCES` or connector registry
- Source `enabled=True`
- Source `confidence_weight ≥ 0.60`
- Source has passed health check within the last refresh window

---

## E. Impact Mode

### Three Operating Modes

| Mode | Signals Displayed | Signals Explain Risk | Signals Change Metrics | Default |
|------|-------------------|---------------------|----------------------|---------|
| **OFF** | Yes (dev only) | No | No | ✅ Production default |
| **ADVISORY** | Yes | Yes (context only) | No | Available via flag |
| **SCORING** | Yes | Yes | Yes (bounded ±15%) | Requires v5 flag + governance |

### Mode Determination

```python
if not ENABLE_DEV_SIGNAL_PREVIEW:
    mode = OFF

elif not ENABLE_SIGNAL_SCORING_V5:
    mode = ADVISORY

elif ENABLE_SIGNAL_SCORING_V5 and governance_gate_passes():
    mode = SCORING

else:
    mode = ADVISORY  # Flag on but gate fails → safe fallback
```

### Mode Transitions

```
OFF ──[ENABLE_DEV_SIGNAL_PREVIEW=true]──→ ADVISORY
ADVISORY ──[ENABLE_SIGNAL_SCORING_V5=true + gate passes]──→ SCORING
SCORING ──[kill switch OR gate fails OR flag off]──→ ADVISORY
ADVISORY ──[ENABLE_DEV_SIGNAL_PREVIEW=false]──→ OFF
```

---

## F. Feature Flag Rule

### Required Flags

| Flag | Default | Purpose |
|------|---------|---------|
| `ENABLE_DEV_SIGNAL_PREVIEW` | `false` | Gates dev preview (v4, already implemented) |
| `ENABLE_SIGNAL_SCORING_V5` | `false` | Gates signal → scoring pipeline |
| `ENABLE_SOURCE_<source_id>` | `false` | Per-source activation (future) |

### Production Rule

**Production must default to OFF or ADVISORY, never SCORING.**

`ENABLE_SIGNAL_SCORING_V5` must NOT be set to `true` in any production deployment config until:
1. This governance document is reviewed and approved
2. At least one source has been validated for 7 days in ADVISORY mode
3. Kill switch procedure is documented and tested
4. Audit logging is confirmed operational
5. Signal adjustment bounds (±15%) are tested across all 20 scenarios

---

## G. Audit Rule

### Every Signal Impact Attempt Must Record

| Field | Type | Description |
|-------|------|-------------|
| `source_id` | string | Which source produced the signal |
| `snapshot_id` | string | Which snapshot was evaluated |
| `scenario_id` | string | Which scenario was targeted |
| `confidence` | float | Computed confidence at decision time |
| `freshness` | string | Freshness status at decision time |
| `decision` | enum | `ALLOWED`, `BLOCKED_LOW_CONFIDENCE`, `BLOCKED_STALE`, `BLOCKED_EXPIRED`, `ADVISORY_ONLY`, `BLOCKED_KILL_SWITCH`, `BLOCKED_FLAG_OFF` |
| `fallback_used` | bool | Whether static fallback was used |
| `calculation_before` | float | Scenario value before signal (always static baseline) |
| `calculation_after` | float | Scenario value after signal (same as before if blocked) |
| `adjustment_factor` | float | Signal adjustment applied (0.0 if blocked) |
| `approved_by` | string | `system_rule`, `feature_flag`, `governance_owner`, `auto_disabled` |
| `timestamp` | string | ISO-8601 when the decision was made |
| `mode` | string | `OFF`, `ADVISORY`, `SCORING` |

### Audit Trail Immutability

Audit entries are append-only frozen records. No entry may be deleted, modified, or overwritten. The audit trail must survive:
- Application restart
- Feature flag changes
- Kill switch activation
- Deployment rollback

---

## H. Kill Switch

### Emergency Disable Procedure

```
Kill switch activated
    │
    ├─ Step 1: Set ENABLE_SIGNAL_SCORING_V5=false
    │   └─ All scoring stops immediately
    │   └─ System reverts to ADVISORY mode
    │
    ├─ Step 2: Optionally set ENABLE_DEV_SIGNAL_PREVIEW=false
    │   └─ All signal display stops
    │   └─ System reverts to OFF mode
    │
    ├─ Step 3: All scenario values revert to SCENARIO_CATALOG static baseline
    │   └─ is_static_fallback = True
    │   └─ No signal adjustment applied
    │
    ├─ Step 4: Audit trail records kill switch activation
    │   └─ approved_by = "kill_switch"
    │   └─ decision = "BLOCKED_KILL_SWITCH"
    │
    └─ Step 5: All connectors disabled
        └─ source.enabled = False
        └─ ConnectorStatus = DISABLED
```

### Auto-Kill Triggers

The system automatically activates the kill switch if:
1. **3 consecutive connector failures** for any source → that source disabled
2. **All sources degraded/unavailable** → system reverts to OFF
3. **Signal adjustment exceeds bounds** (|factor| > 0.15) → that signal blocked, audit flagged

### Recovery After Kill Switch

1. Investigate root cause (source outage, data quality, config error)
2. Fix the issue
3. Re-enable in ADVISORY mode first (monitor for 24h)
4. Only then re-enable SCORING if governance owner approves

---

## Decision Gate Checklist

Before enabling `ENABLE_SIGNAL_SCORING_V5=true` in any environment:

- [ ] This governance document reviewed and approved
- [ ] At least 1 source validated in ADVISORY mode for 7+ days
- [ ] Confidence thresholds tested across all 20 scenarios
- [ ] Signal adjustment bounds (±15%) verified
- [ ] Kill switch tested (activate → verify revert → recover)
- [ ] Audit logging confirmed operational
- [ ] Freshness windows configured per source type
- [ ] Fallback chain tested (signal unavailable → static baseline)
- [ ] No "live intelligence" or "real-time" wording in production UI
- [ ] Deployment operator documented in deployment log
