"use client";

/**
 * Impact Observatory | مرصد الأثر — Authority Audit Timeline
 *
 * Renders the hash-chained, immutable audit trail for a single DecisionAuthority.
 * Each event shows: actor, action, state transition, timestamp, notes, hash chain.
 *
 * Used by:
 *   - Regulator: full audit view with hash verification
 *   - Executive: summary view (latest 5 events)
 *   - Analyst: read-only trail for own proposals
 *
 * Hash chain integrity: visually indicates chain continuity.
 * Each event links to its predecessor via previous_event_hash.
 */

import React, { useEffect, useMemo, useState } from "react";
import { useAuthorityStore } from "@/store/authority-store";
import type { AuthorityEvent, AuthorityAction, AuthorityActor } from "@/types/authority";
import type { Language } from "@/types/observatory";

// ─── Module-level stable selectors ───────────────────────────────────────────
type AS_AAT = ReturnType<typeof useAuthorityStore.getState>;
const selectEvents_AAT      = (s: AS_AAT) => s.events;
const selectGetAuthority_AAT = (s: AS_AAT) => s.getAuthority;
const selectLoadEvents_AAT  = (s: AS_AAT) => s.loadEvents;
const selectVerifyChain_AAT = (s: AS_AAT) => s.verifyChain;

// ─── Action Icons ─────────────────────────────────────────────────────────

const ACTION_ICONS: Record<AuthorityAction, string> = {
  PROPOSE:                  "📋",
  SUBMIT_FOR_REVIEW:        "📤",
  APPROVE:                  "✅",
  REJECT:                   "❌",
  RETURN_FOR_REVISION:      "↩️",
  ESCALATE:                 "⬆️",
  QUEUE_EXECUTION:          "📦",
  EXECUTE:                  "⚡",
  REPORT_EXECUTION_FAILURE: "💥",
  REVOKE:                   "🚫",
  WITHDRAW:                 "🔙",
  OVERRIDE:                 "🔓",
  ANNOTATE:                 "💬",
};

const ACTION_LABELS: Record<AuthorityAction, { en: string; ar: string }> = {
  PROPOSE:                  { en: "Proposed",          ar: "تم الاقتراح" },
  SUBMIT_FOR_REVIEW:        { en: "Submitted for Review", ar: "أُرسل للمراجعة" },
  APPROVE:                  { en: "Approved",          ar: "تمت الموافقة" },
  REJECT:                   { en: "Rejected",          ar: "تم الرفض" },
  RETURN_FOR_REVISION:      { en: "Returned",          ar: "تم الإرجاع" },
  ESCALATE:                 { en: "Escalated",         ar: "تم التصعيد" },
  QUEUE_EXECUTION:          { en: "Queued for Execution", ar: "وُضع بقائمة التنفيذ" },
  EXECUTE:                  { en: "Executed",          ar: "تم التنفيذ" },
  REPORT_EXECUTION_FAILURE: { en: "Execution Failed",  ar: "فشل التنفيذ" },
  REVOKE:                   { en: "Revoked",           ar: "تم الإلغاء" },
  WITHDRAW:                 { en: "Withdrawn",         ar: "تم السحب" },
  OVERRIDE:                 { en: "Override Applied",  ar: "تم التجاوز" },
  ANNOTATE:                 { en: "Note Added",        ar: "تمت إضافة ملاحظة" },
};

const ROLE_LABELS: Record<AuthorityActor, { en: string; ar: string }> = {
  SYSTEM:    { en: "System",     ar: "النظام" },
  ANALYST:   { en: "Analyst",    ar: "محلل" },
  OPERATOR:  { en: "Operator",   ar: "مشغّل" },
  EXECUTIVE: { en: "Executive",  ar: "تنفيذي" },
  REGULATOR: { en: "Regulator",  ar: "مراقب" },
  ADMIN:     { en: "Admin",      ar: "مدير" },
};

// ─── Chain Integrity Badge ────────────────────────────────────────────────

function ChainBadge({
  event,
  previousEvent,
  lang,
}: {
  event: AuthorityEvent;
  previousEvent: AuthorityEvent | null;
  lang: Language;
}) {
  const isAr = lang === "ar";

  // Check chain integrity
  let chainValid = true;
  if (event.previous_event_hash !== null) {
    if (!previousEvent || previousEvent.event_hash !== event.previous_event_hash) {
      chainValid = false;
    }
  }

  if (!chainValid) {
    return (
      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-bold bg-red-100 text-red-700 border border-red-200">
        🔗❌ {isAr ? "سلسلة مكسورة" : "Chain Broken"}
      </span>
    );
  }

  return (
    <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[9px] font-mono text-io-secondary/60 bg-io-bg border border-io-border">
      🔗 {event.event_hash.slice(0, 16)}…
    </span>
  );
}

// ─── Single Event Row ─────────────────────────────────────────────────────

function EventRow({
  event,
  previousEvent,
  showHash,
  lang,
}: {
  event: AuthorityEvent;
  previousEvent: AuthorityEvent | null;
  showHash: boolean;
  lang: Language;
}) {
  const isAr = lang === "ar";
  const actionLabel = ACTION_LABELS[event.action];
  const roleLabel = ROLE_LABELS[event.actor_role];
  const icon = ACTION_ICONS[event.action];

  const formattedTime = useMemo(() => {
    const d = new Date(event.timestamp);
    return d.toLocaleString(isAr ? "ar-SA" : "en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  }, [event.timestamp, isAr]);

  return (
    <div className="flex gap-3 group">
      {/* Timeline spine */}
      <div className="flex flex-col items-center">
        <span className="text-sm leading-none">{icon}</span>
        <div className="w-px flex-1 bg-io-border group-last:bg-transparent mt-1" />
      </div>

      {/* Content */}
      <div className="flex-1 pb-4">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-xs font-semibold text-io-primary">
            {isAr ? actionLabel.ar : actionLabel.en}
          </span>
          {event.from_status && event.from_status !== event.to_status && (
            <span className="text-[10px] text-io-secondary font-mono">
              {event.from_status} → {event.to_status}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2 mt-0.5 text-[10px] text-io-secondary">
          <span>
            <span className="font-medium text-io-primary">{event.actor_id}</span>
            <span className="ml-1 text-io-secondary/60">
              ({isAr ? roleLabel.ar : roleLabel.en})
            </span>
          </span>
          <span className="text-io-secondary/40">·</span>
          <span className="font-mono">{formattedTime}</span>
        </div>

        {event.notes && (
          <p className="text-[11px] text-io-secondary mt-1 pl-0 border-l-2 border-io-border pl-2 italic">
            {event.notes}
          </p>
        )}

        {showHash && <ChainBadge event={event} previousEvent={previousEvent} lang={lang} />}
      </div>
    </div>
  );
}

// ─── Main: Authority Audit Timeline ───────────────────────────────────────

interface AuthorityAuditTimelineProps {
  authorityId: string;
  lang: Language;
  /** Show all events or just the latest N? */
  maxEvents?: number;
  /** Show hash chain badges? (Regulator: true, others: false) */
  showHashChain?: boolean;
}

export function AuthorityAuditTimeline({
  authorityId,
  lang,
  maxEvents,
  showHashChain = false,
}: AuthorityAuditTimelineProps) {
  const isAr = lang === "ar";
  const eventsMap              = useAuthorityStore(selectEvents_AAT);
  const getAuthorityByIdDecisionId = useAuthorityStore(selectGetAuthority_AAT);
  const loadEvents             = useAuthorityStore(selectLoadEvents_AAT);
  const [expanded, setExpanded] = useState(false);
  const [chainValid, setChainValid] = useState<boolean | null>(null);
  const verifyChain            = useAuthorityStore(selectVerifyChain_AAT);
  const allEvents              = useMemo(
    () => eventsMap.get(authorityId) ?? [],
    [eventsMap, authorityId],
  );

  // Load events from backend on mount
  useEffect(() => {
    const auth = getAuthorityByIdDecisionId(authorityId);
    if (auth) {
      loadEvents(auth.decision_id).catch(console.warn);
      if (showHashChain) {
        verifyChain(auth.decision_id)
          .then((r) => setChainValid(r.valid))
          .catch(() => setChainValid(null));
      }
    }
  }, [authorityId, loadEvents, getAuthorityByIdDecisionId, verifyChain, showHashChain]);

  // Events are newest-first in the store; reverse for timeline display (oldest first)
  const eventsChronological = useMemo(() => [...allEvents].reverse(), [allEvents]);

  const displayEvents = useMemo(() => {
    if (!maxEvents || expanded) return eventsChronological;
    return eventsChronological.slice(-maxEvents);
  }, [eventsChronological, maxEvents, expanded]);

  const hasMore = maxEvents && !expanded && eventsChronological.length > maxEvents;

  if (displayEvents.length === 0) {
    return (
      <div className="text-center py-4 text-xs text-io-secondary">
        {isAr ? "لا توجد أحداث" : "No audit events"}
      </div>
    );
  }

  return (
    <div className="space-y-0">
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <h3 className="text-xs font-bold text-io-primary flex items-center gap-1.5">
          <span className="text-sm">📜</span>
          {isAr ? "سجل الأحداث" : "Authority Audit Trail"}
        </h3>
        <span className="text-[10px] text-io-secondary font-mono">
          {eventsChronological.length} {isAr ? "حدث" : "event(s)"}
        </span>
      </div>

      {/* Hash chain summary (regulator only) — backed by backend verify */}
      {showHashChain && (
        <div className="mb-3 px-3 py-2 bg-io-bg rounded border border-io-border">
          <div className="flex items-center gap-2 text-[10px]">
            <span className="font-bold text-io-primary">
              🔗 {isAr ? "سلامة السلسلة" : "Chain Integrity"}:
            </span>
            {chainValid === null ? (
              <span className="text-io-secondary animate-pulse">
                {isAr ? "جارٍ التحقق…" : "Verifying…"}
              </span>
            ) : chainValid ? (
              <span className="text-emerald-600 font-bold">
                ✓ {eventsChronological.length} {isAr ? "حدث مرتبط" : "events linked"}
              </span>
            ) : (
              <span className="text-red-600 font-bold">
                ✗ {isAr ? "سلسلة مكسورة" : "Chain broken"}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Events */}
      <div className="pl-1">
        {displayEvents.map((event, idx) => {
          const prevEvent = idx > 0 ? displayEvents[idx - 1] : null;
          return (
            <EventRow
              key={event.event_id}
              event={event}
              previousEvent={prevEvent}
              showHash={showHashChain}
              lang={lang}
            />
          );
        })}
      </div>

      {/* Show more */}
      {hasMore && (
        <button
          onClick={() => setExpanded(true)}
          className="w-full py-2 text-center text-[10px] font-medium text-io-accent hover:text-io-accent/80 transition-colors"
        >
          {isAr
            ? `عرض الكل (${eventsChronological.length} حدث)`
            : `Show all (${eventsChronological.length} events)`}
        </button>
      )}
    </div>
  );
}
