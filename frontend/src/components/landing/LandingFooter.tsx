/**
 * LandingFooter — minimal institutional footer.
 * Product name, Arabic name, positioning line.
 */

import { Container } from '@/components/primitives';

export function LandingFooter() {
  return (
    <footer className="border-t border-[#E6E6E0]">
      <Container>
        <div className="py-10 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-baseline gap-2.5">
            <span className="text-xs font-medium text-[#5F5F58]">
              Impact Observatory
            </span>
            <span className="text-xs text-[#8A8A83]">
              مرصد الأثر
            </span>
          </div>
          <span className="text-xs text-[#8A8A83]">
            GCC Macro Decision Intelligence
          </span>
        </div>
      </Container>
    </footer>
  );
}
