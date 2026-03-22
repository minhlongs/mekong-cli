/**
 * Mission Workflow Engine routes
 * Tenant routes: GET /workflows, POST /workflows, GET /executions — require auth
 * Admin route:   GET /admin/overview — requires X-Admin-Key header
 */

import { Hono } from 'hono';
import { auth, getTenant } from '../middleware/auth';
import { missionWorkflowEngineService } from '../services/mission-workflow-engine';

// Inline Bindings to avoid index.ts dependency
interface Bindings {
  DB: any;
  ADMIN_API_KEY: string;
  [key: string]: unknown;
}

const app = new Hono<{ Bindings: Bindings }>();

// ── GET /workflows — list tenant workflows ────────────────────────────────────

app.get('/workflows', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const result = await missionWorkflowEngineService.listWorkflows(c.env.DB, tenant.tenantId);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Internal error';
    return c.json({ error }, 500);
  }
});

// ── POST /workflows — create a new workflow ───────────────────────────────────

app.post('/workflows', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const body = await c.req.json().catch(() => ({}));

    const workflowName = body.workflow_name?.trim();
    const triggerEvent = body.trigger_event?.trim();
    const steps = body.steps;

    if (!workflowName) return c.json({ error: 'workflow_name is required' }, 400);
    if (!triggerEvent) return c.json({ error: 'trigger_event is required' }, 400);
    if (!Array.isArray(steps)) return c.json({ error: 'steps must be an array' }, 400);

    const result = await missionWorkflowEngineService.createWorkflow(c.env.DB, tenant.tenantId, {
      workflow_name: workflowName,
      trigger_event: triggerEvent,
      steps,
      status: body.status,
    });

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data }, 201);
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Internal error';
    return c.json({ error }, 500);
  }
});

// ── GET /executions — list tenant executions (optional ?workflow_id=) ─────────

app.get('/executions', auth(), async (c) => {
  try {
    const tenant = getTenant(c);
    const workflowId = c.req.query('workflow_id') ?? undefined;

    const result = await missionWorkflowEngineService.getExecutions(
      c.env.DB,
      tenant.tenantId,
      workflowId
    );

    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Internal error';
    return c.json({ error }, 500);
  }
});

// ── GET /admin/overview — platform-wide stats, X-Admin-Key required ───────────

app.get('/admin/overview', async (c) => {
  try {
    const key = c.req.header('X-Admin-Key');
    if (!key || key !== c.env.ADMIN_API_KEY) {
      return c.json({ error: 'Forbidden' }, 403);
    }

    const result = await missionWorkflowEngineService.getAdminOverview(c.env.DB);
    if (!result.success) return c.json({ error: result.error }, 500);
    return c.json({ success: true, data: result.data });
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Internal error';
    return c.json({ error }, 500);
  }
});

export { app as missionWorkflowEngine };
