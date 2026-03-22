/**
 * Platform Security Policies routes — policy management, templates, violations, compliance
 * Mount path: /security
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import * as svc from '../services/platform-security-policies-service';

const app = new Hono<{ Bindings: Env }>();

// GET /policies — list tenant policies (auth)
app.get('/policies', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listPolicies(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /policies — create policy (auth)
app.post('/policies', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      policy_name: string;
      policy_type?: string;
      rules_json?: Record<string, unknown>;
      is_enforced?: boolean;
      severity?: string;
    }>();
    if (!body.policy_name) return c.json({ error: 'policy_name is required' }, 400);
    const data = await svc.createPolicy(c.env.DB, tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// PUT /policies/:id — update policy (auth)
app.put('/policies/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      policy_name?: string;
      policy_type?: string;
      rules_json?: Record<string, unknown>;
      is_enforced?: boolean;
      severity?: string;
    }>();
    const data = await svc.updatePolicy(c.env.DB, tenantId, c.req.param('id'), body);
    if (!data) return c.json({ error: 'Policy not found' }, 404);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// DELETE /policies/:id — soft-delete policy (auth)
app.delete('/policies/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.deletePolicy(c.env.DB, tenantId, c.req.param('id'));
    if (!data) return c.json({ error: 'Policy not found' }, 404);
    return c.json({ success: true });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /templates — list templates (public, no auth)
app.get('/templates', async (c) => {
  try {
    const data = await svc.listTemplates(c.env.DB);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /apply-template — apply template to tenant (auth)
app.post('/apply-template', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ template_id: string }>();
    if (!body.template_id) return c.json({ error: 'template_id is required' }, 400);
    const data = await svc.applyTemplate(c.env.DB, tenantId, body.template_id);
    if (!data) return c.json({ error: 'Template not found' }, 404);
    return c.json({ success: true, data }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /violations — list violations (auth)
app.get('/violations', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listViolations(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /violations/:id/resolve — resolve violation (auth)
app.post('/violations/:id/resolve', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.resolveViolation(c.env.DB, tenantId, c.req.param('id'));
    if (!data) return c.json({ error: 'Violation not found or already resolved' }, 404);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /compliance — compliance score (auth)
app.get('/compliance', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.getComplianceScore(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /admin/overview — admin stats (X-Admin-Key)
app.get('/admin/overview', async (c) => {
  const key = c.req.header('X-Admin-Key');
  if (key !== c.env.ADMIN_API_KEY) return c.json({ error: 'Forbidden' }, 403);
  try {
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

export { app as platformSecurityPolicies };
