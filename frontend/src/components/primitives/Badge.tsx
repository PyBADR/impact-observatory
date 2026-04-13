/**
 * Badge — small status indicator with muted colors.
 * Used for risk levels, scenario status, sector tags.
 */

type BadgeVariant = 'neutral' | 'amber' | 'red' | 'olive';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
}

const variantStyles: Record<BadgeVariant, string> = {
  neutral: 'bg-[#ECECE8] text-[#5F5F58]',
  amber:   'bg-[#F5EDE3] text-[#A06A34]',
  red:     'bg-[#F2E8E6] text-[#8E4338]',
  olive:   'bg-[#ECEEE9] text-[#5E6759]',
};

export function Badge({ children, variant = 'neutral', className = '' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-md text-xs font-semibold tracking-wide ${variantStyles[variant]} ${className}`}
    >
      {children}
    </span>
  );
}
