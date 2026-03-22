/**
 * Tenant Data Encryption Keys Routes — /v1/tenant-data-encryption-keys
 * GET  /keys          list encryption keys for tenant
 * POST /keys          create encryption key
 * GET  /usage         list key usage logs for tenant
 * GET  /admin/overview admin overview (X-Admin-Key required)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import { tenantDataEncryptionKeysService } from '../services/tenant-data-encryption-keys';

type Bindings = {
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

const app = new Hono<{ Bindings: Bindings }>();

// ── Tenant routes (auth required) ─────────────────────────────────────────────

app.use('/keys', auth());
app.use('/keys/*', auth());
app.use('/usage', auth());

// GET /keys — list encryption keys
app.get('/keys', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const keys = await tenantDataEncryptionKeysService.listKeys(c.env.DB, tenantId);
    return json({ keys, total: keys.length });
  } catch {
    return json({ error: 'Failed to list keys', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// POST /keys — create encryption key
app.post('/keys', async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as {
    key_name?: string;
    algorithm?: string;
    expires_at?: string;
  };
  if (!body.key_name?.trim()) {
    return json({ error: 'key_name is required', code: 'VALIDATION_ERROR' }, { status: 400 });
  }
  try {
    const key = await tenantDataEncryptionKeysService.createKey(c.env.DB, tenantId, {
      key_name: body.key_name.trim(),
      algorithm: body.algorithm,
      expires_at: body.expires_at,
    });
    return json({ key }, { status: 201 });
  } catch (err: any) {
    if (err?.message?.includes('UNIQUE')) {
      return json({ error: 'key_name already exists', code: 'CONFLICT' }, { status: 409 });
    }
    return json({ error: 'Failed to create key', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// GET /usage — list key usage logs
app.get('/usage', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const logs = await tenantDataEncryptionKeysService.getUsageLogs(c.env.DB, tenantId);
    return json({ logs, total: logs.length });
  } catch {
    return json({ error: 'Failed to list usage logs', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// ── Admin route (X-Admin-Key required) ────────────────────────────────────────

// GET /admin/overview
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  }
  try {
    const overview = await tenantDataEncryptionKeysService.getAdminOverview(c.env.DB);
    return json({ overview });
  } catch {
    return json({ error: 'Failed to fetch overview', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

export { app as tenantDataEncryptionKeys };
