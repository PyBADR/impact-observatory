/**
 * Demo page — redirects to Decision Room V2.
 * The demo flow is now accessible via the Presentation Mode button in /command-center.
 */
import { redirect } from "next/navigation";

export default function DemoPage() {
  redirect("/command-center");
}
