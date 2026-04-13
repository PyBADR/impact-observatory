/**
 * SectionTitle — inline heading for sub-sections within a page.
 * Lighter weight than SectionBlock header.
 */

interface SectionTitleProps {
  children: React.ReactNode;
  className?: string;
}

export function SectionTitle({ children, className = '' }: SectionTitleProps) {
  return (
    <h3 className={`text-xl font-semibold tracking-tight text-[#1B1B19] ${className}`}>
      {children}
    </h3>
  );
}
