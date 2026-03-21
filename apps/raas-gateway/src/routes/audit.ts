/**
 * Audit log routes — list audit entries for authenticated tenant
 * Also exports logAudit helper for use by other routes
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';

export const audit = new Hono<{ Bindings: Env }>();
audit.use('*', auth());

/** GET /v1/audit — List audit entries for authenticated tenant (paginated) */
audit.get('/', async (c) => {
  const tenant = getTenant(c);

  const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10), 200);
  const offset = parseInt(c.req.query('offset') ?? '0', 10);

  const result = await c.env.DB.prepare(
    'SELECT id, action, details, ip, user_agent, created_at FROM audit_log WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?'
  ).bind(tenant.tenantId, limit, offset).all();

  const countRow = await c.env.DB.prepare(
    'SELECT COUNT(*) as total FROM audit_log WHERE tenant_id = ?'
  ).bind(tenant.tenantId).first<{ total: number }>();

  return json({
    entries: result.results,
    total: countRow?.total ?? 0,
    limit,
    offset,
  });
});

/**
 * Log an audit event — call from other routes after significant actions.
 * Fire-and-forget safe: errors are swallowed so they never break the caller.
 */
export async function logAudit(
  db: D1Database,
  tenantId: string,
  action: string,
  details?: string,
  ip?: string,
  userAgent?: string
): Promise<void> {
  try {
    const id = crypto.randomUUID();
    await db.prepare(
      'INSERT INTO audit_log (id, tenant_id, action, details, ip, user_agent) VALUES (?, ?, ?, ?, ?, ?)'
    ).bind(id, tenantId, action, details ?? null, ip ?? null, userAgent ?? null).run();
  } catch {
    // Non-critical — never propagate audit errors to callers
  }
}
