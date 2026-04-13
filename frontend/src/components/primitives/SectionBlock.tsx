/**
 * SectionBlock — vertical section with generous spacing.
 * Accepts an optional label, heading, and subheading above children.
 */

interface SectionBlockProps {
  children: React.ReactNode;
  label?: string;
  heading?: string;
  subheading?: string;
  className?: string;
  id?: string;
}

export function SectionBlock({
  children,
  label,
  heading,
  subheading,
  className = '',
  id,
}: SectionBlockProps) {
  return (
    <section id={id} className={`py-16 sm:py-20 lg:py-24 ${className}`}>
      {(label || heading || subheading) && (
        <div className="mb-12 sm:mb-16">
          {label && (
            <p className="text-xs font-semibold uppercase tracking-[0.08em] text-[#8A8A83] mb-3">
              {label}
            </p>
          )}
          {heading && (
            <h2 className="text-[2rem] sm:text-[2.5rem] font-bold tracking-tight leading-[1.1] text-[#1B1B19]">
              {heading}
            </h2>
          )}
          {subheading && (
            <p className="mt-4 text-[1.0625rem] leading-relaxed text-[#5F5F58] max-w-2xl">
              {subheading}
            </p>
          )}
        </div>
      )}
      {children}
    </section>
  );
}
