/**
 * Impact Observatory | مرصد الأثر — Decision Briefing
 *
 * A sovereign-grade directive document — not a task board.
 * Read top to bottom like a board-level decision memo.
 *
 *   1. Directive Identity  — classification, imperative title, summary
 *   2. Primary Directive   — the single dominant action, with rationale
 *   3. Supporting Actions   — subordinate measures in numbered prose
 *   4. Expected Effect      — aggregate outcome and monitoring criteria
 *   5. Briefing Footer      — reference, issued, origin, distribution
 *
 * Data: src/lib/decisions.ts (static manifest, SSG-compatible).
 */

import Link from 'next/link';
import { notFound } from 'next/navigation';
import { PageShell, Container } from '@/components/layout';
import { getDecision, getAllDecisions } from '@/lib/decisions';

export async function generateStaticParams() {
  return getAllDecisions().map((d) => ({ slug: d.id }));
}

const classificationColor: Record<string, string> = {
  Severe:   'text-[var(--io-status-red)]',
  High:     'text-[var(--io-status-red)]',
  Elevated: 'text-[var(--io-status-amber)]',
  Guarded:  'text-[var(--io-text-tertiary)]',
};

function cColor(level: string): string {
  return classificationColor[level] ?? 'text-[var(--io-text-tertiary)]';
}

export default async function DecisionPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const b = getDecision(slug);
  if (!b) notFound();

  const pd = b.primaryDirective;

  return (
    <PageShell>
      <Container>

        {/* Back */}
        <div className="pt-8 pb-4">
          <Link
            href="/"
            className="text-[0.8125rem] text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-150"
          >
            ← All scenarios
          </Link>
        </div>

        {/* ════════════════════════════════════════════════════
           DIRECTIVE IDENTITY
           ════════════════════════════════════════════════════ */}
        <header className="pt-6 pb-14 sm:pb-16 border-b border-[var(--io-border-muted)]">
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 mb-5">
            <span className="io-label">Directive</span>
            <span className={`text-[0.8125rem] font-semibold ${cColor(b.classification)}`}>
              {b.classification}
            </span>
          </div>

          <h1 className="text-[1.75rem] sm:text-[2.25rem] font-bold tracking-tight leading-[1.12] text-[var(--io-charcoal)] mb-6">
            {b.directiveTitle}
          </h1>

          <p className="text-[1rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl mb-4">
            {b.summary}
          </p>

          <Link
            href={`/scenario/${b.scenarioRef}`}
            className="text-[0.8125rem] text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-150"
          >
            View scenario analysis →
          </Link>
        </header>

        {/* ════════════════════════════════════════════════════
           PRIMARY DIRECTIVE
           ════════════════════════════════════════════════════ */}
        <section className="py-14 sm:py-16 border-b border-[var(--io-border-muted)]">
          <p className="io-label mb-6">Primary Directive</p>

          <p className="text-[1.125rem] sm:text-[1.25rem] font-semibold leading-[1.5] text-[var(--io-charcoal)] max-w-3xl mb-3">
            {pd.action}
          </p>

          <p className="text-[0.9375rem] leading-[1.75] text-[var(--io-text-secondary)] max-w-3xl mb-10">
            {pd.owner} must execute within {pd.deadline}. Sector: {pd.sector}.
          </p>

          <div className="max-w-3xl space-y-8">
            <div>
              <p className="io-label mb-3">Rationale</p>
              <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)]">
                {pd.rationale}
              </p>
            </div>

            <div>
              <p className="io-label mb-3">If Not Executed</p>
              <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)]">
                {pd.consequenceOfInaction}
              </p>
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════
           SUPPORTING ACTIONS
           ════════════════════════════════════════════════════ */}
        {b.supportingActions.length > 0 && (
          <section className="py-14 sm:py-16 border-b border-[var(--io-border-muted)]">
            <p className="io-label mb-6">Supporting Actions</p>

            <div className="space-y-6">
              {b.supportingActions.map((a, i) => (
                <p key={i} className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl">
                  <span className="text-[var(--io-text-tertiary)] mr-2">{i + 1}.</span>
                  <span className="font-medium text-[var(--io-charcoal)]">{a.action}</span>
                  <span className="mx-1.5">—</span>
                  {a.owner}, by {a.deadline} ({a.sector})
                </p>
              ))}
            </div>
          </section>
        )}

        {/* ════════════════════════════════════════════════════
           EXPECTED EFFECT
           ════════════════════════════════════════════════════ */}
        <section className="py-14 sm:py-16">
          <p className="io-label mb-3">Expected Effect</p>
          <p className="text-[1rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl">
            {b.expectedEffect}
          </p>

          <div className="mt-14">
            <p className="io-label mb-6">Monitoring Criteria</p>
            <ol className="space-y-4 max-w-3xl">
              {b.monitoringCriteria.map((criterion, i) => (
                <li
                  key={i}
                  className="text-[0.875rem] leading-[1.7] text-[var(--io-text-secondary)]"
                >
                  <span className="text-[var(--io-text-tertiary)] mr-2">{i + 1}.</span>
                  {criterion}
                </li>
              ))}
            </ol>
          </div>

          <div className="mt-10">
            <Link
              href={`/evaluation/${b.id}`}
              className="text-[0.8125rem] text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-150"
            >
              View evaluation →
            </Link>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════
           BRIEFING FOOTER
           ════════════════════════════════════════════════════ */}
        <footer className="py-10 border-t border-[var(--io-border-muted)]">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-y-5 gap-x-8 max-w-3xl">
            <div>
              <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-1">
                Reference
              </p>
              <p className="text-xs text-[var(--io-text-tertiary)]">{b.id}</p>
            </div>
            <div>
              <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-1">
                Issued
              </p>
              <p className="text-xs text-[var(--io-text-tertiary)]">
                {new Date(b.issued).toLocaleDateString('en-GB', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric',
                })}
              </p>
            </div>
            <div>
              <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-1">
                Origin
              </p>
              <Link
                href={`/scenario/${b.scenarioRef}`}
                className="text-xs text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-150"
              >
                Scenario briefing →
              </Link>
            </div>
            <div className="col-span-2 sm:col-span-1">
              <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-1">
                Distribution
              </p>
              <p className="text-xs text-[var(--io-text-tertiary)] leading-relaxed">
                {b.distribution.join(' · ')}
              </p>
            </div>
          </div>
        </footer>

      </Container>
    </PageShell>
  );
}
