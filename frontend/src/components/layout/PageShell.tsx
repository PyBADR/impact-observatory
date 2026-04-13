/**
 * PageShell — top-level page wrapper.
 *
 * Provides TopNav + main content area with the fade-in animation.
 * Every page in the product wraps its content in PageShell.
 */

import { TopNav } from './TopNav';

interface PageShellProps {
  children: React.ReactNode;
}

export function PageShell({ children }: PageShellProps) {
  return (
    <div className="min-h-screen bg-[var(--io-bg)]">
      <TopNav />
      <main className="io-fade-in">
        {children}
      </main>
    </div>
  );
}
