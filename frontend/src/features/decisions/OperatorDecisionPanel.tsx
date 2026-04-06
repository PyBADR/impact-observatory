"use client";

/**
 * Impact Observatory | مرصد الأثر — Operator Decision Panel (v2)
 *
 * AUDIT FIX v2 — corrects the following defects from the v1 surface:
 *
 *  1. REMOVED: manual signal_id / seed_id / run_id free-text inputs
 *  2. ADDED:   auto-linked source context from selected scenario + live signals
 *  3. ADDED:   decision type selector, rationale, confidence slider, impact preview
 *  4. FIXED:   raw API 404/409 errors no longer shown — user-safe messages only
 *  5. ADDED:   empty-state guidance that directs user to select a scenario first
 *  6. ADDED:   source context chips on create form showing what will be linked
 *  7. ADDED:   impact preview section showing scenario loss + stress before commit
 *
 * Data flow:
 *   selectedScenarioId → scenarioResult (store)
 *     → auto-populates source_seed_id (from pending seeds matching scenario)
 *   liveSignals (store) → signal picker (filterable)
 *     → auto-populates source_signal_id
 *   scenarioResult.run_id → auto-populates source_run_id
 *
 * Backend truth: all state derived from /api/v1/decisions
 * No optimistic mutations — state reflects what the backend confirmed.
 */

import React, { useState, useMemo } from "react";
import {
  useDecisions,
  useCreateDecision,
  useExecuteDecision,
  useCloseDecision,
} from "@/hooks/use-api";
import { useAppStore } from "@/store/app-store";
import { useRunState } from "@/lib/run-state";
import type {
  OperatorDecision,
  DecisionType,
  OperatorDecisionStatus,
  WsSignalScoredData,
  Language,
} from "@/types/observatory";

// ── Constants ─────────────────────────────────────────────────────────────────

const DECISION_TYPES: {
  value: DecisionType;
  label: string;
  label_ar: string;
  description: string;
  description_ar: string;
}[] = [
  {
    value: "APPROVE_ACTION",
    label: "Approve Action",
    label_ar: "الموافقة على الإجراء",
    description: "Approve a recommended action from a run decision plan",
    description_ar: "الموافقة على إجراء موصى به من خطة قرارات التشغيل",
  },
  {
    value: "REJECT_ACTION",
    label: "Reject Action",
    label_ar: "رفض الإجراء",
    description: "Reject a recommended action with rationale",
    description_ar: "رفض إجراء موصى به مع توضيح السبب",
  },
  {
    value: "ESCALATE",
    label: "Escalate",
    label_ar: "تصعيد",
    description: "Escalate situation to higher authority",
    description_ar: "تصعيد الموقف إلى جهة أعلى",
  },
  {
    value: "IGNORE",
    label: "Ignore",
    label_ar: "تجاهل",
    description: "Consciously ignore this signal/seed/run",
    description_ar: "تجاهل هذه الإشارة/البذرة/التشغيل بشكل واعٍ",
  },
  {
    value: "TRIGGER_RUN",
    label: "Trigger Run",
    label_ar: "تشغيل جديد",
    description: "Manually trigger a new pipeline run",
    description_ar: "تشغيل دورة تحليل جديدة يدوياً",
  },
  {
    value: "OVERRIDE_RUN_RESULT",
    label: "Override Run Result",
    label_ar: "تجاوز نتيجة التشغيل",
    description: "Override automated assessment with manual judgment",
    description_ar: "تجاوز التقييم الآلي بحكم يدوي",
  },
];

const STATUS_COLORS: Record<OperatorDecisionStatus, string> = {
  CREATED:   "bg-gray-100 text-gray-700 border-gray-200",
  IN_REVIEW: "bg-blue-50 text-blue-700 border-blue-200",
  EXECUTED:  "bg-green-50 text-green-700 border-green-200",
  FAILED:    "bg-red-50 text-red-700 border-red-200",
  CLOSED:    "bg-gray-50 text-gray-500 border-gray-200",
};

const TYPE_COLORS: Record<DecisionType, string> = {
  APPROVE_ACTION:      "text-green-600",
  REJECT_ACTION:       "text-red-600",
  ESCALATE:            "text-orange-600",
  IGNORE:              "text-gray-500",
  TRIGGER_RUN:         "text-blue-600",
  OVERRIDE_RUN_RESULT: "text-purple-600",
};

const TYPE_ICONS: Record<DecisionType, string> = {
  APPROVE_ACTION:      "✓",
  REJECT_ACTION:       "✗",
  ESCALATE:            "↑",
  IGNORE:              "—",
  TRIGGER_RUN:         "▶",
  OVERRIDE_RUN_RESULT: "⊘",
};

// ── User-safe error messages (bilingual) ─────────────────────────────────────

const USER_ERROR_MESSAGES: Record<string, { en: string; ar: string }> = {
  create:  {
    en: "Unable to create decision. Please check your inputs and retry.",
    ar: "تعذّر إنشاء القرار. يرجى مراجعة المدخلات والمحاولة مجدداً.",
  },
  execute: {
    en: "Unable to execute decision. It may have already been processed.",
    ar: "تعذّر تنفيذ القرار. قد يكون قد تمّت معالجته بالفعل.",
  },
  close:   {
    en: "Unable to close decision. It may not be in a closeable state.",
    ar: "تعذّر إغلاق القرار. قد لا يكون في حالة قابلة للإغلاق.",
  },
  load:    {
    en: "Unable to load decisions. Please retry or contact support.",
    ar: "تعذّر تحميل القرارات. يرجى المحاولة مجدداً أو التواصل مع الدعم.",
  },
};

const FALLBACK_ERROR = {
  en: "An unexpected error occurred. Please retry or contact support.",
  ar: "حدث خطأ غير متوقع. يرجى المحاولة مجدداً أو التواصل مع الدعم.",
};

function safeErrorMessage(action: keyof typeof USER_ERROR_MESSAGES, lang: "en" | "ar" = "en"): string {
  const msgs = USER_ERROR_MESSAGES[action] ?? FALLBACK_ERROR;
  return msgs[lang];
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function relativeTime(iso: string): string {
  const delta = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (delta < 60) return `${delta}s ago`;
  if (delta < 3600) return `${Math.floor(delta / 60)}m ago`;
  if (delta < 86400) return `${Math.floor(delta / 3600)}h ago`;
  return `${Math.floor(delta / 86400)}d ago`;
}

function truncate(s: string | null | undefined, n: number): string {
  if (!s) return "—";
  return s.length > n ? s.slice(0, n) + "…" : s;
}

function formatUSD(n: number | null | undefined): string {
  if (n == null) return "—";
  return `$${n.toLocaleString("en-US", { maximumFractionDigits: 0 })}`;
}

// ── Source Context Chip ──────────────────────────────────────────────────────

function SourceChip({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex items-center gap-1 font-mono text-[10px] bg-io-accent/10 text-io-accent border border-io-accent/20 px-2 py-0.5 rounded-full">
      <span className="font-semibold">{label}:</span>
      <span>{value.length > 16 ? value.slice(0, 16) + "…" : value}</span>
    </span>
  );
}

// ── Signal Picker ────────────────────────────────────────────────────────────

function SignalPicker({
  signals,
  selectedSignalId,
  onSelect,
  lang = "en",
}: {
  signals: WsSignalScoredData[];
  selectedSignalId: string | null;
  onSelect: (id: string | null) => void;
  lang?: Language;
}) {
  const isAr = lang === "ar";
  if (signals.length === 0) {
    return (
      <p className="text-[10px] text-io-secondary italic">
        {isAr
          ? "لا توجد إشارات حية. تظهر الإشارات عند اكتشاف النظام لأحداث."
          : "No live signals available. Signals appear when the system detects events."}
      </p>
    );
  }

  return (
    <div className="space-y-1 max-h-32 overflow-y-auto">
      {signals.slice(0, 10).map((sig) => (
        <button
          key={sig.signal_id}
          onClick={() =>
            onSelect(selectedSignalId === sig.signal_id ? null : sig.signal_id)
          }
          className={`w-full text-left px-2.5 py-1.5 rounded-lg border text-[10px] transition-all ${
            selectedSignalId === sig.signal_id
              ? "border-io-accent bg-io-accent/10 text-io-accent"
              : "border-io-border bg-io-surface text-io-secondary hover:border-io-accent/40"
          }`}
        >
          <div className="flex items-center justify-between">
            <span className="font-mono font-medium">{sig.signal_id.slice(0, 16)}</span>
            <span className="uppercase font-semibold">{sig.sector}</span>
          </div>
          <div className="flex items-center justify-between mt-0.5 text-io-secondary">
            <span>{sig.event_type}</span>
            <span>score: {sig.signal_score.toFixed(2)}</span>
          </div>
        </button>
      ))}
    </div>
  );
}

// ── Impact Preview ───────────────────────────────────────────────────────────

function ImpactPreview({
  scenarioTitle,
  totalLoss,
  systemStress,
  lang = "en",
}: {
  scenarioTitle: string;
  totalLoss: number;
  systemStress: number;
  lang?: Language;
}) {
  const isAr = lang === "ar";
  const stressColor =
    systemStress > 0.7 ? "text-red-600" : systemStress > 0.4 ? "text-orange-500" : "text-green-600";

  return (
    <div className="p-3 bg-io-bg border border-io-border rounded-lg">
      <p className="text-[10px] font-medium text-io-secondary uppercase tracking-wide mb-2">
        {isAr ? "معاينة الأثر" : "Impact Preview"}
      </p>
      <div className="grid grid-cols-3 gap-2 text-xs">
        <div>
          <p className="text-[10px] text-io-secondary">{isAr ? "السيناريو" : "Scenario"}</p>
          <p className="font-medium text-io-primary">{truncate(scenarioTitle, 24)}</p>
        </div>
        <div>
          <p className="text-[10px] text-io-secondary">{isAr ? "الخسارة المقدّرة" : "Est. Loss"}</p>
          <p className="font-bold text-io-danger tabular-nums">{formatUSD(totalLoss)}</p>
        </div>
        <div>
          <p className="text-[10px] text-io-secondary">{isAr ? "إجهاد النظام" : "System Stress"}</p>
          <p className={`font-bold tabular-nums ${stressColor}`}>
            {(systemStress * 100).toFixed(0)}%
          </p>
        </div>
      </div>
    </div>
  );
}

// ── Decision row ──────────────────────────────────────────────────────────────

function DecisionRow({
  decision,
  selected,
  onSelect,
  onExecute,
  onClose,
  executingId,
  closingId,
  lang = "en",
}: {
  decision: OperatorDecision;
  selected: boolean;
  onSelect: (id: string) => void;
  onExecute: (id: string) => void;
  onClose: (id: string) => void;
  executingId: string | null;
  closingId: string | null;
  lang?: Language;
}) {
  const isAr = lang === "ar";
  const canExecute =
    decision.decision_status === "CREATED" || decision.decision_status === "IN_REVIEW";
  const canClose =
    decision.decision_status === "EXECUTED" || decision.decision_status === "FAILED";
  const isExecuting = executingId === decision.decision_id;
  const isClosing = closingId === decision.decision_id;

  return (
    <div
      className={`p-4 rounded-xl border transition-all cursor-pointer ${
        selected
          ? "border-io-accent bg-io-accent/5 shadow-sm"
          : "border-io-border bg-io-surface hover:border-io-accent/40 hover:shadow-sm"
      }`}
      onClick={() => onSelect(decision.decision_id)}
    >
      {/* Header row */}
      <div className="flex items-start justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className={`text-base font-bold ${TYPE_COLORS[decision.decision_type]}`}>
            {TYPE_ICONS[decision.decision_type]}
          </span>
          <div className="min-w-0">
            <span className={`text-xs font-semibold ${TYPE_COLORS[decision.decision_type]}`}>
              {(isAr
                ? DECISION_TYPES.find((t) => t.value === decision.decision_type)?.label_ar
                : DECISION_TYPES.find((t) => t.value === decision.decision_type)?.label)
                ?? decision.decision_type.replace(/_/g, " ")}
            </span>
            {decision.confidence_score != null && (
              <span className="ml-2 text-[10px] text-io-secondary">
                {Math.round(decision.confidence_score * 100)}
                {isAr ? "٪ ثقة" : "% confidence"}
              </span>
            )}
          </div>
        </div>
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold border whitespace-nowrap ${STATUS_COLORS[decision.decision_status]}`}
        >
          {decision.decision_status}
        </span>
      </div>

      {/* Source linkage — display only, no manual IDs */}
      <div className="flex flex-wrap gap-x-2 gap-y-1 mb-2">
        {decision.source_signal_id && (
          <SourceChip label={isAr ? "إشارة" : "signal"} value={decision.source_signal_id} />
        )}
        {decision.source_seed_id && (
          <SourceChip label={isAr ? "بذرة" : "seed"} value={decision.source_seed_id} />
        )}
        {decision.source_run_id && (
          <SourceChip label={isAr ? "تشغيل" : "run"} value={decision.source_run_id} />
        )}
      </div>

      {/* Rationale */}
      {decision.rationale && (
        <p className="text-xs text-io-secondary mb-2 leading-relaxed">
          {truncate(decision.rationale, 120)}
        </p>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between gap-2">
        <span className="text-[10px] text-io-secondary">
          by {truncate(decision.created_by, 20)} · {relativeTime(decision.created_at)}
        </span>
        <div className="flex gap-1.5" onClick={(e) => e.stopPropagation()}>
          {canExecute && (
            <button
              onClick={() => onExecute(decision.decision_id)}
              disabled={isExecuting}
              className="px-2.5 py-1 text-[10px] font-semibold rounded-lg bg-io-accent text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExecuting ? "…" : (isAr ? "تنفيذ" : "Execute")}
            </button>
          )}
          {canClose && (
            <button
              onClick={() => onClose(decision.decision_id)}
              disabled={isClosing}
              className="px-2.5 py-1 text-[10px] font-semibold rounded-lg border border-io-border text-io-secondary hover:text-io-primary hover:border-io-accent transition-colors disabled:opacity-50"
            >
              {isClosing ? "…" : (isAr ? "إغلاق" : "Close")}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Decision detail ───────────────────────────────────────────────────────────

function DecisionDetail({ decision, lang = "en" }: { decision: OperatorDecision; lang?: Language }) {
  const isAr = lang === "ar";
  return (
    <div className="mt-4 p-4 bg-io-bg border border-io-border rounded-xl space-y-3 text-xs">
      <h4 className="text-sm font-semibold text-io-primary">
        {isAr ? "تفاصيل القرار" : "Decision Detail"}
      </h4>

      <div className="grid grid-cols-2 gap-2">
        <div>
          <span className="text-io-secondary">{isAr ? "النوع" : "Type"}</span>
          <p className="font-medium text-io-primary">
            {(isAr
              ? DECISION_TYPES.find((t) => t.value === decision.decision_type)?.label_ar
              : DECISION_TYPES.find((t) => t.value === decision.decision_type)?.label)
              ?? decision.decision_type.replace(/_/g, " ")}
          </p>
        </div>
        <div>
          <span className="text-io-secondary">{isAr ? "الحالة" : "Status"}</span>
          <p className="font-medium text-io-primary">
            {isAr
              ? ({ CREATED: "تم الإنشاء", IN_REVIEW: "قيد المراجعة", EXECUTED: "تم التنفيذ", FAILED: "فشل", CLOSED: "مغلق" } as Record<string, string>)[decision.decision_status] ?? decision.decision_status
              : decision.decision_status}
          </p>
        </div>
        <div>
          <span className="text-io-secondary">{isAr ? "النتيجة" : "Outcome"}</span>
          <p className="font-medium text-io-primary">{decision.outcome_status}</p>
        </div>
        {decision.confidence_score != null && (
          <div>
            <span className="text-io-secondary">{isAr ? "الثقة" : "Confidence"}</span>
            <p className="font-medium text-io-primary">
              {Math.round(decision.confidence_score * 100)}%
            </p>
          </div>
        )}
      </div>

      {decision.rationale && (
        <div>
          <span className="text-io-secondary">{isAr ? "المبرر" : "Rationale"}</span>
          <p className="text-io-primary mt-0.5 leading-relaxed">{decision.rationale}</p>
        </div>
      )}

      {Object.keys(decision.decision_payload).length > 0 && (
        <div>
          <span className="text-io-secondary block mb-1">{isAr ? "السياق" : "Context"}</span>
          <div className="space-y-1">
            {Object.entries(decision.decision_payload).map(([k, v]) => (
              <div key={k} className="flex items-center justify-between gap-2">
                <span className="text-[10px] text-io-secondary capitalize">{k.replace(/_/g, " ")}</span>
                <span className="text-[10px] font-medium text-io-primary truncate max-w-[140px]">
                  {String(v)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="text-[10px] text-io-secondary font-mono space-y-0.5 pt-1 border-t border-io-border">
        <p>created: {new Date(decision.created_at).toLocaleString()}</p>
        <p>updated: {new Date(decision.updated_at).toLocaleString()}</p>
        {decision.closed_at && (
          <p>closed: {new Date(decision.closed_at).toLocaleString()}</p>
        )}
      </div>
    </div>
  );
}

// ── Create form (v2 — context-driven, no manual IDs) ─────────────────────────

function CreateDecisionForm({ onClose, lang = "en" }: { onClose: () => void; lang?: Language }) {
  const isAr = lang === "ar";
  // ── Store context (auto-linked sources) ──
  const selectedScenarioId = useAppStore((s) => s.selectedScenarioId);
  const liveSignals = useAppStore((s) => s.liveSignals);
  const pendingSeeds = useAppStore((s) => s.pendingSeeds);

  // ── Active run context from unified pipeline (source of truth) ──
  const activeRunId    = useRunState((s) => s.unifiedResult?.run_id ?? null);
  const adaptedResult  = useRunState((s) => s.adaptedResult);

  // ── Local form state ──
  const [type, setType] = useState<DecisionType>("APPROVE_ACTION");
  const [selectedSignalId, setSelectedSignalId] = useState<string | null>(null);
  const [rationale, setRationale] = useState("");
  const [confidence, setConfidence] = useState(0.85);
  const [formError, setFormError] = useState<string | null>(null);

  const createDecision = useCreateDecision();

  // ── Derived sources (auto-linked from store context) ──
  // source_run_id: the actual run UUID from the most recent unified pipeline run
  const sourceRunId = activeRunId;

  // Find matching seed for selected scenario (legacy / HITL path)
  const matchingSeed = useMemo(() => {
    if (!selectedScenarioId) return null;
    return pendingSeeds.find(
      (s) => s.suggested_template_id === selectedScenarioId || s.seed_id.includes(selectedScenarioId.slice(0, 8))
    ) ?? null;
  }, [pendingSeeds, selectedScenarioId]);

  const sourceSeedId   = matchingSeed?.seed_id ?? null;
  const sourceSignalId = selectedSignalId ?? matchingSeed?.signal_id ?? null;

  const hasSource = !!(sourceSignalId || sourceSeedId || sourceRunId);

  const handleSubmit = () => {
    setFormError(null);

    if (!hasSource) {
      setFormError(isAr
        ? "لا يوجد سياق مرتبط. اختر سيناريو أو إشارة أولاً."
        : "No source context available. Select a scenario or signal first.");
      return;
    }

    if (!rationale.trim()) {
      setFormError(isAr
        ? "المبرر مطلوب لضمان التتبع التدقيقي."
        : "A rationale is required for audit traceability.");
      return;
    }

    createDecision.mutate(
      {
        decision_type: type,
        source_signal_id: sourceSignalId,
        source_seed_id: sourceSeedId,
        source_run_id: sourceRunId,
        rationale: rationale.trim(),
        confidence_score: confidence,
        decision_payload: {},
      },
      {
        onSuccess: () => {
          setFormError(null);
          onClose();
        },
        onError: () => {
          setFormError(safeErrorMessage("create", lang));
        },
      }
    );
  };

  // ── No context available: guide the user ──
  if (!activeRunId && !selectedScenarioId && liveSignals.length === 0) {
    return (
      <div className="p-4 bg-io-bg border border-io-border rounded-xl text-center">
        <div className="w-10 h-10 rounded-xl bg-io-accent/10 border border-io-accent/20 flex items-center justify-center mx-auto mb-3">
          <svg className="w-5 h-5 text-io-accent" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 18v-5.25m0 0a6.01 6.01 0 001.5-.189m-1.5.189a6.01 6.01 0 01-1.5-.189m3.75 7.478a12.06 12.06 0 01-4.5 0m3.75 2.354a15.052 15.052 0 01-4.5 0M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
        </div>
        <p className="text-xs font-semibold text-io-primary mb-1">
          {isAr ? "لا يوجد سياق تشغيل نشط" : "No active run context"}
        </p>
        <p className="text-[10px] text-io-secondary leading-relaxed max-w-xs mx-auto">
          {isAr
            ? "شغّل تحليل سيناريو من لوحة المعلومات أولاً. يتم ربط القرارات تلقائياً بالتشغيل النشط."
            : "Run a scenario analysis from the main dashboard first. Decisions are automatically linked to the active run."}
        </p>
        <button
          onClick={onClose}
          className="mt-3 px-3 py-1.5 text-xs font-medium rounded-lg border border-io-border text-io-secondary hover:text-io-primary transition-colors"
        >
          {isAr ? "إغلاق" : "Close"}
        </button>
      </div>
    );
  }

  return (
    <div className="p-4 bg-io-bg border border-io-border rounded-xl space-y-3">
      <h4 className="text-sm font-semibold text-io-primary">
        {isAr ? "قرار جديد" : "New Decision"}
      </h4>

      {/* Auto-linked source context */}
      <div>
        <p className="text-[10px] font-medium text-io-secondary uppercase tracking-wide mb-1.5">
          {isAr ? "السياق المرتبط" : "Linked Source Context"}
        </p>
        <div className="flex flex-wrap gap-1.5">
          {sourceSignalId && <SourceChip label={isAr ? "إشارة" : "signal"} value={sourceSignalId} />}
          {sourceSeedId && <SourceChip label={isAr ? "بذرة" : "seed"} value={sourceSeedId} />}
          {sourceRunId && <SourceChip label={isAr ? "تشغيل" : "scenario"} value={sourceRunId} />}
          {!hasSource && (
            <span className="text-[10px] text-io-danger italic">
              {isAr ? "لا مصدر مرتبط — اختر إشارة أدناه" : "No source linked — select a signal below"}
            </span>
          )}
        </div>
      </div>

      {/* Impact preview (when an active run result exists) */}
      {adaptedResult && (
        <ImpactPreview
          scenarioTitle={adaptedResult.scenario.label}
          totalLoss={adaptedResult.headline.total_loss_usd}
          systemStress={adaptedResult.banking?.aggregate_stress ?? 0}
          lang={lang}
        />
      )}

      {/* Decision Type */}
      <div>
        <label className="block text-[10px] font-medium text-io-secondary mb-1 uppercase tracking-wide">
          {isAr ? "نوع القرار" : "Decision Type"}
        </label>
        <select
          value={type}
          onChange={(e) => setType(e.target.value as DecisionType)}
          className="w-full text-xs border border-io-border rounded-lg px-2.5 py-1.5 bg-io-surface text-io-primary focus:border-io-accent focus:outline-none"
        >
          {DECISION_TYPES.map((t) => (
            <option key={t.value} value={t.value}>
              {isAr ? t.label_ar : t.label}
            </option>
          ))}
        </select>
        <p className="text-[10px] text-io-secondary mt-0.5">
          {isAr
            ? DECISION_TYPES.find((t) => t.value === type)?.description_ar
            : DECISION_TYPES.find((t) => t.value === type)?.description}
        </p>
      </div>

      {/* Signal picker (if live signals exist and no auto-link from seed) */}
      {liveSignals.length > 0 && !matchingSeed?.signal_id && (
        <div>
          <label className="block text-[10px] font-medium text-io-secondary mb-1 uppercase tracking-wide">
            {isAr ? "ربط بإشارة (اختياري)" : "Link to Signal (optional)"}
          </label>
          <SignalPicker
            signals={liveSignals}
            selectedSignalId={selectedSignalId}
            onSelect={setSelectedSignalId}
            lang={lang}
          />
        </div>
      )}

      {/* Rationale (required for audit) */}
      <div>
        <label className="block text-[10px] font-medium text-io-secondary mb-1 uppercase tracking-wide">
          {isAr ? "المبرر" : "Rationale"} <span className="text-io-danger">*</span>
        </label>
        <textarea
          rows={3}
          placeholder={isAr
            ? "اشرح سبب اتخاذ هذا القرار — مطلوب للتتبع التدقيقي…"
            : "Explain why this decision is being made — required for audit traceability…"}
          value={rationale}
          onChange={(e) => setRationale(e.target.value)}
          className="w-full text-xs border border-io-border rounded-lg px-2.5 py-1.5 bg-io-surface text-io-primary placeholder-io-secondary/50 focus:border-io-accent focus:outline-none resize-none"
        />
      </div>

      {/* Confidence slider */}
      <div>
        <label className="block text-[10px] font-medium text-io-secondary mb-1 uppercase tracking-wide">
          {isAr ? `مستوى الثقة — ${Math.round(confidence * 100)}٪` : `Confidence — ${Math.round(confidence * 100)}%`}
        </label>
        <input
          type="range"
          min="0"
          max="1"
          step="0.05"
          value={confidence}
          onChange={(e) => setConfidence(parseFloat(e.target.value))}
          className="w-full h-1.5 rounded-full appearance-none bg-io-border accent-io-accent"
        />
        <div className="flex justify-between text-[9px] text-io-secondary mt-0.5">
          <span>{isAr ? "منخفض" : "Low"}</span>
          <span>{isAr ? "عالٍ" : "High"}</span>
        </div>
      </div>

      {/* Error message — user-safe, never raw API */}
      {formError && (
        <div className="p-2.5 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-[10px] text-red-700 font-medium">{formError}</p>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 pt-1">
        <button
          onClick={handleSubmit}
          disabled={createDecision.isPending || !hasSource || !rationale.trim()}
          className="flex-1 py-1.5 text-xs font-semibold rounded-lg bg-io-accent text-white hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {createDecision.isPending ? (isAr ? "جارٍ الإنشاء…" : "Creating…") : (isAr ? "إنشاء قرار" : "Create Decision")}
        </button>
        <button
          onClick={onClose}
          className="px-3 py-1.5 text-xs font-medium rounded-lg border border-io-border text-io-secondary hover:text-io-primary transition-colors"
        >
          {isAr ? "إلغاء" : "Cancel"}
        </button>
      </div>
    </div>
  );
}

// ── Main panel ────────────────────────────────────────────────────────────────

export function OperatorDecisionPanel({ lang = "en" }: { lang?: Language }) {
  const [statusFilter, setStatusFilter] = useState<string>("");
  const [typeFilter, setTypeFilter] = useState<string>("");
  const [showCreate, setShowCreate] = useState(false);
  const [executingId, setExecutingId] = useState<string | null>(null);
  const [closingId, setClosingId] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const isAr = lang === "ar";

  const selectedDecisionId = useAppStore((s) => s.selectedDecisionId);
  const setSelectedDecisionId = useAppStore((s) => s.setSelectedDecisionId);

  const { data, isLoading, isError } = useDecisions({
    status: statusFilter || undefined,
    decision_type: typeFilter || undefined,
    limit: 50,
  });

  const executeDecision = useExecuteDecision();
  const closeDecision = useCloseDecision();

  const decisions = data?.decisions ?? [];
  const selected = selectedDecisionId
    ? decisions.find((d) => d.decision_id === selectedDecisionId) ?? null
    : null;

  const handleExecute = async (id: string) => {
    setExecutingId(id);
    setActionError(null);
    try {
      await executeDecision.mutateAsync({ decisionId: id });
    } catch {
      setActionError(safeErrorMessage("execute", lang));
    } finally {
      setExecutingId(null);
    }
  };

  const handleClose = async (id: string) => {
    setClosingId(id);
    setActionError(null);
    try {
      await closeDecision.mutateAsync({ decisionId: id });
      if (selectedDecisionId === id) setSelectedDecisionId(null);
    } catch {
      setActionError(safeErrorMessage("close", lang));
    } finally {
      setClosingId(null);
    }
  };

  return (
    <div className="bg-io-surface border border-io-border rounded-2xl overflow-hidden shadow-sm">
      {/* Header */}
      <div className="px-4 py-3 border-b border-io-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 rounded-full bg-io-accent" />
          <h3 className="text-sm font-semibold text-io-primary">
            {isAr ? "قرارات المشغّل" : "Operator Decisions"}
          </h3>
          {data && (
            <span className="text-[10px] font-mono text-io-secondary px-1.5 py-0.5 bg-io-bg border border-io-border rounded-full">
              {data.count}
            </span>
          )}
        </div>
        <button
          onClick={() => setShowCreate((v) => !v)}
          className="px-2.5 py-1 text-[10px] font-semibold rounded-lg bg-io-accent text-white hover:bg-blue-700 transition-colors"
        >
          {showCreate ? (isAr ? "إلغاء" : "Cancel") : (isAr ? "+ جديد" : "+ New")}
        </button>
      </div>

      <div className="p-4 space-y-3">
        {/* Create form */}
        {showCreate && (
          <CreateDecisionForm onClose={() => setShowCreate(false)} lang={lang} />
        )}

        {/* Filters */}
        <div className="flex gap-2">
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="flex-1 text-[10px] border border-io-border rounded-lg px-2 py-1 bg-io-bg text-io-secondary focus:border-io-accent focus:outline-none"
          >
            <option value="">{isAr ? "جميع الحالات" : "All Statuses"}</option>
            {(
              [
                "CREATED",
                "IN_REVIEW",
                "EXECUTED",
                "FAILED",
                "CLOSED",
              ] as OperatorDecisionStatus[]
            ).map((s) => {
              const STATUS_LABELS_AR: Record<string, string> = {
                CREATED:   "تم الإنشاء",
                IN_REVIEW: "قيد المراجعة",
                EXECUTED:  "تم التنفيذ",
                FAILED:    "فشل",
                CLOSED:    "مغلق",
              };
              return (
                <option key={s} value={s}>
                  {isAr ? (STATUS_LABELS_AR[s] ?? s) : s}
                </option>
              );
            })}
          </select>
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="flex-1 text-[10px] border border-io-border rounded-lg px-2 py-1 bg-io-bg text-io-secondary focus:border-io-accent focus:outline-none"
          >
            <option value="">{isAr ? "جميع الأنواع" : "All Types"}</option>
            {DECISION_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {isAr ? t.label_ar : t.label}
              </option>
            ))}
          </select>
        </div>

        {/* Action-level error banner — user-safe */}
        {actionError && (
          <div className="p-2.5 bg-red-50 border border-red-200 rounded-lg flex items-center justify-between">
            <p className="text-[10px] text-red-700 font-medium">{actionError}</p>
            <button
              onClick={() => setActionError(null)}
              className="text-[10px] text-red-500 hover:text-red-700 font-medium ml-2"
            >
              {isAr ? "إغلاق" : "Dismiss"}
            </button>
          </div>
        )}

        {/* Loading state */}
        {isLoading && (
          <div className="py-6 text-center">
            <div className="w-5 h-5 border-2 border-io-accent border-t-transparent rounded-full animate-spin mx-auto mb-2" />
            <p className="text-xs text-io-secondary">{isAr ? "جارٍ تحميل القرارات…" : "Loading decisions…"}</p>
          </div>
        )}

        {/* Error state — user-safe, no raw API message */}
        {isError && (
          <div className="py-4 text-center">
            <div className="w-8 h-8 rounded-xl bg-red-50 border border-red-200 flex items-center justify-center mx-auto mb-2">
              <svg className="w-4 h-4 text-red-600" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
              </svg>
            </div>
            <p className="text-xs text-io-danger font-medium">
              {safeErrorMessage("load", lang)}
            </p>
          </div>
        )}

        {/* Empty state */}
        {!isLoading && !isError && decisions.length === 0 && (
          <div className="py-8 text-center">
            <div className="w-10 h-10 rounded-xl bg-io-bg border border-io-border flex items-center justify-center mx-auto mb-3">
              <svg className="w-5 h-5 text-io-secondary" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z" />
              </svg>
            </div>
            <p className="text-xs font-semibold text-io-primary mb-1">
              {isAr ? "لا توجد قرارات مسجّلة" : "No decisions recorded"}
            </p>
            <p className="text-[10px] text-io-secondary leading-relaxed max-w-xs mx-auto">
              {isAr
                ? "شغّل تحليل سيناريو، ثم أنشئ قراراً لتسجيل استجابتك. يتم ربط القرارات تلقائياً بالتشغيل النشط."
                : "Run a scenario analysis, then create a decision to record your response. Decisions are automatically linked to the active run."}
            </p>
          </div>
        )}

        {/* Decision list */}
        <div className="space-y-2 max-h-[520px] overflow-y-auto pr-0.5">
          {decisions.map((decision) => (
            <div key={decision.decision_id}>
              <DecisionRow
                decision={decision}
                selected={selectedDecisionId === decision.decision_id}
                onSelect={(id) =>
                  setSelectedDecisionId(
                    selectedDecisionId === id ? null : id
                  )
                }
                onExecute={handleExecute}
                onClose={handleClose}
                executingId={executingId}
                closingId={closingId}
                lang={lang}
              />
              {selectedDecisionId === decision.decision_id && selected && (
                <DecisionDetail decision={selected} lang={lang} />
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
