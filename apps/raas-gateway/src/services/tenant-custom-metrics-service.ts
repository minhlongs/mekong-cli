/**
 * Tenant Custom Metrics Service
 * CRUD for metric definitions, data point ingestion, aggregation, admin overview
 */

const genId = () => crypto.randomUUID();
const now = () => new Date().toISOString();

// --- Metric Definitions ---

async function listMetrics(db: any, tenantId: string): Promise<any[]> {
  const { results } = await db.prepare(
    'SELECT * FROM custom_metric_definitions WHERE tenant_id = ? ORDER BY created_at DESC'
  ).bind(tenantId).all();
  return (results as any[]) ?? [];
}

async function createMetric(db: any, tenantId: string, data: any): Promise<any> {
  const id = genId();
  await db.prepare(`
    INSERT INTO custom_metric_definitions
      (id, tenant_id, metric_name, unit, aggregation_type, description, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `).bind(
    id, tenantId,
    data.metric_name,
    data.unit ?? 'count',
    data.aggregation_type ?? 'sum',
    data.description ?? null,
    now(),
  ).run();
  return db.prepare(
    'SELECT * FROM custom_metric_definitions WHERE id = ?'
  ).bind(id).first();
}

// --- Data Points ---

async function getDataPoints(db: any, tenantId: string, metricId: string, opts: {
  from?: string; to?: string; limit?: number;
} = {}): Promise<any[]> {
  let sql = 'SELECT * FROM custom_metric_data_points WHERE tenant_id = ? AND metric_id = ?';
  const binds: any[] = [tenantId, metricId];

  if (opts.from) { sql += ' AND recorded_at >= ?'; binds.push(opts.from); }
  if (opts.to)   { sql += ' AND recorded_at <= ?'; binds.push(opts.to); }

  sql += ' ORDER BY recorded_at DESC LIMIT ?';
  binds.push(opts.limit ?? 500);

  const { results } = await db.prepare(sql).bind(...binds).all();
  return (results as any[]) ?? [];
}

async function recordDataPoint(db: any, tenantId: string, data: any): Promise<any> {
  const id = genId();
  const ts = data.recorded_at ?? now();
  await db.prepare(`
    INSERT INTO custom_metric_data_points
      (id, tenant_id, metric_id, value, dimensions_json, recorded_at)
    VALUES (?, ?, ?, ?, ?, ?)
  `).bind(
    id, tenantId,
    data.metric_id,
    data.value,
    data.dimensions ? JSON.stringify(data.dimensions) : '{}',
    ts,
  ).run();
  return db.prepare(
    'SELECT * FROM custom_metric_data_points WHERE id = ?'
  ).bind(id).first();
}

// --- Admin ---

async function getAdminOverview(db: any): Promise<any> {
  const defs = await db.prepare(
    'SELECT COUNT(*) as total, COUNT(DISTINCT tenant_id) as tenants FROM custom_metric_definitions'
  ).first();
  const pts = await db.prepare(
    'SELECT COUNT(*) as total FROM custom_metric_data_points'
  ).first();
  const topMetrics = await db.prepare(`
    SELECT metric_id, COUNT(*) as point_count
    FROM custom_metric_data_points
    GROUP BY metric_id ORDER BY point_count DESC LIMIT 10
  `).all();
  return {
    definitions: { total: defs?.total ?? 0, tenants: defs?.tenants ?? 0 },
    data_points: { total: pts?.total ?? 0 },
    top_metrics: (topMetrics.results as any[]) ?? [],
  };
}

export const tenantCustomMetricsService = {
  listMetrics,
  createMetric,
  getDataPoints,
  recordDataPoint,
  getAdminOverview,
};
