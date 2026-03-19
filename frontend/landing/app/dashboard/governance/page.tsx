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

export default function GovernancePage() {
  const [stakeholders, setStakeholders] = useState<Stakeholder[]>([])
  const [proposals, setProposals] = useState<Proposal[]>([])
  const [loading, setLoading] = useState(true)

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

  if (loading) return <div className="p-8 text-center">Loading governance...</div>

  return (
    <div className="p-8 max-w-6xl mx-auto">
      <h1 className="text-3xl font-bold mb-2">🏛️ Governance</h1>
      <p className="text-gray-500 mb-8">Tam Giác Ngược — Community-first quadratic voting</p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow">
          <h3 className="text-sm font-medium text-gray-500">Stakeholders</h3>
          <p className="text-3xl font-bold mt-2">{stakeholders.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow">
          <h3 className="text-sm font-medium text-gray-500">Active Proposals</h3>
          <p className="text-3xl font-bold mt-2">{proposals.filter(p => p.status === 'active').length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow">
          <h3 className="text-sm font-medium text-gray-500">Total Votes Cast</h3>
          <p className="text-3xl font-bold mt-2">{proposals.reduce((s, p) => s + p.votes_for + p.votes_against, 0)}</p>
        </div>
      </div>

      <div className="mb-8">
        <h2 className="text-xl font-semibold mb-4">Stakeholders</h2>
        <div className="bg-white dark:bg-gray-800 rounded-xl shadow overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Name</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Role</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Level</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Voice Credits</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {stakeholders.map(s => (
                <tr key={s.id}>
                  <td className="px-6 py-4">{s.display_name}</td>
                  <td className="px-6 py-4 capitalize">{s.role}</td>
                  <td className="px-6 py-4">{s.governance_level}</td>
                  <td className="px-6 py-4">{s.voice_credits}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      <div>
        <h2 className="text-xl font-semibold mb-4">
          Recent Proposals
          <a href="/dashboard/governance/proposals" className="text-sm font-normal text-blue-500 ml-4">View all →</a>
        </h2>
        <div className="space-y-4">
          {proposals.slice(0, 5).map(p => (
            <div key={p.id} className="bg-white dark:bg-gray-800 rounded-xl p-6 shadow">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold">{p.title}</h3>
                  <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded mt-1 inline-block">{p.type}</span>
                </div>
                <span className={`px-3 py-1 rounded-full text-sm ${p.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                  {p.status}
                </span>
              </div>
              <div className="mt-4 flex gap-4 text-sm text-gray-500">
                <span>👍 {p.votes_for}</span>
                <span>👎 {p.votes_against}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
