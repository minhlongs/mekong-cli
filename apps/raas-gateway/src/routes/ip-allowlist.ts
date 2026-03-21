/**
 * IP Allowlist routes — tenant CRUD for IP rules + access log endpoints
 * Auth: JWT or API key via auth() middleware
 * Admin: X-Admin-Key header required for /admin/* routes
 *
 * IMPORTANT: /check, /logs, /blocked-count, /admin/* mounted BEFORE /:id to avoid shadowing
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import {
  addIpRule,
  removeIpRule,
  listIpRules,
  updateIpRule,
  isIpAllowed,
  logAccess,
  getAccessLogs,
  cleanExpiredRules,
  getBlockedCount,
} from '../services/ip-allowlist-service';

const app = new Hono<{ Bindings: Env }>();

app.use('/*', auth());

// ── Check if an IP is allowed for the authenticated tenant ───────────────────
app.post('/check', async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json<{ ip_address: string }>();
  if (!body.ip_address) return c.json({ success: false, error: 'ip_address required' }, 400);
  const allowed = await isIpAllowed(c.env.DB, tenantId, body.ip_address);
  const action = allowed ? 'allowed' : 'blocked';
  await logAccess(c.env.DB, tenantId, body.ip_address, action, c.req.path);
  return c.json({ success: true, data: { ip_address: body.ip_address, allowed, action } });
});

// ── Access logs (paginated) ──────────────────────────────────────────────────
app.get('/logs', async (c) => {
  const { tenantId } = getTenant(c);
  const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10), 200);
  const offset = parseInt(c.req.query('offset') ?? '0', 10);
  const { logs, total } = await getAccessLogs(c.env.DB, tenantId, limit, offset);
  return c.json({ success: true, data: { logs, total, limit, offset } });
});

// ── Blocked attempt count ────────────────────────────────────────────────────
app.get('/blocked-count', async (c) => {
  const { tenantId } = getTenant(c);
  const count = await getBlockedCount(c.env.DB, tenantId);
  return c.json({ success: true, data: { tenant_id: tenantId, blocked_count: count } });
});

// ── Admin: clean expired rules ───────────────────────────────────────────────
app.post('/admin/cleanup', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || adminKey !== c.env.ADMIN_API_KEY) {
    return c.json({ success: false, error: 'Forbidden' }, 403);
  }
  const deleted = await cleanExpiredRules(c.env.DB);
  return c.json({ success: true, data: { deleted_count: deleted } });
});

// ── List IP rules ────────────────────────────────────────────────────────────
app.get('/rules', async (c) => {
  const { tenantId } = getTenant(c);
  const rules = await listIpRules(c.env.DB, tenantId);
  return c.json({ success: true, data: rules });
});

// ── Add IP rule ──────────────────────────────────────────────────────────────
app.post('/rules', async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json<{ ip_address: string; label?: string; expires_at?: string }>();
  if (!body.ip_address) return c.json({ success: false, error: 'ip_address required' }, 400);
  try {
    const rule = await addIpRule(c.env.DB, tenantId, body.ip_address, body.label, body.expires_at);
    return c.json({ success: true, data: rule }, 201);
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    if (msg.includes('UNIQUE constraint')) {
      return c.json({ success: false, error: 'IP rule already exists for this tenant' }, 409);
    }
    throw err;
  }
});

// ── Update IP rule ───────────────────────────────────────────────────────────
app.put('/rules/:id', async (c) => {
  const { tenantId } = getTenant(c);
  const ruleId = c.req.param('id');
  const body = await c.req.json<{ label?: string; is_active?: boolean; expires_at?: string | null }>();
  const updated = await updateIpRule(c.env.DB, tenantId, ruleId, body);
  if (!updated) return c.json({ success: false, error: 'Rule not found or no changes' }, 404);
  return c.json({ success: true, data: updated });
});

// ── Delete IP rule ───────────────────────────────────────────────────────────
app.delete('/rules/:id', async (c) => {
  const { tenantId } = getTenant(c);
  const ruleId = c.req.param('id');
  const deleted = await removeIpRule(c.env.DB, tenantId, ruleId);
  if (!deleted) return c.json({ success: false, error: 'Rule not found' }, 404);
  return c.json({ success: true, data: { deleted: true } });
});

export { app as ipAllowlist };
