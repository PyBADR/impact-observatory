/**
 * Decisions page — redirects to Decision Room tab.
 */
import { redirect } from "next/navigation";

export default function DecisionsPage() {
  redirect("/command-center?tab=decisions");
}
