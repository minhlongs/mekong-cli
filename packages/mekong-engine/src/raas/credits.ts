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
