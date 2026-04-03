'use client';

/**
 * Impact Observatory | مرصد الأثر — Impact Timeline
 * Recovery trajectory chart + decision action columns.
 */

import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { useRunResult } from '@/hooks/use-api';
import { safeFixed } from '@/lib/format';
import type { DecisionAction } from '@/types/observatory';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from 'recharts';

export default function TimelinePage() {
  const searchParams = useSearchParams();
  const runId = searchParams.get('runId');
  const { data: run, isLoading } = useRunResult(runId ?? '');

  if (isLoading) {
    return (
      <div className="min-h-screen bg-io-bg flex items-center justify-center">
        <div className="text-io-secondary text-sm">Loading timeline...</div>
      </div>
    );
  }

  if (!run) {
    return (
      <div className="min-h-screen bg-io-bg flex flex-col items-center justify-center gap-4">
        <div className="text-io-secondary text-sm">No simulation selected. Run a scenario first.</div>
        <Link
          href="/dashboard"
          className="text-xs text-io-accent border border-io-accent/30 rounded px-3 py-1 hover:bg-io-accent/5 transition"
        >
          Go to Dashboard
        </Link>
      </div>
    );
  }

  const trajectory = run.recovery_trajectory ?? [];
  const chartData = trajectory.map((p) => ({
    day: p.day,
    recovery: Math.round(p.recovery_fraction * 100),
    stress: Math.round(p.residual_stress * 100),
    damage: Math.round(p.damage_remaining * 100),
  }));

  const plan = run.decision_plan;
  const immediateActions: DecisionAction[] = plan.immediate_actions ?? [];
  const shortTermActions: DecisionAction[] = plan.short_term_actions ?? [];
  const longTermActions: DecisionAction[] = plan.long_term_actions ?? [];

  return (
    <div className="min-h-screen bg-io-bg text-io-primary">
      {/* Nav */}
      <header className="bg-io-surface border-b border-io-border px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="text-xs text-io-secondary hover:text-io-primary transition">
            ← Dashboard
          </Link>
          <span className="text-io-border">|</span>
          <span className="text-sm font-semibold text-io-primary">Impact Timeline</span>
        </div>
        <div className="text-xs text-io-secondary flex gap-4">
          <span>
            Peak day:{' '}
            <strong className="text-amber-600">D+{run.peak_day}</strong>
          </span>
          <span>
            Full recovery:{' '}
            <strong className="text-green-600">D+{run.headline?.max_recovery_days ?? '?'}</strong>
          </span>
          <span>Scenario: {run.scenario_id}</span>
        </div>
      </header>

      <main className="p-6 space-y-8 max-w-6xl mx-auto">
        {/* Recovery chart */}
        <div className="bg-io-surface rounded-xl p-5 border border-io-border shadow-sm">
          <h2 className="text-sm font-semibold text-io-primary mb-4">Recovery Trajectory</h2>
          {chartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={280}>
              <LineChart data={chartData} margin={{ top: 8, right: 16, bottom: 16, left: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" />
                <XAxis
                  dataKey="day"
                  stroke="#94A3B8"
                  tick={{ fontSize: 11, fill: '#94A3B8' }}
                  label={{ value: 'Day', position: 'insideBottom', offset: -4, fill: '#94A3B8', fontSize: 11 }}
                />
                <YAxis
                  stroke="#94A3B8"
                  tick={{ fontSize: 11, fill: '#94A3B8' }}
                  unit="%"
                  domain={[0, 100]}
                />
                <Tooltip
                  contentStyle={{
                    background: '#FFFFFF',
                    border: '1px solid #E2E8F0',
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                  labelFormatter={(v) => `Day ${v}`}
                />
                <Legend wrapperStyle={{ fontSize: 11, paddingTop: 12 }} />
                <ReferenceLine
                  x={run.peak_day}
                  stroke="#F59E0B"
                  strokeDasharray="4 4"
                  label={{ value: 'Peak', fill: '#F59E0B', fontSize: 11 }}
                />
                <Line
                  type="monotone"
                  dataKey="recovery"
                  stroke="#22C55E"
                  strokeWidth={2}
                  dot={false}
                  name="Recovery %"
                />
                <Line
                  type="monotone"
                  dataKey="stress"
                  stroke="#EF4444"
                  strokeWidth={2}
                  dot={false}
                  name="Stress %"
                />
                <Line
                  type="monotone"
                  dataKey="damage"
                  stroke="#F59E0B"
                  strokeWidth={1.5}
                  dot={false}
                  strokeDasharray="4 4"
                  name="Damage Remaining %"
                />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <div className="h-64 flex items-center justify-center text-io-secondary text-sm">
              No trajectory data for this simulation
            </div>
          )}
        </div>

        {/* Action columns */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <ActionColumn
            title="Immediate (0–6h)"
            colorClass="border-red-200"
            headerClass="text-red-600"
            actions={immediateActions}
          />
          <ActionColumn
            title="Short-term (6–24h)"
            colorClass="border-amber-200"
            headerClass="text-amber-600"
            actions={shortTermActions}
          />
          <ActionColumn
            title="Long-term (24h+)"
            colorClass="border-blue-200"
            headerClass="text-blue-600"
            actions={longTermActions}
          />
        </div>

        {/* Links to other views */}
        <div className="flex gap-3 text-xs">
          <Link
            href={`/regulatory${runId ? `?runId=${runId}` : ''}`}
            className="px-3 py-2 border border-io-border rounded-lg text-io-secondary hover:text-io-primary hover:border-io-accent/40 transition"
          >
            Regulatory View
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

function ActionColumn({
  title,
  colorClass,
  headerClass,
  actions,
}: {
  title: string;
  colorClass: string;
  headerClass: string;
  actions: DecisionAction[];
}) {
  return (
    <div className={`bg-io-surface rounded-xl p-4 border ${colorClass} shadow-sm`}>
      <h3 className={`text-sm font-semibold mb-3 ${headerClass}`}>{title}</h3>
      {actions.length === 0 ? (
        <p className="text-xs text-io-secondary">No actions in this window</p>
      ) : (
        <ul className="space-y-2">
          {actions.map((a) => (
            <li key={a.action_id ?? a.id} className="text-xs border-l-2 border-io-border pl-2">
              <div className="text-io-primary leading-snug">{a.action}</div>
              <div className="text-io-secondary mt-0.5">
                {a.owner} · {safeFixed(a.priority_score * 100, 0)}% priority
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
