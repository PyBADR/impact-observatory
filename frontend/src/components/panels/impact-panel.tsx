"use client";

/**
 * Impact Observatory | مرصد الأثر — Impact Panel (Light Theme)
 */

interface Props {
  result: any | null;
  isAr: boolean;
}

export function ImpactPanel({ result, isAr }: Props) {
  if (!result) {
    return (
      <div className="text-xs text-io-secondary p-2">
        {isAr ? "اختر سيناريو لعرض التأثير" : "Select a scenario to view impact"}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Score cards */}
      <div className="grid grid-cols-2 gap-2">
        <ScoreCard
          label={isAr ? "إجهاد النظام" : "System Stress"}
          value={result.system_stress}
          color="danger"
        />
        <ScoreCard
          label={isAr ? "خسارة اقتصادية" : "Econ. Loss"}
          value={`$${(result.total_economic_loss_usd / 1e9).toFixed(2)}B`}
          color="warning"
          isText
        />
      </div>

      {/* Top impacted */}
      <div>
        <h3 className="text-xs font-bold text-io-accent mb-2">
          {isAr ? "الأكثر تأثراً" : "Top Impacted"}
        </h3>
        <div className="space-y-1">
          {result.impacts?.slice(0, 8).map((imp: any) => (
            <div
              key={imp.entity_id}
              className="flex items-center justify-between text-[10px] py-1 border-b border-io-border"
            >
              <span className="text-io-primary">{imp.entity_id}</span>
              <span
                className={
                  imp.delta > 0.3
                    ? "text-io-danger"
                    : imp.delta > 0.1
                    ? "text-io-warning"
                    : "text-io-secondary"
                }
              >
                {imp.delta > 0 ? "+" : ""}
                {(imp.delta * 100).toFixed(1)}pp
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Recommendations */}
      <div>
        <h3 className="text-xs font-bold text-io-accent mb-2">
          {isAr ? "التوصيات" : "Recommendations"}
        </h3>
        <div className="space-y-2">
          {result.recommendations?.map((rec: string, i: number) => (
            <div
              key={i}
              className="text-[10px] text-io-secondary p-2 bg-io-bg rounded border-l-2 border-io-accent"
            >
              {rec}
            </div>
          ))}
        </div>
      </div>

      {/* Narrative */}
      <div>
        <h3 className="text-xs font-bold text-io-accent mb-2">
          {isAr ? "السرد" : "Narrative"}
        </h3>
        <pre className="text-[10px] text-io-secondary whitespace-pre-wrap font-mono">
          {result.narrative}
        </pre>
      </div>
    </div>
  );
}

function ScoreCard({
  label,
  value,
  color,
  isText,
}: {
  label: string;
  value: number | string;
  color: "danger" | "warning" | "accent";
  isText?: boolean;
}) {
  const colorMap = {
    danger: "text-io-danger border-io-danger",
    warning: "text-io-warning border-io-warning",
    accent: "text-io-accent border-io-accent",
  };

  return (
    <div
      className={`p-2 rounded bg-io-bg border ${colorMap[color]}`}
    >
      <div className="text-[10px] text-io-secondary">{label}</div>
      <div className={`text-lg font-bold ${colorMap[color].split(" ")[0]}`}>
        {isText ? value : `${((value as number) * 100).toFixed(1)}%`}
      </div>
    </div>
  );
}
