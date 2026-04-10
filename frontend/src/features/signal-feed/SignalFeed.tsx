"use client";

/**
 * SignalFeed — live view of signal.scored events from /ws/signals.
 *
 * Data source: store.liveSignals (WsSignalScoredData[])
 *              populated by useSignalStream() which this component mounts.
 *
 * Scope: banking + fintech only (matches backend MVP).
 * No props — reads directly from Zustand store.
 */

import { useAppStore } from "@/store/app-store";
import { useSignalStream } from "@/hooks/use-api";
import type { WsSignalScoredData, Language } from "@/types/observatory";

// ─── Module-level stable selectors ───────────────────────────────────────────
type AppS_SF = ReturnType<typeof useAppStore.getState>;
const selectLiveSignals_SF = (s: AppS_SF) => s.liveSignals;

function scoreLabel(score: number): { text: string; cls: string } {
  if (score >= 0.7) return { text: "HIGH", cls: "bg-red-100 text-red-700" };
  if (score >= 0.4) return { text: "MED",  cls: "bg-amber-100 text-amber-700" };
  return               { text: "LOW",  cls: "bg-slate-100 text-slate-600" };
}

function fmtTime(iso: string): string {
  try {
    return new Date(iso).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
  } catch {
    return iso;
  }
}

function SignalRow({ signal }: { signal: WsSignalScoredData }) {
  const { text, cls } = scoreLabel(signal.signal_score);
  return (
    <div className="flex items-center gap-3 px-4 py-2.5 border-b border-slate-100 last:border-0 text-sm">
      <span className={`shrink-0 inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wide ${cls}`}>
        {text} {signal.signal_score.toFixed(3)}
      </span>
      <span className="shrink-0 inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 capitalize">
        {signal.sector}
      </span>
      <span className="flex-1 font-mono text-xs text-slate-700 truncate">
        {signal.event_type}
      </span>
      <span className="shrink-0 text-xs text-slate-400 uppercase tracking-wide">
        {signal.source}
      </span>
      <span className="shrink-0 text-xs text-slate-400 tabular-nums">
        {fmtTime(signal.scored_at)}
      </span>
    </div>
  );
}

export function SignalFeed({ lang = "en" }: { lang?: Language }) {
  useSignalStream();
  const liveSignals = useAppStore(selectLiveSignals_SF);
  const isAr = lang === "ar";

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50">
        <div className="flex items-center gap-2">
          <span className="inline-block w-2 h-2 rounded-full bg-green-500 animate-pulse" />
          <span className="text-sm font-semibold text-slate-800">
            {isAr ? "الإشارات المالية الحية" : "Live Financial Signals"}
          </span>
        </div>
        <span className="text-xs text-slate-500 tabular-nums">
          {isAr
            ? `${liveSignals.length} إشارة`
            : `${liveSignals.length} signal${liveSignals.length !== 1 ? "s" : ""}`}
        </span>
      </div>
      <div className="max-h-64 overflow-y-auto">
        {liveSignals.length === 0 ? (
          <p className="px-4 py-6 text-sm text-slate-400 text-center">
            {isAr ? "لا توجد إشارات حية" : "No live signals received"}
          </p>
        ) : (
          liveSignals.map((s) => (
            <SignalRow key={`${s.signal_id}-${s.scored_at}`} signal={s} />
          ))
        )}
      </div>
    </div>
  );
}

export default SignalFeed;
