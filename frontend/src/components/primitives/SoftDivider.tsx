/**
 * SoftDivider — a subtle horizontal rule.
 * Quiet separation between content blocks.
 */

interface SoftDividerProps {
  className?: string;
}

export function SoftDivider({ className = '' }: SoftDividerProps) {
  return (
    <hr
      className={`border-0 h-px bg-[#E6E6E0] ${className}`}
      aria-hidden="true"
    />
  );
}
