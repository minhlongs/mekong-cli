/**
 * Mission Execution Metrics Service
 * Record and query per-mission execution performance metrics and aggregates
 */

export interface ExecutionMetric {
  id: string; tenantId: string; missionId: string;
  executionTimeMs: number; tokensUsed: number; modelUsed: string | null;
  success: number; errorType: string | null; createdAt: string;
}

export interface ExecutionAggregate {
  id: string; tenantId: string; period: string;
  totalExecutions: number; avgExecutionTimeMs: number; p95ExecutionTimeMs: number;
  totalTokens: number; successRate: number; createdAt: string;
}

type MRow = { id: string; tenant_id: string; mission_id: string; execution_time_ms: number;
  tokens_used: number; model_used: string | null; success: number; error_type: string | null; created_at: string };
type ARow = { id: string; tenant_id: string; period: string; total_executions: number;
  avg_execution_time_ms: number; p95_execution_time_ms: number; total_tokens: number; success_rate: number; created_at: string };
type ORow = { tenant_id: string; total_executions: number; avg_execution_time_ms: number; total_tokens: number; success_rate: number };

const mapM = (r: MRow): ExecutionMetric => ({
  id: r.id, tenantId: r.tenant_id, missionId: r.mission_id,
  executionTimeMs: r.execution_time_ms, tokensUsed: r.tokens_used,
  modelUsed: r.model_used, success: r.success, errorType: r.error_type, createdAt: r.created_at,
});

const mapA = (r: ARow): ExecutionAggregate => ({
  id: r.id, tenantId: r.tenant_id, period: r.period,
  totalExecutions: r.total_executions, avgExecutionTimeMs: r.avg_execution_time_ms,
  p95ExecutionTimeMs: r.p95_execution_time_ms, totalTokens: r.total_tokens,
  successRate: r.success_rate, createdAt: r.created_at,
});

/** List recent metrics for a tenant, optionally filtered by mission_id */
async function listMetrics(db: any, tenantId: string, missionId?: string): Promise<ExecutionMetric[]> {
  try {
    let q = 'SELECT * FROM mission_execution_metrics WHERE tenant_id = ?';
    const b: string[] = [tenantId];
    if (missionId) { q += ' AND mission_id = ?'; b.push(missionId); }
    q += ' ORDER BY created_at DESC LIMIT 500';
    const result = await db.prepare(q).bind(...b).all();
    return ((result.results ?? []) as MRow[]).map(mapM);
  } catch (err) {
    console.error('[missionExecutionMetricsService.listMetrics]', err); throw err;
  }
}

/** Record a single mission execution metric */
async function recordMetric(db: any, tenantId: string, input: {
  missionId: string; executionTimeMs: number; tokensUsed?: number;
  modelUsed?: string; success?: number; errorType?: string;
}): Promise<ExecutionMetric> {
  try {
    const id = crypto.randomUUID();
    await db.prepare(
      `INSERT INTO mission_execution_metrics
       (id, tenant_id, mission_id, execution_time_ms, tokens_used, model_used, success, error_type)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(id, tenantId, input.missionId, input.executionTimeMs,
      input.tokensUsed ?? 0, input.modelUsed ?? null, input.success ?? 1, input.errorType ?? null).run();
    const row = (await db.prepare('SELECT * FROM mission_execution_metrics WHERE id = ?').bind(id).first()) as MRow | null;
    if (!row) throw new Error('Metric insert failed');
    return mapM(row);
  } catch (err) {
    console.error('[missionExecutionMetricsService.recordMetric]', err); throw err;
  }
}

/** Get execution aggregates for a tenant */
async function getAggregates(db: any, tenantId: string): Promise<ExecutionAggregate[]> {
  try {
    const result = await db.prepare(
      'SELECT * FROM mission_execution_aggregates WHERE tenant_id = ? ORDER BY created_at DESC'
    ).bind(tenantId).all();
    return ((result.results ?? []) as ARow[]).map(mapA);
  } catch (err) {
    console.error('[missionExecutionMetricsService.getAggregates]', err); throw err;
  }
}

/** Admin: platform-wide execution stats grouped by tenant */
async function getAdminOverview(db: any): Promise<{
  tenantId: string; totalExecutions: number; avgExecutionTimeMs: number;
  totalTokens: number; successRate: number;
}[]> {
  try {
    const result = await db.prepare(
      `SELECT tenant_id, COUNT(*) as total_executions,
              AVG(execution_time_ms) as avg_execution_time_ms,
              SUM(tokens_used) as total_tokens, AVG(success) as success_rate
       FROM mission_execution_metrics GROUP BY tenant_id
       ORDER BY total_executions DESC LIMIT 1000`
    ).all();
    return ((result.results ?? []) as ORow[]).map((r) => ({
      tenantId: r.tenant_id, totalExecutions: r.total_executions,
      avgExecutionTimeMs: Math.round(r.avg_execution_time_ms ?? 0),
      totalTokens: r.total_tokens ?? 0,
      successRate: Math.round((r.success_rate ?? 0) * 100) / 100,
    }));
  } catch (err) {
    console.error('[missionExecutionMetricsService.getAdminOverview]', err); throw err;
  }
}

export const missionExecutionMetricsService = { listMetrics, recordMetric, getAggregates, getAdminOverview };
