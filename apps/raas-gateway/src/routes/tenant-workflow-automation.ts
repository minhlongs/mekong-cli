/**
 * Tenant Workflow Automation routes
 * Mount at: /v1/workflow-automation
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import { tenantWorkflowAutomationService as svc } from '../services/tenant-workflow-automation-service';

const app = new Hono<{ Bindings: Env }>();

app.use('*', auth());

/** GET /v1/workflow-automation/workflows — List active workflows for tenant */
app.get('/workflows', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listWorkflows(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[workflow-automation GET /workflows] error:', err);
    return c.json({ success: false, error: 'Failed to list workflows' }, 500);
  }
});

/** POST /v1/workflow-automation/workflows — Create a workflow automation */
app.post('/workflows', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json();
    if (!body?.workflow_name || !body?.trigger_event || !body?.action_type) {
      return c.json({ success: false, error: 'workflow_name, trigger_event, action_type are required' }, 400);
    }
    const created = await svc.createWorkflow(c.env.DB, tenantId, body);
    return c.json({ success: true, data: created }, 201);
  } catch (err) {
    console.error('[workflow-automation POST /workflows] error:', err);
    return c.json({ success: false, error: 'Failed to create workflow' }, 500);
  }
});

/** GET /v1/workflow-automation/runs?workflow_id=&limit= — Run history for tenant */
app.get('/runs', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const workflowId = c.req.query('workflow_id');
    const limit = parseInt(c.req.query('limit') ?? '50', 10) || 50;
    const data = await svc.getRuns(c.env.DB, tenantId, workflowId, limit);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[workflow-automation GET /runs] error:', err);
    return c.json({ success: false, error: 'Failed to fetch runs' }, 500);
  }
});

/** GET /v1/workflow-automation/admin/overview — Platform-wide stats (admin only) */
app.get('/admin/overview', async (c) => {
  try {
    const adminKey = c.req.header('X-Admin-Key');
    if (!adminKey || adminKey !== c.env.ADMIN_API_KEY) {
      return c.json({ success: false, error: 'Forbidden' }, 403);
    }
    const data = await svc.getAdminOverview(c.env.DB);
    return c.json({ success: true, data });
  } catch (err) {
    console.error('[workflow-automation GET /admin/overview] error:', err);
    return c.json({ success: false, error: 'Failed to fetch admin overview' }, 500);
  }
});

export { app as tenantWorkflowAutomation };
