/**
 * Usage Forecast Service — ML-lite prediction for capacity planning
 * Supports linear regression and moving average models
 */

import type { D1Database } from '@cloudflare/workers-types';

export type MetricType = 'missions' | 'credits' | 'api_calls' | 'storage';
export type ModelType = 'linear' | 'moving_average' | 'exponential';

export interface UsageForecast {
  id: string;
  tenant_id: string;
  metric_type: string;
  forecast_date: string;
  predicted_value: number;
  confidence_low: number | null;
  confidence_high: number | null;
  model_type: string;
  generated_at: string;
}

interface DataPoint { date: string; value: number }
interface ForecastPoint { date: string; value: number; band: number }

// ─── Math helpers ─────────────────────────────────────────────────────────────

function linearRegression(points: { x: number; y: number }[]): { slope: number; intercept: number } {
  const n = points.length;
  if (n < 2) return { slope: 0, intercept: points[0]?.y ?? 0 };
  const sumX = points.reduce((s, p) => s + p.x, 0);
  const sumY = points.reduce((s, p) => s + p.y, 0);
  const sumXY = points.reduce((s, p) => s + p.x * p.y, 0);
  const sumX2 = points.reduce((s, p) => s + p.x * p.x, 0);
  const slope = (n * sumXY - sumX * sumY) / (n * sumX2 - sumX * sumX) || 0;
  return { slope, intercept: (sumY - slope * sumX) / n };
}

function stddev(values: number[]): number {
  if (values.length < 2) return 0;
  const mean = values.reduce((s, v) => s + v, 0) / values.length;
  return Math.sqrt(values.reduce((s, v) => s + (v - mean) ** 2, 0) / values.length);
}

function futureDate(offsetDays: number): string {
  return new Date(Date.now() + offsetDays * 86400000).toISOString().slice(0, 10);
}

// ─── Snapshot CRUD ────────────────────────────────────────────────────────────

/** Record daily usage snapshot — upserts by tenant/metric/date */
export async function recordSnapshot(
  db: D1Database, tenantId: string, metricType: MetricType, value: number, date?: string
): Promise<void> {
  const snapshotDate = date ?? new Date().toISOString().slice(0, 10);
  await db
    .prepare(`INSERT INTO usage_snapshots (id, tenant_id, metric_type, metric_value, snapshot_date)
              VALUES (?, ?, ?, ?, ?)
              ON CONFLICT(tenant_id, metric_type, snapshot_date)
              DO UPDATE SET metric_value = excluded.metric_value`)
    .bind(crypto.randomUUID(), tenantId, metricType, value, snapshotDate)
    .run();
}

/** Get historical snapshots ordered by date ascending */
export async function getSnapshots(
  db: D1Database, tenantId: string, metricType: MetricType, days = 30
): Promise<DataPoint[]> {
  const since = new Date(Date.now() - days * 86400000).toISOString().slice(0, 10);
  const rows = await db
    .prepare(`SELECT snapshot_date as date, metric_value as value
              FROM usage_snapshots
              WHERE tenant_id = ? AND metric_type = ? AND snapshot_date >= ?
              ORDER BY snapshot_date ASC`)
    .bind(tenantId, metricType, since)
    .all<DataPoint>();
  return rows.results ?? [];
}

// ─── Forecast models ──────────────────────────────────────────────────────────

/** Linear regression forecast with confidence band */
export function linearForecast(data: DataPoint[], daysAhead: number): ForecastPoint[] {
  if (data.length < 2) return [];
  const points = data.map((d, i) => ({ x: i, y: d.value }));
  const { slope, intercept } = linearRegression(points);
  const residuals = points.map(p => p.y - (slope * p.x + intercept));
  const band = 1.5 * stddev(residuals);
  return Array.from({ length: daysAhead }, (_, i) => ({
    date: futureDate(i + 1),
    value: Math.max(0, slope * (data.length + i) + intercept),
    band,
  }));
}

/** Moving average forecast */
export function movingAverageForecast(data: DataPoint[], daysAhead: number, window = 7): ForecastPoint[] {
  if (data.length < 1) return [];
  const slice = data.slice(-window);
  const avg = slice.reduce((s, d) => s + d.value, 0) / slice.length;
  const band = 1.5 * stddev(slice.map(d => d.value));
  return Array.from({ length: daysAhead }, (_, i) => ({
    date: futureDate(i + 1), value: Math.max(0, avg), band,
  }));
}

// ─── Forecast persistence ─────────────────────────────────────────────────────

/** Generate and persist forecast for a metric */
export async function generateForecast(
  db: D1Database, tenantId: string, metricType: MetricType,
  daysAhead = 7, modelType: ModelType = 'linear'
): Promise<UsageForecast[]> {
  const data = await getSnapshots(db, tenantId, metricType, 30);
  const predictions = modelType === 'moving_average'
    ? movingAverageForecast(data, daysAhead)
    : linearForecast(data, daysAhead);

  const now = new Date().toISOString();
  const saved: UsageForecast[] = [];
  for (const p of predictions) {
    const id = crypto.randomUUID();
    const low = Math.max(0, p.value - p.band);
    const high = p.value + p.band;
    await db
      .prepare(`INSERT INTO usage_forecasts
                (id, tenant_id, metric_type, forecast_date, predicted_value, confidence_low, confidence_high, model_type)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)`)
      .bind(id, tenantId, metricType, p.date, p.value, low, high, modelType)
      .run();
    saved.push({ id, tenant_id: tenantId, metric_type: metricType, forecast_date: p.date,
      predicted_value: p.value, confidence_low: low, confidence_high: high,
      model_type: modelType, generated_at: now });
  }
  return saved;
}

/** Get latest forecast rows for a metric */
export async function getForecast(
  db: D1Database, tenantId: string, metricType: MetricType
): Promise<UsageForecast[]> {
  const rows = await db
    .prepare(`SELECT * FROM usage_forecasts
              WHERE tenant_id = ? AND metric_type = ?
              AND generated_at = (
                SELECT MAX(generated_at) FROM usage_forecasts
                WHERE tenant_id = ? AND metric_type = ?
              )
              ORDER BY forecast_date ASC`)
    .bind(tenantId, metricType, tenantId, metricType)
    .all<UsageForecast>();
  return rows.results ?? [];
}

/** Get latest forecasts for all metric types */
export async function getAllForecasts(db: D1Database, tenantId: string): Promise<Record<string, UsageForecast[]>> {
  const metrics: MetricType[] = ['missions', 'credits', 'api_calls', 'storage'];
  const results = await Promise.all(metrics.map(m => getForecast(db, tenantId, m)));
  return Object.fromEntries(metrics.map((m, i) => [m, results[i]]));
}

// ─── Analysis ─────────────────────────────────────────────────────────────────

/** Detect anomalies — data points > 2 stddev from mean */
export async function detectAnomalies(
  db: D1Database, tenantId: string, metricType: MetricType
): Promise<DataPoint[]> {
  const data = await getSnapshots(db, tenantId, metricType, 30);
  if (data.length < 3) return [];
  const mean = data.reduce((s, d) => s + d.value, 0) / data.length;
  const sd = stddev(data.map(d => d.value));
  return data.filter(d => Math.abs(d.value - mean) > 2 * sd);
}

/** Check if any metric forecast approaches/exceeds plan limits */
export async function getCapacityAlert(
  db: D1Database, tenantId: string
): Promise<{ metric: string; alert: string; predicted_peak: number }[]> {
  const limits: Record<string, number> = { missions: 500, credits: 10000, api_calls: 50000 };
  const alerts = [];
  for (const [metric, limit] of Object.entries(limits)) {
    const forecasts = await getForecast(db, tenantId, metric as MetricType);
    const peak = Math.max(...forecasts.map(f => f.predicted_value), 0);
    if (peak > limit * 0.8) {
      alerts.push({ metric, alert: peak > limit ? 'exceeded' : 'approaching', predicted_peak: peak });
    }
  }
  return alerts;
}

/** Collect today's metrics from missions/credits/usage_logs tables */
export async function collectDailySnapshots(db: D1Database, tenantId: string): Promise<void> {
  const today = new Date().toISOString().slice(0, 10);
  const [missionRow, creditRow, apiRow] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as cnt FROM missions WHERE tenant_id = ? AND date(created_at) = ?`)
      .bind(tenantId, today).first<{ cnt: number }>(),
    db.prepare(`SELECT COALESCE(SUM(amount), 0) as total FROM credit_transactions
                WHERE tenant_id = ? AND type = 'debit' AND date(created_at) = ?`)
      .bind(tenantId, today).first<{ total: number }>(),
    db.prepare(`SELECT COUNT(*) as cnt FROM usage_logs WHERE tenant_id = ? AND date(created_at) = ?`)
      .bind(tenantId, today).first<{ cnt: number }>().catch(() => null),
  ]);
  await Promise.all([
    recordSnapshot(db, tenantId, 'missions', missionRow?.cnt ?? 0, today),
    recordSnapshot(db, tenantId, 'credits', creditRow?.total ?? 0, today),
    recordSnapshot(db, tenantId, 'api_calls', apiRow?.cnt ?? 0, today),
  ]);
}
