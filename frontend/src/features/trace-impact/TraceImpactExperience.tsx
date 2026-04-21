"use client";

import { useEffect, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { useTraceImpactStore, TOTAL_STEPS } from "./store/trace-impact-store";
import { makeSlideVariants, STEP_TRANSITION } from "./lib/transitions";
import { TraceImpactProvider } from "./lib/trace-impact-context";
import { NarrativeStrip } from "./components/NarrativeStrip";
import { StepChrome } from "./components/StepChrome";
import { MacroEntryStep } from "./steps/00-MacroEntryStep";
import { ShockStep } from "./steps/01-ShockStep";
import { PropagationStep } from "./steps/02-PropagationStep";
import { ExposureStep } from "./steps/03-ExposureStep";
import { DecisionSplitStep } from "./steps/04-DecisionSplitStep";
import { OutcomeStep } from "./steps/05-OutcomeStep";
import { useRouter, useSearchParams } from "next/navigation";
import type { Locale } from "@/i18n/dictionary";
import type { CommandCenterHeadline } from "@/features/command-center/lib/command-store";
import type { ScenarioId } from "@/features/demo/data/demo-scenario";

interface TraceImpactExperienceProps {
  locale: Locale;
  runId?: string | null;
  headline?: CommandCenterHeadline | null;
  /** Optional scenario override — defaults to hormuz */
  scenarioId?: ScenarioId | null;
}

function renderStep(stepIndex: number, locale: Locale, headline?: CommandCenterHeadline | null) {
  switch (stepIndex) {
    case 0:
      // NEW — Macro Entry: signal → interpretation → why elevated
      return <MacroEntryStep locale={locale} />;
    case 1:
      return (
        <ShockStep
          locale={locale}
          totalLossUsd={headline?.totalLossUsd ?? null}
        />
      );
    case 2:
      return <PropagationStep locale={locale} />;
    case 3:
      return <ExposureStep locale={locale} />;
    case 4:
      return <DecisionSplitStep locale={locale} />;
    case 5:
      return <OutcomeStep locale={locale} />;
    default:
      return null;
  }
}

export function TraceImpactExperience({
  locale,
  headline,
  scenarioId,
}: TraceImpactExperienceProps) {
  const { stepIndex, next, prev, reset } = useTraceImpactStore();
  const prevStepRef = useRef(stepIndex);
  const isAr = locale === "ar";
  const router = useRouter();
  const searchParams = useSearchParams();

  // Reset step to 0 on mount
  useEffect(() => {
    reset();
  }, [reset]);

  // Track direction for slide animation
  const direction = stepIndex > prevStepRef.current ? 1 : -1;
  useEffect(() => {
    prevStepRef.current = stepIndex;
  }, [stepIndex]);

  // Keyboard navigation
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      if (e.key === "ArrowRight") {
        isAr ? prev() : next();
      } else if (e.key === "ArrowLeft") {
        isAr ? next() : prev();
      }
    };
    window.addEventListener("keydown", handleKey);
    return () => window.removeEventListener("keydown", handleKey);
  }, [isAr, next, prev]);

  const slideVariants = makeSlideVariants(isAr ? "rtl" : "ltr");

  const handleFinish = () => {
    const params = new URLSearchParams();
    params.set("tab", "decisions");
    const runId = searchParams.get("run");
    if (runId) params.set("run", runId);
    router.push(`/command-center?${params.toString()}`);
  };

  return (
    <TraceImpactProvider scenarioId={scenarioId}>
      <div
        className={`flex flex-col h-full bg-io-bg ${isAr ? "rtl" : "ltr"}`}
        dir={isAr ? "rtl" : "ltr"}
      >
        {/* Narrative strip — sticky at top */}
        <NarrativeStrip stepIndex={stepIndex} locale={locale} />

        {/* Step content — scrollable */}
        <div className="flex-1 overflow-y-auto">
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={stepIndex}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={STEP_TRANSITION}
            >
              {renderStep(stepIndex, locale, headline)}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Step chrome — sticky at bottom */}
        <StepChrome
          stepIndex={stepIndex}
          locale={locale}
          onPrev={prev}
          onNext={next}
          onFinish={handleFinish}
        />
      </div>
    </TraceImpactProvider>
  );
}
