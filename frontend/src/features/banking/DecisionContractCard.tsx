'use client';

import { DecisionContract, DecisionStatus } from '@/types/banking-intelligence';
import { formatUSD, formatHours } from '@/lib/format';
import { ChevronDown, ChevronUp, Clock, Users, Scale, AlertCircle } from 'lucide-react';
import { useState } from 'react';

interface DecisionContractCardProps {
  contract: DecisionContract;
  lang?: 'en' | 'ar';
}

const statusColors: Record<DecisionStatus, string> = {
  DRAFT: 'bg-gray-100 text-gray-800',
  PENDING_APPROVAL: 'bg-yellow-100 text-yellow-800',
  APPROVED: 'bg-blue-100 text-blue-800',
  EXECUTING: 'bg-purple-100 text-purple-800',
  EXECUTED: 'bg-green-100 text-green-800',
  UNDER_REVIEW: 'bg-cyan-100 text-cyan-800',
  CLOSED: 'bg-gray-100 text-gray-800',
  ROLLED_BACK: 'bg-red-100 text-red-800',
  EXPIRED: 'bg-orange-100 text-orange-800',
  REJECTED: 'bg-red-100 text-red-800',
};

const translations = {
  en: {
    title: 'Decision Contract',
    status: 'Status',
    sector: 'Sector',
    type: 'Type',
    owner: 'Owner',
    approver: 'Approver',
    deadline: 'Deadline',
    trigger: 'Trigger Condition',
    escalation: 'Escalation Threshold',
    legal: 'Legal Authority',
    reversibility: 'Reversibility',
    execution: 'Execution Feasibility',
    dependencies: 'Dependencies',
    satisfied: 'Satisfied',
    pending: 'Pending',
    rollbackPlan: 'Rollback Plan',
    possible: 'Possible',
    notPossible: 'Not Possible',
    steps: 'Steps',
    rollbackOwner: 'Rollback Owner',
    maxWindow: 'Max Rollback Window',
    cost: 'Estimated Cost',
    sideEffects: 'Side Effects',
    observation: 'Observation Plan',
    primaryMetric: 'Primary Metric',
    secondaryMetrics: 'Secondary Metrics',
    windows: 'Windows (hours)',
    baseline: 'Baseline',
    target: 'Target',
    alert: 'Alert Threshold',
    observer: 'Observer',
    history: 'Status History',
    changedBy: 'Changed By',
    reason: 'Reason',
  },
  ar: {
    title: 'عقد القرار',
    status: 'الحالة',
    sector: 'القطاع',
    type: 'النوع',
    owner: 'المالك',
    approver: 'الموافق',
    deadline: 'الموعد النهائي',
    trigger: 'شرط التفعيل',
    escalation: 'عتبة التصعيد',
    legal: 'الأساس القانوني',
    reversibility: 'القابلية للعكس',
    execution: 'جدوى التنفيذ',
    dependencies: 'التبعيات',
    satisfied: 'مستوفى',
    pending: 'قيد الانتظار',
    rollbackPlan: 'خطة الاسترجاع',
    possible: 'ممكنة',
    notPossible: 'غير ممكنة',
    steps: 'الخطوات',
    rollbackOwner: 'مالك الاسترجاع',
    maxWindow: 'الحد الأقصى لنافذة الاسترجاع',
    cost: 'التكلفة المقدرة',
    sideEffects: 'الآثار الجانبية',
    observation: 'خطة الملاحظة',
    primaryMetric: 'المقياس الأساسي',
    secondaryMetrics: 'المقاييس الثانوية',
    windows: 'النوافذ (ساعات)',
    baseline: 'الخط الأساسي',
    target: 'الهدف',
    alert: 'عتبة التنبيه',
    observer: 'المراقب',
    history: 'سجل الحالة',
    changedBy: 'تم التغيير بواسطة',
    reason: 'السبب',
  },
};

export function DecisionContractCard({
  contract,
  lang = 'en',
}: DecisionContractCardProps) {
  const t = (key: keyof (typeof translations)['en']) => translations[lang]?.[key] ?? key;
  const [expandedRollback, setExpandedRollback] = useState(false);
  const [expandedObservation, setExpandedObservation] = useState(false);
  const [expandedHistory, setExpandedHistory] = useState(false);

  const satisfiedDeps = contract.dependencies.filter((d) => d.is_satisfied).length;
  const allDeps = contract.dependencies.length;

  const isRTL = lang === 'ar';

  return (
    <div
      className={`rounded-lg border border-gray-200 bg-white p-6 shadow-sm ${
        isRTL ? 'text-right' : 'text-left'
      }`}
    >
      {/* Header */}
      <div className="mb-4 flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{contract.title}</h3>
          <p className="text-sm text-gray-500">{contract.decision_id}</p>
        </div>
        <div
          className={`inline-flex rounded-full px-3 py-1 text-sm font-medium ${
            statusColors[contract.status]
          }`}
        >
          {contract.status}
        </div>
      </div>

      {/* Description */}
      {contract.description && (
        <p className="mb-4 text-sm text-gray-700">{contract.description}</p>
      )}

      {/* Key Metadata Grid */}
      <div className="mb-6 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="font-medium text-gray-600">{t('sector')}</p>
          <p className="text-gray-900">{contract.sector}</p>
        </div>
        <div>
          <p className="font-medium text-gray-600">{t('type')}</p>
          <p className="text-gray-900">{contract.decision_type}</p>
        </div>
        <div>
          <p className="font-medium text-gray-600">{t('owner')}</p>
          <p className="text-gray-900">{contract.primary_owner_id}</p>
        </div>
        <div>
          <p className="font-medium text-gray-600">{t('approver')}</p>
          <p className="text-gray-900">{contract.approver_id}</p>
        </div>
      </div>

      {/* Deadline & Escalation */}
      <div className="mb-6 flex items-center gap-4 rounded-lg bg-gray-50 p-4 text-sm">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4 text-gray-600" />
          <div>
            <p className="font-medium text-gray-600">{t('deadline')}</p>
            <p className="text-gray-900">{new Date(contract.deadline_at).toLocaleString()}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <AlertCircle className="h-4 w-4 text-orange-600" />
          <div>
            <p className="font-medium text-gray-600">{t('escalation')}</p>
            <p className="text-gray-900">{(contract.escalation_threshold * 100).toFixed(0)}%</p>
          </div>
        </div>
      </div>

      {/* Trigger & Legal */}
      <div className="mb-6 grid grid-cols-1 gap-4 text-sm lg:grid-cols-2">
        <div>
          <p className="font-medium text-gray-600">{t('trigger')}</p>
          <p className="font-mono text-xs text-gray-700">{contract.trigger_condition}</p>
        </div>
        <div>
          <p className="font-medium text-gray-600">{t('legal')}</p>
          <p className="text-gray-900">{contract.legal_authority_basis}</p>
        </div>
      </div>

      {/* Reversibility & Execution */}
      <div className="mb-6 grid grid-cols-2 gap-4 text-sm">
        <div>
          <p className="font-medium text-gray-600">{t('reversibility')}</p>
          <p className="text-gray-900">{contract.reversibility}</p>
        </div>
        <div>
          <p className="font-medium text-gray-600">{t('execution')}</p>
          <p className="text-gray-900">{contract.execution_feasibility}</p>
        </div>
      </div>

      {/* Dependencies */}
      {allDeps > 0 && (
        <div className="mb-6 rounded-lg border border-gray-200 p-4">
          <p className="mb-3 font-medium text-gray-900">
            {t('dependencies')} ({satisfiedDeps}/{allDeps})
          </p>
          <div className="space-y-2">
            {contract.dependencies.map((dep) => (
              <div
                key={dep.dependency_id}
                className="flex items-center gap-2 text-sm"
              >
                <div
                  className={`h-2 w-2 rounded-full ${
                    dep.is_satisfied ? 'bg-green-500' : 'bg-yellow-500'
                  }`}
                />
                <span className="text-gray-700">{dep.dependency_type}</span>
                <span className="text-gray-500">{dep.dependency_id}</span>
                {!dep.is_satisfied && dep.blocker_description && (
                  <span className="text-xs text-red-600">({dep.blocker_description})</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rollback Plan */}
      <div className="mb-6 border-t border-gray-200 pt-4">
        <button
          onClick={() => setExpandedRollback(!expandedRollback)}
          className="flex w-full items-center justify-between rounded-lg bg-gray-50 px-4 py-3 font-medium text-gray-900 hover:bg-gray-100"
        >
          <span>{t('rollbackPlan')}</span>
          {expandedRollback ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>
        {expandedRollback && (
          <div className="mt-4 space-y-3 text-sm">
            <div>
              <p className="font-medium text-gray-600">Status</p>
              <p className="text-gray-900">
                {contract.rollback_plan.is_rollback_possible
                  ? t('possible')
                  : t('notPossible')}
              </p>
            </div>
            {contract.rollback_plan.rollback_steps.length > 0 && (
              <div>
                <p className="font-medium text-gray-600">{t('steps')}</p>
                <ol className="space-y-1 text-gray-700">
                  {contract.rollback_plan.rollback_steps.map((step, i) => (
                    <li key={i} className="ml-4 list-decimal">
                      {step}
                    </li>
                  ))}
                </ol>
              </div>
            )}
            <div>
              <p className="font-medium text-gray-600">{t('rollbackOwner')}</p>
              <p className="text-gray-900">{contract.rollback_plan.rollback_owner_id}</p>
            </div>
            {contract.rollback_plan.max_rollback_window_hours && (
              <div>
                <p className="font-medium text-gray-600">{t('maxWindow')}</p>
                <p className="text-gray-900">
                  {formatHours(contract.rollback_plan.max_rollback_window_hours)}
                </p>
              </div>
            )}
            {contract.rollback_plan.estimated_rollback_cost_usd !== null && (
              <div>
                <p className="font-medium text-gray-600">{t('cost')}</p>
                <p className="text-gray-900">
                  {formatUSD(contract.rollback_plan.estimated_rollback_cost_usd)}
                </p>
              </div>
            )}
            {contract.rollback_plan.side_effects_of_rollback.length > 0 && (
              <div>
                <p className="font-medium text-gray-600">{t('sideEffects')}</p>
                <ul className="space-y-1 text-gray-700">
                  {contract.rollback_plan.side_effects_of_rollback.map((effect, i) => (
                    <li key={i} className="ml-4 list-disc">
                      {effect}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Observation Plan */}
      <div className="mb-6 border-t border-gray-200 pt-4">
        <button
          onClick={() => setExpandedObservation(!expandedObservation)}
          className="flex w-full items-center justify-between rounded-lg bg-gray-50 px-4 py-3 font-medium text-gray-900 hover:bg-gray-100"
        >
          <span>{t('observation')}</span>
          {expandedObservation ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>
        {expandedObservation && (
          <div className="mt-4 space-y-3 text-sm">
            <div>
              <p className="font-medium text-gray-600">{t('primaryMetric')}</p>
              <p className="text-gray-900">{contract.observation_plan.primary_metric}</p>
            </div>
            {contract.observation_plan.secondary_metrics.length > 0 && (
              <div>
                <p className="font-medium text-gray-600">{t('secondaryMetrics')}</p>
                <p className="text-gray-700">
                  {contract.observation_plan.secondary_metrics.join(', ')}
                </p>
              </div>
            )}
            <div>
              <p className="font-medium text-gray-600">{t('windows')}</p>
              <p className="text-gray-700">
                {contract.observation_plan.observation_windows_hours.join(', ')}
              </p>
            </div>
            {contract.observation_plan.baseline_value !== null && (
              <div>
                <p className="font-medium text-gray-600">{t('baseline')}</p>
                <p className="text-gray-900">{contract.observation_plan.baseline_value}</p>
              </div>
            )}
            {contract.observation_plan.target_value !== null && (
              <div>
                <p className="font-medium text-gray-600">{t('target')}</p>
                <p className="text-gray-900">{contract.observation_plan.target_value}</p>
              </div>
            )}
            {contract.observation_plan.alert_threshold !== null && (
              <div>
                <p className="font-medium text-gray-600">{t('alert')}</p>
                <p className="text-gray-900">{contract.observation_plan.alert_threshold}</p>
              </div>
            )}
            <div>
              <p className="font-medium text-gray-600">{t('observer')}</p>
              <p className="text-gray-900">{contract.observation_plan.observer_entity_id}</p>
            </div>
          </div>
        )}
      </div>

      {/* Status History */}
      {contract.status_history.length > 0 && (
        <div className="border-t border-gray-200 pt-4">
          <button
            onClick={() => setExpandedHistory(!expandedHistory)}
            className="flex w-full items-center justify-between rounded-lg bg-gray-50 px-4 py-3 font-medium text-gray-900 hover:bg-gray-100"
          >
            <span>{t('history')}</span>
            {expandedHistory ? (
              <ChevronUp className="h-4 w-4" />
            ) : (
              <ChevronDown className="h-4 w-4" />
            )}
          </button>
          {expandedHistory && (
            <div className="mt-4 space-y-3 text-sm">
              {contract.status_history.map((entry, i) => (
                <div
                  key={i}
                  className="border-l-2 border-gray-300 pl-4"
                >
                  <p className="font-mono text-xs text-gray-500">
                    {new Date(entry.timestamp).toLocaleString()}
                  </p>
                  <p className="text-gray-900">
                    {entry.from_status} → {entry.to_status}
                  </p>
                  <p className="text-gray-600">{t('changedBy')}: {entry.changed_by}</p>
                  {entry.reason && (
                    <p className="text-gray-600">{t('reason')}: {entry.reason}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
