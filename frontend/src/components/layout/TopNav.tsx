/**
 * TopNav — minimal, calm top navigation.
 *
 * Product name left, navigation links right.
 * Frosted glass bar, sticky. No visual noise. Institutional.
 */
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Container } from './Container';

const links = [
  { href: '/',           label: 'Overview' },
  { href: '/decision',   label: 'Decisions' },
  { href: '/evaluation', label: 'Evaluation' },
];

export function TopNav() {
  const pathname = usePathname();

  return (
    <nav className="sticky top-0 z-50 bg-[var(--io-bg)]/80 backdrop-blur-md border-b border-[var(--io-border-muted)]">
      <Container>
        <div className="flex items-center justify-between h-14">
          {/* Brand */}
          <Link href="/" className="flex items-baseline gap-2.5">
            <span className="text-[0.9375rem] font-semibold tracking-tight text-[var(--io-charcoal)]">
              Impact Observatory
            </span>
            <span className="text-[0.75rem] text-[var(--io-text-tertiary)] font-medium hidden sm:inline">
              مرصد الأثر
            </span>
          </Link>

          {/* Navigation */}
          <div className="flex items-center gap-8">
            {links.map((link) => {
              const isActive =
                link.href === '/'
                  ? pathname === '/'
                  : pathname.startsWith(link.href);

              return (
                <Link
                  key={link.href}
                  href={link.href}
                  className={[
                    'text-[0.8125rem] font-medium transition-colors duration-150',
                    isActive
                      ? 'text-[var(--io-charcoal)]'
                      : 'text-[var(--io-text-tertiary)] hover:text-[var(--io-text-secondary)]',
                  ].join(' ')}
                >
                  {link.label}
                </Link>
              );
            })}
          </div>
        </div>
      </Container>
    </nav>
  );
}
