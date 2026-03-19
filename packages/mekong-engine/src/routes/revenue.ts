import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { createError, handleAsync, handleDb } from '../types/error'

type Variables = { tenant: Tenant }
const revenueRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
revenueRoutes.use('*', authMiddleware)

// Default revenue split config (Binh Pháp tam giác ngược — community gets most)
const DEFAULT_SPLIT = {
  platform: 0.20,       // 20% — Owner (servant, smallest share)
  expert: 0.30,          // 30% — Expert who provided knowledge
  ai_compute: 0.15,      // 15% — LLM inference cost + margin
  developer: 0.15,       // 15% — Developer/agency who brought customer
  community_fund: 0.10,  // 10% — Treasury for quadratic funding
  customer_reward: 0.10, // 10% — Loyalty credits back to customer
}

// Zod schema for POST /split
const splitSchema = z.object({
  total_credits: z.number().int().positive('total_credits must be positive').max(1_000_000_000, 'total_credits too large'),
  customer_account: z.string().min(1, 'customer_account is required').max(100, 'customer_account must be ≤100 chars'),
  expert_account: z.string().uuid('expert_account must be a valid UUID').optional(),
  developer_account: z.string().uuid('developer_account must be a valid UUID').optional(),
  description: z.string().max(500, 'description must be ≤500 chars'),
  split_override: z.record(z.number()).refine(
    (val) => {
      const sum = Object.values(val).reduce((a, b) => a + b, 0)
      return Math.abs(sum - 1.0) < 0.01 // Allow 1% rounding tolerance
    },
    { message: 'split_override percentages must sum to 1.0 (±1%)' }
  ).optional(),
})
type SplitInput = z.infer<typeof splitSchema>

// POST /split — Execute revenue split for a completed task
revenueRoutes.post('/split', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')

  let body: SplitInput
  try {
    body = splitSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    throw error
  }

  const split = body.split_override || DEFAULT_SPLIT
  const db = c.env.DB

  // Ensure all accounts exist
  const ensureAcct = async (code: string, type: string) => {
    const existingResult = await handleDb(
      async () => {
        const r = await db.prepare('SELECT id FROM ledger_accounts WHERE tenant_id = ? AND code = ?').bind(tenant.id, code).first()
        return r as { id: string } | null
      },
      'DATABASE_ERROR',
      'Failed to ensure account exists'
    )
    if (existingResult) return (existingResult as { id: string }).id
    const id = crypto.randomUUID()
    await handleDb(
      async () => {
        await db.prepare('INSERT INTO ledger_accounts (id, tenant_id, code, account_type) VALUES (?, ?, ?, ?)').bind(id, tenant.id, code, type).run()
      },
      'DATABASE_ERROR',
      'Failed to create account'
    )
    return id
  }

  const customerAcctId = await ensureAcct(body.customer_account, 'asset')
  const platformAcctId = await ensureAcct('revenue:platform', 'revenue')
  const expertAcctId = await ensureAcct(body.expert_account || 'revenue:expert:pool', 'revenue')
  const devAcctId = await ensureAcct(body.developer_account || 'revenue:developer:pool', 'revenue')
  const aiAcctId = await ensureAcct('expense:ai_compute', 'expense')
  const treasuryAcctId = await ensureAcct('treasury:community', 'equity')
  const rewardAcctId = await ensureAcct(body.customer_account + ':rewards', 'asset')

  // Check customer balance
  const bal = await handleDb(
    async () => {
      const r = await db.prepare('SELECT balance FROM ledger_accounts WHERE id = ?').bind(customerAcctId).first()
      return r as { balance: number } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch customer balance'
  )
  if ((bal?.balance || 0) < body.total_credits) {
    return c.json(createError('INSUFFICIENT_CREDITS', 'Insufficient credits', [{ balance: (bal as { balance: number })?.balance ?? 0 }]), 402)
  }

  // Calculate amounts
  const amounts = {
    platform: Math.floor(body.total_credits * (split.platform || 0.20)),
    expert: Math.floor(body.total_credits * (split.expert || 0.30)),
    ai_compute: Math.floor(body.total_credits * (split.ai_compute || 0.15)),
    developer: Math.floor(body.total_credits * (split.developer || 0.15)),
    community_fund: Math.floor(body.total_credits * (split.community_fund || 0.10)),
    customer_reward: Math.floor(body.total_credits * (split.customer_reward || 0.10)),
  }
  // Remainder goes to platform (rounding)
  const distributed = Object.values(amounts).reduce((a, b) => a + b, 0)
  amounts.platform += (body.total_credits - distributed)

  // Create journal entry with N transaction lines
  const jeId = crypto.randomUUID()
  const batch = [
    db.prepare('INSERT INTO journal_entries (id, tenant_id, description, entry_type, metadata) VALUES (?, ?, ?, ?, ?)')
      .bind(jeId, tenant.id, body.description, 'revenue_share', JSON.stringify({ split: amounts, total: body.total_credits })),
    // Debit customer
    db.prepare('INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction) VALUES (?, ?, ?, ?, ?)')
      .bind(crypto.randomUUID(), jeId, customerAcctId, body.total_credits, -1),
    db.prepare('UPDATE ledger_accounts SET balance = balance - ? WHERE id = ?').bind(body.total_credits, customerAcctId),
    // Credit each recipient
    ...[
      [platformAcctId, amounts.platform],
      [expertAcctId, amounts.expert],
      [aiAcctId, amounts.ai_compute],
      [devAcctId, amounts.developer],
      [treasuryAcctId, amounts.community_fund],
      [rewardAcctId, amounts.customer_reward],
    ].flatMap(([acctId, amount]) => [
      db.prepare('INSERT INTO transaction_lines (id, journal_entry_id, account_id, amount, direction) VALUES (?, ?, ?, ?, ?)')
        .bind(crypto.randomUUID(), jeId, acctId, amount as number, 1),
      db.prepare('UPDATE ledger_accounts SET balance = balance + ? WHERE id = ?').bind(amount as number, acctId),
    ]),
  ]

  await handleDb(
    () => db.batch(batch),
    'DATABASE_ERROR',
    'Failed to execute revenue split'
  )

  // Update treasury table too
  await handleDb(
    () => db.prepare("UPDATE treasury SET balance = balance + ?, total_in = total_in + ?, last_updated = datetime('now') WHERE tenant_id = ?")
      .bind(amounts.community_fund, amounts.community_fund, tenant.id).run(),
    'DATABASE_ERROR',
    'Failed to update treasury'
  )

  return c.json({
    journal_entry_id: jeId,
    total: body.total_credits,
    split: amounts,
    message: 'Revenue split executed — 6-way distribution via double-entry ledger'
  }, 201)
}))

// GET /split-config — Current split percentages
revenueRoutes.get('/split-config', (c) => {
  return c.json({ split: DEFAULT_SPLIT, note: 'Tam giác ngược: community_fund + customer_reward = 20% goes back to community' })
})

// GET /revenue-summary — Revenue by account
revenueRoutes.get('/summary', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  const rowsResult = await handleDb(
    async () => {
      const r = await c.env.DB.prepare(
        "SELECT code, balance FROM ledger_accounts WHERE tenant_id = ? AND code LIKE 'revenue:%' ORDER BY balance DESC"
      ).bind(tenant.id).all()
      return r as { results?: Array<{ code: string; balance: number }> }
    },
    'DATABASE_ERROR',
    'Failed to fetch revenue accounts'
  )
  return c.json({ accounts: (rowsResult as { results?: Array<{ code: string; balance: number }> }).results ?? [] })
}))

export { revenueRoutes }
