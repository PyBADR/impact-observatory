/**
 * Impact Observatory | مرصد الأثر — Scenario Briefing
 *
 * A vertical institutional briefing — not a dashboard.
 * Read top to bottom like a sovereign intelligence memo.
 *
 *   1. Context        — what happened and why it matters now
 *   2. Transmission   — how pressure moves through the system
 *   3. Impact         — institutional exposure in business language
 *   4. Decision       — what must happen, by whom, by when
 *   5. Outcome        — expected result and monitoring criteria
 *
 * Data: src/lib/scenarios.ts (static manifest, SSG-compatible).
 */

import Link from 'next/link';
import { notFound } from 'next/navigation';
import { PageShell, Container } from '@/components/layout';
import { getScenario, getAllScenarios } from '@/lib/scenarios';
import type { ExposureLine } from '@/lib/scenarios';

export async function generateStaticParams() {
  return getAllScenarios().map((s) => ({ slug: s.id }));
}

const severityColor: Record<string, string> = {
  Severe:   'text-[var(--io-status-red)]',
  Critical: 'text-[var(--io-status-red)]',
  High:     'text-[var(--io-status-red)]',
  Elevated: 'text-[var(--io-status-amber)]',
  Guarded:  'text-[var(--io-text-tertiary)]',
};

function sColor(level: string): string {
  return severityColor[level] ?? 'text-[var(--io-text-tertiary)]';
}

export default async function ScenarioPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const b = getScenario(slug);
  if (!b) notFound();

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
           1. CONTEXT
           ════════════════════════════════════════════════════ */}
        <header className="pt-6 pb-14 sm:pb-16 border-b border-[var(--io-border-muted)]">
          {/* Metadata line */}
          <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1 mb-5">
            <span className={`text-[0.8125rem] font-semibold ${sColor(b.severity)}`}>
              {b.severity}
            </span>
            <span className="text-[0.8125rem] text-[var(--io-text-tertiary)]">
              {b.domain}
            </span>
            <span className="text-[0.8125rem] text-[var(--io-text-tertiary)]">
              {b.horizonHours}h horizon
            </span>
            <span className="text-[0.8125rem] text-[var(--io-text-tertiary)]">
              {b.sectors.join(' · ')}
            </span>
          </div>

          {/* Title */}
          <h1 className="text-[1.75rem] sm:text-[2.25rem] font-bold tracking-tight leading-[1.12] text-[var(--io-charcoal)] mb-8">
            {b.title}
          </h1>

          {/* Situational summary */}
          <p className="text-[1rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl mb-6">
            {b.context}
          </p>

          {/* Significance */}
          <p className="text-[0.9375rem] leading-[1.75] text-[var(--io-text-tertiary)] max-w-3xl">
            {b.significance}
          </p>
        </header>

        {/* ════════════════════════════════════════════════════
           2. TRANSMISSION
           ════════════════════════════════════════════════════ */}
        <section className="py-14 sm:py-16 border-b border-[var(--io-border-muted)]">
          <p className="io-label mb-3">How Pressure Transmits</p>
          <p className="text-[0.9375rem] leading-relaxed text-[var(--io-text-secondary)] max-w-3xl mb-10">
            {b.transmissionFraming}
          </p>

          <div className="space-y-8">
            {b.transmission.map((step, i) => (
              <p key={i} className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl">
                <span className="text-[var(--io-text-tertiary)] mr-2">{i + 1}.</span>
                <span className="font-medium text-[var(--io-charcoal)]">
                  {step.from} → {step.to}
                </span>
                {step.delayHours > 0 && (
                  <span className="text-[var(--io-text-tertiary)]"> (+{step.delayHours}h)</span>
                )}
                <span className="mx-1.5">—</span>
                {step.mechanism}
              </p>
            ))}
          </div>
        </section>

        {/* ════════════════════════════════════════════════════
           3. IMPACT
           ════════════════════════════════════════════════════ */}
        <section className="py-14 sm:py-16 border-b border-[var(--io-border-muted)]">
          <p className="io-label mb-3">Institutional Exposure</p>
          <p className="text-[0.9375rem] leading-relaxed text-[var(--io-text-secondary)] max-w-3xl mb-10">
            {b.impactFraming}
          </p>

          <div className="space-y-8">
            {b.impact.map((line: ExposureLine, i: number) => (
              <div key={i} className="max-w-3xl">
                <div className="flex items-baseline gap-3 mb-1.5">
                  <span className="text-[0.9375rem] font-medium text-[var(--io-charcoal)]">
                    {line.entity}
                  </span>
                  <span className={`text-[0.8125rem] font-semibold ${sColor(line.severity)}`}>
                    {line.severity}
                  </span>
                </div>
                <p className="text-[0.8125rem] text-[var(--io-text-tertiary)] mb-2">
                  {line.sector}
                </p>
                <p className="text-[0.875rem] leading-[1.7] text-[var(--io-text-secondary)]">
                  {line.exposure}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* ════════════════════════════════════════════════════
           4. DECISION
           ════════════════════════════════════════════════════ */}
        <section className="py-14 sm:py-16 border-b border-[var(--io-border-muted)]">
          <p className="io-label mb-3">Required Response</p>
          <p className="text-[0.9375rem] leading-relaxed text-[var(--io-text-secondary)] max-w-3xl mb-10">
            {b.decisionFraming}
          </p>

          <div className="space-y-8">
            {b.decisions.map((d, i) => (
              <p key={i} className="text-[0.9375rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl">
                <span className="text-[var(--io-text-tertiary)] mr-2">{i + 1}.</span>
                <span className="font-medium text-[var(--io-charcoal)]">{d.action}</span>
                <span className="mx-1.5">—</span>
                {d.owner}, by {d.deadline} ({d.sector})
              </p>
            ))}
          </div>

          <div className="mt-10">
            <Link
              href={`/decision/${b.id}`}
              className="text-[0.8125rem] text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)] transition-colors duration-150"
            >
              View decision brief →
            </Link>
          </div>
        </section>

        {/* ════════════════════════════════════════════════════
           5. OUTCOME
           ════════════════════════════════════════════════════ */}
        <section className="py-14 sm:py-16">
          <p className="io-label mb-3">Expected Outcome</p>
          <p className="text-[1rem] leading-[1.8] text-[var(--io-text-secondary)] max-w-3xl">
            {b.outcome}
          </p>

          <div className="mt-16">
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
        </section>

        {/* Quiet bottom */}
        <div className="py-8 border-t border-[var(--io-border-muted)] flex items-baseline justify-between">
          <span className="text-xs text-[var(--io-text-tertiary)]">
            Impact Observatory · مرصد الأثر
          </span>
          <span className="text-xs text-[var(--io-text-tertiary)]">
            {b.id}
          </span>
        </div>

      </Container>
    </PageShell>
  );
}
