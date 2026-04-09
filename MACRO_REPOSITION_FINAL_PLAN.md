# MACRO UI REPOSITIONING — Final Execution Plan

**Date:** 2026-04-08
**Scope:** Reposition the primary results experience to read as a GCC Macro Decision System.
**Constraint:** No backend changes. No new features. No architecture redesign. Preserve all live/mock wiring.

---

## 0. CRITICAL FINDING: TWO SURFACES, ONE PRIMARY

Users hit the product at `/` (`page.tsx`). After running a scenario they stay on `/` in the results view. This is the primary results surface — not `/command-center`.

| Surface | URL | How Users Reach It | Audience |
|---------|-----|-------------------|----------|
| **A — Primary (page.tsx)** | `/` | Landing → Scenario → Results | 95% of users |
| **B — Command Center** | `/command-center?run=<id>` | Direct URL / embed | Power users, linked dashboards |

**Surface A results view** currently shows:

```
TopNav
Tab Bar: Overview | Banking | Insurance | Fintech | Decisions
─────────────────────────────────────────────────────────
"Overview" tab (default) renders:
  FlowExecutiveView
    ├── FlowTimeline (compact progress bar)
    ├── UnifiedControlTower
    │     ├── "Control Tower" header + SystemHealthBadge
    │     ├── StageSummaryCards (4 cards: completed/active/failed/total)
    │     ├── IntelligenceSummary (6 cards: signals/impact/decisions/outcomes/ROI/operator)
    │     ├── AuthorityQueuePanel
    │     ├── FlowNarrativePanel
    │     └── ExecutiveControlTower (Value/Drivers/Performance/Risk panels)
    └── ExecutiveDashboard
          ├── TrustBox (model provenance)
          ├── KPI Strip (6 headline metrics)
          ├── PipelineViewer (stage log)
          ├── Sector Analysis (FinancialImpactTable + 3 SectorStressPanels)
          ├── Decision Actions (InstitutionalActionCard ×4)
          └── Forward-Looking Timelines (Business + Regulatory)
```

**Problem:** The first thing an executive reads on the "Overview" tab is:

1. "Control Tower" (process label, not macro context)
2. Stage summary cards (how many stages completed — pipeline detail)
3. Intelligence summary (6 equal-weight cards — no hierarchy)
4. Authority queue (operator decisions — not macro framing)

There is **no macro context**, **no transmission channels**, **no country/sector exposure**, and **no system risk index** anywhere in the primary results surface. Those components exist only on Surface B (`/command-center`), which most users never visit.

**Surface B** (`/command-center`) is already largely macro-framed with the right hierarchy. It needs minor label renames only.

---

## 1. FILE TREE (all touched files)

```
frontend/src/
├── app/
│   ├── page.tsx                                    # ✏️ MAJOR — tab restructure + macro tab content
│   └── command-center/
│       ├── layout.tsx                              # ✏️ metadata title rename
│       └── page.tsx                                # ✏️ panel reorder + section dividers
│
├── features/
│   ├── command-center/
│   │   └── components/
│   │       ├── MacroOverviewHeader.tsx              # ✏️ "Active Scenario" → "Stress Context"
│   │       ├── DecisionCard.tsx                     # ✏️ "Decision Actions" → "Decision Priorities"
│   │       ├── GraphPanel.tsx                       # ✏️ "Knowledge Graph" → "System Graph"
│   │       ├── PropagationView.tsx                  # ✏️ "Propagation Trace" → "Transmission Mechanics"
│   │       ├── ImpactPanel.tsx                      # ✏️ "Impact Assessment" → "Sector Exposure Detail"
│   │       ├── ExplanationPanel.tsx                 # ✏️ "Explanation" → "Operational Reasoning"
│   │       ├── EventHeader.tsx                      # 🗑️ DELETE (dead code)
│   │       ├── index.ts                            # ✏️ remove EventHeader export
│   │       ├── TransmissionChannels.tsx             # — UNCHANGED
│   │       ├── ExposureLayer.tsx                    # — UNCHANGED
│   │       ├── SectorRollupBar.tsx                  # — UNCHANGED
│   │       └── StatusBar.tsx                        # — UNCHANGED
│   │
│   ├── flow/
│   │   └── PersonaFlowView.tsx                     # ✏️ reorder FlowExecutiveView internals
│   │
│   └── dashboard/
│       └── ExecutiveDashboard.tsx                   # ✏️ section header renames
│
└── (no other files touched)
```

**Summary: 13 files edited, 1 file deleted, 0 files created.**

---

## 2. FILES TO MODIFY — Grouped by Surface

### Surface A — Primary Results Experience (the big win)

#### 2A-1. `frontend/src/app/page.tsx`

**Tab restructure.** The current tab bar is sector-first:

```
Overview | Banking | Insurance | Fintech | Decisions
```

Change to macro-first:

```
Macro Overview | Exposure | Decisions | Sectors
```

Exact changes:

| Item | Current | New |
|------|---------|-----|
| `DetailView` type (line 51) | `"dashboard" \| "banking" \| "insurance" \| "fintech" \| "decisions"` | `"macro" \| "exposure" \| "decisions" \| "sectors"` |
| `detailLabels.en` | `{ dashboard: "Overview", banking: "Banking", insurance: "Insurance", fintech: "Fintech", decisions: "Decisions" }` | `{ macro: "Macro Overview", exposure: "Exposure", decisions: "Decisions", sectors: "Sectors" }` |
| `detailLabels.ar` | `{ dashboard: "النظرة العامة", banking: "البنوك", insurance: "التأمين", fintech: "الفنتك", decisions: "القرارات" }` | `{ macro: "النظرة الكلية", exposure: "التعرض", decisions: "القرارات", sectors: "القطاعات" }` |
| Default `detailView` (line 279) | `"dashboard"` | `"macro"` |
| Scenario selector heading (line 842) | `"Select a Scenario"` | `"Select a Macro Stress Event"` |
| Scenario selector subheading (line 845) | `"Choose an event to analyze financial impact across GCC sectors"` | `"Choose a stress event to analyze macro transmission across the GCC"` |
| Scenario selector heading AR | `"اختر سيناريو لتحليله"` | `"اختر حدث إجهاد كلي"` |
| Scenario selector subheading AR | `"اختر حدثاً لتحليل الأثر المالي عبر القطاعات الخليجية"` | `"اختر حدث إجهاد لتحليل الانتقال الكلي عبر الخليج"` |

**New imports** (add to existing import block):

```typescript
import { MacroOverviewHeader } from "@/features/command-center/components/MacroOverviewHeader";
import { TransmissionChannels } from "@/features/command-center/components/TransmissionChannels";
import { ExposureLayer } from "@/features/command-center/components/ExposureLayer";
import { SectorRollupBar } from "@/features/command-center/components/SectorRollupBar";
import { useCommandCenter } from "@/features/command-center/lib/use-command-center";
```

**Tab routing — new "macro" tab content** (replaces the `detailView === "dashboard"` block):

When `detailView === "macro"` and `result` is present, render:

```
MacroOverviewHeader   ← macro context, system risk index, KPIs
TransmissionChannels  ← 4 channel cards
ExposureLayer         ← country + sector breakdown
SectorRollupBar       ← horizontal sector strip
─── divider ───
DecisionPanel (from command-center) or InstitutionalActionCards (existing)
─── divider ───
TrustBox              ← model provenance (already in ExecutiveDashboard)
```

**Data bridge for the macro tab:** Call `useCommandCenter(runId)` where `runId` comes from `result.run_id`. The hook fetches from the same API, hits TanStack Query cache (already fetched during scenario run), and provides: `graphNodes`, `graphEdges`, `sectorRollups`, `impacts`, `decisionActions`, `confidence`, `trust`, etc.

Where `runId` is null (result came from local state but has no run_id), pass `null` → hook loads mock data → components render with deterministic demo values. This matches the existing fallback pattern.

**New "exposure" tab content** (merges old banking + insurance + fintech tabs):

```
ImpactPanel (from command-center — SafeImpact[] grid)   ← at top
BankingDetailPanel   ← inline, with section divider
InsuranceDetailPanel ← inline, with section divider
FintechDetailPanel   ← inline, with section divider
```

**New "sectors" tab content** (preserves old PersonaFlowView):

```
PersonaFlowView result={result} lang={lang}  ← unchanged, moved to last tab
```

**"decisions" tab** — unchanged, still renders `DecisionDetailPanel`.

#### 2A-2. `frontend/src/features/flow/PersonaFlowView.tsx`

**Reorder `FlowExecutiveView` internals** — for users who reach it via the "Sectors" tab, the persona view should also read macro-first. Move `ExecutiveDashboard` KPIs above `UnifiedControlTower`:

| Current Order | New Order |
|---------------|-----------|
| FlowTimeline (compact) | FlowTimeline (compact) |
| UnifiedControlTower (Control Tower header → stages → intelligence → authority → narrative → panels) | ExecutiveDashboard (TrustBox → KPIs → Sector Analysis → Decision Actions → Timelines) |
| ExecutiveDashboard (TrustBox → KPIs → Sector Analysis → Decision Actions → Timelines) | UnifiedControlTower (Control Tower header → stages → intelligence → authority → narrative → panels) |

This means KPIs and sector data appear before the control tower pipeline detail.

#### 2A-3. `frontend/src/features/dashboard/ExecutiveDashboard.tsx`

**Section header renames:**

| Line | Current | New |
|------|---------|-----|
| 304 | `"Executive Analysis Report"` | `"GCC Macro Analysis"` |
| 304 AR | `"تقرير التحليل التنفيذي"` | `"التحليل الكلي للخليج"` |
| 363 | `"Headline Metrics"` | `"Macro Indicators"` |
| 363 AR | `"المؤشرات الرئيسية"` | `"المؤشرات الكلية"` |
| 476 | `"Sector Analysis"` | `"Sector Exposure"` |
| 476 AR | `"تحليل القطاعات"` | `"تعرض القطاعات"` |
| 537 | `"Recommended Response Actions"` | `"Decision Priorities"` |
| 537 AR | `"إجراءات الاستجابة الموصى بها"` | `"أولويات القرار"` |

### Surface B — Command Center (`/command-center`)

#### 2B-1. `frontend/src/app/command-center/page.tsx`

**Panel reorder** — promote DecisionPanel, group exposure together:

| Current Row | Component | New Row | Change |
|-------------|-----------|---------|--------|
| 1 | MacroOverviewHeader | 1 | — |
| 2 | TransmissionChannels | 2 | — |
| 3 | ExposureLayer | 3 | — |
| 4 | Graph \| Propagation \| Decision (4+4+4) | Split: see below | **BREAK APART** |
| 5 | SectorRollupBar | 4 | Move up (group with exposure) |
| — | _(new section divider)_ | — | "DECISION PRIORITIES" |
| — | DecisionPanel | 5 | **PROMOTE** to full-width 12-col, `max-h-[320px]` scroll |
| — | _(new section divider)_ | — | "OPERATIONAL DETAIL" |
| — | Graph \| Propagation | 6 | **DEMOTE** to 6+6 grid |
| 6 → 7 | ImpactPanel | 7 | — |
| 7 → 8 | ExplanationPanel | 8 | — |
| 8 → 9 | StatusBar | 9 | — |

**Update ASCII diagram comment** at top of file to match new layout.

#### 2B-2. `frontend/src/app/command-center/layout.tsx`

| Current | New |
|---------|-----|
| `"Decision Command Center \| Impact Observatory"` | `"GCC Macro Intelligence \| Impact Observatory"` |

#### 2B-3–8. Command Center Component Label Renames (6 files)

| File | Current Header | New Header |
|------|---------------|------------|
| `MacroOverviewHeader.tsx` (line 288) | `Active Scenario` / `السيناريو النشط` | `Stress Context` / `سياق الإجهاد` |
| `DecisionCard.tsx` (line 294) | `Decision Actions` | `Decision Priorities` |
| `GraphPanel.tsx` (line 263) | `Knowledge Graph` | `System Graph` |
| `PropagationView.tsx` (line 181) | `Propagation Trace` | `Transmission Mechanics` |
| `ImpactPanel.tsx` (line 177) | `Impact Assessment` | `Sector Exposure Detail` |
| `ExplanationPanel.tsx` (line 103) | `Explanation` | `Operational Reasoning` |

#### 2B-9. `index.ts` + `EventHeader.tsx`

- Remove `export { EventHeader } from "./EventHeader";` from `index.ts`
- Delete `EventHeader.tsx` (dead code — exported but never imported)

---

## 3. EXACT STRUCTURAL MOVES

### Move 1: New "Macro Overview" Tab on Primary Surface
**What:** When the user runs a scenario and lands on the results view, the default tab ("Macro Overview") now renders the command-center macro components: `MacroOverviewHeader` → `TransmissionChannels` → `ExposureLayer` → `SectorRollupBar` → Decision Actions → TrustBox.
**Why:** This is the single highest-impact change. It puts GCC macro context — system risk index, transmission channels, country/sector exposure — as the first thing executives see.
**Data bridge:** `useCommandCenter(result.run_id)` — reuses existing hook, hits TanStack Query cache, zero new API calls.

### Move 2: Merge Sector Tabs into "Exposure"
**What:** Banking + Insurance + Fintech tabs collapse into a single "Exposure" tab showing `ImpactPanel` at top + 3 sector detail panels inline.
**Why:** Sector-first tabs fragment the macro narrative. A single exposure tab frames all sectors as dimensions of the same GCC stress.

### Move 3: Old PersonaFlowView Moves to "Sectors" Tab
**What:** The existing persona-driven view (FlowTimeline → UnifiedControlTower → ExecutiveDashboard) moves to the last tab.
**Why:** Preserves all existing functionality for users who want the flow-based view, but it's no longer the default.

### Move 4: Reorder ExecutiveDashboard Above ControlTower in PersonaFlowView
**What:** Within `FlowExecutiveView`, swap: show ExecutiveDashboard (KPIs, sector data, decisions) before UnifiedControlTower (pipeline stages, intelligence summary, authority queue).
**Why:** Even in the persona view, macro data (KPIs, sector stress) should precede pipeline operational detail (stage cards, flow narrative).

### Move 5: Command Center Panel Reorder
**What:** DecisionPanel promoted to full-width above Graph/Propagation. SectorRollupBar moved up to group with ExposureLayer. Graph+Propagation become 6+6 operational detail.
**Why:** Decisions are executive output. Graph/Propagation are diagnostic tools. They should not share equal visual weight.

---

## 4. EXACT LABEL CHANGES (complete registry)

| File | Line | Before (EN) | After (EN) | Before (AR) | After (AR) |
|------|------|-------------|------------|-------------|------------|
| `MacroOverviewHeader.tsx` | 288 | Active Scenario | Stress Context | السيناريو النشط | سياق الإجهاد |
| `DecisionCard.tsx` | 294 | Decision Actions | Decision Priorities | — | — |
| `GraphPanel.tsx` | 263 | Knowledge Graph | System Graph | — | — |
| `PropagationView.tsx` | 181 | Propagation Trace | Transmission Mechanics | — | — |
| `ImpactPanel.tsx` | 177 | Impact Assessment | Sector Exposure Detail | — | — |
| `ExplanationPanel.tsx` | 103 | Explanation | Operational Reasoning | — | — |
| `layout.tsx` | 3 | Decision Command Center | GCC Macro Intelligence | — | — |
| `page.tsx` tab bar | 500–513 | Overview / Banking / Insurance / Fintech / Decisions | Macro Overview / Exposure / Decisions / Sectors | النظرة العامة / البنوك / التأمين / الفنتك / القرارات | النظرة الكلية / التعرض / القرارات / القطاعات |
| `page.tsx` scenario heading | 842 | Select a Scenario | Select a Macro Stress Event | اختر سيناريو لتحليله | اختر حدث إجهاد كلي |
| `page.tsx` scenario subheading | 845 | Choose an event to analyze financial impact across GCC sectors | Choose a stress event to analyze macro transmission across the GCC | اختر حدثاً لتحليل الأثر المالي عبر القطاعات الخليجية | اختر حدث إجهاد لتحليل الانتقال الكلي عبر الخليج |
| `ExecutiveDashboard.tsx` | 304 | Executive Analysis Report | GCC Macro Analysis | تقرير التحليل التنفيذي | التحليل الكلي للخليج |
| `ExecutiveDashboard.tsx` | 363 | Headline Metrics | Macro Indicators | المؤشرات الرئيسية | المؤشرات الكلية |
| `ExecutiveDashboard.tsx` | 476 | Sector Analysis | Sector Exposure | تحليل القطاعات | تعرض القطاعات |
| `ExecutiveDashboard.tsx` | 537 | Recommended Response Actions | Decision Priorities | إجراءات الاستجابة الموصى بها | أولويات القرار |

---

## 5. WHAT STAYS UNCHANGED

| Item | Reason |
|------|--------|
| **All backend APIs** | Zero backend changes |
| **All Pydantic schemas** | Zero schema changes |
| **All backend tests (140)** | Zero backend changes |
| **Landing page** | Already macro-framed |
| **`useCommandCenter` hook** | Reused as-is, not modified |
| **All command-center sub-components (internals)** | Only header labels change; all logic, props, data flow unchanged |
| **`command-store.ts`, `mock-data.ts`, `live-mappers.ts`, `format.ts`** | Untouched |
| **All stores** (`app-store`, `flow-store`, `authority-store`) | Untouched |
| **`PersonaFlowView` routing** (executive/analyst/regulator switch) | Preserved — moved to "Sectors" tab |
| **`FlowAnalystView`, `FlowRegulatorView`** | Untouched |
| **`BankingDetailPanel`, `InsuranceDetailPanel`, `FintechDetailPanel`** | Preserved — rehoused under "Exposure" tab |
| **`DecisionDetailPanel`** | Preserved under "Decisions" tab |
| **`UnifiedControlTower` internals** | Untouched |
| **`ExecutiveDashboard` internals** | Only section header strings change |
| **`TrustBox`, `PipelineViewer`** | Untouched |
| **Graph Explorer** (`/graph-explorer`) | Untouched |
| **Impact Map** (`/map`) | Untouched |
| **Decisions Page** (`/decisions`) | Untouched |
| **Theme tokens, design system** | No visual redesign |
| **TopNav structure and cross-links** | Preserved |
| **Live/mock wiring, error handling, fallback banners** | Preserved |
| **`executeAction` flow** | Preserved |
| **`Suspense`, `ErrorBoundary` wrapping** | Preserved |
| **Loading skeleton, error state, empty state** | Preserved |
| **PDF export** | Preserved |

---

## 6. IMPLEMENTATION ORDER

| Step | File(s) | What | Risk | Reversible |
|------|---------|------|------|------------|
| **1** | 6 command-center components | Label renames (single-string edits) | Zero | Yes |
| **2** | `command-center/layout.tsx` | Metadata title rename | Zero | Yes |
| **3** | `command-center/components/index.ts` | Remove `EventHeader` export | Zero | Yes |
| **4** | `EventHeader.tsx` | Delete dead file | Zero | Git recoverable |
| **5** | `command-center/page.tsx` | Panel reorder: promote DecisionPanel, group exposure, demote graph/propagation, add section dividers, update comment | Low | Yes |
| **6** | `ExecutiveDashboard.tsx` | Section header renames (4 string edits) | Zero | Yes |
| **7** | `PersonaFlowView.tsx` | Swap ExecutiveDashboard above UnifiedControlTower in FlowExecutiveView | Low | Yes |
| **8** | `page.tsx` — imports + type | Add command-center imports, change `DetailView` type | Low | Yes |
| **9** | `page.tsx` — tab bar | Change `detailLabels` object, default to `"macro"` | Low | Yes |
| **10** | `page.tsx` — macro tab | Add "macro" tab block: call `useCommandCenter(result?.run_id)`, render MacroOverviewHeader → TransmissionChannels → ExposureLayer → SectorRollupBar → decision actions → TrustBox | **Medium** — data bridge | Isolatable |
| **11** | `page.tsx` — exposure tab | Merge banking/insurance/fintech into "exposure" tab with ImpactPanel + 3 inline detail panels | Low | Yes |
| **12** | `page.tsx` — sectors tab | Route "sectors" to existing `PersonaFlowView` | Zero | Yes |
| **13** | `page.tsx` — scenario selector labels | Rename heading/subheading strings | Zero | Yes |
| **14** | Verify | `npx tsc --noEmit` + visual check at `localhost:3000` (mock) + `localhost:3000/command-center` (mock) | Verification | — |

---

## 7. RISKS

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| **TanStack Query cache miss on macro tab** — `useCommandCenter(result.run_id)` fires a GET that was already cached during scenario run, but if the cache key differs (different query key namespace), it triggers a second fetch | Medium | Low | Verify the key is `["command-center", "run", runId]`. The scenario run uses a different fetch path (`fetch(/api/v1/runs/${runId})`), so the cache WILL miss. The second GET is cheap (~100ms, same data). Acceptable. |
| **`useCommandCenter` reads `useSearchParams`** — The hook itself does not, but if it's used inside a component that expects URL params, it could conflict | N/A | N/A | Verified: `useCommandCenter` accepts `runId` as a direct argument. It does not read URL params. No conflict. |
| **`useCommandCenter(null)` when result.run_id is missing** — If the result came from local state without a run_id, the hook loads mock data | Low | Low | Acceptable: mock data in the macro tab is better than an empty shell. The scenario flow always produces a `run_id`, so this path only triggers in edge cases. |
| **Mobile overflow on macro tab** — Stacking MacroOverviewHeader + TransmissionChannels + ExposureLayer + SectorRollupBar vertically on mobile could be tall | Medium | Low | These components already handle responsive breakpoints via Tailwind. Add `overflow-y-auto` to the macro tab container. |
| **Persona view regression** — Moving PersonaFlowView to the "Sectors" tab could confuse users who expect it as the default | Low | Medium | The old default was process-first (Control Tower → stages → intelligence), which is the behavior we're explicitly replacing. Users who want the persona view can find it in "Sectors". |
| **Type narrowing on DetailView** — Changing the union type from 5 to 4 members will cause TypeScript errors in any code that references the old member names ("dashboard", "banking", "insurance", "fintech") | Medium | Low | `page.tsx` is the only file that defines and consumes `DetailView`. All references are co-located. Update all switch cases and routing blocks in the same step. |

---

## 8. STATUS: READY FOR CODE

All pre-conditions met:

- Primary results surface (`page.tsx`) fully audited — component tree, data flow, tab routing, imports all mapped
- Command center surface (`command-center/page.tsx`) fully audited — layout, all component headers, data contracts verified
- Data bridge confirmed: `useCommandCenter(runId)` works with direct argument, no URL dependency, TanStack Query cache provides fast second fetch
- All label strings identified with exact line numbers and before/after values
- `PersonaFlowView` internal structure verified — swap is safe (both children receive same props)
- `ExecutiveDashboard` section headers identified — 4 string replacements
- Dead code (`EventHeader`) confirmed dead (exported but never imported anywhere)
- All unchanged items catalogued

**Implementation can proceed immediately, following Steps 1–14 in order.**
