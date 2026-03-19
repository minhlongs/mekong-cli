import { Hono } from 'hono'
import { z } from 'zod'
import type { D1Database } from '@cloudflare/workers-types'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { createError, handleAsync, handleDb } from '../types/error'

type Variables = { tenant: Tenant }
const ledgerRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
ledgerRoutes.use('*', authMiddleware)

// Zod schemas
const transferSchema = z.object({
  from_code: z.string().min(1, 'from_code is required').max(100, 'from_code must be ≤100 chars'),
  to_code: z.string().min(1, 'to_code is required').max(100, 'to_code must be ≤100 chars'),
  amount: z.number().positive('amount must be positive').max(1_000_000_000, 'amount too large'),
  description: z.string().max(500, 'description must be ≤500 chars').optional(),
  entry_type: z.string().max(50, 'entry_type must be ≤50 chars').optional(),
  idempotency_key: z.string().max(100, 'idempotency_key must be ≤100 chars').optional(),
})
type TransferInput = z.infer<typeof transferSchema>

const topupSchema = z.object({
  account_code: z.string().min(1, 'account_code is required').max(100, 'account_code must be ≤100 chars'),
  amount: z.number().positive('amount must be positive').max(1_000_000_000, 'amount too large'),
  description: z.string().max(500, 'description must be ≤500 chars').optional(),
})
type TopupInput = z.infer<typeof topupSchema>

// Ensure account exists (upsert)
async function ensureAccount(db: D1Database, tenantId: string, code: string, type: string, ownerId?: string) {
  return await handleDb(
    async () => {
      const existing = await db.prepare('SELECT id FROM ledger_accounts WHERE tenant_id = ? AND code = ?').bind(tenantId, code).first()
      if (existing) return existing.id as string
      const id = crypto.randomUUID()
      await db.prepare('INSERT INTO ledger_accounts (id, tenant_id, owner_id, code, account_type) VALUES (?, ?, ?, ?, ?)')
        .bind(id, tenantId, ownerId || null, code, type).run()
      return id
    },
    'DATABASE_ERROR',
    'Failed to ensure account exists'
  )
}

// POST /transfer — Double-entry transfer between accounts
ledgerRoutes.post('/transfer', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')

  let body: TransferInput
  try {
    body = transferSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const db = c.env.DB

  // Idempotency check
  if (body.idempotency_key) {
    const existingResult = await handleDb(
      async () => {
        const result = await db.prepare('SELECT id FROM journal_entries WHERE idempotency_key = ?').bind(body.idempotency_key).first()
        return result as { id: string } | null
      },
      'DATABASE_ERROR',
      'Failed to check idempotency'
    )
    if (existingResult) return c.json({ journal_entry_id: existingResult.id, status: 'already_processed' })
  }

  // Ensure accounts exist
  const fromAcctId = await ensureAccount(db, tenant.id, body.from_code, 'asset')
  const toAcctId = await ensureAccount(db, tenant.id, body.to_code, 'asset')

  // Check balance
  const fromAcct = await handleDb(
    async () => {
      const result = await db.prepare('SELECT balance FROM ledger_accounts WHERE id = ?').bind(fromAcctId).first()
      return result as { balance: number } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch account balance'
  )
  if ((fromAcct?.balance || 0) < body.amount) {
    return c.json(createError('INSUFFICIENT_CREDITS', 'Insufficient balance', [{ balance: fromAcct?.balance ?? 0 }]), 402)
  }

  // Create journal entry + 2 transaction lines (ATOMIC)
  const jeId = crypto.randomUUID()
  const line1Id = crypto.randomUUID()
  const line2Id = crypto.randomUUID()

  const batch = [
    db.prepare('INSERT INTO journal_entries (id, tenant_id, description, entry_type, idempotency_key) VALUES (?, ?, ?, ?, ?)')
      .bind(jeId, tenant.id, body.description, body.entry_type || 'transfer', body.idempotency_key || null),
    // Debit from source (decrease)
    db.prepare('INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction) VALUES (?, ?, ?, ?, ?)')
      .bind(line1Id, jeId, fromAcctId, body.amount, -1),
    // Credit to destination (increase)
    db.prepare('INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction) VALUES (?, ?, ?, ?, ?)')
      .bind(line2Id, jeId, toAcctId, body.amount, 1),
    // Update balances
    db.prepare('UPDATE ledger_accounts SET balance = balance - ? WHERE id = ?').bind(body.amount, fromAcctId),
    db.prepare('UPDATE ledger_accounts SET balance = balance + ? WHERE id = ?').bind(body.amount, toAcctId),
  ]
  await handleDb(
    () => db.batch(batch),
    'DATABASE_ERROR',
    'Failed to execute transfer'
  )

  return c.json({ journal_entry_id: jeId, from: body.from_code, to: body.to_code, amount: body.amount }, 201)
}))

// POST /topup — Add credits to an account (from platform)
ledgerRoutes.post('/topup', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')

  let body: TopupInput
  try {
    body = topupSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    return c.json(createError('BAD_REQUEST', 'Invalid JSON'), 400)
  }

  const acctId = await ensureAccount(c.env.DB, tenant.id, body.account_code, 'asset')
  const platformId = await ensureAccount(c.env.DB, tenant.id, 'platform:treasury', 'equity')

  const jeId = crypto.randomUUID()
  await handleDb(
    () => c.env.DB.batch([
      c.env.DB.prepare('INSERT INTO journal_entries (id, tenant_id, description, entry_type) VALUES (?, ?, ?, ?)')
        .bind(jeId, tenant.id, body.description || 'Credit top-up', 'topup'),
      c.env.DB.prepare('INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction) VALUES (?, ?, ?, ?, ?)')
        .bind(crypto.randomUUID(), jeId, platformId, body.amount, -1),
      c.env.DB.prepare('INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction) VALUES (?, ?, ?, ?, ?)')
        .bind(crypto.randomUUID(), jeId, acctId, body.amount, 1),
      c.env.DB.prepare('UPDATE ledger_accounts SET balance = balance + ? WHERE id = ?').bind(body.amount, acctId),
    ]),
    'DATABASE_ERROR',
    'Failed to execute topup'
  )

  return c.json({ journal_entry_id: jeId, account: body.account_code, credited: body.amount }, 201)
}))

// GET /balance — Account balance(s)
ledgerRoutes.get('/balance', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  const code = c.req.query('code')
  const query = code
    ? 'SELECT * FROM ledger_accounts WHERE tenant_id = ? AND code = ?'
    : 'SELECT * FROM ledger_accounts WHERE tenant_id = ? ORDER BY code'
  const params = code ? [tenant.id, code] : [tenant.id]
  const rowsResult = await handleDb(
    async () => {
      const result = await c.env.DB.prepare(query).bind(...params).all()
      return result as { results?: unknown[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch account balances'
  )
  return c.json({ accounts: rowsResult.results })
}))

// GET /history — Transaction log
ledgerRoutes.get('/history', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  const limit = Math.min(parseInt(c.req.query('limit') || '30'), 100)
  const rowsResult = await handleDb(
    async () => {
      const result = await c.env.DB.prepare(
        `SELECT je.*, GROUP_CONCAT(tl.account_id || ':' || tl.amount || ':' || tl.direction) as lines
         FROM journal_entries je LEFT JOIN transaction_lines tl ON tl.journal_entry_id = je.id
         WHERE je.tenant_id = ? GROUP BY je.id ORDER BY je.posted_at DESC LIMIT ?`
      ).bind(tenant.id, limit).all()
      return result as { results?: unknown[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch transaction history'
  )
  return c.json({ entries: rowsResult.results })
}))

export { ledgerRoutes }
