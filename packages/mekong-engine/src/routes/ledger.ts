import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'

type Variables = { tenant: Tenant }
const ledgerRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
ledgerRoutes.use('*', authMiddleware)

// Ensure account exists (upsert)
async function ensureAccount(db: D1Database, tenantId: string, code: string, type: string, ownerId?: string) {
  const existing = await db.prepare('SELECT id FROM ledger_accounts WHERE tenant_id = ? AND code = ?').bind(tenantId, code).first()
  if (existing) return existing.id as string
  const id = crypto.randomUUID()
  await db.prepare('INSERT INTO ledger_accounts (id, tenant_id, owner_id, code, account_type) VALUES (?, ?, ?, ?, ?)')
    .bind(id, tenantId, ownerId || null, code, type).run()
  return id
}

// POST /transfer — Double-entry transfer between accounts
ledgerRoutes.post('/transfer', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const body = await c.req.json<{
    from_code: string; to_code: string; amount: number;
    description: string; entry_type?: string; idempotency_key?: string
  }>()

  if (!body.from_code || !body.to_code || !body.amount || body.amount <= 0) {
    return c.json({ error: 'Missing from_code, to_code, or positive amount' }, 400)
  }

  const db = c.env.DB

  // Idempotency check
  if (body.idempotency_key) {
    const existing = await db.prepare('SELECT id FROM journal_entries WHERE idempotency_key = ?').bind(body.idempotency_key).first()
    if (existing) return c.json({ journal_entry_id: existing.id, status: 'already_processed' })
  }

  // Ensure accounts exist
  const fromAcctId = await ensureAccount(db, tenant.id, body.from_code, 'asset')
  const toAcctId = await ensureAccount(db, tenant.id, body.to_code, 'asset')

  // Check balance
  const fromAcct = await db.prepare('SELECT balance FROM ledger_accounts WHERE id = ?').bind(fromAcctId).first()
  if ((fromAcct?.balance as number || 0) < body.amount) {
    return c.json({ error: 'Insufficient balance', balance: fromAcct?.balance }, 400)
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
  await db.batch(batch)

  return c.json({ journal_entry_id: jeId, from: body.from_code, to: body.to_code, amount: body.amount }, 201)
})

// POST /topup — Add credits to an account (from platform)
ledgerRoutes.post('/topup', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const body = await c.req.json<{ account_code: string; amount: number; description?: string }>()

  const acctId = await ensureAccount(c.env.DB, tenant.id, body.account_code, 'asset')
  const platformId = await ensureAccount(c.env.DB, tenant.id, 'platform:treasury', 'equity')

  const jeId = crypto.randomUUID()
  await c.env.DB.batch([
    c.env.DB.prepare('INSERT INTO journal_entries (id, tenant_id, description, entry_type) VALUES (?, ?, ?, ?)')
      .bind(jeId, tenant.id, body.description || 'Credit top-up', 'topup'),
    c.env.DB.prepare('INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction) VALUES (?, ?, ?, ?, ?)')
      .bind(crypto.randomUUID(), jeId, platformId, body.amount, -1),
    c.env.DB.prepare('INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction) VALUES (?, ?, ?, ?, ?)')
      .bind(crypto.randomUUID(), jeId, acctId, body.amount, 1),
    c.env.DB.prepare('UPDATE ledger_accounts SET balance = balance + ? WHERE id = ?').bind(body.amount, acctId),
  ])

  return c.json({ journal_entry_id: jeId, account: body.account_code, credited: body.amount }, 201)
})

// GET /balance — Account balance(s)
ledgerRoutes.get('/balance', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const code = c.req.query('code')
  const query = code
    ? 'SELECT * FROM ledger_accounts WHERE tenant_id = ? AND code = ?'
    : 'SELECT * FROM ledger_accounts WHERE tenant_id = ? ORDER BY code'
  const params = code ? [tenant.id, code] : [tenant.id]
  const rows = await c.env.DB.prepare(query).bind(...params).all()
  return c.json({ accounts: rows.results })
})

// GET /history — Transaction log
ledgerRoutes.get('/history', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const limit = Math.min(parseInt(c.req.query('limit') || '30'), 100)
  const rows = await c.env.DB.prepare(
    `SELECT je.*, GROUP_CONCAT(tl.account_id || ':' || tl.amount || ':' || tl.direction) as lines
     FROM journal_entries je LEFT JOIN transaction_lines tl ON tl.journal_entry_id = je.id
     WHERE je.tenant_id = ? GROUP BY je.id ORDER BY je.posted_at DESC LIMIT ?`
  ).bind(tenant.id, limit).all()
  return c.json({ entries: rows.results })
})

export { ledgerRoutes }
