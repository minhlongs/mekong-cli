/**
 * Tenant Collaboration Service — comments, shared views, activity feed
 */

import type { D1Database } from '@cloudflare/workers-types';

// ── Types ──────────────────────────────────────────────────────────────────────

export interface MissionComment {
  id: string;
  tenant_id: string;
  mission_id: string;
  user_id: string;
  content: string;
  parent_id: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface SharedView {
  id: string;
  tenant_id: string;
  name: string;
  view_type: string;
  filters: string | null;
  shared_with: string | null;
  created_by: string;
  created_at: string;
}

export interface ActivityEntry {
  id: string;
  tenant_id: string;
  actor_id: string;
  action: string;
  resource_type: string;
  resource_id: string | null;
  metadata: string | null;
  created_at: string;
}

export interface CollaborationStats {
  comments: number;
  views: number;
  activities: number;
}

export interface AdminTenantActivity {
  tenant_id: string;
  comment_count: number;
  view_count: number;
  activity_count: number;
}

// ── Comments ───────────────────────────────────────────────────────────────────

/** Add a comment to a mission — supports threaded replies via parent_id */
export async function addComment(
  db: D1Database,
  tenantId: string,
  missionId: string,
  userId: string,
  content: string,
  parentId?: string,
): Promise<MissionComment> {
  const id = crypto.randomUUID();
  try {
    await db.prepare(
      `INSERT INTO mission_comments (id, tenant_id, mission_id, user_id, content, parent_id)
       VALUES (?, ?, ?, ?, ?, ?)`
    ).bind(id, tenantId, missionId, userId, content, parentId ?? null).run();

    return db.prepare('SELECT * FROM mission_comments WHERE id = ?')
      .bind(id).first<MissionComment>() as Promise<MissionComment>;
  } catch (err) {
    throw new Error(`Failed to add comment: ${String(err)}`);
  }
}

/** List all comments for a mission within a tenant, ordered chronologically */
export async function listComments(
  db: D1Database,
  tenantId: string,
  missionId: string,
): Promise<MissionComment[]> {
  try {
    const result = await db.prepare(
      `SELECT * FROM mission_comments WHERE tenant_id = ? AND mission_id = ? ORDER BY created_at ASC`
    ).bind(tenantId, missionId).all<MissionComment>();
    return result.results ?? [];
  } catch (err) {
    throw new Error(`Failed to list comments: ${String(err)}`);
  }
}

/** Delete a comment — user may only delete their own */
export async function deleteComment(
  db: D1Database,
  tenantId: string,
  commentId: string,
  userId: string,
): Promise<{ deleted: boolean }> {
  try {
    const result = await db.prepare(
      `DELETE FROM mission_comments WHERE id = ? AND tenant_id = ? AND user_id = ?`
    ).bind(commentId, tenantId, userId).run();
    return { deleted: (result.meta?.changes ?? 0) > 0 };
  } catch (err) {
    throw new Error(`Failed to delete comment: ${String(err)}`);
  }
}

// ── Shared Views ───────────────────────────────────────────────────────────────

/** Create a shared view for a tenant */
export async function createSharedView(
  db: D1Database,
  tenantId: string,
  createdBy: string,
  name: string,
  viewType: string,
  filters?: unknown,
  sharedWith?: string[] | 'all',
): Promise<SharedView> {
  const id = crypto.randomUUID();
  const filtersJson = filters ? JSON.stringify(filters) : null;
  const sharedWithJson = sharedWith ? JSON.stringify(sharedWith) : null;
  try {
    await db.prepare(
      `INSERT INTO shared_views (id, tenant_id, name, view_type, filters, shared_with, created_by)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).bind(id, tenantId, name, viewType, filtersJson, sharedWithJson, createdBy).run();

    return db.prepare('SELECT * FROM shared_views WHERE id = ?')
      .bind(id).first<SharedView>() as Promise<SharedView>;
  } catch (err) {
    throw new Error(`Failed to create shared view: ${String(err)}`);
  }
}

/** List shared views accessible to a user — own views + views shared with 'all' or explicitly */
export async function listSharedViews(
  db: D1Database,
  tenantId: string,
  userId: string,
): Promise<SharedView[]> {
  try {
    const result = await db.prepare(
      `SELECT * FROM shared_views
       WHERE tenant_id = ?
         AND (created_by = ? OR shared_with = '"all"' OR shared_with LIKE ?)
       ORDER BY created_at DESC`
    ).bind(tenantId, userId, `%"${userId}"%`).all<SharedView>();
    return result.results ?? [];
  } catch (err) {
    throw new Error(`Failed to list shared views: ${String(err)}`);
  }
}

/** Delete a shared view — user may only delete their own */
export async function deleteSharedView(
  db: D1Database,
  tenantId: string,
  viewId: string,
  userId: string,
): Promise<{ deleted: boolean }> {
  try {
    const result = await db.prepare(
      `DELETE FROM shared_views WHERE id = ? AND tenant_id = ? AND created_by = ?`
    ).bind(viewId, tenantId, userId).run();
    return { deleted: (result.meta?.changes ?? 0) > 0 };
  } catch (err) {
    throw new Error(`Failed to delete shared view: ${String(err)}`);
  }
}

// ── Activity Feed ──────────────────────────────────────────────────────────────

/** Get paginated activity feed for a tenant, newest first */
export async function getActivityFeed(
  db: D1Database,
  tenantId: string,
  limit = 50,
  offset = 0,
): Promise<ActivityEntry[]> {
  try {
    const result = await db.prepare(
      `SELECT * FROM activity_feed WHERE tenant_id = ? ORDER BY created_at DESC LIMIT ? OFFSET ?`
    ).bind(tenantId, limit, offset).all<ActivityEntry>();
    return result.results ?? [];
  } catch (err) {
    throw new Error(`Failed to get activity feed: ${String(err)}`);
  }
}

/** Log an activity event — fire-and-forget friendly (non-throwing) */
export async function logActivity(
  db: D1Database,
  tenantId: string,
  actorId: string,
  action: string,
  resourceType: string,
  resourceId?: string,
  metadata?: unknown,
): Promise<void> {
  try {
    const id = crypto.randomUUID();
    const metaJson = metadata ? JSON.stringify(metadata) : null;
    await db.prepare(
      `INSERT INTO activity_feed (id, tenant_id, actor_id, action, resource_type, resource_id, metadata)
       VALUES (?, ?, ?, ?, ?, ?, ?)`
    ).bind(id, tenantId, actorId, action, resourceType, resourceId ?? null, metaJson).run();
  } catch {
    // Non-critical — don't surface logging failures to callers
  }
}

// ── Stats ──────────────────────────────────────────────────────────────────────

/** Collaboration counts for a single tenant */
export async function getCollaborationStats(
  db: D1Database,
  tenantId: string,
): Promise<CollaborationStats> {
  try {
    const [comments, views, activities] = await Promise.all([
      db.prepare('SELECT COUNT(*) as n FROM mission_comments WHERE tenant_id = ?').bind(tenantId).first<{ n: number }>(),
      db.prepare('SELECT COUNT(*) as n FROM shared_views WHERE tenant_id = ?').bind(tenantId).first<{ n: number }>(),
      db.prepare('SELECT COUNT(*) as n FROM activity_feed WHERE tenant_id = ?').bind(tenantId).first<{ n: number }>(),
    ]);
    return {
      comments: comments?.n ?? 0,
      views: views?.n ?? 0,
      activities: activities?.n ?? 0,
    };
  } catch (err) {
    throw new Error(`Failed to get collaboration stats: ${String(err)}`);
  }
}

/** Admin — most active tenants ranked by total activity */
export async function getAdminCollaborationOverview(db: D1Database): Promise<AdminTenantActivity[]> {
  try {
    const result = await db.prepare(
      `SELECT
         a.tenant_id,
         COALESCE(c.cnt, 0) AS comment_count,
         COALESCE(v.cnt, 0) AS view_count,
         a.cnt              AS activity_count
       FROM (
         SELECT tenant_id, COUNT(*) AS cnt FROM activity_feed GROUP BY tenant_id
       ) a
       LEFT JOIN (SELECT tenant_id, COUNT(*) AS cnt FROM mission_comments GROUP BY tenant_id) c
         ON c.tenant_id = a.tenant_id
       LEFT JOIN (SELECT tenant_id, COUNT(*) AS cnt FROM shared_views GROUP BY tenant_id) v
         ON v.tenant_id = a.tenant_id
       ORDER BY activity_count DESC
       LIMIT 50`
    ).all<AdminTenantActivity>();
    return result.results ?? [];
  } catch (err) {
    throw new Error(`Failed to get admin collaboration overview: ${String(err)}`);
  }
}
