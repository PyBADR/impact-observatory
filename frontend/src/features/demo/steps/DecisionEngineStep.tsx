'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Clock,
  AlertTriangle,
  CheckCircle2,
  AlertCircle,
  Zap,
  Activity,
} from 'lucide-react';
import { DemoStepProps } from '../DemoStepRenderer';
import { getScenario } from '../data/demo-scenario';

const URGENCY_BADGE: Record<string, { bg: string; text: string; icon: React.ElementType }> = {
  IMMEDIATE: {
    bg: 'bg-red-100',
    text: 'text-red-700',
    icon: AlertTriangle,
  },
  '24H': {
    bg: 'bg-orange-100',
    text: 'text-orange-700',
    icon: Clock,
  },
  '72H': {
    bg: 'bg-amber-100',
    text: 'text-amber-700',
    icon: Clock,
  },
};

const formatTime = (hours: number): string => {
  if (hours >= 24) {
    const days = Math.floor(hours / 24);
    const remainingHours = Math.round((hours % 24) * 10) / 10;
    return `${days}d ${remainingHours}h`;
  }
  return `${Math.round(hours)}h`;
};

interface DecisionCardProps {
  title: string;
  owner: string;
  urgency: 'IMMEDIATE' | '24H' | '72H';
  expectedEffect: string;
  consequence: string;
  isActive: boolean;
  onToggle: () => void;
}

const DecisionCard: React.FC<DecisionCardProps> = ({
  title,
  owner,
  urgency,
  expectedEffect,
  consequence,
  isActive,
  onToggle,
}) => {
  const urgencyConfig = URGENCY_BADGE[urgency];
  const UrgencyIcon = urgencyConfig.icon;

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -10 }}
      className={`border rounded-xl p-4 cursor-pointer transition-all ${
        isActive
          ? 'bg-emerald-50 border-emerald-300 shadow-md'
          : 'bg-white border-slate-200 hover:border-slate-300 hover:shadow-sm'
      }`}
      onClick={onToggle}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <h4 className="font-semibold text-slate-900 text-sm mb-1">{title}</h4>
          <p className="text-xs text-slate-500">{owner}</p>
        </div>
        <div className={`${urgencyConfig.bg} rounded-lg p-1.5 ml-2 flex-shrink-0`}>
          <UrgencyIcon className={`w-4 h-4 ${urgencyConfig.text}`} />
        </div>
      </div>

      <div className="space-y-2">
        <div>
          <p className="text-xs font-medium text-slate-600">Expected Effect</p>
          <p className="text-sm text-slate-700">{expectedEffect}</p>
        </div>

        <div className="bg-slate-50 rounded-lg p-2 border border-slate-100">
          <p className="text-xs font-medium text-slate-600 mb-1">Risk if Delayed</p>
          <p className="text-sm text-slate-700">{consequence}</p>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-slate-200 flex items-center justify-between">
        <span
          className={`text-xs font-medium ${
            isActive ? 'text-emerald-700' : 'text-slate-500'
          }`}
        >
          {isActive ? 'Active' : 'Select to activate'}
        </span>
        <div
          className={`w-5 h-5 rounded-full border-2 flex items-center justify-center ${
            isActive
              ? 'bg-emerald-500 border-emerald-600'
              : 'border-slate-300'
          }`}
        >
          {isActive && <CheckCircle2 className="w-4 h-4 text-white" />}
        </div>
      </div>
    </motion.div>
  );
};

export const DecisionEngineStep: React.FC<DemoStepProps> = ({
  onPause,
  activeRole,
  sim,
  onToggleDecision,
  scenarioId,
}) => {
  const scenario = getScenario(scenarioId);
  const [timeRemaining, setTimeRemaining] = useState(scenario?.decisionPressure.hoursRemaining || 0);
  const [activeDecisions, setActiveDecisions] = useState<Set<number>>(new Set());

  useEffect(() => {
    if (!scenario) return;

    const interval = setInterval(() => {
      setTimeRemaining((prev) => {
        const newTime = Math.max(prev - 0.1, 0);
        return newTime;
      });
    }, 360);

    return () => clearInterval(interval);
  }, [scenario]);

  const handleToggleDecision = (index: number) => {
    const newActive = new Set(activeDecisions);
    if (newActive.has(index)) {
      newActive.delete(index);
    } else {
      newActive.add(index);
    }
    setActiveDecisions(newActive);
    if (onToggleDecision) {
      onToggleDecision(index);
    }
  };

  if (!scenario) {
    return (
      <div className="flex items-center justify-center h-full text-slate-500">
        Scenario not found
      </div>
    );
  }

  const { decisionPressure } = scenario;
  const escalationLevel = timeRemaining < 1 ? 'CRITICAL' : timeRemaining < 3 ? 'HIGH' : 'MODERATE';

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
      className="h-full flex flex-col"
    >
      {/* Header with Timer */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Decision Room</h2>
          <p className="text-slate-600 text-sm mt-1">Executive actions to mitigate sector stress</p>
        </div>
        <button
          onClick={onPause}
          className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-sm font-medium transition"
        >
          Pause
        </button>
      </div>

      {/* Decision Window Timer */}
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className={`rounded-xl p-4 mb-6 border-2 ${
          escalationLevel === 'CRITICAL'
            ? 'bg-red-50 border-red-300'
            : escalationLevel === 'HIGH'
            ? 'bg-orange-50 border-orange-300'
            : 'bg-blue-50 border-blue-300'
        }`}
      >
        <div className="flex items-center gap-4">
          <div className={`p-3 rounded-lg ${
            escalationLevel === 'CRITICAL'
              ? 'bg-red-100'
              : escalationLevel === 'HIGH'
              ? 'bg-orange-100'
              : 'bg-blue-100'
          }`}>
            <Clock className={`w-6 h-6 ${
              escalationLevel === 'CRITICAL'
                ? 'text-red-700'
                : escalationLevel === 'HIGH'
                ? 'text-orange-700'
                : 'text-blue-700'
            }`} />
          </div>
          <div className="flex-1">
            <p className={`text-sm font-medium ${
              escalationLevel === 'CRITICAL'
                ? 'text-red-900'
                : escalationLevel === 'HIGH'
                ? 'text-orange-900'
                : 'text-blue-900'
            }`}>
              {decisionPressure.clockLabel}
            </p>
            <p className={`text-xs ${
              escalationLevel === 'CRITICAL'
                ? 'text-red-700'
                : escalationLevel === 'HIGH'
                ? 'text-orange-700'
                : 'text-blue-700'
            }`}>
              {formatTime(timeRemaining)} remaining to activate mitigations
            </p>
          </div>
          <div className="text-right">
            <div className={`text-3xl font-bold font-mono ${
              escalationLevel === 'CRITICAL'
                ? 'text-red-700'
                : escalationLevel === 'HIGH'
                ? 'text-orange-700'
                : 'text-blue-700'
            }`}>
              {formatTime(timeRemaining)}
            </div>
          </div>
        </div>
      </motion.div>

      {/* Escalation Risk Banner */}
      <AnimatePresence>
        {escalationLevel !== 'MODERATE' && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className={`rounded-xl p-3 mb-6 border-l-4 flex items-start gap-3 ${
              escalationLevel === 'CRITICAL'
                ? 'bg-red-50 border-l-red-600'
                : 'bg-orange-50 border-l-orange-600'
            }`}
          >
            <AlertTriangle className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
              escalationLevel === 'CRITICAL'
                ? 'text-red-600'
                : 'text-orange-600'
            }`} />
            <div>
              <p className={`text-sm font-semibold ${
                escalationLevel === 'CRITICAL'
                  ? 'text-red-900'
                  : 'text-orange-900'
              }`}>
                {decisionPressure.escalationBanner}
              </p>
              <p className={`text-xs ${
                escalationLevel === 'CRITICAL'
                  ? 'text-red-700'
                  : 'text-orange-700'
              } mt-1`}>
                {decisionPressure.consequenceStatement}
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Decision Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 overflow-y-auto">
        <AnimatePresence mode="popLayout">
          {scenario.decisions.map((decision, idx) => (
            <DecisionCard
              key={`decision-${idx}`}
              title={decision.title}
              owner={decision.owner}
              urgency={decision.urgency}
              expectedEffect={decision.expectedEffect}
              consequence={decision.consequence}
              isActive={activeDecisions.has(idx)}
              onToggle={() => handleToggleDecision(idx)}
            />
          ))}
        </AnimatePresence>
      </div>

      {/* Assessment Status Footer */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-6 pt-4 border-t border-slate-200 flex items-center justify-between"
      >
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-blue-600" />
          <span className="text-sm text-slate-600">
            Projection: <span className="font-semibold text-slate-900">
              {sim && sim.decisionsActivated > 0 ? 'Updated with interventions' : 'Baseline scenario'}
            </span>
          </span>
        </div>
        <div className="text-xs text-slate-500">
          {activeDecisions.size > 0 && (
            <span className="font-medium text-emerald-700">
              {activeDecisions.size} action{activeDecisions.size !== 1 ? 's' : ''} activated
            </span>
          )}
        </div>
      </motion.div>
    </motion.div>
  );
};
