/**
 * Tenant SSO V2 Routes — SAML and OIDC identity provider management
 * Mount at: /v1/sso/v2
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  createSSOConfig,
  listSSOConfigs,
  getSSOConfig,
  updateSSOConfig,
  deleteSSOConfig,
  initiateSSOLogin,
  handleSSOCallback,
  getSSOSession,
  getSSOStats,
  getAdminSSOOverview,
} from '../services/tenant-sso-v2-service';

export const tenantSsoV2 = new Hono<{ Bindings: Env }>();

// ── Authenticated routes ──────────────────────────────────────────────────────

/** GET /configs — list SSO configurations for current tenant */
tenantSsoV2.get('/configs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const configs = await listSSOConfigs(c.env.DB, tenantId);
    return json({ success: true, data: configs });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** POST /configs — create a new SSO configuration */
tenantSsoV2.post('/configs', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();

    if (!body.provider_name) {
      return json({ error: 'provider_name is required' }, { status: 400 });
    }
    if (!['oidc', 'saml'].includes(body.provider_type ?? 'oidc')) {
      return json({ error: 'provider_type must be oidc or saml' }, { status: 400 });
    }

    const config = await createSSOConfig(c.env.DB, tenantId, body);
    return json({ success: true, data: config }, { status: 201 });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /configs/:configId — get a single SSO configuration */
tenantSsoV2.get('/configs/:configId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const configId = c.req.param('configId');
    const config = await getSSOConfig(c.env.DB, configId, tenantId);
    if (!config) return json({ error: 'SSO configuration not found' }, { status: 404 });
    return json({ success: true, data: config });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** PUT /configs/:configId — update an SSO configuration */
tenantSsoV2.put('/configs/:configId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const configId = c.req.param('configId');
    const body = await c.req.json();

    // Prevent overriding immutable fields
    delete body.id;
    delete body.tenant_id;
    delete body.created_at;

    const updated = await updateSSOConfig(c.env.DB, configId, tenantId, body);
    if (!updated) return json({ error: 'SSO configuration not found' }, { status: 404 });
    return json({ success: true, data: updated });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** DELETE /configs/:configId — soft-delete (deactivate) an SSO configuration */
tenantSsoV2.delete('/configs/:configId', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const configId = c.req.param('configId');
    const deleted = await deleteSSOConfig(c.env.DB, configId, tenantId);
    if (!deleted) return json({ error: 'SSO configuration not found' }, { status: 404 });
    return json({ success: true, message: 'SSO configuration deactivated' });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** GET /stats — SSO authentication statistics for current tenant */
tenantSsoV2.get('/stats', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const stats = await getSSOStats(c.env.DB, tenantId);
    return json({ success: true, data: stats });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

// ── Public routes (no auth — used during SSO flow) ────────────────────────────

/** POST /login/:configId — initiate SSO login, returns redirect URL */
tenantSsoV2.post('/login/:configId', async (c) => {
  try {
    const body = await c.req.json().catch(() => ({}));
    const configId = c.req.param('configId');

    // tenantId must be supplied in body for public endpoint (no JWT context)
    const tenantId: string = body.tenant_id;
    if (!tenantId) return json({ error: 'tenant_id is required' }, { status: 400 });

    const result = await initiateSSOLogin(c.env.DB, tenantId, configId, {
      ip: c.req.header('CF-Connecting-IP') ?? c.req.header('X-Forwarded-For'),
      userAgent: c.req.header('User-Agent'),
    });
    return json({ success: true, data: result }, { status: 201 });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});

/** POST /callback — handle SSO provider callback with identity claims */
tenantSsoV2.post('/callback', async (c) => {
  try {
    const body = await c.req.json();
    const { state, ...identityData } = body;

    if (!state) return json({ error: 'state is required' }, { status: 400 });

    const session = await handleSSOCallback(c.env.DB, state, identityData);
    return json({ success: true, data: session });
  } catch (e: any) {
    const status = e.message.includes('expired') || e.message.includes('Invalid') ? 400 : 500;
    return json({ error: e.message }, { status });
  }
});

// ── Admin route ───────────────────────────────────────────────────────────────

/** GET /admin/overview — platform-wide SSO stats (X-Admin-Key required) */
tenantSsoV2.get('/admin/overview', async (c) => {
  if (c.req.header('X-Admin-Key') !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Unauthorized' }, { status: 401 });
  }
  try {
    const overview = await getAdminSSOOverview(c.env.DB);
    return json({ success: true, data: overview });
  } catch (e: any) {
    return json({ error: e.message }, { status: 500 });
  }
});
