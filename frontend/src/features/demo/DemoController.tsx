"use client";

/**
 * DemoController — V4.0 (Macro Financial Intelligence)
 *
 * Right-side vertical control panel with scenario selector.
 * Enterprise neutral palette — calm, clean, no heavy accents.
 */

import React from "react";
import { motion } from "framer-motion";
import {
  Play,
  Pause,
  ChevronRight,
  ChevronLeft,
  X,
  RotateCcw,
} from "lucide-react";
import { SCENARIOS, type ScenarioId } from "./data/demo-scenario";

const STEP_LABELS = [
  "Macro State",
  "Transmission",
  "Country Exposure",
  "Banking",
  "Insurance",
  "Sector Impact",
  "Decision Panel",
  "Outcome",
  "Trust Layer",
];

const STEP_ICONS = [
  "\u25C9", // ◉ macro
  "\u21C9", // ⇉ propagation
  "\u25CB", // ○ exposure
  "\u2302", // ⌂ banking
  "\u2637", // ☷ insurance
  "\u25A3", // ▣ sectors
  "\u2691", // ⚑ decisions
  "\u2713", // ✓ outcome
  "\u2731", // ✱ trust
];

interface DemoControllerProps {
  currentStep: number;
  totalSteps: number;
  isPlaying: boolean;
  onPlay: () => void;
  onPause: () => void;
  onNext: () => void;
  onBack: () => void;
  onExit: () => void;
  onRestart: () => void;
  scenarioId: ScenarioId;
  onSwitchScenario: (id: ScenarioId) => void;
}

export function DemoController({
  currentStep,
  totalSteps,
  isPlaying,
  onPlay,
  onPause,
  onNext,
  onBack,
  onExit,
  onRestart,
  scenarioId,
  onSwitchScenario,
}: DemoControllerProps) {
  const progress = ((currentStep + 1) / totalSteps) * 100;

  return (
    <motion.div
      initial={{ x: 80, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ delay: 0.3, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
      className="fixed right-0 top-0 h-full w-[260px] bg-white border-l border-slate-200/80 z-[60] flex flex-col will-change-transform"
    >
      {/* Brand header */}
      <div className="px-5 pt-5 pb-3 border-b border-slate-100">
        <div className="flex items-center gap-2.5 mb-3">
          <div className="w-7 h-7 rounded-lg bg-slate-900 flex items-center justify-center">
            <span className="text-white font-bold text-[10px]">IO</span>
          </div>
          <div>
            <p className="text-[11px] font-bold text-slate-800 leading-tight">
              Impact Observatory
            </p>
            <p className="text-[9px] text-slate-400 font-medium">
              Macroeconomic Intelligence for the GCC
            </p>
          </div>
        </div>

        {/* Scenario selector */}
        <div className="flex gap-1 mb-3">
          {(Object.keys(SCENARIOS) as ScenarioId[]).map((id) => (
            <button
              key={id}
              onClick={() => onSwitchScenario(id)}
              className={`flex-1 px-2 py-1.5 rounded text-[9px] font-semibold transition-all duration-200 ${
                scenarioId === id
                  ? "bg-slate-900 text-white"
                  : "bg-slate-50 text-slate-400 hover:text-slate-600 hover:bg-slate-100 border border-slate-100"
              }`}
            >
              {id === "hormuz" ? "Energy & Trade" : "Financial Flow"}
            </button>
          ))}
        </div>

        {/* Progress */}
        <div className="flex items-center justify-between mb-2">
          <span className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
            Layer {currentStep + 1}/{totalSteps}
          </span>
          <span className="text-[10px] font-bold text-slate-700 tabular-nums">
            {Math.round(progress)}%
          </span>
        </div>
        <div className="h-[3px] bg-slate-100 rounded-full overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-slate-700"
            animate={{ width: `${progress}%` }}
            transition={{ duration: 0.5, ease: "easeOut" }}
          />
        </div>
      </div>

      {/* Step list */}
      <div className="flex-1 overflow-y-auto px-3 py-3">
        <div className="space-y-px">
          {STEP_LABELS.map((label, i) => {
            const isActive = i === currentStep;
            const isCompleted = i < currentStep;
            const isFuture = i > currentStep;

            return (
              <motion.div
                key={i}
                animate={{
                  backgroundColor: isActive ? "rgba(15,23,42,0.04)" : "transparent",
                }}
                transition={{ duration: 0.25 }}
                className={`flex items-center gap-2.5 px-2.5 py-[7px] rounded-lg transition-opacity ${
                  isFuture ? "opacity-35" : ""
                }`}
              >
                <div
                  className={`w-[22px] h-[22px] rounded-full flex items-center justify-center flex-shrink-0 text-[9px] font-bold transition-all duration-300 ${
                    isActive
                      ? "bg-slate-900 text-white"
                      : isCompleted
                      ? "bg-emerald-100 text-emerald-600"
                      : "bg-slate-50 text-slate-300 border border-slate-100"
                  }`}
                >
                  {isCompleted ? "\u2713" : STEP_ICONS[i]}
                </div>
                <span
                  className={`text-[11px] leading-tight ${
                    isActive
                      ? "font-bold text-slate-900"
                      : isCompleted
                      ? "font-medium text-slate-500"
                      : "font-medium text-slate-400"
                  }`}
                >
                  {label}
                </span>

                {isActive && (
                  <motion.div
                    layoutId="activeDot"
                    className="ml-auto w-1.5 h-1.5 rounded-full bg-slate-700"
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                  />
                )}
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Controls */}
      <div className="px-5 py-4 border-t border-slate-100">
        {isPlaying && (
          <div className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-slate-50 mb-3">
            <span className="relative flex h-1.5 w-1.5">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-slate-400 opacity-75" />
              <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-slate-600" />
            </span>
            <span className="text-[10px] font-semibold text-slate-600">
              Auto-playing
            </span>
          </div>
        )}

        <div className="flex items-center justify-center gap-1.5">
          <button
            onClick={onBack}
            disabled={currentStep === 0}
            className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-25 disabled:cursor-not-allowed transition-all"
            aria-label="Previous layer"
          >
            <ChevronLeft size={16} />
          </button>

          <button
            onClick={isPlaying ? onPause : onPlay}
            className="w-11 h-11 rounded-xl bg-slate-900 text-white flex items-center justify-center hover:bg-slate-800 active:scale-95 transition-all"
            aria-label={isPlaying ? "Pause" : "Play"}
          >
            {isPlaying ? (
              <Pause size={18} strokeWidth={2.5} />
            ) : (
              <Play size={18} strokeWidth={2.5} className="ml-0.5" />
            )}
          </button>

          <button
            onClick={onNext}
            disabled={currentStep >= totalSteps - 1}
            className="w-9 h-9 rounded-lg bg-slate-50 border border-slate-200 flex items-center justify-center text-slate-500 hover:bg-slate-100 hover:text-slate-700 disabled:opacity-25 disabled:cursor-not-allowed transition-all"
            aria-label="Next layer"
          >
            <ChevronRight size={16} />
          </button>
        </div>

        <div className="flex items-center justify-center gap-3 mt-2.5">
          <button
            onClick={onRestart}
            className="flex items-center gap-1 px-2 py-1.5 rounded text-[10px] font-medium text-slate-400 hover:text-slate-600 hover:bg-slate-50 transition-all"
          >
            <RotateCcw size={10} />
            Restart
          </button>
          <button
            onClick={onExit}
            className="flex items-center gap-1 px-2 py-1.5 rounded text-[10px] font-medium text-slate-400 hover:text-red-500 hover:bg-red-50 transition-all"
          >
            <X size={10} />
            Exit
          </button>
        </div>

        <div className="flex items-center justify-center gap-2 mt-3 pt-3 border-t border-slate-50">
          <kbd className="px-1.5 py-0.5 rounded bg-slate-50 text-[8px] font-mono text-slate-400 border border-slate-100">
            Space
          </kbd>
          <kbd className="px-1.5 py-0.5 rounded bg-slate-50 text-[8px] font-mono text-slate-400 border border-slate-100">
            &larr; &rarr;
          </kbd>
          <kbd className="px-1.5 py-0.5 rounded bg-slate-50 text-[8px] font-mono text-slate-400 border border-slate-100">
            Esc
          </kbd>
        </div>
      </div>
    </motion.div>
  );
}
