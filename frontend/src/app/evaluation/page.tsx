/**
 * Impact Observatory | مرصد الأثر — Evaluation Register
 *
 * An institutional index of post-decision evaluations.
 * Same calm register pattern as the landing page.
 * Reads as an accountability ledger, not an analytics console.
 */

import Link from 'next/link';
import { PageShell, Container } from '@/components/layout';
import { getEvaluationsByVerdict } from '@/lib/evaluations';
import type { Verdict } from '@/lib/evaluations';

const verdictColor: Record<Verdict, string> = {
  Confirmed:            'text-[var(--io-status-olive)]',
  'Partially Confirmed': 'text-[var(--io-status-amber)]',
  Revised:              'text-[var(--io-status-red)]',
  Inconclusive:         'text-[var(--io-text-tertiary)]',
};

export default function EvaluationRegisterPage() {
  const evaluations = getEvaluationsByVerdict();

  return (
    <PageShell>
      <Container>

        <header className="pt-16 sm:pt-20 pb-14 sm:pb-16 border-b border-[var(--io-border-muted)]">
          <p className="io-label mb-3">Accountability</p>
          <h1 className="text-[1.75rem] sm:text-[2.25rem] font-bold tracking-tight leading-[1.12] text-[var(--io-charcoal)] mb-5">
            Decision Evaluation
          </h1>
          <p className="text-[1rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl">
            Post-decision review for each scenario. Expected outcomes compared against actual results, with analyst commentary and institutional learning.
          </p>
        </header>

        <ol className="divide-y divide-[var(--io-border-muted)]">
          {evaluations.map((e) => (
            <li key={e.id}>
              <Link
                href={`/evaluation/${e.id}`}
                className="group block py-6 sm:py-7 transition-colors duration-150 hover:bg-[var(--io-muted)]/40 -mx-6 sm:-mx-8 lg:-mx-12 px-6 sm:px-8 lg:px-12"
              >
                <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 mb-2">
                  <span className={`text-[0.8125rem] font-semibold ${verdictColor[e.verdict]}`}>
                    {e.verdict}
                  </span>
                  <span className="text-[0.8125rem] text-[var(--io-text-tertiary)]">
                    {(e.correctness * 100).toFixed(0)}% correctness
                  </span>
                </div>

                <p className="text-[1rem] font-medium text-[var(--io-charcoal)] group-hover:text-[var(--io-graphite)] transition-colors duration-150 mb-1.5">
                  {e.scenarioTitle}
                </p>

                <p className="text-[0.875rem] leading-[1.65] text-[var(--io-text-secondary)] max-w-3xl">
                  {e.summary}
                </p>
              </Link>
            </li>
          ))}
        </ol>

        <div className="py-8 border-t border-[var(--io-border-muted)] flex items-baseline justify-between">
          <span className="text-xs text-[var(--io-text-tertiary)]">
            Impact Observatory · مرصد الأثر
          </span>
          <span className="text-xs text-[var(--io-text-tertiary)]">
            {evaluations.length} evaluations
          </span>
        </div>

      </Container>
    </PageShell>
  );
}
