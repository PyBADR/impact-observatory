"use client";

/**
 * Impact Observatory | مرصد الأثر — Scientist Bar (Light Theme)
 */

interface Props {
  result: any | null;
  isAr: boolean;
}

export function ScientistBar({ result, isAr }: Props) {
  if (!result) {
    return (
      <div className="px-4 py-2 bg-io-surface border-t border-io-border text-xs text-io-secondary">
        {isAr ? "في انتظار المحاكاة" : "Awaiting simulation"}
      </div>
    );
  }

  const metrics = [
    {
      label: isAr ? "طاقة النظام" : "System Energy",
      value: `${(result.system_stress * 100).toFixed(1)}%`,
      color:
        result.system_stress > 0.5
          ? "text-io-danger"
          : result.system_stress > 0.2
          ? "text-io-warning"
          : "text-io-success",
    },
    {
      label: isAr ? "خسارة اقتصادية" : "Econ. Loss",
      value: `$${(result.total_economic_loss_usd / 1e9).toFixed(2)}B`,
      color: "text-io-warning",
    },
    {
      label: isAr ? "كيانات متأثرة" : "Impacted Entities",
      value: String(result.impacts?.length || 0),
      color: "text-io-primary",
    },
    {
      label: isAr ? "السيناريو" : "Scenario",
      value: result.title || result.scenario_id,
      color: "text-io-accent",
    },
  ];

  return (
    <div className="px-4 py-2 bg-io-surface border-t border-io-border flex items-center gap-6 text-xs">
      {metrics.map((m) => (
        <div key={m.label} className="flex items-center gap-2">
          <span className="text-io-secondary">{m.label}:</span>
          <span className={`font-mono font-bold ${m.color}`}>{m.value}</span>
        </div>
      ))}
    </div>
  );
}
