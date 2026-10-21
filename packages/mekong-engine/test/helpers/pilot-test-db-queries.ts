import type { PilotInviteRecord } from '../../src/raas/invite-codes'
import type { Mission, Tenant } from '../../src/types/raas'

export interface OutboxRow {
  id: string
  mission_id: string
  tenant_id: string
  payload_json: string
  status: string
  attempts: number
  last_error: string | null
  created_at: string
  updated_at: string
}

export interface CreditEventRow {
  idempotency_key: string
  mission_id: string
  tenant_id: string
  event_type: string
  amount: number
  credit_entry_id: string
  created_at: string
}

export interface CreditRow {
  id: number
  tenant_id: string
  amount: number
  reason: string
  created_at: string
}

export interface FeedbackRow {
  mission_id: string
  tenant_id: string
  rating: number
  comment: string | null
  within_48h: number
  submitted_at: string
}

export interface InMemoryPilotDbState {
  invites: PilotInviteRecord[]
  tenants: Tenant[]
  credits: CreditRow[]
  creditEvents: CreditEventRow[]
  missions: Mission[]
  outbox: OutboxRow[]
  feedback: FeedbackRow[]
  statusHistory: Array<{ missionId: string; status: string }>
}

export async function executePilotFirst<T = unknown>(
  sql: string,
  boundArgs: unknown[],
  state: InMemoryPilotDbState,
): Promise<T | null> {
  if (sql.includes('COUNT(*) as total FROM pilot_invites')) {
    const total = state.invites.filter((i) => i.status === 'active' || i.status === 'redeemed').length
    return { total } as unknown as T
  }
  if (sql.includes('FROM pilot_invites WHERE code_hash = ?')) {
    const codeHash = String(boundArgs[0])
    return (state.invites.find((i) => i.code_hash === codeHash) ?? null) as unknown as T
  }
  if (sql.includes('FROM tenants WHERE api_key_hash = ?')) {
    const hash = String(boundArgs[0])
    return (state.tenants.find((t) => t.api_key_hash === hash) ?? null) as unknown as T
  }
  if (sql.includes('SUM(amount)') && sql.includes('FROM credits')) {
    const tenantId = String(boundArgs[0])
    const balance = state.credits
      .filter((c) => c.tenant_id === tenantId)
      .reduce((acc, c) => acc + c.amount, 0)
    return { balance } as unknown as T
  }
  if (sql.includes('FROM mission_credit_events WHERE idempotency_key = ?')) {
    const key = String(boundArgs[0])
    return (state.creditEvents.find((e) => e.idempotency_key === key) ?? null) as unknown as T
  }
  if (sql.includes('FROM missions WHERE id = ? AND tenant_id = ?')) {
    const missionId = String(boundArgs[0])
    const tenantId = String(boundArgs[1])
    return (state.missions.find((m) => m.id === missionId && m.tenant_id === tenantId) ?? null) as unknown as T
  }
  if (sql.includes("COUNT(*) as count FROM missions WHERE status IN ('planning', 'executing', 'verifying', 'running')")) {
    const activeStatuses = new Set(['planning', 'executing', 'verifying', 'running'])
    const count = state.missions.filter((m) => activeStatuses.has(m.status)).length
    return { count } as unknown as T
  }
  return null
}

export async function executePilotAll<T = unknown>(
  sql: string,
  boundArgs: unknown[],
  state: InMemoryPilotDbState,
): Promise<{ results: T[] }> {
  if (sql.includes('FROM pilot_invites')) {
    return { results: [...state.invites] as unknown as T[] }
  }
  if (sql.includes('FROM credits WHERE tenant_id = ?')) {
    const tenantId = String(boundArgs[0])
    const rows = state.credits.filter((c) => c.tenant_id === tenantId)
    return { results: rows as unknown as T[] }
  }
  if (sql.includes('FROM missions WHERE tenant_id = ?')) {
    const tenantId = String(boundArgs[0])
    const rows = state.missions.filter((m) => m.tenant_id === tenantId)
    return { results: rows as unknown as T[] }
  }
  if (sql.includes('SELECT id, tenant_id, status FROM missions')) {
    return { results: [...state.missions] as unknown as T[] }
  }
  if (sql.includes('FROM mission_feedback')) {
    return { results: [...state.feedback] as unknown as T[] }
  }
  if (sql.includes('FROM mission_outbox WHERE status =')) {
    const rows = state.outbox.filter((o) => o.status === 'pending')
    return { results: rows as unknown as T[] }
  }
  return { results: [] }
}
