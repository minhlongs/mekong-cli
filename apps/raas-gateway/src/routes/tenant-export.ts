/**
 * Tenant data export/import + GDPR delete
 */
import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';

export const tenantExport = new Hono<{ Bindings: Env }>();

function isAdmin(c: any): boolean {
  return !!(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

async function exportData(db: any, tenantId: string) {
  const [tenant, missions, credits, apiKeys, projects] = await Promise.all([
    db.prepare('SELECT * FROM tenants WHERE id = ?').bind(tenantId).first(),
    db.prepare('SELECT * FROM missions WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 1000').bind(tenantId).all(),
    db.prepare('SELECT * FROM credit_transactions WHERE tenant_id = ? ORDER BY created_at DESC LIMIT 1000').bind(tenantId).all(),
    db.prepare('SELECT id, name, scope, created_at FROM api_keys WHERE tenant_id = ?').bind(tenantId).all(),
    db.prepare('SELECT * FROM projects WHERE tenant_id = ?').bind(tenantId).all(),
  ]);
  return { tenant, missions: missions.results, credits: credits.results, apiKeys: apiKeys.results, projects: projects.results, exportedAt: new Date().toISOString(), version: '1.0' };
}

/** GET /v1/export - download own data */
tenantExport.get('/v1/export', auth(), async (c) => {
  const tenant = getTenant(c);
  const data = await exportData(c.env.DB, tenant.tenantId);
  return new Response(JSON.stringify(data, null, 2), {
    headers: { 'Content-Type': 'application/json', 'Content-Disposition': `attachment; filename="tenant-${tenant.tenantId}-export.json"` },
  });
});

/** DELETE /v1/data - GDPR delete request */
tenantExport.delete('/v1/data', auth(), async (c) => {
  const tenant = getTenant(c);
  await c.env.SESSION_KV.put(`gdpr:delete:${tenant.tenantId}`, JSON.stringify({ requested: new Date().toISOString(), grace_days: 30 }), { expirationTtl: 30 * 86400 });
  return c.json({ success: true, message: 'Data deletion scheduled. 30-day grace period.', cancel_before: new Date(Date.now() + 30 * 86400000).toISOString() });
});

/** GET /admin/tenants/:id/export - admin export */
tenantExport.get('/admin/tenants/:id/export', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Unauthorized' }, 401);
  const data = await exportData(c.env.DB, c.req.param('id'));
  return c.json({ success: true, data });
});

/** DELETE /admin/tenants/:id/data - immediate deletion */
tenantExport.delete('/admin/tenants/:id/data', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Unauthorized' }, 401);
  const id = c.req.param('id');
  const tables = ['missions', 'credit_transactions', 'api_keys', 'projects', 'team_members', 'webhooks'];
  const deleted: Record<string, number> = {};
  for (const t of tables) {
    const r = await c.env.DB.prepare(`DELETE FROM ${t} WHERE tenant_id = ?`).bind(id).run();
    deleted[t] = r.meta?.changes ?? 0;
  }
  await c.env.DB.prepare('DELETE FROM tenants WHERE id = ?').bind(id).run();
  deleted['tenants'] = 1;
  return c.json({ success: true, data: { deleted } });
});
