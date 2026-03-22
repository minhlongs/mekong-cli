/**
 * Platform Analytics Dashboard Service
 * Manages dashboard widgets, saved queries, analytics snapshots, and admin overview.
 */

import { nanoid } from 'nanoid';

// ── Widgets ────────────────────────────────────────────────────────────────────

async function listWidgets(db: any, tenantId: string): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM dashboard_widgets
     WHERE tenant_id = ? OR is_system = 1
     ORDER BY is_system DESC, created_at ASC`
  ).bind(tenantId).all();
  return rows.results;
}

async function createWidget(db: any, tenantId: string, data: {
  name: string;
  widget_type: string;
  query_json?: string;
  config_json?: string;
  position_json?: string;
}): Promise<unknown> {
  const id = nanoid();
  const now = new Date().toISOString();
  return db.prepare(
    `INSERT INTO dashboard_widgets (id, tenant_id, name, widget_type, query_json, config_json, position_json, created_at, updated_at)
     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    id, tenantId, data.name, data.widget_type,
    data.query_json ?? '{}',
    data.config_json ?? '{}',
    data.position_json ?? '{"x":0,"y":0,"w":6,"h":4}',
    now, now
  ).first();
}

async function updateWidget(db: any, tenantId: string, id: string, data: {
  name?: string;
  config_json?: string;
  position_json?: string;
}): Promise<unknown> {
  const now = new Date().toISOString();
  const sets: string[] = ['updated_at = ?'];
  const binds: unknown[] = [now];
  if (data.name !== undefined) { sets.push('name = ?'); binds.push(data.name); }
  if (data.config_json !== undefined) { sets.push('config_json = ?'); binds.push(data.config_json); }
  if (data.position_json !== undefined) { sets.push('position_json = ?'); binds.push(data.position_json); }
  binds.push(id, tenantId);
  return db.prepare(
    `UPDATE dashboard_widgets SET ${sets.join(', ')}
     WHERE id = ? AND tenant_id = ? AND is_system = 0 RETURNING *`
  ).bind(...binds).first();
}

async function deleteWidget(db: any, tenantId: string, id: string): Promise<boolean> {
  const result = await db.prepare(
    `DELETE FROM dashboard_widgets WHERE id = ? AND tenant_id = ? AND is_system = 0`
  ).bind(id, tenantId).run();
  return result.meta?.changes > 0;
}

// ── Saved Queries ──────────────────────────────────────────────────────────────

async function listSavedQueries(db: any, tenantId: string): Promise<unknown[]> {
  const rows = await db.prepare(
    `SELECT * FROM saved_queries WHERE tenant_id = ? ORDER BY created_at DESC`
  ).bind(tenantId).all();
  return rows.results;
}

async function createQuery(db: any, tenantId: string, data: {
  name: string;
  query_type: string;
  parameters_json?: string;
  schedule?: string;
}): Promise<unknown> {
  const id = nanoid();
  return db.prepare(
    `INSERT INTO saved_queries (id, tenant_id, name, query_type, parameters_json, schedule)
     VALUES (?, ?, ?, ?, ?, ?) RETURNING *`
  ).bind(
    id, tenantId, data.name, data.query_type,
    data.parameters_json ?? '{}',
    data.schedule ?? null
  ).first();
}

async function runQuery(db: any, tenantId: string, queryId: string): Promise<unknown> {
  const query = await db.prepare(
    `SELECT * FROM saved_queries WHERE id = ? AND tenant_id = ?`
  ).bind(queryId, tenantId).first();
  if (!query) return null;
  await db.prepare(
    `UPDATE saved_queries SET last_run_at = ? WHERE id = ?`
  ).bind(new Date().toISOString(), queryId).run();
  return { query_id: queryId, query_type: query.query_type, ran_at: new Date().toISOString(), status: 'ok' };
}

async function deleteQuery(db: any, tenantId: string, id: string): Promise<boolean> {
  const result = await db.prepare(
    `DELETE FROM saved_queries WHERE id = ? AND tenant_id = ?`
  ).bind(id, tenantId).run();
  return result.meta?.changes > 0;
}

// ── Snapshots ──────────────────────────────────────────────────────────────────

async function getSnapshots(db: any, type: string, period?: string): Promise<unknown[]> {
  const rows = period
    ? await db.prepare(
        `SELECT * FROM analytics_snapshots WHERE snapshot_type = ? AND period = ? ORDER BY created_at DESC LIMIT 100`
      ).bind(type, period).all()
    : await db.prepare(
        `SELECT * FROM analytics_snapshots WHERE snapshot_type = ? ORDER BY created_at DESC LIMIT 100`
      ).bind(type).all();
  return rows.results;
}

async function createSnapshot(db: any, data: {
  snapshot_type: string;
  data_json: string;
  period: string;
}): Promise<unknown> {
  const id = nanoid();
  return db.prepare(
    `INSERT INTO analytics_snapshots (id, snapshot_type, data_json, period) VALUES (?, ?, ?, ?) RETURNING *`
  ).bind(id, data.snapshot_type, data.data_json, data.period).first();
}

// ── Admin Overview ─────────────────────────────────────────────────────────────

async function getAdminOverview(db: any): Promise<unknown> {
  const [tenants, widgets, queries, snapshots] = await Promise.all([
    db.prepare(`SELECT COUNT(*) as count FROM tenants WHERE active = 1`).first(),
    db.prepare(`SELECT COUNT(*) as count FROM dashboard_widgets`).first(),
    db.prepare(`SELECT COUNT(*) as count FROM saved_queries`).first(),
    db.prepare(`SELECT COUNT(*) as count FROM analytics_snapshots`).first(),
  ]);
  return {
    active_tenants: tenants?.count ?? 0,
    total_widgets: widgets?.count ?? 0,
    total_saved_queries: queries?.count ?? 0,
    total_snapshots: snapshots?.count ?? 0,
    generated_at: new Date().toISOString(),
  };
}

// ── Exported service object ────────────────────────────────────────────────────

export const platformAnalyticsDashboardService = {
  listWidgets,
  createWidget,
  updateWidget,
  deleteWidget,
  listSavedQueries,
  createQuery,
  runQuery,
  deleteQuery,
  getSnapshots,
  createSnapshot,
  getAdminOverview,
};
