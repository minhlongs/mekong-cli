import type { D1Database } from '@cloudflare/workers-types'
import type { CreditEntry } from '../types/raas'
import { CreditEntrySchema } from '../types/raas'

export async function getBalance(db: D1Database, tenantId: string): Promise<number> {
  const result = await db
    .prepare('SELECT COALESCE(SUM(amount), 0) as balance FROM credits WHERE tenant_id = ?')
    .bind(tenantId)
    .first<{ balance: number }>()
  return result?.balance ?? 0
}

export async function addCredits(
  db: D1Database,
  tenantId: string,
  amount: number,
  reason: string,
): Promise<number> {
  if (amount < 0) {
    throw new Error('Cannot add negative credits')
  }
  await db
    .prepare('INSERT INTO credits (tenant_id, amount, reason) VALUES (?, ?, ?)')
    .bind(tenantId, amount, reason)
    .run()
  return getBalance(db, tenantId)
}

export async function deductCredits(
  db: D1Database,
  tenantId: string,
  amount: number,
  reason: string,
): Promise<boolean> {
  const balance = await getBalance(db, tenantId)
  if (balance < amount) return false
  await db
    .prepare('INSERT INTO credits (tenant_id, amount, reason) VALUES (?, ?, ?)')
    .bind(tenantId, -amount, reason)
    .run()
  return true
}

/**
 * Check if tenant has sufficient credits
 * Returns true if balance >= required amount
 */
export async function hasSufficientCredits(
  db: D1Database,
  tenantId: string,
  amount: number,
): Promise<boolean> {
  const balance = await getBalance(db, tenantId)
  return balance >= amount
}

/**
 * Require sufficient credits helper
 * Throws error if balance is insufficient (for use in routes)
 */
export async function requireSufficientCredits(
  db: D1Database,
  tenantId: string,
  amount: number,
): Promise<{ balance: number }> {
  const balance = await getBalance(db, tenantId)
  if (balance < amount) {
    throw new Error(`INSUFFICIENT_CREDITS: Required ${amount}, has ${balance}`)
  }
  return { balance }
}

export async function getHistory(
  db: D1Database,
  tenantId: string,
  limit = 50,
): Promise<CreditEntry[]> {
  const { results } = await db
    .prepare(
      'SELECT id, tenant_id, amount, COALESCE(reason, \'\') as reason, created_at FROM credits WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?',
    )
    .bind(tenantId, limit)
    .all()
  return results.map((row) => CreditEntrySchema.parse(row))
}

export async function ensureMissionCreditEventsTable(db: D1Database): Promise<void> {
  await db
    .exec(
      `CREATE TABLE IF NOT EXISTS mission_credit_events (idempotency_key TEXT PRIMARY KEY, mission_id TEXT NOT NULL, tenant_id TEXT NOT NULL, event_type TEXT NOT NULL, amount INTEGER NOT NULL, credit_entry_id TEXT NOT NULL, created_at TEXT NOT NULL DEFAULT (datetime('now')))`,
    )
    .catch(() => {})
}

export async function deductMissionCreditsOnce(
  db: D1Database,
  tenantId: string,
  missionId: string,
  amount: number,
  reason: string,
): Promise<{ deducted: boolean; alreadyProcessed: boolean }> {
  await ensureMissionCreditEventsTable(db)
  const idempotencyKey = `debit:mission:${missionId}`
  const existing = await db
    .prepare('SELECT idempotency_key FROM mission_credit_events WHERE idempotency_key = ?')
    .bind(idempotencyKey)
    .first<{ idempotency_key: string }>()

  if (existing) return { deducted: true, alreadyProcessed: true }

  const balance = await getBalance(db, tenantId)
  if (balance < amount) return { deducted: false, alreadyProcessed: false }

  const now = new Date().toISOString()
  const eventStmt = db
    .prepare(
      'INSERT OR IGNORE INTO mission_credit_events (idempotency_key, mission_id, tenant_id, event_type, amount, credit_entry_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
    )
    .bind(idempotencyKey, missionId, tenantId, 'debit', -amount, crypto.randomUUID(), now)
  const creditStmt = db
    .prepare('INSERT INTO credits (tenant_id, amount, reason) VALUES (?, ?, ?)')
    .bind(tenantId, -amount, reason)

  if (typeof db.batch === 'function') {
    const [evRes] = await db.batch([eventStmt, creditStmt])
    const changes = (evRes as { meta?: { changes?: number } })?.meta?.changes ?? 0
    if (changes === 0) return { deducted: true, alreadyProcessed: true }
  } else {
    const evRes = await eventStmt.run()
    const changes = (evRes as { meta?: { changes?: number } })?.meta?.changes ?? 0
    if (changes === 0) return { deducted: true, alreadyProcessed: true }
    await creditStmt.run()
  }

  return { deducted: true, alreadyProcessed: false }
}

export async function refundMissionCreditsOnce(
  db: D1Database,
  tenantId: string,
  missionId: string,
  amount: number,
  reason: string,
): Promise<{ refunded: boolean; alreadyRefunded: boolean; newBalance: number }> {
  await ensureMissionCreditEventsTable(db)
  const debitKey = `debit:mission:${missionId}`
  const priorDebit = await db
    .prepare('SELECT idempotency_key FROM mission_credit_events WHERE idempotency_key = ?')
    .bind(debitKey)
    .first<{ idempotency_key: string }>()
  if (!priorDebit) {
    return { refunded: false, alreadyRefunded: false, newBalance: await getBalance(db, tenantId) }
  }

  const idempotencyKey = `refund:mission:${missionId}`
  const existing = await db
    .prepare('SELECT idempotency_key FROM mission_credit_events WHERE idempotency_key = ?')
    .bind(idempotencyKey)
    .first<{ idempotency_key: string }>()
  if (existing) {
    return { refunded: false, alreadyRefunded: true, newBalance: await getBalance(db, tenantId) }
  }

  const now = new Date().toISOString()
  const eventStmt = db
    .prepare(
      'INSERT OR IGNORE INTO mission_credit_events (idempotency_key, mission_id, tenant_id, event_type, amount, credit_entry_id, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)',
    )
    .bind(idempotencyKey, missionId, tenantId, 'refund', amount, crypto.randomUUID(), now)
  const creditStmt = db
    .prepare('INSERT INTO credits (tenant_id, amount, reason) VALUES (?, ?, ?)')
    .bind(tenantId, amount, reason)

  const [insertEvent] = typeof db.batch === 'function'
    ? await db.batch([eventStmt, creditStmt])
    : [await eventStmt.run(), await creditStmt.run()]

  const changes = (insertEvent as { meta?: { changes?: number } })?.meta?.changes ?? 0
  if (changes === 0) {
    return { refunded: false, alreadyRefunded: true, newBalance: await getBalance(db, tenantId) }
  }

  return { refunded: true, alreadyRefunded: false, newBalance: await getBalance(db, tenantId) }
}
