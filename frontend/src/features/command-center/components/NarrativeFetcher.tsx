"use client";

/**
 * NarrativeFetcher — Self-fetching wrapper for NarrativePanel.
 *
 * When mounted (tab becomes active), calls POST /api/v1/narrative/run
 * with the current scenario parameters. Caches result for the session.
 *
 * Isolation: Does NOT alter the existing data pipeline or store.
 * Additive only — fetches narrative layer independently.
 */

import React, { useState, useEffect, useRef } from "react";
import { NarrativePanel, type NarrativeData } from "./NarrativePanel";
import { api } from "@/lib/api";

interface NarrativeFetcherProps {
  scenarioId: string;
  severity: number;
  horizonHours: number;
  language?: "en" | "ar";
}

export function NarrativeFetcher({
  scenarioId,
  severity,
  horizonHours,
  language = "en",
}: NarrativeFetcherProps) {
  const [narrative, setNarrative] = useState<NarrativeData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fetchedRef = useRef<string | null>(null);

  // Cache key: scenario+severity+horizon
  const cacheKey = `${scenarioId}-${severity}-${horizonHours}`;

  useEffect(() => {
    if (fetchedRef.current === cacheKey) return;

    let cancelled = false;
    setLoading(true);
    setError(null);

    api.narrative
      .run({
        scenario_id: scenarioId,
        severity,
        horizon_hours: horizonHours,
        language,
      })
      .then((res) => {
        if (cancelled) return;
        fetchedRef.current = cacheKey;
        setNarrative(res.narrative as NarrativeData);
        setLoading(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setError(err?.message ?? "Failed to generate narrative");
        setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [cacheKey, scenarioId, severity, horizonHours, language]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3">
        <div className="w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        <p className="text-[11px] text-slate-500">Generating intelligence brief...</p>
        <p className="text-[10px] text-slate-600">Signal → Propagation → Exposure → Decision → Outcome</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-2 text-center px-6">
        <div className="w-8 h-8 rounded-lg bg-amber-500/10 border border-amber-500/20 flex items-center justify-center">
          <span className="text-amber-500 text-sm">!</span>
        </div>
        <p className="text-[11px] text-amber-400">{error}</p>
        <p className="text-[10px] text-slate-600">
          The narrative layer is optional — all simulation data remains available in other tabs.
        </p>
      </div>
    );
  }

  return <NarrativePanel narrative={narrative} language={language} />;
}
