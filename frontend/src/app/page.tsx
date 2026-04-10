/**
 * Impact Observatory | مرصد الأثر — Root Entry Point
 *
 * Redirects to /command-center which renders DecisionRoomV2.
 * This is the ONLY product interface. No parallel dashboards.
 */

import { redirect } from "next/navigation";

export default function RootPage() {
  redirect("/command-center");
}
