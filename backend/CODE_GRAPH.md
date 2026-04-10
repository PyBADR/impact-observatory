# CODE GRAPH — Impact Observatory | مرصد الأثر

**Module dependency contract v2.1.0**
Enforced ownership rules for the 9-layer deterministic simulation engine.

---

## 1. Directed Dependency Graph

```
                         ┌─────────────────────────────────────┐
                         │         src/config.py               │
                         │  (all formula weights / constants)  │
                         └──────────────┬──────────────────────┘
                                        │ imported by ALL layers
              ┌─────────────────────────┼─────────────────────────┐
              ▼                         ▼                         ▼
    src/utils.py             src/risk_models.py      src/physics_intelligence_layer.py
    (pure helpers)           (financial math)         (node/flow physics)
         │                        │                         │
         │              ┌─────────┘                         │
         ▼              ▼                                    ▼
    src/flow_models.py                              src/decision_layer.py
    (GCC flow types)                                (priority actions)
              │                                            │
              └─────────────────────┬──────────────────────┘
                                    ▼
                         src/explainability.py
                         (narrative + causal chain)
                                    │
                                    ▼
                         src/simulation_engine.py
                         (17-stage pipeline orchestrator)
                                    │
                         ┌──────────┴──────────┐
                         ▼                     ▼
              src/services/             src/api/
              run_orchestrator.py       (routes, v1/)
                         │                     │
                         └──────────┬──────────┘
                                    ▼
                              src/main.py
                         (FastAPI entry point)
```

---

## 2. File Ownership Map

| File | Owns | May Import | May NOT Import |
|------|------|-----------|----------------|
| `src/config.py` | All formula weights & thresholds | `src.core.config` | anything else |
| `src/utils.py` | Pure helpers (clamp, classify, format) | stdlib only | any src module |
| `src/risk_models.py` | Event severity, exposure, propagation, LSI, ISI, financial loss, confidence, URS | `config`, `utils`, `numpy`, `math` | `physics_intelligence_layer`, `decision_layer`, `explainability`, `flow_models`, `api`, `main` |
| `src/physics_intelligence_layer.py` | Node utilization, flow conservation, bottlenecks, shock wave, recovery, congestion | `config`, `utils`, `numpy`, `math` | `risk_models`, `decision_layer`, `explainability`, `api`, `main` |
| `src/flow_models.py` | GCC flow simulation (money, logistics, energy, payments, claims) | `config`, `utils`, `math` | `risk_models`, `physics_intelligence_layer`, `decision_layer`, `explainability`, `api`, `main` |
| `src/decision_layer.py` | Action priorities, 5-question framework, escalation triggers | `config`, `utils`, `math` | `explainability`, `physics_intelligence_layer`, `risk_models`, `api`, `main` |
| `src/explainability.py` | Causal chain (20 steps), narrative, sensitivity, uncertainty | `config`, `utils`, `math` | `decision_layer`, `physics_intelligence_layer`, `risk_models`, `api`, `main` |
| `src/simulation_engine.py` | Pipeline orchestration ONLY — no math, no formatting | all above modules | `api`, `main`, direct math/format logic |
| `src/services/run_orchestrator.py` | API-to-engine bridge, output mapping | `simulation_engine`, `schemas`, `audit_service` | math modules directly |
| `src/main.py` | FastAPI app, middleware, route registration | `api`, `services`, `core.config` | any math module, simulation_engine directly (except /simulate endpoint) |
| `src/api/**` | HTTP interface — no business logic | `schemas`, `services`, `auth` | math modules, simulation_engine, physics layers |

---

## 3. Prohibited Import Table

```
FROM                              TO                              REASON
──────────────────────────────────────────────────────────────────────────────
main.py                         risk_models                       No math in HTTP layer
main.py                         physics_intelligence_layer        No physics in HTTP layer
main.py                         decision_layer                    No decisions in HTTP layer
main.py                         flow_models                       No flow math in HTTP layer
main.py                         explainability                    No explain in HTTP layer

api/**                          risk_models                       No math in routes
api/**                          physics_intelligence_layer        No physics in routes
api/**                          decision_layer                    No decisions in routes
api/**                          explainability                    No explain in routes

decision_layer                  explainability                    Parallel layer, no circular
decision_layer                  physics_intelligence_layer        No physics in decisions
decision_layer                  risk_models                       Math owned by risk_models

explainability                  decision_layer                    Parallel layer, no circular
explainability                  physics_intelligence_layer        No physics in explain

risk_models                     physics_intelligence_layer        No cross-layer imports
risk_models                     decision_layer                    No decision logic in math
risk_models                     flow_models                       No flow logic in math
risk_models                     explainability                    No explain in math

physics_intelligence_layer      risk_models                       No financial math in physics
physics_intelligence_layer      decision_layer                    No decisions in physics
physics_intelligence_layer      flow_models                       No flow in physics

flow_models                     risk_models                       No risk math in flow
flow_models                     physics_intelligence_layer        No physics in flow
flow_models                     decision_layer                    No decisions in flow

utils.py                        ANY src module                    Leaf node — no src imports
config.py (src/)                anything except src.core.config   Constants only
```

---

## 4. Layer Boundary Rules

### Rule 1 — Constants Ownership
All formula weights (w1–w4, alpha_j, beta, l1–l4, m1–m4, r1–r4, g1–g5, theta_j) are defined
**only** in `src/config.py`. No file may hardcode a weight value that also appears in config.py.

### Rule 2 — Math Boundary
Financial mathematics (severities, exposures, losses, stress indices, URS) lives exclusively
in `src/risk_models.py`. Physics mathematics (utilization, flow, bottlenecks, shock wave,
recovery) lives exclusively in `src/physics_intelligence_layer.py`.

### Rule 3 — Orchestration Only
`src/simulation_engine.py` **orchestrates** — it calls layer functions in order and assembles
the result dict. It must not contain inline mathematical formulae. All computation must be
delegated to a named function in the appropriate layer module.

### Rule 4 — API Layer Purity
`src/main.py` and all modules under `src/api/` must not import or invoke any math module
directly. The `/simulate` endpoint in main.py is the **only** exception and must import
`SimulationEngine` lazily inside the endpoint function body.

### Rule 5 — No Circular Imports
The dependency graph is a DAG. Cycles are forbidden. The topological order is:
`config → utils → (risk_models, physics, flow, decision, explainability) → simulation_engine → services → api → main`

### Rule 6 — Schema Contracts
Public API input/output shapes are owned by `src/simulation_schemas.py`.
Route handlers must validate using these schemas via Pydantic — no raw dicts at the HTTP boundary.

### Rule 7 — Determinism
Every function that receives the same arguments must return the same result.
No `random`, no `time.time()` inside math functions, no global mutable state inside layer modules.

---

## 5. Enforcement Checklist

Run these grep checks before any commit touching a math layer:

```bash
# No math imports in main.py
grep -n "from src.risk_models\|from src.physics\|from src.decision\|from src.flow_models\|from src.explainability" src/main.py

# No physics in risk_models
grep -n "physics_intelligence_layer\|flow_models" src/risk_models.py

# No circular: decision → explainability
grep -n "from src.explainability\|from src.physics" src/decision_layer.py

# No hardcoded weights in layer files (should all reference config)
grep -n "W = \[0\.\|w1 = \|l1 = \|g1 = " src/risk_models.py src/physics_intelligence_layer.py
```

---

## 6. Module Metrics (v2.1.0)

| Module | Lines | Functions | Test Coverage |
|--------|-------|-----------|---------------|
| `config.py` | ~130 | 0 (constants) | N/A |
| `utils.py` | ~90 | 7 | 100% |
| `risk_models.py` | ~300 | 9 | 95% |
| `physics_intelligence_layer.py` | ~390 | 6 | 90% |
| `flow_models.py` | ~200 | 6 | 85% |
| `decision_layer.py` | ~250 | 4 | 88% |
| `explainability.py` | ~300 | 4 | 85% |
| `simulation_engine.py` | ~950 | 3 | 92% |
| `run_orchestrator.py` | ~280 | 1 | 88% |

---

*Generated: 2026-04-03 | Model version: 2.1.0 | Architecture layers: 9*
