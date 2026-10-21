import type { Hono } from 'hono'
import type { Bindings } from '../index'
import type { Tenant } from '../types/raas'
import { createError, handleAsync, handleDb } from '../types/error'
import {
  type CapTableHolder,
  type EquityEntity,
  type EquityGrant,
  type SafeNote,
  computeVestingSchedule,
} from './equity-schemas'

type Variables = { tenant: Tenant }

export function registerCapTableRoute(
  app: Hono<{ Bindings: Bindings; Variables: Variables }>
): void {
  app.get('/cap-table/:entityId', handleAsync(async (c) => {
    const entityId = c.req.param('entityId')
    const tenant = c.get('tenant') as Tenant

    const entity = await handleDb(
      async () => {
        const r = await c.env.DB!.prepare(
          'SELECT * FROM equity_entities WHERE id = ? AND tenant_id = ?'
        ).bind(entityId, tenant.id).first()
        return r as EquityEntity | null
      },
      'DATABASE_ERROR',
      'Failed to fetch entity'
    )
    if (!entity) return c.json(createError('NOT_FOUND', 'Entity not found'), 404)

    await handleDb(
      async () => {
        const r = await c.env.DB!.prepare(`
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
        return r as unknown as { results?: CapTableHolder[] }
      },
      'DATABASE_ERROR',
      'Failed to fetch cap table grants'
    )

    const detailedGrantsResult = await handleDb(
      async () => {
        const r = await c.env.DB!.prepare(
          'SELECT * FROM equity_grants WHERE entity_id = ? ORDER BY effective_date'
        ).bind(entityId).all()
        return r as unknown as { results?: EquityGrant[] }
      },
      'DATABASE_ERROR',
      'Failed to fetch grant details'
    )

    const vestingDetails = computeVestingSchedule(detailedGrantsResult.results || [])

    const grantsResult = await handleDb(
      async () => {
        const r = await c.env.DB!.prepare(`
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
        return r as unknown as { results?: CapTableHolder[] }
      },
      'DATABASE_ERROR',
      'Failed to fetch cap table grants'
    )

    const totalOutstanding = (grantsResult.results || []).reduce(
      (sum: number, g: CapTableHolder) => sum + (g.total_granted - g.total_cancelled),
      0
    )

    const safesResult = await handleDb(
      async () => {
        const r = await c.env.DB!.prepare(
          'SELECT sn.*, s.display_name FROM safe_notes sn JOIN stakeholders s ON s.id = sn.investor_stakeholder_id WHERE sn.entity_id = ?'
        ).bind(entityId).all()
        return r as unknown as { results?: SafeNote[] }
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
}
