/**
 * Tenant API Versioning routes — manage per-tenant API versions and endpoint mappings
 * Auth routes: tenant-scoped (JWT or API key)
 * Admin routes: X-Admin-Key protected
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  listVersions,
  createVersion,
  getMappings,
  getAdminOverview,
} from '../services/tenant-api-versioning-service';

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

// ─── Tenant: list versions ────────────────────────────────────────────────────

/** GET /versions — list all API versions for authenticated tenant */
app.get('/versions', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const versions = await listVersions(c.env.DB, tenant.tenantId);
    return json({ versions, total: versions.length });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

// ─── Tenant: create version ───────────────────────────────────────────────────

/** POST /versions — create a new API version for authenticated tenant */
app.post('/versions', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json<{
      version_label: string;
      base_url: string;
      is_default?: number;
      is_deprecated?: number;
      deprecation_date?: string;
    }>();
    if (!body.version_label) return json({ error: 'version_label is required' }, { status: 400 });
    if (!body.base_url) return json({ error: 'base_url is required' }, { status: 400 });
    const version = await createVersion(c.env.DB, tenant.tenantId, body);
    return json({ version }, { status: 201 });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

// ─── Tenant: list mappings ────────────────────────────────────────────────────

/** GET /mappings — list all endpoint mappings for authenticated tenant */
app.get('/mappings', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const mappings = await getMappings(c.env.DB, tenant.tenantId);
    return json({ mappings, total: mappings.length });
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

// ─── Admin: platform overview ─────────────────────────────────────────────────

/** GET /admin/overview — platform-wide counts of versions and mappings */
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (!c.env.ADMIN_API_KEY || key !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  }
  try {
    const overview = await getAdminOverview(c.env.DB);
    return json(overview);
  } catch (err: any) {
    return json({ error: err.message }, { status: 500 });
  }
});

export { app as tenantApiVersioning };
