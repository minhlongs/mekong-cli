import { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import type { Variables } from '../raas/auth-middleware'
import { authMiddleware } from '../raas/auth-middleware'
import { handleAsync } from '../types/error'

const analyticsRoutes = new Hono<{ Bindings: Bindings; Variables: Variables }>()

/**
 * GET /v1/analytics/usage
 * Returns usage analytics for the current tenant
 */
analyticsRoutes.get('/usage', authMiddleware, handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const db = c.env.DB
  const tenant = c.get('tenant') as Tenant
  const tenantId = tenant.id

  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate()).toISOString()
  const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000).toISOString()
  const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000).toISOString()

  // Credits consumed by period
  const creditsToday = await db
    .prepare(`
      SELECT COALESCE(SUM(amount), 0) as total
      FROM credits
      WHERE tenant_id = ? AND amount < 0 AND created_at >= ?
    `)
    .bind(tenantId, today)
    .first<{ total: number }>()

  const creditsWeek = await db
    .prepare(`
      SELECT COALESCE(SUM(amount), 0) as total
      FROM credits
      WHERE tenant_id = ? AND amount < 0 AND created_at >= ?
    `)
    .bind(tenantId, weekAgo)
    .first<{ total: number }>()

  const creditsMonth = await db
    .prepare(`
      SELECT COALESCE(SUM(amount), 0) as total
      FROM credits
      WHERE tenant_id = ? AND amount < 0 AND created_at >= ?
    `)
    .bind(tenantId, monthAgo)
    .first<{ total: number }>()

  // Mission statistics
  const missionStats = await db
    .prepare(`
      SELECT
        COUNT(*) as total,
        SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
        SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed,
        SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running
      FROM missions
      WHERE tenant_id = ?
    `)
    .bind(tenantId)
    .first<{ total: number; completed: number; failed: number; running: number }>()

  // Success rate
  const totalCompletedOrFailed = (missionStats?.completed ?? 0) + (missionStats?.failed ?? 0)
  const successRate = totalCompletedOrFailed > 0
    ? ((missionStats?.completed ?? 0) / totalCompletedOrFailed) * 100
    : 0

  // Top endpoints by usage (from missions goal analysis - simplified)
  const topEndpoints = await db
    .prepare(`
      SELECT
        'missions' as endpoint,
        COUNT(*) as count
      FROM missions
      WHERE tenant_id = ?
      GROUP BY endpoint
      ORDER BY count DESC
      LIMIT 5
    `)
    .bind(tenantId)
    .all()

  // Average mission duration (for completed missions)
  const avgDuration = await db
    .prepare(`
      SELECT AVG(
        (julianday(completed_at) - julianday(created_at)) * 24 * 60 * 60 * 1000
      ) as avg_ms
      FROM missions
      WHERE tenant_id = ? AND status = 'completed' AND completed_at IS NOT NULL
    `)
    .bind(tenantId)
    .first<{ avg_ms: number }>()

  return c.json({
    tenant_id: tenantId,
    period: {
      daily: new Date(today),
      weekly: new Date(weekAgo),
      monthly: new Date(monthAgo),
    },
    credits: {
      consumed_today: Math.abs(creditsToday?.total ?? 0),
      consumed_week: Math.abs(creditsWeek?.total ?? 0),
      consumed_month: Math.abs(creditsMonth?.total ?? 0),
    },
    missions: {
      total: missionStats?.total ?? 0,
      completed: missionStats?.completed ?? 0,
      failed: missionStats?.failed ?? 0,
      running: missionStats?.running ?? 0,
      success_rate: Math.round(successRate * 100) / 100,
      avg_duration_ms: Math.round(avgDuration?.avg_ms ?? 0),
    },
    top_endpoints: topEndpoints.results || [],
  })
}))

/**
 * GET /v1/analytics/missions
 * Returns detailed mission analytics with pagination
 */
analyticsRoutes.get('/missions', authMiddleware, handleAsync(async (c) => {
  if (!c.env.DB) return c.json({ error: 'D1 not configured' }, 503)
  const db = c.env.DB
  const tenant = c.get('tenant') as Tenant

  const page = Math.max(1, parseInt(c.req.query('page') ?? '1', 10) || 1)
  const limit = Math.min(50, Math.max(1, parseInt(c.req.query('limit') ?? '20', 10) || 20))
  const offset = (page - 1) * limit
  const status = c.req.query('status')

  let query = `
    SELECT id, goal, status, credits_used, total_steps, completed_steps, created_at, completed_at
    FROM missions
    WHERE tenant_id = ?
  `
  const params: (string | number)[] = [tenant.id]

  if (status) {
    query += ' AND status = ?'
    params.push(status)
  }

  query += ' ORDER BY created_at DESC LIMIT ? OFFSET ?'
  params.push(limit, offset)

  const { results } = await db.prepare(query).bind(...params).all()

  // Get total count
  let countQuery = 'SELECT COUNT(*) as total FROM missions WHERE tenant_id = ?'
  const countParams: (string | number)[] = [tenant.id]
  if (status) {
    countQuery += ' AND status = ?'
    countParams.push(status)
  }
  const countResult = await db.prepare(countQuery).bind(...countParams).first<{ total: number }>()

  return c.json({
    tenant_id: tenant.id,
    missions: results,
    pagination: {
      page,
      limit,
      total: countResult?.total ?? 0,
      pages: Math.ceil((countResult?.total ?? 0) / limit),
    },
  })
}))

export { analyticsRoutes }
