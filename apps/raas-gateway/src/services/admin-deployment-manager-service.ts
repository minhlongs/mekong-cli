// Admin Deployment Manager Service — deployment lifecycle, checks, canary configs

const adminDeploymentManagerService = {
  /** List deployments with optional filters (environment, status, limit) */
  async listDeployments(db: any, filters?: { environment?: string; status?: string; limit?: number }): Promise<unknown[]> {
    const conditions: string[] = [];
    const binds: unknown[] = [];

    if (filters?.environment) { conditions.push('environment = ?'); binds.push(filters.environment); }
    if (filters?.status) { conditions.push('status = ?'); binds.push(filters.status); }

    const where = conditions.length ? `WHERE ${conditions.join(' AND ')}` : '';
    binds.push(Math.min(filters?.limit ?? 50, 200));

    const rows = await db.prepare(
      `SELECT * FROM deployments ${where} ORDER BY created_at DESC LIMIT ?`
    ).bind(...binds).all();
    return rows.results;
  },

  /** Create a new deployment record */
  async createDeployment(db: any, data: {
    version: string;
    environment?: string;
    deploy_type?: string;
    commit_hash?: string;
    release_notes?: string;
    deployed_by?: string;
    health_check_url?: string;
  }): Promise<unknown> {
    const id = crypto.randomUUID();
    return db.prepare(
      `INSERT INTO deployments (id, version, environment, deploy_type, commit_hash, release_notes, deployed_by, health_check_url)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?) RETURNING *`
    ).bind(
      id,
      data.version,
      data.environment ?? 'production',
      data.deploy_type ?? 'full',
      data.commit_hash ?? null,
      data.release_notes ?? null,
      data.deployed_by ?? null,
      data.health_check_url ?? null
    ).first();
  },

  /** Get a single deployment by ID */
  async getDeployment(db: any, id: string): Promise<unknown | null> {
    return db.prepare(`SELECT * FROM deployments WHERE id = ?`).bind(id).first();
  },

  /** Mark deployment as running */
  async startDeployment(db: any, id: string): Promise<unknown | null> {
    return db.prepare(
      `UPDATE deployments SET status = 'running', started_at = datetime('now') WHERE id = ? RETURNING *`
    ).bind(id).first();
  },

  /** Complete a deployment with given status (success|failed) */
  async completeDeployment(db: any, id: string, status: string): Promise<unknown | null> {
    return db.prepare(
      `UPDATE deployments SET status = ?, completed_at = datetime('now') WHERE id = ? RETURNING *`
    ).bind(status, id).first();
  },

  /** Rollback — create new deployment referencing the source deployment */
  async rollback(db: any, id: string): Promise<unknown | null> {
    const source: any = await db.prepare(`SELECT * FROM deployments WHERE id = ?`).bind(id).first();
    if (!source) return null;
    const rollbackId = crypto.randomUUID();
    return db.prepare(
      `INSERT INTO deployments (id, version, environment, deploy_type, status, deployed_by, rollback_from)
       VALUES (?, ?, ?, 'rollback', 'pending', ?, ?) RETURNING *`
    ).bind(rollbackId, source.version, source.environment, source.deployed_by, id).first();
  },

  /** Add a health/smoke check result for a deployment */
  async addCheck(db: any, deploymentId: string, checkType: string, resultJson?: Record<string, unknown>): Promise<unknown> {
    const id = crypto.randomUUID();
    return db.prepare(
      `INSERT INTO deployment_checks (id, deployment_id, check_type, result_json)
       VALUES (?, ?, ?, ?) RETURNING *`
    ).bind(id, deploymentId, checkType, JSON.stringify(resultJson ?? {})).first();
  },

  /** Get all checks for a deployment */
  async getChecks(db: any, deploymentId: string): Promise<unknown[]> {
    const rows = await db.prepare(
      `SELECT * FROM deployment_checks WHERE deployment_id = ? ORDER BY checked_at DESC`
    ).bind(deploymentId).all();
    return rows.results;
  },

  /** Get canary config for a deployment */
  async getCanaryConfig(db: any, deploymentId: string): Promise<unknown | null> {
    return db.prepare(`SELECT * FROM canary_configs WHERE deployment_id = ?`).bind(deploymentId).first();
  },

  /** Create or replace canary config for a deployment */
  async setCanaryConfig(db: any, deploymentId: string, data: {
    percentage?: number;
    duration_minutes?: number;
    success_threshold?: number;
    auto_promote?: number;
    metrics_json?: Record<string, unknown>;
  }): Promise<unknown> {
    const id = crypto.randomUUID();
    return db.prepare(
      `INSERT INTO canary_configs (id, deployment_id, percentage, duration_minutes, success_threshold, auto_promote, metrics_json)
       VALUES (?, ?, ?, ?, ?, ?, ?)
       ON CONFLICT(deployment_id) DO UPDATE SET
         percentage = excluded.percentage,
         duration_minutes = excluded.duration_minutes,
         success_threshold = excluded.success_threshold,
         auto_promote = excluded.auto_promote,
         metrics_json = excluded.metrics_json
       RETURNING *`
    ).bind(
      id, deploymentId,
      data.percentage ?? 10,
      data.duration_minutes ?? 30,
      data.success_threshold ?? 0.99,
      data.auto_promote ?? 0,
      JSON.stringify(data.metrics_json ?? {})
    ).first();
  },

  /** Promote canary to full deployment */
  async promoteCanary(db: any, deploymentId: string): Promise<unknown | null> {
    return db.prepare(
      `UPDATE deployments SET canary_percentage = 100, status = 'promoted', completed_at = datetime('now')
       WHERE id = ? RETURNING *`
    ).bind(deploymentId).first();
  },

  /** Admin overview: deployment counts by status and environment */
  async getAdminOverview(db: any): Promise<unknown> {
    const [total, pending, running, success, failed, canary] = await Promise.all([
      db.prepare(`SELECT COUNT(*) as count FROM deployments`).first() as Promise<{ count: number } | null>,
      db.prepare(`SELECT COUNT(*) as count FROM deployments WHERE status = 'pending'`).first() as Promise<{ count: number } | null>,
      db.prepare(`SELECT COUNT(*) as count FROM deployments WHERE status = 'running'`).first() as Promise<{ count: number } | null>,
      db.prepare(`SELECT COUNT(*) as count FROM deployments WHERE status = 'success'`).first() as Promise<{ count: number } | null>,
      db.prepare(`SELECT COUNT(*) as count FROM deployments WHERE status = 'failed'`).first() as Promise<{ count: number } | null>,
      db.prepare(`SELECT COUNT(*) as count FROM deployments WHERE deploy_type = 'canary'`).first() as Promise<{ count: number } | null>,
    ]);
    return {
      deployments: {
        total: total?.count ?? 0,
        pending: pending?.count ?? 0,
        running: running?.count ?? 0,
        success: success?.count ?? 0,
        failed: failed?.count ?? 0,
        canary: canary?.count ?? 0,
      },
    };
  },
};

export { adminDeploymentManagerService };
