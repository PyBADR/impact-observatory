/**
 * MetricPill — displays a single metric with label.
 * Compact, readable, institutional.
 */

interface MetricPillProps {
  label: string;
  value: string;
  className?: string;
}

export function MetricPill({ label, value, className = '' }: MetricPillProps) {
  return (
    <div className={`flex flex-col gap-1 ${className}`}>
      <span className="text-xs font-semibold uppercase tracking-[0.06em] text-[#8A8A83]">
        {label}
      </span>
      <span className="text-lg font-semibold text-[#1B1B19] tracking-tight">
        {value}
      </span>
    </div>
  );
}
