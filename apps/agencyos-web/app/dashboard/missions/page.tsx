type MissionStatus = 'Running' | 'Success' | 'Failed' | 'Queued'

interface Mission {
  id: number
  name: string
  status: MissionStatus
  project: string
  duration: string
  result: string
}

const MISSIONS: Mission[] = [
  { id: 1, name: 'Scrape 500 CEO leads - SaaS vertical', status: 'Success', project: 'sophia-ai-factory', duration: '4m 12s', result: '497 leads' },
  { id: 2, name: 'SEO article batch #8 - 10 posts', status: 'Running', project: 'agencyos-web', duration: '2m 05s', result: '6/10 done' },
  { id: 3, name: 'Competitor report - Linear.app', status: 'Queued', project: 'agencyos-web', duration: '-', result: '-' },
  { id: 4, name: 'Lead nurturing email sequence', status: 'Failed', project: 'sophia-ai-factory', duration: '0m 43s', result: 'Quota exceeded' },
  { id: 5, name: 'Scrape 200 CMO leads - Fintech', status: 'Success', project: 'sophia-ai-factory', duration: '2m 58s', result: '200 leads' },
  { id: 6, name: 'Blog post: "What is RaaS?"', status: 'Success', project: 'agencyos-web', duration: '1m 10s', result: '1,240 words' },
  { id: 7, name: 'Health check all agents', status: 'Running', project: 'openclaw-worker', duration: '0m 22s', result: 'In progress' },
]

const STATUS_CONFIG: Record<MissionStatus, { label: string; className: string }> = {
  Running: { label: 'Running', className: 'bg-blue-500/20 text-blue-400 border border-blue-500/30' },
  Success: { label: 'Success', className: 'bg-green-500/20 text-green-400 border border-green-500/30' },
  Failed:  { label: 'Failed',  className: 'bg-red-500/20 text-red-400 border border-red-500/30' },
  Queued:  { label: 'Queued',  className: 'bg-zinc-700/60 text-zinc-400 border border-zinc-600/40' },
}

const FILTERS: Array<{ key: 'All' | MissionStatus; label: string }> = [
  { key: 'All', label: 'All' },
  { key: 'Running', label: 'Running' },
  { key: 'Success', label: 'Success' },
  { key: 'Failed', label: 'Failed' },
]

export default function MissionsPage({
  searchParams,
}: {
  searchParams?: Promise<{ filter?: string }>
}) {
  // searchParams is async in Next 16 but unused here — filter is static for now
  void searchParams

  const missions = MISSIONS

  return (
    <div className="space-y-6 max-w-5xl">
      <div>
        <h1 className="text-2xl font-bold text-white">Missions</h1>
        <p className="mt-1 text-sm text-zinc-500">All agent missions across your projects.</p>
      </div>

      {/* Filter bar */}
      <div className="flex gap-2" role="group" aria-label="Filter missions by status">
        {FILTERS.map(({ key, label }) => (
          <button
            key={key}
            className="rounded-lg border border-zinc-700 bg-zinc-900 px-4 py-1.5 text-sm text-zinc-400 hover:bg-zinc-800 hover:text-white transition-colors first:bg-zinc-800 first:text-white"
            aria-label={`Filter: ${label}`}
          >
            {label}
          </button>
        ))}
      </div>

      {/* Table */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 overflow-hidden">
        <table className="w-full text-sm" role="table" aria-label="Missions table">
          <thead>
            <tr className="border-b border-zinc-800 text-left text-xs text-zinc-500 uppercase tracking-wide">
              <th className="px-5 py-3 font-medium">Name</th>
              <th className="px-5 py-3 font-medium hidden sm:table-cell">Status</th>
              <th className="px-5 py-3 font-medium hidden md:table-cell">Project</th>
              <th className="px-5 py-3 font-medium hidden lg:table-cell">Duration</th>
              <th className="px-5 py-3 font-medium">Result</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-zinc-800/60">
            {missions.map((m) => {
              const cfg = STATUS_CONFIG[m.status]
              return (
                <tr key={m.id} className="hover:bg-zinc-800/30 transition-colors">
                  <td className="px-5 py-3 text-zinc-200 font-medium truncate max-w-[200px]">{m.name}</td>
                  <td className="px-5 py-3 hidden sm:table-cell">
                    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${cfg.className}`}>
                      {cfg.label}
                    </span>
                  </td>
                  <td className="px-5 py-3 text-zinc-500 hidden md:table-cell">{m.project}</td>
                  <td className="px-5 py-3 text-zinc-500 hidden lg:table-cell font-mono">{m.duration}</td>
                  <td className="px-5 py-3 text-zinc-400">{m.result}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
}
