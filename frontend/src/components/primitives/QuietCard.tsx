/**
 * QuietCard — a calm surface container with soft border.
 * The foundational card for all content blocks.
 */

interface QuietCardProps {
  children: React.ReactNode;
  className?: string;
  interactive?: boolean;
  as?: 'div' | 'article' | 'li';
}

export function QuietCard({
  children,
  className = '',
  interactive = false,
  as: Tag = 'div',
}: QuietCardProps) {
  const base = 'bg-white border border-[#E6E6E0] rounded-xl';
  const hover = interactive
    ? 'transition-colors duration-200 hover:border-[#D9D9D2] cursor-pointer'
    : '';

  return (
    <Tag className={`${base} ${hover} ${className}`}>
      {children}
    </Tag>
  );
}
