import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'AgencyOS — Vận hành doanh nghiệp bằng AI',
  description:
    '167 commands, 464 skills, 105 AI agents. Kim Tự Tháp 5 tầng từ Founder đến Ops.',
  keywords: ['AI agency', 'CLI', 'founder tools', 'multi-agent', 'mekong-cli'],
  openGraph: {
    title: 'AgencyOS — Vận hành doanh nghiệp bằng AI',
    description: '167 commands, 464 skills, 105 AI agents. Kim Tự Tháp 5 tầng từ Founder đến Ops.',
    url: 'https://agencyos.network',
    siteName: 'AgencyOS',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="vi" className="dark">
      <body>{children}</body>
    </html>
  )
}
