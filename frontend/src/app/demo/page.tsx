"use client";

/**
 * /demo — Executive Demo Landing
 *
 * Brand-forward landing page for Impact Observatory.
 * Clicking "Start Executive Demo" navigates to the Command Center —
 * the full intelligence flow IS the demo experience.
 */

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Play, ArrowRight } from "lucide-react";

/** Lightweight brand-mark loader — prevents blank white screen */
function DemoLoader() {
  return (
    <div className="fixed inset-0 z-50 bg-white flex flex-col items-center justify-center gap-5">
      <div className="animate-pulse">
        <div className="w-14 h-14 rounded-2xl bg-io-accent-dim border border-io-accent/15 flex items-center justify-center">
          <div className="w-7 h-7 rounded-lg bg-io-accent flex items-center justify-center">
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
  const router = useRouter();
  const [ready, setReady] = useState(false);

  // Brief mount delay so the landing never flashes blank
  useEffect(() => {
    const t = setTimeout(() => setReady(true), 80);
    return () => clearTimeout(t);
  }, []);

  if (!ready) return <DemoLoader />;

  return (
    <div className="min-h-screen bg-white flex flex-col items-center justify-center px-8">
      {/* Pre-demo landing */}
      <div className="text-center max-w-xl">
        {/* Logo / badge */}
        <div className="mb-8 flex justify-center">
          <div className="w-16 h-16 rounded-2xl bg-io-accent-dim border border-io-accent/15 flex items-center justify-center">
            <div className="w-8 h-8 rounded-lg bg-io-accent flex items-center justify-center">
              <span className="text-white font-bold text-sm">IO</span>
            </div>
          </div>
        </div>

        <h1 className="text-h1 md:text-display-sm text-slate-900 mb-4">
          GCC Macro Financial Intelligence
        </h1>

        <p className="text-body-lg text-slate-500 mb-2">
          Institutional Intelligence & Decision Platform
        </p>

        <p className="text-sm text-slate-400 mb-12">
          منصة الاستخبارات الاقتصادية والمالية لدول الخليج
        </p>

        {/* Start button — navigates to Command Center */}
        <button
          onClick={() => router.push("/command-center?demo=true")}
          className="group inline-flex items-center gap-3 px-8 py-4 bg-io-primary text-white rounded-xl font-semibold text-sm shadow-lg shadow-io-primary/20 hover:bg-io-accent hover:shadow-xl hover:shadow-io-accent/20 transition-all"
        >
          <Play size={18} />
          Start Executive Demo
          <ArrowRight
            size={16}
            className="group-hover:translate-x-1 transition-transform"
          />
        </button>

        {/* Navigation hint */}
        <div className="mt-8 flex items-center justify-center gap-4">
          <KeyHint label="Tabs" description="Navigate flow" />
          <KeyHint label="Scenarios" description="Switch scenarios" />
          <KeyHint label="EN/AR" description="Toggle language" />
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
