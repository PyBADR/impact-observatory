import type { Metadata, Viewport } from 'next'
import '../styles/globals.css'

export const metadata: Metadata = {
  title: {
    default: 'Deevo Sim — Simulation Intelligence Engine',
    template: '%s | Deevo Sim',
  },
  description:
    'Turn real-world inputs into entity graphs, agent behavior, and predictive simulation across GCC scenarios.',
  keywords: [
    'simulation',
    'AI',
    'GCC',
    'agent-based modeling',
    'entity graph',
    'decision intelligence',
    'Saudi Arabia',
    'Kuwait',
  ],
  authors: [{ name: 'Deevo Analytics' }],
  openGraph: {
    title: 'Deevo Sim — Simulation Intelligence Engine',
    description:
      'Simulate public reaction, media spread, and economic impact across GCC scenarios using AI-powered agent modeling.',
    siteName: 'Deevo Sim',
    type: 'website',
    locale: 'en_US',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Deevo Sim — Simulation Intelligence Engine',
    description:
      'AI simulation engine for GCC scenarios. Entity graphs, agent personas, predictive intelligence.',
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
  themeColor: '#06060A',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="min-h-screen bg-ds-bg text-ds-text antialiased">
        {children}
      </body>
    </html>
  )
  }
