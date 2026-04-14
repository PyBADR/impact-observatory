/**
 * Impact Observatory | مرصد الأثر — Root Route
 *
 * All intelligence lives at /command-center.
 * Root redirects there unconditionally.
 */

import { redirect } from "next/navigation";

export default function RootPage() {
  redirect("/command-center");
}
