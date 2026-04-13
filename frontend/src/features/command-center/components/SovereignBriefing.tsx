"use client";

/**
 * SovereignBriefing — 5-Block Executive Command Surface
 *
 * Block 1: CURRENT STATE — what is happening
 * Block 2: DOMINANT SIGNAL — where pressure is concentrated
 * Block 3: HOW PRESSURE SPREADS — causal transmission
 * Block 4: EXECUTIVE DECISION — what must be done
 * Block 5: MONITORING AND CONSEQUENCE — who owns it
 *
 * No extra blocks. No tabs. No equal-weight sections.
 * One focal point per block. Strong contrast. Command feel.
 */

import React from "react";
import type {
  SovereignBriefing as SovereignBriefingType,
} from "@/lib/intelligence/sovereignBriefingEngine";

/* ═══════════════════════════════════════════════════════════════════════
 * Block 1: CURRENT STATE
 * What is happening. GCC posture. Top stress. Required decision now.
 * ═══════════════════════════════════════════════════════════════════════ */

function CurrentStateBlock({ briefing }: { briefing: SovereignBriefingType }) {
  const topExposures = briefing.macroExposures.slice(0, 3);
  const topCountries = [...new Set(topExposures.map(e => e.country))].slice(0, 3);
  const topSector = topExposures[0]?.sector ?? "—";
  const primaryDirective = briefing.directives[0];

  return (
    <section className="mb-2">
      {/* Posture headline — the single dominant focal point */}
      <h2 className="text-[1.375rem] sm:text-[1.625rem] font-bold text-[#1d1d1f] leading-tight tracking-tight mb-5">
        {briefing.macro.posture}
      </h2>

      {/* Advisory — the context sentence */}
      <p className="text-[0.9375rem] text-[#515154] leading-[1.75] mb-6">
        {briefing.macro.advisory}
      </p>

      {/* Key facts — prose, not grid */}
      <p className="text-[0.8125rem] text-[#6e6e73] leading-[1.75]">
        {briefing.temporalHorizon.now.split('.')[0]}.
        {topCountries.length > 0 && (
          <> Top stress in {topCountries.join(', ')} — primary sector: {topSector}.</>
        )}
        {primaryDirective && (
          <> Required now: <span className="text-[#0071e3] font-semibold">{primaryDirective.directive.split('.')[0]}</span>.</>
        )}
        {!primaryDirective && (
          <> Monitoring posture — no binding directive.</>
        )}
      </p>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Block 2: DOMINANT SIGNAL
 * What signal dominates. Why. Runner-up in diminished form.
 * ═══════════════════════════════════════════════════════════════════════ */

function DominantSignalBlock({ briefing }: { briefing: SovereignBriefingType }) {
  const signal = briefing.signal;

  return (
    <section>
      {/* Dominant signal — large, unmissable */}
      <p className="text-[1.125rem] font-bold text-[#1d1d1f] leading-snug mb-2">
        {signal.dominantSignal}
      </p>

      {/* Intensity marker */}
      {signal.dominantType && (
        <p className="text-[0.75rem] text-[#0071e3] font-semibold tracking-wide uppercase mb-4">
          {signal.dominantType} · {Math.round(signal.dominantIntensity * 100)}% intensity
        </p>
      )}

      {/* Why it dominates — one sentence */}
      <p className="text-[0.875rem] text-[#515154] leading-[1.75] mb-5">
        {signal.selectionBasis}
      </p>

      {/* Runner-up — deliberately smaller */}
      {signal.secondSignal && (
        <div className="border-l-2 border-[#e5e5e7] pl-5">
          <p className="text-[0.8125rem] text-[#6e6e73] leading-relaxed">
            Runner-up: {signal.secondSignal}
            <span className="text-[#6e6e73] ml-2">
              · {signal.secondType} · {Math.round(signal.secondIntensity * 100)}%
            </span>
          </p>
        </div>
      )}
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Block 3: HOW PRESSURE SPREADS
 * 3-4 steps. Plain prose. No containers. No dead space.
 * ═══════════════════════════════════════════════════════════════════════ */

function PressureSpreadsBlock({ briefing }: { briefing: SovereignBriefingType }) {
  const steps = briefing.propagation.slice(0, 4);

  if (steps.length === 0) {
    return (
      <section>
        <p className="text-[0.875rem] text-[#6e6e73]">
          No propagation chain detected at current scenario progress.
        </p>
      </section>
    );
  }

  return (
    <section className="space-y-5">
      {steps.map((step) => (
        <div key={step.stepNumber} className="flex gap-4">
          <span className="text-[0.875rem] font-bold text-[#0071e3] tabular-nums flex-shrink-0 w-5 text-right">
            {step.stepNumber}.
          </span>
          <p className="text-[0.875rem] text-[#515154] leading-[1.75]">
            {step.prose}
          </p>
        </div>
      ))}
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Block 4: EXECUTIVE DECISION
 * One dominant directive. Max 2 supporting. Owner. Urgency. Consequence.
 * ═══════════════════════════════════════════════════════════════════════ */

function ExecutiveDecisionBlock({ briefing }: { briefing: SovereignBriefingType }) {
  const directives = briefing.directives;

  if (directives.length === 0) {
    return (
      <section>
        <p className="text-[0.875rem] text-[#6e6e73]">
          No active directives. System in monitoring posture.
        </p>
      </section>
    );
  }

  const primary = directives[0];
  const supporting = directives.slice(1, 3);

  return (
    <section>
      {/* Primary directive — the dominant visual element */}
      <div className="mb-8">
        <p className="text-[1.0625rem] font-bold text-[#1d1d1f] leading-snug mb-3">
          {primary.directive}
        </p>

        {/* Owner and urgency — visible, not buried */}
        <div className="flex flex-wrap gap-x-6 gap-y-1 text-[0.75rem] mb-3">
          <span className="text-[#515154]">
            Owner: <span className="text-[#1d1d1f] font-semibold">{primary.owner}</span>
          </span>
          <span className="text-[#515154]">
            Sector: <span className="text-[#1d1d1f] font-semibold">{primary.sector}</span>
          </span>
        </div>

        {/* Consequence of delay — amber, not decorative */}
        <p className="text-[0.8125rem] text-[#0071e3] leading-[1.7]">
          {primary.consequence}
        </p>
      </div>

      {/* Supporting directives — deliberately smaller */}
      {supporting.length > 0 && (
        <div className="space-y-4 border-l-2 border-[#e5e5e7] pl-5">
          {supporting.map((d, i) => (
            <div key={i}>
              <p className="text-[0.875rem] text-[#515154] leading-snug mb-1">
                {d.directive}
              </p>
              <p className="text-[0.6875rem] text-[#6e6e73]">
                {d.owner} · {d.sector}
              </p>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Block 5: MONITORING AND CONSEQUENCE
 * Who is responsible. Review cycle. Counterfactual. Confidence.
 * ═══════════════════════════════════════════════════════════════════════ */

function MonitoringConsequenceBlock({ briefing }: { briefing: SovereignBriefingType }) {
  const monitoring = briefing.monitoring;
  const topAssignment = monitoring.assignments[0];

  return (
    <section className="space-y-6">
      {/* Execution ownership — prose, not grid */}
      {topAssignment && (
        <div>
          <p className="text-[0.9375rem] text-[#515154] leading-[1.8]">
            Execution is owned by <span className="text-[#1d1d1f] font-semibold">{topAssignment.owner}</span>.
            {' '}If the deadline passes, escalation authority transfers to{' '}
            <span className="text-[#1d1d1f] font-semibold">{topAssignment.escalationAuthority}</span>.
            {' '}Review cycle is every {topAssignment.reviewCycleHours}h.
          </p>
          <p className={`text-[0.8125rem] mt-2 ${
            topAssignment.status === 'escalated' ? 'text-[#d92f2f]'
              : topAssignment.status === 'at_risk' ? 'text-[#0071e3]'
              : 'text-[#6e6e73]'
          }`}>
            Status: {topAssignment.status} · {Math.round(topAssignment.hoursRemaining)}h remaining
          </p>
        </div>
      )}

      {/* Counterfactual — what happens without action */}
      <div className="border-l-2 border-[#d92f2f]/30 pl-5">
        <p className="text-[0.6875rem] text-[#6e6e73] uppercase tracking-widest font-medium mb-2">
          Without Action
        </p>
        <p className="text-[0.875rem] text-[#d92f2f]/80 leading-[1.75]">
          {briefing.counterfactual.withoutAction}
        </p>
      </div>

      {/* Confidence basis — one sentence */}
      <div>
        <p className="text-[0.8125rem] text-[#6e6e73] leading-[1.7]">
          {briefing.confidenceBasis.explanation}
        </p>
      </div>
    </section>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Block divider — minimal, not decorative
 * ═══════════════════════════════════════════════════════════════════════ */

function BlockDivider({ label }: { label: string }) {
  return (
    <div className="pt-10 pb-6">
      <p className="text-[0.6875rem] text-[#8e8e93] uppercase tracking-[0.2em] font-semibold mb-2">
        {label}
      </p>
      <div className="h-px bg-[#e5e5e7]" />
    </div>
  );
}

/* ═══════════════════════════════════════════════════════════════════════
 * Main Component — 5 blocks, vertical read, one pass
 * ═══════════════════════════════════════════════════════════════════════ */

interface SovereignBriefingProps {
  briefing: SovereignBriefingType;
}

export function SovereignBriefing({ briefing }: SovereignBriefingProps) {
  return (
    <div className="max-w-3xl mx-auto px-6 sm:px-8 py-10">
      {/* Block 1: CURRENT STATE */}
      <CurrentStateBlock briefing={briefing} />

      {/* Block 2: DOMINANT SIGNAL */}
      <BlockDivider label="Dominant Signal" />
      <DominantSignalBlock briefing={briefing} />

      {/* Block 3: HOW PRESSURE SPREADS */}
      <BlockDivider label="How Pressure Spreads" />
      <PressureSpreadsBlock briefing={briefing} />

      {/* Block 4: EXECUTIVE DECISION */}
      <BlockDivider label="Executive Decision" />
      <ExecutiveDecisionBlock briefing={briefing} />

      {/* Block 5: MONITORING AND CONSEQUENCE */}
      <BlockDivider label="Monitoring and Consequence" />
      <MonitoringConsequenceBlock briefing={briefing} />

      {/* Timestamp — minimal */}
      <div className="mt-14 pt-5 border-t border-[#e5e5e7]">
        <p className="text-[0.625rem] text-[#8e8e93] tracking-wider">
          Generated {new Date(briefing.timestamp).toLocaleString()} · {briefing.scenarioId}
        </p>
      </div>
    </div>
  );
}
