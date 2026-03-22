/**
 * Platform Audit Policies routes — manage audit policies and violations
 * All endpoints require X-Admin-Key header. Mount path: /admin/platform-audit-policies
 */

import { Hono } from 'hono';
import { platformAuditPoliciesService as svc } from '../services/platform-audit-policies';

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

// Admin auth middleware for ALL routes
app.use('*', async (c, next) => {
  const adminKey = c.req.header('X-Admin-Key');
  if (adminKey !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  await next();
});

// GET /policies — list all audit policies
app.get('/policies', async (c) => {
  try {
    const policies = await svc.listPolicies(c.env.DB);
    return c.json({ policies, count: (policies as unknown[]).length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /policies — create a new audit policy
app.post('/policies', async (c) => {
  try {
    const body = await c.req.json<{
      policy_name: string;
      description?: string;
      event_types?: string;
      retention_days?: number;
      is_active?: number;
    }>();
    if (!body.policy_name) {
      return c.json({ error: 'policy_name is required' }, 400);
    }
    const policy = await svc.createPolicy(c.env.DB, body);
    return c.json({ policy }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /violations — list all policy violations
app.get('/violations', async (c) => {
  try {
    const violations = await svc.getViolations(c.env.DB);
    return c.json({ violations, count: (violations as unknown[]).length });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /dashboard — audit policies dashboard stats
app.get('/dashboard', async (c) => {
  try {
    const dashboard = await svc.getDashboard(c.env.DB);
    return c.json({ dashboard });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as platformAuditPolicies };
