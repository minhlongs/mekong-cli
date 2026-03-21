/**
 * Admin tenant impersonation + isolation audit
 */
import { Hono } from 'hono';
import * as jose from 'jose';
import type { Env } from '../index';

export const tenantImpersonation = new Hono<{ Bindings: Env }>();

function isAdmin(c: any): boolean {
  return !!(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);
}

/** POST /admin/impersonate - create short-lived JWT for target tenant */
tenantImpersonation.post('/admin/impersonate', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Unauthorized' }, 401);
  const body = await c.req.json().catch(() => ({}));
  if (!body.tenant_id) return c.json({ error: 'tenant_id required' }, 400);

  const tenant = await c.env.DB.prepare('SELECT * FROM tenants WHERE id = ?').bind(body.tenant_id).first<any>();
  if (!tenant) return c.json({ error: 'Tenant not found' }, 404);

  const secret = new TextEncoder().encode(c.env.JWT_SECRET=REDACTED);
  const expiresAt = new Date(Date.now() + 15 * 60 * 1000);
  const token = await new jose.SignJWT({ sub: tenant.id, tier: tenant.plan || 'free', permissions: [], impersonated: true })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt().setIssuer('raas-gateway').setAudience('raas-api')
    .setExpirationTime('15m').sign(secret);

  await c.env.SESSION_KV.put(`impersonate:${tenant.id}:${Date.now()}`, JSON.stringify({ admin: true, tenant_id: tenant.id, created: new Date().toISOString() }), { expirationTtl: 900 });
  return c.json({ success: true, data: { token, expires_at: expiresAt.toISOString(), impersonated_tenant_id: tenant.id } });
});

/** GET /admin/impersonate/active - list active sessions */
tenantImpersonation.get('/admin/impersonate/active', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Unauthorized' }, 401);
  const keys = await c.env.SESSION_KV.list({ prefix: 'impersonate:' });
  const sessions = await Promise.all(keys.keys.map(async (k: any) => {
    const data = await c.env.SESSION_KV.get(k.name, 'json');
    return { key: k.name, ...data as any };
  }));
  return c.json({ success: true, data: sessions });
});

/** GET /admin/isolation/violations - list isolation violations */
tenantImpersonation.get('/admin/isolation/violations', async (c) => {
  if (!isAdmin(c)) return c.json({ error: 'Unauthorized' }, 401);
  const keys = await c.env.RATE_LIMIT_KV.list({ prefix: 'isolation:violation:' });
  const violations = await Promise.all(keys.keys.slice(0, 50).map(async (k: any) => {
    const data = await c.env.RATE_LIMIT_KV.get(k.name, 'json');
    return { key: k.name, ...data as any };
  }));
  return c.json({ success: true, data: violations });
});
