/**
 * Mission Approval Workflow routes — multi-step approval chains for missions
 * Auth endpoints require JWT/API-key. Admin endpoint requires X-Admin-Key.
 * Mount path: /v1/mission-approvals
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { auth, getTenant } from '../middleware/auth';
import * as svc from '../services/mission-approval-workflow-service';

const app = new Hono<{ Bindings: Env }>();

// GET /workflows — list all workflows for tenant
app.get('/workflows', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listWorkflows(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /workflows — create a new approval workflow
app.post('/workflows', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{ name: string; description?: string; steps?: unknown[] }>();
    if (!body.name) return c.json({ error: 'name is required' }, 400);
    const data = await svc.createWorkflow(c.env.DB, tenantId, body);
    return c.json({ success: true, data }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /workflows/:id — get single workflow
app.get('/workflows/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.getWorkflow(c.env.DB, tenantId, c.req.param('id'));
    if (!data) return c.json({ error: 'Workflow not found' }, 404);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// PUT /workflows/:id — update workflow
app.put('/workflows/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      name?: string; description?: string; steps?: unknown[]; is_active?: boolean;
    }>();
    const data = await svc.updateWorkflow(c.env.DB, tenantId, c.req.param('id'), body);
    if (!data) return c.json({ error: 'Workflow not found' }, 404);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /submit — submit a mission for approval
app.post('/submit', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      mission_id: string; workflow_id: string; requested_by?: string;
    }>();
    if (!body.mission_id) return c.json({ error: 'mission_id is required' }, 400);
    if (!body.workflow_id) return c.json({ error: 'workflow_id is required' }, 400);
    const data = await svc.submitForApproval(
      c.env.DB, tenantId, body.mission_id, body.workflow_id,
      body.requested_by ?? tenantId
    );
    return c.json({ success: true, data }, 201);
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /requests/:id — get approval request with decisions
app.get('/requests/:id', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.getApprovalRequest(c.env.DB, tenantId, c.req.param('id'));
    if (!data) return c.json({ error: 'Approval request not found' }, 404);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// POST /requests/:id/decide — record approve/reject/delegate decision
app.post('/requests/:id/decide', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      approver_id: string; decision: string; comment?: string;
    }>();
    if (!body.approver_id) return c.json({ error: 'approver_id is required' }, 400);
    if (!['approve', 'reject', 'delegate'].includes(body.decision)) {
      return c.json({ error: 'decision must be approve, reject, or delegate' }, 400);
    }
    const data = await svc.makeDecision(
      c.env.DB, tenantId, c.req.param('id'),
      body.approver_id, body.decision, body.comment
    );
    if (!data) return c.json({ error: 'Request not found or not pending' }, 404);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /pending — list pending approvals for tenant
app.get('/pending', auth(), async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const data = await svc.listPendingApprovals(c.env.DB, tenantId);
    return c.json({ success: true, data });
  } catch (e: unknown) {
    return c.json({ error: (e as Error).message }, 500);
  }
});

// GET /admin/overview — admin stats (X-Admin-Key required)
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

export { app as missionApprovalWorkflow };
