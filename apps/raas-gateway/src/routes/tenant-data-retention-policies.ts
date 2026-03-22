/**
 * Tenant Data Retention Policies Routes — manage per-tenant data retention rules and run history
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { json } from '../utils/response';
import {
  listPolicies,
  createPolicy,
  getRuns,
  getAdminOverview,
} from '../services/tenant-data-retention-policies';

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

// Auth middleware for tenant routes
app.use('/policies', auth());
app.use('/policies/*', auth());
app.use('/runs', auth());
app.use('/runs/*', auth());

/** GET /policies — list data retention policies for authenticated tenant */
app.get('/policies', async (c) => {
  const tenant = getTenant(c);
  const result = await listPolicies(c.env.DB, tenant.tenantId);
  return json(result);
});

/** POST /policies — create a new data retention policy for authenticated tenant */
app.post('/policies', async (c) => {
  const tenant = getTenant(c);
  const body = await c.req.json().catch(() => ({}));

  if (!body.entity_type || typeof body.entity_type !== 'string') {
    return json({ error: 'entity_type is required', code: 'INVALID_INPUT' }, { status: 400 });
  }
  if (!body.retention_days || typeof body.retention_days !== 'number' || body.retention_days < 1) {
    return json({ error: 'retention_days must be a positive integer', code: 'INVALID_INPUT' }, { status: 400 });
  }

  const result = await createPolicy(c.env.DB, tenant.tenantId, {
    entity_type: body.entity_type,
    retention_days: body.retention_days,
    action: body.action,
    is_active: body.is_active,
  });

  if (result.error || !result.policy) {
    return json({ error: result.error ?? 'Failed to create policy', code: 'CREATE_FAILED' }, { status: 500 });
  }

  return json({ policy: result.policy }, { status: 201 });
});

/** GET /runs — list retention run history for authenticated tenant */
app.get('/runs', async (c) => {
  const tenant = getTenant(c);
  const result = await getRuns(c.env.DB, tenant.tenantId);
  return json(result);
});

/** GET /admin/overview — aggregate counts across all tenants (admin-only) */
app.get('/admin/overview', async (c) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
    return json({ error: 'Forbidden', code: 'FORBIDDEN' }, { status: 403 });
  }

  const result = await getAdminOverview(c.env.DB);
  return json(result);
});

export { app as dataRetentionPolicies };
