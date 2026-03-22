/** Mission SLA Compliance routes — policy management and violation tracking */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { missionSlaComplianceService as svc } from '../services/mission-sla-compliance-service';

const app = new Hono<{ Bindings: Env }>();

app.use('/*', auth());

app.get('/policies', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const policies = await svc.listPolicies(c.env.DB, tenantId);
    return c.json({ success: true, data: policies });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

app.post('/policies', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      policy_name?: string;
      max_execution_time_ms?: number;
      min_success_rate?: number;
      evaluation_window?: string;
    }>();

    if (!body.policy_name?.trim()) {
      return c.json({ success: false, error: 'policy_name is required' }, 400);
    }

    const policy = await svc.createPolicy(c.env.DB, tenantId, {
      policy_name: body.policy_name.trim(),
      max_execution_time_ms: body.max_execution_time_ms,
      min_success_rate: body.min_success_rate,
      evaluation_window: body.evaluation_window,
    });
    return c.json({ success: true, data: policy }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

app.get('/violations', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const policyId = c.req.query('policy_id');
    const violations = await svc.getViolations(c.env.DB, tenantId, policyId);
    return c.json({ success: true, data: violations });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
      return c.json({ success: false, error: 'Forbidden' }, 403);
    }
    const overview = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data: overview });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

export { app as missionSlaCompliance };
