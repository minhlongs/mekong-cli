import { Hono } from 'hono'
import { z } from 'zod'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'
import { createError, handleAsync, handleDb } from '../types/error'
import { payloadSizeLimit } from '../raas/payload-limiter'
import { logger } from '../lib/monitoring'
import {
  type CreateEntityBody,
  type CreateGrantBody,
  type CreateSafeBody,
  type ConvertSafeBody,
  type EquityEntity,
  createEntitySchema,
  createGrantSchema,
  createSafeSchema,
  convertSafeSchema,
} from './equity-schemas'
import { registerCapTableRoute } from './equity-cap-table-handler'

type Variables = { tenant: Tenant }
const equityRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
equityRoutes.use('*', authMiddleware)

// ─── ENTITIES (portfolio companies) ───

equityRoutes.post('/entities', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  let body: CreateEntityBody
  try {
    body = createEntitySchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    logger.error('Failed to parse createEntity request', { error: error instanceof Error ? error.message : String(error), tenant_id: tenant.id })
    throw error
  }

  const id = crypto.randomUUID()
  await handleDb(
    async () => {
      await c.env.DB!.prepare(
        'INSERT INTO equity_entities (id, tenant_id, name, entity_type, total_authorized_shares, jurisdiction) VALUES (?, ?, ?, ?, ?, ?)'
      ).bind(id, tenant.id, body.name, body.entity_type || 'portfolio_company', body.total_shares || 10000000, body.jurisdiction || 'VN').run()
    },
    'DATABASE_ERROR',
    'Failed to create equity entity'
  )

  const classId = crypto.randomUUID()
  await handleDb(
    async () => {
      await c.env.DB!.prepare('INSERT INTO share_classes (id, entity_id, name, class_type) VALUES (?, ?, ?, ?)').bind(classId, id, 'Common', 'common').run()
    },
    'DATABASE_ERROR',
    'Failed to create Common share class'
  )

  return c.json({ id, share_class_id: classId }, 201)
}))

equityRoutes.get('/entities', handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  const limit = Math.min(Number(c.req.query('limit') ?? 50), 200)
  const rowsResult = await handleDb(
    async () => (await c.env.DB!.prepare('SELECT * FROM equity_entities WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ?').bind(tenant.id, limit).all()) as unknown as { results?: EquityEntity[] },
    'DATABASE_ERROR',
    'Failed to fetch entities'
  )
  return c.json({ entities: rowsResult.results, count: rowsResult.results?.length || 0 })
}))

// ─── GRANTS (issue equity) ───

equityRoutes.post('/grants', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  let body: CreateGrantBody
  try {
    body = createGrantSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    logger.error('Failed to parse createGrant request', { error: error instanceof Error ? error.message : String(error), tenant_id: tenant.id })
    throw error
  }

  const id = crypto.randomUUID()
  await handleDb(
    async () => {
      await c.env.DB!.prepare(
        `INSERT INTO equity_grants (id, entity_id, stakeholder_id, share_class_id, grant_type, shares, price_per_share, vesting_months, cliff_months, vesting_start_date)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`
      ).bind(id, body.entity_id, body.stakeholder_id, body.share_class_id, body.grant_type || 'grant', body.shares, body.price_per_share || 0, body.vesting_months || 0, body.cliff_months || 0).run()
    },
    'DATABASE_ERROR',
    'Failed to create equity grant'
  )

  return c.json({ id, shares: body.shares, vesting_months: body.vesting_months || 0 }, 201)
}))

// ─── CAP TABLE (computed view) ───

registerCapTableRoute(equityRoutes)

// ─── SAFE NOTES ───

equityRoutes.post('/safe', payloadSizeLimit(), handleAsync(async (c) => {
  const tenant = c.get('tenant') as Tenant
  let body: CreateSafeBody
  try {
    body = createSafeSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    logger.error('Failed to parse createSafe request', { error: error instanceof Error ? error.message : String(error), tenant_id: tenant.id })
    throw error
  }

  const id = crypto.randomUUID()
  await handleDb(
    async () => {
      await c.env.DB!.prepare(
        'INSERT INTO safe_notes (id, entity_id, investor_stakeholder_id, principal_amount, valuation_cap, discount_rate) VALUES (?, ?, ?, ?, ?, ?)'
      ).bind(id, body.entity_id, body.investor_stakeholder_id, body.principal_amount, body.valuation_cap || null, body.discount_rate || 0).run()
    },
    'DATABASE_ERROR',
    'Failed to create SAFE note'
  )

  return c.json({ id, status: 'outstanding' }, 201)
}))

equityRoutes.post('/safe/:id/convert', payloadSizeLimit(), handleAsync(async (c) => {
  const safeId = c.req.param('id')
  const tenant = c.get('tenant') as Tenant
  let body: ConvertSafeBody
  try {
    body = convertSafeSchema.parse(await c.req.json())
  } catch (error) {
    if (error instanceof z.ZodError) return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
    logger.error('Failed to parse convertSafe request', { error: error instanceof Error ? error.message : String(error), tenant_id: tenant.id, safeId })
    throw error
  }

  const safe = await handleDb(
    async () => (await c.env.DB!.prepare('SELECT * FROM safe_notes WHERE id = ? AND status = ?').bind(safeId, 'outstanding').first()) as {
      discount_rate: number; principal_amount: number; valuation_cap?: number; entity_id: string; investor_stakeholder_id: string
    } | null,
    'DATABASE_ERROR',
    'Failed to fetch SAFE note'
  )
  if (!safe) return c.json(createError('NOT_FOUND', 'SAFE not found or already converted'), 404)

  const effectivePrice = body.price_per_share * (1 - (safe.discount_rate || 0))
  let shares = Math.floor(safe.principal_amount / effectivePrice)

  if (safe.valuation_cap) {
    const entityResult = await handleDb(
      async () => (await c.env.DB!.prepare('SELECT total_authorized_shares FROM equity_entities WHERE id = ? AND tenant_id = ?').bind(safe.entity_id, tenant.id).first()) as { total_authorized_shares: number } | null,
      'DATABASE_ERROR',
      'Failed to fetch entity for valuation cap calculation'
    )
    const capShares = Math.floor(safe.principal_amount / (safe.valuation_cap / (entityResult?.total_authorized_shares || 10000000)))
    shares = Math.max(shares, capShares)
  }

  const grantId = crypto.randomUUID()
  await handleDb(
    async () => {
      await c.env.DB!.batch([
        c.env.DB!.prepare(
          `INSERT INTO equity_grants (id, entity_id, stakeholder_id, share_class_id, grant_type, shares, price_per_share) VALUES (?, ?, ?, ?, 'conversion', ?, ?)`
        ).bind(grantId, safe.entity_id, safe.investor_stakeholder_id, body.share_class_id, shares, effectivePrice),
        c.env.DB!.prepare("UPDATE safe_notes SET status = 'converted', conversion_date = datetime('now'), converted_shares = ? WHERE id = ?").bind(shares, safeId),
      ])
    },
    'DATABASE_ERROR',
    'Failed to execute SAFE conversion'
  )

  return c.json({ grant_id: grantId, shares_converted: shares, effective_price: effectivePrice.toFixed(4) })
}))

export { equityRoutes, createEntitySchema, createGrantSchema, createSafeSchema, convertSafeSchema }
