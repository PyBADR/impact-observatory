/**
 * Container — max-width wrapper with consistent horizontal padding.
 * Centers content and provides the calm, wide reading measure.
 */

interface ContainerProps {
  children: React.ReactNode;
  className?: string;
  narrow?: boolean;
}

export function Container({ children, className = '', narrow = false }: ContainerProps) {
  const maxWidth = narrow ? 'max-w-3xl' : 'max-w-6xl';

  return (
    <div className={`mx-auto px-6 sm:px-8 lg:px-12 ${maxWidth} ${className}`}>
      {children}
    </div>
  );
}
