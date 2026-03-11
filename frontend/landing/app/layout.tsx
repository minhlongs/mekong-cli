import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AgencyOS — AI-Operated Business Platform',
  description:
    '289 commands, 216 skills, 127 AI agents. 5-layer pyramid from Founder to Ops.',
  keywords: ['AI agency', 'CLI', 'founder tools', 'multi-agent', 'mekong-cli'],
  openGraph: {
    title: 'AgencyOS — AI-Operated Business Platform',
    description: '289 commands, 216 skills, 127 AI agents. 5-layer pyramid from Founder to Ops.',
    url: 'https://agencyos.network',
    siteName: 'AgencyOS',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  )
}
