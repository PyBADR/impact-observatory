import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Control Room | Impact Observatory",
  description:
    "Spatial decision-making interface for Global Cascade Control platform. Real-time scenario analysis, entity visualization, and risk propagation.",
  viewport: "width=device-width, initial-scale=1, maximum-scale=1",
};

export default function ControlRoomLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
