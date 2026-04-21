"use client";

/**
 * /demo — Executive Demo Mode
 *
 * Full-screen, autoplay narrative walkthrough of Impact Observatory.
 * Curated scenario: Strait of Hormuz Partial Blockage.
 *
 * Controls: Play/Pause/Next/Back/Exit via right panel or keyboard.
 * Keyboard: Arrow keys (navigate), Space (play/pause), Escape (exit).
 */

import React, { useState, useEffect } from "react";
import dynamic from "next/dynamic";
import { Play, ArrowRight } from "lucide-react";

// Lazy-load DemoOverlay to avoid blank flash while heavy JS loads
const DemoOverlay = dynamic(
  () => import("@/features/demo/DemoOverlay").then((m) => ({ default: m.DemoOverlay })),
  {
    ssr: false,
    loading: () => <DemoLoader />,
  },
);

/** Lightweight brand-mark loader — prevents blank white screen */
function DemoLoader() {
  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col items-center justify-center gap-5">
      {/* Pulsing IO mark */}
      <div className="animate-pulse">
        <div className="w-14 h-14 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center">
          <div className="w-7 h-7 rounded-lg bg-[#1B1B19] flex items-center justify-center">
            <span className="text-white font-bold text-[10px]">IO</span>
          </div>
        </div>
      </div>
      <p className="text-xs text-slate-400 font-medium tracking-wide">
        Loading demo&hellip;
      </p>
    </div>
  );
}

export default function DemoPage() {
  const [demoStarted, setDemoStarted] = useState(false);
  const [ready, setReady] = useState(false);

  // Brief mount delay so the landing never flashes blank
  useEffect(() => {
    const t = setTimeout(() => setReady(true), 80);
    return () => clearTimeout(t);
  }, []);

  if (!ready) return <DemoLoader />;

  if (demoStarted) {
    return <DemoOverlay onExit={() => setDemoStarted(false)} />;
  }

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-8">
      {/* Pre-demo landing */}
      <div className="text-center max-w-xl">
        {/* Logo / badge */}
        <div className="mb-8 flex justify-center">
          <div className="w-16 h-16 rounded-2xl bg-slate-100 border border-slate-200 flex items-center justify-center">
            <div className="w-8 h-8 rounded-lg bg-[#1B1B19] flex items-center justify-center">
              <span className="text-white font-bold text-sm">IO</span>
            </div>
          </div>
        </div>

        <h1 className="text-h1 md:text-display-sm text-slate-900 mb-4">
          GCC Economic Macro
        </h1>

        <p className="text-body-lg text-slate-500 mb-2">
          From Signal to Economic Decisions
        </p>

        <p className="text-sm text-slate-400 mb-12" dir="rtl">
          من الإشارة إلى القرارات الاقتصادية
        </p>

        {/* Start button */}
        <button
          onClick={() => setDemoStarted(true)}
          className="group inline-flex items-center gap-3 px-8 py-4 bg-[#1B1B19] text-white rounded-xl font-semibold text-sm shadow-lg hover:bg-[#2C2C2A] hover:shadow-xl transition-all"
        >
          <Play size={18} />
          <span>
            Start Executive Demo
            <span className="block text-[11px] font-normal text-white/60 leading-none mt-0.5">
              ابدأ العرض التنفيذي
            </span>
          </span>
          <ArrowRight
            size={16}
            className="group-hover:translate-x-1 transition-transform"
          />
        </button>

        {/* Keyboard hint */}
        <div className="mt-8 flex items-center justify-center gap-4">
          <KeyHint label="Space" description="Play / Pause" />
          <KeyHint label="Arrow keys" description="Navigate" />
          <KeyHint label="Esc" description="Exit" />
        </div>
      </div>
    </div>
  );
}

function KeyHint({ label, description }: { label: string; description: string }) {
  return (
    <div className="flex items-center gap-2">
      <kbd className="px-2 py-1 rounded bg-slate-100 border border-slate-200 text-[10px] font-mono font-semibold text-slate-500">
        {label}
      </kbd>
      <span className="text-[11px] text-slate-400">{description}</span>
    </div>
  );
}
