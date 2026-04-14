/**
 * Impact Observatory — Landing Page V2
 *
 * Institutional. Not a product page. Not SaaS.
 * This is the entry point to a macro intelligence system
 * used by GCC decision-makers: central bank governors,
 * sovereign wealth fund CIOs, ministry officials.
 *
 * Structure:
 *   Opening statement (hero)
 *   Scope (what it covers, briefly)
 *   Entry (single quiet link)
 *
 * That's it.
 */

import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-bg-main flex flex-col">
      {/* ── Wordmark ── */}
      <header className="px-8 pt-8">
        <span className="text-[0.8125rem] font-medium tracking-[0.04em] text-tx-tertiary">
          Impact Observatory
        </span>
      </header>

      {/* ── Opening ── */}
      <main className="flex-1 flex items-center">
        <div className="w-full max-w-[900px] px-8 sm:px-12 py-20 sm:py-0">
          <h1
            className="
              text-[clamp(2.5rem,5.5vw,4.25rem)] font-semibold
              leading-[1.08] tracking-[-0.035em]
              text-charcoal text-balance
            "
          >
            From macro signals
            <br />
            to economic decisions.
          </h1>

          <p
            className="
              mt-8 text-[1.1875rem] sm:text-[1.3125rem]
              leading-[1.6] text-tx-secondary
              max-w-[440px]
            "
          >
            How shocks move across GCC economies
            — and who must act.
          </p>

          {/* ── Scope ── */}
          <div className="mt-16 flex items-baseline gap-10 sm:gap-14 flex-wrap">
            <Fact value="6" label="economies" />
            <Fact value="15" label="scenarios" />
            <Fact value="7" label="sectors" />
          </div>

          {/* ── Entry ── */}
          <div className="mt-16">
            <Link
              href="/command-center?demo=true"
              className="
                inline-flex items-center gap-3
                text-[0.9375rem] font-medium text-charcoal
                border-b border-charcoal/30 pb-1
                transition-all duration-200
                hover:border-charcoal hover:gap-4
              "
            >
              Enter
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                aria-hidden="true"
              >
                <path
                  d="M3 8h10M9 4l4 4-4 4"
                  stroke="currentColor"
                  strokeWidth="1.4"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </Link>
          </div>
        </div>
      </main>

      {/* ── Footer ── */}
      <footer className="px-8 pb-8 flex items-end justify-between">
        <span className="text-[0.6875rem] text-tx-tertiary tracking-[0.02em]">
          GCC Macro Financial Intelligence
        </span>
        <span className="text-[0.6875rem] text-tx-tertiary tabular-nums">
          2026
        </span>
      </footer>
    </div>
  );
}

function Fact({ value, label }: { value: string; label: string }) {
  return (
    <div className="flex items-baseline gap-2">
      <span className="text-[1.75rem] font-semibold tabular-nums tracking-[-0.02em] text-charcoal">
        {value}
      </span>
      <span className="text-[0.8125rem] text-tx-tertiary tracking-[0.01em]">
        {label}
      </span>
    </div>
  );
}
