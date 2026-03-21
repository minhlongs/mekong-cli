'use client'

import { useEffect, useState } from 'react'
import { createRaasClient } from '../../lib/raas-client'
import MissionTemplatesPicker from './mission-templates-picker'
import CouponRedemption from './coupon-redemption'
import ReferralLeaderboard from './referral-leaderboard'
import TrialExtensionCta from './trial-extension-cta'

interface DashboardData {
  profile: { name: string; email: string; tier: string; balance: number } | null
  analytics: { summary: any; byStatus: any; daily: any[] } | null
  missions: any[]
  referrals: { referralCode: string; totalReferred: number; creditsEarned: number } | null
  alertCount: number
  marketplace: any[]
}

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? 'https://api.agencyos.network'

const S = {
  page: { minHeight: '100vh', background: '#09090b', color: '#fff', fontFamily: 'system-ui, -apple-system, sans-serif', padding: '2rem', maxWidth: '1100px', margin: '0 auto' } as React.CSSProperties,
  card: { background: 'rgba(24,24,27,0.5)', border: '1px solid #27272a', borderRadius: '12px', padding: '1.25rem' } as React.CSSProperties,
  cardHeader: { padding: '1rem 1.25rem', borderBottom: '1px solid #27272a', display: 'flex', justifyContent: 'space-between', alignItems: 'center' } as React.CSSProperties,
  input: { width: '100%', padding: '0.75rem', borderRadius: '8px', background: '#27272a', border: '1px solid #3f3f46', color: '#fff', marginBottom: '0.75rem', fontSize: '1rem', outline: 'none' } as React.CSSProperties,
  btnPrimary: { width: '100%', padding: '0.75rem', borderRadius: '8px', background: '#06b6d4', color: '#000', fontWeight: 700, border: 'none', cursor: 'pointer', fontSize: '1rem' } as React.CSSProperties,
  btnSmall: { padding: '0.5rem 1rem', borderRadius: '8px', background: '#06b6d4', color: '#000', fontWeight: 700, border: 'none', cursor: 'pointer', fontSize: '0.875rem' } as React.CSSProperties,
  muted: { color: '#71717a', fontSize: '0.75rem' } as React.CSSProperties,
  cyan: { color: '#22d3ee' } as React.CSSProperties,
  badge: (color: string) => ({ padding: '0.125rem 0.5rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 500, background: `${color}20`, color } as React.CSSProperties),
}

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData>({ profile: null, analytics: null, missions: [], referrals: null, alertCount: 0, marketplace: [] })
  const [stripePacks, setStripePacks] = useState<any[]>([])
  const [showPacks, setShowPacks] = useState(false)
  const [packsLoading, setPacksLoading] = useState(false)
  const [loading, setLoading] = useState(true)
  const [token, setToken] = useState('')
  const [loginEmail, setLoginEmail] = useState('')
  // mission goal input state — shared with template picker
  const [missionGoal, setMissionGoal] = useState('')

  useEffect(() => {
    const stored = typeof window !== 'undefined' ? localStorage.getItem('raas_token') : null
    if (stored) { setToken(stored); loadDashboard(stored) }
    else setLoading(false)
  }, [])

  async function loadDashboard(t: string) {
    setLoading(true)
    const client = createRaasClient({ token: t })
    try {
      const [profile, analytics, missionData, referrals, alertCountRes, marketplaceRes] = await Promise.all([
        client.getProfile().catch(() => null),
        client.getAnalytics().catch(() => null),
        client.listMissions({ limit: 10 }).catch(() => ({ missions: [] })),
        client.getReferrals().catch(() => null),
        client.getAlertCount().catch(() => ({ count: 0 })),
        client.getMarketplace({ limit: 6 }).catch(() => ({ missions: [] })),
      ])
      setData({
        profile, analytics, missions: missionData.missions, referrals,
        alertCount: alertCountRes?.count ?? alertCountRes?.unread ?? 0,
        marketplace: marketplaceRes?.missions ?? marketplaceRes?.items ?? [],
      })
    } catch { localStorage.removeItem('raas_token'); setToken('') }
    setLoading(false)
  }

  async function handleLogin() {
    if (!loginEmail) return
    try {
      const res = await createRaasClient().login(loginEmail)
      localStorage.setItem('raas_token', res.token)
      setToken(res.token)
      loadDashboard(res.token)
    } catch (e: any) { alert(e.message) }
  }

  function logout() {
    localStorage.removeItem('raas_token')
    setToken('')
    setData({ profile: null, analytics: null, missions: [], referrals: null, alertCount: 0, marketplace: [] })
  }

  async function handleBuyCredits() {
    setPacksLoading(true); setShowPacks(true)
    try {
      const res = await createRaasClient({ token }).getStripePacks()
      setStripePacks(res?.packs ?? [])
    } catch (e: any) { alert(e.message) }
    setPacksLoading(false)
  }

  async function handleCheckout(packId: string) {
    try {
      const res = await createRaasClient({ token }).createStripeCheckout(packId)
      if (res?.checkoutUrl) window.open(res.checkoutUrl, '_blank')
    } catch (e: any) { alert(e.message) }
  }

  // Login screen
  if (!token) {
    return (
      <main style={{ ...S.page, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ ...S.card, width: '100%', maxWidth: '380px' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '1rem', ...S.cyan }}>Mekong Dashboard</h1>
          <input style={S.input} placeholder="your@email.com" value={loginEmail}
            onChange={e => setLoginEmail(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleLogin()} />
          <button onClick={handleLogin} style={S.btnPrimary}>Login</button>
        </div>
      </main>
    )
  }

  if (loading) return <main style={S.page}><p style={{ color: '#71717a' }}>Loading...</p></main>

  const { profile, analytics, missions, referrals, alertCount, marketplace } = data
  const sm = analytics?.summary || {}
  const statusColor = (s: string) => s === 'completed' ? '#22c55e' : s === 'failed' ? '#ef4444' : s === 'queued' ? '#71717a' : '#3b82f6'

  return (
    <main style={S.page}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700 }}>Welcome, {profile?.name || 'User'}</h1>
          {alertCount > 0 && (
            <span style={{ background: '#ef4444', color: '#fff', borderRadius: '50%', width: '24px', height: '24px', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.7rem', fontWeight: 700 }}>
              {alertCount > 99 ? '99+' : alertCount}
            </span>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <span style={{ color: '#71717a', fontSize: '0.875rem' }}>{profile?.email} | {profile?.tier}</span>
          <button onClick={logout} style={{ background: 'none', border: 'none', color: '#71717a', cursor: 'pointer', fontSize: '0.875rem' }}>Logout</button>
        </div>
      </div>

      {/* Trial Extension CTA */}
      <TrialExtensionCta token={token} apiBase={API_BASE} onExtended={() => loadDashboard(token)} />

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginBottom: '1rem' }}>
        {[
          { label: 'Balance', value: `${profile?.balance ?? 0} MCU`, color: '#22d3ee' },
          { label: 'Missions', value: sm.totalMissions ?? 0, color: '#fff' },
          { label: 'Credits Used', value: sm.totalCreditsUsed ?? 0, color: '#f97316' },
          { label: 'Referrals', value: referrals?.totalReferred ?? 0, color: '#22c55e' },
        ].map((stat, i) => (
          <div key={i} style={S.card}>
            <p style={S.muted}>{stat.label}</p>
            <p style={{ fontSize: '1.5rem', fontWeight: 700, color: stat.color, marginTop: '0.25rem' }}>{stat.value}</p>
          </div>
        ))}
      </div>

      {/* Buy Credits + Coupon — side by side on wide screens */}
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: '1.5rem' }}>
        <button onClick={handleBuyCredits} style={S.btnSmall}>Buy Credits</button>
      </div>
      <CouponRedemption token={token} apiBase={API_BASE} onSuccess={() => loadDashboard(token)} />

      {/* Stripe Packs */}
      {showPacks && (
        <div style={{ ...S.card, marginBottom: '2rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '1rem' }}>
            <h2 style={{ fontWeight: 600, ...S.cyan }}>Credit Packs</h2>
            <button onClick={() => setShowPacks(false)} style={{ background: 'none', border: 'none', color: '#71717a', cursor: 'pointer' }}>Close</button>
          </div>
          {packsLoading && <p style={{ color: '#71717a' }}>Loading...</p>}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '0.75rem' }}>
            {stripePacks.map((p: any) => (
              <div key={p.id} style={{ background: '#27272a', border: '1px solid #3f3f46', borderRadius: '8px', padding: '1rem' }}>
                <p style={{ fontWeight: 600 }}>{p.name}</p>
                <p style={{ color: '#22d3ee', fontSize: '1.25rem', fontWeight: 700, margin: '0.25rem 0' }}>{p.credits} MCU</p>
                <p style={{ color: '#71717a', fontSize: '0.875rem', marginBottom: '0.75rem' }}>${(p.priceInCents / 100).toFixed(0)}</p>
                <button onClick={() => handleCheckout(p.id)} style={{ ...S.btnSmall, width: '100%' }}>Buy</button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mission Templates Picker + goal input */}
      <MissionTemplatesPicker onSelect={(goal) => setMissionGoal(goal)} />
      {missionGoal && (
        <div style={{ ...S.card, marginBottom: '2rem' }}>
          <p style={{ ...S.muted, marginBottom: '0.5rem' }}>Selected template goal — edit and launch:</p>
          <textarea
            value={missionGoal}
            onChange={e => setMissionGoal(e.target.value)}
            rows={3}
            style={{ ...S.input, resize: 'vertical', marginBottom: '0.5rem', fontFamily: 'inherit' }}
          />
          <div style={{ display: 'flex', gap: '0.5rem', justifyContent: 'flex-end' }}>
            <button onClick={() => setMissionGoal('')} style={{ ...S.btnSmall, background: '#27272a', color: '#fff' }}>Clear</button>
            <button style={S.btnSmall}>Launch Mission</button>
          </div>
        </div>
      )}

      {/* Missions */}
      <div style={{ ...S.card, padding: 0, marginBottom: '2rem', overflow: 'hidden' }}>
        <div style={S.cardHeader}>
          <h2 style={{ fontWeight: 600 }}>Recent Missions</h2>
          <span style={S.muted}>{missions.length} shown</span>
        </div>
        {missions.length === 0 && <p style={{ padding: '1rem 1.25rem', color: '#71717a' }}>No missions yet</p>}
        {missions.map((m: any) => (
          <div key={m.id} style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid rgba(39,39,42,0.6)', display: 'flex', alignItems: 'center', gap: '1rem', fontSize: '0.875rem' }}>
            <span style={S.badge(statusColor(m.status))}>{m.status}</span>
            <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{m.goal}</span>
            <span style={{ color: '#71717a' }}>{m.creditsCost} MCU</span>
          </div>
        ))}
      </div>

      {/* Referral Program info */}
      {referrals && (
        <div style={{ ...S.card, marginBottom: '2rem' }}>
          <h2 style={{ fontWeight: 600, marginBottom: '0.5rem' }}>Referral Program</h2>
          <p style={{ fontSize: '0.875rem', color: '#71717a' }}>
            Code: <span style={{ ...S.cyan, fontFamily: 'monospace' }}>{referrals.referralCode}</span> — both get +5 MCU. Referred: {referrals.totalReferred} | Earned: {referrals.creditsEarned} MCU
          </p>
        </div>
      )}

      {/* Referral Leaderboard */}
      <ReferralLeaderboard token={token} apiBase={API_BASE} />

      {/* Marketplace */}
      <div style={{ ...S.card, padding: 0, overflow: 'hidden' }}>
        <div style={{ ...S.cardHeader, flexDirection: 'column', alignItems: 'flex-start' }}>
          <h2 style={{ fontWeight: 600 }}>Featured Marketplace</h2>
          <p style={S.muted}>Public missions from the community</p>
        </div>
        {marketplace.length === 0 ? (
          <p style={{ padding: '1rem 1.25rem', color: '#71717a', fontSize: '0.875rem' }}>No featured missions yet.</p>
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))' }}>
            {marketplace.map((item: any, i: number) => (
              <div key={item.id ?? i} style={{ padding: '1rem 1.25rem', borderBottom: '1px solid #27272a' }}>
                <p style={{ fontSize: '0.875rem', fontWeight: 500, marginBottom: '0.5rem', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.goal ?? item.title}</p>
                <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
                  {item.complexity && <span style={S.badge('#3b82f6')}>{item.complexity}</span>}
                  {item.author && <span style={S.muted}>by {item.author}</span>}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </main>
  )
}
