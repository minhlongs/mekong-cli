import { Bot, Brain, Cpu } from 'lucide-react'

type AgentStatus = 'online' | 'offline' | 'busy'

interface Agent {
  id: string
  name: string
  role: string
  status: AgentStatus
  currentTask: string
  uptime: string
  icon: React.ElementType
  accentColor: string
}

const AGENTS: Agent[] = [
  {
    id: 'tom-hum',
    name: 'Tôm Hùm',
    role: 'Task Dispatcher',
    status: 'online',
    currentTask: 'Watching tasks/ directory for new missions',
    uptime: '99.2% (72h)',
    icon: Bot,
    accentColor: 'from-purple-500 to-blue-600',
  },
  {
    id: 'cc-cli',
    name: 'CC CLI',
    role: 'Execution Engine',
    status: 'busy',
    currentTask: 'Running /cook SEO articles batch #8',
    uptime: '97.8% (72h)',
    icon: Cpu,
    accentColor: 'from-blue-500 to-cyan-600',
  },
  {
    id: 'antigravity',
    name: 'Antigravity',
    role: 'Strategic Brain',
    status: 'online',
    currentTask: 'Monitoring mission queue, next dispatch in 4m',
    uptime: '100% (72h)',
    icon: Brain,
    accentColor: 'from-violet-500 to-purple-700',
  },
]

const STATUS_CONFIG: Record<AgentStatus, { label: string; dotClass: string; badgeClass: string }> = {
  online:  { label: 'Online',  dotClass: 'bg-green-400 shadow-green-400/50',  badgeClass: 'bg-green-500/20 text-green-400 border border-green-500/30' },
  busy:    { label: 'Busy',    dotClass: 'bg-yellow-400 shadow-yellow-400/50', badgeClass: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30' },
  offline: { label: 'Offline', dotClass: 'bg-zinc-600',                        badgeClass: 'bg-zinc-700 text-zinc-500 border border-zinc-600' },
}

export default function AgentsPage() {
  return (
    <div className="space-y-6 max-w-4xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Agents</h1>
        <p className="mt-1 text-sm text-zinc-500">Live status of your autonomous agent fleet.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
        {AGENTS.map((agent) => {
          const cfg = STATUS_CONFIG[agent.status]
          const Icon = agent.icon
          return (
            <div
              key={agent.id}
              className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5 flex flex-col gap-4 hover:border-zinc-700 transition-colors"
              role="article"
              aria-label={`Agent: ${agent.name}`}
            >
              {/* Header */}
              <div className="flex items-start justify-between">
                <div className={`h-10 w-10 rounded-lg bg-gradient-to-br ${agent.accentColor} flex items-center justify-center`}>
                  <Icon className="h-5 w-5 text-white" aria-hidden="true" />
                </div>
                <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium flex items-center gap-1.5 ${cfg.badgeClass}`}>
                  <span className={`inline-block h-1.5 w-1.5 rounded-full shadow-sm ${cfg.dotClass}`} aria-hidden="true" />
                  {cfg.label}
                </span>
              </div>

              {/* Name + role */}
              <div>
                <h2 className="font-semibold text-white">{agent.name}</h2>
                <p className="text-xs text-zinc-500 mt-0.5">{agent.role}</p>
              </div>

              {/* Current task */}
              <div className="rounded-lg bg-zinc-800/60 px-3 py-2">
                <p className="text-xs text-zinc-500 mb-1">Current task</p>
                <p className="text-xs text-zinc-300 leading-relaxed">{agent.currentTask}</p>
              </div>

              {/* Uptime */}
              <div className="flex items-center justify-between border-t border-zinc-800 pt-3">
                <span className="text-xs text-zinc-600">Uptime</span>
                <span className="text-xs font-mono text-zinc-400">{agent.uptime}</span>
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
