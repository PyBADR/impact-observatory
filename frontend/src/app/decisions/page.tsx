/**
 * Decisions page — redirects to Decision Room V2.
 * The decision interface is now unified inside /command-center.
 */
import { redirect } from "next/navigation";

export default function DecisionsPage() {
  redirect("/command-center");
}
