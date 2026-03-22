/**
 * Mission Workflow Engine Service — CRUD for workflow definitions and execution records
 * All operations are tenant-scoped. Uses raw db: any to stay compatible with D1 bindings.
 */

// ── List workflows for a tenant ──────────────────────────────────────────────

async function listWorkflows(
  db: any,
  tenantId: string
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const result = await db
      .prepare('SELECT * FROM mission_workflows WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return { success: true, data: result.results };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Failed to list workflows';
    return { success: false, error };
  }
}

// ── Create a new workflow definition ─────────────────────────────────────────

async function createWorkflow(
  db: any,
  tenantId: string,
  payload: {
    workflow_name: string;
    trigger_event: string;
    steps: unknown[];
    status?: string;
  }
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const stepsJson = JSON.stringify(payload.steps);
    const status = payload.status ?? 'active';
    const now = new Date().toISOString().replace('T', ' ').replace(/\.\d+Z$/, '');

    await db
      .prepare(
        `INSERT INTO mission_workflows
         (id, tenant_id, workflow_name, trigger_event, steps_json, status, created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(id, tenantId, payload.workflow_name, payload.trigger_event, stepsJson, status, now, now)
      .run();

    const created = await db
      .prepare('SELECT * FROM mission_workflows WHERE id = ?')
      .bind(id)
      .first();

    return { success: true, data: created };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Failed to create workflow';
    return { success: false, error };
  }
}

// ── List executions for a tenant (optionally filter by workflow_id) ───────────

async function getExecutions(
  db: any,
  tenantId: string,
  workflowId?: string
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    let query = 'SELECT * FROM mission_workflow_executions WHERE tenant_id = ?';
    const bindings: string[] = [tenantId];

    if (workflowId) {
      query += ' AND workflow_id = ?';
      bindings.push(workflowId);
    }

    query += ' ORDER BY started_at DESC';

    const result = await db
      .prepare(query)
      .bind(...bindings)
      .all();

    return { success: true, data: result.results };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Failed to get executions';
    return { success: false, error };
  }
}

// ── Admin overview across all tenants ────────────────────────────────────────

async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const [workflows, executions] = await Promise.all([
      db
        .prepare(
          `SELECT
             COUNT(*) as total,
             SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active,
             SUM(CASE WHEN status = 'inactive' THEN 1 ELSE 0 END) as inactive
           FROM mission_workflows`
        )
        .first(),
      db
        .prepare(
          `SELECT
             COUNT(*) as total,
             SUM(CASE WHEN status = 'running' THEN 1 ELSE 0 END) as running,
             SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
             SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
           FROM mission_workflow_executions`
        )
        .first(),
    ]);

    return {
      success: true,
      data: { workflows, executions },
    };
  } catch (err) {
    const error = err instanceof Error ? err.message : 'Failed to get admin overview';
    return { success: false, error };
  }
}

// ── Public API ────────────────────────────────────────────────────────────────

export const missionWorkflowEngineService = {
  listWorkflows,
  createWorkflow,
  getExecutions,
  getAdminOverview,
};
