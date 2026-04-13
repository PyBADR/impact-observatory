/**
 * Impact Observatory | مرصد الأثر — Decision Register
 *
 * An institutional index of sovereign-grade decision directives.
 * Same calm register pattern as the landing and evaluation pages.
 * Reads as a directive ledger, not a task manager.
 */

import Link from 'next/link';
import { PageShell, Container } from '@/components/layout';
import { getDecisionsByClassification } from '@/lib/decisions';

const classificationColor: Record<string, string> = {
  Severe:   'text-[var(--io-status-red)]',
  High:     'text-[var(--io-status-red)]',
  Elevated: 'text-[var(--io-status-amber)]',
  Guarded:  'text-[var(--io-text-tertiary)]',
};

function cColor(level: string): string {
  return classificationColor[level] ?? 'text-[var(--io-text-tertiary)]';
}

export default function DecisionRegisterPage() {
  const decisions = getDecisionsByClassification();

  return (
    <PageShell>
      <Container>

        <header className="pt-16 sm:pt-20 pb-14 sm:pb-16 border-b border-[var(--io-border-muted)]">
          <p className="io-label mb-3">Directives</p>
          <h1 className="text-[1.75rem] sm:text-[2.25rem] font-bold tracking-tight leading-[1.12] text-[var(--io-charcoal)] mb-5">
            Decision Briefings
          </h1>
          <p className="text-[1rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl">
            Sovereign-grade directives issued for each active scenario. Primary actions, owners, deadlines, and expected effects — ordered by classification severity.
          </p>
        </header>

        <ol className="divide-y divide-[var(--io-border-muted)]">
          {decisions.map((d) => (
            <li key={d.id}>
              <Link
                href={`/decision/${d.id}`}
                className="group block py-6 sm:py-7 transition-colors duration-150 hover:bg-[var(--io-muted)]/40 -mx-6 sm:-mx-8 lg:-mx-12 px-6 sm:px-8 lg:px-12"
              >
                <div className="flex flex-col sm:flex-row sm:items-baseline gap-1 sm:gap-4 mb-2">
                  <span className={`text-[0.8125rem] font-semibold ${cColor(d.classification)}`}>
                    {d.classification}
                  </span>
                  <span className="text-[0.8125rem] text-[var(--io-text-tertiary)]">
                    {d.primaryDirective.owner} · {d.primaryDirective.deadline}
                  </span>
                </div>

                <p className="text-[1rem] font-medium text-[var(--io-charcoal)] group-hover:text-[var(--io-graphite)] transition-colors duration-150 mb-1.5">
                  {d.directiveTitle}
                </p>

                <p className="text-[0.875rem] leading-[1.65] text-[var(--io-text-secondary)] max-w-3xl">
                  {d.summary}
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
            {decisions.length} directives
          </span>
        </div>

      </Container>
    </PageShell>
  );
}
