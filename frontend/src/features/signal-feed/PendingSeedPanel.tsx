"use client";

/**
 * PendingSeedPanel — HITL review panel for pending ScenarioSeeds.
 *
 * Data source: store.pendingSeeds (ScenarioSeed[])
 *              kept fresh by usePendingSeeds() (polls GET /pending every 15 s).
 *
 * Actions:
 *   Approve → useApproveSeed().mutate() → pipeline triggered inside hitl.approve()
 *   Reject  → useRejectSeed().mutate()  → no pipeline trigger
 */

import { useState } from "react";
import { useAppStore } from "@/store/app-store";
import { usePendingSeeds, useApproveSeed, useRejectSeed } from "@/hooks/use-api";
import type { ScenarioSeed, Language } from "@/types/observatory";

// ─── Module-level stable selectors ───────────────────────────────────────────
type AppS_PSP = ReturnType<typeof useAppStore.getState>;
const selectPendingSeeds_PSP = (s: AppS_PSP) => s.pendingSeeds;

interface SeedRowProps {
  seed: ScenarioSeed;
  onApprove: (seedId: string, reason: string) => void;
  onReject:  (seedId: string, reason: string) => void;
  isApproving: boolean;
  isRejecting: boolean;
  lang?: Language;
}

function SeedRow({ seed, onApprove, onReject, isApproving, isRejecting, lang = "en" }: SeedRowProps) {
  const [reason, setReason] = useState("");
  const busy = isApproving || isRejecting;
  const isAr = lang === "ar";

  return (
    <div className="border border-slate-200 rounded-lg p-4 flex flex-col gap-3 bg-white">
      <div className="flex items-start justify-between gap-2">
        <div className="flex flex-col gap-1">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 capitalize">
              {seed.sector}
            </span>
            <span className="text-xs font-mono text-slate-600">
              {seed.suggested_template_id}
            </span>
          </div>
          <span className="text-xs text-slate-400 font-mono">{seed.seed_id}</span>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-sm font-bold tabular-nums text-slate-800">
            {(seed.suggested_severity * 100).toFixed(1)}%
          </p>
          <p className="text-xs text-slate-400">{seed.suggested_horizon_hours}h horizon</p>
        </div>
      </div>

      <p className="text-xs text-slate-600 leading-relaxed border-l-2 border-slate-300 pl-3">
        {seed.rationale}
      </p>

      <div className="flex gap-2 items-center">
        <input
          type="text"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Optional reason…"
          disabled={busy}
          className="flex-1 text-xs border border-slate-200 rounded px-2 py-1.5 text-slate-700 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-blue-400 disabled:opacity-50"
        />
        <button
          onClick={() => onApprove(seed.seed_id, reason)}
          disabled={busy}
          className="shrink-0 px-3 py-1.5 rounded text-xs font-semibold bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isApproving ? (isAr ? "جارٍ الموافقة…" : "Approving…") : (isAr ? "موافقة" : "Approve")}
        </button>
        <button
          onClick={() => onReject(seed.seed_id, reason)}
          disabled={busy}
          className="shrink-0 px-3 py-1.5 rounded text-xs font-semibold bg-slate-200 text-slate-700 hover:bg-slate-300 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isRejecting ? (isAr ? "جارٍ الرفض…" : "Rejecting…") : (isAr ? "رفض" : "Reject")}
        </button>
      </div>
    </div>
  );
}

export function PendingSeedPanel({ lang = "en" }: { lang?: Language }) {
  const { isLoading, isError } = usePendingSeeds();
  const pendingSeeds = useAppStore(selectPendingSeeds_PSP);
  const approveSeed  = useApproveSeed();
  const rejectSeed   = useRejectSeed();
  const isAr = lang === "ar";

  const [actioning, setActioning] = useState<{ seedId: string; action: "approve" | "reject" } | null>(null);

  function handleApprove(seedId: string, reason: string) {
    setActioning({ seedId, action: "approve" });
    approveSeed.mutate(
      { seedId, reason: reason || undefined },
      { onSettled: () => setActioning(null) }
    );
  }

  function handleReject(seedId: string, reason: string) {
    setActioning({ seedId, action: "reject" });
    rejectSeed.mutate(
      { seedId, reason: reason || undefined },
      { onSettled: () => setActioning(null) }
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50">
        <div className="flex items-center gap-2">
          <span className="text-sm font-semibold text-slate-800">
            {isAr ? "الإشارات المالية في انتظار الموافقة" : "Financial Signals Awaiting Approval"}
          </span>
          {isLoading && <span className="text-xs text-slate-400">{isAr ? "جارٍ التحميل…" : "Loading…"}</span>}
          {isError && <span className="text-xs text-amber-600 font-medium">{isAr ? "تعذّر تحميل الموافقات" : "Unable to load pending approvals"}</span>}
        </div>
        <span className="text-xs text-slate-500 tabular-nums">
          {isAr ? `${pendingSeeds.length} في الانتظار` : `${pendingSeeds.length} pending`}
        </span>
      </div>

      <div className="max-h-96 overflow-y-auto p-3 flex flex-col gap-3">
        {pendingSeeds.length === 0 ? (
          <p className="py-6 text-sm text-slate-400 text-center">
            {isAr
              ? "لا توجد إشارات في انتظار الموافقة — الإشارات المعتمدة تطلق تشغيل سيناريو جديد"
              : "No signals pending approval — approved signals trigger a new scenario run"}
          </p>
        ) : (
          pendingSeeds.map((seed) => (
            <SeedRow
              key={seed.seed_id}
              seed={seed}
              onApprove={handleApprove}
              onReject={handleReject}
              isApproving={actioning?.seedId === seed.seed_id && actioning.action === "approve"}
              isRejecting={actioning?.seedId === seed.seed_id && actioning.action === "reject"}
              lang={lang}
            />
          ))
        )}
      </div>
    </div>
  );
}

export default PendingSeedPanel;
