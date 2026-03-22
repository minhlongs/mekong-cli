/**
 * Tenant API Key Management routes
 * GET    /keys           — list keys (auth)
 * POST   /keys           — create key (auth)
 * GET    /keys/:id       — get key metadata (auth)
 * DELETE /keys/:id       — revoke key (auth)
 * POST   /keys/:id/rotate — rotate key (auth)
 * PUT    /keys/:id/scopes — update scopes (auth)
 * GET    /keys/:id/usage  — paginated usage logs (auth)
 * GET    /admin/overview  — admin overview (admin key)
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { tenantApiKeyService } from '../services/tenant-api-key-management-service';

const app = new Hono<{
  Bindings: {
    DB: any; RATE_LIMIT_KV: any; SESSION_KV: any; AI: any;
    JWT_SECRET=REDACTED: string; POLAR_WEBHOOK_SECRET: string;
    TELEGRAM_BOT_TOKEN: string; ENVIRONMENT: string;
    LOG_LEVEL: string; ADMIN_API_KEY: string;
  }
}>();

// --- admin middleware ---
const adminAuth = async (c: any, next: any) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return c.json({ error: 'Unauthorized' }, 401);
  }
  await next();
};

// --- tenant routes (require auth) ---

app.get('/keys', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const keys = await tenantApiKeyService.listKeys(c.env.DB, tenantId);
    return c.json({ keys, total: keys.length });
  } catch {
    return c.json({ error: 'Failed to list keys' }, 500);
  }
});

app.post('/keys', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({})) as {
      name?: string; scopes?: string[]; expires_at?: string;
    };
    if (!body.name?.trim()) {
      return c.json({ error: 'name is required', code: 'VALIDATION_ERROR' }, 400);
    }
    const result = await tenantApiKeyService.createKey(c.env.DB, tenantId, {
      name: body.name.trim(),
      scopes: body.scopes,
      expires_at: body.expires_at,
    });
    return c.json(result, 201);
  } catch {
    return c.json({ error: 'Failed to create key' }, 500);
  }
});

app.get('/keys/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const key = await tenantApiKeyService.getKey(c.env.DB, tenantId, c.req.param('id'));
    if (!key) return c.json({ error: 'Key not found', code: 'NOT_FOUND' }, 404);
    return c.json(key);
  } catch {
    return c.json({ error: 'Failed to get key' }, 500);
  }
});

app.delete('/keys/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const ok = await tenantApiKeyService.revokeKey(c.env.DB, tenantId, c.req.param('id'));
    if (!ok) return c.json({ error: 'Key not found or already revoked', code: 'NOT_FOUND' }, 404);
    return c.json({ success: true, message: 'API key revoked' });
  } catch {
    return c.json({ error: 'Failed to revoke key' }, 500);
  }
});

app.post('/keys/:id/rotate', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const result = await tenantApiKeyService.rotateKey(c.env.DB, tenantId, c.req.param('id'));
    if (!result) return c.json({ error: 'Key not found or already revoked', code: 'NOT_FOUND' }, 404);
    return c.json(result, 201);
  } catch {
    return c.json({ error: 'Failed to rotate key' }, 500);
  }
});

app.put('/keys/:id/scopes', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json().catch(() => ({})) as { scopes?: string[] };
    if (!Array.isArray(body.scopes) || body.scopes.length === 0) {
      return c.json({ error: 'scopes array is required', code: 'VALIDATION_ERROR' }, 400);
    }
    const ok = await tenantApiKeyService.updateScopes(c.env.DB, tenantId, c.req.param('id'), body.scopes);
    if (!ok) return c.json({ error: 'Key not found or revoked', code: 'NOT_FOUND' }, 404);
    return c.json({ success: true });
  } catch {
    return c.json({ error: 'Failed to update scopes' }, 500);
  }
});

app.get('/keys/:id/usage', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const limit = Math.min(Number(c.req.query('limit') ?? 50), 200);
    const offset = Number(c.req.query('offset') ?? 0);
    const result = await tenantApiKeyService.getUsageLogs(c.env.DB, tenantId, c.req.param('id'), limit, offset);
    if (!result) return c.json({ error: 'Key not found', code: 'NOT_FOUND' }, 404);
    return c.json(result);
  } catch {
    return c.json({ error: 'Failed to get usage logs' }, 500);
  }
});

// --- admin route ---

app.get('/admin/overview', adminAuth, async (c) => {
  try {
    const overview = await tenantApiKeyService.getAdminOverview(c.env.DB);
    return c.json(overview);
  } catch {
    return c.json({ error: 'Failed to get overview' }, 500);
  }
});

export { app as tenantApiKeyManagement };
