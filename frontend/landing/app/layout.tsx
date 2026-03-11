import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Mekong CLI — AI-Operated Business Platform',
  description:
    '319 commands, 463 skills, 127 AI agents. 5-layer pyramid from Founder to Ops.',
  keywords: ['AI agency', 'CLI', 'founder tools', 'multi-agent', 'mekong-cli'],
  openGraph: {
    title: 'Mekong CLI — AI-Operated Business Platform',
    description: '319 commands, 463 skills, 127 AI agents. 5-layer pyramid from Founder to Ops.',
    url: 'https://mekong.cli.dev',
    siteName: 'Mekong CLI',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body>{children}</body>
    </html>
  )
}
