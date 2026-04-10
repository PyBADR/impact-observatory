# MACRO UI REPOSITIONING PACK — Architecture Brief

**Date:** 2026-04-08
**Author:** Principal Product Architect
**Scope:** UI narrative repositioning — no backend changes, no new features
**Target:** Shift first impression from event-first / graph-first → macro-first / transmission-first / exposure-first / decision-first

---

## 1. CURRENT STATE AUDIT

The product has two UI surfaces that serve different roles:

**Surface A — Landing + Results** (`/` → `page.tsx`, ~1050 lines)

The root page is a 3-phase SPA: Landing → Scenario Selector → Results. The landing page is well-positioned — it already frames the product as "Decision Intelligence Platform · GCC Financial Markets" with macro-level metrics (31 entities, $2.1T GDP, 6 modules). The scenario selector is event-first by design (the user chooses an event), which is correct for that step. The results view routes through a `PersonaFlowView` component with tabs (Overview, Banking, Insurance, Fintech, Decisions).

**Surface B — Decision Command Center** (`/command-center/page.tsx`, 373 lines)

This is the single-screen intelligence terminal, accessed via `?run=<id>`. Its layout was already repositioned in a prior iteration to macro-first, with this hierarchy:

| Row | Component | Width | Current Framing |
|-----|-----------|-------|-----------------|
| 1 | `MacroOverviewHeader` | 12 col | **GCC Macro Overview** — System Risk Index, affected regions, KPIs |
| 2 | `TransmissionChannels` | 12 col | 4 channel cards: Oil & Energy, Liquidity & FX, Trade & Ports, Insurance & Fintech |
| 3 | `ExposureLayer` | 12 col | Country exposure (6 GCC nations) + Sector exposure (ranked by stress) |
| 4 | `GraphPanel` / `PropagationView` / `DecisionPanel` | 4+4+4 col | Graph, causal chain, ranked actions |
| 5 | `SectorRollupBar` | 12 col | Horizontal sector stress strip |
| 6 | `ImpactPanel` | 12 col | Per-entity impact grid |
| 7 | `ExplanationPanel` | 12 col | Narrative, methodology, audit trail |
| 8 | `StatusBar` | 12 col | Pipeline meta: LIVE/MOCK, stages, confidence, audit hash |

**Surface C — Secondary Pages** (`/graph-explorer`, `/map`, `/decisions`)

Graph explorer, impact map, and decisions page. These are deep-dive tools and should remain subordinate. They are correctly linked from the top nav as secondary destinations.

---

## 2. DIAGNOSIS: WHERE THE EVENT-FIRST / GRAPH-FIRST FRAMING PERSISTS

After auditing every component, the macro-first repositioning is **partially complete** on Surface B but **not executed** on Surface A. Here are the specific gaps:

### 2.1 Surface A — Results View (the primary gap)

**Problem:** When a user runs a scenario from the landing page and arrives at the results view, they see `PersonaFlowView` which is organized by persona (Executive / Analyst / Regulator), not by macro context. The tab bar reads: Overview | Banking | Insurance | Fintech | Decisions. This is a **sector-first** framing, not a macro-first framing.

**Impact:** The user's first post-analysis impression is "which sector was hit?" rather than "what is the GCC-wide macro picture, how did the shock transmit, where is exposure concentrated, and what should I do?"

**Root cause:** The results view was never connected to the repositioned Command Center layout. It uses a separate component tree (`PersonaFlowView`, `ExecutiveView`, `AnalystView`, `RegulatorView`) that predates the macro-first design.

### 2.2 Surface B — Command Center (mostly done, minor gaps)

| Component | Issue | Severity |
|-----------|-------|----------|
| `MacroOverviewHeader` | Row 3 still says "Active Scenario" — the word "scenario" anchors thinking to the event, not the macro state | Low |
| `GraphPanel` header | Panel label says nothing — no macro context for why the graph matters | Low |
| `PropagationView` header | "Causal cascade" — correct framing, but could be labeled "Transmission Mechanics" to match the macro vocabulary | Low |
| `EventHeader` | Legacy component, still exported in barrel (`index.ts`) but no longer imported by `page.tsx` — dead code | Housekeeping |
| Nav cross-links (Surface A) | "Propagation" and "Impact Map" labels in the top nav — correct | None |

### 2.3 Surface A — Landing Page (well-positioned)

The landing page already uses macro framing: "Financial impact intelligence for GCC institutions", "Quantitative shock propagation modeling", 6 analysis modules. No repositioning needed here.

### 2.4 Surface A — Scenario Selector (correctly event-first)

The scenario selector is the one place where event-first framing is appropriate — the user is choosing an event. However, we should reframe it from "Select a Scenario" to "Select a Macro Stress Event" to maintain the macro vocabulary.

---

## 3. PROPOSED SCREEN HIERARCHY

The repositioned read-order for the results experience (Surface A + B unified):

```
┌─────────────────────────────────────────────────────────────────────┐
│  TOP NAV — "Impact Observatory" + Persona + Lang + Run Scenario     │
├─────────────────────────────────────────────────────────────────────┤
│  TAB BAR (repositioned):                                            │
│   Macro Overview | Transmission | Exposure | Decisions | Sectors    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  TAB: Macro Overview (default, replaces "Overview/Dashboard")       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  MacroOverviewHeader (System Risk, KPIs, regions)           │    │
│  │  TransmissionChannels (4 channel cards)                     │    │
│  │  ExposureLayer (country + sector)                           │    │
│  │  SectorRollupBar (horizontal stress strip)                  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  TAB: Transmission (replaces ad-hoc graph)                          │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  PropagationView (causal cascade — full width)              │    │
│  │  GraphPanel (node-link graph — full width, expandable)      │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  TAB: Exposure (replaces Banking/Insurance/Fintech tabs)            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  ImpactPanel (per-entity grid, all sectors unified)         │    │
│  │  BankingDetailPanel  (inline expandable)                    │    │
│  │  InsuranceDetailPanel (inline expandable)                   │    │
│  │  FintechDetailPanel  (inline expandable)                    │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  TAB: Decisions (stays)                                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  DecisionPanel (ranked actions — full width)                │    │
│  │  ExplanationPanel (narrative, methodology, audit)           │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
│  TAB: Sectors (deep-dive, was the old default)                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │  PersonaFlowView (existing persona-based view, preserved)   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
├─────────────────────────────────────────────────────────────────────┤
│  STATUS BAR — pipeline stages, confidence, audit hash               │
└─────────────────────────────────────────────────────────────────────┘
```

**Key shift:** The first tab is now "Macro Overview" and it renders the same components as the Command Center's top 4 rows — not a persona-based view. The sector drill-downs (Banking/Insurance/Fintech) collapse into a single "Exposure" tab with inline expansion. "Decisions" stays as its own tab. The old persona-based view moves to a "Sectors" tab for backwards compatibility.

---

## 4. EXACT COMPONENTS TO RENAME / REPOSITION

### 4.1 Renames (labels and section headers — no logic changes)

| File | Current Label | New Label | Scope |
|------|--------------|-----------|-------|
| `page.tsx` tab bar | `Overview` / `النظرة العامة` | `Macro Overview` / `النظرة الكلية` | `detailLabels` object |
| `page.tsx` tab bar | `Banking` | `Exposure` / `التعرض` | `detailLabels` — merge Banking/Insurance/Fintech into one tab |
| `page.tsx` tab bar | Remove standalone `Insurance`, `Fintech` tabs | Fold into Exposure tab with inline sub-sections | Tab array + routing logic |
| `page.tsx` tab bar | `Decisions` / `القرارات` | Keep as-is | — |
| `page.tsx` tab bar | _(new)_ | `Sectors` / `القطاعات` | New tab rendering `PersonaFlowView` |
| `MacroOverviewHeader` Row 3 | `Active Scenario` / `السيناريو النشط` | `Stress Context` / `سياق الإجهاد` | Label string |
| `PropagationView` | `Causal cascade` (internal) | `Transmission Mechanics` | Panel header label |
| `GraphPanel` | No section header | Add `System Graph` / `الرسم البياني` header label | Component internal |
| Scenario selector heading | `Select a Scenario` | `Select a Macro Stress Event` | `page.tsx` scenario section |
| Scenario selector subheading | `Choose an event to analyze financial impact across GCC sectors` | `Choose a stress event to analyze macro transmission across the GCC` | `page.tsx` |

### 4.2 Repositioning (layout changes — no new components)

| Change | Current | Proposed | Files Affected |
|--------|---------|----------|----------------|
| **Results default tab** | `dashboard` → renders `PersonaFlowView` | `macro` → renders `MacroOverviewHeader` + `TransmissionChannels` + `ExposureLayer` + `SectorRollupBar` | `page.tsx` (results view section) |
| **Import Command Center components into page.tsx** | Not imported | Import `MacroOverviewHeader`, `TransmissionChannels`, `ExposureLayer`, `SectorRollupBar`, `StatusBar` from `@/features/command-center/components` | `page.tsx` (imports) |
| **Connect `useCommandCenter` hook to results view** | Results view uses raw `RunResult` | Wire `useCommandCenter` with the run ID from `runData` to derive graph nodes, edges, causal chain, impacts, etc. | `page.tsx` (results section), possibly new local adapter |
| **Merge sector tabs into Exposure** | 3 separate tabs: banking, insurance, fintech | Single "Exposure" tab with `ImpactPanel` at top + 3 collapsible `DetailPanel` sections below | `page.tsx` (tab routing) |
| **Move PersonaFlowView to "Sectors" tab** | Default view on results | Last tab, available but not default | `page.tsx` (tab routing) |
| **Remove dead EventHeader export** | Exported in `index.ts`, never imported | Remove export line | `features/command-center/components/index.ts` |

### 4.3 Data Bridge (critical dependency)

The Command Center components (`MacroOverviewHeader`, `TransmissionChannels`, `ExposureLayer`, `SectorRollupBar`) consume data from `useCommandCenter(runId)`. The results view in `page.tsx` currently uses raw `RunResult` state. To reuse the Command Center components in the results view, we need to either:

**Option A (recommended):** After the scenario run completes and we have a `runId`, call `useCommandCenter(runId)` inside the results view. This reuses the existing data pipeline with zero duplication.

**Option B:** Create a thin adapter that maps `RunResult` fields to the props expected by each Command Center component. This avoids the second fetch but requires manual mapping.

**Decision:** Option A. The `useCommandCenter` hook already handles the full pipeline including mock fallback. The `runId` is available from the scenario execution flow. The only cost is one additional GET request, which is already cached.

---

## 5. WHAT STAYS UNCHANGED

| Component / Surface | Reason |
|---------------------|--------|
| **Landing page** (`page.tsx` landing view) | Already macro-framed. No changes needed. |
| **Scenario Selector** (`page.tsx` scenarios view) | Correctly event-first. Only label rename. |
| **Command Center** (`/command-center/page.tsx`) | Already repositioned. Standalone URL for direct-link use cases. |
| **Graph Explorer** (`/graph-explorer`) | Deep-dive tool. Correctly secondary. |
| **Impact Map** (`/map`) | Deep-dive tool. Correctly secondary. |
| **Decisions Page** (`/decisions`) | Standalone decisions view. Correctly secondary. |
| **All backend APIs** | Zero backend changes. |
| **All Pydantic schemas** | Zero schema changes. |
| **`useCommandCenter` hook** | Reused as-is, not modified. |
| **All Command Center sub-components** | Reused as-is in new position. No internal logic changes. |
| **`PersonaFlowView` + all persona views** | Preserved, moved to "Sectors" tab. |
| **`BankingDetailPanel`, `InsuranceDetailPanel`, `FintechDetailPanel`** | Preserved, rehoused under "Exposure" tab. |
| **`DecisionDetailPanel`** | Preserved under "Decisions" tab. |
| **Top Nav structure** | Preserved. Cross-links stay. |
| **Theme tokens, design system** | No visual redesign. |
| **Store layer** (`app-store`, `flow-store`, `authority-store`) | No changes. |
| **All backend tests (113 contract + 27 API)** | Unaffected — zero backend changes. |

---

## 6. MINIMAL FILE-LEVEL PLAN

Ordered execution sequence. Each step is independently testable.

### Step 1: Label Renames (zero-risk, zero-logic)

| File | Change |
|------|--------|
| `frontend/src/app/page.tsx` | Rename tab labels in `detailLabels` object |
| `frontend/src/app/page.tsx` | Rename scenario selector heading/subheading |
| `frontend/src/features/command-center/components/MacroOverviewHeader.tsx` | "Active Scenario" → "Stress Context" |
| `frontend/src/features/command-center/components/PropagationView.tsx` | Add "Transmission Mechanics" section header |
| `frontend/src/features/command-center/components/GraphPanel.tsx` | Add "System Graph" section header |

### Step 2: Tab Restructure (routing changes)

| File | Change |
|------|--------|
| `frontend/src/app/page.tsx` | Redefine `DetailView` type: `"macro" \| "transmission" \| "exposure" \| "decisions" \| "sectors"` |
| `frontend/src/app/page.tsx` | Update tab bar to render new tab set |
| `frontend/src/app/page.tsx` | Default `detailView` to `"macro"` instead of `"dashboard"` |
| `frontend/src/app/page.tsx` | Route "sectors" tab to existing `PersonaFlowView` |

### Step 3: Macro Overview Tab Content

| File | Change |
|------|--------|
| `frontend/src/app/page.tsx` | Import Command Center components: `MacroOverviewHeader`, `TransmissionChannels`, `ExposureLayer`, `SectorRollupBar`, `StatusBar` |
| `frontend/src/app/page.tsx` | Import `useCommandCenter` hook |
| `frontend/src/app/page.tsx` | In results view, call `useCommandCenter(runId)` and pass derived data to Command Center components |
| `frontend/src/app/page.tsx` | Render macro tab: Header → Channels → Exposure → Rollup |

### Step 4: Exposure Tab Consolidation

| File | Change |
|------|--------|
| `frontend/src/app/page.tsx` | Create "exposure" tab view that stacks: `ImpactPanel` + collapsible `BankingDetailPanel` + `InsuranceDetailPanel` + `FintechDetailPanel` |
| `frontend/src/app/page.tsx` | Remove standalone "banking", "insurance", "fintech" tabs |

### Step 5: Transmission Tab

| File | Change |
|------|--------|
| `frontend/src/app/page.tsx` | Create "transmission" tab view that renders `PropagationView` (full-width) + `GraphPanel` (full-width) |

### Step 6: Decisions Tab Enrichment

| File | Change |
|------|--------|
| `frontend/src/app/page.tsx` | In "decisions" tab, add `ExplanationPanel` below `DecisionDetailPanel` |

### Step 7: Cleanup

| File | Change |
|------|--------|
| `frontend/src/features/command-center/components/index.ts` | Remove `EventHeader` export |
| `frontend/src/features/command-center/components/EventHeader.tsx` | Delete file (dead code) |
| `frontend/src/app/page.tsx` | Remove old `DetailView` type values (`"dashboard"`, `"banking"`, `"insurance"`, `"fintech"`) |

---

## 7. RISKS

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| **Double-fetch on results view** — `useCommandCenter(runId)` triggers a second GET after the scenario run already fetched the result | Medium | Low (same data, ~100ms) | The hook checks `useRunState` first. If the result is already in the store (from the scenario run), it can short-circuit. Verify this path exists or add a store check. |
| **Mock data divergence** — Command Center components have their own mock data path (`useCommandCenter(null)`); results view has its own. Using both in the same page could cause confusion. | Low | Medium | When rendering Command Center components in the results view, always pass the real `runId`. Never invoke mock mode from the results view. |
| **Layout overflow on mobile** — Stacking `MacroOverviewHeader` + `TransmissionChannels` + `ExposureLayer` + `SectorRollupBar` vertically on mobile could exceed viewport. | Medium | Low | Add `overflow-y-auto` to the macro tab container. These components already handle responsive collapse via Tailwind breakpoints. |
| **`useSearchParams` conflict** — `useCommandCenter` reads `?run=` from search params. In the results view, the run ID comes from local state, not the URL. | Medium | Medium | Pass `runId` directly to `useCommandCenter(runId)` — the hook already accepts an explicit parameter. Do not rely on search params in the results view. |
| **PersonaFlowView data contract mismatch** — Moving it to the "Sectors" tab doesn't change its data contract, but it was designed as the default view. If it assumes it's always mounted, there could be lazy-loading issues. | Low | Low | PersonaFlowView is already wrapped in `ErrorBoundary`. It receives `result` as a prop and renders defensively. No issue expected. |
| **Tab state persistence** — If the user navigates away and returns, the tab resets to "macro". This is acceptable — macro-first is the goal. | Low | None | Intentional. |

---

## 8. DEFINITION OF DONE

All conditions must be true before the repositioning is considered complete:

- [ ] **First impression test:** When a user completes a scenario run, the first screen they see is the Macro Overview tab showing System Risk Index, Transmission Channels, and Exposure Distribution — not a persona view or sector tab.
- [ ] **Tab order test:** Tab bar reads: `Macro Overview | Transmission | Exposure | Decisions | Sectors` in English and `النظرة الكلية | الانتقال | التعرض | القرارات | القطاعات` in Arabic.
- [ ] **No new API calls:** The repositioning introduces zero new backend endpoints. The only additional fetch is the existing `GET /api/v1/runs/{id}` via `useCommandCenter`.
- [ ] **Command Center parity:** The Macro Overview tab in the results view renders the same components as `/command-center` rows 1–5 with identical data.
- [ ] **Sector drill-down preserved:** Banking, Insurance, and Fintech detail panels are all reachable from the "Exposure" tab with collapsible sections.
- [ ] **PersonaFlowView preserved:** The existing persona-based view is fully accessible from the "Sectors" tab with no functional regression.
- [ ] **Decisions tab complete:** `DecisionDetailPanel` + `ExplanationPanel` render together under the Decisions tab.
- [ ] **Label audit:** No instance of "Active Scenario" remains in the Command Center header. "Select a Scenario" is replaced with "Select a Macro Stress Event" in the selector.
- [ ] **Dead code removed:** `EventHeader.tsx` is deleted and its barrel export is removed.
- [ ] **TypeScript clean:** `npx tsc --noEmit` passes with zero errors.
- [ ] **Bilingual parity:** All renamed labels have Arabic equivalents.
- [ ] **No backend test regression:** `pytest tests/ -v` passes all 140 tests unchanged.
- [ ] **Visual regression:** No component is visually broken at 1440px and 768px widths.

---

## DECISION GATE

**What must be true before proceeding to implementation:**

1. Product owner confirms the tab order: Macro Overview → Transmission → Exposure → Decisions → Sectors
2. Product owner confirms the "Sectors" tab is acceptable as the home for `PersonaFlowView` (vs. removing it entirely)
3. Decision on whether `useCommandCenter(runId)` should short-circuit from the store (Option A-prime) or always re-fetch (Option A)
4. Confirmation that the `/command-center` standalone URL remains live and unchanged for direct-link / embed use cases

**Once these four gates are cleared, implementation follows Steps 1–7 in order. Each step is independently deployable and testable.**
