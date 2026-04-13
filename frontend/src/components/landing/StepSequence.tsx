/**
 * StepSequence — the 3-step logic block on the landing page.
 * Signal → Transmission → Decision.
 * Calm, numbered, wide spacing.
 */

import { landing } from '@/lib/copy';

export function StepSequence() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-8 lg:gap-12">
      {landing.steps.map((step) => (
        <div key={step.number} className="flex flex-col gap-4">
          <span className="text-[0.75rem] font-semibold tracking-[0.1em] uppercase text-[#8A8A83]">
            {step.number}
          </span>
          <h3 className="text-xl font-semibold tracking-tight text-[#1B1B19]">
            {step.title}
          </h3>
          <p className="text-[0.9375rem] leading-relaxed text-[#5F5F58]">
            {step.description}
          </p>
        </div>
      ))}
    </div>
  );
}
