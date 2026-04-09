import type { Metadata } from "next";
import { MacroIntelligenceDemoView } from "@/features/macro-demo";

export const metadata: Metadata = {
  title: "Macro Intelligence Demo — Impact Observatory",
  description:
    "AI decision intelligence for GCC macroeconomic shock scenarios. Executive narrative demo.",
};

export default function DemoPage() {
  return <MacroIntelligenceDemoView />;
}
