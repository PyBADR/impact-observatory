import type { Metadata } from "next";
import "../theme/globals.css";
import { Providers } from "@/components/shared/providers";

export const metadata: Metadata = {
  title: "Impact Observatory | مرصد الأثر",
  description:
    "Simulate systemic stress across banking, insurance, fintech, and critical infrastructure — then act before failure. Production-grade GCC executive decision intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" dir="ltr">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,400&family=IBM+Plex+Sans+Arabic:wght@300;400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="bg-io-bg text-io-primary antialiased font-sans">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
