/**
 * Platform Feature Requests Service
 * Tables: feature_requests, feature_request_votes, feature_request_comments
 */

import type { D1Database } from '@cloudflare/workers-types';

export type FeatureCategory = 'general' | 'api' | 'dashboard' | 'billing' | 'integrations' | 'security';
export type FeatureStatus = 'submitted' | 'under_review' | 'planned' | 'in_progress' | 'completed' | 'declined';
export type FeaturePriority = 'low' | 'medium' | 'high' | 'critical';

export interface FeatureRequest {
  id: string;
  tenant_id: string;
  title: string;
  description: string;
  category: FeatureCategory;
  status: FeatureStatus;
  priority: FeaturePriority;
  vote_count: number;
  comment_count: number;
  admin_response: string | null;
  planned_version: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface FeatureComment {
  id: string;
  feature_request_id: string;
  tenant_id: string;
  content: string;
  is_admin: number;
  created_at: string;
}

export interface FeatureOverview {
  total: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  top_voted: FeatureRequest[];
}

const uid = (prefix: string) => prefix + crypto.randomUUID().replace(/-/g, '').slice(0, 16);

export async function createRequest(
  db: D1Database, tenantId: string, title: string, description: string,
  category: FeatureCategory = 'general',
): Promise<FeatureRequest> {
  const id = uid('fr_');
  await db.prepare(
    'INSERT INTO feature_requests (id, tenant_id, title, description, category) VALUES (?, ?, ?, ?, ?)',
  ).bind(id, tenantId, title, description, category).run();
  return db.prepare('SELECT * FROM feature_requests WHERE id = ?').bind(id).first<FeatureRequest>() as Promise<FeatureRequest>;
}

export async function listRequests(
  db: D1Database,
  opts: { sort?: 'votes' | 'date'; status?: string; category?: string; limit?: number; offset?: number } = {},
): Promise<FeatureRequest[]> {
  const { sort = 'votes', status, category, limit = 20, offset = 0 } = opts;
  const conds: string[] = [];
  const bind: unknown[] = [];
  if (status) { conds.push('status = ?'); bind.push(status); }
  if (category) { conds.push('category = ?'); bind.push(category); }
  const where = conds.length ? `WHERE ${conds.join(' AND ')}` : '';
  const order = sort === 'votes' ? 'vote_count DESC, created_at DESC' : 'created_at DESC';
  bind.push(limit, offset);
  const rows = await db.prepare(
    `SELECT * FROM feature_requests ${where} ORDER BY ${order} LIMIT ? OFFSET ?`,
  ).bind(...bind).all<FeatureRequest>();
  return rows.results;
}

export async function getRequest(db: D1Database, requestId: string): Promise<FeatureRequest | null> {
  return db.prepare('SELECT * FROM feature_requests WHERE id = ?').bind(requestId).first<FeatureRequest>();
}

export async function updateRequest(
  db: D1Database, requestId: string,
  updates: Partial<Pick<FeatureRequest, 'title' | 'description' | 'category'>>,
): Promise<FeatureRequest | null> {
  const fields = Object.keys(updates) as Array<keyof typeof updates>;
  if (!fields.length) return getRequest(db, requestId);
  const set = [...fields.map((f) => `${f} = ?`), "updated_at = datetime('now')"].join(', ');
  await db.prepare(`UPDATE feature_requests SET ${set} WHERE id = ?`)
    .bind(...fields.map((f) => updates[f]), requestId).run();
  return getRequest(db, requestId);
}

export async function voteForRequest(db: D1Database, requestId: string, tenantId: string): Promise<boolean> {
  const result = await db.prepare(
    'INSERT OR IGNORE INTO feature_request_votes (id, feature_request_id, tenant_id) VALUES (?, ?, ?)',
  ).bind(uid('frv_'), requestId, tenantId).run();
  if ((result.meta?.changes ?? 0) > 0) {
    await db.prepare(
      "UPDATE feature_requests SET vote_count = vote_count + 1, updated_at = datetime('now') WHERE id = ?",
    ).bind(requestId).run();
    return true;
  }
  return false;
}

export async function removeVote(db: D1Database, requestId: string, tenantId: string): Promise<boolean> {
  const result = await db.prepare(
    'DELETE FROM feature_request_votes WHERE feature_request_id = ? AND tenant_id = ?',
  ).bind(requestId, tenantId).run();
  if ((result.meta?.changes ?? 0) > 0) {
    await db.prepare(
      "UPDATE feature_requests SET vote_count = MAX(0, vote_count - 1), updated_at = datetime('now') WHERE id = ?",
    ).bind(requestId).run();
    return true;
  }
  return false;
}

export async function addComment(
  db: D1Database, requestId: string, tenantId: string, content: string, isAdmin = false,
): Promise<FeatureComment> {
  const id = uid('frc_');
  await db.prepare(
    'INSERT INTO feature_request_comments (id, feature_request_id, tenant_id, content, is_admin) VALUES (?, ?, ?, ?, ?)',
  ).bind(id, requestId, tenantId, content, isAdmin ? 1 : 0).run();
  await db.prepare(
    "UPDATE feature_requests SET comment_count = comment_count + 1, updated_at = datetime('now') WHERE id = ?",
  ).bind(requestId).run();
  return db.prepare('SELECT * FROM feature_request_comments WHERE id = ?')
    .bind(id).first<FeatureComment>() as Promise<FeatureComment>;
}

export async function listComments(db: D1Database, requestId: string): Promise<FeatureComment[]> {
  const rows = await db.prepare(
    'SELECT * FROM feature_request_comments WHERE feature_request_id = ? ORDER BY created_at ASC',
  ).bind(requestId).all<FeatureComment>();
  return rows.results;
}

export async function updateRequestStatus(
  db: D1Database, requestId: string,
  updates: Partial<Pick<FeatureRequest, 'status' | 'priority' | 'admin_response' | 'planned_version' | 'completed_at'>>,
): Promise<FeatureRequest | null> {
  const fields = Object.keys(updates) as Array<keyof typeof updates>;
  if (!fields.length) return getRequest(db, requestId);
  const set = [...fields.map((f) => `${f} = ?`), "updated_at = datetime('now')"].join(', ');
  await db.prepare(`UPDATE feature_requests SET ${set} WHERE id = ?`)
    .bind(...fields.map((f) => updates[f]), requestId).run();
  return getRequest(db, requestId);
}

export async function getAdminFeatureOverview(db: D1Database): Promise<FeatureOverview> {
  const [totalRow, statusRows, categoryRows, topRows] = await Promise.all([
    db.prepare('SELECT COUNT(*) as total FROM feature_requests').first<{ total: number }>(),
    db.prepare('SELECT status, COUNT(*) as count FROM feature_requests GROUP BY status').all<{ status: string; count: number }>(),
    db.prepare('SELECT category, COUNT(*) as count FROM feature_requests GROUP BY category').all<{ category: string; count: number }>(),
    db.prepare('SELECT * FROM feature_requests ORDER BY vote_count DESC LIMIT 5').all<FeatureRequest>(),
  ]);
  const by_status: Record<string, number> = {};
  for (const r of statusRows.results) by_status[r.status] = r.count;
  const by_category: Record<string, number> = {};
  for (const r of categoryRows.results) by_category[r.category] = r.count;
  return { total: totalRow?.total ?? 0, by_status, by_category, top_voted: topRows.results };
}
