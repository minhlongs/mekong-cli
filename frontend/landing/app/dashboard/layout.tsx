'use client'
import Link from 'next/link'
import { usePathname } from 'next/navigation'

const NAV = [
  { href: '/dashboard', label: 'Overview', icon: '📊' },
  { href: '/dashboard/governance', label: 'Governance', icon: '⚖️' },
  { href: '/dashboard/reputation', label: 'Reputation', icon: '🏆' },
  { href: '/dashboard/ngu-su', label: 'Ngũ Sự', icon: '五' },
]

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  return (
    <div className="flex min-h-screen bg-[var(--md-surface,#111)] text-[var(--md-on-surface,#e0e0e0)]">
      <aside className="w-56 border-r border-[var(--md-outline-variant,#333)] p-4 space-y-1">
        <h2 className="text-lg font-bold mb-4">Mekong Studio</h2>
        {NAV.map(n => (
          <Link key={n.href} href={n.href}
            className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${
              pathname === n.href ? 'bg-[var(--md-primary-container,#1a3a5c)] font-semibold' : 'hover:bg-[var(--md-surface-container,#222)]'
            }`}>
            <span>{n.icon}</span>{n.label}
          </Link>
        ))}
      </aside>
      <main className="flex-1 p-6 overflow-auto">{children}</main>
    </div>
  )
}
