"use client";

/**
 * Monitoring — Governance and Accountability
 *
 * This page answers five questions only:
 *   1. Who owns execution
 *   2. What is overdue
 *   3. What escalates next
 *   4. When review happens
 *   5. What confirms control
 *
 * Hard rules:
 *   - No technical provenance (audit hash, model version, pipeline stages)
 *   - No dashboard metric grids
 *   - No ops-console or admin-panel feel
 *   - Governance reading flow: prose, not widgets
 */

import React from "react";

/* ── Sector → institutional escalation authority ── */
const SECTOR_ESCALATION: Record<string, { en: string; ar: string }> = {
  Energy: { en: "GCC Supreme Council", ar: "المجلس الأعلى لدول الخليج" },
  Banking: { en: "Ministry of Finance", ar: "وزارة المالية" },
  Insurance: { en: "Ministry of Finance", ar: "وزارة المالية" },
  Shipping: { en: "Cabinet Economic Council", ar: "المجلس الاقتصادي لمجلس الوزراء" },
  Government: { en: "Head of State Office", ar: "مكتب رئيس الدولة" },
  OilGas: { en: "Supreme Council / OPEC Coordination", ar: "المجلس الأعلى / تنسيق أوبك" },
  Fintech: { en: "Central Bank Governor", ar: "محافظ البنك المركزي" },
  RealEstate: { en: "Ministry of Finance", ar: "وزارة المالية" },
};

/* ── Sector → review cadence hours ── */
const SECTOR_REVIEW_HOURS: Record<string, number> = {
  Energy: 4,
  Banking: 6,
  Insurance: 12,
  Shipping: 8,
  Government: 4,
  OilGas: 4,
  Fintech: 8,
  RealEstate: 24,
};

interface RegulatoryAuditViewProps {
  locale: "en" | "ar";
  runId?: string;
  scenarioLabel?: string;
  scenarioLabelAr?: string;
  severity?: number;
  horizonHours?: number;
  trustInfo?: {
    warnings?: string[];
    confidence?: number;
  };
  decisionActions?: Array<{
    id: string;
    action: string;
    action_ar?: string;
    sector: string;
    owner: string;
    priority: number;
    confidence: number;
    status?: string;
  }>;
}

export const RegulatoryAuditView: React.FC<RegulatoryAuditViewProps> = ({
  locale = "en",
  scenarioLabel,
  scenarioLabelAr,
  severity,
  horizonHours,
  trustInfo,
  decisionActions = [],
}) => {
  const isAr = locale === "ar";
  const displayLabel = isAr ? (scenarioLabelAr || scenarioLabel) : scenarioLabel;

  /* ── Derive governance state ── */
  const overdueActions = decisionActions.filter(
    (d) => d.status === "Proposed" || !d.status,
  );
  const executed = decisionActions.filter(
    (d) => d.status === "Approved" || d.status === "Executed",
  );
  const hasWarnings = trustInfo?.warnings && trustInfo.warnings.length > 0;

  /* ── Escalation: highest-priority unexecuted directive ── */
  const unexecuted = decisionActions.filter(
    (d) => d.status !== "Approved" && d.status !== "Executed",
  );
  const nextEscalation = [...unexecuted].sort((a, b) => a.priority - b.priority)[0];

  /* ── Review cadence: shortest cycle among active sectors ── */
  const activeSectors = [...new Set(decisionActions.map((d) => d.sector))];
  const shortestCycleHours = activeSectors.length > 0
    ? Math.min(...activeSectors.map((s) => SECTOR_REVIEW_HOURS[s] ?? 12))
    : 12;

  /* ── Control assessment ── */
  const allExecuted = overdueActions.length === 0 && decisionActions.length > 0;
  const controlConfirmed = allExecuted && !hasWarnings;

  return (
    <div
      className="max-w-3xl mx-auto px-6 sm:px-8 py-10"
      dir={isAr ? "rtl" : "ltr"}
    >
      {/* ── Header ── */}
      <div className="mb-12">
        <h2 className="text-[1.375rem] sm:text-[1.625rem] font-bold text-[#1d1d1f] leading-tight tracking-tight mb-3">
          {isAr ? "المراقبة والحوكمة" : "Monitoring and Governance"}
        </h2>
        {displayLabel && (
          <p className="text-[0.875rem] text-[#6e6e73] leading-relaxed">
            {displayLabel}
            {severity != null && (
              <span className="text-[#0071e3] ml-2">· {Math.round(severity * 100)}% severity</span>
            )}
            {horizonHours != null && (
              <span className="ml-2">· {horizonHours}h horizon</span>
            )}
          </p>
        )}
      </div>

      {/* ── No data state ── */}
      {decisionActions.length === 0 && (
        <p className="text-[0.9375rem] text-[#6e6e73] leading-[1.8]">
          {isAr
            ? "لا توجد توجيهات نشطة — لا شيء للمراقبة."
            : "No active directives — nothing to monitor."}
        </p>
      )}

      {decisionActions.length > 0 && (
        <>
          {/* ═══════════════════════════════════════════════════════
              1. EXECUTION OWNERSHIP — who owns each directive
              ═══════════════════════════════════════════════════════ */}
          <section className="mb-12">
            <p className="text-[0.6875rem] text-[#8e8e93] uppercase tracking-[0.2em] font-semibold mb-2">
              {isAr ? "مسؤولية التنفيذ" : "Execution Ownership"}
            </p>
            <div className="h-px bg-[#e5e5e7] mb-6" />

            <div className="space-y-5">
              {decisionActions.map((action) => (
                <div key={action.id}>
                  <div className="flex gap-4 items-baseline">
                    <p className="text-[0.9375rem] text-[#515154] leading-snug flex-1">
                      {isAr && action.action_ar ? action.action_ar : action.action}
                    </p>
                    <p className="text-[0.8125rem] font-semibold text-[#1d1d1f] whitespace-nowrap flex-shrink-0">
                      {action.owner}
                    </p>
                  </div>
                  <p className="text-[0.75rem] text-[#6e6e73] mt-1">
                    {action.sector}
                    {action.status && (
                      <span className={`ml-2 ${
                        action.status === "Approved" || action.status === "Executed"
                          ? "text-[#4a7c59]"
                          : action.status === "Under Review"
                            ? "text-[#6e6e73]"
                            : "text-[#0071e3]"
                      }`}>
                        · {action.status === "Proposed" || !action.status
                          ? (isAr ? "في انتظار التنفيذ" : "Awaiting execution")
                          : action.status === "Approved" || action.status === "Executed"
                            ? (isAr ? "تم التنفيذ" : "Executed")
                            : (isAr ? "قيد المراجعة" : "Under review")}
                      </span>
                    )}
                  </p>
                </div>
              ))}
            </div>
          </section>

          {/* ═══════════════════════════════════════════════════════
              2. OVERDUE — what has not been executed
              ═══════════════════════════════════════════════════════ */}
          <section className="mb-12">
            <p className="text-[0.6875rem] text-[#8e8e93] uppercase tracking-[0.2em] font-semibold mb-2">
              {isAr ? "المتأخر" : "Overdue"}
            </p>
            <div className="h-px bg-[#e5e5e7] mb-6" />

            {overdueActions.length === 0 ? (
              <p className="text-[0.9375rem] text-[#515154] leading-[1.8]">
                {isAr
                  ? "لا توجد توجيهات متأخرة. جميع الإجراءات قيد التنفيذ أو مكتملة."
                  : "No overdue directives. All actions are in progress or complete."}
              </p>
            ) : (
              <>
                <p className="text-[0.9375rem] text-[#515154] leading-[1.8] mb-5">
                  {isAr
                    ? `${overdueActions.length} ${overdueActions.length === 1 ? "توجيه" : "توجيهات"} في انتظار التنفيذ. لم يبدأ أي مسؤول تنفيذ بعد.`
                    : `${overdueActions.length} ${overdueActions.length === 1 ? "directive" : "directives"} awaiting execution. No responsible owner has initiated action.`}
                </p>
                <div className="space-y-4">
                  {overdueActions.map((action) => (
                    <div key={action.id} className="border-l-2 border-[#d92f2f]/40 pl-5">
                      <p className="text-[0.9375rem] text-[#1d1d1f] leading-snug mb-1">
                        {isAr && action.action_ar ? action.action_ar : action.action}
                      </p>
                      <p className="text-[0.75rem] text-[#6e6e73]">
                        {action.owner}
                        <span className="mx-2 text-[#8e8e93]">·</span>
                        {action.sector}
                      </p>
                    </div>
                  ))}
                </div>
              </>
            )}
          </section>

          {/* ═══════════════════════════════════════════════════════
              3. ESCALATION — what escalates next and to whom
              ═══════════════════════════════════════════════════════ */}
          <section className="mb-12">
            <p className="text-[0.6875rem] text-[#8e8e93] uppercase tracking-[0.2em] font-semibold mb-2">
              {isAr ? "التصعيد القادم" : "Next Escalation"}
            </p>
            <div className="h-px bg-[#e5e5e7] mb-6" />

            {nextEscalation ? (
              <div>
                <p className="text-[0.9375rem] text-[#515154] leading-[1.8] mb-4">
                  {isAr
                    ? `التوجيه الأعلى أولوية غير المنفذ هو "${nextEscalation.action_ar || nextEscalation.action}"، المملوك لـ ${nextEscalation.owner}. إذا لم يتم تنفيذه خلال دورة المراجعة القادمة، يتم تصعيده إلى ${SECTOR_ESCALATION[nextEscalation.sector]?.ar ?? "قيادة القطاع"}.`
                    : `The highest-priority unexecuted directive is "${nextEscalation.action}", owned by ${nextEscalation.owner}. If not executed within the next review cycle, it escalates to ${SECTOR_ESCALATION[nextEscalation.sector]?.en ?? "sector leadership"}.`}
                </p>
                <p className="text-[0.8125rem] text-[#6e6e73] leading-relaxed">
                  {isAr ? "الأولوية" : "Priority"}: <span className="text-[#1d1d1f] font-semibold">P{nextEscalation.priority}</span>
                  <span className="mx-2 text-[#8e8e93]">·</span>
                  {isAr ? "سلطة التصعيد" : "Escalation authority"}: <span className="text-[#1d1d1f]">{isAr ? (SECTOR_ESCALATION[nextEscalation.sector]?.ar ?? "قيادة القطاع") : (SECTOR_ESCALATION[nextEscalation.sector]?.en ?? "Sector leadership")}</span>
                </p>
              </div>
            ) : (
              <p className="text-[0.9375rem] text-[#515154] leading-[1.8]">
                {isAr
                  ? "لا يوجد تصعيد معلق. جميع التوجيهات منفذة."
                  : "No pending escalation. All directives have been executed."}
              </p>
            )}
          </section>

          {/* ═══════════════════════════════════════════════════════
              4. REVIEW SCHEDULE — when reassessment happens
              ═══════════════════════════════════════════════════════ */}
          <section className="mb-12">
            <p className="text-[0.6875rem] text-[#8e8e93] uppercase tracking-[0.2em] font-semibold mb-2">
              {isAr ? "جدول المراجعة" : "Review Schedule"}
            </p>
            <div className="h-px bg-[#e5e5e7] mb-6" />

            <p className="text-[0.9375rem] text-[#515154] leading-[1.8] mb-5">
              {isAr
                ? `دورة المراجعة الحالية كل ${shortestCycleHours} ساعات، محددة بأقصر إيقاع قطاعي نشط. تتم مراجعة جميع التوجيهات المعلقة في كل دورة.`
                : `The current review cadence is every ${shortestCycleHours} hours, set by the shortest active sector cycle. All pending directives are reassessed at each interval.`}
            </p>

            {activeSectors.length > 1 && (
              <div className="space-y-2">
                {activeSectors.map((sector) => {
                  const hours = SECTOR_REVIEW_HOURS[sector] ?? 12;
                  return (
                    <p key={sector} className="text-[0.8125rem] text-[#6e6e73]">
                      {sector}
                      <span className="mx-2 text-[#8e8e93]">—</span>
                      <span className="text-[#515154]">
                        {isAr ? `كل ${hours} ساعات` : `every ${hours}h`}
                      </span>
                    </p>
                  );
                })}
              </div>
            )}
          </section>

          {/* ═══════════════════════════════════════════════════════
              5. CONTROL CONFIRMATION — what confirms control
              ═══════════════════════════════════════════════════════ */}
          <section className="mb-10">
            <p className="text-[0.6875rem] text-[#8e8e93] uppercase tracking-[0.2em] font-semibold mb-2">
              {isAr ? "تأكيد السيطرة" : "Control Confirmation"}
            </p>
            <div className="h-px bg-[#e5e5e7] mb-6" />

            {/* Warnings — governance-relevant only */}
            {hasWarnings && (
              <div className="border-l-2 border-[#0071e3]/40 pl-5 mb-6">
                <p className="text-[0.6875rem] text-[#6e6e73] uppercase tracking-widest font-medium mb-2">
                  {isAr ? "تنبيهات" : "Warnings"}
                </p>
                {trustInfo!.warnings!.map((warning, idx) => (
                  <p key={idx} className="text-[0.8125rem] text-[#0071e3] leading-relaxed mb-1">
                    {warning}
                  </p>
                ))}
              </div>
            )}

            {/* Control statement — the governance verdict */}
            <p className="text-[0.9375rem] text-[#515154] leading-[1.8] mb-4">
              {controlConfirmed
                ? isAr
                  ? `جميع التوجيهات الـ ${decisionActions.length} منفذة. لا توجد تنبيهات نشطة. السيطرة مؤكدة.`
                  : `All ${decisionActions.length} directives have been executed. No active warnings. Control is confirmed.`
                : overdueActions.length > 0
                  ? isAr
                    ? `${overdueActions.length} من ${decisionActions.length} ${overdueActions.length === 1 ? "توجيه" : "توجيهات"} في انتظار التنفيذ. السيطرة غير مؤكدة حتى تكتمل جميع الإجراءات المعلقة.`
                    : `${overdueActions.length} of ${decisionActions.length} ${overdueActions.length === 1 ? "directive" : "directives"} awaiting execution. Control is not confirmed until all pending actions are complete.`
                  : isAr
                    ? "التوجيهات قيد التنفيذ لكن توجد تنبيهات نشطة. مطلوب مراجعة قبل تأكيد السيطرة."
                    : "Directives are in progress but active warnings exist. Review is required before control can be confirmed."}
            </p>

            {/* Explicit criteria */}
            <p className="text-[0.8125rem] text-[#6e6e73] leading-[1.75]">
              {isAr
                ? "معايير التأكيد: تنفيذ جميع التوجيهات، عدم وجود تنبيهات نشطة، اكتمال دورة مراجعة واحدة على الأقل بعد آخر تنفيذ."
                : "Confirmation criteria: all directives executed, no active warnings, at least one review cycle completed after last execution."}
            </p>
          </section>
        </>
      )}

      {/* ── Footer ── */}
      <div className="mt-14 pt-5 border-t border-[#e5e5e7]">
        <p className="text-[0.625rem] text-[#8e8e93] tracking-wider">
          {isAr ? "صفحة الحوكمة والمراقبة" : "Governance and monitoring"}{displayLabel ? ` · ${displayLabel}` : ""}
        </p>
      </div>
    </div>
  );
};

export default RegulatoryAuditView;
