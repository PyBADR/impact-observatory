"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { scenarioCatalog, getScenarioById } from "./data";
import type { DemoData } from "./data";
import { MacroHero } from "./components/MacroHero";
import { TransmissionFlow } from "./components/TransmissionFlow";
import { ExposureLayer } from "./components/ExposureLayer";
import { DecisionEngine } from "./components/DecisionEngine";
import { Outcome } from "./components/Outcome";
import { TrustStrip } from "./components/TrustStrip";
import { ScenarioSelector } from "./components/ScenarioSelector";

/**
 * MacroIntelligenceDemoView — Multi-Scenario Presenter Edition
 *
 * Two-phase UX:
 *   Phase 1 — SELECTOR   Presenter picks a GCC scenario from the catalog
 *   Phase 2 — NARRATIVE   Auto-play cinematic demo with presenter controls
 *
 * Sequence: Selector → Shock → Transmission → Exposure → Decision → Highlight → Outcome → Trust
 *
 * Keyboard:
 *   ArrowRight    → next step
 *   ArrowLeft     → previous step
 *   Space         → toggle pause/resume auto-play
 *   R             → replay current scenario
 *   S             → return to scenario selector
 *   H             → toggle presenter overlay
 *   1-9           → jump to scenario by index (in selector phase)
 */

// ─── Constants ──────────────────────────────────────────────────────────────

const MAX_STEP = 6;
const STEP_INTERVAL_MS = 2000;
const DEBOUNCE_MS = 180;

const STEP_LABELS = [
  "Shock",
  "Transmission",
  "Exposure",
  "Decisions",
  "Highlight",
  "Outcome",
  "Trust",
] as const;

type Phase = "selector" | "narrative";

// ─── Component ──────────────────────────────────────────────────────────────

export function MacroIntelligenceDemoView() {
  // ── Scenario state ─────────────────────────────────────────────────────
  const [phase, setPhase] = useState<Phase>("selector");
  const [activeScenarioId, setActiveScenarioId] = useState(
    scenarioCatalog[0].meta.id
  );
  const activeScenario = getScenarioById(activeScenarioId);
  const data: DemoData = activeScenario.data;

  // ── Narrative state ────────────────────────────────────────────────────
  const [step, setStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [overlayVisible, setOverlayVisible] = useState(true);

  // Debounce guard
  const lastActionRef = useRef(0);
  const canAct = useCallback(() => {
    const now = Date.now();
    if (now - lastActionRef.current < DEBOUNCE_MS) return false;
    lastActionRef.current = now;
    return true;
  }, []);

  // ── Scenario selection ─────────────────────────────────────────────────

  const selectScenario = useCallback(
    (id: string) => {
      setActiveScenarioId(id);
      // Don't auto-launch — let presenter confirm
    },
    []
  );

  const launchNarrative = useCallback(() => {
    setStep(0);
    setIsPlaying(true);
    setPhase("narrative");
  }, []);

  const returnToSelector = useCallback(() => {
    setIsPlaying(false);
    setStep(0);
    setPhase("selector");
  }, []);

  // ── Step navigation ────────────────────────────────────────────────────

  const goNext = useCallback(() => {
    if (!canAct()) return;
    setStep((s) => {
      if (s >= MAX_STEP) {
        setIsPlaying(false);
        return s;
      }
      return s + 1;
    });
  }, [canAct]);

  const goBack = useCallback(() => {
    if (!canAct()) return;
    setStep((s) => Math.max(0, s - 1));
    setIsPlaying(false);
  }, [canAct]);

  const replay = useCallback(() => {
    if (!canAct()) return;
    setStep(0);
    setIsPlaying(true);
  }, [canAct]);

  const togglePlay = useCallback(() => {
    if (!canAct()) return;
    setIsPlaying((p) => {
      if (!p && step >= MAX_STEP) {
        setStep(0);
        return true;
      }
      return !p;
    });
  }, [canAct, step]);

  // ── Interval-based auto-play ───────────────────────────────────────────

  useEffect(() => {
    if (!isPlaying || phase !== "narrative") return;

    const id = setInterval(() => {
      setStep((s) => {
        if (s >= MAX_STEP) {
          setIsPlaying(false);
          return s;
        }
        return s + 1;
      });
    }, STEP_INTERVAL_MS);

    return () => clearInterval(id);
  }, [isPlaying, phase]);

  // ── Keyboard controls ──────────────────────────────────────────────────

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      )
        return;

      // ── Selector-phase keys ─────────────────────────────────────────
      if (phase === "selector") {
        if (e.key === "Enter") {
          e.preventDefault();
          launchNarrative();
          return;
        }
        // Number keys 1-9 → quick-select by index
        const num = parseInt(e.key, 10);
        if (num >= 1 && num <= Math.min(9, scenarioCatalog.length)) {
          e.preventDefault();
          selectScenario(scenarioCatalog[num - 1].meta.id);
          return;
        }
        return;
      }

      // ── Narrative-phase keys ────────────────────────────────────────
      switch (e.key) {
        case "ArrowRight":
          e.preventDefault();
          goNext();
          break;
        case "ArrowLeft":
          e.preventDefault();
          goBack();
          break;
        case " ":
          e.preventDefault();
          togglePlay();
          break;
        case "r":
        case "R":
          e.preventDefault();
          replay();
          break;
        case "s":
        case "S":
          e.preventDefault();
          returnToSelector();
          break;
        case "h":
        case "H":
          e.preventDefault();
          setOverlayVisible((v) => !v);
          break;
      }
    }

    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [
    phase,
    goNext,
    goBack,
    togglePlay,
    replay,
    launchNarrative,
    returnToSelector,
    selectScenario,
  ]);

  // ── Render helpers ─────────────────────────────────────────────────────

  const show = (threshold: number) => step >= threshold;

  return (
    <div className="relative min-h-screen bg-[#0A0E17] text-white overflow-hidden select-none">
      {/* Subtle grid texture */}
      <div
        className="fixed inset-0 pointer-events-none opacity-[0.03]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.05) 1px, transparent 1px)",
          backgroundSize: "60px 60px",
        }}
      />

      {/* Gradient vignette */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse 80% 60% at 50% 0%, rgba(30,58,138,0.08) 0%, transparent 60%)",
        }}
      />

      {/* ════════════════════════════════════════════════════════════════ */}
      {/* PHASE: SELECTOR                                                 */}
      {/* ════════════════════════════════════════════════════════════════ */}
      <AnimatePresence mode="wait">
        {phase === "selector" && (
          <motion.div
            key="selector-phase"
            className="relative z-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0, y: -20 }}
            transition={{ duration: 0.4 }}
          >
            <ScenarioSelector
              scenarios={scenarioCatalog}
              activeId={activeScenarioId}
              onSelect={selectScenario}
            />

            {/* Launch button — fixed bottom center */}
            <motion.div
              className="fixed bottom-8 left-1/2 -translate-x-1/2 z-50"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.5 }}
            >
              <button
                onClick={launchNarrative}
                className="
                  group flex items-center gap-3 px-8 py-3.5 rounded-full
                  bg-white/[0.06] border border-white/[0.1]
                  hover:bg-white/[0.1] hover:border-white/[0.2]
                  transition-all duration-300 cursor-pointer
                "
              >
                <svg
                  width="18"
                  height="18"
                  viewBox="0 0 24 24"
                  fill="currentColor"
                  className="text-white/70 group-hover:text-white transition-colors"
                >
                  <polygon points="5 3 19 12 5 21" />
                </svg>
                <span className="text-sm font-medium text-slate-300 group-hover:text-white transition-colors">
                  Launch{" "}
                  <span className="text-white font-semibold">
                    {activeScenario.meta.name}
                  </span>
                </span>
                <kbd className="text-[10px] text-slate-600 bg-white/[0.04] px-1.5 py-0.5 rounded border border-white/[0.06]">
                  Enter
                </kbd>
              </button>
            </motion.div>
          </motion.div>
        )}

        {/* ════════════════════════════════════════════════════════════════ */}
        {/* PHASE: NARRATIVE                                                */}
        {/* ════════════════════════════════════════════════════════════════ */}
        {phase === "narrative" && (
          <motion.div
            key={`narrative-${activeScenarioId}`}
            className="relative z-10"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.4 }}
          >
            {/* Back to selector — top left */}
            <motion.button
              className="
                fixed top-5 left-5 z-50 flex items-center gap-2
                text-xs text-slate-600 hover:text-slate-300
                transition-colors duration-200 cursor-pointer
              "
              onClick={returnToSelector}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.8, duration: 0.5 }}
              title="S — return to scenarios"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              >
                <polyline points="15 18 9 12 15 6" />
              </svg>
              Scenarios
            </motion.button>

            {/* Narrative sections */}
            <AnimatePresence mode="sync">
              {show(0) && (
                <motion.div
                  key="hero"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <MacroHero shock={data.shock} />
                </motion.div>
              )}

              {show(1) && (
                <motion.div
                  key="transmission"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <TransmissionFlow nodes={data.transmission} />
                </motion.div>
              )}

              {show(2) && (
                <motion.div
                  key="exposure"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <ExposureLayer entries={data.exposure} />
                </motion.div>
              )}

              {show(3) && (
                <motion.div
                  key="decisions"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <DecisionEngine
                    decisions={data.decisions}
                    highlightBest={show(4)}
                  />
                </motion.div>
              )}

              {show(5) && (
                <motion.div
                  key="outcome"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <Outcome outcome={data.outcome} />
                </motion.div>
              )}

              {show(6) && (
                <motion.div
                  key="trust"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ duration: 0.3 }}
                >
                  <TrustStrip trust={data.trust} />
                </motion.div>
              )}
            </AnimatePresence>

            {/* ── Progress dots ─────────────────────────────────────────── */}
            <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50 flex items-center gap-2">
              {STEP_LABELS.map((label, i) => (
                <button
                  key={label}
                  onClick={() => {
                    if (!canAct()) return;
                    setStep(i);
                    setIsPlaying(false);
                  }}
                  className="group relative flex items-center cursor-pointer"
                  aria-label={`Go to step: ${label}`}
                >
                  <motion.div
                    className="rounded-full transition-all duration-500"
                    style={{
                      width: step === i ? 24 : 6,
                      height: 6,
                      background:
                        step >= i
                          ? step === i
                            ? "rgba(255,255,255,0.8)"
                            : "rgba(255,255,255,0.4)"
                          : "rgba(255,255,255,0.1)",
                    }}
                    layout
                  />
                  <span className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-2 py-1 text-[10px] font-medium text-slate-300 bg-slate-800/90 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity duration-200 pointer-events-none">
                    {label}
                  </span>
                </button>
              ))}
            </div>

            {/* ── Presenter overlay ─────────────────────────────────────── */}
            <AnimatePresence>
              {overlayVisible && (
                <motion.div
                  className="fixed bottom-6 right-6 z-50"
                  initial={{ opacity: 0, y: 12 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: 12 }}
                  transition={{ duration: 0.3, ease: "easeOut" }}
                >
                  <div
                    className="flex items-center gap-1 px-2 py-1.5 rounded-xl border border-white/[0.06] backdrop-blur-md"
                    style={{ background: "rgba(10,14,23,0.85)" }}
                  >
                    <OverlayButton
                      onClick={goBack}
                      disabled={step <= 0}
                      aria-label="Previous step"
                      title="← Back"
                    >
                      <ChevronLeft />
                    </OverlayButton>

                    <OverlayButton
                      onClick={togglePlay}
                      aria-label={isPlaying ? "Pause" : "Play"}
                      title="Space"
                    >
                      {isPlaying ? <PauseIcon /> : <PlayIcon />}
                    </OverlayButton>

                    <OverlayButton
                      onClick={goNext}
                      disabled={step >= MAX_STEP}
                      aria-label="Next step"
                      title="→ Next"
                    >
                      <ChevronRight />
                    </OverlayButton>

                    <div className="w-px h-4 bg-white/[0.06] mx-1" />

                    <OverlayButton
                      onClick={replay}
                      aria-label="Replay"
                      title="R"
                    >
                      <ReplayIcon />
                    </OverlayButton>

                    <OverlayButton
                      onClick={returnToSelector}
                      aria-label="Scenarios"
                      title="S"
                    >
                      <GridIcon />
                    </OverlayButton>

                    <div className="w-px h-4 bg-white/[0.06] mx-1" />

                    <span className="text-[11px] font-mono text-slate-500 pl-1 pr-2 tabular-nums min-w-[52px] text-center">
                      {step + 1} / {MAX_STEP + 1}
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Keyboard hints (top-right, auto-fade) ─────────────────────── */}
      <KeyboardHints phase={phase} />
    </div>
  );
}

// ─── Internal sub-components ────────────────────────────────────────────────

interface OverlayButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

function OverlayButton({ children, disabled, ...props }: OverlayButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled}
      className={`
        w-8 h-8 flex items-center justify-center rounded-lg
        transition-all duration-200 cursor-pointer
        ${
          disabled
            ? "text-slate-700 cursor-not-allowed"
            : "text-slate-400 hover:text-white hover:bg-white/[0.06]"
        }
      `}
    >
      {children}
    </button>
  );
}

function KeyboardHints({ phase }: { phase: Phase }) {
  const [visible, setVisible] = useState(true);

  useEffect(() => {
    setVisible(true);
    const timer = setTimeout(() => setVisible(false), 5000);
    return () => clearTimeout(timer);
  }, [phase]);

  return (
    <AnimatePresence>
      {visible && (
        <motion.div
          className="fixed top-5 right-5 z-50"
          initial={{ opacity: 0, y: -8 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.4 }}
        >
          <div
            className="px-3 py-2.5 rounded-lg border border-white/[0.04] text-[10px] leading-relaxed text-slate-600 space-y-0.5"
            style={{ background: "rgba(10,14,23,0.7)" }}
          >
            {phase === "selector" ? (
              <>
                <div>
                  <kbd className="text-slate-400">1</kbd>–
                  <kbd className="text-slate-400">9</kbd> quick select
                </div>
                <div>
                  <kbd className="text-slate-400">Enter</kbd> launch scenario
                </div>
              </>
            ) : (
              <>
                <div>
                  <kbd className="text-slate-400">←</kbd>{" "}
                  <kbd className="text-slate-400">→</kbd> navigate
                </div>
                <div>
                  <kbd className="text-slate-400">Space</kbd> pause / resume
                </div>
                <div>
                  <kbd className="text-slate-400">R</kbd> replay
                </div>
                <div>
                  <kbd className="text-slate-400">S</kbd> scenarios
                </div>
                <div>
                  <kbd className="text-slate-400">H</kbd> toggle controls
                </div>
              </>
            )}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// ─── Icons (inline SVG, zero deps) ─────────────────────────────────────────

function ChevronLeft() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="15 18 9 12 15 6" />
    </svg>
  );
}

function ChevronRight() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="9 18 15 12 9 6" />
    </svg>
  );
}

function PlayIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <polygon points="5 3 19 12 5 21" />
    </svg>
  );
}

function PauseIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
      <rect x="6" y="4" width="4" height="16" rx="1" />
      <rect x="14" y="4" width="4" height="16" rx="1" />
    </svg>
  );
}

function ReplayIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <polyline points="1 4 1 10 7 10" />
      <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10" />
    </svg>
  );
}

function GridIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <rect x="3" y="3" width="7" height="7" />
      <rect x="14" y="3" width="7" height="7" />
      <rect x="3" y="14" width="7" height="7" />
      <rect x="14" y="14" width="7" height="7" />
    </svg>
  );
}
