"use client";

import React, { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { ChevronDown, Copy, CheckCircle, AlertCircle, Clock, Zap } from "lucide-react";

interface RegulatoryAuditViewProps {
  locale: "en" | "ar";
  runId?: string;
  scenarioLabel?: string;
  scenarioLabelAr?: string;
  severity?: number;
  horizonHours?: number;
  trustInfo?: {
    auditHash?: string;
    modelVersion?: string;
    pipelineVersion?: string;
    dataSources?: string[];
    stagesCompleted?: string[];
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
  pipelineStages?: Array<{ name: string; duration_ms: number; status: string }>;
  regulatoryBreaches?: Array<{
    sector: string;
    metric: string;
    threshold: number;
    actual: number;
    severity: string;
    mandatory_actions: string[];
  }>;
}

const LABELS = {
  en: {
    title: "Governance & Oversight",
    runProvenance: "Run Provenance & Identity",
    decisionLifecycle: "Decision Lifecycle & Lineage",
    outcomeAudit: "Decision Outcome Record",
    decisionValue: "Decision Value Audit",
    institutionalMemory: "Institutional Memory",
    pipelineExecution: "Pipeline Execution Record",
    regulatoryBreaches: "Regulatory Breach Events",
    runId: "Run ID",
    scenario: "Scenario",
    severity: "Severity",
    horizon: "Horizon",
    timestamp: "Timestamp",
    pipelineVersion: "Pipeline Version",
    modelVersion: "Model Version",
    auditHash: "Audit Hash",
    dataSources: "Data Sources",
    warnings: "Warnings",
    confidence: "Confidence",
    decisionId: "Decision ID",
    action: "Action",
    sector: "Sector",
    owner: "Owner",
    priority: "Priority",
    status: "Status",
    proposed: "Proposed",
    underReview: "Under Review",
    approved: "Approved",
    executed: "Executed",
    stage: "Stage",
    duration: "Duration",
    metric: "Metric",
    threshold: "Threshold",
    actual: "Actual",
    mandatoryActions: "Mandatory Actions",
    noBreaches: "No regulatory breaches detected",
    noDecisions: "No decision actions available",
    noPipeline: "No pipeline stages available",
    copy: "Copy",
    copied: "Copied!",
    hours: "hours",
  },
  ar: {
    title: "الحوكمة والرقابة",
    runProvenance: "أصل التشغيل والهوية",
    decisionLifecycle: "دورة حياة القرار والنسب",
    outcomeAudit: "سجل نتائج القرارات",
    decisionValue: "تدقيق قيمة القرار",
    institutionalMemory: "الذاكرة المؤسسية",
    pipelineExecution: "سجل تنفيذ خط الأنابيب",
    regulatoryBreaches: "أحداث انتهاك اللوائح",
    runId: "معرّف التشغيل",
    scenario: "السيناريو",
    severity: "الخطورة",
    horizon: "الأفق",
    timestamp: "الطابع الزمني",
    pipelineVersion: "إصدار خط الأنابيب",
    modelVersion: "إصدار النموذج",
    auditHash: "تجزئة التدقيق",
    dataSources: "مصادر البيانات",
    warnings: "التحذيرات",
    confidence: "الثقة",
    decisionId: "معرّف القرار",
    action: "الإجراء",
    sector: "القطاع",
    owner: "المالك",
    priority: "الأولوية",
    status: "الحالة",
    proposed: "مقترح",
    underReview: "قيد المراجعة",
    approved: "موافق عليه",
    executed: "منفذ",
    stage: "المرحلة",
    duration: "المدة",
    metric: "المقياس",
    threshold: "الحد",
    actual: "الفعلي",
    mandatoryActions: "الإجراءات الإلزامية",
    noBreaches: "لم يتم كشف انتهاكات تنظيمية",
    noDecisions: "لا توجد إجراءات قرارات متاحة",
    noPipeline: "لا توجد مراحل خط أنابيب متاحة",
    copy: "نسخ",
    copied: "تم النسخ!",
    hours: "ساعات",
  },
};

const CollapsibleSection: React.FC<{
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
  defaultOpen?: boolean;
}> = ({ title, icon, children, defaultOpen = true }) => {
  const [isOpen, setIsOpen] = useState(defaultOpen);

  return (
    <div className="border border-slate-200 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-slate-50 hover:bg-slate-100 transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="text-slate-500">{icon}</div>
          <span className="text-sm font-semibold text-slate-700">{title}</span>
        </div>
        <ChevronDown
          size={18}
          className={`text-slate-500 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>
      {isOpen && (
        <div className="px-4 py-3 bg-white border-t border-slate-200">
          {children}
        </div>
      )}
    </div>
  );
};

const CopyableHash: React.FC<{ hash?: string; label: string }> = ({ hash, label }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (hash) {
      navigator.clipboard.writeText(hash);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (!hash) return null;

  return (
    <div className="flex items-center justify-between bg-slate-50 p-2 rounded border border-slate-200">
      <code className="text-xs text-slate-700 truncate">{hash}</code>
      <button
        onClick={handleCopy}
        className="ml-2 p-1 hover:bg-slate-100 rounded transition-colors"
        title={label}
      >
        {copied ? (
          <CheckCircle size={16} className="text-green-600" />
        ) : (
          <Copy size={16} className="text-slate-500 hover:text-slate-700" />
        )}
      </button>
    </div>
  );
};

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const severityMap: Record<string, string> = {
    critical: "bg-red-50 text-red-700 border-red-200",
    high: "bg-orange-50 text-orange-700 border-orange-200",
    medium: "bg-amber-50 text-amber-700 border-amber-200",
    low: "bg-yellow-50 text-yellow-700 border-yellow-200",
    nominal: "bg-green-50 text-green-700 border-green-200",
  };

  const classes = severityMap[severity.toLowerCase()] || severityMap.nominal;

  return (
    <span className={`inline-block px-2 py-1 text-xs rounded border ${classes}`}>
      {severity}
    </span>
  );
};

const StatusFlow: React.FC<{
  status?: string;
  locale: "en" | "ar";
}> = ({ status = "Proposed", locale }) => {
  const statuses = ["Proposed", "Under Review", "Approved", "Executed"];
  const statusesAr = ["مقترح", "قيد المراجعة", "موافق عليه", "منفذ"];
  const statusList = locale === "ar" ? statusesAr : statuses;
  const currentIndex = statusList.indexOf(status);

  return (
    <div className="flex items-center gap-2">
      {statusList.map((s, idx) => (
        <React.Fragment key={s}>
          <div
            className={`px-2 py-1 text-xs rounded transition-colors ${
              idx <= currentIndex
                ? "bg-blue-50 text-blue-700 border border-blue-200"
                : "bg-slate-50 text-slate-400 border border-slate-200"
            }`}
          >
            {s}
          </div>
          {idx < statusList.length - 1 && (
            <div
              className={`h-0.5 w-2 ${idx < currentIndex ? "bg-blue-300" : "bg-slate-200"}`}
            />
          )}
        </React.Fragment>
      ))}
    </div>
  );
};

export const RegulatoryAuditView: React.FC<RegulatoryAuditViewProps> = ({
  locale = "en",
  runId,
  scenarioLabel,
  scenarioLabelAr,
  severity,
  horizonHours,
  trustInfo,
  decisionActions = [],
  pipelineStages = [],
  regulatoryBreaches = [],
}) => {
  const labels = LABELS[locale];
  const isArabic = locale === "ar";
  const currentScenario = isArabic ? scenarioLabelAr : scenarioLabel;

  const totalDuration = pipelineStages.reduce((sum, s) => sum + s.duration_ms, 0);

  // Outcome feedback loop — fetch outcomes for this run
  const outcomeQuery = useQuery({
    queryKey: ["outcomes", runId],
    queryFn: () => api.outcomes.list({ run_id: runId }),
    enabled: !!runId,
    staleTime: 30_000,
  });
  const outcomes = outcomeQuery.data?.outcomes ?? [];

  return (
    <div
      className={`w-full space-y-4 ${isArabic ? "dir-rtl" : "dir-ltr"}`}
      dir={isArabic ? "rtl" : "ltr"}
    >
      {/* ── Governance Trust Intro ── */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center mt-0.5">
            <CheckCircle size={16} className="text-slate-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-sm font-bold text-slate-900 mb-1">
              {locale === "ar" ? "طبقة الحوكمة والثقة" : "Governance & Trust Layer"}
            </h2>
            <p className="text-xs text-slate-600 leading-relaxed mb-3">
              {locale === "ar"
                ? "كل رقم في هذا التقييم قابل للتدقيق وقابل للتتبع. تُوضح هذه الطبقة المصادر التي أغذت كل إشارة، والافتراضات التي بُنيت عليها التقديرات، ودرجة الثقة المحسوبة لكل مخرج. الإجابة على السؤال: «لماذا يجب أن أثق بهذا النظام؟»"
                : "Every number in this assessment is auditable and traceable. This layer shows which data sources fed each signal, what assumptions underlie the estimates, and the confidence score derived for each output. It directly answers: \"Why should I trust this system?\""}
            </p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-xs">
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                <p className="font-semibold text-slate-700 mb-1">
                  {locale === "ar" ? "المصادر → الإشارات" : "Sources → Signals"}
                </p>
                <p className="text-slate-500">
                  {locale === "ar"
                    ? "كل إشارة مرتبطة بمصدر بيانات موثق. الإشارات المحاكاة مُعلَّمة."
                    : "Every signal is linked to a documented data source. Simulated signals are labelled."}
                </p>
              </div>
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                <p className="font-semibold text-slate-700 mb-1">
                  {locale === "ar" ? "الافتراضات → النتائج" : "Assumptions → Outcomes"}
                </p>
                <p className="text-slate-500">
                  {locale === "ar"
                    ? "الافتراضات ذات الحساسية العالية تؤثر مباشرة على نطاق التقديرات المالية."
                    : "High-sensitivity assumptions directly affect the financial estimate range — shown as confidence bands."}
                </p>
              </div>
              <div className="bg-slate-50 rounded-lg p-3 border border-slate-100">
                <p className="font-semibold text-slate-700 mb-1">
                  {locale === "ar" ? "درجة الثقة" : "Confidence Score"}
                </p>
                <p className="text-slate-500">
                  {locale === "ar"
                    ? "تعكس نسبة الثقة مستوى التوافق بين الإشارات المستقلة."
                    : "The confidence score reflects the consensus level across independent signals, not data completeness."}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Header with Scenario Context */}
      <div className="bg-white border border-slate-200 rounded-lg p-4 shadow-sm">
        <h1 className="text-lg font-bold text-slate-900 mb-2">{labels.title}</h1>
        <div className="flex flex-wrap items-center gap-4">
          {currentScenario && (
            <div>
              <p className="text-xs text-slate-500">{labels.scenario}</p>
              <p className="text-sm font-semibold text-blue-700">{currentScenario}</p>
            </div>
          )}
          {runId && (
            <div>
              <p className="text-xs text-slate-500">{labels.runId}</p>
              <p className="text-xs font-mono text-slate-700 truncate max-w-xs">{runId}</p>
            </div>
          )}
          {severity !== undefined && (
            <div>
              <p className="text-xs text-slate-500">{labels.severity}</p>
              <p className="text-sm font-semibold text-slate-900">
                {(severity * 100).toFixed(1)}%
              </p>
            </div>
          )}
          {horizonHours !== undefined && (
            <div>
              <p className="text-xs text-slate-500">{labels.horizon}</p>
              <p className="text-sm font-semibold text-slate-900">
                {horizonHours} {labels.hours}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Run Provenance & Identity */}
      <CollapsibleSection
        title={labels.runProvenance}
        icon={<AlertCircle size={18} />}
        defaultOpen={true}
      >
        <div className="space-y-3">
          {trustInfo?.auditHash && (
            <div>
              <p className="text-xs text-slate-500 mb-1">{labels.auditHash}</p>
              <CopyableHash hash={trustInfo.auditHash} label={labels.auditHash} />
            </div>
          )}

          {trustInfo?.modelVersion && (
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">{labels.modelVersion}</span>
              <span className="text-slate-900 font-mono">{trustInfo.modelVersion}</span>
            </div>
          )}

          {trustInfo?.pipelineVersion && (
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">{labels.pipelineVersion}</span>
              <span className="text-slate-900 font-mono">{trustInfo.pipelineVersion}</span>
            </div>
          )}

          {trustInfo?.dataSources && trustInfo.dataSources.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 mb-1">{labels.dataSources}</p>
              <div className="flex flex-wrap gap-1">
                {trustInfo.dataSources.map((source, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 text-xs bg-white text-slate-700 rounded border border-slate-200"
                  >
                    {source}
                  </span>
                ))}
              </div>
            </div>
          )}

          {trustInfo?.confidence !== undefined && (
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">{labels.confidence}</span>
              <div className="flex items-center gap-2">
                <div className="w-24 h-2 bg-slate-100 rounded-full overflow-hidden border border-slate-200">
                  <div
                    className="h-full bg-gradient-to-r from-green-500 to-blue-500 rounded-full"
                    style={{ width: `${trustInfo.confidence * 100}%` }}
                  />
                </div>
                <span className="text-slate-900 font-mono text-xs">
                  {(trustInfo.confidence * 100).toFixed(1)}%
                </span>
              </div>
            </div>
          )}

          {trustInfo?.warnings && trustInfo.warnings.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 mb-1">{labels.warnings}</p>
              <div className="space-y-1">
                {trustInfo.warnings.map((warning, idx) => (
                  <div key={idx} className="text-xs text-amber-700 flex gap-2">
                    <AlertCircle size={12} className="flex-shrink-0 mt-0.5" />
                    <span>{warning}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </CollapsibleSection>

      {/* Decision Lifecycle & Lineage */}
      <CollapsibleSection
        title={labels.decisionLifecycle}
        icon={<Zap size={18} />}
        defaultOpen={true}
      >
        {decisionActions.length === 0 ? (
          <p className="text-sm text-slate-500">{labels.noDecisions}</p>
        ) : (
          <div className="space-y-3">
            {decisionActions.map((decision) => (
              <div key={decision.id} className="bg-white p-3 rounded border border-slate-200 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-slate-900">
                      {isArabic && decision.action_ar ? decision.action_ar : decision.action}
                    </p>
                    <div className="flex gap-2 mt-1 flex-wrap text-xs">
                      <span className="text-slate-500">{labels.sector}:</span>
                      <span className="text-slate-700">{decision.sector}</span>
                      <span className="text-slate-500">{labels.owner}:</span>
                      <span className="text-slate-700">{decision.owner}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="inline-block px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded border border-blue-200">
                      P{decision.priority}
                    </span>
                  </div>
                </div>

                <div className="flex justify-between items-center mb-2 text-xs">
                  <span className="text-slate-500">
                    {labels.confidence}: {(decision.confidence * 100).toFixed(0)}%
                  </span>
                  <span className="text-slate-500 font-mono text-xs">{decision.id}</span>
                </div>

                <StatusFlow status={decision.status} locale={locale} />
              </div>
            ))}
          </div>
        )}
      </CollapsibleSection>

      {/* Decision Value Audit */}
      <CollapsibleSection
        title={labels.decisionValue}
        icon={<CheckCircle size={18} />}
        defaultOpen={false}
      >
        <div className="text-sm text-slate-500">
          <p className="mb-2">
            Linked outcomes and ROI computations appear here when decisions are executed.
          </p>
          <div className="bg-slate-50 p-2 rounded text-xs font-mono text-slate-600 border border-slate-200">
            outcome_id → loss_avoided - cost = net_value
          </div>
        </div>
      </CollapsibleSection>

      {/* Outcome Audit Trail */}
      <CollapsibleSection
        title={labels.outcomeAudit}
        icon={<Clock size={18} />}
        defaultOpen={false}
      >
        <div className="text-sm text-slate-500">
          <p>Outcomes linked to decision actions with observation and confirmation status.</p>
          <div className="mt-2 bg-slate-50 p-2 rounded text-xs font-mono text-slate-600 border border-slate-200">
            observation_timestamp → confirmation_status
          </div>
        </div>
      </CollapsibleSection>

      {/* Pipeline Execution Record */}
      <CollapsibleSection
        title={labels.pipelineExecution}
        icon={<Zap size={18} />}
        defaultOpen={true}
      >
        {pipelineStages.length === 0 ? (
          <p className="text-sm text-slate-500">{labels.noPipeline}</p>
        ) : (
          <div className="space-y-3">
            {/* Progress Bar */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <p className="text-xs text-slate-500">Pipeline Progress</p>
                <span className="text-xs text-slate-600 font-mono">
                  {totalDuration.toFixed(0)}ms total
                </span>
              </div>
              <div className="flex h-6 gap-0.5 bg-slate-100 rounded overflow-hidden border border-slate-200">
                {pipelineStages.map((stage, idx) => {
                  const percentage = totalDuration > 0 ? (stage.duration_ms / totalDuration) * 100 : 0;
                  const isPass = stage.status === "pass" || stage.status === "success";
                  const bgColor = isPass ? "bg-green-500" : "bg-red-500";

                  return (
                    <div
                      key={idx}
                      className={`${bgColor} transition-all hover:opacity-80`}
                      style={{ width: `${percentage}%` }}
                      title={`${stage.name}: ${stage.duration_ms}ms (${stage.status})`}
                    />
                  );
                })}
              </div>
            </div>

            {/* Stage Details */}
            <div className="space-y-2">
              {pipelineStages.map((stage, idx) => (
                <div key={idx} className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2 flex-1">
                    {stage.status === "pass" || stage.status === "success" ? (
                      <CheckCircle size={14} className="text-green-600 flex-shrink-0" />
                    ) : (
                      <AlertCircle size={14} className="text-red-600 flex-shrink-0" />
                    )}
                    <span className="text-slate-700 font-mono truncate">{stage.name}</span>
                  </div>
                  <div className="flex gap-2 items-center">
                    <span className="text-slate-600 font-mono">{stage.duration_ms}ms</span>
                    <SeverityBadge severity={stage.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CollapsibleSection>

      {/* Institutional Memory — live outcome feedback loop */}
      <CollapsibleSection
        title={labels.institutionalMemory}
        icon={<Clock size={18} />}
        defaultOpen={false}
      >
        <div className="space-y-3">
          <div className="bg-io-accent/5 border border-io-accent/15 rounded-lg p-4">
            <p className="text-sm text-slate-700 mb-2">
              {locale === "ar"
                ? "الذاكرة المؤسسية تربط القرارات السابقة بنتائجها الفعلية — لتحسين جودة القرار في السيناريوهات المستقبلية."
                : "Institutional memory links past decisions to their actual outcomes — improving decision quality for future scenarios."}
            </p>
            <div className="grid grid-cols-3 gap-3 mt-3">
              <div className="bg-white rounded-lg p-3 border border-slate-200 text-center">
                <p className="text-lg font-bold text-io-accent">{outcomes.length || "—"}</p>
                <p className="text-[10px] text-slate-500 uppercase mt-1">
                  {locale === "ar" ? "قرارات مسجلة" : "Decisions Recorded"}
                </p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-slate-200 text-center">
                <p className="text-lg font-bold text-io-status-low">
                  {outcomes.filter((o: any) => o.outcome_status === "confirmed" || o.outcome_status === "closed").length || "—"}
                </p>
                <p className="text-[10px] text-slate-500 uppercase mt-1">
                  {locale === "ar" ? "نتائج مؤكدة" : "Outcomes Confirmed"}
                </p>
              </div>
              <div className="bg-white rounded-lg p-3 border border-slate-200 text-center">
                <p className="text-lg font-bold text-io-status-elevated">
                  {outcomes.filter((o: any) => o.outcome_classification != null).length || "—"}
                </p>
                <p className="text-[10px] text-slate-500 uppercase mt-1">
                  {locale === "ar" ? "حلقة التعلم" : "Learning Loop"}
                </p>
              </div>
            </div>
          </div>
          {/* Outcome timeline */}
          {outcomes.length > 0 ? (
            <div className="space-y-2">
              {outcomes.slice(0, 10).map((o: any) => (
                <div key={o.outcome_id} className="flex items-center justify-between text-xs bg-slate-50 rounded-lg px-3 py-2 border border-slate-200">
                  <div className="flex items-center gap-2">
                    <span className={`w-2 h-2 rounded-full ${
                      o.outcome_status === "confirmed" || o.outcome_status === "closed"
                        ? "bg-io-status-low"
                        : o.outcome_status === "observed"
                          ? "bg-io-status-elevated"
                          : "bg-slate-400"
                    }`} />
                    <span className="text-slate-700 font-medium">
                      {o.source_decision_id?.slice(0, 8) ?? "—"}
                    </span>
                  </div>
                  <span className="text-slate-500">{o.outcome_status}</span>
                  <span className="text-slate-400 tabular-nums">
                    {new Date(o.recorded_at).toLocaleDateString()}
                  </span>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">
              {locale === "ar"
                ? "سيتم تفعيل هذا القسم بعد تنفيذ أول قرار وتسجيل نتائجه."
                : "This section activates after the first decision is executed and its outcome is recorded."}
            </p>
          )}
        </div>
      </CollapsibleSection>

      {/* Regulatory Breach Events */}
      <CollapsibleSection
        title={labels.regulatoryBreaches}
        icon={<AlertCircle size={18} />}
        defaultOpen={true}
      >
        {regulatoryBreaches.length === 0 ? (
          <div className="flex items-center gap-2 text-sm text-green-700">
            <CheckCircle size={16} />
            <span>{labels.noBreaches}</span>
          </div>
        ) : (
          <div className="space-y-3">
            {regulatoryBreaches.map((breach, idx) => (
              <div key={idx} className="bg-white p-3 rounded border border-slate-200 shadow-sm">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="text-sm font-semibold text-slate-900">{breach.metric}</p>
                    <p className="text-xs text-slate-500 mt-1">{breach.sector}</p>
                  </div>
                  <SeverityBadge severity={breach.severity} />
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                  <div>
                    <span className="text-slate-500">{labels.threshold}</span>
                    <p className="font-mono text-slate-700">{breach.threshold.toFixed(4)}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">{labels.actual}</span>
                    <p className="font-mono text-slate-700">{breach.actual.toFixed(4)}</p>
                  </div>
                </div>

                {breach.mandatory_actions.length > 0 && (
                  <div>
                    <p className="text-xs text-slate-500 mb-1">{labels.mandatoryActions}</p>
                    <ul className="space-y-1">
                      {breach.mandatory_actions.map((action, actionIdx) => (
                        <li key={actionIdx} className="text-xs text-slate-700 flex gap-2">
                          <span className="text-amber-600 flex-shrink-0">•</span>
                          <span>{action}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </CollapsibleSection>
    </div>
  );
};

export default RegulatoryAuditView;
