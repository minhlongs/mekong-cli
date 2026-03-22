/**
 * Mission Scheduling Engine Service
 * CRUD + admin operations for scheduled_jobs, job_executions, skip_rules
 */

export const missionSchedulingService = {
  // --- Jobs ---

  async listJobs(db: any, tenantId: string) {
    const result = await db
      .prepare('SELECT * FROM scheduled_jobs WHERE tenant_id = ? ORDER BY created_at DESC')
      .bind(tenantId)
      .all();
    return result.results ?? [];
  },

  async createJob(db: any, tenantId: string, data: any) {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO scheduled_jobs
          (id, tenant_id, name, cron_expression, timezone, mission_config_json,
           status, next_run_at, max_runs, skip_if_running, execution_window_minutes,
           created_at, updated_at)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        data.name,
        data.cron_expression,
        data.timezone ?? 'UTC',
        JSON.stringify(data.mission_config ?? {}),
        data.status ?? 'active',
        data.next_run_at ?? null,
        data.max_runs ?? null,
        data.skip_if_running ?? 1,
        data.execution_window_minutes ?? 60,
        now,
        now
      )
      .run();
    return this.getJob(db, tenantId, id);
  },

  async getJob(db: any, tenantId: string, id: string) {
    return db
      .prepare('SELECT * FROM scheduled_jobs WHERE id = ? AND tenant_id = ?')
      .bind(id, tenantId)
      .first();
  },

  async updateJob(db: any, tenantId: string, id: string, data: any) {
    const fields: string[] = [];
    const values: any[] = [];

    const allowed = [
      'name', 'cron_expression', 'timezone', 'mission_config_json',
      'status', 'next_run_at', 'max_runs', 'skip_if_running', 'execution_window_minutes'
    ];

    for (const key of allowed) {
      if (data[key] !== undefined) {
        fields.push(`${key} = ?`);
        values.push(data[key]);
      }
    }

    if (fields.length === 0) return this.getJob(db, tenantId, id);

    fields.push('updated_at = ?');
    values.push(new Date().toISOString());
    values.push(id, tenantId);

    await db
      .prepare(`UPDATE scheduled_jobs SET ${fields.join(', ')} WHERE id = ? AND tenant_id = ?`)
      .bind(...values)
      .run();
    return this.getJob(db, tenantId, id);
  },

  async deleteJob(db: any, tenantId: string, id: string) {
    await db
      .prepare('DELETE FROM scheduled_jobs WHERE id = ? AND tenant_id = ?')
      .bind(id, tenantId)
      .run();
    return { id, deleted: true };
  },

  async pauseJob(db: any, tenantId: string, id: string) {
    await db
      .prepare(`UPDATE scheduled_jobs SET status = 'paused', updated_at = ? WHERE id = ? AND tenant_id = ?`)
      .bind(new Date().toISOString(), id, tenantId)
      .run();
    return this.getJob(db, tenantId, id);
  },

  async resumeJob(db: any, tenantId: string, id: string) {
    await db
      .prepare(`UPDATE scheduled_jobs SET status = 'active', updated_at = ? WHERE id = ? AND tenant_id = ?`)
      .bind(new Date().toISOString(), id, tenantId)
      .run();
    return this.getJob(db, tenantId, id);
  },

  async triggerJob(db: any, tenantId: string, id: string) {
    const job = await this.getJob(db, tenantId, id);
    if (!job) return null;

    const execId = crypto.randomUUID();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO job_executions (id, job_id, tenant_id, status, started_at)
         VALUES (?, ?, ?, 'running', ?)`
      )
      .bind(execId, id, tenantId, now)
      .run();

    await db
      .prepare(
        `UPDATE scheduled_jobs SET run_count = run_count + 1, last_run_at = ?, updated_at = ?
         WHERE id = ? AND tenant_id = ?`
      )
      .bind(now, now, id, tenantId)
      .run();

    return { executionId: execId, jobId: id, triggered: true };
  },

  // --- Executions ---

  async listExecutions(db: any, tenantId: string, jobId: string) {
    const result = await db
      .prepare(
        `SELECT * FROM job_executions WHERE job_id = ? AND tenant_id = ? ORDER BY started_at DESC LIMIT 100`
      )
      .bind(jobId, tenantId)
      .all();
    return result.results ?? [];
  },

  async getExecution(db: any, tenantId: string, executionId: string) {
    return db
      .prepare('SELECT * FROM job_executions WHERE id = ? AND tenant_id = ?')
      .bind(executionId, tenantId)
      .first();
  },

  // --- Skip Rules ---

  async listSkipRules(db: any, jobId: string) {
    const result = await db
      .prepare('SELECT * FROM skip_rules WHERE job_id = ? ORDER BY created_at ASC')
      .bind(jobId)
      .all();
    return result.results ?? [];
  },

  async addSkipRule(db: any, jobId: string, data: any) {
    const id = crypto.randomUUID();
    const now = new Date().toISOString();
    await db
      .prepare(
        `INSERT INTO skip_rules (id, job_id, rule_type, rule_config_json, created_at)
         VALUES (?, ?, ?, ?, ?)`
      )
      .bind(id, jobId, data.rule_type, JSON.stringify(data.rule_config ?? {}), now)
      .run();
    return { id, job_id: jobId, rule_type: data.rule_type, created_at: now };
  },

  // --- Admin ---

  async getAdminOverview(db: any) {
    const totals = await db
      .prepare(`SELECT status, COUNT(*) as count FROM scheduled_jobs GROUP BY status`)
      .all();

    const nextRuns = await db
      .prepare(
        `SELECT id, tenant_id, name, next_run_at FROM scheduled_jobs
         WHERE status = 'active' AND next_run_at IS NOT NULL
         ORDER BY next_run_at ASC LIMIT 10`
      )
      .all();

    const execCount = await db
      .prepare(`SELECT COUNT(*) as total FROM job_executions WHERE status = 'running'`)
      .first();

    return {
      job_counts: totals.results ?? [],
      next_runs: nextRuns.results ?? [],
      running_executions: execCount?.total ?? 0,
    };
  },
};
