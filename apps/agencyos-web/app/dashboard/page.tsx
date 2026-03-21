'use client'

import { useEffect, useState } from 'react'
import { createRaasClient } from '../../lib/raas-client'

interface DashboardData {
  profile: { name: string; email: string; tier: string; balance: number } | null
  analytics: { summary: any; byStatus: any; daily: any[] } | null
  missions: any[]
  referrals: { referralCode: string; totalReferred: number; creditsEarned: number } | null
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData>({ profile: null, analytics: null, missions: [], referrals: null })
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState('')
  const [loginEmail, setLoginEmail] = useState('')

  // Check for stored token
  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('raas_token') : null
    if (stored) { setToken(stored); loadDashboard(stored) }
    else setLoading(false)
  }, [])

  async function loadDashboard(t: string) {
    setLoading(true)
    const client = createRaasClient({ token: t })
    try {
      const [profile, analytics, missionData, referrals] = await Promise.all([
        client.getProfile().catch(() => null),
        client.getAnalytics().catch(() => null),
        client.listMissions({ limit: 10 }).catch(() => ({ missions: [] })),
        client.getReferrals().catch(() => null),
      ])
      setData({ profile, analytics, missions: missionData.missions, referrals })
    } catch { localStorage.removeItem('raas_token'); setToken('') }
    setLoading(false)
  }

  async function handleLogin() {
    if (!loginEmail) return
    const client = createRaasClient()
    try {
      const res = await client.login(loginEmail)
      localStorage.setItem('raas_token', res.token)
      setToken(res.token)
      loadDashboard(res.token)
    } catch (e: any) { alert(e.message) }
  }

  function logout() {
    localStorage.removeItem('raas_token')
    setToken('')
    setData({ profile: null, analytics: null, missions: [], referrals: null })
  }

  // Login screen
  if (!token) {
    return (
      <main className="min-h-screen bg-zinc-950 text-white flex items-center justify-center">
        <div className="bg-zinc-900 border border-zinc-800 rounded-xl p-8 w-full max-w-sm">
          <h1 className="text-2xl font-bold mb-4 text-cyan-400">Mekong Dashboard</h1>
          <input className="w-full p-3 rounded-lg bg-zinc-800 border border-zinc-700 text-white mb-3"
            placeholder="your@email.com" value={loginEmail} onChange={e => setLoginEmail(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleLogin()} />
          <button onClick={handleLogin}
            className="w-full p-3 rounded-lg bg-cyan-500 text-black font-bold hover:opacity-90">
            Login
          </button>
        </div>
      </main>
    )
  }

  if (loading) return <main className="min-h-screen bg-zinc-950 text-white p-8"><p className="text-zinc-400">Loading...</p></main>

  const { profile, analytics, missions, referrals } = data
  const s = analytics?.summary || {}

  return (
    <main className="min-h-screen bg-zinc-950 text-white p-8 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h1 className="text-2xl font-bold">Welcome, {profile?.name || 'User'}</h1>
          <p className="text-zinc-400 text-sm">{profile?.email} | {profile?.tier} tier</p>
        </div>
        <button onClick={logout} className="text-zinc-500 hover:text-white text-sm">Logout</button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {[
          { label: 'Balance', value: `${profile?.balance ?? 0} MCU`, color: 'text-cyan-400' },
          { label: 'Missions', value: s.totalMissions ?? 0, color: 'text-white' },
          { label: 'Credits Used', value: s.totalCreditsUsed ?? 0, color: 'text-orange-400' },
          { label: 'Referrals', value: referrals?.totalReferred ?? 0, color: 'text-green-400' },
        ].map((stat, i) => (
          <div key={i} className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
            <p className="text-zinc-500 text-xs mb-1">{stat.label}</p>
            <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Missions */}
      <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 overflow-hidden mb-8">
        <div className="px-5 py-4 border-b border-zinc-800 flex justify-between">
          <h2 className="font-semibold">Recent Missions</h2>
          <span className="text-zinc-500 text-sm">{missions.length} shown</span>
        </div>
        <div className="divide-y divide-zinc-800/60">
          {missions.length === 0 && <p className="px-5 py-4 text-zinc-500">No missions yet</p>}
          {missions.map((m: any) => (
            <div key={m.id} className="px-5 py-3 flex items-center gap-4 text-sm">
              <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                m.status === 'completed' ? 'bg-green-500/20 text-green-400' :
                m.status === 'failed' ? 'bg-red-500/20 text-red-400' :
                m.status === 'queued' ? 'bg-zinc-700/60 text-zinc-400' :
                'bg-blue-500/20 text-blue-400'
              }`}>{m.status}</span>
              <span className="flex-1 truncate">{m.goal}</span>
              <span className="text-zinc-500">{m.creditsCost} MCU</span>
            </div>
          ))}
        </div>
      </div>

      {/* Referral */}
      {referrals && (
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 p-5">
          <h2 className="font-semibold mb-2">Referral Program</h2>
          <p className="text-sm text-zinc-400">
            Share your code: <span className="text-cyan-400 font-mono">{referrals.referralCode}</span> —
            both get +5 MCU. Referred: {referrals.totalReferred} | Earned: {referrals.creditsEarned} MCU
          </p>
        </div>
      )}
    </main>
  )
}
