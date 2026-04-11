"use client";

import React, { useState } from "react";
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
    title: "Regulatory & Audit",
    runProvenance: "Run Provenance & Identity",
    decisionLifecycle: "Decision Lifecycle & Lineage",
    outcomeAudit: "Outcome Audit Trail",
    decisionValue: "Decision Value Audit",
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
    title: "الرقابة والتدقيق",
    runProvenance: "أصل التشغيل والهوية",
    decisionLifecycle: "دورة حياة القرار والنسب",
    outcomeAudit: "مسار تدقيق النتائج",
    decisionValue: "تدقيق قيمة القرار",
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
    <div className="border border-slate-700 rounded-lg overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full px-4 py-3 bg-slate-800/50 hover:bg-slate-800 transition-colors flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div className="text-slate-400">{icon}</div>
          <span className="text-sm font-semibold text-slate-200">{title}</span>
        </div>
        <ChevronDown
          size={18}
          className={`text-slate-400 transition-transform ${isOpen ? "rotate-180" : ""}`}
        />
      </button>
      {isOpen && (
        <div className="px-4 py-3 bg-slate-900/50 border-t border-slate-700">
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
    <div className="flex items-center justify-between bg-slate-900 p-2 rounded border border-slate-700">
      <code className="text-xs text-slate-300 truncate">{hash}</code>
      <button
        onClick={handleCopy}
        className="ml-2 p-1 hover:bg-slate-800 rounded transition-colors"
        title={label}
      >
        {copied ? (
          <CheckCircle size={16} className="text-green-500" />
        ) : (
          <Copy size={16} className="text-slate-500 hover:text-slate-300" />
        )}
      </button>
    </div>
  );
};

const SeverityBadge: React.FC<{ severity: string }> = ({ severity }) => {
  const severityMap: Record<string, string> = {
    critical: "bg-red-900/40 text-red-300 border-red-700",
    high: "bg-red-800/40 text-red-300 border-red-700",
    medium: "bg-amber-900/40 text-amber-300 border-amber-700",
    low: "bg-yellow-900/40 text-yellow-300 border-yellow-700",
    nominal: "bg-green-900/40 text-green-300 border-green-700",
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
                ? "bg-blue-900/50 text-blue-300 border border-blue-700"
                : "bg-slate-800 text-slate-500 border border-slate-700"
            }`}
          >
            {s}
          </div>
          {idx < statusList.length - 1 && (
            <div
              className={`h-0.5 w-2 ${idx < currentIndex ? "bg-blue-600" : "bg-slate-700"}`}
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

  return (
    <div
      className={`w-full space-y-4 ${isArabic ? "dir-rtl" : "dir-ltr"}`}
      dir={isArabic ? "rtl" : "ltr"}
    >
      {/* Header with Scenario Context */}
      <div className="bg-gradient-to-r from-slate-800 to-slate-900 border border-slate-700 rounded-lg p-4">
        <h1 className="text-lg font-bold text-slate-100 mb-2">{labels.title}</h1>
        <div className="flex flex-wrap items-center gap-4">
          {currentScenario && (
            <div>
              <p className="text-xs text-slate-500">{labels.scenario}</p>
              <p className="text-sm font-semibold text-blue-300">{currentScenario}</p>
            </div>
          )}
          {runId && (
            <div>
              <p className="text-xs text-slate-500">{labels.runId}</p>
              <p className="text-xs font-mono text-slate-300 truncate max-w-xs">{runId}</p>
            </div>
          )}
          {severity !== undefined && (
            <div>
              <p className="text-xs text-slate-500">{labels.severity}</p>
              <p className="text-sm font-semibold text-slate-200">
                {(severity * 100).toFixed(1)}%
              </p>
            </div>
          )}
          {horizonHours !== undefined && (
            <div>
              <p className="text-xs text-slate-500">{labels.horizon}</p>
              <p className="text-sm font-semibold text-slate-200">
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
              <span className="text-slate-300 font-mono">{trustInfo.modelVersion}</span>
            </div>
          )}

          {trustInfo?.pipelineVersion && (
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">{labels.pipelineVersion}</span>
              <span className="text-slate-300 font-mono">{trustInfo.pipelineVersion}</span>
            </div>
          )}

          {trustInfo?.dataSources && trustInfo.dataSources.length > 0 && (
            <div>
              <p className="text-xs text-slate-500 mb-1">{labels.dataSources}</p>
              <div className="flex flex-wrap gap-1">
                {trustInfo.dataSources.map((source, idx) => (
                  <span
                    key={idx}
                    className="px-2 py-1 text-xs bg-slate-800 text-slate-300 rounded border border-slate-700"
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
                <div className="w-24 h-2 bg-slate-800 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-green-600 to-blue-600 rounded-full"
                    style={{ width: `${trustInfo.confidence * 100}%` }}
                  />
                </div>
                <span className="text-slate-300 font-mono text-xs">
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
                  <div key={idx} className="text-xs text-amber-300 flex gap-2">
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
              <div key={decision.id} className="bg-slate-800/50 p-3 rounded border border-slate-700">
                <div className="flex justify-between items-start mb-2">
                  <div className="flex-1">
                    <p className="text-sm font-semibold text-slate-200">
                      {isArabic && decision.action_ar ? decision.action_ar : decision.action}
                    </p>
                    <div className="flex gap-2 mt-1 flex-wrap text-xs">
                      <span className="text-slate-500">{labels.sector}:</span>
                      <span className="text-slate-300">{decision.sector}</span>
                      <span className="text-slate-500">{labels.owner}:</span>
                      <span className="text-slate-300">{decision.owner}</span>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="inline-block px-2 py-1 text-xs bg-blue-900/40 text-blue-300 rounded border border-blue-700">
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
        <div className="text-sm text-slate-400">
          <p className="mb-2">
            Linked outcomes and ROI computations appear here when decisions are executed.
          </p>
          <div className="bg-slate-900 p-2 rounded text-xs font-mono text-slate-500">
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
        <div className="text-sm text-slate-400">
          <p>Outcomes linked to decision actions with observation and confirmation status.</p>
          <div className="mt-2 bg-slate-900 p-2 rounded text-xs font-mono text-slate-500">
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
                <span className="text-xs text-slate-400 font-mono">
                  {totalDuration.toFixed(0)}ms total
                </span>
              </div>
              <div className="flex h-6 gap-0.5 bg-slate-900 rounded overflow-hidden border border-slate-700">
                {pipelineStages.map((stage, idx) => {
                  const percentage = totalDuration > 0 ? (stage.duration_ms / totalDuration) * 100 : 0;
                  const isPass = stage.status === "pass" || stage.status === "success";
                  const bgColor = isPass ? "bg-green-700" : "bg-red-700";

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
                      <CheckCircle size={14} className="text-green-500 flex-shrink-0" />
                    ) : (
                      <AlertCircle size={14} className="text-red-500 flex-shrink-0" />
                    )}
                    <span className="text-slate-300 font-mono truncate">{stage.name}</span>
                  </div>
                  <div className="flex gap-2 items-center">
                    <span className="text-slate-500 font-mono">{stage.duration_ms}ms</span>
                    <SeverityBadge severity={stage.status} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </CollapsibleSection>

      {/* Regulatory Breach Events */}
      <CollapsibleSection
        title={labels.regulatoryBreaches}
        icon={<AlertCircle size={18} />}
        defaultOpen={true}
      >
        {regulatoryBreaches.length === 0 ? (
          <div className="flex items-center gap-2 text-sm text-green-400">
            <CheckCircle size={16} />
            <span>{labels.noBreaches}</span>
          </div>
        ) : (
          <div className="space-y-3">
            {regulatoryBreaches.map((breach, idx) => (
              <div key={idx} className="bg-slate-800/50 p-3 rounded border border-slate-700">
                <div className="flex justify-between items-start mb-2">
                  <div>
                    <p className="text-sm font-semibold text-slate-200">{breach.metric}</p>
                    <p className="text-xs text-slate-500 mt-1">{breach.sector}</p>
                  </div>
                  <SeverityBadge severity={breach.severity} />
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs mb-2">
                  <div>
                    <span className="text-slate-500">{labels.threshold}</span>
                    <p className="font-mono text-slate-300">{breach.threshold.toFixed(4)}</p>
                  </div>
                  <div>
                    <span className="text-slate-500">{labels.actual}</span>
                    <p className="font-mono text-slate-300">{breach.actual.toFixed(4)}</p>
                  </div>
                </div>

                {breach.mandatory_actions.length > 0 && (
                  <div>
                    <p className="text-xs text-slate-500 mb-1">{labels.mandatoryActions}</p>
                    <ul className="space-y-1">
                      {breach.mandatory_actions.map((action, actionIdx) => (
                        <li key={actionIdx} className="text-xs text-slate-300 flex gap-2">
                          <span className="text-amber-500 flex-shrink-0">•</span>
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
