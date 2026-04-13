/**
 * Container — max-width wrapper with consistent horizontal padding.
 *
 * Centers content within the calm, wide reading measure.
 * `narrow` constrains to ~48rem for long-form prose sections.
 */

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
  /** Narrow measure for prose-heavy sections (max-w-3xl). */
  narrow?: boolean;
}

export function Container({ children, className = '', narrow = false }: ContainerProps) {
  return (
    <div
      className={[
        'mx-auto px-6 sm:px-8 lg:px-12',
        narrow ? 'max-w-3xl' : 'max-w-6xl',
        className,
      ]
        .filter(Boolean)
        .join(' ')}
    >
      {children}
    </div>
  );
}
