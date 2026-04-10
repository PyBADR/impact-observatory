# Impact Observatory — Unified Flow Architecture

## Final Verdict: UNIFIED

---

## 1. Unified Flow Design (UI State)

### Flow State Machine: `store/flow-store.ts`

Single state machine governing the entire decision intelligence pipeline:

```
Signal (Jet Nexus) → Reasoning (TREK) → Simulation (Impact)
→ Decision → Outcome → ROI → Control Tower
```

**Key properties:**
- One active flow at a time (the "current scenario journey")
- Every stage transition is timestamped and traceable
- All UI components read from `useFlowStore` — no isolated state
- Personas read the SAME flow, rendered through different lenses
- Control Tower aggregates the full flow, not just the latest stage

**State shape:**
- `activeFlow: FlowInstance | null` — current journey
- `flowHistory: FlowInstance[]` — archived completed flows
- Each `FlowInstance` contains: stages[], context (RunResult + decisions + outcomes + values), health status

**Stage transitions driven by `runScenario()` in `page.tsx`:**
1. `startFlow()` → signal stage
2. `advanceStage("reasoning")` → API call initiated
3. `advanceStage("simulation")` → run processing
4. `advanceStage("decision")` → results available
5. `attachRunResult()` → full data in context
6. Outcomes/Values auto-advance via `useEffect` watchers
7. `completeFlow()` → control_tower stage, flow archived

---

## 2. Narrative Model: `lib/narrative-engine.ts`

### Structure
Every flow generates a `FlowNarrative` containing ordered `NarrativeBlock` entries:

| Block Type   | What it explains                          | Visible to          |
|-------------|-------------------------------------------|----------------------|
| `signal`     | What happened (trigger event)             | All personas         |
| `reasoning`  | Why it happened (TREK causal chain)       | Analyst, Regulator   |
| `simulation` | How it propagated (Impact simulation)     | All personas         |
| `decision`   | What decision was taken                   | All personas         |
| `outcome`    | What outcome occurred                     | All personas         |
| `roi`        | What value was generated                  | All personas         |
| `synthesis`  | System health + flow completion summary   | All personas         |

### Properties
- **Deterministic:** Same `FlowInstance` → same narrative (no randomness)
- **Traceable:** Every block has `dataTrail[]` mapping sentences to data fields
- **Persona-aware:** `filterBlocksByPersona()` returns only relevant blocks
- **Bilingual:** Each block has `textEn` and `textAr`

---

## 3. Component Wiring Plan

### Before (Fragmented)
```
page.tsx
├── ExecutiveView (isolated)
├── AnalystView (isolated)
├── RegulatorView (isolated)
├── ExecutiveControlTower (sub-panel of Executive only)
└── Detail panels (Executive-only tabs)
```

### After (Unified)
```
page.tsx
├── PersonaFlowView (single entry point)
│   ├── FlowExecutiveView
│   │   ├── FlowTimeline (compact)
│   │   └── UnifiedControlTower (central brain)
│   │       ├── SystemHealthBadge
│   │       ├── StageSummaryCards
│   │       ├── IntelligenceSummary (cross-layer)
│   │       ├── FlowNarrativePanel (persona-filtered)
│   │       └── ExecutiveControlTower (existing 5 panels)
│   ├── FlowAnalystView
│   │   ├── FlowTimeline (full)
│   │   ├── FlowNarrativePanel (reasoning-heavy)
│   │   └── AnalystView (existing mechanics)
│   └── FlowRegulatorView
│       ├── FlowTimeline (full)
│       ├── Flow Provenance Banner
│       ├── FlowNarrativePanel (audit-heavy)
│       └── RegulatorView (existing audit tables)
└── Sector Detail Panels (Banking/Insurance/Fintech/Decisions — shared across all personas)
```

### Data Flow (single source of truth)
```
API → useRunState (adapted RunResult)
    → useAppStore (outcomes, decisions, values via polling hooks)
    → useFlowStore (flow state machine, context accumulation)
    → PersonaFlowView → reads from all three stores
    → No duplicated fetching
```

---

## 4. Persona Rendering Logic

| Persona    | Flow Timeline | Narrative Focus    | Primary View                 | Drill-Down Access |
|-----------|--------------|--------------------|-----------------------------|-------------------|
| Executive | Compact       | Value + synthesis  | UnifiedControlTower (full)   | All sector tabs   |
| Analyst   | Full          | Reasoning + chain  | AnalystView + Narrative      | All sector tabs   |
| Regulator | Full + Banner | Audit + provenance | RegulatorView + Narrative    | All sector tabs   |

### Persona-Specific Narrative Visibility
- **Executive** sees: signal, simulation, decision, outcome, roi, synthesis
- **Analyst** sees: ALL blocks (including reasoning mechanics)
- **Regulator** sees: ALL blocks (including reasoning for audit)

---

## 5. Control Tower Integration

### Before
ExecutiveControlTower was a sub-component inside ExecutiveView — a dashboard panel, not a brain.

### After
`UnifiedControlTower` is the **central intelligence hub** of the system:

1. **System Health Badge** — real-time flow health (healthy/degraded/failed)
2. **Stage Summary Cards** — completed/active/failed/total stages
3. **Cross-Layer Intelligence Summary** — 6 cards consuming ALL layers:
   - Signals (live count)
   - Impact (total loss + classification)
   - Decisions (pipeline + operator)
   - Outcomes (total + confirmed)
   - ROI (net value)
   - Operator (decisions + closed)
4. **Flow Narrative** — persona-filtered story of the entire journey
5. **Existing Control Tower Panels** — Value Overview, Decision Narrative, Value Drivers, Outcome Performance, Risk & Loss

---

## 6. Files Created / Updated

### New Files
| File | Purpose | Layer |
|------|---------|-------|
| `store/flow-store.ts` | Unified flow state machine | State |
| `lib/narrative-engine.ts` | Deterministic narrative generation | Logic |
| `features/flow/FlowTimeline.tsx` | Visual pipeline indicator | UI |
| `features/flow/FlowNarrativePanel.tsx` | Persona-aware narrative display | UI |
| `features/flow/UnifiedControlTower.tsx` | Central intelligence hub | UI |
| `features/flow/PersonaFlowView.tsx` | Persona flow router | UI |
| `features/flow/index.ts` | Barrel exports | Module |

### Modified Files
| File | Change |
|------|--------|
| `app/page.tsx` | Replaced fragmented persona rendering with PersonaFlowView; integrated flow engine into runScenario; added flow context sync watchers; made sector drill-down tabs available to all personas |

### Preserved Files (no changes needed)
- `features/personas/ExecutiveView.tsx` — consumed by PersonaFlowView
- `features/personas/AnalystView.tsx` — consumed by PersonaFlowView
- `features/personas/RegulatorView.tsx` — consumed by PersonaFlowView
- `features/personas/ExecutiveControlTower.tsx` — consumed by UnifiedControlTower
- `store/app-store.ts` — single source of truth (unchanged)
- `lib/run-state.ts` — unified adapter (unchanged)
- `hooks/use-api.ts` — data polling (unchanged)

---

## 7. Decision Gates

### Gate 1: Flow Engine Operational
- [x] FlowStore creates, advances, and completes flows
- [x] Stage transitions are timestamped
- [x] Context accumulates RunResult + decisions + outcomes + values

### Gate 2: Narrative Engine Deterministic
- [x] Same FlowInstance produces same narrative
- [x] Every block maps to data fields (dataTrail)
- [x] Persona filtering works correctly

### Gate 3: UI Unified
- [x] Single PersonaFlowView entry point
- [x] FlowTimeline visible during active flow
- [x] Control Tower consumes all layers
- [x] Sector drill-downs available to all personas

### Gate 4: No Fragmentation
- [x] No disconnected dashboards
- [x] No isolated scenario pages
- [x] No duplicate data fetching
- [x] Everything connects to the flow

---

## Risk Register

| Risk | Probability | Mitigation |
|------|------------|------------|
| Flow store grows unbounded with long sessions | Low | `maxHistory: 20` cap on archived flows |
| Narrative blocks become stale after store updates | Medium | Narrative regenerated on every render via `useMemo` with flow dependency |
| FlowTimeline SSR hydration mismatch | Low | All flow components use `"use client"` directive |
| Existing persona views break with new wrapper | Low | PersonaFlowView wraps existing views; no internal changes needed |

---

## Observability Hooks

- Flow ID traceable across all stages
- Every stage transition includes timestamp + snapshot
- Narrative blocks include `dataTrail[]` for audit
- System health badge reflects real-time flow status
- Regulator view includes Flow Provenance Banner with flowId, createdAt, stage count

---

## Architecture Layer Mapping

| Layer | Component |
|-------|-----------|
| Data | `app-store.ts` (Zustand), `run-state.ts`, `use-api.ts` polling |
| Features | `flow-store.ts` (flow state machine) |
| Models | `narrative-engine.ts` (pure transformation) |
| Agents | Flow stage advancement in `runScenario()` |
| APIs | Unchanged — `POST /runs`, `GET /runs/:id` |
| UI | `PersonaFlowView`, `FlowTimeline`, `UnifiedControlTower`, `FlowNarrativePanel` |
| Governance | Narrative traceability, flow provenance, persona-based visibility |
