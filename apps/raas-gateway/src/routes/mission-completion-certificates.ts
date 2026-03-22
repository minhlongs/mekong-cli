/**
 * Mission Completion Certificates routes
 * GET  /certificates        — list tenant certificates (auth required)
 * POST /certificates        — issue new certificate (auth required)
 * GET  /templates           — list tenant certificate templates (auth required)
 * GET  /admin/overview      — platform-wide stats (X-Admin-Key required)
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { missionCompletionCertificatesService as svc } from '../services/mission-completion-certificates';

type Bindings = { Bindings: Env };

const app = new Hono<Bindings>();

/**
 * GET /certificates — list all certificates for authenticated tenant
 */
app.get('/certificates', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const result = await svc.listCertificates(c.env.DB, tenant.tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data, total: result.data?.length ?? 0 });
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Unexpected error';
    return c.json({ error }, 500);
  }
});

/**
 * POST /certificates — issue a new completion certificate
 * Required body: mission_id, issued_to
 * Optional body: expires_at
 */
app.post('/certificates', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json().catch(() => ({}));

    const mission_id = body.mission_id?.trim();
    const issued_to = body.issued_to?.trim();

    if (!mission_id) return c.json({ error: 'mission_id is required' }, 400);
    if (!issued_to) return c.json({ error: 'issued_to is required' }, 400);

    const result = await svc.createCertificate(c.env.DB, tenant.tenantId, {
      mission_id,
      issued_to,
      expires_at: body.expires_at ?? undefined,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Unexpected error';
    return c.json({ error }, 500);
  }
});

/**
 * GET /templates — list certificate templates for authenticated tenant
 */
app.get('/templates', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const result = await svc.getTemplates(c.env.DB, tenant.tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data, total: result.data?.length ?? 0 });
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Unexpected error';
    return c.json({ error }, 500);
  }
});

/**
 * GET /admin/overview — platform-wide certificate stats, protected by X-Admin-Key
 */
app.get('/admin/overview', async (c) => {
  try {
    const key = c.req.header('X-Admin-Key');
    const expected = c.env.ADMIN_API_KEY;
    if (!expected || key !== expected) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await svc.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err: unknown) {
    const error = err instanceof Error ? err.message : 'Unexpected error';
    return c.json({ error }, 500);
  }
});

export { app as missionCompletionCertificates };
