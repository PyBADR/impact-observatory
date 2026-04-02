"use client";

/**
 * Impact Observatory | مرصد الأثر — Scenario Panel (Light Theme)
 */

interface ScenarioTemplate {
  id: string;
  title: string;
  title_ar: string;
  scenario_type: string;
  horizon_hours: number;
  shock_count: number;
}

interface Props {
  templates: ScenarioTemplate[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  severity: number;
  onSeverityChange: (s: number) => void;
  isRunning: boolean;
  isAr: boolean;
}

const TYPE_COLORS: Record<string, string> = {
  disruption: "text-io-danger",
  escalation: "text-io-warning",
  cascading: "text-purple-600",
  hypothetical: "text-cyan-600",
};

export function ScenarioPanel({
  templates,
  selectedId,
  onSelect,
  severity,
  onSeverityChange,
  isRunning,
  isAr,
}: Props) {
  return (
    <div className="space-y-4">
      <h2 className="text-xs font-bold text-io-accent uppercase tracking-wider">
        {isAr ? "المحاكاة" : "Scenarios"}
      </h2>

      <div className="space-y-1">
        {templates.map((t) => (
          <button
            key={t.id}
            onClick={() => onSelect(t.id)}
            disabled={isRunning}
            className={`w-full text-left p-2 rounded text-xs transition ${
              selectedId === t.id
                ? "bg-io-accent/10 border border-io-accent"
                : "bg-io-bg border border-io-border hover:border-io-accent/30"
            } ${isRunning ? "opacity-50 cursor-wait" : ""}`}
          >
            <div className="font-medium text-io-primary">
              {isAr ? t.title_ar : t.title}
            </div>
            <div className="flex items-center gap-2 mt-1">
              <span className={`${TYPE_COLORS[t.scenario_type] || "text-io-secondary"}`}>
                {t.scenario_type}
              </span>
              <span className="text-io-secondary">{t.horizon_hours}h</span>
              <span className="text-io-secondary">{t.shock_count} shocks</span>
            </div>
          </button>
        ))}
      </div>

      <div>
        <label className="block text-xs text-io-accent font-bold mb-1">
          {isAr ? "الشدة" : "Severity"}: {(severity * 100).toFixed(0)}%
        </label>
        <input
          type="range"
          min={0}
          max={1}
          step={0.01}
          value={severity}
          onChange={(e) => onSeverityChange(parseFloat(e.target.value))}
          className="w-full accent-io-accent"
        />
      </div>
    </div>
  );
}
