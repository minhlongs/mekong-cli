'use client'

import { useState, useEffect } from 'react'

interface Stakeholder {
  id: string
  display_name: string
  role: string
  governance_level: number
  voice_credits: number
}

interface Proposal {
  id: string
  title: string
  type: string
  status: string
  votes_for: number
  votes_against: number
  created_at: string
}

interface ChartData {
  label: string
  value: number
}

export default function GovernancePage() {
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([])
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [loading, setLoading] = useState(true)
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('7d')

  // Chart data
  const votingDistribution: ChartData[] = [
    { label: 'For', value: 65 },
    { label: 'Against', value: 25 },
    { label: 'Abstain', value: 10 },
  ]

  const activityData: ChartData[] = [
    { label: 'Mon', value: 120 },
    { label: 'Tue', value: 180 },
    { label: 'Wed', value: 95 },
    { label: 'Thu', value: 210 },
    { label: 'Fri', value: 150 },
    { label: 'Sat', value: 85 },
    { label: 'Sun', value: 110 },
  ]

  useEffect(() => {
    Promise.all([
      fetch('/api/v1/governance/stakeholders').then(r => r.json()).catch(() => ({ stakeholders: [] })),
      fetch('/api/v1/governance/proposals').then(r => r.json()).catch(() => ({ proposals: [] })),
    ]).then(([sh, pr]) => {
      setStakeholders(sh.stakeholders || [])
      setProposals(pr.proposals || [])
      setLoading(false)
    })
  }, [])

  if (loading) return (
    <div className="p-8 text-center flex items-center justify-center min-h-[400px]">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>
  )

  return (
    <div className="p-4 sm:p-8 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6 sm:mb-8">
        <h1 className="text-2xl sm:text-3xl font-bold mb-2">🏛️ Governance</h1>
        <p className="text-gray-500 text-sm sm:text-base">Tam Giác Ngược — Community-first quadratic voting</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6 mb-6 sm:mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-6 shadow-lg border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Stakeholders</h3>
          <p className="text-3xl font-bold mt-2 text-gray-900 dark:text-white">{stakeholders.length}</p>
          <div className="mt-3 flex items-center text-sm">
            <span className="text-green-600 font-medium">+12%</span>
            <span className="text-gray-500 ml-2">tháng này</span>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-6 shadow-lg border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Active Proposals</h3>
          <p className="text-3xl font-bold mt-2 text-gray-900 dark:text-white">{proposals.filter(p => p.status === 'active').length}</p>
          <div className="mt-3 flex items-center text-sm">
            <span className="text-blue-600 font-medium">5 đang vote</span>
          </div>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-6 shadow-lg border border-gray-100 dark:border-gray-700">
          <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400">Total Votes Cast</h3>
          <p className="text-3xl font-bold mt-2 text-gray-900 dark:text-white">{proposals.reduce((s, p) => s + p.votes_for + p.votes_against, 0).toLocaleString()}</p>
          <div className="mt-3 flex items-center text-sm">
            <span className="text-green-600 font-medium">+28%</span>
            <span className="text-gray-500 ml-2">tuần này</span>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6 mb-6 sm:mb-8">
        {/* Voting Distribution Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-6 shadow-lg border border-gray-100 dark:border-gray-700">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">📊 Voting Distribution</h2>
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as typeof timeRange)}
              className="text-sm border border-gray-300 dark:border-gray-600 rounded-lg px-3 py-1.5 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 focus:ring-2 focus:ring-blue-500"
            >
              <option value="7d">7 days</option>
              <option value="30d">30 days</option>
              <option value="90d">90 days</option>
            </select>
          </div>
          <div className="space-y-3">
            {votingDistribution.map((item) => (
              <div key={item.label} className="space-y-1">
                <div className="flex justify-between text-sm">
                  <span className="font-medium text-gray-700 dark:text-gray-300">{item.label}</span>
                  <span className="text-gray-500 dark:text-gray-400">{item.value}%</span>
                </div>
                <div className="h-3 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all duration-500 ease-out ${
                      item.label === 'For' ? 'bg-green-500' :
                      item.label === 'Against' ? 'bg-red-500' : 'bg-gray-400'
                    }`}
                    style={{ width: `${item.value}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Activity Chart */}
        <div className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-6 shadow-lg border border-gray-100 dark:border-gray-700">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">📈 Weekly Activity</h2>
          <div className="flex items-end justify-between h-40 gap-2">
            {activityData.map((item, idx) => {
              const maxValue = Math.max(...activityData.map(d => d.value))
              const height = (item.value / maxValue) * 100
              return (
                <div key={item.label} className="flex-1 flex flex-col items-center gap-2">
                  <div className="w-full relative group">
                    <div
                      className="w-full bg-gradient-to-t from-blue-600 to-blue-400 rounded-t-lg transition-all duration-300 hover:from-blue-700 hover:to-blue-500 cursor-pointer"
                      style={{ height: `${height}%`, minHeight: '8px' }}
                    />
                    <div className="absolute -top-8 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                      {item.value} votes
                    </div>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400">{item.label}</span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Stakeholders</h2>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-700">
                <tr>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Name</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Role</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Level</th>
                  <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase whitespace-nowrap">Voice Credits</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {stakeholders.map(s => (
                  <tr key={s.id} className="hover:bg-gray-50 dark:hover:bg-gray-750">
                    <td className="px-4 py-4 font-medium text-gray-900 dark:text-white">{s.display_name}</td>
                    <td className="px-4 py-4 capitalize text-gray-600 dark:text-gray-300">{s.role}</td>
                    <td className="px-4 py-4">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200">
                        Level {s.governance_level}
                      </span>
                    </td>
                    <td className="px-4 py-4 text-gray-600 dark:text-gray-300">{s.voice_credits.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {stakeholders.length === 0 && (
            <div className="p-8 text-center text-gray-500 dark:text-gray-400">
              No stakeholders yet
            </div>
          )}
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4 flex items-center justify-between">
          <span>Recent Proposals</span>
          <a href="/dashboard/governance/proposals" className="text-sm font-normal text-blue-500 hover:text-blue-600">View all →</a>
        </h2>
        <div className="space-y-3">
          {proposals.slice(0, 5).map(p => (
            <div key={p.id} className="bg-white dark:bg-gray-800 rounded-xl p-4 sm:p-6 shadow hover:shadow-md transition-shadow">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start gap-3">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white">{p.title}</h3>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-xs bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200 px-2.5 py-0.5 rounded">{p.type}</span>
                    <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${
                      p.status === 'active' ? 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200' : 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-300'
                    }`}>
                      {p.status}
                    </span>
                  </div>
                </div>
              </div>
              <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-700">
                <div className="flex items-center gap-4 text-sm">
                  <div className="flex items-center gap-1.5 text-green-600 dark:text-green-400">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M2 10.5a1.5 1.5 0 113 0v6a1.5 1.5 0 01-3 0v-6zM6 10.333v5.43a2 2 0 001.106 1.79l.05.025A4 4 0 008.943 18h5.416a2 2 0 001.962-1.608l1.2-6A2 2 0 0015.56 8H12V4a2 2 0 00-2-2 1 1 0 00-1 1v.667a4 4 0 01-.8 2.4L6.8 7.933a4 4 0 00-.8 2.4z" /></svg>
                    <span className="font-medium">{p.votes_for}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-red-600 dark:text-red-400">
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20"><path d="M2 9.5a1.5 1.5 0 113 0v-6a1.5 1.5 0 01-3 0v6zM6 9.667v-5.43a2 2 0 011.106-1.79l.05-.025A4 4 0 018.943 2h5.416a2 2 0 011.962 1.608l1.2 6A2 2 0 0115.56 12H12v4a2 2 0 01-2 2 1 1 0 01-1-1v-.667a4 4 0 00-.8-2.4L6.8 12.067a4 4 0 01-.8-2.4z" /></svg>
                    <span className="font-medium">{p.votes_against}</span>
                  </div>
                  <div className="ml-auto text-gray-500 dark:text-gray-400">
                    {p.votes_for + p.votes_against} total votes
                  </div>
                </div>
                {/* Progress bar */}
                <div className="mt-3 h-2 bg-gray-100 dark:bg-gray-700 rounded-full overflow-hidden">
                  {p.votes_for + p.votes_against > 0 ? (
                    <div className="h-full flex">
                      <div
                        className="bg-green-500 transition-all duration-300"
                        style={{ width: `${(p.votes_for / (p.votes_for + p.votes_against)) * 100}%` }}
                      />
                      <div
                        className="bg-red-500 transition-all duration-300"
                        style={{ width: `${(p.votes_against / (p.votes_for + p.votes_against)) * 100}%` }}
                      />
                    </div>
                  ) : (
                    <div className="h-full bg-gray-200 dark:bg-gray-600" />
                  )}
                </div>
              </div>
            </div>
          ))}
          {proposals.length === 0 && (
            <div className="p-8 text-center text-gray-500 dark:text-gray-400 bg-white dark:bg-gray-800 rounded-xl">
              No proposals yet
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
