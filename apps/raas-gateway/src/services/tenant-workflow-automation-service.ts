/**
 * Tenant Workflow Automation Service
 * CRUD for workflow_automations + run history per tenant
 */

function newId(): string {
  return crypto.randomUUID();
}

export const tenantWorkflowAutomationService = {
  /**
   * List active workflow automations for a tenant
   */
  async listWorkflows(db: any, tenantId: string): Promise<any[]> {
    try {
      const result = await db
        .prepare(
          'SELECT * FROM workflow_automations WHERE tenant_id = ? AND is_active = 1 ORDER BY created_at DESC'
        )
        .bind(tenantId)
        .all();
      return (result.results ?? []) as any[];
    } catch (err) {
      console.error('[WorkflowAutomationService.listWorkflows] error:', err);
      throw err;
    }
  },

  /**
   * Create a new workflow automation for a tenant
   */
  async createWorkflow(db: any, tenantId: string, data: {
    workflow_name: string;
    trigger_event: string;
    condition_json?: string;
    action_type: string;
    action_config_json?: string;
  }): Promise<any> {
    try {
      const id = newId();
      const now = new Date().toISOString();
      await db
        .prepare(
          `INSERT INTO workflow_automations
            (id, tenant_id, workflow_name, trigger_event, condition_json, action_type, action_config_json, is_active, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)`
        )
        .bind(
          id,
          tenantId,
          data.workflow_name,
          data.trigger_event,
          data.condition_json ?? '{}',
          data.action_type,
          data.action_config_json ?? '{}',
          now,
          now
        )
        .run();
      return { id, tenant_id: tenantId, ...data, is_active: 1, created_at: now, updated_at: now };
    } catch (err) {
      console.error('[WorkflowAutomationService.createWorkflow] error:', err);
      throw err;
    }
  },

  /**
   * Get run history for a tenant, optionally filtered by workflow_id
   */
  async getRuns(db: any, tenantId: string, workflowId?: string, limit = 50): Promise<any[]> {
    try {
      const cap = Math.min(limit, 200);
      const result = workflowId
        ? await db
            .prepare(
              'SELECT * FROM workflow_automation_runs WHERE tenant_id = ? AND workflow_id = ? ORDER BY started_at DESC LIMIT ?'
            )
            .bind(tenantId, workflowId, cap)
            .all()
        : await db
            .prepare(
              'SELECT * FROM workflow_automation_runs WHERE tenant_id = ? ORDER BY started_at DESC LIMIT ?'
            )
            .bind(tenantId, cap)
            .all();
      return (result.results ?? []) as any[];
    } catch (err) {
      console.error('[WorkflowAutomationService.getRuns] error:', err);
      throw err;
    }
  },

  /**
   * Admin overview: totals across all tenants
   */
  async getAdminOverview(db: any): Promise<{ total_workflows: number; active_tenants: number; total_runs: number }> {
    try {
      const wf = await db
        .prepare(
          'SELECT COUNT(*) as total_workflows, COUNT(DISTINCT tenant_id) as active_tenants FROM workflow_automations WHERE is_active = 1'
        )
        .first() as any;
      const runs = await db
        .prepare('SELECT COUNT(*) as total_runs FROM workflow_automation_runs')
        .first() as any;
      return {
        total_workflows: wf?.total_workflows ?? 0,
        active_tenants: wf?.active_tenants ?? 0,
        total_runs: runs?.total_runs ?? 0,
      };
    } catch (err) {
      console.error('[WorkflowAutomationService.getAdminOverview] error:', err);
      throw err;
    }
  },
};
