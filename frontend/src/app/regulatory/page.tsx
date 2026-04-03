'use client';

/**
 * Impact Observatory | مرصد الأثر — Regulatory Compliance View
 * Shows Basel III / Solvency / IFRS 17 breach risk from a run result.
 */

import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useRunResult } from '@/hooks/use-api';
import { safeFixed } from '@/lib/format';

export default function RegulatoryPage() {
  const searchParams = useSearchParams();
  const runId = searchParams.get('runId');
  const { data: run, isLoading } = useRunResult(runId ?? '');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-io-bg flex items-center justify-center">
        <div className="text-io-secondary text-sm">Loading regulatory data...</div>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="min-h-screen bg-io-bg flex flex-col items-center justify-center gap-4">
        <div className="text-io-secondary text-sm">No simulation selected. Run a scenario first.</div>
        <Link href="/dashboard" className="text-xs text-io-accent border border-io-accent/30 rounded px-3 py-1 hover:bg-io-accent/5 transition">
          Go to Dashboard
        </Link>
      </div>
    );
  }

  const bank = run.banking_stress;
  const ins = run.insurance_stress;
  const plan = run.decision_plan;

  const breachRisk =
    bank.time_to_liquidity_breach_hours < 48
      ? 'CRITICAL'
      : bank.time_to_liquidity_breach_hours < 168
      ? 'HIGH'
      : 'NOMINAL';

  return (
    <div className="min-h-screen bg-io-bg text-io-primary">
      {/* Nav */}
      <header className="bg-io-surface border-b border-io-border px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="text-xs text-io-secondary hover:text-io-primary transition">
            ← Dashboard
          </Link>
          <span className="text-io-border">|</span>
          <span className="text-sm font-semibold text-io-primary">Regulatory Compliance View</span>
        </div>
        <span className="text-xs text-io-secondary">Scenario: {run.scenario_id}</span>
      </header>

      <main className="p-6 space-y-6 max-w-5xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Banking Regulatory */}
          <div className="bg-io-surface rounded-xl p-5 border border-io-border shadow-sm">
            <h2 className="text-base font-semibold mb-4 text-blue-600">Banking — Basel III</h2>
            <div className="space-y-3 text-sm">
              <Row
                label="Capital Adequacy Impact"
                value={`-${safeFixed(bank.capital_adequacy_impact_pct, 1)}%`}
                alert={bank.capital_adequacy_impact_pct > 5}
              />
              <Row
                label="Interbank Contagion"
                value={safeFixed(bank.interbank_contagion * 100, 1) + '%'}
                alert={bank.interbank_contagion > 0.5}
              />
              <Row
                label="Liquidity Stress"
                value={safeFixed(bank.liquidity_stress * 100, 1) + '%'}
                alert={bank.liquidity_stress > 0.6}
              />
              <Row
                label="Credit Stress"
                value={safeFixed(bank.credit_stress * 100, 1) + '%'}
                alert={bank.credit_stress > 0.6}
              />
              <Row
                label="Time to Liquidity Breach"
                value={
                  bank.time_to_liquidity_breach_hours >= 9999
                    ? 'N/A'
                    : `${safeFixed(bank.time_to_liquidity_breach_hours, 0)}h`
                }
                alert={bank.time_to_liquidity_breach_hours < 48}
              />
              <Row
                label="Breach Risk Classification"
                value={breachRisk}
                alert={breachRisk === 'CRITICAL'}
                warn={breachRisk === 'HIGH'}
              />
            </div>
          </div>

          {/* Insurance Regulatory */}
          <div className="bg-io-surface rounded-xl p-5 border border-io-border shadow-sm">
            <h2 className="text-base font-semibold mb-4 text-purple-600">Insurance — Solvency / IFRS 17</h2>
            <div className="space-y-3 text-sm">
              <Row
                label="Reinsurance Trigger"
                value={ins.reinsurance_trigger ? 'TRIGGERED' : 'CLEAR'}
                alert={ins.reinsurance_trigger}
              />
              <Row
                label="IFRS 17 Risk Adjustment"
                value={`+${safeFixed(ins.ifrs17_risk_adjustment_pct, 1)}%`}
                alert={ins.ifrs17_risk_adjustment_pct > 10}
              />
              <Row
                label="Claims Surge Multiplier"
                value={`${safeFixed(ins.claims_surge_multiplier, 2)}x`}
                alert={ins.claims_surge_multiplier > 3}
              />
              <Row
                label="Combined Ratio"
                value={safeFixed(ins.combined_ratio * 100, 1) + '%'}
                alert={ins.combined_ratio > 1.1}
                warn={ins.combined_ratio > 1.0}
              />
              <Row
                label="Time to Insolvency"
                value={
                  ins.time_to_insolvency_hours >= 9999
                    ? 'No imminent risk'
                    : `${safeFixed(ins.time_to_insolvency_hours, 0)}h`
                }
                alert={ins.time_to_insolvency_hours < 72}
              />
              <Row
                label="Aggregate Stress"
                value={safeFixed(ins.aggregate_stress * 100, 1) + '%'}
                alert={ins.aggregate_stress > 0.6}
                warn={ins.aggregate_stress > 0.4}
              />
            </div>
          </div>
        </div>

        {/* Escalation Triggers */}
        {plan.escalation_triggers && plan.escalation_triggers.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-5">
            <h2 className="text-base font-semibold mb-3 text-red-600">
              Active Escalation Triggers ({plan.escalation_triggers.length})
            </h2>
            <ul className="space-y-1 text-sm text-io-primary">
              {plan.escalation_triggers.map((t, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-red-500 mt-0.5 shrink-0">•</span>
                  <span>{t}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Monitoring priorities */}
        {plan.monitoring_priorities && plan.monitoring_priorities.length > 0 && (
          <div className="bg-io-surface border border-io-border rounded-xl p-5">
            <h2 className="text-base font-semibold mb-3 text-io-accent">Monitoring Priorities</h2>
            <ul className="space-y-1 text-sm text-io-secondary">
              {plan.monitoring_priorities.map((p, i) => (
                <li key={i} className="flex items-start gap-2">
                  <span className="text-io-accent mt-0.5 shrink-0">{i + 1}.</span>
                  <span>{p}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Links to other views */}
        <div className="flex gap-3 text-xs">
          <Link
            href={`/timeline${runId ? `?runId=${runId}` : ''}`}
            className="px-3 py-2 border border-io-border rounded-lg text-io-secondary hover:text-io-primary hover:border-io-accent/40 transition"
          >
            View Timeline
          </Link>
          <Link
            href={`/graph-explorer${runId ? `?runId=${runId}` : ''}`}
            className="px-3 py-2 border border-io-border rounded-lg text-io-secondary hover:text-io-primary hover:border-io-accent/40 transition"
          >
            Graph Explorer
          </Link>
        </div>
      </main>
    </div>
  );
}

function Row({
  label,
  value,
  alert,
  warn,
}: {
  label: string;
  value: string;
  alert?: boolean;
  warn?: boolean;
}) {
  return (
    <div className="flex justify-between items-center border-b border-io-border pb-2 last:border-0 last:pb-0">
      <span className="text-io-secondary">{label}</span>
      <span
        className={
          alert
            ? 'text-red-600 font-semibold'
            : warn
            ? 'text-amber-600 font-medium'
            : 'text-io-primary'
        }
      >
        {value}
      </span>
    </div>
  );
}
