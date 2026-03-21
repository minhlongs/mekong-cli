/**
 * Workflow routes — CRUD and execution endpoints for custom workflow builder
 * Mounted at /v1/workflows in parent router
 */

import { Hono } from 'hono';
import type { Env } from '../index';
import { getTenant } from '../middleware/auth';
import {
  createWorkflow,
  getWorkflows,
  getWorkflow,
  updateWorkflow,
  deleteWorkflow,
  executeWorkflow,
  getExecution,
  listExecutions,
  cancelExecution,
  getWorkflowStats,
  type WorkflowStatus,
  type ExecutionStatus,
} from '../services/workflow-service';

const app = new Hono<{ Bindings: Env }>();

// GET /stats — must be BEFORE /:id to avoid route shadowing
app.get('/stats', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const stats = await getWorkflowStats(c.env.DB, tenantId);
    return c.json({ success: true, data: stats });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET /executions/:executionId — before /:id to prevent shadowing
app.get('/executions/:executionId', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const execution = await getExecution(c.env.DB, tenantId, c.req.param('executionId'));
    if (!execution) return c.json({ success: false, error: 'Execution not found' }, 404);
    return c.json({ success: true, data: execution });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// POST /executions/:executionId/cancel
app.post('/executions/:executionId/cancel', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const execution = await cancelExecution(c.env.DB, tenantId, c.req.param('executionId'));
    if (!execution) return c.json({ success: false, error: 'Execution not found or not running' }, 404);
    return c.json({ success: true, data: execution });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// POST / — create workflow
app.post('/', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      name?: string;
      description?: string;
      steps?: unknown[];
      triggerType?: string;
      triggerConfig?: Record<string, unknown>;
    }>();

    if (!body.name?.trim()) {
      return c.json({ success: false, error: 'name is required' }, 400);
    }

    const workflow = await createWorkflow(c.env.DB, tenantId, {
      name: body.name.trim(),
      description: body.description,
      steps: (body.steps ?? []) as Parameters<typeof createWorkflow>[2]['steps'],
      triggerType: body.triggerType as Parameters<typeof createWorkflow>[2]['triggerType'],
      triggerConfig: body.triggerConfig,
    });

    return c.json({ success: true, data: workflow }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET / — list workflows
app.get('/', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const status = c.req.query('status') as WorkflowStatus | undefined;
    const workflows = await getWorkflows(c.env.DB, tenantId, { status });
    return c.json({ success: true, data: workflows, total: workflows.length });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET /:id — get workflow
app.get('/:id', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const workflow = await getWorkflow(c.env.DB, tenantId, c.req.param('id'));
    if (!workflow) return c.json({ success: false, error: 'Workflow not found' }, 404);
    return c.json({ success: true, data: workflow });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// PUT /:id — update workflow
app.put('/:id', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<{
      name?: string;
      description?: string;
      steps?: unknown[];
      status?: string;
      triggerType?: string;
      triggerConfig?: Record<string, unknown>;
    }>();

    const workflow = await updateWorkflow(c.env.DB, tenantId, c.req.param('id'), {
      name: body.name,
      description: body.description,
      steps: body.steps as Parameters<typeof updateWorkflow>[3]['steps'],
      status: body.status as WorkflowStatus | undefined,
      triggerType: body.triggerType as Parameters<typeof updateWorkflow>[3]['triggerType'],
      triggerConfig: body.triggerConfig,
    });

    if (!workflow) return c.json({ success: false, error: 'Workflow not found' }, 404);
    return c.json({ success: true, data: workflow });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// DELETE /:id — delete workflow
app.delete('/:id', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const deleted = await deleteWorkflow(c.env.DB, tenantId, c.req.param('id'));
    if (!deleted) return c.json({ success: false, error: 'Workflow not found' }, 404);
    return c.json({ success: true, data: { deleted: true } });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// POST /:id/execute — execute workflow
app.post('/:id/execute', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const body = await c.req.json<Record<string, unknown>>().catch(() => ({}));
    const execution = await executeWorkflow(c.env.DB, tenantId, c.req.param('id'), body);
    if (!execution) return c.json({ success: false, error: 'Workflow not found' }, 404);
    return c.json({ success: true, data: execution }, 201);
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

// GET /:id/executions — list executions for a workflow
app.get('/:id/executions', async (c) => {
  try {
    const { tenantId } = getTenant(c);
    const status = c.req.query('status') as ExecutionStatus | undefined;
    const limit = c.req.query('limit') ? Number(c.req.query('limit')) : 50;
    const executions = await listExecutions(c.env.DB, tenantId, {
      workflowId: c.req.param('id'),
      status,
      limit,
    });
    return c.json({ success: true, data: executions, total: executions.length });
  } catch (err) {
    return c.json({ success: false, error: String(err) }, 500);
  }
});

export const workflows = app;
