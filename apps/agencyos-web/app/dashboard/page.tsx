import { createClient } from '@/lib/supabase/server'
import { Target, Bot, DollarSign, TrendingUp } from 'lucide-react'

const STATS = [
  { label: 'Active Missions', value: '12', icon: Target, color: 'text-purple-400' },
  { label: 'Agents Running', value: '3', icon: Bot, color: 'text-blue-400' },
  { label: 'Revenue Today', value: '$840', icon: DollarSign, color: 'text-green-400' },
  { label: 'Success Rate', value: '94%', icon: TrendingUp, color: 'text-yellow-400' },
]

const RECENT_ACTIVITY = [
  { id: 1, event: 'Mission "Scrape 500 CEO leads" completed', time: '2 min ago', status: 'success' },
  { id: 2, event: 'Agent Tôm Hùm dispatched new task', time: '8 min ago', status: 'info' },
  { id: 3, event: 'Mission "SEO articles batch #7" running', time: '15 min ago', status: 'running' },
  { id: 4, event: 'Revenue milestone: $800 daily target hit', time: '32 min ago', status: 'success' },
  { id: 5, event: 'Mission "Competitor report - Notion" failed', time: '1 hr ago', status: 'error' },
]

const STATUS_COLORS: Record<string, string> = {
  success: 'bg-green-500/20 text-green-400',
  error: 'bg-red-500/20 text-red-400',
  running: 'bg-blue-500/20 text-blue-400',
  info: 'bg-zinc-700 text-zinc-300',
}

export default async function DashboardPage() {
  const supabase = await createClient()
  const { data: { user } } = await supabase.auth.getUser()
  const email = user?.email ?? 'User'

  return (
    <div className="space-y-8 max-w-5xl">
      {/* Welcome */}
      <div>
        <h1 className="text-2xl font-bold text-white">
          Welcome back, <span className="text-purple-400">{email.split('@')[0]}</span>
        </h1>
        <p className="mt-1 text-sm text-zinc-500">Here&apos;s your RaaS engine status.</p>
      </div>

      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {STATS.map(({ label, value, icon: Icon, color }) => (
          <div
            key={label}
            className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 flex flex-col gap-3"
          >
            <div className="flex items-center justify-between">
              <span className="text-xs text-zinc-500 font-medium">{label}</span>
              <Icon className={`h-4 w-4 ${color}`} aria-hidden="true" />
            </div>
            <span className="text-3xl font-bold text-white">{value}</span>
          </div>
        ))}
      </div>

      {/* Recent Activity */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 overflow-hidden">
        <div className="px-5 py-4 border-b border-zinc-800">
          <h2 className="text-sm font-semibold text-white">Recent Activity</h2>
        </div>
        <ul className="divide-y divide-zinc-800/60">
          {RECENT_ACTIVITY.map((item) => (
            <li key={item.id} className="flex items-center justify-between px-5 py-3 gap-4">
              <span className="text-sm text-zinc-300 truncate">{item.event}</span>
              <div className="flex items-center gap-3 shrink-0">
                <span className="text-xs text-zinc-600">{item.time}</span>
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-medium ${STATUS_COLORS[item.status]}`}
                >
                  {item.status}
                </span>
              </div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
