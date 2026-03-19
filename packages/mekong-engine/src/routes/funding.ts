import { Hono } from 'hono'
import type { D1Database } from '@cloudflare/workers-types'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { authMiddleware } from '../raas/auth-middleware'

type Variables = { tenant: Tenant }
const fundingRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()
fundingRoutes.use('*', authMiddleware)

// Inline table creation (proper migration can be added later)
async function ensureFundingTables(db: D1Database) {
  await db.exec(`
    CREATE TABLE IF NOT EXISTS funding_rounds (
      id TEXT PRIMARY KEY, tenant_id TEXT NOT NULL, title TEXT NOT NULL,
      matching_pool INTEGER NOT NULL DEFAULT 0,
      status TEXT DEFAULT 'active' CHECK (status IN ('active','calculating','completed')),
      starts_at TEXT, ends_at TEXT, created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS funding_projects (
      id TEXT PRIMARY KEY, round_id TEXT NOT NULL, tenant_id TEXT NOT NULL,
      name TEXT NOT NULL, description TEXT, author_id TEXT,
      total_contributions INTEGER DEFAULT 0, contributor_count INTEGER DEFAULT 0,
      matched_amount INTEGER DEFAULT 0,
      created_at TEXT DEFAULT (datetime('now'))
    );
    CREATE TABLE IF NOT EXISTS funding_contributions (
      id TEXT PRIMARY KEY, project_id TEXT NOT NULL, stakeholder_id TEXT NOT NULL,
      amount INTEGER NOT NULL, created_at TEXT DEFAULT (datetime('now')),
      UNIQUE(project_id, stakeholder_id)
    );
  `).catch(() => {})
}

// Create funding round
fundingRoutes.post('/rounds', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  await ensureFundingTables(c.env.DB)

  const body = await c.req.json<{ title: string; matching_pool: number; duration_days?: number }>()
  const now = new Date()
  const end = new Date(now.getTime() + (body.duration_days || 14) * 24 * 60 * 60 * 1000)

  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    'INSERT INTO funding_rounds (id, tenant_id, title, matching_pool, starts_at, ends_at) VALUES (?, ?, ?, ?, ?, ?)'
  ).bind(id, tenant.id, body.title, body.matching_pool, now.toISOString(), end.toISOString()).run()

  return c.json({ id, matching_pool: body.matching_pool, ends_at: end.toISOString() }, 201)
})

// Add project to round
fundingRoutes.post('/projects', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  const body = await c.req.json<{ round_id: string; name: string; description?: string; author_id?: string }>()

  const id = crypto.randomUUID()
  await c.env.DB.prepare(
    'INSERT INTO funding_projects (id, round_id, tenant_id, name, description, author_id) VALUES (?, ?, ?, ?, ?, ?)'
  ).bind(id, body.round_id, tenant.id, body.name, body.description || '', body.author_id || null).run()

  return c.json({ id }, 201)
})

// Contribute to project
fundingRoutes.post('/contribute', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const body = await c.req.json<{ project_id: string; stakeholder_id: string; amount: number }>()

  const id = crypto.randomUUID()
  try {
    await c.env.DB.prepare(
      'INSERT INTO funding_contributions (id, project_id, stakeholder_id, amount) VALUES (?, ?, ?, ?)'
    ).bind(id, body.project_id, body.stakeholder_id, body.amount).run()
  } catch (e: any) {
    if (e.message?.includes('UNIQUE')) return c.json({ error: 'Already contributed to this project' }, 409)
    throw e
  }

  // Update project totals
  await c.env.DB.prepare(
    'UPDATE funding_projects SET total_contributions = total_contributions + ?, contributor_count = contributor_count + 1 WHERE id = ?'
  ).bind(body.amount, body.project_id).run()

  return c.json({ id, amount: body.amount }, 201)
})

// Calculate QF matching: matched = (Σ√ci)² - Σci
fundingRoutes.post('/rounds/:id/calculate', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const roundId = c.req.param('id')
  const db = c.env.DB

  const round = await db.prepare('SELECT * FROM funding_rounds WHERE id = ?').bind(roundId).first()
  if (!round) return c.json({ error: 'Round not found' }, 404)

  const projects = await db.prepare('SELECT * FROM funding_projects WHERE round_id = ?').bind(roundId).all()

  const results: any[] = []
  let totalQFScore = 0

  for (const project of projects.results || []) {
    const contributions = await db.prepare(
      'SELECT amount FROM funding_contributions WHERE project_id = ?'
    ).bind(project.id).all()

    // QF formula: matched = (Σ√ci)² - Σci
    const sqrtSum = (contributions.results || []).reduce((sum: number, c: any) => sum + Math.sqrt(c.amount), 0)
    const directSum = (contributions.results || []).reduce((sum: number, c: any) => sum + c.amount, 0)
    const qfScore = Math.pow(sqrtSum, 2) - directSum

    results.push({ id: project.id, name: project.name, direct: directSum, qf_score: qfScore, contributors: contributions.results?.length || 0, matched_amount: 0, total: 0 })
    totalQFScore += Math.max(0, qfScore)
  }

  // Distribute matching pool proportionally to QF scores
  const matchingPool = round.matching_pool as number
  for (const r of results) {
    r.matched_amount = totalQFScore > 0 ? Math.floor((r.qf_score / totalQFScore) * matchingPool) : 0
    r.total = r.direct + r.matched_amount

    await db.prepare('UPDATE funding_projects SET matched_amount = ? WHERE id = ?').bind(r.matched_amount, r.id).run()
  }

  await db.prepare("UPDATE funding_rounds SET status = 'completed' WHERE id = ?").bind(roundId).run()

  return c.json({
    round_id: roundId,
    matching_pool: matchingPool,
    results: results.sort((a: any, b: any) => b.total - a.total),
    note: 'QF: 10 people × $1 beats 1 person × $10 — democratic funding'
  })
})

// List rounds
fundingRoutes.get('/rounds', async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const tenant = c.get('tenant')
  await ensureFundingTables(c.env.DB)
  const rows = await c.env.DB.prepare('SELECT * FROM funding_rounds WHERE tenant_id = ? ORDER BY created_at DESC').bind(tenant.id).all()
  return c.json({ rounds: rows.results })
})

export { fundingRoutes }
