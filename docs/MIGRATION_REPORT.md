# Migration Execution Report

Impact Observatory | مرصد الأثر — Controlled In-Place Replatforming

Generated: 2026-04-01

## Step 1: Repository Audit

Classified 144+ Python files, 15+ frontend components, 12 frontend lib modules.

KEEP: All intelligence engines (propagation, scenario, decision, monte carlo, gcc_constants), all math_core (16 modules), physics_core (7 modules), insurance_intelligence (4 modules), graph layer (5 modules), Docker Compose, database connectors, test golden suite.

REFACTOR: main.py (identity), settings.py (app name, DB name), Navbar (brand), layout.tsx (theme), API routers (add observatory), schemas (add financial sector models).

REPLACE: globals.css (dark → light), tailwind.config.ts (dark palette → light), page.tsx (marketing → executive dashboard), README.md (outdated → canonical brief).

REMOVE: Nothing removed yet. Dead code removal deferred to Step 8 per migration rules.

## Step 2: Structure Refactored

Directories created per target structure:

```
backend/app/api/            — 15 routers including observatory.py (NEW)
backend/app/schemas/        — observatory.py with 12 canonical domain objects (NEW)
backend/app/services/       — 12 service modules (6 NEW: financial, banking, insurance, fintech, decision, explainability, reporting, audit)
backend/app/intelligence/   — KEPT: engines, math_core, physics_core, insurance_intelligence
backend/app/graph/          — KEPT: client, nodes, edges, queries, schema
backend/app/orchestration/  — Directory created (ready for flow orchestrator)
backend/app/rules/          — Directory created (ready for regulatory rules)
frontend/features/          — 5 feature directories (dashboard, banking, insurance, fintech, decisions)
frontend/theme/             — Directory created
config/                     — project.yml canonical config
```

## Step 3: Product Renamed

Old: DecisionCore Intelligence, Deevo Sim, Deevo Intelligence Core
New: Impact Observatory | مرصد الأثر

Files touched: 38+ files across frontend, backend, docs, tests, seeds. Grep verification: zero remaining legacy references in main repo.

## Step 4: Domain Models Aligned

12 canonical objects implemented in `backend/app/schemas/observatory.py`:

| Object | Status | Fields |
|--------|--------|--------|
| Scenario (ScenarioInput) | DONE | id, name, name_ar, severity, duration_days, description |
| Entity | DONE | id, name, name_ar, layer, sector, severity, metadata |
| Edge | DONE | source, target, weight, propagation_factor, edge_type |
| FlowState | DONE | timestep, entity_states, total_stress, peak_entity, converged |
| FinancialImpact | DONE | headline_loss_usd, peak_day, time_to_failure_days, severity_code, confidence |
| BankingStress | DONE | liquidity_gap_usd, capital_adequacy_ratio, interbank_rate_spike, time_to_liquidity_breach_days, fx_reserve_drawdown_pct, stress_level |
| InsuranceStress | DONE | claims_surge_pct, reinsurance_trigger, combined_ratio, solvency_margin_pct, time_to_insolvency_days, premium_adequacy, stress_level |
| FintechStress | DONE | payment_failure_rate, settlement_delay_hours, gateway_downtime_pct, digital_banking_disruption, time_to_payment_failure_days, stress_level |
| DecisionAction | DONE | id, title, title_ar, urgency, value, priority, cost_usd, loss_avoided_usd, regulatory_risk, sector, description |
| DecisionPlan | DONE | plan_id, name, name_ar, actions, total_cost_usd, total_loss_avoided_usd, net_benefit_usd, execution_days, sectors_covered |
| RegulatoryState | DONE | pdpl_compliant, ifrs17_impact, basel3_car_floor, sama_alert_level, cbuae_alert_level, sanctions_exposure, regulatory_triggers |
| ExplanationPack | DONE | summary_en, summary_ar, key_findings, causal_chain, confidence_note, data_sources, audit_trail |

## Step 5: Backend Services Refactored

12/12 required modules operational:

| Module | Location | Status |
|--------|----------|--------|
| scenario_engine | intelligence/engines/scenario_engines.py | KEPT (17 engines, 45KB) |
| physics_engine | intelligence/physics_core/ | KEPT (7 modules) |
| entity_graph_service | graph/ | KEPT (5 modules) |
| propagation_engine | intelligence/engines/propagation_engine.py | KEPT (563 lines) |
| financial_engine | services/financial/engine.py | NEW (80 lines) |
| banking_risk_engine | services/banking/engine.py | NEW (100 lines) |
| insurance_risk_engine | services/insurance/engine.py | NEW (100 lines) |
| fintech_engine | services/fintech/engine.py | NEW (102 lines) |
| decision_engine | services/decision/engine.py | NEW (239 lines) |
| explainability_engine | services/explainability/engine.py | NEW (155 lines) |
| reporting_service | services/reporting/engine.py | NEW (155 lines) |
| audit_service | services/audit/engine.py | NEW (130 lines) |

Observatory API router: `backend/app/api/observatory.py` (405 lines) — wired to main.py.

## Step 6: Frontend UI Redesigned

Theme: Dark (#06060A) → Light (#F8FAFC)
Palette: Deep blue primary (#0F172A), accent (#1D4ED8), boardroom aesthetic
Layout: Executive dashboard (page.tsx) — KPI cards top, financial impact middle, sector stress right, decisions bottom
Bilingual: Arabic (default) + English, RTL/LTR switching preserved
Graph/Map: Moved to secondary views (control-room, observatory routes)

Files replaced: tailwind.config.ts, globals.css, page.tsx, layout.tsx, Navbar.tsx

## Step 7: V1 Hormuz Closure

Pipeline validated end-to-end (severity=0.85, 14 days):

| Output | Value |
|--------|-------|
| Headline Loss | $624.8B |
| Severity | CRITICAL |
| Peak Day | Day 7 |
| Time to Failure | 16 days |
| Banking Stress | CRITICAL (CAR 9.5%) |
| Insurance Stress | HIGH (CR 1.25, +42% claims surge) |
| Fintech Stress | CRITICAL (13.1% payment failure, 65h delay) |
| Decision #1 | Emergency Liquidity Facility — $2.5B cost, avoids $45B |
| Decision #2 | Payment System Backup — $350M cost, avoids $8B |
| Decision #3 | Reinsurance Treaty Activation — $800M cost, avoids $12B |
| Explanation | 5 findings, 10-node causal chain |
| Reports | Executive, Analyst, Regulatory Brief modes |
| Audit | SHA-256 hash, decision provenance, PDPL compliance |

## Step 8: Dead Code Status

Not yet removed. Per migration rules, dead code removal happens only after new flow is confirmed working. Current dead code candidates:

- frontend/app/page.tsx old marketing content (REPLACED)
- Old dark theme tokens (REPLACED in tailwind.config.ts and globals.css)
- Duplicate insurance modules (intelligence/insurance/ vs intelligence/insurance_intelligence/) — consolidation pending
- Legacy demo routes (api/demo_routes.py) — review pending

## Risks and Safeguards

| Risk | Probability | Mitigation |
|------|-------------|------------|
| Existing golden tests break with new schemas | MEDIUM | Tests use existing engines directly; observatory schemas are additive, not breaking |
| Docker Compose DB name change (decision_core → impact_observatory) | LOW | Settings.py env_prefix DC7_ allows override; compose uses env vars |
| Frontend ds-* class references in components not yet migrated | MEDIUM | Tailwind ds-* tokens preserved in new config for backward compatibility |
| Insurance module duplication | LOW | Both paths kept; new observatory uses services/insurance/engine.py |
| Model drift on deterministic engines | LOW | Seeded RNG, golden test suite (63 tests), SHA-256 audit trail |
| PDPL data sovereignty | LOW | All computation local; no external API calls in pipeline |

## Architecture

```
Runtime Flow (10 stages):
Scenario → Physics → Graph Snapshot → Propagation → Financial →
Sector Risk → Regulatory → Decision → Explanation → Output

API: POST /api/v1/observatory/run
     GET  /api/v1/observatory/labels
     GET  /api/v1/observatory/flow

Stack: FastAPI + Next.js 14 + PostgreSQL/PostGIS + Neo4j + Redis
Theme: White/light executive (#F8FAFC), boardroom aesthetic
Locale: Arabic (default) + English
```
