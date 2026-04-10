"use client";

/**
 * StorySequenceWrapper — Orchestrates the macro-to-decision story flow
 *
 * Wraps the existing results view with the story layer:
 *   1. IntelligenceHeader  — product positioning + story flow indicator
 *   2. MacroShockStrip     — what changed in the world
 *   3. TransmissionStory   — how impact propagates
 *   4. SectorImpactStory   — which sectors absorb the shock
 *   5. [children]          — existing portfolio / decision / action views
 *
 * This is ADDITIVE ONLY. It does not replace or modify any existing
 * components. It wraps them with narrative context.
 */

import React from "react";
import { IntelligenceHeader } from "./IntelligenceHeader";
import { MacroShockStrip } from "./MacroShockStrip";
import { TransmissionStoryPanel } from "./TransmissionStoryPanel";
import { SectorImpactStory } from "./SectorImpactStory";
import type { RunResult, Language } from "@/types/observatory";

interface StorySequenceWrapperProps {
  result: RunResult;
  lang?: Language;
  children: React.ReactNode;
}

export function StorySequenceWrapper({
  result,
  lang = "en",
  children,
}: StorySequenceWrapperProps) {
  return (
    <div className="w-full">
      {/* ── Layer 1: Intelligence Header — product framing ── */}
      <IntelligenceHeader result={result} lang={lang} />

      {/* ── Layer 2: Macro Shock — what changed ── */}
      <MacroShockStrip result={result} lang={lang} />

      {/* ── Layer 3: Transmission — how it propagates ── */}
      <TransmissionStoryPanel result={result} lang={lang} />

      {/* ── Layer 4: Sector Impact — who is hit ── */}
      <SectorImpactStory result={result} lang={lang} />

      {/* ── Layer 5+6: Portfolio Exposure + Decision + Action ── */}
      {/* These are the existing views, passed through unchanged */}
      {children}
    </div>
  );
}
