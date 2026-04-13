/**
 * ScenarioCard — a single scenario entry on the landing page.
 * Shows severity badge, title, affected sectors, and brief description.
 * Links to /scenario/[slug].
 */

import Link from 'next/link';
import { Badge } from '@/components/primitives';

export interface ScenarioCardProps {
  id: string;
  title: string;
  titleAr?: string;
  description: string;
  severityLevel: 'nominal' | 'low' | 'guarded' | 'elevated' | 'high' | 'severe';
  affectedSectors: string[];
  horizonHours: number;
}

const severityDisplay: Record<
  ScenarioCardProps['severityLevel'],
  { label: string; variant: 'neutral' | 'olive' | 'amber' | 'red' }
> = {
  nominal:  { label: 'Nominal',  variant: 'neutral' },
  low:      { label: 'Low',      variant: 'neutral' },
  guarded:  { label: 'Guarded',  variant: 'olive' },
  elevated: { label: 'Elevated', variant: 'amber' },
  high:     { label: 'High',     variant: 'red' },
  severe:   { label: 'Severe',   variant: 'red' },
};

export function ScenarioCard({
  id,
  title,
  description,
  severityLevel,
  affectedSectors,
  horizonHours,
}: ScenarioCardProps) {
  const severity = severityDisplay[severityLevel];

  return (
    <Link href={`/scenario/${id}`} className="block group">
      <article className="bg-white border border-[#E6E6E0] rounded-xl p-6 h-full flex flex-col gap-4 transition-colors duration-200 group-hover:border-[#D9D9D2]">
        {/* Top row: badge + horizon */}
        <div className="flex items-center justify-between">
          <Badge variant={severity.variant}>{severity.label}</Badge>
          <span className="text-xs text-[#8A8A83] font-medium">
            {horizonHours}h horizon
          </span>
        </div>

        {/* Title */}
        <h4 className="text-base font-semibold tracking-tight text-[#1B1B19] leading-snug">
          {title}
        </h4>

        {/* Description */}
        <p className="text-sm text-[#5F5F58] leading-relaxed line-clamp-2 flex-1">
          {description}
        </p>

        {/* Sectors */}
        <div className="flex flex-wrap gap-1.5 pt-1">
          {affectedSectors.slice(0, 4).map((sector) => (
            <span
              key={sector}
              className="text-[0.6875rem] text-[#8A8A83] bg-[#F5F5F2] px-2 py-0.5 rounded font-medium"
            >
              {sector}
            </span>
          ))}
          {affectedSectors.length > 4 && (
            <span className="text-[0.6875rem] text-[#8A8A83] px-1 py-0.5 font-medium">
              +{affectedSectors.length - 4}
            </span>
          )}
        </div>
      </article>
    </Link>
  );
}
