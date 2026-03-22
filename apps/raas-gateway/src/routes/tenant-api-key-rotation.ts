/**
 * Tenant API Key Rotation routes — rotation schedule and history management
 *
 * Tenant (auth): GET /rotations, POST /rotations, GET /history
 * Admin (X-Admin-Key): GET /admin/overview
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantApiKeyRotationService } from '../services/tenant-api-key-rotation';

const app = new Hono<{
  Bindings: {
    DB: any;
    RATE_LIMIT_KV: any;
    SESSION_KV: any;
    AI: any;
    JWT_SECRET=REDACTED: string;
    POLAR_WEBHOOK_SECRET: string;
    TELEGRAM_BOT_TOKEN: string;
    ENVIRONMENT: string;
    LOG_LEVEL: string;
    ADMIN_API_KEY: string;
  };
}>();

const isAdmin = (c: { req: { header: (k: string) => string | undefined }; env: { ADMIN_API_KEY: string } }) =>
  Boolean(c.env.ADMIN_API_KEY && c.req.header('X-Admin-Key') === c.env.ADMIN_API_KEY);

// GET /rotations — list rotation schedules for the authenticated tenant
app.get('/rotations', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const result = await tenantApiKeyRotationService.listRotations(c.env.DB, tenant.tenantId);
    if (!result.success) return json({ error: result.error }, { status: 500 });
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'Unexpected error' }, { status: 500 });
  }
});

// POST /rotations — create a new rotation schedule
app.post('/rotations', auth(), async (c) => {
  const tenant = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON', code: 'BAD_REQUEST' }, { status: 400 });
  }

  if (!body.key_name || typeof body.key_name !== 'string') {
    return json({ error: 'key_name is required', code: 'BAD_REQUEST' }, { status: 400 });
  }

  try {
    const result = await tenantApiKeyRotationService.createRotation(c.env.DB, tenant.tenantId, {
      key_name: body.key_name,
      rotation_interval_days: typeof body.rotation_interval_days === 'number' ? body.rotation_interval_days : undefined,
      next_rotation_at: typeof body.next_rotation_at === 'string' ? body.next_rotation_at : undefined,
    });
    if (!result.success) return json({ error: result.error }, { status: 500 });
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'Unexpected error' }, { status: 500 });
  }
});

// GET /history — rotation history for the authenticated tenant
app.get('/history', auth(), async (c) => {
  const tenant = getTenant(c);
  try {
    const result = await tenantApiKeyRotationService.getHistory(c.env.DB, tenant.tenantId);
    if (!result.success) return json({ error: result.error }, { status: 500 });
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'Unexpected error' }, { status: 500 });
  }
});

// GET /admin/overview — platform-wide summary (admin only)
app.get('/admin/overview', async (c) => {
  if (!isAdmin(c)) return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  try {
    const result = await tenantApiKeyRotationService.getAdminOverview(c.env.DB);
    if (!result.success) return json({ error: result.error }, { status: 500 });
    return c.json({ success: true, data: result.data });
  } catch (err) {
    return json({ error: err instanceof Error ? err.message : 'Unexpected error' }, { status: 500 });
  }
});

export { app as tenantApiKeyRotation };
