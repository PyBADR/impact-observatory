"use client";

import type { UnifiedRunResult, ImpactedEntity } from "@/types/observatory";

interface Props {
  result: UnifiedRunResult;
  selectedEntity?: ImpactedEntity | null;
  isAr?: boolean;
  /** CV-01 FIX: explicit pipeline stage count from the adapted RunResult.
   * UnifiedRunResult only carries stages_completed[] (always empty from backend);
   * the correct count lives in RunResult.pipeline_stages_completed. Pass it here. */
  stagesCompleted?: number;
}

const fmt = (n: number) =>
  n >= 1e9
    ? `$${(n / 1e9).toFixed(1)}B`
    : n >= 1e6
    ? `$${(n / 1e6).toFixed(1)}M`
    : `$${n.toLocaleString()}`;

export function ImpactOverlay({ result, selectedEntity, isAr = false, stagesCompleted }: Props) {
  const { headline, sector_rollups, decision_inputs, confidence, trust } = result;

  return (
    <div className="space-y-3">
      {/* Headline metrics */}
      <div className="bg-slate-900/90 backdrop-blur border border-slate-700 rounded-lg p-3">
        <h3 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
          {isAr ? "الملخص" : "Headline"}
        </h3>
        <div className="grid grid-cols-3 gap-2 text-center">
          <MetricCard
            label={isAr ? "إجمالي الخسارة" : "Total Loss"}
            value={fmt(headline.total_loss_usd)}
            color="text-red-400"
          />
          <MetricCard
            label={isAr ? "العقد المتأثرة" : "Nodes Hit"}
            value={String(headline.total_nodes_impacted)}
            color="text-amber-400"
          />
          <MetricCard
            label={isAr ? "الثقة" : "Confidence"}
            value={`${(confidence * 100).toFixed(0)}%`}
            color="text-emerald-400"
          />
        </div>
      </div>

      {/* Sector rollups */}
      <div className="bg-slate-900/90 backdrop-blur border border-slate-700 rounded-lg p-3">
        <h3 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
          {isAr ? "القطاعات" : "Sectors"}
        </h3>
        <div className="space-y-1.5">
          {Object.entries(sector_rollups)
            .filter(([, v]) => v.node_count > 0)
            .sort((a, b) => b[1].aggregate_stress - a[1].aggregate_stress)
            .map(([sector, data]) => (
              <SectorBar key={sector} sector={sector} data={data} isAr={isAr} />
            ))}
        </div>
      </div>

      {/* Top actions */}
      {decision_inputs.actions.length > 0 && (
        <div className="bg-slate-900/90 backdrop-blur border border-slate-700 rounded-lg p-3">
          <h3 className="text-xs font-semibold text-slate-400 mb-2 uppercase tracking-wider">
            {isAr ? "الإجراءات ذات الأولوية" : "Priority Actions"}
          </h3>
          <div className="space-y-1">
            {decision_inputs.actions.slice(0, 3).map((action) => (
              <div
                key={action.id}
                className="flex items-center justify-between text-xs p-1.5 rounded bg-slate-800/50"
              >
                <span className="text-slate-300 truncate flex-1">
                  {isAr ? (action.action_ar || action.action) : action.action}
                </span>
                <span className="text-indigo-400 font-mono ml-2">
                  P:{(action.priority ?? 0).toFixed(2)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Selected entity detail */}
      {selectedEntity && (
        <div className="bg-slate-900/90 backdrop-blur border border-indigo-500/30 rounded-lg p-3">
          <h3 className="text-xs font-semibold text-indigo-400 mb-1">
            {isAr && selectedEntity.label_ar ? selectedEntity.label_ar : selectedEntity.label}
          </h3>
          <div className="grid grid-cols-2 gap-1 text-[11px]">
            <span className="text-slate-400">{isAr ? "الضغط" : "Stress"}</span>
            <span className="text-white">{(selectedEntity.stress * 100).toFixed(1)}%</span>
            <span className="text-slate-400">{isAr ? "الخسارة" : "Loss"}</span>
            <span className="text-white">{fmt(selectedEntity.loss_usd)}</span>
            <span className="text-slate-400">{isAr ? "التصنيف" : "Class"}</span>
            <span className="text-white">{selectedEntity.classification}</span>
          </div>
        </div>
      )}

      {/* Trust badge */}
      {trust && (
        <div className="bg-slate-900/90 backdrop-blur border border-slate-700 rounded-lg p-2 flex items-center gap-2 text-[10px]">
          <span className="text-emerald-400">SHA-256</span>
          <span className="text-slate-500 font-mono truncate">{trust.audit_hash?.slice(0, 16)}...</span>
          <span className="text-slate-400 ml-auto">
            {/* CV-01 FIX: prefer the explicit prop count (from adaptedResult.pipeline_stages_completed),
                then trust.stages_completed length, then 0 — never shows a wrong zero */}
            {stagesCompleted ?? trust.stages_completed?.length ?? 0} stages
          </span>
        </div>
      )}
    </div>
  );
}

function MetricCard({ label, value, color }: { label: string; value: string; color: string }) {
  return (
    <div>
      <div className={`text-sm font-bold ${color}`}>{value}</div>
      <div className="text-[10px] text-slate-500">{label}</div>
    </div>
  );
}

function SectorBar({
  sector,
  data,
  isAr,
}: {
  sector: string;
  data: { aggregate_stress: number; total_loss: number; node_count: number; classification: string };
  isAr: boolean;
}) {
  const pct = Math.min(100, data.aggregate_stress * 100);
  const barColor =
    data.classification === "CRITICAL"
      ? "bg-red-500"
      : data.classification === "ELEVATED"
      ? "bg-orange-500"
      : data.classification === "MODERATE"
      ? "bg-yellow-500"
      : "bg-emerald-500";

  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-16 text-slate-400 capitalize truncate">{sector}</span>
      <div className="flex-1 h-1.5 bg-slate-800 rounded-full overflow-hidden">
        <div className={`h-full ${barColor} rounded-full`} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-slate-300 w-10 text-right font-mono">{pct.toFixed(0)}%</span>
    </div>
  );
}
