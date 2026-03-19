import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'

type Variables = { tenant: Tenant }
const equityRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
equityRoutes.use('*', authMiddleware)

// ─── ENTITIES (portfolio companies) ───

equityRoutes.post('/entities', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const body = await c.req.json<{
    name: string; entity_type?: string; total_shares?: number; jurisdiction?: string
  }>()
  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    'INSERT INTO equity_entities (id, tenant_id, name, entity_type, total_authorized_shares, jurisdiction) VALUES (?, ?, ?, ?, ?, ?)'
  ).bind(id, tenant.id, body.name, body.entity_type || 'portfolio_company',
    body.total_shares || 10000000, body.jurisdiction || 'VN').run()

  // Auto-create Common share class
  const classId = crypto.randomUUID()
  await c.env.DB.prepare(
    'INSERT INTO share_classes (id, entity_id, name, class_type) VALUES (?, ?, ?, ?)'
  ).bind(classId, id, 'Common', 'common').run()

  return c.json({ id, share_class_id: classId }, 201)
})

equityRoutes.get('/entities', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const rows = await c.env.DB.prepare('SELECT * FROM equity_entities WHERE tenant_id = ?').bind(tenant.id).all()
  return c.json({ entities: rows.results })
})

// ─── GRANTS (issue equity) ───

equityRoutes.post('/grants', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const body = await c.req.json<{
    entity_id: string; stakeholder_id: string; share_class_id: string;
    shares: number; price_per_share?: number; grant_type?: string;
    vesting_months?: number; cliff_months?: number
  }>()

  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    `INSERT INTO equity_grants (id, entity_id, stakeholder_id, share_class_id, grant_type, shares, price_per_share, vesting_months, cliff_months, vesting_start_date)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))`
  ).bind(id, body.entity_id, body.stakeholder_id, body.share_class_id,
    body.grant_type || 'grant', body.shares, body.price_per_share || 0,
    body.vesting_months || 0, body.cliff_months || 0).run()

  return c.json({ id, shares: body.shares, vesting_months: body.vesting_months || 0 }, 201)
})

// ─── CAP TABLE (computed view) ───

equityRoutes.get('/cap-table/:entityId', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const entityId = c.req.param('entityId')

  const entity = await c.env.DB.prepare('SELECT * FROM equity_entities WHERE id = ?').bind(entityId).first()
  if (!entity) return c.json({ error: 'Entity not found' }, 404)

  // Aggregate grants per stakeholder
  const grants = await c.env.DB.prepare(`
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

  // Calculate vested shares per grant
  const now = new Date()
  const detailedGrants = await c.env.DB.prepare(
    'SELECT * FROM equity_grants WHERE entity_id = ? ORDER BY effective_date'
  ).bind(entityId).all()

  const vestingDetails = (detailedGrants.results || []).map((g: any) => {
    if (!g.vesting_months || g.vesting_months === 0) return { ...g, vested_shares: g.shares, vested_pct: 100 }
    const start = new Date(g.vesting_start_date || g.effective_date)
    const monthsElapsed = Math.max(0, (now.getTime() - start.getTime()) / (30.44 * 24 * 60 * 60 * 1000))
    if (monthsElapsed < (g.cliff_months || 0)) return { ...g, vested_shares: 0, vested_pct: 0 }
    const vestedPct = Math.min(100, (monthsElapsed / g.vesting_months) * 100)
    return { ...g, vested_shares: Math.floor(g.shares * vestedPct / 100), vested_pct: Math.round(vestedPct) }
  })

  // Total outstanding
  const totalOutstanding = (grants.results || []).reduce((sum: number, g: any) =>
    sum + (g.total_granted - g.total_cancelled), 0)

  // SAFE notes
  const safes = await c.env.DB.prepare(
    'SELECT sn.*, s.display_name FROM safe_notes sn JOIN stakeholders s ON s.id = sn.investor_stakeholder_id WHERE sn.entity_id = ?'
  ).bind(entityId).all()

  return c.json({
    entity: { name: entity.name, total_authorized: entity.total_authorized_shares },
    total_outstanding: totalOutstanding,
    dilution_pct: ((totalOutstanding / (entity.total_authorized_shares as number)) * 100).toFixed(2),
    holders: grants.results,
    vesting_schedule: vestingDetails,
    safe_notes: safes.results,
  })
})

// ─── SAFE NOTES ───

equityRoutes.post('/safe', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const body = await c.req.json<{
    entity_id: string; investor_stakeholder_id: string;
    principal_amount: number; valuation_cap?: number; discount_rate?: number
  }>()

  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    'INSERT INTO safe_notes (id, entity_id, investor_stakeholder_id, principal_amount, valuation_cap, discount_rate) VALUES (?, ?, ?, ?, ?, ?)'
  ).bind(id, body.entity_id, body.investor_stakeholder_id, body.principal_amount,
    body.valuation_cap || null, body.discount_rate || 0).run()

  return c.json({ id, status: 'outstanding' }, 201)
})

// Convert SAFE to equity
equityRoutes.post('/safe/:id/convert', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const safeId = c.req.param('id')
  const body = await c.req.json<{ price_per_share: number; share_class_id: string }>()

  const safe = await c.env.DB.prepare('SELECT * FROM safe_notes WHERE id = ? AND status = ?').bind(safeId, 'outstanding').first()
  if (!safe) return c.json({ error: 'SAFE not found or already converted' }, 404)

  // Calculate shares: principal / (price * (1 - discount))
  const effectivePrice = body.price_per_share * (1 - ((safe.discount_rate as number) || 0))
  let shares = Math.floor((safe.principal_amount as number) / effectivePrice)

  // Apply valuation cap if lower
  if (safe.valuation_cap) {
    const entity = await c.env.DB.prepare('SELECT total_authorized_shares FROM equity_entities WHERE id = ?')
      .bind(safe.entity_id).first()
    const capShares = Math.floor((safe.principal_amount as number) / ((safe.valuation_cap as number) / (entity?.total_authorized_shares as number || 10000000)))
    shares = Math.max(shares, capShares) // Investor gets the better deal
  }

  // Create equity grant + update SAFE status
  const grantId = crypto.randomUUID()
  await c.env.DB.batch([
    c.env.DB.prepare(
      `INSERT INTO equity_grants (id, entity_id, stakeholder_id, share_class_id, grant_type, shares, price_per_share)
       VALUES (?, ?, ?, ?, 'conversion', ?, ?)`
    ).bind(grantId, safe.entity_id, safe.investor_stakeholder_id, body.share_class_id, shares, effectivePrice),
    c.env.DB.prepare(
      "UPDATE safe_notes SET status = 'converted', conversion_date = datetime('now'), converted_shares = ? WHERE id = ?"
    ).bind(shares, safeId),
  ])

  return c.json({ grant_id: grantId, shares_converted: shares, effective_price: effectivePrice.toFixed(4) })
})

export { equityRoutes }
