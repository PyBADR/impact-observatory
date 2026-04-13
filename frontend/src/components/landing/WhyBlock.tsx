/**
 * WhyBlock — the "Why This Matters" narrative section.
 * Calm, centered, long-form readable text.
 */

import { landing } from '@/lib/copy';

export function WhyBlock() {
  return (
    <div className="max-w-2xl">
      <p className="text-[1.0625rem] leading-[1.8] text-[#5F5F58]">
        {landing.whyBody}
      </p>
    </div>
  );
}
