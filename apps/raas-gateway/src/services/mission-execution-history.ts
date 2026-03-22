/**
 * Mission Execution History Service — record and query mission execution history and metrics
 * Supports: listHistory, recordExecution, getMetrics, getAdminOverview
 */

export interface ExecutionRecord {
  id: string;
  tenant_id: string;
  mission_id?: string;
  executor_type?: string;
  status: string;
  duration_ms?: number;
  input_summary?: string;
  output_summary?: string;
  error_message?: string;
  created_at?: string;
}

export interface ExecutionMetric {
  id: string;
  tenant_id: string;
  mission_id?: string;
  metric_type: string;
  metric_value: number;
  recorded_at?: string;
}

export interface RecordExecutionData {
  mission_id?: string;
  executor_type?: string;
  status?: string;
  duration_ms?: number;
  input_summary?: string;
  output_summary?: string;
  error_message?: string;
}

export interface AdminOverview {
  total_executions: number;
  total_metrics: number;
  tenants_with_executions: number;
}

/**
 * List execution history for a tenant, optionally filtered by mission_id.
 * Returns up to 100 most recent records.
 */
export async function listHistory(
  db: any,
  tenantId: string,
  missionId?: string
): Promise<ExecutionRecord[]> {
  try {
    let query = `SELECT * FROM execution_history WHERE tenant_id = ?`;
    const bindings: unknown[] = [tenantId];

    if (missionId) {
      query += ` AND mission_id = ?`;
      bindings.push(missionId);
    }

    query += ` ORDER BY created_at DESC LIMIT 100`;

    const result = await db
      .prepare(query)
      .bind(...bindings)
      .all();

    return (result.results ?? []) as ExecutionRecord[];
  } catch (err) {
    console.error('[execution-history] listHistory error', err);
    return [];
  }
}

/**
 * Insert a new execution record for a tenant.
 * Generates a UUID for the record id.
 */
export async function recordExecution(
  db: any,
  tenantId: string,
  data: RecordExecutionData
): Promise<{ success: boolean; id: string }> {
  const id = crypto.randomUUID();

  try {
    await db
      .prepare(
        `INSERT INTO execution_history
           (id, tenant_id, mission_id, executor_type, status, duration_ms, input_summary, output_summary, error_message)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`
      )
      .bind(
        id,
        tenantId,
        data.mission_id ?? null,
        data.executor_type ?? null,
        data.status ?? 'completed',
        data.duration_ms ?? null,
        data.input_summary ?? null,
        data.output_summary ?? null,
        data.error_message ?? null
      )
      .run();

    return { success: true, id };
  } catch (err) {
    console.error('[execution-history] recordExecution error', err);
    return { success: false, id };
  }
}

/**
 * Get all execution metrics for a tenant ordered by most recent first.
 */
export async function getMetrics(
  db: any,
  tenantId: string
): Promise<ExecutionMetric[]> {
  try {
    const result = await db
      .prepare(
        `SELECT * FROM execution_metrics WHERE tenant_id = ? ORDER BY recorded_at DESC LIMIT 200`
      )
      .bind(tenantId)
      .all();

    return (result.results ?? []) as ExecutionMetric[];
  } catch (err) {
    console.error('[execution-history] getMetrics error', err);
    return [];
  }
}

/**
 * Admin overview: count executions and metrics across all tenants.
 */
export async function getAdminOverview(db: any): Promise<AdminOverview> {
  try {
    const execRow = (await db
      .prepare(
        `SELECT COUNT(*) as total_executions,
                COUNT(DISTINCT tenant_id) as tenants_with_executions
         FROM execution_history`
      )
      .first()) as { total_executions: number; tenants_with_executions: number } | null;

    const metricsRow = (await db
      .prepare(`SELECT COUNT(*) as total_metrics FROM execution_metrics`)
      .first()) as { total_metrics: number } | null;

    return {
      total_executions: execRow?.total_executions ?? 0,
      total_metrics: metricsRow?.total_metrics ?? 0,
      tenants_with_executions: execRow?.tenants_with_executions ?? 0,
    };
  } catch (err) {
    console.error('[execution-history] getAdminOverview error', err);
    return { total_executions: 0, total_metrics: 0, tenants_with_executions: 0 };
  }
}

export const missionExecutionHistoryService = {
  listHistory,
  recordExecution,
  getMetrics,
  getAdminOverview,
};
