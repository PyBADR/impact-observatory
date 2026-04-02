import type { Metadata, Viewport } from 'next'
import '../styles/globals.css'

export const metadata: Metadata = {
  title: {
    default: 'Impact Observatory | مرصد الأثر — Decision Intelligence for Financial Impact',
    template: '%s | Impact Observatory',
  },
  description:
    'Decision intelligence platform transforming complex events into financial loss, banking stress, insurance stress, and decision actions across GCC markets.',
  keywords: [
    'decision intelligence',
    'financial impact',
    'GCC',
    'banking stress',
    'insurance risk',
    'fintech disruption',
    'Saudi Arabia',
    'impact observatory',
  ],
  authors: [{ name: 'Impact Observatory' }],
  openGraph: {
    title: 'Impact Observatory | مرصد الأثر — Decision Intelligence for Financial Impact',
    description:
      'Transform complex events into financial loss, banking stress, and decision actions across GCC markets.',
    siteName: 'Impact Observatory',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Impact Observatory | مرصد الأثر',
    description:
      'AI decision intelligence for GCC financial impact. Banking stress, insurance risk, fintech disruption.',
  },
  robots: {
    index: true,
    follow: true,
  },
  icons: {
    icon: [
      { url: '/favicon.svg', type: 'image/svg+xml' },
    ],
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#F8FAFC',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" dir="ltr" className="light">
      <body className="min-h-screen bg-ds-bg text-ds-text antialiased font-en">
        {children}
      </body>
    </html>
  )
  }
