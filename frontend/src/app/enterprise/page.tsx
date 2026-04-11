/**
 * Enterprise dashboard — redirects to sectors tab.
 */
import { redirect } from "next/navigation";

export default function EnterprisePage() {
  redirect("/command-center?tab=sectors");
}
