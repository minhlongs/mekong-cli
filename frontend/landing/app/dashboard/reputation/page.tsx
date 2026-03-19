'use client'
import { useState, useEffect } from 'react'
import { api } from '@/lib/api'

export default function ReputationPage() {
  const [leaderboard, setLeaderboard] = useState<any[]>([])

  useEffect(() => {
    api.getReputation().then(r => setLeaderboard(r.leaderboard || [])).catch(console.error)
  }, [])

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Reputation Leaderboard</h1>
      <div className="rounded-xl border border-[var(--md-outline-variant)] bg-[var(--md-surface-container-low)] overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-[var(--md-surface-container)]">
            <tr>
              <th className="text-left p-3">#</th>
              <th className="text-left p-3">Ten</th>
              <th className="text-left p-3">Role</th>
              <th className="text-left p-3">Gov. Level</th>
              <th className="text-right p-3">Reputation</th>
            </tr>
          </thead>
          <tbody>
            {leaderboard.map((s: any, i: number) => (
              <tr key={s.id} className="border-t border-[var(--md-outline-variant)]">
                <td className="p-3 font-bold">{i + 1}</td>
                <td className="p-3">{s.display_name}</td>
                <td className="p-3"><span className="px-2 py-0.5 text-xs rounded bg-blue-500/10 text-blue-400">{s.role}</span></td>
                <td className="p-3">{s.governance_level}/6</td>
                <td className="p-3 text-right font-bold text-emerald-400">{s.reputation_score}</td>
              </tr>
            ))}
            {leaderboard.length === 0 && (
              <tr><td colSpan={5} className="p-6 text-center text-[var(--md-on-surface-variant)]">Chua co du lieu reputation.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}
