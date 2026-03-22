/**
 * Tenant API Deprecation routes — view and manage API deprecation notices
 *
 * Tenant (auth required):
 *   GET  /notices              — list deprecation notices visible to tenant
 *   POST /notices              — create a deprecation notice for tenant
 *   GET  /acknowledgements     — list tenant's acknowledgements (optional ?notice_id=)
 *
 * Admin (X-Admin-Key required):
 *   GET  /admin/overview       — aggregate stats across all tenants
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantApiDeprecationService } from '../services/tenant-api-deprecation-service';

export const tenantApiDeprecation = new Hono<{ Bindings: Env }>();

// ---------------------------------------------------------------------------
// Tenant routes
// ---------------------------------------------------------------------------

tenantApiDeprecation.get('/notices', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const notices = await tenantApiDeprecationService.listNotices(c.env.DB, tenantId);
    return json({ notices });
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});

tenantApiDeprecation.post('/notices', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const body = await c.req.json<{
      endpoint: string;
      deprecation_date?: string;
      sunset_date?: string;
      replacement_endpoint?: string;
      message?: string;
    }>();
    if (!body.endpoint?.trim()) {
      return json({ error: 'endpoint is required' }, { status: 400 });
    }
    const notice = await tenantApiDeprecationService.createNotice(c.env.DB, tenantId, body);
    return json({ notice }, { status: 201 });
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});

tenantApiDeprecation.get('/acknowledgements', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const noticeId = c.req.query('notice_id');
  try {
    const acknowledgements = await tenantApiDeprecationService.getAcknowledgements(c.env.DB, tenantId, noticeId);
    return json({ acknowledgements });
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});

// ---------------------------------------------------------------------------
// Admin route
// ---------------------------------------------------------------------------

tenantApiDeprecation.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden' }, { status: 403 });
  }
  try {
    const overview = await tenantApiDeprecationService.getAdminOverview(c.env.DB);
    return json({ overview });
  } catch (err) {
    return json({ error: (err as Error).message }, { status: 500 });
  }
});
