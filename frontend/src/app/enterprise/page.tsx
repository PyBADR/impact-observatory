/**
 * Enterprise dashboard — redirects to Decision Room V2.
 * Enterprise intelligence is now unified inside /command-center.
 */
import { redirect } from "next/navigation";

export default function EnterprisePage() {
  redirect("/command-center");
}
