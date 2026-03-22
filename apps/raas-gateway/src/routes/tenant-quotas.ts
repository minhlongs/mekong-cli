/**
 * Tenant Quotas routes — quota lookup, usage, enforcement, and admin management
 * Mount at: /v1/quotas
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  getQuotas,
  getQuotaUsage,
  checkQuota,
  getQuotaHistory,
  getTierDefaults,
  updateQuotas,
  getAdminQuotaOverview,
  upgradeQuotasForTier,
} from '../services/tenant-quotas-service';

export const tenantQuotas = new Hono<{ Bindings: Env }>();

/**
 * GET /quotas — get current quota limits for the authenticated tenant
 */
tenantQuotas.get('/', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const quotas = await getQuotas(c.env.DB, tenantId);
    if (!quotas) return json({ error: 'Quota record not found' }, { status: 404 });
    return json({ quotas });
  } catch {
    return json({ error: 'Failed to fetch quotas' }, { status: 500 });
  }
});

/**
 * GET /quotas/usage — get current usage vs limits from latest snapshots
 */
tenantQuotas.get('/usage', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  try {
    const usage = await getQuotaUsage(c.env.DB, tenantId);
    return json({ usage });
  } catch {
    return json({ error: 'Failed to fetch quota usage' }, { status: 500 });
  }
});

/**
 * POST /quotas/check — check if a specific resource is within quota
 * Body: { resource_type: string, current_usage: number }
 */
tenantQuotas.post('/check', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { resource_type, current_usage } = body;
  if (!resource_type) return json({ error: 'resource_type is required' }, { status: 400 });

  const validTypes = ['projects', 'team_members', 'api_keys', 'missions_today', 'templates', 'webhooks', 'storage_mb'];
  if (!validTypes.includes(String(resource_type))) {
    return json({ error: `resource_type must be one of: ${validTypes.join(', ')}` }, { status: 400 });
  }

  try {
    const result = await checkQuota(
      c.env.DB, tenantId, String(resource_type), Number(current_usage ?? 0)
    );
    const status = result.allowed ? 200 : 429;
    return json({ result }, { status });
  } catch {
    return json({ error: 'Failed to check quota' }, { status: 500 });
  }
});

/**
 * GET /quotas/history — usage history for a resource type
 * Query: resource_type (required), limit (default 50, max 200)
 */
tenantQuotas.get('/history', auth(), async (c) => {
  const { tenantId } = getTenant(c);
  const resourceType = c.req.query('resource_type');
  if (!resourceType) return json({ error: 'resource_type query param is required' }, { status: 400 });

  const limit = Math.min(parseInt(c.req.query('limit') ?? '50', 10) || 50, 200);
  try {
    const history = await getQuotaHistory(c.env.DB, tenantId, resourceType, limit);
    return json({ history });
  } catch {
    return json({ error: 'Failed to fetch quota history' }, { status: 500 });
  }
});

/**
 * GET /quotas/tier-defaults/:tier — public: return default quotas for a given tier
 * Tiers: starter | pro | enterprise
 */
tenantQuotas.get('/tier-defaults/:tier', async (c) => {
  const tier = c.req.param('tier');
  const validTiers = ['starter', 'pro', 'enterprise'];
  if (!validTiers.includes(tier)) {
    return json({ error: `tier must be one of: ${validTiers.join(', ')}` }, { status: 400 });
  }
  const defaults = getTierDefaults(tier);
  return json({ tier, defaults });
});

/**
 * PUT /quotas/admin/quotas/:tenantId — admin: update quota limits for a tenant
 * Requires X-Admin-Key header
 */
tenantQuotas.put('/admin/quotas/:tenantId', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return json({ error: 'Forbidden' }, { status: 403 });

  const targetTenantId = c.req.param('tenantId');
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const updates: Record<string, number | null> = {};
  const allowed = ['maxProjects', 'maxTeamMembers', 'maxApiKeys', 'maxMissionsPerDay', 'maxTemplates', 'maxWebhooks', 'maxStorageMb'];
  for (const key of allowed) {
    if (key in body) updates[key] = body[key] !== null ? Number(body[key]) : null;
  }

  try {
    const quotas = await updateQuotas(c.env.DB, targetTenantId, updates);
    if (!quotas) return json({ error: 'Tenant quota record not found' }, { status: 404 });
    return json({ quotas });
  } catch {
    return json({ error: 'Failed to update quotas' }, { status: 500 });
  }
});

/**
 * GET /quotas/admin/overview — admin: tenants at 75%+ quota utilization
 * Requires X-Admin-Key header
 */
tenantQuotas.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return json({ error: 'Forbidden' }, { status: 403 });

  try {
    const overview = await getAdminQuotaOverview(c.env.DB);
    return json({ overview });
  } catch {
    return json({ error: 'Failed to fetch admin overview' }, { status: 500 });
  }
});

/**
 * POST /quotas/admin/upgrade/:tenantId — admin: upgrade quota limits to a new tier
 * Requires X-Admin-Key header
 * Body: { tier: string }
 */
tenantQuotas.post('/admin/upgrade/:tenantId', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return json({ error: 'Forbidden' }, { status: 403 });

  const targetTenantId = c.req.param('tenantId');
  let body: Record<string, unknown>;
  try {
    body = await c.req.json();
  } catch {
    return json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { tier } = body;
  const validTiers = ['starter', 'pro', 'enterprise'];
  if (!tier || !validTiers.includes(String(tier))) {
    return json({ error: `tier must be one of: ${validTiers.join(', ')}` }, { status: 400 });
  }

  try {
    const quotas = await upgradeQuotasForTier(c.env.DB, targetTenantId, String(tier));
    if (!quotas) return json({ error: 'Tenant quota record not found' }, { status: 404 });
    return json({ quotas, upgradedTo: tier });
  } catch {
    return json({ error: 'Failed to upgrade quotas' }, { status: 500 });
  }
});
