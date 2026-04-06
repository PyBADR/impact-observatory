"use client";

/**
 * Impact Observatory | مرصد الأثر — Decision Control Room
 *
 * Institutional decision management surface.
 * Wired to useRunState: scenario context, adapted result, live run_id.
 * Shows DecisionDetailPanel when an active run exists.
 * Shows empty state guidance when no run is active.
 *
 * AppShell provides: unified nav, persona switch, language switch.
 * activeRoute="decisions" highlights Decision Room in nav.
 */

import AppShell from "@/components/shell/AppShell";
import { useAppStore } from "@/store/app-store";
import { useRunState } from "@/lib/run-state";
import { OperatorDecisionPanel } from "@/features/decisions/OperatorDecisionPanel";
import DecisionDetailPanel from "@/features/decisions/DecisionDetailPanel";
import type { Language } from "@/types/observatory";

// ── Empty state when no active run ─────────────────────────────────────

function DecisionRoomEmptyState({ isAr }: { isAr: boolean }) {
  return (
    <div className="flex-1 flex items-center justify-center bg-io-bg">
      <div className="max-w-sm w-full mx-6 text-center">
        <div className="w-12 h-12 border border-io-border rounded-xl flex items-center justify-center mx-auto mb-4 bg-io-surface">
          <svg
            className="w-6 h-6 text-io-secondary"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z"
            />
          </svg>
        </div>
        <p className="text-sm font-semibold text-io-primary mb-2">
          {isAr ? "لا يوجد تشغيل نشط" : "No Active Run"}
        </p>
        <p className="text-xs text-io-secondary leading-relaxed mb-4">
          {isAr
            ? "شغّل سيناريو من لوحة المعلومات لعرض خطة القرار هنا. يمكنك بعدها الموافقة على الإجراءات أو رفضها أو تصعيدها."
            : "Run a scenario from the dashboard to populate the decision plan here. You can then approve, reject, or escalate recommended actions."}
        </p>
        <a
          href="/"
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg bg-io-accent text-white hover:bg-blue-700 transition-colors"
        >
          {isAr ? "الانتقال إلى لوحة المعلومات" : "Go to Dashboard"}
        </a>
      </div>
    </div>
  );
}

// ── Main Page ──────────────────────────────────────────────────────────

export default function DecisionsPage() {
  const language = useAppStore((s) => s.language);
  const isAr = language === "ar";
  const lang: Language = isAr ? "ar" : "en";

  const adaptedResult = useRunState((s) => s.adaptedResult);
  const scenarioLabel = adaptedResult?.scenario?.label ?? undefined;

  const hasRun = adaptedResult !== null;
  const decisionPlan = adaptedResult?.decisions ?? null;
  const explanation = adaptedResult?.explanation ?? undefined;

  return (
    <AppShell activeRoute="decisions" scenarioLabel={scenarioLabel}>
      <div className="flex h-[calc(100vh-56px)] overflow-hidden" dir={isAr ? "rtl" : "ltr"}>

        {/* ── Left: Operator Decision Panel ───────────────────────── */}
        <div className="w-80 flex-shrink-0 border-r border-io-border bg-io-surface overflow-y-auto">
          <OperatorDecisionPanel lang={lang} />
        </div>

        {/* ── Right: Decision Detail Panel or Empty State ──────────── */}
        {hasRun && decisionPlan ? (
          <div className="flex-1 overflow-y-auto bg-io-bg p-6">
            <DecisionDetailPanel
              decisions={decisionPlan}
              explanation={explanation}
              lang={lang}
            />
          </div>
        ) : (
          <DecisionRoomEmptyState isAr={isAr} />
        )}
      </div>
    </AppShell>
  );
}
