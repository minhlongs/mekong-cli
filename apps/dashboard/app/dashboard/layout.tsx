import type { ReactNode } from 'react'
import { DashboardShell } from '@/components/DashboardShell'

export default function DashboardSectionLayout({ children }: { children: ReactNode }) {
  return <DashboardShell>{children}</DashboardShell>
}
