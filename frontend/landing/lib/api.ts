const API_BASE = process.env.NEXT_PUBLIC_ENGINE_URL || 'http://localhost:8787'

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const token = typeof window !== 'undefined' ? localStorage.getItem('mekong_api_key') : null
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options?.headers,
    },
  })
  if (!res.ok) throw new Error(`API ${res.status}: ${res.statusText}`)
  return res.json() as Promise<T>
}

export const api = {
  // Governance
  listStakeholders: () => apiFetch<any>('/v1/governance/stakeholders'),
  registerStakeholder: (data: any) => apiFetch<any>('/v1/governance/stakeholders', { method: 'POST', body: JSON.stringify(data) }),
  listProposals: (status?: string) => apiFetch<any>(`/v1/governance/proposals${status ? `?status=${status}` : ''}`),
  createProposal: (data: any) => apiFetch<any>('/v1/governance/proposals', { method: 'POST', body: JSON.stringify(data) }),
  castVote: (data: any) => apiFetch<any>('/v1/governance/vote', { method: 'POST', body: JSON.stringify(data) }),
  getReputation: () => apiFetch<any>('/v1/governance/reputation'),
  getNguSu: () => apiFetch<any>('/v1/governance/ngu-su'),
  scoreNguSu: (data: any) => apiFetch<any>('/v1/governance/ngu-su', { method: 'POST', body: JSON.stringify(data) }),
  getTreasury: () => apiFetch<any>('/v1/governance/treasury'),
  getLedgerBalance: () => apiFetch<any>('/v1/ledger/balance'),
  getLedgerHistory: () => apiFetch<any>('/v1/ledger/history'),
}
