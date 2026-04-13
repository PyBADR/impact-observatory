/**
 * SectorCoverageGrid — displays covered sectors with descriptions.
 * Clean grid, no icons, institutional typography.
 */

import { landing } from '@/lib/copy';

export function SectorCoverageGrid() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-6">
      {landing.sectors.map((sector) => (
        <div
          key={sector.name}
          className="py-4 border-t border-[#E6E6E0]"
        >
          <h4 className="text-[0.9375rem] font-semibold text-[#1B1B19] mb-1.5">
            {sector.name}
          </h4>
          <p className="text-sm text-[#5F5F58] leading-relaxed">
            {sector.description}
          </p>
        </div>
      ))}
    </div>
  );
}
