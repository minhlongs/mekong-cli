import type { Mission, Tenant } from '../../src/types/raas'
import type { FeedbackRow, InMemoryPilotDbState, OutboxRow } from './pilot-test-db-queries'

function handleInviteAndTenantMutations(
  sql: string,
  args: unknown[],
  state: InMemoryPilotDbState,
  nextCreditId: () => number,
): { success: boolean; meta: { changes: number } } | null {
  const ok = (changes = 1) => ({ success: true, meta: { changes } })
  if (sql.includes('INSERT INTO pilot_invites')) {
    state.invites.push({
      id: String(args[0]), code_hash: String(args[1]), partner_label: (args[2] as string | null) ?? null,
      status: 'active', issued_by: String(args[4]), redeemed_by_tenant_id: null, created_at: String(args[5]), redeemed_at: null,
    })
    return ok()
  }
  if (sql.includes("UPDATE pilot_invites SET status = 'redeemed', redeemed_by_tenant_id = ?, redeemed_at = ?")) {
    const inv = state.invites.find((i) => i.id === String(args[2]) && i.status === 'active')
    if (!inv) return ok(0)
    Object.assign(inv, { status: 'redeemed', redeemed_by_tenant_id: String(args[0]), redeemed_at: String(args[1]) })
    return ok()
  }
  if (sql.includes("UPDATE pilot_invites SET status = 'redeemed'")) {
    const inv = state.invites.find((i) => i.id === String(args[1]) && i.status === 'active')
    if (!inv) return ok(0)
    Object.assign(inv, { status: 'redeemed', redeemed_at: String(args[0]) })
    return ok()
  }
  if (sql.includes('UPDATE pilot_invites SET redeemed_by_tenant_id = ?')) {
    const inv = state.invites.find((i) => i.id === String(args[1]))
    if (inv) inv.redeemed_by_tenant_id = String(args[0])
    return ok(inv ? 1 : 0)
  }
  if (sql.includes('INSERT INTO tenants')) {
    state.tenants.push({
      id: String(args[0]), name: String(args[1]), api_key_hash: String(args[2]),
      tier: (args[3] as Tenant['tier']) ?? 'free', created_at: String(args[4]),
    })
    return ok()
  }
  if (sql.includes('INSERT INTO credits')) {
    state.credits.push({
      id: nextCreditId(), tenant_id: String(args[0]), amount: Number(args[1]),
      reason: String(args[2] ?? ''), created_at: new Date().toISOString(),
    })
    return ok()
  }
  if (sql.includes('INSERT OR IGNORE INTO mission_credit_events')) {
    const key = String(args[0])
    if (state.creditEvents.some((e) => e.idempotency_key === key)) return ok(0)
    state.creditEvents.push({
      idempotency_key: key, mission_id: String(args[1]), tenant_id: String(args[2]),
      event_type: String(args[3]), amount: Number(args[4]), credit_entry_id: String(args[5]), created_at: String(args[6]),
    })
    return ok()
  }
  return null
}

export async function executePilotRun(
  sql: string,
  args: unknown[],
  state: InMemoryPilotDbState,
  nextCreditId: () => number,
): Promise<{ success: boolean; meta: { changes: number } }> {
  const firstPass = handleInviteAndTenantMutations(sql, args, state, nextCreditId)
  if (firstPass) return firstPass
  const ok = (changes = 1) => ({ success: true, meta: { changes } })
  const findOpenMission = (id: string) =>
    state.missions.find((m) => m.id === id && m.status !== 'completed' && m.status !== 'failed')

  if (sql.includes('INSERT INTO missions')) {
    const missionId = String(args[0])
    state.missions.push({
      id: missionId, tenant_id: String(args[1]), goal: String(args[2]), status: 'pending',
      credits_used: Number(args[4]), total_steps: 0, completed_steps: 0, result: null,
      created_at: String(args[5]), completed_at: null,
    })
    state.statusHistory.push({ missionId, status: 'pending' })
    return ok()
  }
  if (sql.includes("WHERE id = ? AND status = 'pending'")) {
    const status = args[0] as Mission['status']
    const missionId = String(args[3])
    const m = state.missions.find((item) => item.id === missionId && item.status === 'pending')
    if (!m) return ok(0)
    Object.assign(m, { status, result: String(args[1]), completed_at: (args[2] as string | null) ?? null })
    state.statusHistory.push({ missionId, status })
    return ok()
  }
  if (sql.includes('UPDATE missions SET status = ?, total_steps = ?')) {
    const status = args[0] as Mission['status']
    const missionId = String(args[5])
    const m = findOpenMission(missionId)
    if (!m) return ok(0)
    Object.assign(m, {
      status, total_steps: Number(args[1]), completed_steps: Number(args[2]),
      result: String(args[3]), completed_at: String(args[4]),
    })
    state.statusHistory.push({ missionId, status })
    return ok()
  }
  if (sql.includes('UPDATE missions SET status = ?, result = ?')) {
    const status = args[0] as Mission['status']
    const missionId = String(args[3])
    const m = findOpenMission(missionId)
    if (!m) return ok(0)
    Object.assign(m, { status, result: String(args[1]), completed_at: (args[2] as string | null) ?? null })
    state.statusHistory.push({ missionId, status })
    return ok()
  }
  if (sql.includes('UPDATE missions SET status = ?, completed_at = ?')) {
    const status = args[0] as Mission['status']
    const missionId = String(args[2])
    const m = findOpenMission(missionId)
    if (!m) return ok(0)
    Object.assign(m, { status, completed_at: (args[1] as string | null) ?? null })
    state.statusHistory.push({ missionId, status })
    return ok()
  }
  if (sql.includes('INSERT OR REPLACE INTO mission_outbox')) {
    const row: OutboxRow = {
      id: String(args[0]), mission_id: String(args[1]), tenant_id: String(args[2]),
      payload_json: String(args[3]), status: String(args[4]), attempts: 0, last_error: null,
      created_at: String(args[5]), updated_at: String(args[6]),
    }
    const idx = state.outbox.findIndex((o) => o.mission_id === row.mission_id)
    if (idx >= 0) state.outbox[idx] = row
    else state.outbox.push(row)
    return ok()
  }
  if (sql.includes("UPDATE mission_outbox SET status = 'published'")) {
    const out = state.outbox.find((o) => o.mission_id === String(args[1]))
    if (out) out.status = 'published'
    return ok()
  }
  if (sql.includes("UPDATE mission_outbox SET status = 'processed'")) {
    const out = state.outbox.find((o) => o.mission_id === String(args[2]))
    if (out) Object.assign(out, { status: 'processed', attempts: Number(args[0]) })
    return ok()
  }
  if (sql.includes("UPDATE mission_outbox SET status = 'dlq'")) {
    const out = state.outbox.find((o) => o.mission_id === String(args[3]))
    if (out) Object.assign(out, { status: 'dlq', attempts: Number(args[0]), last_error: String(args[1]) })
    return ok()
  }
  if (sql.includes('UPDATE mission_outbox SET attempts = ?')) {
    const out = state.outbox.find((o) => o.mission_id === String(args[3]))
    if (out) Object.assign(out, { attempts: Number(args[0]), last_error: String(args[1]) })
    return ok()
  }
  if (sql.includes('INSERT OR REPLACE INTO mission_feedback')) {
    const row: FeedbackRow = {
      mission_id: String(args[0]), tenant_id: String(args[1]), rating: Number(args[2]),
      comment: (args[3] as string | null) ?? null, within_48h: Number(args[4]), submitted_at: String(args[5]),
    }
    const idx = state.feedback.findIndex((f) => f.mission_id === row.mission_id)
    if (idx >= 0) state.feedback[idx] = row
    else state.feedback.push(row)
    return ok()
  }
  return ok()
}
