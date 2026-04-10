import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Decision Command Center | Impact Observatory",
  description: "Single-screen intelligence terminal for GCC financial decision intelligence",
};

export default function CommandCenterLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
