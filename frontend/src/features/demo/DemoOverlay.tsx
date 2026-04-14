"use client";

/**
 * DemoOverlay — Executive Demo Experience
 *
 * Navigates directly to the Command Center intelligence flow.
 * The Command Center IS the executive demo — no separate walkthrough needed.
 */

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export function DemoOverlay({ onExit }: { onExit?: () => void }) {
  const router = useRouter();

  useEffect(() => {
    // Navigate to Command Center in demo mode — the full intelligence demo surface
    router.push("/command-center?demo=true");
  }, [router]);

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
        Loading Intelligence Flow&hellip;
      </p>
    </div>
  );
}
