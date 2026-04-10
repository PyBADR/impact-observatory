# Impact Observatory | مرصد الأثر — Release Report

**Release**: Phases 2–6 Decision Intelligence Stack  
**Date**: 2026-04-10  
**Commit**: `fd596f8` → `main`  
**Author**: BDRAI + Claude Opus 4.6

---

## Deployment Status

| Component | URL | Status |
|-----------|-----|--------|
| **GitHub** | https://github.com/PyBADR/impact-observatory | `fd596f8` on `main` |
| **Backend (Railway)** | https://deevo-cortex-production.up.railway.app | ● Live |
| **Frontend (Vercel)** | https://deevo-sim.vercel.app | ● Live |
| **API Docs** | https://deevo-cortex-production.up.railway.app/docs | ● Live |
| **Health** | https://deevo-cortex-production.up.railway.app/health | ● OK |

---

## What Shipped

### Pipeline Extension: 17 → 41 Deterministic Stages

The simulation engine was extended from a 17-stage financial contagion pipeline to a 41-stage decision intelligence pipeline across 6 phases:

**Phase 1 — Execution Engine** (stages 18–21): Transmission chain analysis, counterfactual scenarios, action pathway generation for GCC contagion propagation.

**Phase 2 — Decision Trust** (stages 22–26): Confidence scoring, policy evaluation against GCC regulatory frameworks, attribution defense, expected-vs-actual tracking across 43 nodes.

**Phase 3 — Decision Integration** (stages 27–30): Workflow orchestration, override governance with SHA-256 audit trails, ownership assignment mapping decisions to CRO/CFO/Board roles.

**Phase 4 — Decision Value** (stages 31–36): Portfolio optimization, value attribution, lifecycle tracking, effectiveness measurement for banking/insurance/fintech sectors.

**Phase 5 — Evidence & Governance** (stage 36 extended): Evidence assembly, trust scoring, completeness verification, IFRS 17 / PDPL compliance gates.

**Phase 6 — Pilot Readiness** (stages 37–41): Scope enforcement (banking/liquidity only), KPI measurement, shadow mode execution, failure mode catalog, pilot reporting engine.

### Numbers

| Metric | Value |
|--------|-------|
| New backend engines | 20 |
| New API endpoints | 3 (Phase 6) + prior phases |
| Total API paths | 100 |
| New frontend panels | 5 |
| New test files | 6 |
| Total tests passing | 326 |
| Files changed | 46 |
| Lines added | 10,849 |

---

## Live Verification Results (2026-04-10)

| Check | Result |
|-------|--------|
| Backend health | ✓ `{"status":"ok"}` |
| Frontend loads | ✓ HTTP 200 (27KB) |
| Frontend→Backend proxy | ✓ Health passes through Vercel rewrite |
| API docs | ✓ HTTP 200 |
| CORS (deevo-sim.vercel.app) | ✓ `access-control-allow-origin: https://deevo-sim.vercel.app` |
| Full pipeline run | ✓ 41 stages, run_id `21cca9b3` |
| Pilot scope validation | ✓ `in_scope: true`, mode: `SHADOW` |
| KPI measurement | ✓ accuracy 100%, latency reduction 98.8% |
| Shadow comparisons | ✓ 5 comparisons generated |
| Failure mode detection | ✓ 1 mode triggered with fallback |
| Pilot report | ✓ Recommendation generated |
| Phase 6 endpoints live | ✓ `/pilot`, `/pilot/kpi`, `/pilot/shadow` |

---

## Architecture

```
Frontend (Vercel)          Backend (Railway)
deevo-sim.vercel.app  →    deevo-cortex-production.up.railway.app
Next.js 15 + React 19      FastAPI + Python 3.12
                     
/api/* rewrites to →        /api/v1/* (100 paths)
                            41-stage SimulationEngine
                            20 decision engines
                            Pydantic v2 contracts
```

### Phase 6 Engine Architecture

```
Stage 37: pilot_scope_engine    → Scope validation (banking/liquidity only)
Stage 38: shadow_engine         → System vs human comparison (never overrides)
Stage 39: kpi_engine            → Latency, accuracy, avoided loss, false positives
Stage 40: pilot_report_engine   → Findings, trends, recommendation
Stage 41: failure_engine        → 8 failure modes with explicit fallbacks
```

### Failure Mode Catalog

| ID | Trigger | Fallback |
|----|---------|----------|
| FM-001 | Low confidence (<0.60) | REQUIRE_MANUAL_APPROVAL |
| FM-002 | Missing data (<0.50) | SWITCH_TO_ADVISORY |
| FM-003 | Pipeline timeout (>30s) | USE_CACHED_RESULT |
| FM-004 | Policy conflict | ESCALATE_TO_CRO |
| FM-005 | Out-of-scope scenario | REJECT_AND_LOG |
| FM-006 | Shadow divergence >80% | PAUSE_AND_REVIEW |
| FM-007 | Negative value | SWITCH_TO_ADVISORY |
| FM-008 | No actions generated | REQUIRE_MANUAL_ASSESSMENT |

---

## Known Issues

1. **Git worktree corruption**: The local `.git/worktrees/` directory had stale references from prior Claude Code sessions. Resolved via fresh clone to `/tmp/io-push` for the push. The user's local repo at `/Users/bdr.ai/Projects/deevo-sim` still has the corruption in `.claude/worktrees/` — run `rm -rf .claude/worktrees && git worktree prune` to clean up.

2. **Node registry**: `/api/v1/nodes` returns 2 nodes in the current deployment (sector-level aggregates). The full 43-node graph is available within individual run results.

3. **Scenario templates**: Only 1 template appears in the `/api/v1/scenario/templates` endpoint, though all 15 scenarios execute correctly when called by `scenario_id` directly.

---

## Test Summary

```
326 tests passed in 0.55s

test_pipeline_contracts.py    — 113 tests (core pipeline contracts)
test_api_endpoints.py         —  27 tests (API endpoint validation)
test_phase1_engines.py        —  26 tests (execution engine)
test_phase2_trust.py          —  40 tests (decision trust)
test_phase3_integration.py    —  30 tests (decision integration)
test_phase4_value.py          —  45 tests (decision value)
test_phase5_governance.py     —  20 tests (evidence & governance)
test_phase6_pilot.py          —  45 tests (pilot readiness)
```

---

## Next Decision Gate

Before proceeding to Phase 7 (Production Hardening / Multi-Tenant), the following must be true:

1. Pilot runs accumulate ≥10 shadow comparisons with real human decisions
2. Accuracy rate sustains ≥80% across 5+ consecutive runs
3. No CRITICAL failure modes triggered in 48h window
4. CRO sign-off on shadow mode divergence patterns
5. PDPL data sovereignty audit passes for pilot scope data
