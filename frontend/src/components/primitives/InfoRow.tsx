/**
 * InfoRow — a simple label-value pair displayed horizontally.
 * For metadata, decision properties, audit fields.
 */

interface InfoRowProps {
  label: string;
  value: string;
  className?: string;
}

export function InfoRow({ label, value, className = '' }: InfoRowProps) {
  return (
    <div className={`flex items-baseline justify-between gap-4 py-3 ${className}`}>
      <span className="text-sm text-[#8A8A83] font-medium shrink-0">{label}</span>
      <span className="text-sm text-[#1B1B19] font-medium text-right">{value}</span>
    </div>
  );
}
