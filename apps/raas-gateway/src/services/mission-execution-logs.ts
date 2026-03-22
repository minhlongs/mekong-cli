/**
 * Mission Execution Logs Service — per-step log entries and summaries for mission runs
 * Supports: listLogs, createLog, getSummaries, getAdminOverview
 */

/**
 * List log entries for a tenant's mission, ordered by created_at ASC.
 * Optionally filter by mission_id and limit results.
 */
async function listLogs(
  db: any,
  tenantId: string,
  opts: { missionId?: string; limit?: number } = {}
): Promise<{ success: boolean; data?: unknown[]; error?: string }> {
  try {
    const limit = Math.min(opts.limit ?? 50, 200);
    let query = 'SELECT * FROM mission_execution_logs WHERE tenant_id = ?';
    const bindings: unknown[] = [tenantId];

    if (opts.missionId) {
      query += ' AND mission_id = ?';
      bindings.push(opts.missionId);
    }

    query += ' ORDER BY created_at ASC LIMIT ?';
    bindings.push(limit);

    const result = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: result.results };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Failed to list logs' };
  }
}

/**
 * Insert a new execution log entry for a mission step.
 * Generates a UUID for the record id.
 */
async function createLog(
  db: any,
  entry: {
    tenant_id: string;
    mission_id: string;
    step_name: string;
    log_level?: string;
    message: string;
    metadata?: string;
    duration_ms?: number;
  }
): Promise<{ success: boolean; data?: { id: string }; error?: string }> {
  try {
    const id = crypto.randomUUID();
    const level = entry.log_level ?? 'info';

    await db
      .prepare(
        `INSERT INTO mission_execution_logs
           (id, tenant_id, mission_id, step_name, log_level, message, metadata, duration_ms)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        entry.tenant_id,
        entry.mission_id,
        entry.step_name,
        level,
        entry.message,
        entry.metadata ?? null,
        entry.duration_ms ?? null
      )
      .run();

    return { success: true, data: { id } };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Failed to create log' };
  }
}

/**
 * List execution summaries for a tenant, ordered by created_at DESC.
 * Optionally filter by mission_id and limit results.
 */
async function getSummaries(
  db: any,
  tenantId: string,
  opts: { missionId?: string; limit?: number } = {}
): Promise<{ success: boolean; data?: unknown[]; error?: string }> {
  try {
    const limit = Math.min(opts.limit ?? 20, 100);
    let query = 'SELECT * FROM mission_execution_summaries WHERE tenant_id = ?';
    const bindings: unknown[] = [tenantId];

    if (opts.missionId) {
      query += ' AND mission_id = ?';
      bindings.push(opts.missionId);
    }

    query += ' ORDER BY created_at DESC LIMIT ?';
    bindings.push(limit);

    const result = await db.prepare(query).bind(...bindings).all();
    return { success: true, data: result.results };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Failed to get summaries' };
  }
}

/**
 * Admin overview — aggregate stats across all tenants.
 * Returns total logs, total summaries, and per-level log counts.
 */
async function getAdminOverview(
  db: any
): Promise<{ success: boolean; data?: unknown; error?: string }> {
  try {
    const [logsTotal, summariesTotal, levelBreakdown] = await Promise.all([
      db
        .prepare('SELECT COUNT(*) as total FROM mission_execution_logs')
        .first(),
      db
        .prepare('SELECT COUNT(*) as total FROM mission_execution_summaries')
        .first(),
      db
        .prepare(
          `SELECT log_level, COUNT(*) as count
           FROM mission_execution_logs
           GROUP BY log_level`
        )
        .all(),
    ]);

    const levels: Record<string, number> = {};
    for (const row of (levelBreakdown.results as { log_level: string; count: number }[])) {
      levels[row.log_level] = row.count;
    }

    return {
      success: true,
      data: {
        total_logs: (logsTotal as { total: number } | null)?.total ?? 0,
        total_summaries: (summariesTotal as { total: number } | null)?.total ?? 0,
        log_levels: levels,
      },
    };
  } catch (err) {
    return { success: false, error: err instanceof Error ? err.message : 'Failed to get overview' };
  }
}

export const missionExecutionLogsService = {
  listLogs,
  createLog,
  getSummaries,
  getAdminOverview,
};
