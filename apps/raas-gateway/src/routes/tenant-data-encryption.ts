/**
 * Tenant Data Encryption Routes — /v1/encryption
 * GET  /keys          list keys
 * POST /keys          create key
 * POST /keys/:id/rotate  rotate key
 * POST /keys/:id/revoke  revoke key
 * GET  /audit         audit trail
 * POST /fields        register encrypted field
 * GET  /fields        list encrypted fields
 * GET  /stats         key statistics
 * GET  /admin/overview admin overview (X-Admin-Key)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  listKeys,
  createKey,
  rotateKey,
  revokeKey,
  listAudit,
  registerField,
  listFields,
  getKeyStats,
  getAdminOverview,
} from '../services/tenant-data-encryption-service';

type Env = {
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
};

const app = new Hono<Env>();

// --- Auth-protected routes ---

app.use('/keys', auth());
app.use('/keys/*', auth());
app.use('/audit', auth());
app.use('/fields', auth());
app.use('/stats', auth());

// GET /keys — list encryption keys
app.get('/keys', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const keys = await listKeys(c.env.DB, tenantId);
    return json({ keys, total: keys.length });
  } catch {
    return json({ error: 'Failed to list keys', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// POST /keys — create key
app.post('/keys', async (c) => {
  const { tenantId, userId } = getTenant(c) as any;
  const body = await c.req.json().catch(() => ({})) as {
    key_alias?: string; key_type?: string; expires_at?: string;
  };
  if (!body.key_alias?.trim()) {
    return json({ error: 'key_alias is required', code: 'VALIDATION_ERROR' }, { status: 400 });
  }
  try {
    const key = await createKey(c.env.DB, tenantId, {
      key_alias: body.key_alias.trim(),
      key_type: body.key_type,
      expires_at: body.expires_at,
    });
    return json({ key }, { status: 201 });
  } catch (err: any) {
    if (err?.message?.includes('UNIQUE')) {
      return json({ error: 'key_alias already exists', code: 'CONFLICT' }, { status: 409 });
    }
    return json({ error: 'Failed to create key', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// POST /keys/:id/rotate
app.post('/keys/:id/rotate', async (c) => {
  const { tenantId, userId } = getTenant(c) as any;
  const keyId = c.req.param('id');
  try {
    const key = await rotateKey(c.env.DB, tenantId, keyId, userId);
    if (!key) return json({ error: 'Key not found', code: 'NOT_FOUND' }, { status: 404 });
    return json({ key });
  } catch {
    return json({ error: 'Failed to rotate key', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// POST /keys/:id/revoke
app.post('/keys/:id/revoke', async (c) => {
  const { tenantId, userId } = getTenant(c) as any;
  const keyId = c.req.param('id');
  try {
    const ok = await revokeKey(c.env.DB, tenantId, keyId, userId);
    if (!ok) return json({ error: 'Key not found or already revoked', code: 'NOT_FOUND' }, { status: 404 });
    return json({ success: true });
  } catch {
    return json({ error: 'Failed to revoke key', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// GET /audit — audit trail
app.get('/audit', async (c) => {
  const { tenantId } = getTenant(c);
  const limit = Math.min(Number(c.req.query('limit') ?? 100), 1000);
  try {
    const entries = await listAudit(c.env.DB, tenantId, limit);
    return json({ entries, total: entries.length });
  } catch {
    return json({ error: 'Failed to fetch audit', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// POST /fields — register encrypted field
app.post('/fields', async (c) => {
  const { tenantId } = getTenant(c);
  const body = await c.req.json().catch(() => ({})) as {
    table_name?: string; field_name?: string; key_id?: string; encryption_type?: string;
  };
  if (!body.table_name?.trim() || !body.field_name?.trim() || !body.key_id?.trim()) {
    return json({ error: 'table_name, field_name, and key_id are required', code: 'VALIDATION_ERROR' }, { status: 400 });
  }
  try {
    const field = await registerField(c.env.DB, tenantId, {
      table_name: body.table_name.trim(),
      field_name: body.field_name.trim(),
      key_id: body.key_id.trim(),
      encryption_type: body.encryption_type,
    });
    return json({ field }, { status: 201 });
  } catch {
    return json({ error: 'Failed to register field', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// GET /fields — list encrypted fields
app.get('/fields', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const fields = await listFields(c.env.DB, tenantId);
    return json({ fields, total: fields.length });
  } catch {
    return json({ error: 'Failed to list fields', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// GET /stats — key statistics
app.get('/stats', async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const stats = await getKeyStats(c.env.DB, tenantId);
    return json({ stats });
  } catch {
    return json({ error: 'Failed to fetch stats', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

// --- Admin route (X-Admin-Key) ---

// GET /admin/overview
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized', code: 'UNAUTHORIZED' }, { status: 401 });
  }
  try {
    const overview = await getAdminOverview(c.env.DB);
    return json({ overview });
  } catch {
    return json({ error: 'Failed to fetch overview', code: 'INTERNAL_ERROR' }, { status: 500 });
  }
});

export { app as tenantDataEncryption };
