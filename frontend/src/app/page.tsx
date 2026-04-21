/**
 * Impact Observatory | مرصد الأثر — Root Route
 *
 * Entry flow:
 *   /                → /demo       (institutional intro: "GCC Economic Macro — From Signal to Economic Decisions")
 *   /demo            → DemoOverlay or → /command-center on "Start Executive Demo"
 *   /command-center  → full intelligence surface (8 tabs)
 *
 * Returning users can bookmark /command-center directly — the redirect here
 * only governs first entry and keeps the executive-demo intro as the default
 * first page before the command center opens.
 */

import { redirect } from "next/navigation";

export default function RootPage() {
  redirect("/demo");
}
