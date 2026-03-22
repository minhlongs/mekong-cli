/**
 * Platform Capacity Planning Service
 * Capacity snapshots, forecasts, and scaling recommendations for platform resources
 */

export type ResourceType = 'compute' | 'storage' | 'bandwidth' | 'api_calls';
export type RecommendationType = 'scale_up' | 'scale_down' | 'optimize' | 'no_action';
export type Priority = 'low' | 'medium' | 'high' | 'critical';
export type RecommendationStatus = 'pending' | 'accepted' | 'rejected' | 'implemented';

export interface CapacitySnapshot {
  id: string;
  resource_type: ResourceType;
  current_usage: number;
  max_capacity: number;
  utilization_pct: number;
  recorded_at: string;
  created_at: string;
}

export interface CapacityForecast {
  id: string;
  resource_type: ResourceType;
  forecast_date: string;
  predicted_usage: number;
  confidence_pct: number;
  model_version: string;
  created_at: string;
}

export interface ScalingRecommendation {
  id: string;
  resource_type: ResourceType;
  recommendation_type: RecommendationType;
  current_value: number;
  recommended_value: number;
  reason: string;
  priority: Priority;
  status: RecommendationStatus;
  created_at: string;
  updated_at: string;
}

/** Record a new capacity snapshot for a resource */
export async function recordSnapshot(
  db: any,
  data: { resource_type: ResourceType; current_usage: number; max_capacity: number }
): Promise<CapacitySnapshot> {
  const id = crypto.randomUUID();
  const utilization_pct = data.max_capacity > 0
    ? Math.round((data.current_usage / data.max_capacity) * 10000) / 100
    : 0;
  await db.prepare(
    `INSERT INTO capacity_snapshots (id, resource_type, current_usage, max_capacity, utilization_pct)
     VALUES (?, ?, ?, ?, ?)`
  ).bind(id, data.resource_type, data.current_usage, data.max_capacity, utilization_pct).run();
  return db.prepare('SELECT * FROM capacity_snapshots WHERE id = ?').bind(id).first();
}

/** Get snapshots for a resource type (most recent first) */
export async function getSnapshots(
  db: any,
  resourceType?: ResourceType,
  limit = 50
): Promise<CapacitySnapshot[]> {
  if (resourceType) {
    const { results } = await db.prepare(
      'SELECT * FROM capacity_snapshots WHERE resource_type = ? ORDER BY recorded_at DESC LIMIT ?'
    ).bind(resourceType, limit).all();
    return results;
  }
  const { results } = await db.prepare(
    'SELECT * FROM capacity_snapshots ORDER BY recorded_at DESC LIMIT ?'
  ).bind(limit).all();
  return results;
}

/** Get the latest snapshot per resource type (current capacity overview) */
export async function getCurrentCapacity(db: any): Promise<CapacitySnapshot[]> {
  const { results } = await db.prepare(
    `SELECT * FROM capacity_snapshots WHERE id IN (
       SELECT id FROM capacity_snapshots
       GROUP BY resource_type
       HAVING recorded_at = MAX(recorded_at)
     ) ORDER BY resource_type`
  ).all();
  return results;
}

/** Create a capacity forecast entry */
export async function createForecast(
  db: any,
  data: { resource_type: ResourceType; forecast_date: string; predicted_usage: number; confidence_pct: number; model_version?: string }
): Promise<CapacityForecast> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO capacity_forecasts (id, resource_type, forecast_date, predicted_usage, confidence_pct, model_version)
     VALUES (?, ?, ?, ?, ?, ?)`
  ).bind(id, data.resource_type, data.forecast_date, data.predicted_usage, data.confidence_pct, data.model_version ?? 'v1').run();
  return db.prepare('SELECT * FROM capacity_forecasts WHERE id = ?').bind(id).first();
}

/** Get forecasts, optionally filtered by resource type */
export async function getForecasts(
  db: any,
  resourceType?: ResourceType
): Promise<CapacityForecast[]> {
  if (resourceType) {
    const { results } = await db.prepare(
      'SELECT * FROM capacity_forecasts WHERE resource_type = ? ORDER BY forecast_date ASC'
    ).bind(resourceType).all();
    return results;
  }
  const { results } = await db.prepare(
    'SELECT * FROM capacity_forecasts ORDER BY forecast_date ASC'
  ).all();
  return results;
}

/** Create a scaling recommendation */
export async function createRecommendation(
  db: any,
  data: { resource_type: ResourceType; recommendation_type: RecommendationType; current_value: number; recommended_value: number; reason: string; priority?: Priority }
): Promise<ScalingRecommendation> {
  const id = crypto.randomUUID();
  await db.prepare(
    `INSERT INTO scaling_recommendations (id, resource_type, recommendation_type, current_value, recommended_value, reason, priority)
     VALUES (?, ?, ?, ?, ?, ?, ?)`
  ).bind(id, data.resource_type, data.recommendation_type, data.current_value, data.recommended_value, data.reason, data.priority ?? 'medium').run();
  return db.prepare('SELECT * FROM scaling_recommendations WHERE id = ?').bind(id).first();
}

/** List recommendations, optionally filtered by status */
export async function listRecommendations(
  db: any,
  status?: RecommendationStatus
): Promise<ScalingRecommendation[]> {
  if (status) {
    const { results } = await db.prepare(
      `SELECT * FROM scaling_recommendations WHERE status = ?
       ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC`
    ).bind(status).all();
    return results;
  }
  const { results } = await db.prepare(
    `SELECT * FROM scaling_recommendations
     ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END, created_at DESC`
  ).all();
  return results;
}

/** Update recommendation status (accept/reject/implement) */
export async function updateRecommendation(
  db: any,
  recId: string,
  status: RecommendationStatus
): Promise<ScalingRecommendation | null> {
  const result = await db.prepare(
    `UPDATE scaling_recommendations SET status = ?, updated_at = datetime('now') WHERE id = ?`
  ).bind(status, recId).run();
  if (!result.meta?.changes) return null;
  return db.prepare('SELECT * FROM scaling_recommendations WHERE id = ?').bind(recId).first();
}

/** Full capacity dashboard: current state + upcoming forecasts + open recommendations */
export async function getCapacityDashboard(db: any) {
  const [current, forecasts, recommendations] = await Promise.all([
    getCurrentCapacity(db),
    db.prepare(
      `SELECT * FROM capacity_forecasts WHERE forecast_date >= date('now') ORDER BY forecast_date ASC LIMIT 20`
    ).all().then((r: any) => r.results),
    db.prepare(
      `SELECT * FROM scaling_recommendations WHERE status = 'pending'
       ORDER BY CASE priority WHEN 'critical' THEN 0 WHEN 'high' THEN 1 WHEN 'medium' THEN 2 ELSE 3 END`
    ).all().then((r: any) => r.results),
  ]);
  return { current_capacity: current, upcoming_forecasts: forecasts, open_recommendations: recommendations };
}

/** Admin overview — same as dashboard with full counts */
export async function getAdminOverview(db: any) {
  const dashboard = await getCapacityDashboard(db);
  const [snapshotCount, forecastCount, recCount] = await Promise.all([
    db.prepare('SELECT COUNT(*) as count FROM capacity_snapshots').first(),
    db.prepare('SELECT COUNT(*) as count FROM capacity_forecasts').first(),
    db.prepare('SELECT COUNT(*) as count FROM scaling_recommendations').first(),
  ]);
  return {
    ...dashboard,
    stats: {
      total_snapshots: snapshotCount?.count ?? 0,
      total_forecasts: forecastCount?.count ?? 0,
      total_recommendations: recCount?.count ?? 0,
    },
  };
}
