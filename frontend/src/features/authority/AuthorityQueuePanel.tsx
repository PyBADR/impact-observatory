"use client";

/**
 * Impact Observatory | مرصد الأثر — Authority Queue Panel
 *
 * The DECISION AUTHORITY queue for the Control Tower.
 * Displays pending approvals, active reviews, execution queue, and completed decisions
 * in a tabbed interface with per-persona visibility rules.
 *
 * Data flow:
 *   useAuthorityStore.getQueueSummary() → header badges
 *   useAuthorityStore.getQueueForPersona() → queue items
 *   PERSONA_AUTHORITY_CAPABILITIES → visible queues / allowed actions
 *
 * This component does NOT duplicate OperatorDecision data.
 * It renders the authority envelope only — the governance wrapper.
 */

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { useAuthorityStore } from "@/store/authority-store";
import { useAppStore } from "@/store/app-store";
import {
  PERSONA_AUTHORITY_CAPABILITIES,
  AUTHORITY_PERMISSIONS,
  type AuthorityStatus,
  type AuthorityAction,
  type AuthorityActor,
  type AuthorityQueueItem,
  type DecisionAuthority,
} from "@/types/authority";
import type { Language } from "@/types/observatory";
import { useRunState } from "@/lib/run-state";
import { emitAudit } from "@/lib/audit";

// ─── Module-level stable selectors (Zustand v5 + React 19 safe) ─────────────
// Inline arrow selectors `(s) => s.field` create a NEW function reference on
// every render.  Zustand v5 wraps them in useCallback([api, selector]).
// Since selector changes reference, useCallback recreates getSnapshot every
// render.  React 19 calls pushStoreConsistencyCheck for each
// hook.getSnapshot !== getSnapshot mismatch.  With 17+ useAuthorityStore hooks
// in one component, that is 17+ consistency-check entries per render.
// When loadAll() mutates the store during passive effects, those checks detect
// tearing and schedule re-renders — compounding into React error #185.
// Fix: module-level constants are defined once; Object.is(prev, next) is always
// true for these references → no getSnapshot churn → no re-render loop.
type AS = ReturnType<typeof useAuthorityStore.getState>;

const selectAuthorities            = (s: AS) => s.authorities;
const selectMetrics                = (s: AS) => s.metrics;
const selectLoadAll                = (s: AS) => s.loadAll;
const selectLoading                = (s: AS) => s.loading;
const selectStoreError             = (s: AS) => s.error;
const selectCanPerform             = (s: AS) => s.canPerform;
const selectSubmitForReview        = (s: AS) => s.submitForReview;
const selectApprove                = (s: AS) => s.approve;
const selectReject                 = (s: AS) => s.reject;
const selectReturnForRevision      = (s: AS) => s.returnForRevision;
const selectEscalate               = (s: AS) => s.escalate;
const selectQueueExecution         = (s: AS) => s.queueExecution;
const selectMarkExecuted           = (s: AS) => s.markExecuted;
const selectReportExecutionFailure = (s: AS) => s.reportExecutionFailure;
const selectRevoke                 = (s: AS) => s.revoke;
const selectWithdraw               = (s: AS) => s.withdraw;
const selectOverride               = (s: AS) => s.override;
const selectAnnotate               = (s: AS) => s.annotate;

type AppS_AQP = ReturnType<typeof useAppStore.getState>;
type RS_AQP   = ReturnType<typeof useRunState.getState>;
const selectPersona_AQP       = (s: AppS_AQP) => s.persona;
const selectAdaptedResult_AQP = (s: RS_AQP)   => s.adaptedResult;
const selectActiveRunId_AQP   = (s: RS_AQP)   => s.unifiedResult?.run_id ?? null;

// ─── Safe helpers ─────────────────────────────────────────────────────────

/**
 * Safe date → sort timestamp.
 * Returns 0 for null / undefined / invalid ISO strings so sort is always
 * deterministic and the comparator never returns NaN.
 */
function safeTime(value: unknown): number {
  const t =
    typeof value === "string" || value instanceof Date
      ? new Date(value as string).getTime()
      : 0;
  return Number.isFinite(t) ? t : 0;
}

// ─── Status Badge ─────────────────────────────────────────────────────────

const STATUS_STYLES: Record<AuthorityStatus, string> = {
  PROPOSED:          "bg-blue-100 text-blue-700 border-blue-200",
  UNDER_REVIEW:      "bg-amber-100 text-amber-700 border-amber-200",
  APPROVED:          "bg-emerald-100 text-emerald-700 border-emerald-200",
  REJECTED:          "bg-red-100 text-red-700 border-red-200",
  RETURNED:          "bg-orange-100 text-orange-700 border-orange-200",
  ESCALATED:         "bg-purple-100 text-purple-700 border-purple-200",
  EXECUTION_PENDING: "bg-cyan-100 text-cyan-700 border-cyan-200",
  EXECUTED:          "bg-emerald-100 text-emerald-800 border-emerald-300",
  EXECUTION_FAILED:  "bg-red-100 text-red-800 border-red-300",
  REVOKED:           "bg-gray-200 text-gray-600 border-gray-300",
  WITHDRAWN:         "bg-gray-100 text-gray-500 border-gray-200",
};

const STATUS_LABELS: Record<AuthorityStatus, { en: string; ar: string }> = {
  PROPOSED:          { en: "Proposed",          ar: "مقترح" },
  UNDER_REVIEW:      { en: "Under Review",      ar: "قيد المراجعة" },
  APPROVED:          { en: "Approved",          ar: "معتمد" },
  REJECTED:          { en: "Rejected",          ar: "مرفوض" },
  RETURNED:          { en: "Returned",          ar: "مُرتجع" },
  ESCALATED:         { en: "Escalated",         ar: "مُصعّد" },
  EXECUTION_PENDING: { en: "Pending Execution", ar: "بانتظار التنفيذ" },
  EXECUTED:          { en: "Executed",          ar: "مُنفّذ" },
  EXECUTION_FAILED:  { en: "Failed",            ar: "فشل" },
  REVOKED:           { en: "Revoked",           ar: "مُلغى" },
  WITHDRAWN:         { en: "Withdrawn",         ar: "مسحوب" },
};

function StatusBadge({ status, lang }: { status: AuthorityStatus; lang: Language }) {
  const isAr = lang === "ar";
  // C1 guard: backend may return an unrecognised status string — fall back to
  // neutral styles/labels rather than crashing on STATUS_LABELS[unknown].en
  const safeStyle  = STATUS_STYLES[status]  ?? "bg-gray-100 text-gray-600 border-gray-200";
  const safeLabels = STATUS_LABELS[status]  ?? { en: String(status ?? "UNKNOWN"), ar: String(status ?? "UNKNOWN") };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border ${safeStyle}`}
    >
      {isAr ? safeLabels.ar : safeLabels.en}
    </span>
  );
}

// ─── Priority Indicator ───────────────────────────────────────────────────

function PriorityDot({ priority }: { priority: 1 | 2 | 3 | 4 | 5 }) {
  const colors: Record<number, string> = {
    1: "bg-red-500",
    2: "bg-orange-500",
    3: "bg-yellow-500",
    4: "bg-blue-400",
    5: "bg-gray-400",
  };
  // C8 guard: out-of-range priority → neutral colour; never puts "undefined" in className
  const colorClass = colors[priority] ?? "bg-gray-300";
  return (
    <span
      className={`inline-block w-2 h-2 rounded-full ${colorClass}`}
      title={`Priority ${priority}`}
    />
  );
}

// ─── Queue Tab Buttons ────────────────────────────────────────────────────

type QueueTab = "pending" | "review" | "approved" | "executed" | "rejected" | "escalated" | "all";

const QUEUE_TAB_META: Record<QueueTab, { en: string; ar: string; statuses: AuthorityStatus[] }> = {
  pending:   { en: "Pending",   ar: "معلق",       statuses: ["PROPOSED"] },
  review:    { en: "In Review", ar: "قيد المراجعة", statuses: ["UNDER_REVIEW"] },
  approved:  { en: "Approved",  ar: "معتمد",       statuses: ["APPROVED", "EXECUTION_PENDING"] },
  executed:  { en: "Executed",  ar: "مُنفّذ",       statuses: ["EXECUTED"] },
  rejected:  { en: "Rejected",  ar: "مرفوض",       statuses: ["REJECTED", "RETURNED", "EXECUTION_FAILED"] },
  escalated: { en: "Escalated", ar: "مُصعّد",      statuses: ["ESCALATED"] },
  all:       { en: "All",       ar: "الكل",       statuses: [] },
};

function QueueTabs({
  activeTab,
  onTabChange,
  counts,
  visibleTabs,
  lang,
}: {
  activeTab: QueueTab;
  onTabChange: (tab: QueueTab) => void;
  counts: Record<QueueTab, number>;
  visibleTabs: QueueTab[];
  lang: Language;
}) {
  const isAr = lang === "ar";
  return (
    <div className="flex flex-wrap gap-1 border-b border-io-border pb-2">
      {visibleTabs.map((tab) => (
        <button
          key={tab}
          onClick={() => onTabChange(tab)}
          className={`
            inline-flex items-center gap-1.5 px-3 py-1.5 rounded-t text-xs font-medium
            transition-colors duration-150
            ${activeTab === tab
              ? "bg-io-accent text-white"
              : "bg-io-bg text-io-secondary hover:bg-io-border hover:text-io-primary"
            }
          `}
        >
          {isAr ? QUEUE_TAB_META[tab].ar : QUEUE_TAB_META[tab].en}
          {counts[tab] > 0 && (
            <span className={`
              inline-flex items-center justify-center min-w-[18px] h-[18px] px-1
              rounded-full text-[10px] font-bold
              ${activeTab === tab ? "bg-white/30 text-white" : "bg-io-border text-io-secondary"}
            `}>
              {counts[tab]}
            </span>
          )}
        </button>
      ))}
    </div>
  );
}

// ─── Action Button ────────────────────────────────────────────────────────

const ACTION_BUTTON_STYLES: Partial<Record<AuthorityAction, string>> = {
  APPROVE:              "bg-emerald-600 hover:bg-emerald-700 text-white",
  REJECT:               "bg-red-600 hover:bg-red-700 text-white",
  SUBMIT_FOR_REVIEW:    "bg-blue-600 hover:bg-blue-700 text-white",
  RETURN_FOR_REVISION:  "bg-orange-500 hover:bg-orange-600 text-white",
  ESCALATE:             "bg-purple-600 hover:bg-purple-700 text-white",
  QUEUE_EXECUTION:      "bg-cyan-600 hover:bg-cyan-700 text-white",
  EXECUTE:              "bg-emerald-700 hover:bg-emerald-800 text-white",
  REVOKE:               "bg-red-700 hover:bg-red-800 text-white",
  WITHDRAW:             "bg-gray-500 hover:bg-gray-600 text-white",
  OVERRIDE:             "bg-red-800 hover:bg-red-900 text-white",
};

const ACTION_LABELS: Partial<Record<AuthorityAction, { en: string; ar: string }>> = {
  APPROVE:              { en: "Approve",   ar: "اعتماد" },
  REJECT:               { en: "Reject",    ar: "رفض" },
  SUBMIT_FOR_REVIEW:    { en: "Submit",    ar: "إرسال" },
  RETURN_FOR_REVISION:  { en: "Return",    ar: "إرجاع" },
  ESCALATE:             { en: "Escalate",  ar: "تصعيد" },
  QUEUE_EXECUTION:      { en: "Queue",     ar: "وضع بالقائمة" },
  EXECUTE:              { en: "Execute",   ar: "تنفيذ" },
  REVOKE:               { en: "Revoke",    ar: "إلغاء" },
  WITHDRAW:             { en: "Withdraw",  ar: "سحب" },
  OVERRIDE:             { en: "Override",  ar: "تجاوز" },
};

function AuthorityActionButton({
  action,
  lang,
  onClick,
  disabled = false,
}: {
  action: AuthorityAction;
  lang: Language;
  onClick: () => void;
  disabled?: boolean;
}) {
  const isAr = lang === "ar";
  const label = ACTION_LABELS[action];
  if (!label) return null;

  return (
    <button
      onClick={onClick}
      disabled={disabled}
      className={`
        inline-flex items-center px-2 py-1 rounded text-[10px] font-semibold
        transition-colors duration-150 disabled:opacity-40 disabled:cursor-not-allowed
        ${ACTION_BUTTON_STYLES[action] ?? "bg-gray-200 text-gray-700"}
      `}
    >
      {isAr ? label.ar : label.en}
    </button>
  );
}

// ─── Queue Item Row ───────────────────────────────────────────────────────

function QueueItemRow({
  item,
  lang,
  allowedActions,
  actorRole,
  onAction,
}: {
  item: AuthorityQueueItem;
  lang: Language;
  allowedActions: AuthorityAction[];
  actorRole: AuthorityActor;
  onAction: (authorityId: string, action: AuthorityAction) => void;
}) {
  const isAr = lang === "ar";
  // C4 guard: canPerform may be undefined at store initialisation
  const canPerform = useAuthorityStore(selectCanPerform);

  const availableActions = useMemo(() => {
    // C5 guard: allowedActions must be an array; C4 guard: canPerform must be callable
    if (!Array.isArray(allowedActions)) return [];
    if (typeof canPerform !== "function") return [];
    return allowedActions.filter((action) => {
      try { return canPerform(item.authority_id, action, actorRole); }
      catch { return false; }
    });
  }, [allowedActions, canPerform, item.authority_id, actorRole]);

  const timeAgo = useMemo(() => {
    // C3 guard: invalid or missing proposed_at → safeTime returns 0 (epoch);
    // cap to sensible display rather than showing "56y ago" or "NaN d"
    const t = safeTime(item.proposed_at);
    if (t === 0) return "—";
    const diff = Date.now() - t;
    if (diff < 0) return "—";
    const mins = Math.floor(diff / 60000);
    if (mins < 60) return `${mins}m`;
    const hrs = Math.floor(mins / 60);
    if (hrs < 24) return `${hrs}h`;
    return `${Math.floor(hrs / 24)}d`;
  }, [item.proposed_at]);

  return (
    <div
      className={`
        flex items-start gap-3 px-4 py-3 border-b border-io-border last:border-b-0
        hover:bg-io-bg/50 transition-colors
        ${item.is_overdue ? "bg-red-50/50" : ""}
      `}
    >
      {/* Priority + Status */}
      <div className="flex flex-col items-center gap-1.5 pt-0.5">
        <PriorityDot priority={item.priority} />
        {item.is_overdue && (
          <span className="text-[9px] font-bold text-red-600 uppercase">
            {isAr ? "متأخر" : "LATE"}
          </span>
        )}
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1">
          <StatusBadge status={item.authority_status} lang={lang} />
          <span className="text-[10px] text-io-secondary font-mono truncate">
            {/* C6 guard: decision_id could be empty string or unexpectedly null */}
            {(item.decision_id ?? "").slice(0, 12) || "—"}…
          </span>
          {item.escalation_level > 0 && (
            <span className="text-[9px] bg-purple-100 text-purple-700 px-1.5 py-0.5 rounded font-bold">
              ESC-{item.escalation_level}
            </span>
          )}
          {item.revision_number > 1 && (
            <span className="text-[9px] bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded font-bold">
              Rev {item.revision_number}
            </span>
          )}
        </div>

        {/* Rationale preview */}
        {item.rationale_preview && (
          <p className="text-xs text-io-secondary line-clamp-1 mb-1">
            {item.rationale_preview}
          </p>
        )}

        {/* Meta row */}
        <div className="flex items-center gap-3 text-[10px] text-io-secondary">
          <span>
            {isAr ? "بواسطة" : "by"}{" "}
            <span className="font-medium text-io-primary">{item.proposed_by}</span>
            <span className="text-io-secondary/60 ml-1">({item.proposed_by_role})</span>
          </span>
          <span className="text-io-secondary/40">·</span>
          <span>{timeAgo} {isAr ? "مضت" : "ago"}</span>
          {item.last_authority_actor && (
            <>
              <span className="text-io-secondary/40">·</span>
              <span>
                {isAr ? "آخر:" : "Last:"}{" "}
                <span className="font-medium">{item.last_authority_actor}</span>
              </span>
            </>
          )}
        </div>
      </div>

      {/* Actions */}
      {availableActions.length > 0 && (
        <div className="flex flex-wrap gap-1 ml-2 shrink-0">
          {availableActions.map((action) => (
            <AuthorityActionButton
              key={action}
              action={action}
              lang={lang}
              onClick={() => onAction(item.authority_id, action)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// ─── Main: Authority Queue Panel ──────────────────────────────────────────

interface AuthorityQueuePanelProps {
  lang: Language;
}

export function AuthorityQueuePanel({ lang }: AuthorityQueuePanelProps) {
  const isAr = lang === "ar";
  const persona       = useAppStore(selectPersona_AQP);
  const activeRunId   = useRunState(selectActiveRunId_AQP);
  const adaptedResult = useRunState(selectAdaptedResult_AQP);

  // CRIT-01 FIX: select stable primitives from the store; derive objects in useMemo.
  // useShallow(s => s.getQueueForPersona(persona)) creates new object instances on every
  // call — useShallow compares elements by Object.is, so new objects trigger re-renders
  // indefinitely once the store is non-empty (infinite loop).
  const authorities  = useAuthorityStore(selectAuthorities);
  const storeMetrics = useAuthorityStore(selectMetrics);

  const queueSummary = useMemo(
    () =>
      storeMetrics ?? {
        proposed: 0,
        under_review: 0,
        approved_pending_execution: 0,
        executed: 0,
        rejected: 0,
        failed: 0,
        escalated: 0,
        overdue: 0,
        total_active: 0,
      },
    [storeMetrics],
  );

  // SW-01 FIX: filter by persona's visible_queues (authority items outside a persona's
  // visible_queues must not be shown even in the "all" tab — prevents data exposure).
  const personaVisibleQueues = useMemo(
    () => new Set(PERSONA_AUTHORITY_CAPABILITIES[persona]?.visible_queues ?? []),
    [persona],
  );

  const allItems = useMemo<AuthorityQueueItem[]>(() => {
    // C2 guard: authorities must be a Map with a forEach method.
    // In normal operation it always is (Zustand initialises it as new Map()), but
    // a store reset or unexpected API response could leave it null/undefined.
    if (!authorities || typeof (authorities as Map<string, DecisionAuthority>).forEach !== "function") {
      return [];
    }

    const items: AuthorityQueueItem[] = [];
    (authorities as Map<string, DecisionAuthority>).forEach((auth) => {
      // Guard: individual Map values could be null if a backend race produced a
      // partial upsert — skip rather than crash
      if (!auth || typeof auth !== "object") return;

      // Persona filter: skip items whose status is not visible to this persona
      if (!personaVisibleQueues.has(auth.authority_status)) return;

      // C7 guard: tags could be non-array from a malformed API response
      const firstTag = Array.isArray(auth.tags) && typeof auth.tags[0] === "string"
        ? auth.tags[0]
        : "UNKNOWN";

      items.push({
        authority_id:          auth.authority_id          ?? `anon_${Math.random().toString(36).slice(2)}`,
        decision_id:           auth.decision_id           ?? "",
        authority_status:      auth.authority_status,
        decision_type:         firstTag,
        proposed_by:           auth.proposed_by           ?? "system",
        proposed_by_role:      auth.proposed_by_role      ?? "ANALYST",
        proposed_at:           auth.proposed_at           ?? "",
        priority:              (typeof auth.priority === "number" && auth.priority >= 1 && auth.priority <= 5)
                                 ? auth.priority as 1|2|3|4|5
                                 : 3,
        is_overdue:            typeof auth.is_overdue === "boolean" ? auth.is_overdue : false,
        rationale_preview:     typeof auth.proposal_rationale === "string"
                                 ? auth.proposal_rationale.slice(0, 120)
                                 : null,
        source_run_id:         null,
        source_scenario_label: null,
        revision_number:       typeof auth.revision_number === "number" ? auth.revision_number : 1,
        escalation_level:      typeof auth.escalation_level === "number" ? auth.escalation_level : 0,
        last_authority_actor:  auth.authority_actor_id    ?? null,
        last_authority_action: null,
        last_authority_at:     auth.authority_decided_at  ?? null,
      });
    });

    // C9 guard: use safeTime (NaN-safe) instead of raw getTime()
    items.sort((a, b) => {
      if (a.is_overdue !== b.is_overdue) return a.is_overdue ? -1 : 1;
      if (a.priority   !== b.priority)   return a.priority - b.priority;
      return safeTime(b.proposed_at) - safeTime(a.proposed_at);
    });
    return items;
  }, [authorities, personaVisibleQueues]);

  // Use stable module-level selectors — see block comment above for why this
  // matters in Zustand v5 + React 19 (prevents React error #185).
  const loadAll = useAuthorityStore(selectLoadAll);
  const loading = useAuthorityStore(selectLoading);
  const error   = useAuthorityStore(selectStoreError);

  // Hydrate authority store on mount
  useEffect(() => {
    loadAll();
  }, [loadAll]);

  // Map persona → AuthorityActor for action dispatch
  const actorRoleMap: Record<string, AuthorityActor> = {
    executive: "EXECUTIVE",
    analyst: "ANALYST",
    regulator: "REGULATOR",
  };
  const actorRole = actorRoleMap[persona] ?? "OPERATOR";

  // Get persona capabilities
  const capabilities = PERSONA_AUTHORITY_CAPABILITIES[persona];
  const allowedActions = capabilities?.allowed_actions ?? [];

  // Determine visible tabs based on persona's visible_queues
  const visibleQueues = capabilities?.visible_queues ?? [];
  const visibleTabs = useMemo(() => {
    const tabs: QueueTab[] = [];
    const allTabs: QueueTab[] = ["pending", "review", "approved", "executed", "rejected", "escalated"];
    for (const tab of allTabs) {
      const tabStatuses = QUEUE_TAB_META[tab].statuses;
      if (tabStatuses.some((s) => visibleQueues.includes(s))) {
        tabs.push(tab);
      }
    }
    tabs.push("all");
    return tabs;
  }, [visibleQueues]);

  const [activeTab, setActiveTab] = useState<QueueTab>(visibleTabs[0] ?? "all");

  // Filter items by tab
  const filteredItems = useMemo(() => {
    if (activeTab === "all") return allItems;
    const statuses = QUEUE_TAB_META[activeTab].statuses;
    return allItems.filter((item) => statuses.includes(item.authority_status));
  }, [activeTab, allItems]);

  // Count per tab
  const tabCounts = useMemo(() => {
    const counts: Record<QueueTab, number> = {
      pending: 0, review: 0, approved: 0, executed: 0, rejected: 0, escalated: 0, all: allItems.length,
    };
    for (const item of allItems) {
      for (const [tab, meta] of Object.entries(QUEUE_TAB_META)) {
        if (meta.statuses.includes(item.authority_status)) {
          counts[tab as QueueTab]++;
        }
      }
    }
    return counts;
  }, [allItems]);

  // Extract action dispatch methods via stable module-level selectors.
  // All store action functions are defined once at store creation time, so
  // Object.is(prev, next) === true on every render → no getSnapshot churn.
  const _submitForReview        = useAuthorityStore(selectSubmitForReview);
  const _approve                = useAuthorityStore(selectApprove);
  const _reject                 = useAuthorityStore(selectReject);
  const _returnForRevision      = useAuthorityStore(selectReturnForRevision);
  const _escalate               = useAuthorityStore(selectEscalate);
  const _queueExecution         = useAuthorityStore(selectQueueExecution);
  const _markExecuted           = useAuthorityStore(selectMarkExecuted);
  const _reportExecutionFailure = useAuthorityStore(selectReportExecutionFailure);
  const _revoke                 = useAuthorityStore(selectRevoke);
  const _withdraw               = useAuthorityStore(selectWithdraw);
  const _override               = useAuthorityStore(selectOverride);
  const _annotate               = useAuthorityStore(selectAnnotate);

  // Group into a stable object — all deps are stable function references, so
  // this useMemo runs once on mount and never re-runs.
  const storeActions = useMemo(
    () => ({
      submitForReview:        _submitForReview,
      approve:                _approve,
      reject:                 _reject,
      returnForRevision:      _returnForRevision,
      escalate:               _escalate,
      queueExecution:         _queueExecution,
      markExecuted:           _markExecuted,
      reportExecutionFailure: _reportExecutionFailure,
      revoke:                 _revoke,
      withdraw:               _withdraw,
      override:               _override,
      annotate:               _annotate,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [_submitForReview, _approve, _reject, _returnForRevision, _escalate,
     _queueExecution, _markExecuted, _reportExecutionFailure, _revoke,
     _withdraw, _override, _annotate]
  );
  const [actionError, setActionError] = useState<string | null>(null);

  // Dispatch authority action to backend, clear error on success
  const handleAction = useCallback(
    async (authorityId: string, action: AuthorityAction) => {
      setActionError(null);
      try {
        switch (action) {
          case "SUBMIT_FOR_REVIEW":
            await storeActions.submitForReview({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole });
            break;
          case "APPROVE":
            await storeActions.approve({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole, rationale: "Approved via console" });
            break;
          case "REJECT":
            await storeActions.reject({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole, rationale: "Rejected via console" });
            break;
          case "RETURN_FOR_REVISION":
            await storeActions.returnForRevision({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole, rationale: "Returned for revision" });
            break;
          case "ESCALATE":
            await storeActions.escalate({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole, target_role: "ADMIN" });
            break;
          case "QUEUE_EXECUTION":
            await storeActions.queueExecution({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole });
            break;
          case "EXECUTE":
            await storeActions.markExecuted({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole, execution_result: "Executed via console" });
            break;
          case "REPORT_EXECUTION_FAILURE":
            await storeActions.reportExecutionFailure({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole, failure_reason: "Execution failed" });
            break;
          case "REVOKE":
            await storeActions.revoke({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole, rationale: "Revoked via console" });
            break;
          case "WITHDRAW":
            await storeActions.withdraw({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole });
            break;
          case "OVERRIDE":
            await storeActions.override({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole, override_to: "APPROVED", rationale: "Admin override" });
            break;
          case "ANNOTATE":
            await storeActions.annotate({ authority_id: authorityId, actor_id: actorRole, actor_role: actorRole, notes: "Annotation via console" });
            break;
          default:
            console.warn(`[DAL] Unhandled action: ${action}`);
        }
        // Emit lifecycle_transition after every successful authority action
        emitAudit({
          event_type:  "lifecycle_transition",
          entity_id:   authorityId,
          run_id:      activeRunId,
          scenario_id: adaptedResult?.scenario?.template_id ?? null,
          actor:       actorRole,
          details: {
            action:      action,
            entity_kind: "authority",
          },
          lineage_ref: null,
        });
      } catch (err) {
        const msg = err instanceof Error ? err.message : String(err);
        setActionError(msg);
      }
    },
    [actorRole, storeActions, activeRunId, adaptedResult]
  );

  return (
    <section className="bg-io-surface border border-io-border rounded-xl shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-5 py-4 border-b border-io-border bg-gradient-to-r from-amber-50/50 to-transparent">
        <div className="flex items-start justify-between gap-4">
          <div>
            <h2 className="text-sm font-bold text-io-primary flex items-center gap-2">
              <span className="text-base">⚖️</span>
              {isAr
                ? capabilities?.surface_label_ar ?? "قائمة الصلاحيات"
                : capabilities?.surface_label ?? "Authority Queue"}
            </h2>
            <p className="text-[10px] text-io-secondary mt-0.5">
              {isAr
                ? "دورة حياة الصلاحيات — من الاقتراح إلى التنفيذ"
                : "Authority lifecycle — proposal to execution"}
            </p>
          </div>

          {/* Summary badges */}
          <div className="flex items-center gap-2 flex-wrap justify-end">
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-blue-50 text-blue-700 border border-blue-200">
              {queueSummary.total_active} {isAr ? "نشط" : "active"}
            </span>
            {queueSummary.overdue > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-red-50 text-red-700 border border-red-200 animate-pulse">
                {queueSummary.overdue} {isAr ? "متأخر" : "overdue"}
              </span>
            )}
            {queueSummary.escalated > 0 && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-purple-50 text-purple-700 border border-purple-200">
                {queueSummary.escalated} {isAr ? "مُصعّد" : "escalated"}
              </span>
            )}
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="px-5 pt-3">
        <QueueTabs
          activeTab={activeTab}
          onTabChange={setActiveTab}
          counts={tabCounts}
          visibleTabs={visibleTabs}
          lang={lang}
        />
      </div>

      {/* Error banner */}
      {(error || actionError) && (
        <div className="mx-5 mt-2 px-3 py-2 bg-red-50 border border-red-200 rounded text-xs text-red-700">
          {isAr ? "خطأ:" : "Error:"} {error ?? actionError}
        </div>
      )}

      {/* Loading indicator */}
      {loading && (
        <div className="px-5 py-2 text-[10px] text-io-secondary animate-pulse">
          {isAr ? "جارٍ التحميل…" : "Loading…"}
        </div>
      )}

      {/* Queue Items */}
      <div className="max-h-[400px] overflow-y-auto">
        {filteredItems.length === 0 ? (
          <div className="px-5 py-8 text-center">
            <p className="text-sm text-io-secondary">
              {isAr ? "لا توجد قرارات في هذه القائمة" : "No decisions in this queue"}
            </p>
          </div>
        ) : (
          filteredItems.map((item) => (
            <QueueItemRow
              key={item.authority_id}
              item={item}
              lang={lang}
              allowedActions={allowedActions}
              actorRole={actorRole}
              onAction={handleAction}
            />
          ))
        )}
      </div>

      {/* Footer stats */}
      <div className="px-5 py-2.5 border-t border-io-border bg-io-bg/50">
        <div className="flex items-center justify-between text-[10px] text-io-secondary">
          <span>
            {filteredItems.length} {isAr ? "عنصر" : "item(s)"}
            {activeTab !== "all" && ` · ${allItems.length} ${isAr ? "إجمالي" : "total"}`}
          </span>
          <span className="font-mono text-io-secondary/60">
            {isAr ? "قائمة:" : "Queue:"} {capabilities?.surface_label ?? persona}
          </span>
        </div>
      </div>
    </section>
  );
}
