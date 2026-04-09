# MACRO UI REPOSITIONING — Execution Plan

**Scope:** Command Center only (`/command-center`). No backend. No new features. No architecture changes.

---

## 1. FILE TREE (touched files only)

```
frontend/src/
├── app/
│   └── command-center/
│       ├── layout.tsx                          # ✏️ metadata title rename
│       └── page.tsx                            # ✏️ panel reorder + section dividers + comment update
│
└── features/
    └── command-center/
        ├── components/
        │   ├── MacroOverviewHeader.tsx          # ✏️ "Active Scenario" → "Stress Context"
        │   ├── TransmissionChannels.tsx         # — UNCHANGED
        │   ├── ExposureLayer.tsx                # — UNCHANGED
        │   ├── DecisionCard.tsx                 # ✏️ header "Decision Actions" → "Decision Priorities"
        │   ├── SectorRollupBar.tsx              # — UNCHANGED
        │   ├── GraphPanel.tsx                   # ✏️ header "Knowledge Graph" → "System Graph"
        │   ├── PropagationView.tsx              # ✏️ header "Propagation Trace" → "Transmission Mechanics"
        │   ├── ImpactPanel.tsx                  # ✏️ header "Impact Assessment" → "Sector Exposure Detail"
        │   ├── ExplanationPanel.tsx             # ✏️ header "Explanation" → "Operational Reasoning"
        │   ├── StatusBar.tsx                    # — UNCHANGED
        │   ├── EventHeader.tsx                  # 🗑️ DELETE (dead code — exported but never imported)
        │   └── index.ts                         # ✏️ remove EventHeader export
        │
        └── lib/
            ├── use-command-center.ts            # — UNCHANGED
            ├── command-store.ts                 # — UNCHANGED
            ├── format.ts                        # — UNCHANGED
            ├── live-mappers.ts                  # — UNCHANGED
            └── mock-data.ts                     # — UNCHANGED
```

**Summary: 9 files edited, 1 file deleted, 0 files created.**
All data hooks, stores, API contracts, and safety wiring untouched.

---

## 2. EXACT UI REPOSITIONING

### Current layout (what the user sees top-to-bottom):

```
ROW 1  MacroOverviewHeader     — GCC Macro Overview, KPIs, "Active Scenario"    [12 col]
ROW 2  TransmissionChannels    — 4 channel cards                                [12 col]
ROW 3  ExposureLayer           — Country + Sector exposure                      [12 col]
ROW 4  GraphPanel | PropagationView | DecisionPanel                             [4+4+4 col]
ROW 5  SectorRollupBar         — Horizontal sector stress strip                 [12 col]
ROW 6  ImpactPanel             — Per-entity impact grid                         [12 col]
ROW 7  ExplanationPanel        — Narrative, methodology, audit                  [12 col]
ROW 8  StatusBar               — Pipeline meta                                 [12 col]
```

### Target layout (after repositioning):

```
 ┌─────────────────────────────────────────────────────────────────┐
 │  SECTION 1: GCC MACRO CONTEXT                                   │
 │                                                                  │
 │  ROW 1  MacroOverviewHeader                            [12 col] │
 │         — "Stress Context" (was "Active Scenario")               │
 │                                                                  │
 ├─────────────────────────────────────────────────────────────────┤
 │  SECTION 2: TRANSMISSION                                        │
 │                                                                  │
 │  ROW 2  TransmissionChannels                           [12 col] │
 │         — UNCHANGED                                              │
 │                                                                  │
 ├─────────────────────────────────────────────────────────────────┤
 │  SECTION 3: EXPOSURE                                            │
 │                                                                  │
 │  ROW 3  ExposureLayer (country + sector)               [12 col] │
 │  ROW 4  SectorRollupBar                                [12 col] │
 │         — MOVED UP from Row 5 (groups all exposure together)     │
 │                                                                  │
 ├─────────────────────────────────────────────────────────────────┤
 │  SECTION 4: DECISION PRIORITIES                                 │
 │                                                                  │
 │  ROW 5  DecisionPanel                                  [12 col] │
 │         — PROMOTED to full-width (was 4-col in 3-panel grid)     │
 │         — header: "Decision Priorities" (was "Decision Actions")  │
 │         — max-h-[320px] with scroll                              │
 │                                                                  │
 ├─────────────────────────────────────────────────────────────────┤
 │  SECTION 5: OPERATIONAL DETAIL                                  │
 │                                                                  │
 │  ROW 6  GraphPanel | PropagationView                   [6+6 col]│
 │         — "System Graph" (was "Knowledge Graph")                 │
 │         — "Transmission Mechanics" (was "Propagation Trace")     │
 │  ROW 7  ImpactPanel                                    [12 col] │
 │         — "Sector Exposure Detail" (was "Impact Assessment")     │
 │  ROW 8  ExplanationPanel                               [12 col] │
 │         — "Operational Reasoning" (was "Explanation")             │
 │                                                                  │
 ├─────────────────────────────────────────────────────────────────┤
 │  ROW 9  StatusBar                                      [12 col] │
 │         — UNCHANGED                                              │
 └─────────────────────────────────────────────────────────────────┘
```

### What changed in the layout:

| Change | Before | After | Why |
|--------|--------|-------|-----|
| **DecisionPanel position** | Row 4, right 4-col (buried in 3-panel grid alongside Graph + Propagation) | Row 5, full-width 12-col with max-height | Decisions are a primary executive output — they must appear before operational detail, not alongside it |
| **SectorRollupBar position** | Row 5, after the 3-panel grid | Row 4, directly after ExposureLayer | Groups all exposure data together (country + sector + rollup) before showing decisions |
| **GraphPanel + PropagationView** | Row 4, left 4-col + center 4-col (equal weight with Decisions) | Row 6, two-panel 6+6 split | These are operational/mechanical views — they support decisions, not compete with them |
| **3-panel equal grid** | 4+4+4 (Graph : Propagation : Decisions) | Eliminated — Decisions promoted, Graph+Propagation demoted | Removes the visual equivalence between diagnosis tools and executive actions |

### What the executive reads in order:

1. **"What is the GCC macro picture?"** → MacroOverviewHeader (System Risk Index, regions, KPIs)
2. **"How is the shock transmitting?"** → TransmissionChannels (4 channel cards with directional flow)
3. **"Where is exposure concentrated?"** → ExposureLayer + SectorRollupBar (country + sector + rollup)
4. **"What should I do?"** → DecisionPanel (priority-ranked actions, full-width)
5. **"Show me the operational reasoning"** → Graph + Propagation + Impact + Explanation (collapsible detail)

---

## 3. LABEL RENAMES (exact string replacements)

### 3a. `MacroOverviewHeader.tsx` — Line 288

| Before | After |
|--------|-------|
| `{isAr ? "السيناريو النشط" : "Active Scenario"}` | `{isAr ? "سياق الإجهاد" : "Stress Context"}` |

### 3b. `DecisionCard.tsx` — Line 294–295

| Before | After |
|--------|-------|
| `Decision Actions` | `Decision Priorities` |

### 3c. `GraphPanel.tsx` — Line 262–263

| Before | After |
|--------|-------|
| `Knowledge Graph` | `System Graph` |

### 3d. `PropagationView.tsx` — Line 180–181

| Before | After |
|--------|-------|
| `Propagation Trace` | `Transmission Mechanics` |

### 3e. `ImpactPanel.tsx` — Line 177

| Before | After |
|--------|-------|
| `Impact Assessment` | `Sector Exposure Detail` |

### 3f. `ExplanationPanel.tsx` — Line 102–103

| Before | After |
|--------|-------|
| `Explanation` | `Operational Reasoning` |

### 3g. `layout.tsx` — Line 3

| Before | After |
|--------|-------|
| `title: "Decision Command Center \| Impact Observatory"` | `title: "GCC Macro Intelligence \| Impact Observatory"` |

### 3h. `index.ts` — Line 4

| Before | After |
|--------|-------|
| `export { EventHeader } from "./EventHeader";` | _(delete line)_ |

---

## 4. `page.tsx` — JSX Reorder (the core change)

The JSX inside `CommandCenterInner` return block changes from:

```
MacroOverviewHeader
TransmissionChannels
ExposureLayer
┌─────────────────────────┐
│ Grid 4+4+4              │
│ Graph | Prop | Decision │
└─────────────────────────┘
SectorRollupBar
ImpactPanel
ExplanationPanel
StatusBar
```

To:

```
MacroOverviewHeader
TransmissionChannels
ExposureLayer
SectorRollupBar                    ← moved up
─── section divider ───
DecisionPanel (12-col, max-h)     ← promoted, full-width
─── section divider ───
┌─────────────────────┐
│ Grid 6+6            │
│ Graph | Propagation │            ← Decisions removed, 2-panel
└─────────────────────┘
ImpactPanel
ExplanationPanel
StatusBar
```

**Section dividers** are thin `border-t` strips with a muted section label (e.g., "DECISION PRIORITIES" / "OPERATIONAL DETAIL"), matching the existing visual language of `TransmissionChannels` and `ExposureLayer` (which already use colored left-bar + uppercase label + horizontal rule).

**DecisionPanel full-width wrapper:** The existing `<DecisionPanel>` component renders as a flex-col with header and scrollable card list. When promoted to 12-col, we wrap it in a `max-h-[320px] overflow-y-auto` container to keep the single-screen constraint. No internal component changes.

**Graph + Propagation 6+6:** Change `lg:col-span-4` → `lg:col-span-6` on both wrappers. Remove the third column (DecisionPanel).

---

## 5. WHAT REMAINS UNCHANGED

| Item | Status |
|------|--------|
| `useCommandCenter` hook | Untouched — all data flow preserved |
| `command-store.ts` | Untouched — state management preserved |
| `mock-data.ts` | Untouched — demo data preserved |
| `live-mappers.ts` | Untouched — live API mapping preserved |
| `format.ts` | Untouched — all formatters preserved |
| `TransmissionChannels.tsx` | Untouched — layout and logic preserved |
| `ExposureLayer.tsx` | Untouched — country/sector derivation preserved |
| `SectorRollupBar.tsx` | Untouched — just moved position in parent JSX |
| `StatusBar.tsx` | Untouched — pipeline meta preserved |
| All backend APIs | Zero changes |
| All backend tests (140) | Zero changes |
| `page.tsx` (root `/`) | Zero changes — landing, scenario selector, results view untouched |
| All stores (`app-store`, `flow-store`, `authority-store`) | Zero changes |
| All persona views, detail panels, flow components | Zero changes |
| Graph explorer (`/graph-explorer`) | Zero changes |
| Impact map (`/map`) | Zero changes |
| Decisions page (`/decisions`) | Zero changes |
| Theme tokens, design system | Zero changes |
| `?run=<id>` URL contract | Preserved — same parameter, same behavior |
| Live/mock fallback behavior | Preserved — error banner, retry, mock switch all intact |
| `executeAction` flow | Preserved — decision execution + authority proposal unchanged |
| `Suspense` + `ErrorBoundary` wiring | Preserved |
| Loading skeleton, error state, empty state | Preserved |
| `handleCountrySelect` / `handleSectorSelect` bridges | Preserved |

---

## 6. RISKS

| Risk | Prob | Impact | Mitigation |
|------|------|--------|------------|
| **DecisionPanel at full-width may feel too tall** — Currently constrained by 4-col height; at 12-col it could show all cards and push Operational Detail off-screen | Medium | Low | Apply `max-h-[320px] overflow-y-auto` — cards scroll within bounds. Test with mock data (5 actions). |
| **Graph/Propagation losing vertical space** — Moving from flex-1 in the old 3-panel grid to a fixed section may clip the SVG graph | Medium | Low | Apply `max-h-[360px]` to the 6+6 grid wrapper. Graph SVG already has a fixed viewBox (520×420). |
| **Section dividers add ~48px total** — Two new label strips could push StatusBar slightly off-screen on 768px viewports | Low | Low | Section labels are 28px each. Test at 768px. If tight, reduce py from 2.5 to 1.5. |
| **No functional regression** — This is purely JSX reorder + string renames; no data flow or logic changes | N/A | N/A | Run `npx tsc --noEmit` after changes. Visually verify with mock data (no `?run=` param). |

---

## 7. ORDERED IMPLEMENTATION STEPS

| Step | Action | Risk |
|------|--------|------|
| **1** | Label renames: MacroOverviewHeader, DecisionCard, GraphPanel, PropagationView, ImpactPanel, ExplanationPanel (6 single-string edits) | Zero |
| **2** | Layout metadata: rename title in `layout.tsx` | Zero |
| **3** | Barrel cleanup: remove `EventHeader` export from `index.ts` | Zero |
| **4** | Delete `EventHeader.tsx` | Zero |
| **5** | `page.tsx` JSX reorder: move SectorRollupBar up, extract DecisionPanel to full-width section, convert 3-panel grid to 2-panel, add section dividers | Low — purely visual |
| **6** | Update the ASCII diagram comment at top of `page.tsx` to match new layout | Zero |
| **7** | `npx tsc --noEmit` — verify TypeScript clean | Verification |
| **8** | Visual verification at `localhost:3000/command-center` (mock mode) | Verification |

---

## 8. READINESS NOTE

**This plan is ready for immediate execution.** Every change is a string replacement or JSX block move within a single file (`page.tsx`) plus 6 single-line edits across component headers. No imports change. No props change. No data contracts change. No new components. No new dependencies.

**Pre-conditions met:**
- All target files audited and line numbers verified
- All label strings identified with exact before/after values
- Layout change is pure JSX reorder — no conditional logic affected
- Live/mock wiring, safety behavior, error handling, Suspense boundaries all outside the change surface

**Post-conditions to verify:**
- `npx tsc --noEmit` passes
- `/command-center` loads with mock data (no `?run=` param)
- Visual read-order matches: Macro → Transmission → Exposure → Decisions → Operational Detail
- DecisionPanel renders full-width with scroll
- Graph + Propagation render side-by-side at 6+6
- StatusBar remains pinned at bottom
- All labels read macro-first vocabulary

**Awaiting your go to execute.**
