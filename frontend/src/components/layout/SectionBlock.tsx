/**
 * SectionBlock — vertical section with generous spacing.
 *
 * Accepts an optional label (uppercase micro), heading, and subheading
 * above children. Used to introduce every major content area on a page.
 */

interface SectionBlockProps {
  children: React.ReactNode;
  /** Uppercase micro-label above the heading (e.g. "How It Works"). */
  label?: string;
  /** Section heading — large, charcoal, tight tracking. */
  heading?: string;
  /** Supporting line below the heading — secondary color, max-w-2xl. */
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
            <p className="io-label mb-3">{label}</p>
          )}
          {heading && (
            <h2 className="text-[2rem] sm:text-[2.5rem] font-bold tracking-tight leading-[1.1] text-[var(--io-charcoal)]">
              {heading}
            </h2>
          )}
          {subheading && (
            <p className="mt-4 text-[1.0625rem] leading-relaxed text-[var(--io-text-secondary)] max-w-2xl">
              {subheading}
            </p>
          )}
        </div>
      )}
      {children}
    </section>
  );
}
