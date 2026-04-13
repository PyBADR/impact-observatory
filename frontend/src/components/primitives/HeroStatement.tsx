/**
 * HeroStatement — large, calm hero text with optional subtitle.
 * Used at the top of major pages for clear product framing.
 */

interface HeroStatementProps {
  title: string;
  subtitle?: string;
  className?: string;
}

export function HeroStatement({ title, subtitle, className = '' }: HeroStatementProps) {
  return (
    <div className={`py-20 sm:py-28 lg:py-32 ${className}`}>
      <h1 className="text-[2.75rem] sm:text-[3.5rem] lg:text-[4rem] font-bold tracking-[-0.03em] leading-[1.06] text-[#1B1B19] whitespace-pre-line">
        {title}
      </h1>
      {subtitle && (
        <p className="mt-6 text-[1.125rem] sm:text-[1.25rem] leading-relaxed text-[#5F5F58] max-w-xl">
          {subtitle}
        </p>
      )}
    </div>
  );
}
