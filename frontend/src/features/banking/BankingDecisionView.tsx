"use client";

/**
 * Banking Decision View — Contract Intelligence Assembly
 *
 * Parent component that fetches the full banking decision chain for a run
 * and distributes contracts to child panels:
 *   1. DecisionContractCard  → decision_contract
 *   2. CounterfactualPanel   → counterfactual_contract
 *   3. PropagationPathView   → propagation_contracts[]
 *   4. OutcomeValuePanel     → outcome_review_contract + value_audit
 *
 * Data flow: useBankingChain(runId) → chain → child panels
 */

import { useMemo } from "react";
import { useBankingChain, useBridgeFromRun } from "@/hooks/use-banking-api";
import { DecisionContractCard } from "./DecisionContractCard";
import CounterfactualPanel from "./CounterfactualPanel";
import PropagationPathView from "./PropagationPathView";
import OutcomeValuePanel from "./OutcomeValuePanel";

interface BankingDecisionViewProps {
  /** Simulation run ID to fetch chain for */
  runId: string | null;
  /** Optional scenario ID for bridge-from-run */
  scenarioId?: string;
  /** UI language */
  lang?: "en" | "ar";
}

// ─── Loading State ───────────────────────────────────────────────────────────

function ChainLoading({ isAr }: { isAr: boolean }) {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="flex flex-col items-center gap-3">
        <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        <p className="text-sm text-slate-400">
          {isAr ? "جاري تحميل عقود القرار..." : "Loading decision contracts..."}
        </p>
      </div>
    </div>
  );
}

// ─── Error State ─────────────────────────────────────────────────────────────

function ChainError({ message, isAr }: { message: string; isAr: boolean }) {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="max-w-sm text-center px-6">
        <div className="w-10 h-10 rounded-lg bg-red-500/10 border border-red-500/20 flex items-center justify-center mx-auto mb-3">
          <span className="text-red-400 text-sm font-bold">!</span>
        </div>
        <p className="text-sm font-medium text-slate-200 mb-1">
          {isAr ? "خطأ في تحميل العقود" : "Contract Chain Error"}
        </p>
        <p className="text-xs text-slate-500">{message}</p>
      </div>
    </div>
  );
}

// ─── Empty State (no run) ────────────────────────────────────────────────────

function ChainEmpty({
  isAr,
  scenarioId,
  onBridge,
  isBridging,
}: {
  isAr: boolean;
  scenarioId?: string;
  onBridge?: () => void;
  isBridging: boolean;
}) {
  return (
    <div className="flex items-center justify-center py-16">
      <div className="max-w-sm text-center px-6">
        <div className="w-10 h-10 rounded-lg bg-slate-700/50 border border-slate-600/30 flex items-center justify-center mx-auto mb-3">
          <svg
            className="w-5 h-5 text-slate-400"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"
            />
          </svg>
        </div>
        <p className="text-sm font-medium text-slate-200 mb-1">
          {isAr
            ? "لا توجد عقود قرار لهذا التشغيل"
            : "No Decision Contracts for This Run"}
        </p>
        <p className="text-xs text-slate-500 mb-4">
          {isAr
            ? "شغّل الجسر لإنشاء عقود قرار من نتائج المحاكاة."
            : "Bridge simulation results to generate decision contracts."}
        </p>
        {scenarioId && onBridge && (
          <button
            onClick={onBridge}
            disabled={isBridging}
            className="px-4 py-2 text-xs font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isBridging
              ? isAr
                ? "جاري الإنشاء..."
                : "Generating..."
              : isAr
                ? "إنشاء عقود القرار"
                : "Generate Decision Contracts"}
          </button>
        )}
      </div>
    </div>
  );
}

// ─── Section Header ──────────────────────────────────────────────────────────

function SectionHeader({
  title,
  titleAr,
  isAr,
}: {
  title: string;
  titleAr: string;
  isAr: boolean;
}) {
  return (
    <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3 px-1">
      {isAr ? titleAr : title}
    </h3>
  );
}

// ─── Main Component ──────────────────────────────────────────────────────────

export function BankingDecisionView({
  runId,
  scenarioId,
  lang = "en",
}: BankingDecisionViewProps) {
  const isAr = lang === "ar";

  // Fetch the chain
  const {
    data: chain,
    isLoading,
    isError,
    error,
  } = useBankingChain(runId);

  // Bridge mutation (generate contracts from a run)
  const bridgeMutation = useBridgeFromRun();

  const handleBridge = useMemo(() => {
    if (!runId || !scenarioId) return undefined;
    return () => {
      bridgeMutation.mutate({
        runId,
        scenarioId,
        baselineUrs: 0.25,
      });
    };
  }, [runId, scenarioId, bridgeMutation]);

  // ── Loading ──
  if (!runId) {
    return <ChainEmpty isAr={isAr} isBridging={false} />;
  }
  if (isLoading) {
    return <ChainLoading isAr={isAr} />;
  }
  if (isError) {
    // If chain not found, offer to generate it
    const is404 = (error as { status?: number })?.status === 404;
    if (is404) {
      return (
        <ChainEmpty
          isAr={isAr}
          scenarioId={scenarioId}
          onBridge={handleBridge}
          isBridging={bridgeMutation.isPending}
        />
      );
    }
    return (
      <ChainError
        message={error instanceof Error ? error.message : String(error)}
        isAr={isAr}
      />
    );
  }
  if (!chain) {
    return (
      <ChainEmpty
        isAr={isAr}
        scenarioId={scenarioId}
        onBridge={handleBridge}
        isBridging={bridgeMutation.isPending}
      />
    );
  }

  // ── Render full chain ──
  return (
    <div className="space-y-6" dir={isAr ? "rtl" : "ltr"}>
      {/* ── 1. Decision Contract ── */}
      <section>
        <SectionHeader
          title="Decision Contract"
          titleAr="عقد القرار"
          isAr={isAr}
        />
        <DecisionContractCard contract={chain.decision_contract} lang={lang} />
      </section>

      {/* ── 2. Counterfactual Analysis ── */}
      <section>
        <SectionHeader
          title="Counterfactual Analysis"
          titleAr="التحليل المقارن"
          isAr={isAr}
        />
        <CounterfactualPanel
          contract={chain.counterfactual_contract}
          lang={lang}
        />
      </section>

      {/* ── 3. Propagation Paths ── */}
      {chain.propagation_contracts.length > 0 && (
        <section>
          <SectionHeader
            title="Propagation Paths"
            titleAr="مسارات الانتشار"
            isAr={isAr}
          />
          <PropagationPathView
            propagations={chain.propagation_contracts}
            lang={lang}
          />
        </section>
      )}

      {/* ── 4. Outcome Review + Value Audit ── */}
      <section>
        <SectionHeader
          title="Outcome Review & Value Audit"
          titleAr="مراجعة النتائج وتدقيق القيمة"
          isAr={isAr}
        />
        <OutcomeValuePanel
          review={chain.outcome_review_contract}
          lang={lang}
        />
      </section>
    </div>
  );
}
