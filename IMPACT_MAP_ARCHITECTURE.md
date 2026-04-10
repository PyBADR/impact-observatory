# Impact Map Architecture — Palantir-Level Graph Intelligence

## 1. Current Impact Map Failure Diagnosis

### Root Cause #1: Field Name Mismatch (HTTP 422)
**File:** `backend/src/schemas/scenario.py`
**Symptom:** "Analysis Run Failed (422)" in the UI
**Chain:**
1. Frontend sends `POST /api/v1/runs` with body `{ template_id: "hormuz_full_closure", severity: 0.7 }`
2. Pydantic `ScenarioCreate` requires `scenario_id` (no alias for `template_id`)
3. Base model has `extra="ignore"` → silently drops `template_id`
4. `scenario_id` is required (`...`) → 422 Validation Error
5. Frontend catches non-200 → shows "Analysis Run Failed"

### Root Cause #2: Missing `map_payload` in Response
**File:** `backend/src/services/run_orchestrator.py`
**Symptom:** Map shows "Geospatial analysis is not available" even on successful runs
**Chain:**
1. Orchestrator assembles response at line 468 — no `map_payload` field
2. Frontend reads `result.map_payload?.impacted_entities` → always `undefined`
3. `mapSupported = entities.length > 0` → always `false`
4. Renders `MapCapabilityState` instead of `EntityLayer`

### Root Cause #3: Missing ImpactOverlay Fields
**File:** `backend/src/services/run_orchestrator.py`
**Symptom:** ImpactOverlay crashes with undefined access
**Missing fields:** `sector_rollups`, `decision_inputs`, `confidence`, `trust`, `headline.total_nodes_impacted`

## 2. Root Cause and Immediate Fix (COMPLETED)

### Fix #1: AliasChoices for `scenario_id`
```python
# backend/src/schemas/scenario.py
scenario_id: str = Field(
    ...,
    validation_alias=AliasChoices("scenario_id", "template_id"),
)
```
Both `scenario_id` and `template_id` now accepted.

### Fix #2: `map_payload_engine.py` + Orchestrator Wiring
New file: `backend/src/engines/map_payload_engine.py`
- `build_map_payload()` → converts financial_impacts + GCC_NODES into geo-located entities
- `build_graph_payload()` → 43 nodes + 188 edges from GCC_ADJACENCY
- `build_propagation_steps()` → handles both path-based and entity_id-based chain formats
- All wrapped in try/except with empty fallback (never crashes pipeline)

### Fix #3: ImpactOverlay Compatibility Fields
Added to orchestrator response: `sector_rollups`, `decision_inputs`, `confidence`, `trust`, `headline.total_nodes_impacted`, `headline.propagation_depth`

### Verification
- 336 tests passed (113 contract + 223 bridge)
- 0 TypeScript errors
- Full contract test: 4 entities with geo-coordinates, 43 graph nodes, 188 edges, 12 propagation steps

---

## 3. Unified Impact Map Contract

```typescript
interface ImpactMapResponse {
  runId: string;
  scenario: {
    scenario_id: string;
    label: string;
    label_ar: string;
    severity: number;
    horizon_hours: number;
  };
  nodes: ImpactNode[];           // From graph_payload.nodes
  edges: ImpactEdge[];           // From graph_payload.edges
  propagationEvents: PropagationStep[];  // From propagation_steps
  decisionOverlays: MapDecisionOverlay[];  // Phase 4 (future)
  headline: string;              // Narrative headline
  validationFlags: ValidationFlag[];
}
```

**Source of truth:** `backend/src/engines/map_payload_engine.py`
**Backend builder:** Called inline by `run_orchestrator.py` — NOT a separate endpoint
**Frontend consumer:** `useGlobeEntities.ts` reads `result.map_payload.impacted_entities`
**Migration:** Old `GET /runs/{id}/map` endpoint remains for backward compat

---

## 4. Graph Core Architecture

### A. Node Schema (9 Types)

| Type | Sector | Example | Count in GCC_NODES |
|------|--------|---------|-------------------|
| PORT | maritime | Jebel Ali Port | 6 |
| SHIPPING_LANE | maritime | GCC Shipping Lanes | 1 |
| ENERGY_ASSET | energy | Saudi Aramco, Qatar LNG | 6 |
| BANK | banking | ADCB, QNB, KFH | 8 |
| FINTECH | fintech | STC Pay, Tamara | 5 |
| INSURER | insurance | Tawuniya, OIC | 5 |
| PAYMENT_RAIL | fintech | UAEFTS, SADAD | 4 |
| MARKET_INFRA | infrastructure | DFM, Tadawul | 4 |
| REGULATOR | government | CBUAE, SAMA | 4 |

Each node carries: `id`, `label`, `label_ar`, `country`, `lat`, `lng`, `sector`, `criticality` (systemic importance), `sensitivity` (by scenario type → future), `stress` (current), `time_to_failure` (computed by propagation engine), `status` (NOMINAL→WATCH→STRESSED→BREACHED→FAILED), `source_confidence`, `source_lineage`

### B. Edge Schema (8 Types)

| Type | Meaning | Weight Source |
|------|---------|--------------|
| LIQUIDITY_DEPENDENCY | Interbank lending | criticality × 0.88 |
| PAYMENT_DEPENDENCY | Settlement routing | TX_SECTOR_TRANSFER[fintech] |
| TRADE_FLOW | Goods/commodity flow | capacity × current_load |
| ENERGY_SUPPLY | Oil/gas supply chain | production dependency |
| INSURANCE_CLAIMS_LINK | Claims exposure | TX_SECTOR_TRANSFER[insurance] |
| REGULATORY_CONTROL | Regulatory oversight | criticality |
| CORRESPONDENT_BANKING | Cross-border banking | TX_SECTOR_TRANSFER[banking] |
| SETTLEMENT_ROUTE | Payment clearing | TX_SECTOR_DELAY[fintech] |

Each edge: `source`, `target`, `type`, `weight`, `delay_hours`, `transfer_coefficient`, `reversibility`, `breakability`, `confidence`, `rationale`

### Storage
- Phase 1: In-memory dict (GCC_ADJACENCY already exists with 188 edges)
- Phase 2: PostgreSQL `impact_nodes` / `impact_edges` tables
- Phase 3: Optional Neo4j for graph queries (only if traversal complexity demands it)

### Graph Selection by Scenario Type
```python
SCENARIO_SUBGRAPH: dict[str, set[str]] = {
    "MARITIME":    {"PORT", "SHIPPING_LANE", "ENERGY_ASSET", "INSURER", "BANK"},
    "ENERGY":      {"ENERGY_ASSET", "BANK", "MARKET_INFRA", "INSURER", "PORT"},
    "LIQUIDITY":   {"BANK", "PAYMENT_RAIL", "FINTECH", "REGULATOR", "INSURER"},
    "CYBER":       {"PAYMENT_RAIL", "FINTECH", "BANK", "MARKET_INFRA", "REGULATOR"},
    "REGULATORY":  {"REGULATOR", "BANK", "INSURER", "MARKET_INFRA", "ENERGY_ASSET"},
}
```

---

## 5. Propagation Engine Design

### Architecture: Graph-first, timeline-aware, decision-interruptible

**A. Subgraph Selection**
For each scenario type, filter GCC_NODES and GCC_ADJACENCY to the relevant subgraph using `SCENARIO_SUBGRAPH`. This reduces the 43-node graph to ~15-25 relevant nodes.

**B. Shock Initialization**
```python
origin_nodes = SCENARIO_CATALOG[scenario_id]["origin_nodes"]
for node in origin_nodes:
    node.stress = severity
    node.status = "STRESSED"
    node.time_to_failure = estimate_ttf(node, severity)
```

**C. Shock Transfer Formula**
```
stress_transfer(target) = Σ(source ∈ neighbors) [
    source.stress
    × edge.transfer_coefficient
    × edge.weight
    × target.sensitivity
    × decay(edge.delay_hours)
]

decay(hours) = e^(-α × hours / TX_BASE_DELAY_HOURS)
```

Where `α = PHYS_ALPHA = 0.08` (already in config.py).

**D. Node State Transitions**
```
NOMINAL  → stress < 0.20
WATCH    → 0.20 ≤ stress < 0.35
STRESSED → 0.35 ≤ stress < 0.65
BREACHED → 0.65 ≤ stress < 0.80
FAILED   → stress ≥ 0.80
```

**E. Time-to-Failure Estimation**
```python
def estimate_ttf(node, stress, propagation_speed):
    if stress < BREAKABLE_SEVERITY_THRESHOLD:
        return None  # Won't fail
    base_ttf = TX_CRITICAL_WINDOW_HOURS / (stress * propagation_speed)
    redundancy_factor = 1.0 + node.redundancy * 2.0
    return base_ttf * redundancy_factor
```

---

## 6. Decision Overlay Design

### Decision Action Modes
| Mode | Graph Mutation | Example |
|------|---------------|---------|
| CUT | Remove edge entirely | Sever interbank dependency |
| DELAY | Increase edge.delay_hours | Extend settlement window |
| REDIRECT | Change edge.target | Reroute shipping to Salalah |
| BUFFER | Reduce edge.transfer_coefficient | Inject liquidity buffer |
| NOTIFY | No mutation (alert only) | Notify regulator |
| ISOLATE | Remove all edges to/from node | Quarantine compromised system |

### Decision Overlay Schema
```typescript
interface MapDecisionOverlay {
  decision_id: string;
  action_mode: "CUT" | "DELAY" | "REDIRECT" | "BUFFER" | "NOTIFY" | "ISOLATE";
  target_nodes: string[];
  target_edges: { source: string; target: string }[];
  owner: string;
  approver: string | null;
  time_to_act_hours: number;
  expected_impact_usd: number;
  cost_usd: number;
  status: "PROPOSED" | "APPROVED" | "EXECUTING" | "COMPLETED";
}
```

### Before/After Simulation
Three map modes:
1. **No-Action:** Propagation runs to completion (baseline)
2. **Recommended:** Apply top-5 decision overlays, re-run propagation
3. **Alternative:** Apply alternative decision set, compare

---

## 7. Executive War Room UX Plan

### Screen Composition (top → bottom priority)

```
┌─────────────────────────────────────────────────────────┐
│ PROPAGATION HEADLINE                                     │
│ "Hormuz closure propagates to 12 nodes in 48h.          │
│  First breach: ADCB liquidity (18h). Decision ACT-001   │
│  interrupts chain at banking layer."                     │
├──────────────────┬──────────────────────────────────────┤
│ TOP 3 IMPACTED   │                                      │
│ ┌──────────────┐ │           IMPACT MAP                 │
│ │ 1. Hormuz    │ │     (EntityLayer + edges +           │
│ │ FAILED 0.92  │ │      propagation animation +         │
│ │ $5.0B loss   │ │      decision overlay)               │
│ ├──────────────┤ │                                      │
│ │ 2. Dubai Port│ │    ● ← stressed node                │
│ │ BREACHED 0.71│ │    ◉ ← bottleneck                   │
│ │ $1.2B loss   │ │    ─── ← active dependency          │
│ ├──────────────┤ │    ╳── ← CUT by decision            │
│ │ 3. ADCB      │ │    ⋯── ← DELAYED by decision       │
│ │ STRESSED 0.58│ │                                      │
│ │ TTF: 18h     │ │                                      │
│ └──────────────┘ │                                      │
├──────────────────┤                                      │
│ FIRST BREACH     │                                      │
│ ADCB liquidity   │                                      │
│ in 18 hours      │                                      │
│ LCR drops to 0.87│                                      │
├──────────────────┤                                      │
│ CHAIN BREAKER    │                                      │
│ ACT-001: Activate│                                      │
│ emergency liq.   │                                      │
│ Cost: $500M      │                                      │
│ Saves: $3.2B     │                                      │
│ [APPROVE]        │                                      │
└──────────────────┴──────────────────────────────────────┘
```

### Map Layers (render order)
1. Base geography (dark slate bg with GCC region outline)
2. All 43 nodes (sized by criticality, colored by stress)
3. Dependency edges (188 edges, opacity by weight)
4. Propagation path (animated pulse along affected edges)
5. Stress state coloring (NOMINAL→CRITICAL color scale)
6. Decision overlay (CUT/DELAY/REDIRECT visual indicators)

### Interaction Model
- Click node → detail panel (stress, TTF, loss, sector)
- Click edge → dependency info (type, transfer coefficient, delay)
- Toggle layers → show/hide edge types, decision overlays
- Time slider → step through propagation timeline
- Mode switch → No-Action / Recommended / Alternative

---

## 8. GitHub Patterns to Borrow

### Borrow
- **NetworkX traversal logic**: BFS/DFS for propagation with weighted edges. Adapt for the `GCC_ADJACENCY` dict structure.
- **D3 force-directed layout**: For the graph visualization within the map. Use d3-force for node positioning when not using geo-coordinates.
- **deck.gl ArcLayer**: For animated propagation arcs between geo-located nodes. Can overlay on the existing EntityLayer.
- **Palantir timeline pattern**: Timeline scrubber that steps through propagation events. Each step shows which nodes transition state.

### Do NOT Borrow
- **Neo4j** — Overkill for 43 nodes / 188 edges. The in-memory dict is sufficient.
- **Full Cesium 3D globe** — Too heavy for the current use case. The 2D SVG EntityLayer is more appropriate for a war room.
- **Mapbox GL JS** — Requires token and adds bundle weight. The mercator projection in EntityLayer is sufficient for GCC region.
- **Generic dashboard templates** — The war room layout must be purpose-built for the 4 questions, not a generic grid.

### Adapt Without Drift
- Keep all graph logic in `backend/src/engines/` — never in frontend
- Keep all map data in the unified pipeline response — no separate API calls
- Keep the SVG EntityLayer as the base — enhance it with edges and overlays, don't replace it

---

## 9. Sprint-by-Sprint Build Plan

### Sprint 1: Recovery (COMPLETED)
- [x] Fix `template_id` → `scenario_id` alias
- [x] Build `map_payload_engine.py`
- [x] Wire map_payload + graph_payload into orchestrator
- [x] Add ImpactOverlay compatibility fields
- [x] Fallback-safe try/except wrappers
- [x] 336 tests passing

### Sprint 2: Graph Core (1 week)
- [ ] Create typed `ImpactNode` / `ImpactEdge` Pydantic models in `backend/src/schemas/impact_graph.py`
- [ ] Extend `GCC_NODES` with `sensitivity_by_type`, `redundancy`, `node_type` fields
- [ ] Type `GCC_ADJACENCY` edges with `type`, `delay_hours`, `transfer_coefficient`
- [ ] Build `SCENARIO_SUBGRAPH` selector in `backend/src/engines/graph_selector.py`
- [ ] Add `GET /api/v1/graph/subgraph?scenario_type=MARITIME` endpoint
- [ ] Write 50+ graph contract tests

### Sprint 3: Propagation Engine (1 week)
- [ ] Build `backend/src/engines/propagation_engine_v2.py` with:
  - Subgraph selection
  - BFS shock initialization at origin nodes
  - Iterative stress transfer with delay decay
  - Node state transitions (NOMINAL → FAILED)
  - Time-to-failure estimation per node
- [ ] Wire into orchestrator as new pipeline stage
- [ ] Add propagation timeline to response: `propagation_timeline: [{t: 0, nodes: [...], edges: [...]}]`
- [ ] Write parametrized tests across all 15 scenarios

### Sprint 4: Decision Overlay (1 week)
- [ ] Build `backend/src/engines/decision_overlay_engine.py`:
  - 6 action modes (CUT, DELAY, REDIRECT, BUFFER, NOTIFY, ISOLATE)
  - Graph mutation functions per mode
  - Before/after propagation comparison
- [ ] Extend `DecisionObject` with `action_mode`, `target_nodes`, `target_edges`
- [ ] Add `POST /api/v1/runs/{id}/simulate-decision` endpoint
- [ ] Build counterfactual: no-action vs recommended vs alternative
- [ ] Write decision overlay integration tests

### Sprint 5: War Room UX (1 week)
- [ ] Refactor `frontend/src/app/map/page.tsx` into war room layout:
  - Propagation headline (auto-generated from narrative engine)
  - Top 3 impacted nodes panel
  - First breach forecast panel
  - Chain breaker decision panel
- [ ] Enhance `EntityLayer.tsx`:
  - Render edges between nodes (SVG lines with opacity)
  - Animate propagation pulse along affected paths
  - Decision overlay indicators (CUT = red X, DELAY = dashed, etc.)
- [ ] Add layer toggle controls
- [ ] Add time slider for propagation timeline
- [ ] Add mode switch (No-Action / Recommended / Alternative)

---

## 10. Immediate File Change Targets

| Priority | File | Change |
|----------|------|--------|
| DONE | `backend/src/schemas/scenario.py` | `AliasChoices("scenario_id", "template_id")` |
| DONE | `backend/src/engines/map_payload_engine.py` | NEW — map/graph/propagation builders |
| DONE | `backend/src/services/run_orchestrator.py` | Wire map_payload, graph_payload, sector_rollups, decision_inputs |
| Sprint 2 | `backend/src/schemas/impact_graph.py` | NEW — ImpactNode, ImpactEdge Pydantic models |
| Sprint 2 | `backend/src/engines/graph_selector.py` | NEW — subgraph selection by scenario type |
| Sprint 2 | `backend/src/simulation_engine.py` | Extend GCC_NODES with typed edges |
| Sprint 3 | `backend/src/engines/propagation_engine_v2.py` | NEW — graph-first propagation with TTF |
| Sprint 4 | `backend/src/engines/decision_overlay_engine.py` | NEW — 6 action modes + graph mutation |
| Sprint 5 | `frontend/src/app/map/page.tsx` | War room layout refactor |
| Sprint 5 | `frontend/src/features/globe/EntityLayer.tsx` | Add edges, propagation animation, overlays |
