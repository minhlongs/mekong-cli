// Tenant Data Pipeline Service — CRUD for pipelines and pipeline run history

export const tenantDataPipelineService = {
  /** List all pipelines for a tenant, optionally filtered by status */
  async listPipelines(db: any, tenantId: string, filters?: { status?: string }): Promise<unknown[]> {
    try {
      const conditions: string[] = ['tenant_id = ?'];
      const binds: unknown[] = [tenantId];

      if (filters?.status) { conditions.push('status = ?'); binds.push(filters.status); }

      const rows = await db.prepare(
        `SELECT * FROM data_pipelines WHERE ${conditions.join(' AND ')} ORDER BY created_at DESC`
      ).bind(...binds).all();
      return rows.results as unknown[];
    } catch (e) {
      throw e;
    }
  },

  /** Create a new pipeline for a tenant */
  async createPipeline(db: any, tenantId: string, data: {
    pipeline_name: string;
    source_type: string;
    destination_type: string;
    transform_config_json?: string;
    schedule_cron?: string;
  }): Promise<unknown> {
    try {
      const id = crypto.randomUUID();
      const row = await db.prepare(
        `INSERT INTO data_pipelines (id, tenant_id, pipeline_name, source_type, destination_type, transform_config_json, schedule_cron)
         VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
      ).bind(
        id,
        tenantId,
        data.pipeline_name,
        data.source_type,
        data.destination_type,
        data.transform_config_json ?? '{}',
        data.schedule_cron ?? null
      ).first();
      return row as unknown;
    } catch (e) {
      throw e;
    }
  },

  /** List pipeline runs for a tenant, optionally filtered by pipeline_id */
  async getRuns(db: any, tenantId: string, filters?: { pipeline_id?: string; limit?: number }): Promise<unknown[]> {
    try {
      const conditions: string[] = ['tenant_id = ?'];
      const binds: unknown[] = [tenantId];

      if (filters?.pipeline_id) { conditions.push('pipeline_id = ?'); binds.push(filters.pipeline_id); }

      binds.push(Math.min(filters?.limit ?? 50, 200));

      const rows = await db.prepare(
        `SELECT * FROM data_pipeline_runs WHERE ${conditions.join(' AND ')} ORDER BY started_at DESC LIMIT ?`
      ).bind(...binds).all();
      return rows.results as unknown[];
    } catch (e) {
      throw e;
    }
  },

  /** Admin overview — pipeline and run counts across all tenants */
  async getAdminOverview(db: any): Promise<unknown> {
    try {
      const [totalPipelines, activePipelines, totalRuns, pendingRuns, failedRuns] = await Promise.all([
        db.prepare(`SELECT COUNT(*) as count FROM data_pipelines`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM data_pipelines WHERE status = 'active'`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM data_pipeline_runs`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM data_pipeline_runs WHERE status = 'pending'`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM data_pipeline_runs WHERE status = 'failed'`).first(),
      ]);
      return {
        pipelines: { total: totalPipelines?.count ?? 0, active: activePipelines?.count ?? 0 },
        runs: { total: totalRuns?.count ?? 0, pending: pendingRuns?.count ?? 0, failed: failedRuns?.count ?? 0 },
      };
    } catch (e) {
      throw e;
    }
  },
};
