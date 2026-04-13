# Observatory V2 — Release Notes

## Summary

Full UI system reset. The frontend has been reinterpreted from a dashboard/SaaS application into a calm, institutional macro-financial briefing system for GCC executive decision-makers.

Every page reads as a sovereign-grade intelligence document. No KPI grids, no dashboard cards, no progress bars, no analytics console patterns.

## What Changed

### New Pages

**Scenario Briefing** (`/scenario/[slug]`) — Five-section vertical analysis: Context, Transmission, Impact, Decision, Outcome. Each section renders as labeled prose with numbered paragraphs. Transmission paths show source → target with delay and mechanism woven into a single sentence. Impact renders as stacked disclosure blocks, not column grids. Decisions embed owner/deadline/sector into the prose.

**Decision Directive** (`/decision/[slug]`) — Sovereign-grade directive document. One visually dominant primary directive at 1.25rem with rationale and consequence-of-inaction. Supporting actions rendered as subordinate numbered prose at 0.9375rem. Quiet briefing footer with reference, issued date, origin, and distribution.

**Evaluation Register** (`/evaluation`) — Institutional index of post-decision reviews sorted by verdict. Shows verdict color, correctness percentage, scenario title, and summary.

**Evaluation Review** (`/evaluation/[slug]`) — Six-section accountability document: expected vs actual outcome, correctness assessment, analyst commentary, institutional learning (replay summary), and rule performance audit.

### Redesigned Pages

**Landing Page** (`/`) — Replaced 4-column grid table with stacked register blocks matching the evaluation register pattern. Added section label, significance summary per scenario, full-bleed hover.

### New Data Manifests

- `src/lib/scenarios.ts` — 15-scenario briefing data with observatory-grade institutional prose
- `src/lib/decisions.ts` — 15-scenario decision directive data with primary directive, rationale, and consequence-of-inaction
- `src/lib/evaluations.ts` — 15-scenario evaluation data with expected/actual outcomes, correctness, analyst commentary, replay summary, rule performance

### Design System

- CSS custom properties (`var(--io-*)`) as the canonical token layer
- Palette: #F5F5F2 background, #1B1B19 charcoal, #252522 graphite, #A06A34 amber, #8E4338 red, #5E6759 olive
- Typography: DM Sans + IBM Plex Sans Arabic, `.io-label` utility for section labels
- Component composition: PageShell + Container + SectionBlock
- Tailwind extended with `io.*` color tokens

### Navigation

TopNav updated: Overview · Decisions · Evaluation. Cross-links at every junction:
- Scenario → Decision brief
- Decision → Scenario analysis, Evaluation
- Evaluation → Scenario, Decision

### README

Fully rewritten to reflect Observatory positioning. Removed dashboard language, KPI panel descriptions, and outdated scenario/stack references. Updated to 15 scenarios, React 19, institutional product description.

## Design Principles

1. **Vertical reading** — every page reads top to bottom like a memo, not scanned like a dashboard
2. **Prose over grids** — owner, deadline, sector embedded in sentences, not metadata rows
3. **Visual hierarchy through typography** — primary directives at 1.25rem semibold, supporting actions at 0.9375rem, labels at 0.75rem uppercase
4. **Whitespace as structure** — sections separated by `py-14 sm:py-16` and `border-b`, not cards or containers
5. **Status through color, not chrome** — severity/verdict indicated by olive/amber/red text color, not badges or pills

## Breaking Changes

None. Backend API is unchanged. All new pages use static manifest data (SSG-compatible) with the same scenario IDs as the backend SCENARIO_TEMPLATES.

## Files Changed

| Category | Files |
|---|---|
| Design system | `globals.css`, `tailwind.config.ts`, `layout.tsx`, `theme.ts` |
| Data manifests | `scenarios.ts`, `decisions.ts`, `evaluations.ts` |
| Copy constants | `copy.ts` |
| Layout components | `Container.tsx`, `SectionBlock.tsx`, `TopNav.tsx`, `PageShell.tsx` |
| Pages | `page.tsx` (landing), `scenario/[slug]/page.tsx`, `decision/[slug]/page.tsx`, `evaluation/page.tsx`, `evaluation/[slug]/page.tsx` |
| Documentation | `README.md` |
