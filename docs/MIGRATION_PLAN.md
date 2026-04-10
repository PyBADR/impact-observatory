# Impact Observatory | مرصد الأثر — Migration Plan

## Phase 0: Repository Audit Complete

### Current Repo Structure
```
deevo-sim/
├── frontend/          Next.js 14, React 18, Tailwind, dark theme
│   ├── app/           5 pages: home, demo, control-room, architecture, scenarios
│   ├── components/    15 components (control-room, decision, graph, globe, etc.)
│   ├── lib/           12 modules (propagation, decision, monte-carlo, scenarios, etc.)
│   └── styles/        Dark-first globals.css + tailwind.config.ts
├── backend/           FastAPI, PostgreSQL, Neo4j, Redis
│   ├── app/api/       11 routes (health, scenarios, entities, graph, decision, etc.)
│   ├── app/intelligence/  Engines + math + physics + insurance packages
│   ├── app/services/  9 services (orchestrator, scoring, physics, insurance, etc.)
│   ├── app/schema/    8 schema modules (geo, transport, events, actors, etc.)
│   ├── app/graph/     Neo4j client + nodes/edges/queries/schema
│   ├── app/db/        Postgres + Redis + Neo4j connectors
│   ├── app/scenarios/ Baseline, runner, shock, delta, explainer, templates
│   └── tests/         9 test files including golden suite
├── packages/          @deevo/gcc-knowledge-graph, @deevo/gcc-constants
└── docker-compose.yml PostGIS + Neo4j + Redis
```

## Keep / Refactor / Remove / Replace Matrix

### KEEP (Reusable Infrastructure)
| Component | Path | Reason |
|-----------|------|--------|
| Propagation Engine | backend/app/intelligence/engines/propagation_engine.py | Core formula, tested |
| Decision Engine | backend/app/intelligence/engines/decision_engine.py | DPS/APS, 18 actions |
| Scenario Engines | backend/app/intelligence/engines/scenario_engines.py | 17 engines, exact formulas |
| Monte Carlo | backend/app/intelligence/engines/monte_carlo.py | Box-Muller, seeded audit |
| GCC Constants | backend/app/intelligence/engines/gcc_constants.py | Canonical values |
| Math Core | backend/app/intelligence/math_core/ | 16 modules, tested |
| Physics Core | backend/app/intelligence/physics_core/ | 7 modules |
| Insurance Intelligence | backend/app/intelligence/insurance_intelligence/ | 4 modules |
| Insurance (original) | backend/app/intelligence/insurance/ | 7 modules |
| Physics (original) | backend/app/intelligence/physics/ | 11 modules |
| Math (original) | backend/app/intelligence/math/ | 7 modules |
| Schema Layer | backend/app/schema/ | 8 typed schemas |
| DB Connectors | backend/app/db/ | Postgres, Neo4j, Redis |
| Graph Client | backend/app/graph/ | Neo4j operations |
| Services | backend/app/services/ | 9 service modules |
| Connectors | backend/app/connectors/ | 5 data connectors |
| Seeds | backend/seeds/ | 8 seed files |
| Tests | backend/tests/ | 9 test files |
| Docker Compose | docker-compose.yml | PostGIS + Neo4j + Redis |
| @deevo/gcc-knowledge-graph | packages/ | 76 nodes, 191 edges, 17 scenarios |
| @deevo/gcc-constants | packages/ | Constants + freshness check |
| i18n | frontend/lib/i18n.ts | AR/EN bilingual |
| API Client | frontend/lib/api.ts, lib/api/ | Backend communication |
| Server Auth | frontend/lib/server/ | RBAC, audit, trace |

### REFACTOR (Keep but Transform)
| Component | What Changes |
|-----------|-------------|
| backend/app/main.py | Rename to Impact Observatory, update service names |
| backend/app/api/decision.py | Add financial_engine, banking_risk, fintech endpoints |
| backend/app/api/scenarios.py | Align with canonical Scenario object |
| backend/app/config/settings.py | Rename app identity |
| frontend/app/layout.tsx | White theme, new title, new metadata |
| frontend/tailwind.config.ts | Light color palette |
| frontend/styles/globals.css | White base, clean shadows |
| frontend/components/ui/Navbar.tsx | New nav labels, new brand |
| frontend/lib/types.ts | Add FinancialImpact, BankingStress, etc. |

### REMOVE (Obsolete)
| Component | Reason |
|-----------|--------|
| frontend/app/page.tsx (landing) | Dark marketing page, not financial-first |
| frontend/app/architecture/page.tsx | Dev showcase, not executive view |
| frontend/components/ui/Footer.tsx | Marketing footer |
| frontend/components/ui/SectionHeading.tsx | Marketing component |
| frontend/lib/mock-data.ts | Replace with live API |
| Dark theme CSS (#06060A palette) | Replaced by white/light |

### REPLACE (New Implementation)
| Component | Replaces | New Purpose |
|-----------|----------|-------------|
| frontend/app/page.tsx | Old landing | Executive dashboard |
| frontend/app/observatory/page.tsx | control-room | Financial stress dashboard |
| frontend/components/observatory/ | control-room/ | Executive cards + sector views |
| backend/app/api/observatory.py | NEW | Unified observatory API |
| backend/app/intelligence/financial/ | NEW | BankingStress, InsuranceStress, FintechStress |
