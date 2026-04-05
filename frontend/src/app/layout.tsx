import type { Metadata } from "next";
import Script from "next/script";
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
        <Script
          id="microsoft-clarity"
          strategy="afterInteractive"
          dangerouslySetInnerHTML={{
            __html: `
              (function(c,l,a,r,i,t,y){
                c[a]=c[a]||function(){(c[a].q=c[a].q||[]).push(arguments)};
                t=l.createElement(r);t.async=1;t.src="https://www.clarity.ms/tag/"+i;
                y=l.getElementsByTagName(r)[0];y.parentNode.insertBefore(t,y);
              })(window,document,"clarity","script","w74y18hrex");
            `,
          }}
        />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
