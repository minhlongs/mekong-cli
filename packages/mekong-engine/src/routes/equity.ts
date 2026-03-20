import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { createError, handleAsync, handleDb } from '../types/error'
import { payloadSizeLimit } from '../raas/payload-limiter'

type Variables = { tenant: Tenant }

// Zod schemas for equity operations
const createEntitySchema = z.object({
  name: z.string().min(1, 'name is required').max(200, 'name must be ≤200 chars'),
  entity_type: z.string().optional(),
  total_shares: z.number().int().positive('total_shares must be positive').optional(),
  jurisdiction: z.string().max(100, 'jurisdiction must be ≤100 chars').optional(),
})

const createGrantSchema = z.object({
  entity_id: z.string().uuid('entity_id must be a valid UUID'),
  stakeholder_id: z.string().uuid('stakeholder_id must be a valid UUID'),
  share_class_id: z.string().uuid('share_class_id must be a valid UUID'),
  shares: z.number().int().positive('shares must be positive'),
  price_per_share: z.number().nonnegative('price_per_share must be non-negative').optional(),
  grant_type: z.string().optional(),
  vesting_months: z.number().int().nonnegative('vesting_months must be non-negative').optional(),
  cliff_months: z.number().int().nonnegative('cliff_months must be non-negative').optional(),
})

const createSafeSchema = z.object({
  entity_id: z.string().uuid('entity_id must be a valid UUID'),
  investor_stakeholder_id: z.string().uuid('investor_stakeholder_id must be a valid UUID'),
  principal_amount: z.number().positive('principal_amount must be positive'),
  valuation_cap: z.number().positive('valuation_cap must be positive').optional(),
  discount_rate: z.number().min(0).max(1, 'discount_rate must be between 0 and 1').optional(),
})

const convertSafeSchema = z.object({
  price_per_share: z.number().positive('price_per_share must be positive'),
  share_class_id: z.string().uuid('share_class_id must be a valid UUID'),
})

type CreateEntityBody = z.infer<typeof createEntitySchema>
type CreateGrantBody = z.infer<typeof createGrantSchema>
type CreateSafeBody = z.infer<typeof createSafeSchema>
type ConvertSafeBody = z.infer<typeof convertSafeSchema>

const equityRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
equityRoutes.use('*', authMiddleware)

// ─── ENTITIES (portfolio companies) ───

equityRoutes.post('/entities', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')

  let body: CreateEntityBody
  try {
    body = createEntitySchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    console.error('Failed to parse createEntity request:', { error, tenant_id: tenant.id })
    throw error
  }

  const id = crypto.randomUUID()
  await handleDb(
    async () => {
      await c.env.DB.prepare(
        'INSERT INTO equity_entities (id, tenant_id, name, entity_type, total_authorized_shares, jurisdiction) VALUES (?, ?, ?, ?, ?, ?)'
      ).bind(id, tenant.id, body.name, body.entity_type || 'portfolio_company',
        body.total_shares || 10000000, body.jurisdiction || 'VN').run()
    },
    'DATABASE_ERROR',
    'Failed to create equity entity'
  )

  // Auto-create Common share class
  const classId = crypto.randomUUID()
  await handleDb(
    async () => {
      await c.env.DB.prepare(
        'INSERT INTO share_classes (id, entity_id, name, class_type) VALUES (?, ?, ?, ?)'
      ).bind(classId, id, 'Common', 'common').run()
    },
    'DATABASE_ERROR',
    'Failed to create Common share class'
  )

  return c.json({ id, share_class_id: classId }, 201)
}))

equityRoutes.get('/entities', handleAsync(async (c) => {
  const tenant = c.get('tenant')
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 200)

  const rowsResult = await handleDb(
    async () => {
      const r = await c.env.DB.prepare('SELECT * FROM equity_entities WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?').bind(tenant.id, limit).all()
      return r as { results?: any[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch entities'
  )
  return c.json({ entities: rowsResult.results, count: rowsResult.results?.length || 0 })
}))

// ─── GRANTS (issue equity) ───

equityRoutes.post('/grants', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant')

  let body: CreateGrantBody
  try {
    body = createGrantSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    console.error('Failed to parse createGrant request:', { error, tenant_id: tenant.id })
    throw error
  }

  const id = crypto.randomUUID()
  await handleDb(
    async () => {
      await c.env.DB.prepare(
        `INSERT INTO equity_grants (id, entity_id, stakeholder_id, share_class_id, grant_type, shares, price_per_share, vesting_months, cliff_months, vesting_start_date)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`
      ).bind(id, body.entity_id, body.stakeholder_id, body.share_class_id,
        body.grant_type || 'grant', body.shares, body.price_per_share || 0,
        body.vesting_months || 0, body.cliff_months || 0).run()
    },
    'DATABASE_ERROR',
    'Failed to create equity grant'
  )

  return c.json({ id, shares: body.shares, vesting_months: body.vesting_months || 0 }, 201)
}))

// ─── CAP TABLE (computed view) ───

equityRoutes.get('/cap-table/:entityId', handleAsync(async (c) => {
  const entityId = c.req.param('entityId')
  const tenant = c.get('tenant')

  // Fix IDOR: Add tenant_id to entity lookup
  const entity = await handleDb(
    async () => {
      const r = await c.env.DB.prepare('SELECT * FROM equity_entities WHERE id = ? AND tenant_id = ?').bind(entityId, tenant.id).first()
      return r as Record<string, any> | null
    },
    'DATABASE_ERROR',
    'Failed to fetch entity'
  )
  if (!entity) return c.json(createError('NOT_FOUND', 'Entity not found'), 404)

  // Aggregate grants per stakeholder
  const grants = await handleDb(
    async () => {
      const r = await c.env.DB.prepare(`
      SELECT g.stakeholder_id, s.display_name, s.role, sc.name as share_class,
             SUM(CASE WHEN g.grant_type IN ('grant','exercise','conversion') THEN g.shares ELSE 0 END) as total_granted,
             SUM(CASE WHEN g.grant_type IN ('cancellation') THEN g.shares ELSE 0 END) as total_cancelled
      FROM equity_grants g
      JOIN stakeholders s ON s.id = g.stakeholder_id
      JOIN share_classes sc ON sc.id = g.share_class_id
      WHERE g.entity_id = ?
      GROUP BY g.stakeholder_id, sc.name
      ORDER BY total_granted DESC
    `).bind(entityId).all()
      return r as { results?: any[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch cap table grants'
  )

  // Calculate vested shares per grant
  const now = new Date()
  const detailedGrantsResult = await handleDb(
    async () => {
      const r = await c.env.DB.prepare(
        'SELECT * FROM equity_grants WHERE entity_id = ? ORDER BY effective_date'
      ).bind(entityId).all()
      return r as { results?: any[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch grant details'
  )

  const vestingDetails = (detailedGrantsResult.results || []).map((g: any) => {
    if (!g.vesting_months || g.vesting_months === 0) return { ...g, vested_shares: g.shares, vested_pct: 100 }
    const start = new Date(g.vesting_start_date || g.effective_date)
    const monthsElapsed = Math.max(0, (now.getTime() - start.getTime()) / (30.44 * 24 * 60 * 60 * 1000))
    if (monthsElapsed < (g.cliff_months || 0)) return { ...g, vested_shares: 0, vested_pct: 0 }
    const vestedPct = Math.min(100, (monthsElapsed / g.vesting_months) * 100)
    return { ...g, vested_shares: Math.floor(g.shares * vestedPct / 100), vested_pct: Math.round(vestedPct) }
  })

  // Total outstanding
  const grantsResult = await handleDb(
    async () => {
      const r = await c.env.DB.prepare(`
      SELECT g.stakeholder_id, s.display_name, s.role, sc.name as share_class,
             SUM(CASE WHEN g.grant_type IN ('grant','exercise','conversion') THEN g.shares ELSE 0 END) as total_granted,
             SUM(CASE WHEN g.grant_type IN ('cancellation') THEN g.shares ELSE 0 END) as total_cancelled
      FROM equity_grants g
      JOIN stakeholders s ON s.id = g.stakeholder_id
      JOIN share_classes sc ON sc.id = g.share_class_id
      WHERE g.entity_id = ?
      GROUP BY g.stakeholder_id, sc.name
      ORDER BY total_granted DESC
    `).bind(entityId).all()
      return r as { results?: any[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch cap table grants'
  )

  const totalOutstanding = (grantsResult.results || []).reduce((sum: number, g: any) =>
    sum + (g.total_granted - g.total_cancelled), 0)

  // SAFE notes
  const safesResult = await handleDb(
    async () => {
      const r = await c.env.DB.prepare(
        'SELECT sn.*, s.display_name FROM safe_notes sn JOIN stakeholders s ON s.id = sn.investor_stakeholder_id WHERE sn.entity_id = ?'
      ).bind(entityId).all()
      return r as { results?: any[] }
    },
    'DATABASE_ERROR',
    'Failed to fetch SAFE notes'
  )

  return c.json({
    entity: { name: entity.name, total_authorized: entity.total_authorized_shares },
    total_outstanding: totalOutstanding,
    dilution_pct: ((totalOutstanding / entity.total_authorized_shares) * 100).toFixed(2),
    holders: grantsResult.results,
    vesting_schedule: vestingDetails,
    safe_notes: safesResult.results,
  })
}))

// ─── SAFE NOTES ───

equityRoutes.post('/safe', payloadSizeLimit(), handleAsync(async (c) => {
  let body: CreateSafeBody
  try {
    body = createSafeSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    console.error('Failed to parse createSafe request:', { error, tenant_id: tenant.id })
    throw error
  }

  const id = crypto.randomUUID()
  await handleDb(
    async () => {
      await c.env.DB.prepare(
        'INSERT INTO safe_notes (id, entity_id, investor_stakeholder_id, principal_amount, valuation_cap, discount_rate) VALUES (?, ?, ?, ?, ?, ?)'
      ).bind(id, body.entity_id, body.investor_stakeholder_id, body.principal_amount,
        body.valuation_cap || null, body.discount_rate || 0).run()
    },
    'DATABASE_ERROR',
    'Failed to create SAFE note'
  )

  return c.json({ id, status: 'outstanding' }, 201)
}))

// Convert SAFE to equity
equityRoutes.post('/safe/:id/convert', payloadSizeLimit(), handleAsync(async (c) => {
  const safeId = c.req.param('id')

  let body: ConvertSafeBody
  try {
    body = convertSafeSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) {
      return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    }
    console.error('Failed to parse convertSafe request:', { error, tenant_id: tenant.id, safeId })
    throw error
  }

  const safe = await handleDb(
    async () => {
      const r = await c.env.DB.prepare('SELECT * FROM safe_notes WHERE id = ? AND status = ?').bind(safeId, 'outstanding').first()
      return r as { discount_rate: number; principal_amount: number; valuation_cap?: number; entity_id: string; investor_stakeholder_id: string } | null
    },
    'DATABASE_ERROR',
    'Failed to fetch SAFE note'
  )
  if (!safe) return c.json(createError('NOT_FOUND', 'SAFE not found or already converted'), 404)

  // Calculate shares: principal / (price * (1 - discount))
  const effectivePrice = body.price_per_share * (1 - (safe.discount_rate || 0))
  let shares = Math.floor(safe.principal_amount / effectivePrice)

  // Apply valuation cap if lower
  if (safe.valuation_cap) {
    const entityResult = await handleDb(
      async () => {
        const r = await c.env.DB.prepare('SELECT total_authorized_shares FROM equity_entities WHERE id = ? AND tenant_id = ?')
          .bind(safe.entity_id, tenant.id).first()
        return r as { total_authorized_shares: number } | null
      },
      'DATABASE_ERROR',
      'Failed to fetch entity for valuation cap calculation'
    )
    const capShares = Math.floor(safe.principal_amount / (safe.valuation_cap / (entityResult?.total_authorized_shares || 10000000)))
    shares = Math.max(shares, capShares) // Investor gets the better deal
  }

  // Create equity grant + update SAFE status
  const grantId = crypto.randomUUID()
  const batch = [
    c.env.DB.prepare(
      `INSERT INTO equity_grants (id, entity_id, stakeholder_id, share_class_id, grant_type, shares, price_per_share)
       VALUES (?, ?, ?, ?, 'conversion', ?, ?)`
    ).bind(grantId, safe.entity_id, safe.investor_stakeholder_id, body.share_class_id, shares, effectivePrice),
    c.env.DB.prepare(
      "UPDATE safe_notes SET status = 'converted', conversion_date = datetime('now'), converted_shares = ? WHERE id = ?"
    ).bind(shares, safeId),
  ]
  await handleDb(
    async () => {
      await c.env.DB.batch(batch)
    },
    'DATABASE_ERROR',
    'Failed to execute SAFE conversion'
  )

  return c.json({ grant_id: grantId, shares_converted: shares, effective_price: effectivePrice.toFixed(4) })
}))

export { equityRoutes }
