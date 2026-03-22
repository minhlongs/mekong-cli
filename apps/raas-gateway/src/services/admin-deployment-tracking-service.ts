// Admin Deployment Tracking Service — list deployments, create, rollbacks, dashboard summary

const adminDeploymentTrackingService = {
  /** List deployments with optional filters (environment, status, limit) */
  async listDeployments(db: any, filters?: { environment?: string; status?: string; limit?: number }): Promise<unknown[]> {
    try {
      const conditions: string[] = [];
      const binds: unknown[] = [];

      if (filters?.environment) { conditions.push('environment = ?'); binds.push(filters.environment); }
      if (filters?.status) { conditions.push('status = ?'); binds.push(filters.status); }

      const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
      binds.push(Math.min(filters?.limit ?? 50, 200));

      const rows = await db.prepare(
        `SELECT * FROM deployments ${where} ORDER BY started_at DESC LIMIT ?`
      ).bind(...binds).all();
      return (rows.results as unknown[]);
    } catch (e) {
      throw e;
    }
  },

  /** Create a new deployment record */
  async createDeployment(db: any, data: {
    version: string;
    environment?: string;
    deploy_type?: string;
    deployed_by?: string;
    commit_hash?: string;
    changelog?: string;
  }): Promise<unknown> {
    try {
      const id = crypto.randomUUID();
      const row = await db.prepare(
        `INSERT INTO deployments (id, version, environment, deploy_type, deployed_by, commit_hash, changelog)
         VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *`
      ).bind(
        id,
        data.version,
        data.environment ?? 'production',
        data.deploy_type ?? 'full',
        data.deployed_by ?? null,
        data.commit_hash ?? null,
        data.changelog ?? null
      ).first();
      return row as unknown;
    } catch (e) {
      throw e;
    }
  },

  /** Get all rollbacks, optionally filtered by deployment_id */
  async getRollbacks(db: any, filters?: { deployment_id?: string; limit?: number }): Promise<unknown[]> {
    try {
      const conditions: string[] = [];
      const binds: unknown[] = [];

      if (filters?.deployment_id) { conditions.push('deployment_id = ?'); binds.push(filters.deployment_id); }

      const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
      binds.push(Math.min(filters?.limit ?? 50, 200));

      const rows = await db.prepare(
        `SELECT * FROM deployment_rollbacks ${where} ORDER BY created_at DESC LIMIT ?`
      ).bind(...binds).all();
      return (rows.results as unknown[]);
    } catch (e) {
      throw e;
    }
  },

  /** Dashboard summary: deployment counts by status */
  async getDashboard(db: any): Promise<unknown> {
    try {
      const [total, pending, running, success, failed, rollbacks] = await Promise.all([
        db.prepare(`SELECT COUNT(*) as count FROM deployments`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM deployments WHERE status = 'pending'`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM deployments WHERE status = 'running'`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM deployments WHERE status = 'success'`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM deployments WHERE status = 'failed'`).first(),
        db.prepare(`SELECT COUNT(*) as count FROM deployment_rollbacks`).first(),
      ]);
      return {
        deployments: {
          total: (total as any)?.count ?? 0,
          pending: (pending as any)?.count ?? 0,
          running: (running as any)?.count ?? 0,
          success: (success as any)?.count ?? 0,
          failed: (failed as any)?.count ?? 0,
        },
        rollbacks: {
          total: (rollbacks as any)?.count ?? 0,
        },
      };
    } catch (e) {
      throw e;
    }
  },
};

export { adminDeploymentTrackingService };
