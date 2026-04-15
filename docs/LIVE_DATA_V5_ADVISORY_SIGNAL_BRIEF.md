# Live Data v5 — Advisory Signal Interpretation (Design Brief)

**Date:** 2026-04-15
**Branch:** `feature/live-data-v5-design-brief`
**Type:** Design brief — documentation only, no code changes
**Status:** Defines requirements for advisory signal display

---

## 1. Purpose

Live Data v5 introduces **ADVISORY signal interpretation only**. Signals provide risk context alongside scenario outputs — they explain what external data suggests about the scenario but they do NOT change any metric, score, ranking, or recommendation.

### What ADVISORY means:
- A signal says: *"Brent crude rose 3% on Hormuz tensions — this aligns with the energy disruption scenario."*
- The scenario's $3.2B loss estimate, 61% stress, Day 3 peak, and 84% confidence remain **exactly the same**.
- The analyst sees the signal as context. They decide what it means. The system does not decide for them.

### What ADVISORY does NOT mean:
- It does NOT adjust `base_loss_usd`
- It does NOT recalculate `unified_risk_score`
- It does NOT change `confidence_score`
- It does NOT reorder scenario severity rankings
- It does NOT modify decision recommendations
- It does NOT alter any value shown in the Executive Briefing, Macro Outlook, or Sector Risk tabs

---

## 2. Mode

### Default Mode: OFF

| Environment | Mode | Signals Visible | Signals Explain | Signals Score |
|-------------|------|----------------|-----------------|---------------|
| Production (default) | **OFF** | No | No | No |
| Dev with preview flag | **ADVISORY** | Yes | Yes | No |
| Dev with scoring flag | **SCORING** | Yes | Yes | Yes (bounded) |

### Allowed First Rollout: ADVISORY Only

v5 may only be rolled out in ADVISORY mode. SCORING mode remains blocked by the governance decision gate (PR #14). The rollout path:

```
v5 Phase 1: OFF → ADVISORY (behind ENABLE_SIGNAL_ADVISORY_V5=true)
v5 Phase 2: Monitor ADVISORY for 7+ days
v5 Phase 3: Review advisory accuracy with analyst team
v6 (future): Consider SCORING sandbox — not part of v5
```

### Not Allowed Yet: SCORING

SCORING mode requires:
- `ENABLE_SIGNAL_SCORING_V5=true` (governance gate, PR #14)
- All governance checklist items passed
- 7+ days of stable ADVISORY operation
- Governance owner sign-off

**None of these are satisfied. SCORING is blocked.**

---

## 3. Feature Flags

### Existing Flags (from v4 + governance gate)

| Flag | Default | Purpose |
|------|---------|---------|
| `ENABLE_DEV_SIGNAL_PREVIEW` | `false` | Dev-only fixture preview (v4) |
| `ENABLE_SIGNAL_SCORING_V5` | `false` | Signal → scoring pipeline (governance gated) |

### New Flag for v5

| Flag | Default | Purpose |
|------|---------|---------|
| `ENABLE_SIGNAL_ADVISORY_V5` | `false` | Advisory signal context display in command center |

### Flag Interaction

```
ENABLE_SIGNAL_ADVISORY_V5=false  → No advisory signals shown
ENABLE_SIGNAL_ADVISORY_V5=true   → Advisory context shown alongside scenarios
                                    Metrics remain unchanged
                                    scoring_applied = false (always)

ENABLE_SIGNAL_SCORING_V5=false   → Scoring blocked (regardless of advisory flag)
ENABLE_SIGNAL_SCORING_V5=true    → Only with governance gate pass (v6+)
```

---

## 4. Advisory Behavior

### What Signals May Show

When `ENABLE_SIGNAL_ADVISORY_V5=true`, for each active scenario the system may display:

| Field | Description | Example |
|-------|-------------|---------|
| Related scenario | Which scenario this signal relates to | `hormuz_chokepoint_disruption` |
| Source | Where the signal came from | `Reuters Energy News (fixture)` |
| Freshness | How recent the signal is | `Stale — 5 days old` |
| Confidence | Computed signal confidence | `45%` |
| Risk explanation | What the signal suggests about risk | `Brent crude price increase aligns with energy disruption scenario severity.` |
| Why it matters | Business context | `A sustained oil price increase above $90/bbl historically correlates with trade flow stress in GCC maritime corridors.` |
| Suggested review | Analyst action hint | `Consider validating Hormuz scenario severity against current vessel traffic data.` |

### What Signals Must NOT Do

| Action | v5 Status | Enforcement |
|--------|-----------|-------------|
| Alter loss estimates (`total_loss_usd`, `base_loss_usd`) | **BLOCKED** | `scoring_applied=false` in audit |
| Alter confidence scores | **BLOCKED** | Governance gate rejects SCORING |
| Alter scenario ranking | **BLOCKED** | No sorting/ordering changes |
| Alter decision recommendations | **BLOCKED** | Decision plan unchanged |
| Alter URS/risk level | **BLOCKED** | `unified_risk_score` read-only |
| Alter sector stress values | **BLOCKED** | Sector analysis unchanged |
| Alter propagation scores | **BLOCKED** | Propagation chain unchanged |

---

## 5. Audit Before/After

### Every Advisory Evaluation Must Record

| Field | Type | Description |
|-------|------|-------------|
| `scenario_id` | string | Which scenario the advisory is for |
| `snapshot_id` | string | Which signal snapshot was evaluated |
| `source_id` | string | Source that produced the snapshot |
| `confidence` | float | Snapshot confidence at evaluation time |
| `freshness` | string | Freshness status at evaluation time |
| `advisory_text` | string | The risk explanation shown to the analyst |
| `metric_before` | float | Scenario metric value before advisory (e.g., `base_loss_usd`) |
| `metric_after` | float | Scenario metric value after advisory — **must equal metric_before** |
| `scoring_applied` | bool | **Must be `false` in v5. Always.** |
| `fallback_used` | bool | Whether static fallback was used |
| `governance_decision` | string | Verdict from governance gate |
| `timestamp` | string | ISO-8601 when the advisory was generated |

### Critical Invariant

```
metric_after == metric_before    (always, in v5)
scoring_applied == false         (always, in v5)
```

If either invariant is violated, the audit system must:
1. Log the violation as `CRITICAL`
2. Revert to static fallback
3. Disable the advisory for that scenario
4. Alert via audit trail

---

## 6. Rollback / Fallback

### If Signal Fails

| Failure | Behavior |
|---------|----------|
| Source unavailable | Hide advisory OR show "Signal unavailable" |
| Snapshot expired | Hide advisory OR show "Signal expired" |
| Confidence too low | Show advisory with "Low confidence" badge |
| Parse error | Hide advisory silently |
| Feature flag off | No advisory displayed |

### Fallback Rules

1. **Never block the scenario page.** If the advisory fails, the page renders normally without it.
2. **Never modify metrics.** The advisory is an additive overlay — removing it changes nothing.
3. **Preserve audit log.** Even failed advisories record an audit entry.
4. **Keep static fallback.** All scenario values remain from `SCENARIO_CATALOG`.
5. **Graceful degradation.** The user should never notice a signal failure unless they look for the advisory panel.

---

## 7. Governance Gate

### Advisory Mode Must Still Pass

Even in ADVISORY mode (no scoring), the governance gate must validate:

| Check | Threshold | Failure Action |
|-------|-----------|----------------|
| Minimum source confidence | ≥ 0.60 | Advisory hidden for that source |
| Snapshot confidence | ≥ 0.40 | Advisory shown with "Low confidence" warning |
| Freshness | Not EXPIRED | Advisory hidden if expired |
| Source allowed | `enabled=true` in registry | Advisory not generated |
| Kill switch | Not active | All advisories hidden |

### Why Gate Advisory?

Even though advisories don't change metrics, showing a low-quality or misleading advisory can:
- Erode analyst trust in the platform
- Suggest false urgency or false calm
- Create liability if acted upon manually

The governance gate ensures only credible signals produce advisory context.

---

## 8. v5 Acceptance Criteria

Before v5 advisory implementation can be considered complete:

- [ ] **No metrics changed** — `metric_after == metric_before` for every advisory evaluation
- [ ] **No scoring enabled** — `scoring_applied == false` for every audit entry
- [ ] **Advisory visible only behind feature flag** — `ENABLE_SIGNAL_ADVISORY_V5=true` required
- [ ] **Full audit trail** — every advisory generates an audit record with all 12 fields
- [ ] **Tests prove `scoring_applied=false`** — contract test that fails if scoring is ever true
- [ ] **Production defaults OFF** — `ENABLE_SIGNAL_ADVISORY_V5` not set in production env
- [ ] **Governance gate enforced** — low confidence, expired, and kill-switch all tested
- [ ] **Fallback works** — signal failure does not break scenario page
- [ ] **No "live intelligence" wording** — advisory text uses "signal context", not "live data"
- [ ] **Analyst review suggested, not automated** — advisory says "consider reviewing" not "action required"

---

## 9. Future v6 — Scoring Simulation Sandbox

**Only after v5 advisory is stable for 7+ days** may v6 be considered.

### v6 Scope (NOT part of v5)

| Component | Description |
|-----------|-------------|
| Scoring simulation sandbox | Run signal-adjusted scoring in parallel, compare to static baseline |
| Before/after metrics | Show `metric_before` vs `metric_after_simulated` side by side |
| No production scoring | Sandbox runs in dev/test only, results are informational |
| CFO/analyst approval | A named governance owner must approve before sandbox results are shown |
| Bounded adjustment | ±15% maximum, enforced by governance gate (already implemented) |

### v6 Rollout Path

```
v6 Phase 1: Build scoring sandbox (dev only, behind flag)
v6 Phase 2: Run sandbox for 14+ days, compare to static baseline
v6 Phase 3: Analyst review of sandbox accuracy
v6 Phase 4: Governance owner approves sandbox display
v6 Phase 5: Show sandbox results in dev UI (not production)
v7 (future): Consider production scoring — requires full governance review
```

### What v6 Does NOT Do

- Does NOT enable scoring in production
- Does NOT change any metric the user sees in normal operation
- Does NOT bypass the governance gate
- Does NOT remove the kill switch
- Does NOT auto-approve signal adjustments

---

## Architecture Summary

```
v1  Data Trust Layer        → provenance/freshness display        ✅ Merged (#9, #10)
v2  Signal Snapshots        → typed ingestion models              ✅ Merged (#11)
v3  Connector Pilot         → RSS fixture connector               ✅ Merged (#12)
v4  Dev Preview             → feature-flagged snapshot display     ✅ Merged (#13)
v5  Advisory (this brief)   → signal context alongside scenarios   📋 Design brief
v6  Scoring Sandbox         → parallel before/after comparison     📋 Future
v7  Production Scoring      → governance-approved metric impact    📋 Future
```

Each version is additive. Each is independently reversible. No version depends on the next being implemented. The system is always safe to operate at any version.
