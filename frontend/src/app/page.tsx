/**
 * Impact Observatory | مرصد الأثر — Root Route
 *
 * Entry flow:
 *   /                → /demo       (institutional intro:
 *                                   Impact Observatory — Macroeconomic
 *                                   Intelligence for the GCC — From Signal
 *                                   to Decision)
 *   /demo            → hero landing → /command-center
 *   /command-center  → full product surface (8 tabs, institutional naming)
 *
 * Returning users can bookmark /command-center directly — the redirect here
 * only governs first entry.
 */

import { redirect } from "next/navigation";

export default function RootPage() {
  redirect("/demo");
}
