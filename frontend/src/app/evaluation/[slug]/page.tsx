/**
 * Impact Observatory | مرصد الأثر — Evaluation Briefing
 *
 * An institutional accountability document — not an analytics dashboard.
 * Read top to bottom like a post-decision review memo.
 *
 *   1. Evaluation Identity   — verdict, scenario, summary
 *   2. Outcome Assessment    — expected vs actual in prose
 *   3. Correctness           — quiet score with rationale
 *   4. Analyst Commentary    — human-voice review
 *   5. Institutional Learning — replay summary
 *   6. Rule Performance      — calm audit list
 *
 * Data: src/lib/evaluations.ts (static manifest, SSG-compatible).
 */

import Link from 'next/link';
import { notFound } from 'next/navigation';
import { PageShell, Container } from '@/components/layout';
import { getEvaluation, getAllEvaluations } from '@/lib/evaluations';
import type { Verdict } from '@/lib/evaluations';

export async function generateStaticParams() {
  return getAllEvaluations().map((e) => ({ slug: e.id }));
}

const verdictColor: Record<Verdict, string> = {
  Confirmed:            'text-[var(--io-status-olive)]',
  'Partially Confirmed': 'text-[var(--io-status-amber)]',
  Revised:              'text-[var(--io-status-red)]',
  Inconclusive:         'text-[var(--io-text-tertiary)]',
};

function vColor(verdict: Verdict): string {
  return verdictColor[verdict] ?? 'text-[var(--io-text-tertiary)]';
}

export default async function EvaluationPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const e = getEvaluation(slug);
  if (!e) notFound();

  return (
    <PageShell>
      <Container>

        {/* Back */}
        <div className="pt-8 pb-4">
          <Link
            href="/evaluation"
            className="text-[0.8125rem] text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-150"
          >
            ← All evaluations
          </Link>
        </div>

        {/* ════════════════════════════════════════════════════
           EVALUATION IDENTITY
           ════════════════════════════════════════════════════ */}
        <header className="pt-6 pb-14 sm:pb-16 border-b border-[var(--io-border-muted)]">
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 mb-5">
            <span className="io-label">Evaluation</span>
            <span className={`text-[0.8125rem] font-semibold ${vColor(e.verdict)}`}>
              {e.verdict}
            </span>
            <span className="text-[0.8125rem] text-[var(--io-text-tertiary)]">
              {(e.correctness * 100).toFixed(0)}%
            </span>
          </div>

          <h1 className="text-[1.75rem] sm:text-[2.25rem] font-bold tracking-tight leading-[1.12] text-[var(--io-charcoal)] mb-6">
            {e.scenarioTitle}
          </h1>

          <p className="text-[1rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl mb-4">
            {e.summary}
          </p>

          <div className="flex flex-wrap items-baseline gap-x-5 gap-y-1">
            <Link
              href={`/scenario/${e.scenarioRef}`}
              className="text-[0.8125rem] text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-150"
            >
              View scenario →
            </Link>
            <Link
              href={`/decision/${e.scenarioRef}`}
              className="text-[0.8125rem] text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-150"
            >
              View decision brief →
            </Link>
          </div>
        </header>

        {/* ════════════════════════════════════════════════════
           OUTCOME ASSESSMENT
           ════════════════════════════════════════════════════ */}
        <section className="py-14 sm:py-16 border-b border-[var(--io-border-muted)]">
          <p className="io-label mb-6">Outcome Assessment</p>

          <div className="max-w-3xl space-y-10">
            <div>
              <p className="text-[0.8125rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-2">
                Expected
              </p>
              <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)]">
                {e.expectedOutcome}
              </p>
            </div>

            <div>
              <p className="text-[0.8125rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-2">
                Actual
              </p>
              <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)]">
                {e.actualOutcome}
              </p>
            </div>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════
           CORRECTNESS
           ════════════════════════════════════════════════════ */}
        <section className="py-14 sm:py-16 border-b border-[var(--io-border-muted)]">
          <p className="io-label mb-6">Correctness</p>

          <p className="text-[1.125rem] font-semibold text-[var(--io-charcoal)] mb-4">
            <span className={vColor(e.verdict)}>{e.verdict}</span>
            <span className="text-[var(--io-text-tertiary)] font-normal mx-2">at</span>
            {(e.correctness * 100).toFixed(0)}%
          </p>

          <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl">
            {e.correctnessRationale}
          </p>
        </section>

        {/* ════════════════════════════════════════════════════
           ANALYST COMMENTARY
           ════════════════════════════════════════════════════ */}
        <section className="py-14 sm:py-16 border-b border-[var(--io-border-muted)]">
          <p className="io-label mb-6">Analyst Commentary</p>

          <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl">
            {e.analystCommentary}
          </p>
        </section>

        {/* ════════════════════════════════════════════════════
           INSTITUTIONAL LEARNING
           ════════════════════════════════════════════════════ */}
        <section className="py-14 sm:py-16 border-b border-[var(--io-border-muted)]">
          <p className="io-label mb-6">Replay Summary</p>

          <p className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl">
            {e.replaySummary}
          </p>
        </section>

        {/* ════════════════════════════════════════════════════
           RULE PERFORMANCE
           ════════════════════════════════════════════════════ */}
        <section className="py-14 sm:py-16">
          <p className="io-label mb-6">Rule Performance</p>

          <ol className="space-y-4 max-w-3xl">
            {e.rulePerformance.map((rule, i) => (
              <li
                key={i}
                className="text-[0.875rem] leading-[1.7] text-[var(--io-text-secondary)]"
              >
                <span className="text-[var(--io-text-tertiary)] mr-2">{i + 1}.</span>
                {rule}
              </li>
            ))}
          </ol>
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
              <p className="text-xs text-[var(--io-text-tertiary)]">{e.id}</p>
            </div>
            <div>
              <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-1">
                Evaluated
              </p>
              <p className="text-xs text-[var(--io-text-tertiary)]">
                {new Date(e.evaluatedDate).toLocaleDateString('en-GB', {
                  day: 'numeric',
                  month: 'short',
                  year: 'numeric',
                })}
              </p>
            </div>
            <div>
              <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-1">
                Scenario
              </p>
              <Link
                href={`/scenario/${e.scenarioRef}`}
                className="text-xs text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-150"
              >
                View scenario →
              </Link>
            </div>
            <div>
              <p className="text-[0.6875rem] font-semibold uppercase tracking-[0.06em] text-[var(--io-text-tertiary)] mb-1">
                Decision
              </p>
              <Link
                href={`/decision/${e.scenarioRef}`}
                className="text-xs text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-150"
              >
                View directive →
              </Link>
            </div>
          </div>
        </footer>

      </Container>
    </PageShell>
  );
}
